"""Classify a bounded deterministic CLI reproducer for git bisect run.

Only a successful invocation matching independently justified known-good or
known-bad stdout is classified. Setup failures, novel output and timeouts skip
(exit 125), never pretend to identify the regression. This does not run Git.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

if __package__:
    from .command_receipt import capture
else:
    from command_receipt import capture


def classify(result: dict[str, Any], actual: bytes, good: bytes, bad: bytes) -> int:
    if good == bad:
        raise ValueError("good and bad controls must differ")
    if result.get("state") != "completed" or result.get("exit_code") != 0 or result.get("changed_inputs"):
        return 125
    if actual == good:
        return 0
    if actual == bad:
        return 1
    return 125


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--cwd", type=Path, required=True)
    parser.add_argument("--output-parent", type=Path, required=True)
    parser.add_argument("--good-stdout", type=Path, required=True)
    parser.add_argument("--bad-stdout", type=Path, required=True)
    parser.add_argument("--input", action="append", required=True, dest="inputs")
    parser.add_argument("argv", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    if not args.execute:
        print("not-run: a non-executed reproducer cannot mark a revision good", file=sys.stderr)
        return 125
    try:
        root = args.cwd.resolve(strict=True)
        controls = [(root / path).resolve(strict=True) for path in (args.good_stdout, args.bad_stdout)]
        for path in controls:
            path.relative_to(root)
        good, bad = (path.read_bytes() for path in controls)
        if good == bad:
            raise ValueError("good and bad controls must differ")
        argv = args.argv[1:] if args.argv[:1] == ["--"] else args.argv
        packet, result = capture(argv, cwd=root, output_parent=args.output_parent,
                                 inputs=[*args.inputs, *(str(p.relative_to(root)) for p in controls)])
        verdict = classify(result, (packet / "stdout.bin").read_bytes(), good, bad)
        print(json.dumps({"receipt": str(packet), "retain_externally": result["manifest_sha256"],
                          "bisect_exit": verdict, "meaning": {0: "known-good", 1: "known-bad", 125: "unclassified"}[verdict]}))
        return verdict
    except (OSError, ValueError) as error:
        print(f"reproducer unclassified: {error}", file=sys.stderr)
        return 125


if __name__ == "__main__":
    raise SystemExit(main())
