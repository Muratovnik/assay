"""Run a release command from whichever interpreter started the release tool.

The release tool runs project checks and the smoke with its own Python, which
does not carry this repository's tooling. Its contract leaves dependencies to
the project, so this entry point builds an environment from the pinned
`requirements-tools.txt`, rebuilds it when that file changes, and runs the
command there. Without arguments it runs `check.py --all` in the ignored
`.cache/tools-env`; the smoke names its own environment under the release
tool's scratch directory, because its Git-free snapshot has no ignored files.
Nothing is installed anywhere else.

The environment is built from the interpreter named by ASSAY_TOOLS_PYTHON, or
else the one running this script, and takes prebuilt wheels only: a Python the
pinned requirements publish no wheel for is refused in one line, instead of
compiling a native extension on a machine that may have no compiler.
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
PYTHON_VARIABLE = "ASSAY_TOOLS_PYTHON"
MINIMUM_PYTHON = (3, 11)
VERSION_PROBE = "import sys; print('%d.%d.%d' % sys.version_info[:3])"


def interpreter(environment: Path) -> Path:
    if os.name == "nt":
        return environment / "Scripts" / "python.exe"
    return environment / "bin" / "python"


def requirements_digest(requirements: tuple[Path, ...] = (REQUIREMENTS,)) -> str:
    # pip installs the union of the files, so their bytes in order identify
    # the environment; one file hashes as it always has, keeping old stamps.
    return hashlib.sha256(b"".join(path.read_bytes() for path in requirements)).hexdigest()


def current(environment: Path, digest: str) -> bool:
    """Whether the environment was built from these exact requirements."""
    stamp = environment / STAMP
    return interpreter(environment).is_file() and stamp.is_file() and stamp.read_text("utf-8").strip() == digest


def linked(path: Path) -> bool:
    return path.exists() and (path.is_symlink()
                              or getattr(path.lstat(), "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT)


def refuse(reason: str) -> SystemExit:
    return SystemExit(f"release check: {reason}")


def base_interpreter() -> tuple[str, str]:
    """The interpreter that builds the environment, and its version.

    The pinned requirements decide which Pythons they support by the wheels
    they publish, so a version this script accepts can still be refused later
    when the wheels are fetched.
    """
    python = os.environ.get(PYTHON_VARIABLE) or sys.executable
    try:
        probe = subprocess.run([python, "-c", VERSION_PROBE], capture_output=True, text=True, check=False)
    except OSError as error:
        raise refuse(f"cannot run {python} named by {PYTHON_VARIABLE}: {error}") from error
    version = probe.stdout.strip()
    try:
        numbers = tuple(int(part) for part in version.split("."))
    except ValueError:
        numbers = ()
    if probe.returncode or len(numbers) != 3:
        raise refuse(f"cannot read the version of {python}")
    if numbers[:2] < MINIMUM_PYTHON:
        raise refuse(f"Python {version} ({python}) is older than {'.'.join(map(str, MINIMUM_PYTHON))}, "
                     f"which the tooling needs; name another with {PYTHON_VARIABLE}")
    return python, version


def last_error(output: str) -> str:
    lines = [line.strip() for line in output.splitlines() if line.strip()]
    errors = [line for line in lines if line.startswith("ERROR:")]
    return (errors or lines or ["pip failed without output"])[-1]


def provision(environment: Path, digest: str, requirements: tuple[Path, ...] = (REQUIREMENTS,)) -> None:
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
    python, version = base_interpreter()
    if environment.exists():
        # Only an environment this script built is replaced. A directory
        # without its stamp belongs to something else and may be in use:
        # deleting it would break whatever runs from it.
        if not (environment / STAMP).is_file():
            raise refuse(f"{environment} exists and was not built by this script (it has no {STAMP}); "
                         "remove it yourself or name another directory with --environment")
        shutil.rmtree(environment)
    subprocess.run([python, "-m", "venv", str(environment)], check=True)
    # Stamped before the install, so an interrupted build is still this
    # script's to replace; it is not current until the digest is written.
    (environment / STAMP).write_text("building\n", "utf-8")
    files = [argument for path in requirements for argument in ("-r", str(path))]
    installed = subprocess.run([str(interpreter(environment)), "-m", "pip", "install", "--disable-pip-version-check",
                                "--quiet", "--only-binary", ":all:", *files],
                               capture_output=True, text=True, check=False)
    if installed.returncode:
        shutil.rmtree(environment, ignore_errors=True)
        names = ", ".join(path.name for path in requirements)
        raise refuse(f"cannot install {names} as prebuilt wheels for Python {version} ({python}): "
                     f"{last_error(installed.stdout + installed.stderr)}; "
                     f"name a Python they support with {PYTHON_VARIABLE}")
    (environment / STAMP).write_text(digest + "\n", "utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--environment", type=Path, default=ENVIRONMENT,
                        help="tooling environment to build or reuse (default: .cache/tools-env)")
    parser.add_argument("--requirements", type=Path, action="append",
                        help="requirements file to build from, relative to the repository; "
                             "repeat for several (default: requirements-tools.txt)")
    parser.add_argument("command", nargs=argparse.REMAINDER,
                        help="arguments for the environment's Python after --; default: tools/check.py --all")
    arguments = parser.parse_args(argv)
    command = arguments.command[1:] if arguments.command[:1] == ["--"] else arguments.command
    environment = arguments.environment.resolve()
    requirements = tuple(ROOT / path for path in arguments.requirements or [REQUIREMENTS])
    digest = requirements_digest(requirements)
    if not current(environment, digest):
        provision(environment, digest, requirements)
    return subprocess.run([str(interpreter(environment)), "-B", *(command or CHECK_ALL)],
                          cwd=ROOT, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
