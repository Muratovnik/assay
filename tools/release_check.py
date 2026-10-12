"""Run a release command from whichever interpreter started the release tool.

The release tool runs project checks and the smoke with its own Python, which
does not carry this repository's tooling. Its contract leaves dependencies to
the project, so this entry point builds an environment from the pinned
`requirements-tools.txt`, rebuilds it when that file changes, and runs the
command there. Without arguments it runs `check.py --all` in the ignored
`.cache/tools-env`; the smoke names its own environment under the release
tool's scratch directory, because its Git-free snapshot has no ignored files.
Nothing is installed anywhere else.
"""
from __future__ import annotations

import argparse
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
CHECK_ALL = ["tools/check.py", "--all"]


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


def linked(path: Path) -> bool:
    return path.exists() and (path.is_symlink()
                              or getattr(path.lstat(), "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT)


def provision(environment: Path, digest: str) -> None:
    # The environment is deleted before a rebuild, so neither it nor a parent
    # inside this repository may be a link that would redirect the deletion.
    inside = environment.is_relative_to(ROOT)
    for path in (environment, *environment.parents):
        if inside and path == ROOT:
            break
        if linked(path):
            raise SystemExit(f"release check: refusing a linked tooling environment path: {path}")
        if not inside:
            break
    if environment.exists():
        shutil.rmtree(environment)
    subprocess.run([sys.executable, "-m", "venv", str(environment)], check=True)
    subprocess.run([str(interpreter(environment)), "-m", "pip", "install", "--disable-pip-version-check",
                    "--quiet", "-r", str(REQUIREMENTS)], check=True)
    (environment / STAMP).write_text(digest + "\n", "utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--environment", type=Path, default=ENVIRONMENT,
                        help="tooling environment to build or reuse (default: .cache/tools-env)")
    parser.add_argument("command", nargs=argparse.REMAINDER,
                        help="arguments for the environment's Python after --; default: tools/check.py --all")
    arguments = parser.parse_args(argv)
    command = arguments.command[1:] if arguments.command[:1] == ["--"] else arguments.command
    environment = arguments.environment.resolve()
    digest = requirements_digest()
    if not current(environment, digest):
        provision(environment, digest)
    return subprocess.run([str(interpreter(environment)), "-B", *(command or CHECK_ALL)],
                          cwd=ROOT, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
