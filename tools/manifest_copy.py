"""Copy an installed tree by the manifest of the revision it was installed from.

A rollback snapshot taken before an install or upgrade needs the bytes the
client installed, not whatever else lies in that directory. A plugin cache can
carry a nested `.git`, and one that points at a checkout carries the
checkout's ignored evidence, earlier snapshots included. This tool reads the
file list of the installed revision from Git, copies exactly those paths from
the installed tree, records each one's Git blob hash and status, and lists
every other path it found without copying it. A link is recorded with its
destination and never followed.

Exit codes: 0 when the snapshot is written, whatever deviations it records;
2 when the revision, the installed tree or the output cannot be used.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import stat
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
TREE = "tree"
REPORT = "manifest.json"
# Git modes of what a checkout writes as a file or a link; a gitlink (160000)
# names another repository's commit and has no bytes here.
FILE_MODES = {"100644", "100755"}
LINK_MODE = "120000"


class UnusableInput(Exception):
    """The revision, the installed tree or the output cannot be used."""


def blob_id(data: bytes) -> str:
    """The Git object id of a blob with these bytes."""
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def linked(path: Path) -> bool:
    return path.is_symlink() or bool(getattr(path.lstat(), "st_file_attributes", 0)
                                     & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0))


def revision_manifest(repository: Path, revision: str) -> tuple[str, dict[str, tuple[str, str]]]:
    """The full commit id and {path: (mode, blob id)} of every file it tracks."""
    def git(*arguments: str) -> bytes:
        completed = subprocess.run(["git", "-C", str(repository), *arguments], capture_output=True, check=False)
        if completed.returncode:
            reason = completed.stderr.decode("utf-8", "replace").strip().splitlines()
            raise UnusableInput(f"git {arguments[0]}: {reason[-1] if reason else 'failed'}")
        return completed.stdout

    try:
        commit = git("rev-parse", "--verify", "--end-of-options", f"{revision}^{{commit}}").decode("ascii").strip()
        listing = git("ls-tree", "-r", "-z", "--full-tree", commit)
    except OSError as error:
        raise UnusableInput(f"cannot run git: {error}") from error
    entries: dict[str, tuple[str, str]] = {}
    for record in listing.decode("utf-8", "surrogateescape").split("\0"):
        if not record:
            continue
        header, path = record.split("\t", 1)
        mode, kind, object_id = header.split()
        if kind == "blob" and (mode in FILE_MODES or mode == LINK_MODE):
            entries[path] = (mode, object_id)
    if not entries:
        raise UnusableInput(f"revision {commit[:12]} tracks no files")
    return commit, entries


def unlisted_paths(source: Path, manifest: dict[str, tuple[str, str]]) -> list[dict[str, object]]:
    """Every path in source the manifest does not name, a foreign directory once."""
    listed = set(manifest)
    holders = {parent.as_posix() for name in listed for parent in PurePosixPath(name).parents}
    found: list[dict[str, object]] = []
    for current, directories, files in os.walk(source, followlinks=False):
        base = Path(current)
        kept = []
        for name in sorted(directories):
            path = base / name
            relative = path.relative_to(source).as_posix()
            if relative in listed:
                continue  # a tracked link to a directory; the copy step records it
            if linked(path) or relative not in holders:
                count = 0 if linked(path) else sum(len(names) for _, _, names in os.walk(path, followlinks=False))
                found.append({"path": relative + "/", "files": count, "link": linked(path)})
            else:
                kept.append(name)
        directories[:] = kept
        for name in sorted(files):
            relative = (base / name).relative_to(source).as_posix()
            if relative not in listed:
                found.append({"path": relative, "files": 1, "link": linked(base / name)})
    return found


def copy_by_manifest(repository: Path, revision: str, source: Path, output: Path) -> dict[str, object]:
    """Write output/tree and output/manifest.json; return the report."""
    if not source.is_dir() or linked(source):
        raise UnusableInput(f"installed tree is not a plain directory: {source}")
    source, output = source.resolve(), output.resolve()
    if output.exists():
        raise UnusableInput(f"output already exists: {output}")
    if output == source or output.is_relative_to(source):
        raise UnusableInput("output must lie outside the installed tree")
    commit, manifest = revision_manifest(repository, revision)
    files: list[dict[str, str]] = []
    links: dict[str, str] = {}
    for relative, (_, expected) in sorted(manifest.items()):
        path = source / relative
        if not os.path.lexists(path):
            files.append({"path": relative, "status": "missing", "expected": expected})
            continue
        if linked(path):
            links[relative] = os.readlink(path)
            continue
        if not path.is_file():
            files.append({"path": relative, "status": "not a file", "expected": expected})
            continue
        copy = output / TREE / relative
        copy.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, copy)
        actual = blob_id(copy.read_bytes())
        # A link a checkout wrote as a plain file holds its target as text,
        # which is the blob Git tracks for it.
        status = "same" if actual == expected else "changed"
        files.append({"path": relative, "status": status, "expected": expected, "actual": actual})
    report = {
        "revision": commit,
        "source": str(source),
        "files": files,
        "links": links,
        "unlisted": unlisted_paths(source, manifest),
    }
    output.mkdir(parents=True, exist_ok=True)
    (output / REPORT).write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", "utf-8")
    return report


def summary(report: dict[str, object]) -> str:
    counts: dict[str, int] = {}
    for entry in report["files"]:  # type: ignore[union-attr]
        counts[entry["status"]] = counts.get(entry["status"], 0) + 1
    unlisted = report["unlisted"]
    left = sum(entry["files"] for entry in unlisted)  # type: ignore[union-attr]
    parts = [f"{count} {status}" for status, count in sorted(counts.items())]
    parts.append(f"{len(report['links'])} links recorded")  # type: ignore[arg-type]
    parts.append(f"{len(unlisted)} unlisted paths ({left} files) not copied")  # type: ignore[arg-type]
    return f"manifest copy of {report['revision'][:12]}: " + ", ".join(parts)  # type: ignore[index]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--revision", required=True, help="commit or tag the tree was installed from")
    parser.add_argument("--source", type=Path, required=True, help="the installed tree, such as a plugin cache")
    parser.add_argument("--output", type=Path, required=True, help="new directory for the snapshot")
    parser.add_argument("--repository", type=Path, default=ROOT,
                        help="Git repository that holds the revision (default: this checkout)")
    arguments = parser.parse_args(argv)
    try:
        report = copy_by_manifest(arguments.repository, arguments.revision, arguments.source, arguments.output)
    except (UnusableInput, OSError) as error:
        print(f"manifest copy: {error}", file=sys.stderr)
        return 2
    print(summary(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
