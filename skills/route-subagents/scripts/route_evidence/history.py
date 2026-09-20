"""Private routing telemetry, explicit log import, and offline policy replay.

The store owns one namespace and never searches for client logs.  Import callers
must name every input file; imported observations are returned to the caller and
are not persisted implicitly.
"""
from __future__ import annotations

import copy
import hashlib
import math
import re
import stat
import time
from pathlib import Path
from typing import Any, Callable

from .cache import atomic_write, source_lock
from .core import EvidenceError, encoded, epoch, loads, timestamp


HISTORY_SCHEMA = 1
NAMESPACE = "routing-advisor"
MODES = {"off", "metadata", "full"}
MAX_RECORD_BYTES = 2 * 1024 * 1024
MAX_PRUNE_FILES = 512
MAX_IMPORT_FILES = 64
MAX_IMPORT_LINES = 100_000
MAX_IMPORT_BYTES = 128 * 1024 * 1024
MAX_IMPORT_LINE_BYTES = 2 * 1024 * 1024
_DECISION_FILE = re.compile(r"^decision-([0-9a-f]{64})\.json$")
_OUTCOME_FILE = re.compile(
    r"^outcome-([0-9a-f]{64})-([0-9a-f]{64})-"
    r"(launched|completed|failed|interrupted|unknown)\.json$"
)
_EXECUTION_STATUSES = {"launched", "completed", "failed", "interrupted", "unknown"}
_TERMINAL_STATUSES = _EXECUTION_STATUSES - {"launched"}
_CODE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,199}$")
_FORBIDDEN_KEYS = {
    "answer", "code", "content", "cwd", "input", "message", "messages",
    "output", "path", "prompt", "raw", "response", "source_code", "task",
    "task_prompt", "task_text", "text", "transcript",
}
_EVIDENCE_TEXT_KEYS = {"content", "excerpt", "text"}
_EXECUTION_KEYS = {
    "status", "packet_id", "execution_ref", "requested", "observed",
    "requested_model", "requested_effort", "requested_service_tier",
    "observed_model", "observed_effort", "observed_service_tier",
    "actual_model", "actual_effort", "actual_service_tier", "usage",
    "usage_provenance", "outcome", "outcome_basis", "evidence", "evidence_refs",
    "cost_observation", "task_description",
}


def _identifier(value: Any, field: str) -> str:
    if not isinstance(value, str) or not _CODE.fullmatch(value):
        raise EvidenceError(f"{field}: expected a bounded identifier")
    return value


def _optional_identifier(value: Any, field: str) -> str | None:
    return None if value is None else _identifier(value, field)


def _safe_string(value: Any, field: str, *, limit: int = 300) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise EvidenceError(f"{field}: expected a nonempty bounded string")
    if any(ord(char) < 32 for char in value):
        raise EvidenceError(f"{field}: control characters are not allowed")
    return value.strip()


def _codes(values: Any, field: str) -> list[str]:
    if values is None:
        return []
    if not isinstance(values, list) or len(values) > 256:
        raise EvidenceError(f"{field}: expected a bounded list")
    return [_identifier(value, field) for value in values]


def _is_reparse(path: Path) -> bool:
    try:
        info = path.lstat()
    except FileNotFoundError:
        return False
    return path.is_symlink() or bool(
        getattr(info, "st_file_attributes", 0)
        & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    )


def _refuse_link_ancestors(path: Path) -> None:
    absolute = path.absolute()
    chain = [absolute]
    chain.extend(absolute.parents)
    for node in reversed(chain):
        if node.exists() and _is_reparse(node):
            raise EvidenceError("history root has a symlink or reparse-point ancestor")


def _record_key(decision_id: str) -> str:
    if not isinstance(decision_id, str):
        raise EvidenceError("decision_id must be a string")
    return hashlib.sha256(decision_id.encode("utf-8")).hexdigest()


def _file_parts(name: str) -> tuple[str, str, str | None, str | None] | None:
    match = _DECISION_FILE.fullmatch(name)
    if match:
        return "decision", match.group(1), None, None
    match = _OUTCOME_FILE.fullmatch(name)
    if match:
        return "outcome", match.group(1), match.group(2), match.group(3)
    return None


def _read_json(path: Path) -> dict:
    try:
        if path.is_symlink() or _is_reparse(path) or not path.is_file():
            raise EvidenceError("history record is not a regular file")
        if path.stat().st_size > MAX_RECORD_BYTES:
            raise EvidenceError("history record exceeds size limit")
        value = loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError) as exc:
        raise EvidenceError("history record is unreadable") from exc
    if not isinstance(value, dict):
        raise EvidenceError("history record must be an object")
    return value


def _evidence_refs(evidence: Any) -> list[str]:
    refs: list[str] = []
    values = evidence if isinstance(evidence, list) else [evidence]
    for value in values:
        if isinstance(value, str) and _CODE.fullmatch(value):
            refs.append(value)
        elif isinstance(value, dict):
            for key in ("evidence_id", "source_id", "id"):
                candidate = value.get(key)
                if isinstance(candidate, str) and _CODE.fullmatch(candidate):
                    refs.append(candidate)
                    break
    return list(dict.fromkeys(refs))[:256]


def _candidate(value: Any, field: str) -> dict:
    if not isinstance(value, dict):
        raise EvidenceError(f"{field}: expected an object")
    return {
        "candidate_id": _identifier(value.get("candidate_id"), field + ".candidate_id"),
        "model": _safe_string(value.get("model"), field + ".model"),
        "effort": _optional_identifier(value.get("effort"), field + ".effort"),
    }


