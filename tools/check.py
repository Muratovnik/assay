"""Run the source check, or with --all every gate this repository has.

One command that fails the way continuous integration fails is worth more than a
list in a README that each contributor runs a different subset of.
"""
from __future__ import annotations

import os
from pathlib import Path
import re
import subprocess
import sys

from assay import main

ROOT = Path(__file__).resolve().parents[1]
SCRATCH = Path(os.environ.get("AUDIT_EVAL_TEST_TMP", ROOT / ".cache" / "audit-eval-tests"))

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
)


UNITTEST = ("-m", "unittest")
# unittest's closing summary on stderr: "Ran 3 tests in 0.01s", then
# "OK (skipped=1)" or "FAILED (failures=1, skipped=1)".
RAN = re.compile(r"^Ran (\d+) tests? in ", re.MULTILINE)
SKIPPED = re.compile(r"\bskipped=(\d+)")


def verdict(arguments: tuple[str, ...], completed: subprocess.CompletedProcess[str]) -> tuple[bool, str]:
    """Whether a finished gate passed, and the status its line shows.

    A test suite's status names how many tests ran. One that ran none, or whose
    count is missing, inspected nothing and fails even on exit code 0, which
    interpreters before 3.12 return when discovery finds no tests.
    """
    passed = completed.returncode == 0
    status = "PASS" if passed else "FAIL"
    if arguments[:2] != UNITTEST:
        return passed, status
    counts = list(RAN.finditer(completed.stderr))
    ran = int(counts[-1].group(1)) if counts else 0
    if not ran:
        return False, "FAIL (no tests ran)"
    detail = f"{ran} test" if ran == 1 else f"{ran} tests"
    skipped = SKIPPED.search(completed.stderr, counts[-1].end())
    if skipped:
        detail += f", {skipped.group(1)} skipped"
    return passed, f"{status} ({detail})"


def run_all() -> int:
    """Run every gate, report each as it finishes, and fail if any failed.

    Gates run to completion rather than stopping at the first failure: one run
    that lists everything wrong beats five runs that each reveal one thing.
    Each line is flushed when its gate ends, so output redirected to a file
    shows progress during a run of several minutes rather than all at the end.
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
        passed, status = verdict(arguments, completed)
        print(f"{label:24} {status}", flush=True)
        if not passed:
            failed.append(label)
            output = (completed.stdout + completed.stderr).strip()
            if output:
                print("\n".join(f"    {line}" for line in output.splitlines()), flush=True)
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
