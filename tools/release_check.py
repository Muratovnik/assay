"""Run every gate for a release from whichever interpreter started the release tool.

The release tool runs project checks with its own Python, which does not carry
this repository's tooling. Its contract leaves dependencies to the project, so
this entry point keeps them in an ignored environment under `.cache/tools-env`,
built from the pinned `requirements-tools.txt` and rebuilt when that file
changes, and runs `check.py --all` there. Nothing is installed anywhere else.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
ENVIRONMENT = ROOT / ".cache" / "tools-env"
REQUIREMENTS = ROOT / "requirements-tools.txt"
STAMP = "assay-requirements.sha256"


def interpreter(environment: Path) -> Path:
    if os.name == "nt":
        return environment / "Scripts" / "python.exe"
    return environment / "bin" / "python"


def requirements_digest() -> str:
    return hashlib.sha256(REQUIREMENTS.read_bytes()).hexdigest()


def current(environment: Path, digest: str) -> bool:
    """Whether the environment was built from these exact requirements."""
    stamp = environment / STAMP
    return interpreter(environment).is_file() and stamp.is_file() and stamp.read_text("utf-8").strip() == digest


def provision(environment: Path, digest: str) -> None:
    for path in (environment, *environment.parents):
        if path == ROOT:
            break
        if path.exists() and (path.is_symlink()
                              or getattr(path.lstat(), "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT):
            raise SystemExit(f"release check: refusing a linked tooling environment path: {path}")
    if environment.exists():
        shutil.rmtree(environment)
    subprocess.run([sys.executable, "-m", "venv", str(environment)], check=True)
    subprocess.run([str(interpreter(environment)), "-m", "pip", "install", "--disable-pip-version-check",
                    "--quiet", "-r", str(REQUIREMENTS)], check=True)
    (environment / STAMP).write_text(digest + "\n", "utf-8")


def main() -> int:
    digest = requirements_digest()
    if not current(ENVIRONMENT, digest):
        provision(ENVIRONMENT, digest)
    return subprocess.run([str(interpreter(ENVIRONMENT)), "-B", str(ROOT / "tools" / "check.py"), "--all"],
                          cwd=ROOT, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