def _packet_metadata(value: Any, field: str, candidates: list[dict], *, include_task_features=False) -> dict:
    if not isinstance(value, dict):
        raise EvidenceError(f"{field}: expected an object")
    excluded = value.get("excluded", [])
    if not isinstance(excluded, list) or len(excluded) > 256:
        raise EvidenceError(f"{field}.excluded: expected a bounded list")
    clean_excluded = []
    for index, item in enumerate(excluded):
        if not isinstance(item, dict):
            raise EvidenceError(f"{field}.excluded[{index}]: expected an object")
        clean_excluded.append({
            "candidate_id": _identifier(item.get("candidate_id"), "candidate_id"),
            "reasons": _codes(item.get("reasons"), "reasons"),
        })
    eligible = value.get("eligible", [])
    if not isinstance(eligible, list) or len(eligible) > 256:
        raise EvidenceError(f"{field}.eligible: expected a bounded list")
    baseline = value.get("baseline")
    if isinstance(baseline, dict):
        baseline = next((item["candidate_id"] for item in candidates
                         if item["model"] == baseline.get("model")
                         and item["effort"] == baseline.get("effort")), None)
    context = {}
    if include_task_features and "task_types" in value and "features" in value:
        from .advice_contracts import validate_packets
        packet = validate_packets([{k: value[k] for k in ("packet_id", "task_types", "features")}])[0]
        context = {k: packet[k] for k in ("task_types", "features")}
    return {
        **context,
        "packet_id": _identifier(value.get("packet_id"), field + ".packet_id"),
        "explicit": bool(value.get("explicit", False)),
        "baseline": _optional_identifier(baseline, field + ".baseline"),
        "eligible": [_identifier(item, field + ".eligible") for item in eligible],
        "excluded": clean_excluded,
    }


def _snapshot_metadata(snapshot: Any, *, include_task_features=False) -> dict:
    if not isinstance(snapshot, dict) or snapshot.get("schema_version") != 1:
        raise EvidenceError("snapshot: expected schema_version=1")
    candidates = snapshot.get("candidates")
    packets = snapshot.get("packets")
    if not isinstance(candidates, list) or not isinstance(packets, list):
        raise EvidenceError("snapshot: candidates and packets must be lists")
    if len(candidates) > 256 or len(packets) > 64:
        raise EvidenceError("snapshot: collection exceeds history limits")
    clean_candidates = [_candidate(value, "candidate") for value in candidates]
    result = {
        "schema_version": 1,
        "snapshot_id": _identifier(snapshot.get("snapshot_id"), "snapshot_id"),
        "client": _identifier(snapshot.get("client"), "client"),
        "inventory_hash": _identifier(snapshot.get("inventory_hash"), "inventory_hash"),
        "evidence_hash": _identifier(snapshot.get("evidence_hash"), "evidence_hash"),
        "policy_hash": _identifier(snapshot.get("policy_hash"), "policy_hash"),
        "candidates": clean_candidates,
        "packets": [_packet_metadata(value, "packet", clean_candidates, include_task_features=include_task_features) for value in packets],
        "evidence_refs": _evidence_refs(snapshot.get("evidence")),
    }
    for key in ("created_at", "expires_at"):
        value = snapshot.get(key)
        if value is not None:
            epoch(value)
            result[key] = value
    return result


def _ranking(value: Any, field: str) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list) or len(value) > 256:
        raise EvidenceError(f"{field}: expected a bounded list")
    clean = []
    for item in value:
        candidate_id = item.get("candidate_id") if isinstance(item, dict) else item
        clean.append(_identifier(candidate_id, field))
    return clean


def _result_metadata(result: Any) -> dict | None:
    if result is None:
        return None
    if not isinstance(result, dict) or result.get("schema_version") != 1:
        raise EvidenceError("advisor result: expected schema_version=1")
    rankings = result.get("rankings", [])
    if not isinstance(rankings, list) or len(rankings) > 64:
        raise EvidenceError("advisor result rankings must be a bounded list")
    clean_rankings = []
    for item in rankings:
        if not isinstance(item, dict):
            raise EvidenceError("advisor result ranking must be an object")
        probabilities = item.get("probabilities")
        if probabilities is not None:
            if not isinstance(probabilities, dict) or len(probabilities) > 256:
                raise EvidenceError("probabilities must be a bounded object")
            probabilities = {
                _identifier(key, "probability candidate"): _nonnegative(value, "probability")
                for key, value in probabilities.items()
            }
        confidence = item.get("confidence")
        if confidence is not None:
            confidence = _nonnegative(confidence, "confidence")
            if confidence > 1:
                raise EvidenceError("confidence must not exceed one")
        clean_rankings.append({
            "packet_id": _identifier(item.get("packet_id"), "packet_id"),
            "ranking": _ranking(item.get("ranking"), "ranking"),
            "ties": bool(item.get("ties", False)),
            "abstained": bool(item.get("abstained", False)),
            "reason_codes": _codes(item.get("reason_codes"), "reason_codes"),
            "probabilities": probabilities,
            "confidence": confidence,
        })
    return {
        "schema_version": 1,
        "snapshot_id": _identifier(result.get("snapshot_id"), "snapshot_id"),
        "backend": _identifier(result.get("backend"), "backend"),
        "requested_model": _optional_safe_string(result.get("requested_model"), "requested_model"),
        "resolved_model": _optional_safe_string(result.get("resolved_model"), "resolved_model"),
        "effort": _optional_identifier(result.get("effort"), "effort"),
        "rankings": clean_rankings,
    }


