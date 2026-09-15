"""Prepare an input-only audit packet. Coordinator utility, never executor input."""

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import stat
import tempfile


EVAL_ROOT = Path(__file__).resolve().parent
SKILL_ROOT = EVAL_ROOT.parent


def plain_path(path):
    """Reject links/junctions before resolution; do not follow alternate roots."""
    path = Path(path).absolute()
    for node in (path, *path.parents):
        info = node.lstat()
        if stat.S_ISLNK(info.st_mode) or (
            getattr(info, "st_file_attributes", 0)
            & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
        ):
            raise ValueError(f"Linked/reparse paths are not supported: {node}")
    return path.resolve(strict=True)


def input_file(root, relative):
    if not isinstance(relative, str) or "\\" in relative or ":" in relative:
        raise ValueError("Input paths must be portable relative POSIX paths")
    rel = PurePosixPath(relative)
    if rel.is_absolute() or not rel.parts or any(
        part in ("", ".", "..") for part in relative.split("/")
    ):
        raise ValueError(f"Unsafe input path: {relative}")
    root = plain_path(root)
    path = plain_path(root.joinpath(*rel.parts))
    path.relative_to(root)
    if not path.is_file():
        raise ValueError(f"Not a file: {relative}")
    return path


def load_cases(eval_root=EVAL_ROOT):
    root = plain_path(eval_root)
    catalog = json.loads(input_file(root, "evals.json").read_text(encoding="utf-8"))
    if catalog.get("skill_name") != "independent-audit" or not catalog.get("evals"):
        raise ValueError("Invalid or empty catalog")
    cases = {}
    for case in catalog["evals"]:
        case_id = case.get("id")
        if type(case_id) is not int or case_id < 1 or case_id in cases:
            raise ValueError("Case IDs must be unique positive integers")
        for key in ("prompt", "expected_output"):
            if not isinstance(case.get(key), str) or not case[key].strip():
                raise ValueError(f"Case {case_id} lacks {key}")
        for key in ("files", "assertions"):
            values = case.get(key)
            if not isinstance(values, list) or not values or any(
                not isinstance(value, str) or not value.strip() for value in values
            ):
                raise ValueError(f"Case {case_id} lacks valid {key}")
        seen = set()
        for relative in case["files"]:
            path = input_file(root, relative)
            if PurePosixPath(relative).parts[:2] != ("files", str(case_id)):
                raise ValueError("Executor inputs must stay within their fixture")
            folded = relative.casefold()
            if folded in seen:
                raise ValueError(f"Duplicate/case-colliding input: {relative}")
            seen.add(folded)
            if not path.read_bytes():
                raise ValueError(f"Empty input: {relative}")
        if f"files/{case_id}/brief.md" not in case["files"]:
            raise ValueError(f"Case {case_id} lacks its brief")
        cases[case_id] = case
    return cases


def skill_snapshot(skill_root, name="independent-audit"):
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name):
        raise ValueError("Invalid runtime skill name")
    root = plain_path(skill_root)
    relatives = ["SKILL.md"]
    if (root / "agents" / "openai.yaml").exists():
        relatives.append("agents/openai.yaml")
    if (root / "references").exists():
        plain_path(root / "references")
        for path in sorted((root / "references").rglob("*")):
            plain_path(path)
            if path.is_file():
                relatives.append(path.relative_to(root).as_posix())
    return {
        "skill/" + name + "/" + rel: input_file(root, rel).read_bytes()
        for rel in relatives
    }


