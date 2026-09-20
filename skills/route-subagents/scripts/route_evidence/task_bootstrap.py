"""Pinned public corpus acquisition, separate from bounded local retrieval."""
from __future__ import annotations

import atexit
from contextlib import nullcontext
import hashlib
import json
from pathlib import Path, PurePosixPath
import sys
import tarfile
import tempfile
import threading
import time
import urllib.request

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from route_evidence.cache import atomic_write, source_lock
from route_evidence.core import EvidenceError, digest, encoded
from route_evidence.history import _refuse_link_ancestors
from route_evidence.processes import ProcessScope

SETUP_SECONDS = 180
RETRY_SECONDS = 300
MAX_DOWNLOAD = 2 * 1024**3
MAX_EXPANDED = 8 * 1024**3
MAX_MEMBER = 64 * 1024**2


def source_definition():
    return json.loads(Path(__file__).with_name("task_source.json").read_text(encoding="utf-8"))


class LimitedReader:
    def __init__(self, response):
        self.response, self.total = response, 0

    def read(self, size):
        raw = self.response.read(size)
        self.total += len(raw)
        if self.total > MAX_DOWNLOAD:
            raise EvidenceError("download_size_limit")
        return raw


def acquire(definition, directory):
    """Stream a release; verify selected bytes before parsing, never extract tar paths."""
    expected, seen = definition["members"], set()
    request = urllib.request.Request(definition["url"], headers={"User-Agent": "Assay-task-evidence"})
    with urllib.request.urlopen(request, timeout=30) as response:
        if not response.geturl().startswith("https://"):
            raise EvidenceError("insecure_source_redirect")
        with tarfile.open(fileobj=LimitedReader(response), mode="r|gz") as archive:
            expanded = 0
            for member in archive:
                expanded += member.size
                if expanded > MAX_EXPANDED:
                    raise EvidenceError("archive_size_limit")
                if member.name not in expected:
                    continue
                parts = PurePosixPath(member.name).parts
                if (not member.isfile() or member.size > MAX_MEMBER or member.name in seen
                        or ".." in parts or "\\" in member.name or ":" in member.name
                        or PurePosixPath(member.name).is_absolute()):
                    raise EvidenceError("invalid_source_member")
                with archive.extractfile(member) as stream:
                    raw = stream.read(MAX_MEMBER + 1)
                if hashlib.sha256(raw).hexdigest() != expected[member.name]["sha256"]:
                    raise EvidenceError("source_checksum_mismatch")
                rows = json.loads(raw)["records"]
                if len(rows) != expected[member.name]["rows"]:
                    raise EvidenceError("source_row_count_mismatch")
                # Retain only importer inputs, not model outputs or grading material.
                trimmed = [{**{k: r[k] for k in ("index", "score", "cost", "prompt_tokens", "completion_tokens") if k in r},
                            "origin_query": r.get("origin_query") or r.get("prompt")} for r in rows]
                target = directory / "livecodebench" / parts[-2]
                target.mkdir(parents=True, exist_ok=True)
                (target / "results.json").write_bytes(encoded({"records": trimmed}))
                seen.add(member.name)
                if seen == set(expected):
                    break
    if seen != set(expected):
        raise EvidenceError("incomplete_source_release")


def state_path(evidence):
    path = evidence.root / "acquisition.json"
    _refuse_link_ancestors(path)
    return path


def save_state(evidence, status, reason=None):
    value = {"status": status, "updated_at": time.time()}
    if reason:
        value["reason"] = reason
    if status == "failed":
        value["retry_at"] = time.time() + RETRY_SECONDS
    atomic_write(state_path(evidence), value)
    return value


def provision(evidence, definition=None, directory=None):
    definition = definition or source_definition()
    _refuse_link_ancestors(evidence.root)
    evidence.root.mkdir(parents=True, exist_ok=True)
    lock = evidence.root / "acquisition.lock"
    _refuse_link_ancestors(lock)
    with source_lock(lock) as acquired:
        if not acquired:
            return {"status": "downloading"}
        if evidence.load() is not None:
            return {"status": "ready"}
        save_state(evidence, "downloading")
        try:
            from route_evidence.task_import import llmrouterbench
            workspace = (nullcontext(directory) if directory is not None else
                         tempfile.TemporaryDirectory(prefix="download-", dir=evidence.root))
            with workspace as temp:
                acquire(definition, Path(temp))
                corpus = llmrouterbench(Path(temp), definition["manifest"])
            if len(corpus["records"]) != definition["tasks"]:
                raise EvidenceError("source_task_count_mismatch")
            # Same query-deduplicated split as offline evaluation; never train on holdout.
            keys = sorted({digest(r["query"].strip().casefold()) for r in corpus["records"]})
            train = set(keys[::2])
            corpus["records"] = [r for r in corpus["records"] if digest(r["query"].strip().casefold()) in train]
            if len(corpus["records"]) != definition["installed_tasks"]:
                raise EvidenceError("source_split_mismatch")
            result = evidence.install(corpus, replace=False)
            return {**save_state(evidence, "ready"), "tasks": result["tasks"]}
        except Exception as exc:
            # No remote body, paths, or raw exception strings enter routing context.
            reason = str(exc) if isinstance(exc, EvidenceError) and str(exc) in {
                "source_checksum_mismatch", "incomplete_source_release", "source_row_count_mismatch",
                "source_task_count_mismatch", "source_split_mismatch", "invalid_source_member",
                "download_size_limit", "archive_size_limit", "insecure_source_redirect"} else "download_or_import_failed"
            return save_state(evidence, "failed", reason)