def _optional_safe_string(value: Any, field: str) -> str | None:
    return None if value is None else _safe_string(value, field)


def _decision(value: Any) -> dict:
    if not isinstance(value, dict):
        raise EvidenceError("decision must be an object")
    selected = value.get("selected")
    if selected is not None:
        selected = _candidate(selected, "selected")
    excluded = value.get("excluded", [])
    if not isinstance(excluded, list) or len(excluded) > 256:
        raise EvidenceError("decision excluded must be a bounded list")
    clean_excluded = []
    for item in excluded:
        if not isinstance(item, dict):
            raise EvidenceError("decision excluded item must be an object")
        clean_excluded.append({
            "candidate_id": _identifier(item.get("candidate_id"), "candidate_id"),
            "reasons": _codes(item.get("reasons"), "reasons"),
        })
    fallback = value.get("fallback")
    if isinstance(fallback, dict):
        selected = fallback.get("selected")
        fallback = {
            "status": _optional_identifier(fallback.get("status"), "fallback.status"),
            "selected": _candidate(selected, "fallback.selected") if selected is not None else None,
            "reason": _optional_identifier(fallback.get("reason"), "fallback.reason"),
        }
    elif fallback is not None:
        fallback = _identifier(fallback, "fallback")
    return {
        "packet_id": _identifier(value.get("packet_id"), "packet_id"),
        "status": _identifier(value.get("status"), "decision status"),
        "decision_type": _identifier(value.get("decision_type"), "decision type"),
        "selected": selected,
        "reason_codes": _codes(value.get("reason_codes"), "reason_codes"),
        "ranking": _ranking(value.get("ranking"), "ranking"),
        "excluded": clean_excluded,
        "fallback": fallback,
        "policy_hash": _optional_identifier(value.get("policy_hash"), "policy_hash"),
        "evidence_refs": _evidence_refs(value.get("evidence_refs")),
    }


