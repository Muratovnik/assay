"""Run the source check, or with --all every gate this repository has.

One command that fails the way continuous integration fails is worth more than a
list in a README that each contributor runs a different subset of.
"""
from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys

from assay import main

ROOT = Path(__file__).resolve().parents[1]
SCRATCH = ROOT / ".cache" / "audit-eval-tests"

GATES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("source check", ("tools/check.py",)),
    ("unit suite", ("-m", "unittest", "discover", "-s", "tools", "-p", "test_*.py")),
    ("compatibility fixture", ("tools/compatibility_fixture.py",)),
    ("catalog document", ("tools/catalog_docs.py", "--check")),
    ("evaluation data", ("tools/eval_assets.py", "check")),
    ("rendered client files", ("tools/assay.py", "render", "--check")),
    (
        "audit packets",
        (
            "-m", "unittest", "discover",
            "-s", "skills/independent-audit/evals",
            "-p", "test_prepare_case.py",
        ),
    ),
    (
        "preservation fixtures",
        (
            "-m", "unittest", "discover",
            "-s", "skills/technical-writing/evals",
            "-p", "test_text_check.py",
        ),
    ),
    (
        "revision diagnostics",
        (
            "-m", "unittest", "discover",
            "-s", "skills/text-writing/evals",
            "-p", "test_revision_check.py",
        ),
    ),
)


def run_all() -> int:
    """Run every gate, report each, and fail if any failed.

    Gates run to completion rather than stopping at the first failure: one run
    that lists everything wrong beats five runs that each reveal one thing.
    """
    SCRATCH.mkdir(parents=True, exist_ok=True)
    environment = dict(os.environ, AUDIT_EVAL_TEST_TMP=str(SCRATCH))
    failed: list[str] = []
    for label, arguments in GATES:
        completed = subprocess.run(
            [sys.executable, "-B", *arguments],
            cwd=ROOT,
            env=environment,
            capture_output=True,
            text=True,
            check=False,
        )
        status = "PASS" if completed.returncode == 0 else "FAIL"
        print(f"{label:24} {status}")
        if completed.returncode != 0:
            failed.append(label)
            output = (completed.stdout + completed.stderr).strip()
            if output:
                print("\n".join(f"    {line}" for line in output.splitlines()))
    print()
    if failed:
        print(f"check --all: FAILED ({', '.join(failed)})")
        return 1
    print("check --all: PASS")
    return 0


if __name__ == "__main__":
    if "--all" in sys.argv[1:]:
        raise SystemExit(run_all())
    raise SystemExit(main(["check"]))