def verify_packet(packet, expected_manifest_sha256):
    """Check frozen bytes against an independently retained manifest digest.

    Coordinator-only postflight, not execution isolation or a semantic verdict.
    Never discovers Git, executes the subject, follows links, or edits files.
    """
    if not isinstance(expected_manifest_sha256, str) or not re.fullmatch(
        r"[0-9a-f]{64}", expected_manifest_sha256
    ):
        raise ValueError("Expected a retained lowercase SHA-256 manifest digest")
    root = plain_path(packet)
    manifest_bytes = input_file(root, "manifest.json").read_bytes()
    if hashlib.sha256(manifest_bytes).hexdigest() != expected_manifest_sha256:
        raise ValueError("Manifest differs from the retained pre-run digest")
    manifest = json.loads(manifest_bytes)
    if not isinstance(manifest, dict):
        raise ValueError("Manifest must be an object")
    expected = manifest.get("files")
    if not isinstance(expected, dict) or not expected:
        raise ValueError("Manifest must enumerate files")
    actual = {}
    for name, digest in expected.items():
        if name == "manifest.json" or not isinstance(digest, str) or not re.fullmatch(
            r"[0-9a-f]{64}", digest
        ):
            raise ValueError("Invalid manifest file/digest")
        actual[name] = hashlib.sha256(input_file(root, name).read_bytes()).hexdigest()
    # Check links before descending rather than letting recursive traversal
    # follow a newly inserted junction to a foreign tree.
    observed = set()
    pending = [root]
    while pending:
        directory = pending.pop()
        for path in directory.iterdir():
            checked = plain_path(path)
            checked.relative_to(root)
            if checked.is_dir():
                pending.append(checked)
            elif checked.is_file():
                observed.add(checked.relative_to(root).as_posix())
            else:
                raise ValueError(f"Unsupported entry: {path.name}")
    extras = sorted(observed - set(expected) - {"manifest.json"})
    changed = sorted(name for name in expected if actual[name] != expected[name])
    if extras or changed:
        raise ValueError(f"Packet drift: extra={extras}, changed={changed}")
    return {"manifest_sha256": expected_manifest_sha256,
            "verified_files": actual, "extra_files": [], "byte_integrity": "pass"}


def prepare_case(case_id, output_parent, *, eval_root=EVAL_ROOT,
                 skill_root=SKILL_ROOT, with_skill=True, criteria_roots=()):
    """Create only a fresh child directory; never overwrite or delete a target."""
    root = plain_path(eval_root)
    cases = load_cases(root)
    if case_id not in cases:
        raise ValueError(f"Unknown case: {case_id}")
    parent = plain_path(output_parent)
    if not parent.is_dir():
        raise ValueError("Output parent must be an existing directory")
    criteria = [plain_path(path) for path in criteria_roots]
    names = [path.name for path in criteria]
    if len(set(names)) != len(names) or "independent-audit" in names:
        raise ValueError("Duplicate runtime skill name")
    for source in (root.parent, plain_path(skill_root), *criteria):
        if parent == source or source in parent.parents:
            raise ValueError("Output must be outside the source package")

    case = cases[case_id]
    payload = {}
    for relative in case["files"]:
        destination = PurePosixPath("inputs", *PurePosixPath(relative).parts[2:])
        payload[destination.as_posix()] = input_file(root, relative).read_bytes()
    if with_skill:
        payload.update(skill_snapshot(skill_root))
    for source in criteria:
        payload.update(skill_snapshot(source, source.name))
    payload["prompt.txt"] = (case["prompt"] + "\n").encode("utf-8")
    manifest = {
        "case_id": case_id,
        "files": {name: hashlib.sha256(data).hexdigest()
                  for name, data in sorted(payload.items())},
    }
    payload["manifest.json"] = (json.dumps(manifest, indent=2) + "\n").encode("utf-8")

    packet = Path(tempfile.mkdtemp(prefix=f"audit-{case_id}-", dir=parent)).resolve()
    if packet.parent != parent:
        raise ValueError("Unexpected allocated directory; refusing writes")
    # On an I/O failure retain the partial private packet for inspection.
    # There is intentionally no delete/reset/overwrite path.
    for relative, data in sorted(payload.items()):
        destination = packet.joinpath(*PurePosixPath(relative).parts)
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("xb") as stream:
            stream.write(data)
    return packet


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case_id", type=int)
    parser.add_argument("--output-parent", required=True, type=Path)
    parser.add_argument("--skill-root", type=Path, default=SKILL_ROOT)
    parser.add_argument("--without-skill", action="store_true")
    parser.add_argument("--criteria-skill", action="append", type=Path, default=[],
                        help="Explicit frozen criteria skill root; repeat as needed")
    args = parser.parse_args()
    try:
        packet = prepare_case(
            args.case_id, args.output_parent, skill_root=args.skill_root,
            with_skill=not args.without_skill,
            criteria_roots=args.criteria_skill,
        )
    except (OSError, ValueError, KeyError, TypeError) as exc:
        parser.exit(1, f"Cannot prepare audit packet: {exc}\n")
    print(packet)


if __name__ == "__main__":
    main()