def _redacted_json(value: Any, field: str = "full", *, allow_evidence_text: bool = False) -> Any:
    """Validate explicit diagnostic payloads without accepting prompt-like fields."""
    if value is None or isinstance(value, (bool, int)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise EvidenceError(f"{field}: non-finite number")
        return value
    if isinstance(value, str):
        return _safe_string(value, field, limit=65536 if allow_evidence_text else 1000)
    if isinstance(value, list):
        if len(value) > 512:
            raise EvidenceError(f"{field}: list exceeds limit")
        return [_redacted_json(item, field, allow_evidence_text=allow_evidence_text)
                for item in value]
    if isinstance(value, dict):
        if len(value) > 256:
            raise EvidenceError(f"{field}: object exceeds limit")
        clean = {}
        for key, item in value.items():
            if not isinstance(key, str) or not _CODE.fullmatch(key):
                raise EvidenceError(f"{field}: invalid field name")
            if (key.lower() in _FORBIDDEN_KEYS
                    and not (allow_evidence_text and key.lower() in _EVIDENCE_TEXT_KEYS)):
                raise EvidenceError(f"{field}: field {key} is not permitted in history")
            evidence_boundary = allow_evidence_text or (field == "snapshot" and key == "evidence")
            clean[key] = _redacted_json(item, field + "." + key,
                                        allow_evidence_text=evidence_boundary)
        return clean
    raise EvidenceError(f"{field}: unsupported JSON value")


def _full_payload(snapshot: dict, result: dict | None) -> dict:
    from .advice_contracts import validate_result, validate_routing_snapshot

    normalized_snapshot = validate_routing_snapshot(snapshot)
    normalized_result = (validate_result(normalized_snapshot, result)
                         if result is not None else None)
    clean_snapshot = _redacted_json(normalized_snapshot, "snapshot")
    snapshot_fields = {
        "schema_version", "snapshot_id", "created_at", "expires_at", "client",
        "packet_ids", "inventory_hash", "evidence_hash", "policy_hash", "candidates",
        "packets", "evidence", "policy",
    }
    clean_result = (_redacted_json(normalized_result, "advisor_result")
                    if normalized_result is not None else None)
    if clean_result is not None:
        result_fields = {
            "schema_version", "snapshot_id", "backend", "requested_model",
            "resolved_model", "effort", "rankings", "metadata",
        }
        clean_result = {key: value for key, value in clean_result.items()
                        if key in result_fields}
    return {
        "snapshot": {key: value for key, value in clean_snapshot.items()
                     if key in snapshot_fields},
        "advisor_result": clean_result,
    }


def _nonnegative(value: Any, field: str) -> int | float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise EvidenceError(f"{field}: expected a number")
    number = float(value)
    if not math.isfinite(number) or number < 0:
        raise EvidenceError(f"{field}: expected a nonnegative finite number")
    return int(number) if number.is_integer() else number


def _usage(value: Any, *, provenance: str | None = None) -> dict | None:
    if not isinstance(value, dict):
        return None
    aliases = {
        "input_tokens": ("input_tokens", "inputTokens"),
        "cached_input_tokens": ("cached_input_tokens", "cache_read_input_tokens", "cacheReadInputTokens"),
        "cache_creation_input_tokens": ("cache_creation_input_tokens", "cacheCreationInputTokens"),
        "output_tokens": ("output_tokens", "outputTokens"),
        "reasoning_output_tokens": ("reasoning_output_tokens", "reasoningOutputTokens"),
        "total_tokens": ("total_tokens", "totalTokens"),
    }
    clean: dict[str, Any] = {}
    for target, names in aliases.items():
        found = next((value[name] for name in names if value.get(name) is not None), None)
        if found is not None:
            clean[target] = _nonnegative(found, target)
    if not clean:
        return None
    # Claude reports cache creation/read beside uncached input.  The canonical
    # contract records all input once and keeps cached tokens as a subset.
    if ("input_tokens" in clean and "cached_input_tokens" in clean
            and any(key in value for key in ("cache_read_input_tokens", "cacheReadInputTokens"))):
        clean["input_tokens"] += clean["cached_input_tokens"]
    if ("input_tokens" in clean and "cache_creation_input_tokens" in clean
            and any(key in value for key in
                    ("cache_creation_input_tokens", "cacheCreationInputTokens"))):
        clean["input_tokens"] += clean["cache_creation_input_tokens"]
    if clean.get("cached_input_tokens", 0) > clean.get("input_tokens", math.inf):
        raise EvidenceError("cached input tokens must be a subset of input tokens")
    if clean.get("reasoning_output_tokens", 0) > clean.get("output_tokens", math.inf):
        raise EvidenceError("reasoning tokens must be a subset of output tokens")
    if "input_tokens" in clean and "output_tokens" in clean:
        clean["total_tokens"] = clean["input_tokens"] + clean["output_tokens"]
    clean["provenance"] = _identifier(provenance or "observed", "usage provenance")
    clean["pricing_usd"] = None
    clean["billed_quota"] = None
    return clean


def _route(execution: dict, prefix: str) -> dict:
    nested = execution.get(prefix)
    nested = nested if isinstance(nested, dict) else {}
    result = {}
    for field in ("model", "effort", "service_tier"):
        value = nested.get(field)
        if value is None:
            value = execution.get(prefix + "_" + field)
        if value is None and prefix == "observed":
            value = execution.get("actual_" + field)
        if value is not None:
            result[field] = (_safe_string(value, prefix + "." + field)
                             if field == "model" else _identifier(value, prefix + "." + field))
            result[field + "_provenance"] = prefix
    return result


def _outcome(execution: Any, *, retain_descriptions=False) -> dict:
    if not isinstance(execution, dict):
        raise EvidenceError("execution must be an object")
    unknown = set(execution) - _EXECUTION_KEYS
    if unknown:
        raise EvidenceError("execution contains unsupported fields")
    evidence_refs = _evidence_refs(execution.get("evidence_refs") or execution.get("evidence"))
    outcome = execution.get("outcome", "unknown")
    if isinstance(outcome, dict):
        evidence_refs = _evidence_refs(outcome.get("evidence_refs")) or evidence_refs
        basis = outcome.get("basis")
        outcome = outcome.get("status", "unknown")
    else:
        basis = execution.get("outcome_basis")
    outcome = _identifier(outcome, "outcome")
    if outcome == "accepted" and not evidence_refs:
        outcome = "unknown"
        basis = None
    status = _identifier(execution.get("status", "unknown"), "execution status")
    if status not in _EXECUTION_STATUSES:
        raise EvidenceError("unsupported execution status")
    result = {
        "status": status,
        "execution_ref": _optional_identifier(execution.get("execution_ref"), "execution_ref"),
        "requested": _route(execution, "requested"),
        "observed": _route(execution, "observed"),
        "usage": _usage(execution.get("usage"), provenance=execution.get("usage_provenance", "unknown")),
        "outcome": {
            "status": outcome,
            "basis": _optional_identifier(basis, "outcome basis"),
            "evidence_refs": evidence_refs,
        },
    }
    if "cost_observation" in execution:
        from .task_costs import validate_cost_observation
        if status == "launched":
            raise EvidenceError("chain cost requires a terminal receipt")
        result["cost_observation"] = validate_cost_observation(execution["cost_observation"])
    if "task_description" in execution:
        if not retain_descriptions:
            raise EvidenceError("task description retention requires explicit local opt-in")
        from .task_evidence import query_text
        result["task_description"] = query_text(execution["task_description"])
    return result


class HistoryStore:
    """Immutable per-decision telemetry records in a dedicated local namespace."""

    def __init__(self, root: Path, *, mode: str = "metadata", retention_days: int = 30,
                 clock: Callable[[], float] = time.time, retain_descriptions=False):
        if mode not in MODES:
            raise EvidenceError("telemetry mode must be off, metadata, or full")
        if (isinstance(retention_days, bool) or not isinstance(retention_days, int)
                or not 1 <= retention_days <= 3650):
            raise EvidenceError("retention_days must be an integer from 1 to 3650")
        self.root = Path(root) / NAMESPACE
        self.mode = mode
        self.retention_days = retention_days
        self.clock = clock
        self.retain_descriptions = retain_descriptions
        if mode != "off":
            _refuse_link_ancestors(self.root)
            self.root.mkdir(parents=True, exist_ok=True)
            _refuse_link_ancestors(self.root)

    def _path(self, decision_id: str, kind: str, status: str | None = None,
              attempt_key: str | None = None) -> Path:
        suffix = (f"-{attempt_key}-{status}"
                  if kind == "outcome" and status is not None and attempt_key is not None else "")
        return self.root / f"{kind}-{_record_key(decision_id)}{suffix}.json"

    def _base(self, decision_id: str, kind: str) -> dict:
        now = self.clock()
        if not isinstance(now, (int, float)) or not math.isfinite(now):
            raise EvidenceError("history clock returned an invalid value")
        return {
            "history_schema": HISTORY_SCHEMA,
            "namespace": NAMESPACE,
            "record_type": kind,
            "decision_id": _identifier(decision_id, "decision_id"),
            "created_at": timestamp(now),
            "expires_at": timestamp(now + self.retention_days * 86400),
            "privacy_mode": self.mode,
        }

    def _write_immutable(self, path: Path, record: dict) -> dict:
        _refuse_link_ancestors(self.root)
        if len(encoded(record)) > MAX_RECORD_BYTES:
            raise EvidenceError("history record exceeds size limit")
        with source_lock(self.root / ".write.lock") as acquired:
            if not acquired:
                raise EvidenceError("history write is already in progress")
            self._prune_locked()
            if path.exists():
                current = _read_json(path)
                if current == record:
                    return {**copy.deepcopy(current), "write_status": "unchanged"}
                # Timestamps differ on retries, so compare immutable semantic data.
                left = {key: value for key, value in current.items()
                        if key not in {"created_at", "expires_at"}}
                right = {key: value for key, value in record.items()
                         if key not in {"created_at", "expires_at"}}
                if left == right:
                    return {**copy.deepcopy(current), "write_status": "unchanged"}
                raise EvidenceError("conflicting immutable history record")
            atomic_write(path, record)
        return {**copy.deepcopy(record), "write_status": "written"}

    def write_decision(self, decision_id: str, snapshot: dict, result: dict | None,
                       decisions: list[dict], *, retrieval_seconds=None) -> dict:
        if self.mode == "off":
            return {"status": "disabled", "persisted": False}
        if not isinstance(decisions, list) or not decisions or len(decisions) > 64:
            raise EvidenceError("decisions must be a list with 1..64 items")
        metadata = _snapshot_metadata(snapshot, include_task_features="task_similarity_evidence" in snapshot.get("evidence", {}))
        advisor = _result_metadata(result)
        if advisor is not None and advisor["snapshot_id"] != metadata["snapshot_id"]:
            raise EvidenceError("advisor result snapshot_id does not match snapshot")
        record = self._base(decision_id, "decision")
        record.update(snapshot=metadata, advisor_result=advisor,
                      decisions=[_decision(value) for value in decisions])
        task = snapshot.get("evidence", {}).get("task_similarity_evidence")
        if task is not None:
            if retrieval_seconds is not None:
                from .core import number
                number(retrieval_seconds, "retrieval_seconds")
            record["task_evidence_usage"] = {"status": task["status"], "bytes": len(encoded(task)),
                                             "seconds": retrieval_seconds}
        if self.mode == "full":
            record["full"] = _full_payload(snapshot, result)
        return self._write_immutable(self._path(decision_id, "decision"), record)

    def record_outcome(self, decision_id: str, execution: dict) -> dict:
        if self.mode == "off":
            return {"status": "disabled", "persisted": False}
        decision_path = self._path(decision_id, "decision")
        if not decision_path.exists():
            raise EvidenceError("cannot record outcome for an unknown decision")
        decision_record = _read_json(decision_path)
        self._validate_record(decision_record, decision_id, "decision")
        if epoch(decision_record["expires_at"]) <= self.clock():
            raise EvidenceError("cannot record outcome for an expired decision")
        packet_ids = [item["packet_id"] for item in decision_record.get("decisions", [])]
        supplied_packet = execution.get("packet_id") if isinstance(execution, dict) else None
        if supplied_packet is None:
            if len(packet_ids) != 1:
                raise EvidenceError("packet_id is required for a multi-packet decision")
            packet_id = packet_ids[0]
        else:
            packet_id = _identifier(supplied_packet, "packet_id")
        if packet_id not in packet_ids:
            raise EvidenceError("execution packet_id is not part of the decision")
        record = self._base(decision_id, "outcome")
        # One decision and all of its lifecycle receipts share a retention unit.
        record["expires_at"] = decision_record["expires_at"]
        record["execution"] = _outcome(execution, retain_descriptions=self.retain_descriptions)
        record["packet_id"] = packet_id
        execution_ref = record["execution"]["execution_ref"]
        attempt_key = hashlib.sha256(encoded({"packet_id": packet_id,
                                             "execution_ref": execution_ref or "default"})).hexdigest()
        record["attempt_key"] = attempt_key
        status = record["execution"]["status"]
        path = self._path(decision_id, "outcome", status, attempt_key)
        _refuse_link_ancestors(self.root)
        with source_lock(self.root / ".write.lock") as acquired:
            if not acquired:
                raise EvidenceError("history write is already in progress")
            all_existing = self._outcome_records(decision_id)
            if execution_ref is None and any(item["packet_id"] == packet_id
                                              and item["attempt_key"] != attempt_key
                                              for item in all_existing):
                raise EvidenceError("execution_ref is required for multiple attempts")
            existing = [item for item in all_existing if item["attempt_key"] == attempt_key]
            if path.exists():
                current = _read_json(path)
                left = {key: value for key, value in current.items()
                        if key not in {"created_at", "expires_at"}}
                right = {key: value for key, value in record.items()
                         if key not in {"created_at", "expires_at"}}
                if left == right:
                    return {**copy.deepcopy(current), "write_status": "unchanged"}
                raise EvidenceError("conflicting immutable history record")
            terminal = [item for item in existing
                        if item["execution"]["status"] in _TERMINAL_STATUSES]
            if terminal:
                raise EvidenceError("conflicting terminal execution outcome")
            if status == "launched" and existing:
                raise EvidenceError("conflicting execution lifecycle event")
            atomic_write(path, record)
            self._prune_locked()
        return {**copy.deepcopy(record), "write_status": "written"}

    def _outcome_records(self, decision_id: str) -> list[dict]:
        key = _record_key(decision_id)
        result = []
        for path in self.root.glob(f"outcome-{key}-*.json"):
            parts = _file_parts(path.name)
            if parts is None or parts[0] != "outcome" or parts[1] != key:
                continue
            record = _read_json(path)
            self._validate_record(record, decision_id, "outcome")
            if (record.get("attempt_key") != parts[2]
                    or record.get("execution", {}).get("status") != parts[3]):
                raise EvidenceError("history outcome filename does not match status")
            result.append(record)
        order = {"launched": 0, "completed": 1, "failed": 1, "interrupted": 1, "unknown": 1}
        return sorted(result, key=lambda item: (item["packet_id"], item["attempt_key"],
                                                order[item["execution"]["status"]],
                                                item["created_at"]))

    def read(self, decision_id: str) -> dict | None:
        _identifier(decision_id, "decision_id")
        if self.mode == "off":
            return None
        _refuse_link_ancestors(self.root)
        path = self._path(decision_id, "decision")
        if not path.exists():
            return None
        decision = _read_json(path)
        self._validate_record(decision, decision_id, "decision")
        result = copy.deepcopy(decision)
        outcomes = self._outcome_records(decision_id)
        if outcomes:
            result["outcome_records"] = outcomes
            result["outcome_record"] = outcomes[-1]
        return result

    @staticmethod
    def _validate_record(record: dict, decision_id: str, kind: str) -> None:
        if (record.get("history_schema") != HISTORY_SCHEMA
                or record.get("namespace") != NAMESPACE
                or record.get("record_type") != kind
                or record.get("decision_id") != decision_id):
            raise EvidenceError("history record identity mismatch")
        epoch(record.get("created_at"))
        epoch(record.get("expires_at"))

    def _prune_locked(self) -> dict:
        counts = {"scanned": 0, "deleted": 0, "invalid": 0, "skipped": 0,
                  "bounded": False}
        now = self.clock()
        for path in self.root.iterdir():
            if counts["scanned"] >= MAX_PRUNE_FILES:
                counts["bounded"] = True
                break
            parts = _file_parts(path.name)
            if parts is None:
                counts["skipped"] += 1
                continue
            counts["scanned"] += 1
            if path.is_symlink() or _is_reparse(path) or not path.is_file():
                counts["skipped"] += 1
                continue
            try:
                record = _read_json(path)
                expected, expected_key, expected_attempt, expected_status = parts
                if (record.get("history_schema") != HISTORY_SCHEMA
                        or record.get("namespace") != NAMESPACE
                        or record.get("record_type") != expected
                        or _record_key(record.get("decision_id", "")) != expected_key
                        or (expected_attempt is not None
                            and record.get("attempt_key") != expected_attempt)
                        or (expected_status is not None
                            and record.get("execution", {}).get("status") != expected_status)):
                    counts["invalid"] += 1
                    continue
                if epoch(record.get("expires_at")) <= now:
                    path.unlink()
                    counts["deleted"] += 1
            except (EvidenceError, OSError, TypeError):
                counts["invalid"] += 1
        return counts

    def prune(self) -> dict:
        if self.mode == "off":
            return {"status": "disabled", "scanned": 0, "deleted": 0}
        _refuse_link_ancestors(self.root)
        with source_lock(self.root / ".write.lock") as acquired:
            if not acquired:
                raise EvidenceError("history write is already in progress")
            return self._prune_locked()


def _dig(value: Any, *paths: tuple[str, ...]) -> Any:
    for path in paths:
        current = value
        for key in path:
            if not isinstance(current, dict) or key not in current:
                break
            current = current[key]
        else:
            return current
    return None


def _event_identity(value: dict, normalized: dict, source_index: int, line_number: int) -> str:
    observed = _dig(value, ("uuid",), ("id",), ("message", "id"),
                    ("payload", "id"), ("payload", "turn_id"), ("request_id",))
    if isinstance(observed, str) and observed:
        return "id:" + normalized.get("client", "unknown") + ":" + observed
    stable = {key: normalized.get(key) for key in
              ("client", "timestamp", "request_id", "actual_model", "usage")}
    if any(item is not None for item in stable.values()):
        return "hash:" + hashlib.sha256(encoded(stable)).hexdigest()
    return f"position:{source_index}:{line_number}"


def _context_route(value: dict) -> dict:
    payload = value.get("payload") if isinstance(value.get("payload"), dict) else value
    message = value.get("message") if isinstance(value.get("message"), dict) else {}
    actual_model = message.get("model")
    if actual_model is None and value.get("type") in {"assistant", "result"}:
        actual_model = value.get("model")
        model_usage = value.get("modelUsage")
        if actual_model is None and isinstance(model_usage, dict) and len(model_usage) == 1:
            actual_model = next(iter(model_usage))
    requested_model = _dig(value, ("requested_model",), ("payload", "requested_model"))
    if requested_model is None and value.get("type") in {"turn_context", "context"}:
        requested_model = payload.get("model")
    actual_effort = _dig(value, ("actual_effort",), ("payload", "actual_effort"))
    if actual_effort is None and value.get("type") == "result":
        actual_effort = value.get("effort")
    requested_effort = _dig(value, ("requested_effort",), ("payload", "effort"),
                            ("effort",))
    tier = _dig(message, ("usage", "service_tier"), ("usage", "service_tier"),
                ("payload", "service_tier"))
    return {
        "requested_model": requested_model if isinstance(requested_model, str) else None,
        "requested_effort": requested_effort if isinstance(requested_effort, str) else None,
        "actual_model": actual_model if isinstance(actual_model, str) else None,
        "actual_effort": actual_effort if isinstance(actual_effort, str) else None,
        "service_tier": tier if isinstance(tier, str) else None,
    }


def _quota(value: dict, client: str, when: Any) -> dict | None:
    limits = _dig(value, ("rate_limits",), ("payload", "rate_limits"),
                  ("payload", "info", "rate_limits"))
    if not isinstance(limits, dict):
        return None
    return {
        "timestamp": when if isinstance(when, str) else None,
        "client": client,
        "scope": "account",
        "limits": _redacted_json(limits, "quota"),
        "provenance": "observed:rate_limits",
        "request_attribution": None,
    }


def _client(value: dict) -> str | None:
    kind = value.get("type")
    if kind in {"assistant", "user", "result", "system"} and (
            "sessionId" in value or "session_id" in value or "message" in value):
        return "claude"
    if kind in {"session_meta", "turn_context", "event_msg", "response_item"}:
        return "codex"
    if value.get("client") in {"codex", "claude"}:
        return value["client"]
    return None


def _normalized_event(value: dict, states: dict, source_index: int) -> tuple[dict | None, dict | None]:
    client = _client(value)
    if client is None:
        return None, None
    when = _dig(value, ("timestamp",), ("created_at",), ("payload", "timestamp"))
    quota = _quota(value, client, when)
    stream_id = _dig(value, ("sessionId",), ("session_id",), ("payload", "session_id"))
    stream_key = (source_index, stream_id if isinstance(stream_id, str) else "default")
    route = _context_route(value)
    state = states.setdefault(stream_key, {})
    state.update({key: item for key, item in route.items() if item is not None})
    direct = _dig(value, ("message", "usage"), ("usage",),
                  ("payload", "usage"), ("payload", "info", "last_token_usage"))
    cumulative = _dig(value, ("payload", "info", "total_token_usage"),
                      ("total_token_usage",), ("modelUsage",))
    suppress_result = value.get("type") == "result" and state.get("direct_seen")
    usage = None if suppress_result else _usage(direct, provenance="observed:direct_usage")
    provenance = "direct"
    if usage is not None:
        state["direct_seen"] = True
        if isinstance(cumulative, dict) and "modelUsage" not in value:
            observed_total = _usage(cumulative, provenance="observed:cumulative_baseline")
            if observed_total is not None:
                state["cumulative"] = observed_total
    if not suppress_result and usage is None and isinstance(cumulative, dict) and "modelUsage" not in value:
        current = _usage(cumulative, provenance="derived:cumulative_delta")
        if current is not None:
            previous = state.get("cumulative")
            fields = [key for key in current if key.endswith("_tokens")]
            reset = previous is not None and any(current.get(key, 0) < previous.get(key, 0)
                                                  for key in fields)
            if previous is None or reset:
                usage = current
            else:
                usage = {key: max(0, current.get(key, 0) - previous.get(key, 0))
                         for key in fields}
                usage.update(provenance="derived:cumulative_delta", pricing_usd=None,
                             billed_quota=None)
            state["cumulative"] = current
            provenance = "cumulative_reset" if reset else "cumulative_delta"
    if not suppress_result and usage is None and isinstance(cumulative, dict) and "modelUsage" in value:
        # Claude result aggregates are kept only when no direct assistant request
        # is available to avoid counting the same request twice.
        totals = next(iter(cumulative.values()), None) if len(cumulative) == 1 else None
        usage = _usage(totals, provenance="observed:result_aggregate")
        provenance = "result_aggregate"
    if usage is None:
        return None, quota
    merged = {**state, **{key: item for key, item in route.items() if item is not None}}
    request_id = _dig(value, ("request_id",), ("message", "id"), ("payload", "turn_id"))
    decision_id = _dig(value, ("decision_id",), ("payload", "decision_id"),
                       ("metadata", "decision_id"))
    normalized = {
        "client": client,
        "timestamp": when if isinstance(when, str) else None,
        "request_id": request_id if isinstance(request_id, str) else None,
        "session_id": stream_id if isinstance(stream_id, str) else None,
        "requested": {key.removeprefix("requested_"): item for key, item in merged.items()
                      if key.startswith("requested_")},
        "observed": {key.removeprefix("actual_"): item for key, item in merged.items()
                     if key.startswith("actual_")},
        "usage": usage,
        "usage_kind": provenance,
        "link": {"method": "explicit_request_id" if isinstance(request_id, str)
                 else "heuristic_same_stream", "confidence": "confirmed" if isinstance(request_id, str)
                 else "heuristic"},
        "decision_link": ({"decision_id": decision_id, "method": "explicit_id",
                           "confidence": "confirmed"}
                          if isinstance(decision_id, str) and _CODE.fullmatch(decision_id) else None),
    }
    if merged.get("service_tier") is not None:
        normalized["observed"]["service_tier"] = merged["service_tier"]
    normalized["requested_provenance"] = ({key: "observed:request_context"
                                             for key in normalized["requested"]})
    normalized["observed_provenance"] = ({key: "observed:response"
                                            for key in normalized["observed"]})
    return normalized, quota


def import_history(paths: list[Path]) -> dict:
    """Read explicitly named Codex/Claude JSONL files without changing them."""
    if not isinstance(paths, list) or not paths or len(paths) > MAX_IMPORT_FILES:
        raise EvidenceError(f"history import requires 1..{MAX_IMPORT_FILES} paths")
    requests: list[dict] = []
    quota_events: list[dict] = []
    errors: list[dict] = []
    seen: set[str] = set()
    seen_quota: set[str] = set()
    states: dict = {}
    counters = {"files_requested": len(paths), "files_read": 0, "lines": 0,
                "duplicates": 0, "malformed": 0, "unsupported": 0, "bytes": 0}
    stop = False
    for source_index, supplied in enumerate(paths):
        path = Path(supplied)
        if stop:
            break
        try:
            if path.is_symlink() or _is_reparse(path) or not path.is_file():
                raise OSError("not a regular file")
            handle = path.open("rb")
        except OSError:
            errors.append({"source_index": source_index, "code": "missing_or_unsafe_file"})
            continue
        counters["files_read"] += 1
        with handle:
            for line_number, raw in enumerate(handle, 1):
                counters["lines"] += 1
                counters["bytes"] += len(raw)
                if (counters["lines"] > MAX_IMPORT_LINES
                        or counters["bytes"] > MAX_IMPORT_BYTES):
                    errors.append({"source_index": source_index, "line": line_number,
                                   "code": "import_limit_reached"})
                    stop = True
                    break
                if len(raw) > MAX_IMPORT_LINE_BYTES:
                    counters["malformed"] += 1
                    errors.append({"source_index": source_index, "line": line_number,
                                   "code": "line_too_large"})
                    continue
                try:
                    value = loads(raw.decode("utf-8"))
                    if not isinstance(value, dict):
                        raise EvidenceError("event must be an object")
                    normalized, quota = _normalized_event(value, states, source_index)
                except (EvidenceError, UnicodeError, RecursionError):
                    counters["malformed"] += 1
                    errors.append({"source_index": source_index, "line": line_number,
                                   "code": "malformed_event"})
                    continue
                if quota is not None:
                    quota_key = hashlib.sha256(encoded(quota)).hexdigest()
                    if quota_key not in seen_quota:
                        seen_quota.add(quota_key)
                        quota_events.append(quota)
                if normalized is None:
                    if quota is None and _client(value) is None:
                        counters["unsupported"] += 1
                    continue
                identity = _event_identity(value, normalized, source_index, line_number)
                if identity in seen:
                    counters["duplicates"] += 1
                    continue
                seen.add(identity)
                normalized["event_id"] = hashlib.sha256(identity.encode("utf-8")).hexdigest()
                requests.append(normalized)
    totals: dict[str, int | float] = {}
    for request in requests:
        for key, value in request["usage"].items():
            if key.endswith("_tokens") and isinstance(value, (int, float)):
                totals[key] = totals.get(key, 0) + value
    return {
        "schema_version": 1,
        "status": "partial" if errors else "complete",
        "requests": requests,
        "quota_timeline": quota_events,
        "summary": {**counters, "request_events": len(requests),
                    "quota_events": len(quota_events), "usage": totals,
                    "pricing_usd": None, "billed_quota": None},
        "errors": errors,
    }


def replay(record: dict, *, policy: dict | None = None) -> dict:
    """Replay saved policy inputs only; never call an advisor or external service."""
    if not isinstance(record, dict) or record.get("history_schema") != HISTORY_SCHEMA:
        raise EvidenceError("replay requires a routing history record")
    full = record.get("full")
    if not isinstance(full, dict) or not isinstance(full.get("snapshot"), dict):
        return {"schema_version": 1, "status": "insufficient_record",
                "decision_id": record.get("decision_id"),
                "usage": "diagnostic_only", "execution_authorized": False,
                "reason_codes": ["snapshot_not_retained"]}
    from .advice import decide, default_policy
    from .advice_contracts import derive_packet, snapshot_identity, validate_routing_snapshot
    from .core import digest

    snapshot = copy.deepcopy(full["snapshot"])
    snapshot = validate_routing_snapshot(snapshot)
    original_eligible = {packet["packet_id"]: list(packet["eligible"])
                         for packet in snapshot["packets"]}
    advisor_result = copy.deepcopy(full.get("advisor_result"))
    if policy is not None:
        effective_policy = default_policy(policy)
        source_packets = [{key: copy.deepcopy(packet[key]) for key in
                           ("packet_id", "task_types", "features", "explicit", "baseline",
                            "requirements", "capabilities")}
                          for packet in snapshot["packets"]]
        snapshot["policy"] = effective_policy
        snapshot["policy_hash"] = digest(effective_policy)
        snapshot["packets"] = [derive_packet(packet, snapshot["candidates"],
                                              snapshot["evidence"], effective_policy)
                               for packet in source_packets]
        without_id = {key: value for key, value in snapshot.items() if key != "snapshot_id"}
        snapshot["snapshot_id"] = snapshot_identity(without_id)
        snapshot = validate_routing_snapshot(snapshot)
        changed_eligible = {packet["packet_id"]: list(packet["eligible"])
                            for packet in snapshot["packets"]}
        if changed_eligible != original_eligible:
            return {
                "schema_version": 1,
                "status": "insufficient_record",
                "decision_id": record.get("decision_id"),
                "usage": "diagnostic_only",
                "execution_authorized": False,
                "reason_codes": ["cannot_reuse_advisor_candidate_basis"],
            }
        if advisor_result is not None:
            advisor_result["snapshot_id"] = snapshot["snapshot_id"]
    decisions = decide(snapshot, result=advisor_result,
                       reason="history_replay", offline=False)
    return {
        "schema_version": 1,
        "status": "replayed",
        "decision_id": record.get("decision_id"),
        "mode": "offline_policy",
        "usage": "diagnostic_only",
        "execution_authorized": False,
        "prediction_only": True,
        "decisions": decisions,
        "limitations": ["advisor_output_not_recreated", "no_counterfactual_outcome"],
    }
