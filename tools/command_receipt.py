"""Capture one explicitly authorized command, not an agent runtime or sandbox.

Outputs are private, potentially sensitive evidence. Never publish them by
default. A successful command is not an acceptance verdict.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import time
from typing import Any, Sequence


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_hashes(root: Path, inputs: Sequence[str]) -> dict[str, str]:
    result = {}
    for name in inputs:
        selected = root / name
        path = selected.resolve(strict=True)
        path.relative_to(root)
        if not path.is_file():
            raise ValueError(f"not an input file: {name}")
        # Revisit the caller's path after execution, including link retargets.
        # Canonical keys would silently keep observing a link's former target.
        result[selected.relative_to(root).as_posix()] = digest(path.read_bytes())
    return result


def write_json(path: Path, document: Any) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(document, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write("\n")


def capture(argv: Sequence[str], *, cwd: Path, output_parent: Path,
            inputs: Sequence[str], timeout: float = 120) -> tuple[Path, dict[str, Any]]:
    """Execute argv without a shell; retain failed launches and partial outputs.

    The caller owns permission checks, credentials and process descendants.
    Only the direct child is terminated on timeout; descendant state is unknown.
    This limitation is explicit in every timed-out receipt, not a clean result.
    """
    if (not argv or any(not isinstance(s, str) or not s or "\0" in s for s in argv)
            or not inputs or not 0 < timeout < float("inf")):
        raise ValueError("require argv, at least one source input and a finite positive timeout")
    cwd = cwd.resolve(strict=True)
    output_parent = output_parent.resolve(strict=True)
    if not cwd.is_dir() or not output_parent.is_dir():
        raise ValueError("cwd and output parent must be existing directories")
    before = file_hashes(cwd, inputs)
    packet = Path(tempfile.mkdtemp(prefix="command-", dir=output_parent))
    intent = {"schema": 1, "argv": list(argv), "cwd": str(cwd),
              "inputs_before": before, "timeout_seconds": timeout,
              "capture_scope": "one direct process, not all native tool calls",
              "started_unix_ns": time.time_ns()}
    write_json(packet / "intent.json", intent)
    result: dict[str, Any] = {"schema": 1, "state": "launch-error", "exit_code": None,
                              "error": None, "effects": "not-enforced"}
    start = time.monotonic()
    with (packet / "stdout.bin").open("xb") as out, (packet / "stderr.bin").open("xb") as err:
        try:
            process = subprocess.Popen(list(argv), cwd=cwd, stdin=subprocess.DEVNULL,
                                       stdout=out, stderr=err, shell=False)
            try:
                result["exit_code"] = process.wait(timeout=timeout)
                result["state"] = "completed" if process.returncode == 0 else "failed"
            except subprocess.TimeoutExpired:
                process.kill()
                result["exit_code"] = process.wait()
                result["state"] = "timeout"
                result["effects"] = "direct child killed; descendants and side effects unverified"
        except OSError as error:
            result["error"] = f"{type(error).__name__}: {error}"
    result["elapsed_seconds"] = time.monotonic() - start
    after: dict[str, str | None] = {}
    for name in before:
        try:
            after[name] = file_hashes(cwd, [name])[name]
        except (OSError, ValueError):
            after[name] = None
    result["inputs_after"] = after
    result["changed_inputs"] = [name for name in before if before[name] != after[name]]
    result["limits"] = ["No filesystem, credential or network isolation.",
                        "Equal final hashes do not exclude transient writes or outside reads.",
                        "Exit zero is not proof of a correct oracle or a complete native trace."]
    write_json(packet / "result.json", result)
    manifest = {name: digest((packet / name).read_bytes())
                for name in ("intent.json", "result.json", "stdout.bin", "stderr.bin")}
    write_json(packet / "manifest.json", manifest)
    result = {**result, "manifest_sha256": digest((packet / "manifest.json").read_bytes())}
    return packet, result


def verify(packet: Path, expected_digest: str) -> tuple[dict[str, Any], dict[str, Any]]:
    """Read a receipt only against the digest retained outside its directory."""
    if packet.is_symlink():
        raise ValueError("linked receipt directory")
    manifest_path = packet / "manifest.json"
    if manifest_path.is_symlink() or digest(manifest_path.read_bytes()) != expected_digest:
        raise ValueError("receipt manifest differs from retained digest")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected_names = {"intent.json", "result.json", "stdout.bin", "stderr.bin"}
    if not isinstance(manifest, dict) or set(manifest) != expected_names:
        raise ValueError("unexpected receipt inventory")
    if {p.name for p in packet.iterdir()} != expected_names | {"manifest.json"}:
        raise ValueError("receipt has unexpected files")
    for name, value in manifest.items():
        path = packet / name
        if path.is_symlink() or not path.is_file() or digest(path.read_bytes()) != value:
            raise ValueError(f"receipt drift: {name}")
    return (json.loads((packet / "intent.json").read_text(encoding="utf-8")),
            json.loads((packet / "result.json").read_text(encoding="utf-8")))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true", help="authorize this one command")
    parser.add_argument("--cwd", type=Path, required=True)
    parser.add_argument("--output-parent", type=Path, required=True)
    parser.add_argument("--input", action="append", required=True, dest="inputs")
    parser.add_argument("--timeout", type=float, default=120)
    parser.add_argument("argv", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    argv = args.argv[1:] if args.argv[:1] == ["--"] else args.argv
    if not args.execute:
        print(json.dumps({"state": "not-run", "argv": argv}, ensure_ascii=False))
        return 0
    try:
        packet, result = capture(argv, cwd=args.cwd, output_parent=args.output_parent,
                                 inputs=args.inputs, timeout=args.timeout)
    except (OSError, ValueError) as error:
        parser.exit(2, f"receipt: {error}\n")
    print(json.dumps({"packet": str(packet), **result}, ensure_ascii=False, indent=2))
    return 0 if result["state"] == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
