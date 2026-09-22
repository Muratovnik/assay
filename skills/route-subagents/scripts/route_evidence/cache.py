"""Per-source lazy refresh, OS locks and atomic last-known-good snapshots."""
from __future__ import annotations

import math
import os
import re
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Callable

from .core import (EvidenceError, digest, encoded, epoch, timestamp, validate_guide,
                    validate_snapshot, read_document)

# One refresh mechanism serves both kinds of source; only the payload contract
# and the identity it must keep differ.
CONTRACTS = {"benchmark": (validate_snapshot, (("source_id", "id"), ("source_url", "url"),
                                               ("version", "version"), ("benchmark", "benchmark"))),
             "guide": (validate_guide, (("guide_id", "id"), ("source_url", "url"),
                                        ("extractor_version", "extractor_version")))}


# A bounded history survives reconnects. A new inventory can bypass TTL once,
# but cannot turn successive requests into an unbounded source poller.
MAX_INVENTORY_KEYS = 256
INVENTORY_REFRESH_INTERVAL = 300


def checked_inventory_keys(value, limit=100):
    if (not isinstance(value, (list, tuple)) or len(value) > limit
            or any(not isinstance(k, str) or not re.fullmatch(r"[0-9a-f]{64}", k) for k in value)
            or len(set(value)) != len(value)):
        raise EvidenceError("invalid inventory refresh keys")
    return set(value)


def contract(source: dict):
    kind = source.get("kind", "benchmark")
    if kind not in CONTRACTS:
        raise EvidenceError("unknown source kind: " + str(kind))
    return CONTRACTS[kind]


class FetchError(EvidenceError):
    def __init__(self, message: str, retry_after: float = 0):
        super().__init__(message)
        self.retry_after = retry_after


@contextmanager
def source_lock(path: Path):
    # OS locks are released on process death; never delete a lock file whose
    # inode may still be held by another process. Also works on native Windows.
    with path.open("a+b") as handle:
        if handle.tell() == 0:
            handle.write(b"0")
            handle.flush()
        handle.seek(0)
        acquired = False
        try:
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            acquired = True
        except OSError:
            pass
        try:
            yield acquired
        finally:
            if acquired:
                handle.seek(0)
                if os.name == "nt":
                    import msvcrt
                    msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(handle, fcntl.LOCK_UN)


