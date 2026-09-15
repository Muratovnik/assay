"""Probe project-owned ESLint/TypeScript entrypoints; never install packages.

This records effective configuration and file selection, not CI execution or
product correctness. Use only authorized disposable projects for control files.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any, Sequence

if __package__:
    from .command_receipt import capture
else:
    from command_receipt import capture


def severity(value: Any) -> int:
    if isinstance(value, list):
        value = value[0] if value else None
    if type(value) is int and value in (0, 1, 2):
        return value
    if isinstance(value, str) and value in ("off", "warn", "error"):
        return {"off": 0, "warn": 1, "error": 2}[value]
    raise ValueError("invalid ESLint rule severity")


def diagnostic(report: Any, *, file: Path, rule: str) -> bool:
    if not isinstance(report, list) or len(report) != 1:
        raise ValueError("expected one ESLint file result")
    record = report[0]
    if not isinstance(record, dict) or Path(record.get("filePath", "")).resolve() != file:
        raise ValueError("ESLint result refers to a different file")
    messages = record.get("messages")
    if not isinstance(messages, list):
        raise ValueError("ESLint result has no messages")
    if any(not isinstance(m, dict) or m.get("fatal") for m in messages):
        raise ValueError("parser/setup failure is not rule detection")
    return any(m.get("ruleId") == rule and m.get("severity") == 2 for m in messages)


def probe(*, kind: str, node: str, entry: Path, root: Path, output_parent: Path,
          inputs: Sequence[str], file: str | None = None, rule: str | None = None,
          invalid: str | None = None, valid: str | None = None,
          project: str | None = None, required_files: Sequence[str] = (),
          timeout: float = 120) -> dict[str, Any]:
    root = root.resolve(strict=True)
    entry = entry.resolve(strict=True)
    if not entry.is_file():
        raise ValueError("entry must be the existing project's JS tool entrypoint")
    # Do not silently choose npx/latest or a different tool than the caller names.
    base = [node, str(entry)]
    receipts = []

    def run(arguments: list[str], selected_inputs: Sequence[str] = ()) -> tuple[str, int | None, str]:
        packet, result = capture(base + arguments, cwd=root, output_parent=output_parent,
                                 inputs=list(dict.fromkeys([*inputs, *selected_inputs])),
                                 timeout=timeout)
        receipts.append({"packet": str(packet), "manifest_sha256": result["manifest_sha256"],
                         "state": result["state"], "exit_code": result["exit_code"]})
        if result["state"] not in ("completed", "failed"):
            raise ValueError(f"tool {result['state']}; receipt retained at {packet}")
        if result["changed_inputs"]:
            raise ValueError(f"tool changed selected inputs; receipt retained at {packet}")
        return ((packet / "stdout.bin").read_text(encoding="utf-8"),
                result["exit_code"], str(packet))

    version, code, packet = run(["--version"])
    if code != 0 or not version.strip():
        raise ValueError(f"cannot identify tool version; receipt at {packet}")
    observations: dict[str, Any] = {"kind": kind, "entry": str(entry),
                                    "version_output": version.strip(), "receipts": receipts}
    if kind == "eslint":
        if not file or not rule or bool(invalid) != bool(valid):
            raise ValueError("ESLint requires file/rule and either both controls or neither")
        configurations = {}
        for name in dict.fromkeys([file, *([invalid, valid] if invalid and valid else [])]):
            path = (root / name).resolve(strict=True)
            path.relative_to(root)
            raw, code, packet = run(["--print-config", str(path)], [name])
            if code != 0:
                raise ValueError(f"print-config failed; receipt at {packet}")
            config = json.loads(raw)
            if not isinstance(config, dict) or not isinstance(config.get("rules"), dict):
                raise ValueError(f"file ignored or missing effective rules: {name}")
            configurations[name] = severity(config["rules"].get(rule, 0))
        observations.update({"rule": rule, "effective_severity": configurations,
                             "enforced_on_selected_paths": all(v == 2 for v in configurations.values()),
                             "control_detection": "not-run"})
        if invalid and valid:
            detections = {}
            for name in (invalid, valid):
                path = (root / name).resolve(strict=True)
                raw, code, packet = run(["--no-cache", "--format", "json", str(path)], [name])
                if code not in (0, 1):
                    raise ValueError(f"ESLint setup failure; receipt at {packet}")
                found = diagnostic(json.loads(raw), file=path, rule=rule)
                if found and code != 1:
                    raise ValueError("rule diagnostic and exit code disagree")
                detections[name] = found
                if name == valid and code != 0:
                    raise ValueError("valid control has other errors, not a clean permitted control")
            observations["control_detection"] = "pass" if detections[invalid] and not detections[valid] else "fail"
        observations["status"] = (
            "refuted" if not observations["enforced_on_selected_paths"] or observations["control_detection"] == "fail"
            else "observed" if invalid else "configuration-only"
        )
    elif kind == "tsc":
        if not project or not required_files:
            raise ValueError("TypeScript requires a project and required file paths")
        config, code, packet = run(["--project", project, "--showConfig"], [project, *required_files])
        if code != 0 or not isinstance(json.loads(config), dict):
            raise ValueError(f"showConfig failed; receipt at {packet}")
        raw, code, packet = run(["--project", project, "--listFilesOnly", "--pretty", "false"],
                               [project, *required_files])
        if code != 0:
            raise ValueError(f"file selection failed; receipt at {packet}")
        selected = {(root / line.strip()).resolve() for line in raw.splitlines() if line.strip()}
        missing = [name for name in required_files if (root / name).resolve(strict=True) not in selected]
        observations.update({"project": project, "missing_required_files": missing,
                             "status": "refuted" if missing else "selection-only"})
    else:
        raise ValueError(f"unknown tool kind: {kind}")
    observations["limits"] = (
        "Only selected files/configurations and named tool entrypoints. "
        "Print-config does not lint; listFilesOnly does not type-check. "
        "No claim of CI coverage, complete dependency identity or product acceptance."
    )
    return observations


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("kind", choices=["eslint", "tsc"])
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--node", default="node")
    parser.add_argument("--entry", required=True, type=Path)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--output-parent", required=True, type=Path)
    parser.add_argument("--input", required=True, action="append", dest="inputs")
    parser.add_argument("--file")
    parser.add_argument("--rule")
    parser.add_argument("--invalid")
    parser.add_argument("--valid")
    parser.add_argument("--project")
    parser.add_argument("--require-file", action="append", default=[], dest="required_files")
    args = vars(parser.parse_args())
    if not args.pop("execute"):
        print("not-run: use --execute only after reviewing command effects and control paths")
        return 0
    try:
        result = probe(**args)
    except (OSError, ValueError, TypeError) as error:
        print(f"quality scope: unverified: {error}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if result["status"] == "refuted" else 0


if __name__ == "__main__":
    raise SystemExit(main())
