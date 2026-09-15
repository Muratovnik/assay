"""Check non-UI evaluation data and freeze input-only inline case packets.

No model execution, installation, rubric grading or result-percentage claims.
The legacy audit protocol remains authoritative for its file-backed fixtures.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import runpy
import sys
import tempfile
from typing import Any
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
PAIRED_SKILLS = ("route-subagents", "code-maintenance", "evidence-research", "test-writing", "test-audit")
INPUT_KEYS = {"id", "prompt", "context", "files"}
COLLECTIONS = ("cases", "discovery_cases", "triggers")


def load(path: Path) -> dict[str, Any]:
    def unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"{path.name}: duplicate JSON key {key}")
            result[key] = value
        return result
    document = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique,
                          parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))
    if not isinstance(document, dict):
        raise ValueError(f"{path.name}: expected an object")
    return document


def portable(name: str) -> str:
    if (not isinstance(name, str) or not name or "\\" in name or ":" in name
            or name.startswith("/") or any(p in ("", ".", "..") for p in name.split("/"))):
        raise ValueError(f"unsafe portable path: {name!r}")
    # Windows aliases/device names are ambiguous in shared evaluation inputs.
    for part in name.split("/"):
        if part[-1:] in (".", " ") or re.search(r'[<>"|?*\x00-\x1f]', part):
            raise ValueError(f"nonportable path: {name!r}")
        if re.fullmatch(r"(?:CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\..*)?", part, re.I):
            raise ValueError(f"reserved path: {name!r}")
    return name


def input_case(case: Any) -> dict[str, Any]:
    if not isinstance(case, dict) or set(case) - INPUT_KEYS:
        raise ValueError("input case contains unsupported fields or grading data")
    if not isinstance(case.get("id"), str) or not case["id"].strip():
        raise ValueError("input case requires a string id")
    if not isinstance(case.get("prompt"), str) or not case["prompt"].strip():
        raise ValueError("input case requires a nonempty prompt")
    if "context" in case and not isinstance(case["context"], str):
        raise ValueError("context must be text")
    files = case.get("files", {})
    if not isinstance(files, dict):
        raise ValueError("inline case files must be an object")
    seen = set()
    for name, text in files.items():
        portable(name)
        if name.casefold() in seen or not isinstance(text, str):
            raise ValueError("case-colliding filenames or non-text input")
        seen.add(name.casefold())
    for name in seen:
        if any("/".join(name.split("/")[:n]) in seen for n in range(1, len(name.split("/")))):
            raise ValueError("input file/directory collision")
    return case


def collections(document: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    return {key: value for key, value in document.items()
            if key in COLLECTIONS}


def record_ids(records: Any, label: str) -> set[str]:
    if not isinstance(records, list) or not records:
        raise ValueError(f"{label}: expected a nonempty case array")
    ids = []
    for record in records:
        if not isinstance(record, dict) or not isinstance(record.get("id"), str) or not record["id"]:
            raise ValueError(f"{label}: invalid case ID")
        ids.append(record["id"])
    if len(set(ids)) != len(ids):
        raise ValueError(f"{label}: duplicate case IDs")
    return set(ids)


def check_pair(cases_path: Path, rubric_path: Path, name: str) -> None:
    cases, rubric = load(cases_path), load(rubric_path)
    for document in (cases, rubric):
        if type(document.get("schema_version")) is not int or document["schema_version"] != 1 or document.get("skill_name") != name:
            raise ValueError(f"{name}: schema/skill identity mismatch")
    source_groups, rubric_groups = collections(cases), collections(rubric)
    if "cases" not in source_groups or source_groups.keys() != rubric_groups.keys():
        raise ValueError(f"{name}: case/rubric collections disagree")
    for key, records in source_groups.items():
        if record_ids(records, key) != record_ids(rubric_groups[key], key):
            raise ValueError(f"{name}: {key} IDs disagree with rubric")
        for record in records:
            input_case(record)


def audit_tools(root: Path = ROOT) -> Any:
    path = root / "skills/independent-audit/evals/prepare_case.py"
    # Loading coordinator code must not cache bytecode inside canonical skills.
    return SimpleNamespace(**runpy.run_path(str(path)))


def check(root: Path = ROOT) -> dict[str, str]:
    report = {}
    for name in PAIRED_SKILLS:
        directory = root / "skills" / name / "evals"
        check_pair(directory / "cases.json", directory / "rubric.json", name)
        for cases in sorted(directory.glob("*-cases.json")):
            check_pair(cases, cases.with_name(cases.name.replace("-cases.json", "-rubric.json")), name)
        report[name] = "input/rubric structure checked, no model run"
    # Keep the existing, separately tested fixture/file validation path.
    audit_tools(root).load_cases(root / "skills/independent-audit/evals")
    report["independent-audit"] = "legacy fixture paths checked, no model run"
    if not (root / "skills/skill-design/evals/research-and-transfer.md").is_file():
        raise ValueError("skill-design: missing manual evaluation document")
    report["skill-design"] = "manual Markdown evaluation; no JSON conversion or behavioral claim"
    return report


def prepare(*, cases_path: Path, case_id: str, output_parent: Path,
            collection: str = "cases", skill_roots: tuple[Path, ...] = (), root: Path = ROOT) -> tuple[Path, str]:
    """Materialize only named inputs and explicit method roots, never grading keys.

    Two real consumers (research and maintenance, also test methods) reuse the
    audit utility's path guard, method snapshot and postflight verifier.
    Filesystem blindness must be enforced by the external executor, not here.
    """
    packets = audit_tools(root)
    cases_path = packets.plain_path(cases_path)
    source = load(cases_path)
    if source.get("skill_name") not in PAIRED_SKILLS or type(source.get("schema_version")) is not int or source["schema_version"] != 1:
        raise ValueError("unsupported inline corpus")
    if collection not in COLLECTIONS:
        raise ValueError("unsupported case collection")
    records = source.get(collection)
    record_ids(records, collection)
    matching = [item for item in records if item["id"] == case_id]
    if len(matching) != 1:
        raise ValueError(f"unknown case: {case_id}")
    case = input_case(matching[0])
    parent = packets.plain_path(output_parent)
    methods = tuple(packets.plain_path(path) for path in skill_roots)
    for source_root in (cases_path.parent.parent, *methods):
        if parent == source_root or source_root in parent.parents:
            raise ValueError("output must be outside source packages")
    names = [method.name for method in methods]
    if len(set(names)) != len(names):
        raise ValueError("duplicate method roots")
    payload = {"inputs/" + name: value.encode("utf-8") for name, value in case.get("files", {}).items()}
    payload["prompt.txt"] = (case["prompt"] + "\n").encode("utf-8")
    if "context" in case:
        payload["context.txt"] = (case["context"] + "\n").encode("utf-8")
    for method in methods:
        payload.update(packets.skill_snapshot(method, method.name))
    manifest = {"case_id": case_id, "source_sha256": hashlib.sha256(cases_path.read_bytes()).hexdigest(),
                "files": {name: hashlib.sha256(data).hexdigest() for name, data in sorted(payload.items())}}
    manifest_bytes = (json.dumps(manifest, indent=2) + "\n").encode("utf-8")
    payload["manifest.json"] = manifest_bytes
    # Names have been preflighted before allocating; never overwrite a packet.
    packet = Path(tempfile.mkdtemp(prefix="inline-case-", dir=parent))
    for name, data in sorted(payload.items()):
        destination = packet.joinpath(*PurePosixPath(name).parts)
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("xb") as stream:
            stream.write(data)
    retained = hashlib.sha256(manifest_bytes).hexdigest()
    packets.verify_packet(packet, retained)
    return packet, retained


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    checking = sub.add_parser("check")
    checking.add_argument("--root", type=Path, default=ROOT)
    building = sub.add_parser("prepare")
    building.add_argument("--cases", required=True, type=Path)
    building.add_argument("--case", required=True)
    building.add_argument("--collection", choices=COLLECTIONS, default="cases")
    building.add_argument("--output-parent", required=True, type=Path)
    building.add_argument("--method", action="append", type=Path, default=[])
    args = parser.parse_args()
    try:
        if args.command == "check":
            print(json.dumps(check(args.root), indent=2))
        else:
            packet, digest = prepare(cases_path=args.cases, case_id=args.case,
                                     output_parent=args.output_parent, collection=args.collection,
                                     skill_roots=tuple(args.method))
            print(json.dumps({"packet": str(packet), "retain_externally": digest}, indent=2))
    except (OSError, ValueError, TypeError, KeyError) as error:
        print(f"evaluation data: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