def atomic_write(path: Path, value: dict):
    fd, name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as output:
            output.write(encoded(value))
            output.flush()
            os.fsync(output.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


class Cache:
    def __init__(self, root: Path, *, ttl: float = 86400, retry_base: float = 300,
                 clock: Callable[[], float] = time.time):
        if not math.isfinite(ttl) or not math.isfinite(retry_base) or ttl <= 0 or retry_base <= 0:
            raise EvidenceError("TTL and retry delay must be positive")
        self.root, self.ttl, self.retry_base, self.clock = root, ttl, retry_base, clock
        root.mkdir(parents=True, exist_ok=True)

    def read(self, source: dict) -> dict:
        path = self.root / (source["id"] + ".json")
        try:
            state = read_document(path)
            if (not isinstance(state, dict) or state.get("cache_schema") != 1
                    or state.get("source_fingerprint") != digest(source)):
                raise EvidenceError("cache schema or source definition changed")
            if state.get("snapshot") is not None:
                validate, identity = contract(source)
                state["snapshot"] = validate(state["snapshot"])
                if any(state["snapshot"][k] != source[v] for k, v in identity):
                    raise EvidenceError("cached source identity mismatch")
                if digest(state["snapshot"]) != state.get("data_hash"):
                    raise EvidenceError("cached data checksum mismatch")
            for key in ("last_attempt_at", "last_success_at", "data_changed_at", "next_retry_at", "inventory_probe_after"):
                if state.get(key) is not None:
                    epoch(state[key])
            if type(state.get("failures", 0)) is not int or state.get("failures", 0) < 0:
                raise EvidenceError("invalid cache failure count")
            if not isinstance(state.get("validators", {}), dict):
                raise EvidenceError("invalid cache validators")
            checked_inventory_keys(state.get("inventory_checked", []), MAX_INVENTORY_KEYS)
            return state
        except FileNotFoundError:
            return {}
        except (EvidenceError, OSError, UnicodeError):
            # No partial salvage of unvalidated data. Online calls may recover.
            return {"error": "invalid_cache", "snapshot": None}

    def view(self, source: dict, state: dict, **extra) -> dict:
        now = self.clock()
        success = state.get("last_success_at")
        age = now - epoch(success) if success else None
        # A clock moving backwards cannot make old data indefinitely fresh.
        stale = age is None or age < 0 or age >= self.ttl
        return {"source_id": source["id"], "source_url": source["url"],
                "kind": source.get("kind", "benchmark"),
                "availability": "missing" if state.get("snapshot") is None else "stale" if stale else "fresh",
                "stale": stale, "cache_age_seconds": age,
                "last_attempt_at": state.get("last_attempt_at"),
                "last_success_at": success, "data_changed_at": state.get("data_changed_at"),
                "source_updated_at": (state.get("snapshot") or {}).get("source_updated_at"),
                "next_retry_at": state.get("next_retry_at"),
                "error": state.get("error"), "snapshot": state.get("snapshot"), **extra}

    def get(self, source: dict, fetch: Callable, *, offline=False, force=False,
            inventory_keys=()) -> dict:
        requested = checked_inventory_keys(inventory_keys)

        def decision(state):
            current = self.view(source, state)
            unseen = requested - set(state.get("inventory_checked", []))
            probe_after = state.get("inventory_probe_after")
            deferred = bool(unseen and probe_after and self.clock() < epoch(probe_after))
            early = bool(unseen and not current["stale"] and not deferred)
            return current, early, deferred

        def cached(current, deferred):
            return {**current, "refresh": "inventory_deferred" if deferred else "cached",
                    **({"next_inventory_refresh_at": state.get("inventory_probe_after")}
                       if deferred else {})}

        state = self.read(source)
        current, early, deferred = decision(state)
        if offline:
            return {**current, "refresh": "offline"}
        retry_at = state.get("next_retry_at")
        # Explicit force and inventory probes both respect Retry-After/backoff.
        if retry_at and self.clock() < epoch(retry_at):
            return {**current, "refresh": "backoff"}
        if not force and not current["stale"] and not early:
            return cached(current, deferred)
        with source_lock(self.root / (source["id"] + ".lock")) as acquired:
            if not acquired:
                return self.view(source, self.read(source), refresh="update_in_progress")
            state = self.read(source)
            current, early, deferred = decision(state)
            retry_at = state.get("next_retry_at")
            if retry_at and self.clock() < epoch(retry_at):
                return {**current, "refresh": "backoff"}
            if not force and not current["stale"] and not early:
                return cached(current, deferred)
            if early:
                state["inventory_probe_after"] = timestamp(self.clock() + INVENTORY_REFRESH_INTERVAL)
            previous = state.get("snapshot")
            state.update(cache_schema=1, source_fingerprint=digest(source),
                         last_attempt_at=timestamp(self.clock()))
            if early:
                # Persist the probe lease before I/O: cancellation must not let
                # a reconnect bypass the throttle, nor claim a successful check.
                atomic_write(self.root / (source["id"] + ".json"), state)
            try:
                validators = state.get("validators", {}) if previous else {}
                snapshot, validators = fetch(source, validators)
                if snapshot is None:
                    if previous is None:
                        raise FetchError("304 without a validated cache")
                    snapshot = previous
                not_modified = snapshot is previous
                validate, identity = contract(source)
                snapshot = validate(snapshot)
                if any(snapshot[k] != source[v] for k, v in identity):
                    raise FetchError("source identity mismatch")
                data_hash = digest(snapshot)
                now = timestamp(self.clock())
                if data_hash != state.get("data_hash"):
                    state["data_changed_at"] = now
                state.update(snapshot=snapshot, data_hash=data_hash, validators=validators,
                             last_success_at=now, next_retry_at=None, error=None, failures=0)
                # A successful 200/304 checks the inventory even when the new
                # model is not published yet. Failures do not consume this check.
                old = sorted(set(state.get("inventory_checked", [])) - requested)
                state["inventory_checked"] = sorted(requested) + old[:MAX_INVENTORY_KEYS - len(requested)]
                action = "validated_not_modified" if not_modified else "updated"
            except (EvidenceError, OSError, TimeoutError) as exc:
                # Cancellation must not manufacture a publisher backoff.
                if str(exc) == "refresh_cancelled":
                    return self.view(source, self.read(source), refresh="cancelled")
                count = state.get("failures", 0) + 1
                delay = min(3600, self.retry_base * 2 ** min(count - 1, 8))
                delay = max(delay, min(86400, getattr(exc, "retry_after", 0)))
                state.update(snapshot=previous, failures=count,
                             # Don't persist response bodies, request headers or secrets.
                             error=f"{type(exc).__name__}: {str(exc)[:300]}",
                             next_retry_at=timestamp(self.clock() + delay))
                action = "failed"
            atomic_write(self.root / (source["id"] + ".json"), state)
            return self.view(source, state, refresh=action,
                             **({"refresh_reason": "inventory_changed"} if early else {}))