def setup(evidence, *, offline=False, automatic=False, scope=None):
    """Explicit setup waits; automatic retries honor persisted cooldown and opt-out."""
    try:
        existing = evidence.load()
        if existing is not None:
            return {"status": "ready", "tasks": len(existing["corpus"]["records"])}
        state = CorpusProvisioner(evidence, offline=offline).status()
        if offline:
            return {"status": "missing_offline"}
        if automatic and (not evidence.config["enabled"] or not evidence.config["auto_download"]
                          or state["status"] == "failed"):
            return state
        _refuse_link_ancestors(evidence.root)
        evidence.root.mkdir(parents=True, exist_ok=True)
        scope = scope or ProcessScope(SETUP_SECONDS)
        try:
            # Parent owns scratch so worker cancellation cannot strand partial downloads.
            with tempfile.TemporaryDirectory(prefix="download-", dir=evidence.root) as temp:
                raw = scope.run([sys.executable, "-B", str(Path(__file__).resolve())],
                    encoded({"root": str(evidence.cache_root.resolve()), "directory": temp}))
                result = json.loads(raw)
                if result.get("status") not in {"ready", "downloading", "failed"}:
                    raise EvidenceError("invalid_setup_result")
                return result
        finally:
            scope.cancel()
    except (OSError, ValueError, EvidenceError):
        if evidence.root.exists():
            return save_state(evidence, "failed", "setup_interrupted_or_invalid_cache")
        return {"status": "failed", "reason": "invalid_local_corpus_state"}


class CorpusProvisioner:
    """Own one cancellable background download per connection; OS lock spans clients."""
    def __init__(self, evidence, *, offline=False):
        self.evidence, self.offline = evidence, offline
        self.thread = self.scope = None
        self.wait = False
        self.lock = threading.Lock()

    def status(self):
        e = self.evidence
        if not e.config["enabled"]:
            return {"status": "disabled"}
        try:
            path = e.root / "corpus.json"
            _refuse_link_ancestors(path)
            if path.exists():
                # Full validation remains inside the retrieval deadline.
                return {"status": "present"}
            if self.offline:
                return {"status": "missing_offline", "reason": "run_task_setup_online"}
            if not e.config["auto_download"]:
                return {"status": "missing", "reason": "automatic_download_disabled"}
            path = state_path(e)
            if path.exists() and path.stat().st_size < 4096:
                state = json.loads(path.read_text(encoding="utf-8"))
                if not isinstance(state, dict):
                    raise EvidenceError("invalid_acquisition_state")
                if state.get("status") == "failed" and state.get("retry_at", 0) > time.time():
                    return {"status": "failed", "reason": state.get("reason", "download_failed"), "retry_at": state["retry_at"]}
                if state.get("status") == "downloading" and state.get("updated_at", 0) + SETUP_SECONDS > time.time():
                    return {"status": "downloading"}
            return {"status": "missing"}
        except (OSError, ValueError, TypeError, EvidenceError):
            return {"status": "failed", "reason": "invalid_local_corpus_state"}

    def _run(self):
        setup(self.evidence, offline=self.offline, automatic=True, scope=self.scope)

    def ensure(self):
        with self.lock:
            state = self.status()
            if state["status"] != "missing" or self.offline or not self.evidence.config["auto_download"]:
                return state
            if self.thread and self.thread.is_alive():
                return {"status": "downloading"}
            _refuse_link_ancestors(self.evidence.root)
            self.evidence.root.mkdir(parents=True, exist_ok=True)
            self.scope = ProcessScope(SETUP_SECONDS)
            if self.wait:
                return setup(self.evidence, offline=self.offline, automatic=True, scope=self.scope)
            self.thread = threading.Thread(target=self._run, daemon=True)
            atexit.register(self.close)
            self.thread.start()
            return {"status": "downloading"}

    def close(self):
        if self.scope:
            self.scope.cancel()
        if self.thread:
            self.thread.join(timeout=5)
        atexit.unregister(self.close)


if __name__ == "__main__":
    from route_evidence.task_evidence import TaskEvidence
    request = json.loads(sys.stdin.buffer.read(16384))
    evidence = TaskEvidence(request["root"], {"enabled": True})
    directory = Path(request["directory"])
    _refuse_link_ancestors(directory)
    if directory.resolve().parent != evidence.root.resolve() or not directory.name.startswith("download-"):
        raise EvidenceError("invalid_download_workspace")
    print(json.dumps(provision(evidence, directory=directory)))
