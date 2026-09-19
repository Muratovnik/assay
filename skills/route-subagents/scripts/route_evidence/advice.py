"""Pure snapshot construction, routing policy, and exact cache identities."""
from __future__ import annotations

import copy
import math
import re
from typing import Any

from .advice_contracts import (AdviceLimitError, COMPACT_EVIDENCE_ENCODING, MAX_METADATA_BYTES, candidate_id,
                               derive_packet, normalize_policy, snapshot_identity,
                               validate_packets, validate_result,
                               validate_routing_snapshot)
from .core import EvidenceError, digest, encoded, effort, text
from .routing import TASK_TYPES

_TRANSIENT_EVIDENCE_KEYS = {"cache_age_seconds", "last_attempt_at", "next_retry_at", "refresh", "error",
                            "last_success_at", "data_changed_at", "source_updated_at", "retrieved_at"}
_DESCRIPTOR_KEYS = {"backend", "model", "effort", "prompt_version", "schema_version", "privacy_profile"}
_REASON = re.compile(r"^[a-z0-9][a-z0-9_.:-]{0,95}$")
_CANDIDATE_COLUMNS = ["candidate_ref", "score", "score_low", "score_high", "quality_delta_pp",
                      "expenses", "expense_evidence", "unmeasured_expenses", "cost_basis",
                      "evaluated_at", "frontier", "dominated_by", "stale", "constraints"]


def default_policy(overrides=None) -> dict:
    """Return a normalized, detached routing policy."""
    return normalize_policy(overrides)


def _compact_records(records: Any) -> dict:
    if not isinstance(records, list) or any(not isinstance(record, dict) for record in records):
        raise EvidenceError("context sources must be an array of objects")
    columns = sorted({key for record in records for key in record})
    pool, indexes, rows = [], {}, []
    for record in records:
        row = []
        for key in columns:
            value = copy.deepcopy(record.get(key))
            fingerprint = digest(value)
            index = indexes.get(fingerprint)
            if index is None:
                index = len(pool)
                indexes[fingerprint] = index
                pool.append(value)
            row.append(index)
        rows.append(row)
    return {"record_encoding": "columns+value_pool", "columns": columns,
            "value_pool": pool, "rows": rows}


def _expand_records(table: dict) -> list[dict]:
    columns, pool = table["columns"], table["value_pool"]
    return [{key: copy.deepcopy(pool[ref]) for key, ref in zip(columns, row)}
            for row in table["rows"]]


def _compact_cohort(comparison: dict, pair_refs: dict[tuple[str, str], int]) -> dict:
    cohort = {key: copy.deepcopy(value) for key, value in comparison.items()
              if key not in {"candidates", "missing_candidates"}}
    candidates = comparison.get("candidates", [])
    if not isinstance(candidates, list):
        raise EvidenceError("context cohort candidates must be an array")
    source_urls = {candidate.get("source_url") for candidate in candidates
                   if isinstance(candidate, dict) and candidate.get("source_url") is not None}
    shared_source_url = next(iter(source_urls)) if len(source_urls) == 1 else None
    axes = comparison.get("expense_axes", [])
    if not isinstance(axes, list) or len(set(axes)) != len(axes):
        raise EvidenceError("context cohort expense axes are invalid")
    axis_refs = {axis: index for index, axis in enumerate(axes)}
    rows = []
    expected = {"model", "effort", "score", "score_low", "score_high", "quality_delta_pp",
                "expenses", "expense_evidence", "unmeasured_expenses", "cost_basis", "evaluated_at",
                "frontier", "dominated_by", "stale", "constraints", "source_url"}
    for candidate in candidates:
        if not isinstance(candidate, dict) or set(candidate) - expected:
            raise EvidenceError("context cohort candidate has unsupported fields")
        pair = (candidate.get("model"), candidate.get("effort"))
        if pair not in pair_refs:
            raise EvidenceError("context cohort candidate is absent from inventory")
        dominated_by_axis = {}
        for item in candidate.get("dominated_by", []):
            target = (item.get("model"), item.get("effort")) if isinstance(item, dict) else None
            if (target not in pair_refs or set(item) != {"axis", "model", "effort"}
                    or item["axis"] not in axis_refs):
                raise EvidenceError("context domination reference is invalid")
            dominated_by_axis.setdefault(axis_refs[item["axis"]], []).append(pair_refs[target])
        dominated = [[axis_ref, refs] for axis_ref, refs in dominated_by_axis.items()]
        constraints = []
        for item in candidate.get("constraints", []):
            if (not isinstance(item, dict) or set(item) - {"constraint", "limit", "observed", "status"}
                    or not {"constraint", "status"} <= set(item)):
                raise EvidenceError("context candidate constraint is invalid")
            constraints.append([item["constraint"], item.get("limit"), item.get("observed"), item["status"]])
        source_url = None if shared_source_url is not None else candidate.get("source_url")
        expenses = candidate.get("expenses", {})
        unmeasured = candidate.get("unmeasured_expenses", [])
        frontier = candidate.get("frontier", [])
        if (not isinstance(expenses, dict) or any(axis not in axis_refs for axis in expenses)
                or not isinstance(unmeasured, list) or any(axis not in axis_refs for axis in unmeasured)
                or not isinstance(frontier, list) or any(axis not in axis_refs for axis in frontier)):
            raise EvidenceError("context candidate expense axes are invalid")
        compact_expenses = [[axis_refs[axis], value] for axis, value in expenses.items()]
        rows.append([pair_refs[pair], candidate.get("score"), candidate.get("score_low"),
                     candidate.get("score_high"), candidate.get("quality_delta_pp"),
                     compact_expenses, candidate.get("expense_evidence"),
                     [axis_refs[axis] for axis in unmeasured], candidate.get("cost_basis"),
                     candidate.get("evaluated_at"), [axis_refs[axis] for axis in frontier],
                     dominated, candidate.get("stale"), constraints, source_url])
    columns = [*_CANDIDATE_COLUMNS, "source_url"]
    if shared_source_url is not None:
        columns.pop()
        rows = [row[:-1] for row in rows]
        cohort["candidate_source_url"] = shared_source_url
    pool, pool_indexes = [], {}
    compact_rows = []
    for row in rows:
        compact = [row[0]]
        for value in row[1:]:
            key = digest(value)
            index = pool_indexes.get(key)
            if index is None:
                index = len(pool)
                pool_indexes[key] = index
                pool.append(value)
            compact.append(index)
        compact_rows.append(compact)
    cohort["candidate_columns"] = columns
    cohort["candidate_value_pool"] = pool
    cohort["candidate_rows"] = compact_rows
    missing = comparison.get("missing_candidates", [])
    if not isinstance(missing, list):
        raise EvidenceError("context missing candidates must be an array")
    cohort["missing_candidate_refs"] = []
    for item in missing:
        pair = (item.get("model"), item.get("effort")) if isinstance(item, dict) else None
        if pair not in pair_refs or set(item) != {"model", "effort"}:
            raise EvidenceError("context missing candidate is absent from inventory")
        cohort["missing_candidate_refs"].append(pair_refs[pair])
    return cohort


def _project_evidence(context: dict, candidates: list[dict]) -> dict:
    """Project existing context once without changing benchmark annotations."""
    keys = ("data_status", "data_message", "usage", "task_types", "sources", "excluded",
            "guidance", "declared_constraints", "constraint_note", "warnings")
    evidence = {key: copy.deepcopy(context[key]) for key in keys if key in context}
    evidence["sources"] = _compact_records(evidence.get("sources", []))
    evidence["projection_version"] = 1
    evidence["encoding"] = copy.deepcopy(COMPACT_EVIDENCE_ENCODING)
    cohorts, cohort_by_digest, cohort_by_id, tasks = [], {}, {}, []
    pair_refs = {(candidate["model"], candidate["effort"]): index
                 for index, candidate in enumerate(candidates)}
    for task in context.get("tasks", []):
        if not isinstance(task, dict):
            raise EvidenceError("context task must be an object")
        projected = {key: copy.deepcopy(value) for key, value in task.items()
                     if key not in {"primary_comparisons", "supporting_comparisons", "coverage", "unmeasured"}}
        unmeasured = task.get("unmeasured", [])
        if not isinstance(unmeasured, list):
            raise EvidenceError("context unmeasured candidates must be an array")
        projected["unmeasured_candidate_refs"] = []
        for item in unmeasured:
            pair = (item.get("model"), item.get("effort")) if isinstance(item, dict) else None
            if pair not in pair_refs or set(item) != {"model", "effort"}:
                raise EvidenceError("context unmeasured candidate is absent from inventory")
            projected["unmeasured_candidate_refs"].append(pair_refs[pair])
        for source_key, ref_key in (("primary_comparisons", "primary_cohort_ids"),
                                    ("supporting_comparisons", "supporting_cohort_ids")):
            comparisons = task.get(source_key, [])
            if not isinstance(comparisons, list):
                raise EvidenceError("context comparisons must be arrays")
            refs = []
            for comparison in comparisons:
                if not isinstance(comparison, dict):
                    raise EvidenceError("context comparison must be an object")
                compact = _compact_cohort(comparison, pair_refs)
                fingerprint = digest(compact)
                cohort_id = cohort_by_digest.get(fingerprint)
                if cohort_id is None:
                    cohort_id = "cohort_" + fingerprint[:24]
                    cohort = {"cohort_id": cohort_id, **compact}
                    cohort_by_digest[fingerprint] = cohort_id
                    cohort_by_id[cohort_id] = cohort
                    cohorts.append(cohort)
                refs.append(cohort_id)
            projected[ref_key] = refs
        coverage_refs = []
        coverage_values = task.get("coverage", [])
        if not isinstance(coverage_values, list):
            raise EvidenceError("context coverage must be an array")
        for coverage in coverage_values:
            if not isinstance(coverage, dict):
                raise EvidenceError("context coverage must be an object")
            normalized_coverage = dict(coverage)
            if "missing_candidates" in normalized_coverage:
                normalized_coverage["missing_candidate_refs"] = [pair_refs[(item["model"], item["effort"])]
                                                                   for item in normalized_coverage.pop("missing_candidates")]
            matches = [cohort_id for cohort_id in projected["primary_cohort_ids"]
                       if all(cohort_by_id[cohort_id].get(key) == value
                              for key, value in normalized_coverage.items())]
            if len(matches) != 1:
                raise EvidenceError("context coverage does not identify one primary cohort")
            coverage_refs.append(matches[0])
        projected["coverage_cohort_ids"] = coverage_refs
        tasks.append(projected)
    evidence["cohorts"] = cohorts
    evidence["tasks"] = tasks
    # These fields are the minimum needed to retain primary/support/cohort gaps.
    evidence.setdefault("task_types", copy.deepcopy(context.get("task_types", [])))
    evidence.setdefault("cohorts", [])
    evidence.setdefault("tasks", [])
    evidence.setdefault("sources", [])
    evidence.setdefault("excluded", [])
    evidence.setdefault("guidance", {})
    evidence.setdefault("declared_constraints", {})
    evidence.setdefault("warnings", [])
    try:
        encoded(evidence)
    except (TypeError, ValueError, RecursionError) as exc:
        raise EvidenceError("context evidence must be finite JSON") from exc
    return evidence


def _inventory(context: dict) -> list[dict]:
    inventory = context.get("inventory")
    if not isinstance(inventory, list) or not inventory or len(inventory) > 100:
        raise EvidenceError("context.inventory requires 1..100 model/effort pairs")
    candidates, seen = [], set()
    for index, item in enumerate(inventory):
        if not isinstance(item, dict) or set(item) != {"model", "effort"}:
            raise EvidenceError(f"context.inventory[{index}] requires model and effort")
        model = text(item["model"], "inventory.model")
        level = effort(item["effort"])
        if level is None:
            raise EvidenceError("inventory effort must be explicit")
        if (model, level) in seen:
            raise EvidenceError("duplicate inventory model/effort")
        seen.add((model, level))
        candidates.append({"candidate_id": candidate_id(model, level),
                           "model": model, "effort": level})
    return sorted(candidates, key=lambda item: (item["model"], item["effort"]))


def build_snapshot(context, packets, *, policy, created_at, expires_at, client) -> dict:
    """Build one immutable advisor input over an existing evidence context.

    Configured overflows carry the full validated snapshot on AdviceLimitError;
    callers can still apply explicit, singleton, and baseline policy outcomes.
    """
    if not isinstance(context, dict) or context.get("schema_version") != 2:
        raise EvidenceError("context requires evidence schema_version=2")
    client = text(client, "client")
    if context.get("client") != client:
        raise EvidenceError("context client does not match snapshot client")
    policy = normalize_policy(policy)
    packets = validate_packets(packets)
    context_types = context.get("task_types", [])
    if not isinstance(context_types, list):
        raise EvidenceError("context.task_types must be an array")
    for packet in packets:
        for task_type in packet["task_types"]:
            if task_type not in TASK_TYPES:
                raise EvidenceError("unknown packet task type: " + task_type)
            if task_type not in context_types:
                raise EvidenceError("packet task type is absent from evidence context: " + task_type)
    candidates = _inventory(context)
    evidence = _project_evidence(context, candidates)
    derived = [derive_packet(packet, candidates, evidence, policy) for packet in packets]
    inventory_projection = [{"model": item["model"], "effort": item["effort"]}
                            for item in candidates]
    snapshot = {
        "schema_version": 1,
        "created_at": created_at,
        "expires_at": expires_at,
        "client": client,
        "packet_ids": [packet["packet_id"] for packet in derived],
        "inventory_hash": digest(inventory_projection),
        "evidence_hash": digest(evidence),
        "policy_hash": digest(policy),
        "candidates": candidates,
        "packets": derived,
        "evidence": evidence,
        "policy": policy,
    }
    snapshot["snapshot_id"] = snapshot_identity(snapshot)
    snapshot = validate_routing_snapshot(snapshot)
    if len(snapshot["packets"]) > policy["max_packets"]:
        raise AdviceLimitError("packet_limit_exceeded", snapshot)
    if any(len(packet["eligible"]) > policy["max_candidates_per_packet"]
           for packet in snapshot["packets"]):
        raise AdviceLimitError("candidate_limit_exceeded", snapshot)
    if len(encoded(semantic_projection(snapshot))) > policy["max_snapshot_bytes"]:
        raise AdviceLimitError("snapshot_limit_exceeded", snapshot)
    return snapshot


def _candidate_map(snapshot: dict) -> dict[str, dict]:
    return {item["candidate_id"]: item for item in snapshot["candidates"]}


def _selection(candidate: dict | None) -> dict | None:
    if candidate is None:
        return None
    return {key: candidate[key] for key in ("model", "effort", "candidate_id")}


def _fallback(packet: dict, candidates: dict[str, dict], policy: dict) -> dict:
    if policy["fallback"] != "caller-baseline" or not packet["baseline"]:
        return {"status": "needs_caller_selection", "selected": None,
                "reason": "fallback_not_configured"}
    baseline = packet["baseline"]
    match = next((item for item in candidates.values()
                  if item["model"] == baseline["model"] and item["effort"] == baseline["effort"]), None)
    if match is None or match["candidate_id"] not in packet["eligible"]:
        return {"status": "needs_caller_selection", "selected": None,
                "reason": "baseline_not_eligible"}
    return {"status": "available", "selected": _selection(match),
            "reason": "caller_baseline"}


def _reason(value: Any, fallback: str) -> str:
    return value if isinstance(value, str) and _REASON.fullmatch(value) else fallback


def _top_candidate(entry: dict, packet: dict, candidates: dict[str, dict]) -> dict:
    first = entry["ranking"][0]
    tie = next((group for group in entry["ties"] if first in group), [first])
    baseline = packet["baseline"]
    if baseline:
        current = next((candidate_id for candidate_id in tie
                        if candidates[candidate_id]["model"] == baseline["model"]
                        and candidates[candidate_id]["effort"] == baseline["effort"]), None)
        if current is not None:
            return candidates[current]
    return candidates[min(tie)]


def decide(snapshot, result=None, *, reason=None, offline=False) -> list[dict]:
    """Apply deterministic policy.  This function never launches an executor."""
    snapshot = validate_routing_snapshot(snapshot)
    if not isinstance(offline, bool):
        raise EvidenceError("offline must be boolean")
    result = validate_result(snapshot, result) if result is not None else None
    rankings = {item["packet_id"]: item for item in result["rankings"]} if result else {}
    candidates = _candidate_map(snapshot)
    decisions = []
    pending = result is None and reason in (None, "pending", "advisor_required")
    failure_code = _reason(reason, "advisor_unavailable")
    for packet in snapshot["packets"]:
        fallback = _fallback(packet, candidates, snapshot["policy"])
        entry = rankings.get(packet["packet_id"])
        ranking = list(entry["ranking"]) if entry else []
        base = {
            "schema_version": 1,
            "snapshot_id": snapshot["snapshot_id"],
            "packet_id": packet["packet_id"],
            "policy_version": snapshot["policy"]["policy_version"],
            "policy_hash": snapshot["policy_hash"],
            "ranking": ranking,
            "excluded": copy.deepcopy(packet["excluded"]),
            "fallback": fallback,
            "evidence_refs": [snapshot["evidence_hash"]],
        }
        if offline:
            codes = ["offline_diagnostic"]
            if reason is not None:
                codes.append(failure_code)
            decisions.append({**base, "status": "no_decision", "decision_type": "diagnostic",
                              "selected": None, "reason_codes": list(dict.fromkeys(codes))})
            continue

        explicit = packet["explicit"]
        if set(explicit) == {"model", "effort"}:
            match = next((candidate for candidate in candidates.values()
                          if candidate["model"] == explicit["model"]
                          and candidate["effort"] == explicit["effort"]), None)
            if match is not None and match["candidate_id"] in packet["eligible"]:
                decisions.append({**base, "status": "chosen", "decision_type": "explicit_user_choice",
                                  "selected": _selection(match), "reason_codes": ["explicit_user_choice"]})
            else:
                decisions.append({**base, "status": "no_decision", "decision_type": "explicit_user_choice",
                                  "selected": None, "reason_codes": ["invalid_explicit_choice"]})
            continue

        if len(packet["eligible"]) == 1:
            match = candidates[packet["eligible"][0]]
            codes = ["single_eligible"]
            if any(warning["candidate_id"] == match["candidate_id"] for warning in packet["warnings"]):
                codes.append("unknown_evidence_warning")
            decisions.append({**base, "status": "chosen", "decision_type": "single_eligible",
                              "selected": _selection(match), "reason_codes": codes})
            continue

        if not packet["eligible"]:
            code = "invalid_explicit_choice" if explicit else "no_eligible_candidates"
            decisions.append({**base, "status": "no_decision", "decision_type": "advisor",
                              "selected": None, "reason_codes": [code]})
            continue

        if pending:
            decisions.append({**base, "status": "no_decision", "decision_type": "advisor",
                              "selected": None, "reason_codes": ["advisor_required"]})
            continue

        if entry is not None and not entry["abstained"]:
            selected = _top_candidate(entry, packet, candidates)
            codes = ["advisor_selected", *entry["reason_codes"]]
            if any(warning["candidate_id"] == selected["candidate_id"] for warning in packet["warnings"]):
                codes.append("unknown_evidence_warning")
            decisions.append({**base, "status": "chosen", "decision_type": "advisor",
                              "selected": _selection(selected),
                              "reason_codes": list(dict.fromkeys(codes))})
            continue

        cause = "advisor_abstained" if entry is not None else failure_code
        if fallback["status"] == "available":
            decisions.append({**base, "status": "chosen", "decision_type": "fallback",
                              "selected": fallback["selected"], "reason_codes": [cause, "caller_baseline"]})
        else:
            decisions.append({**base, "status": "no_decision", "decision_type": "fallback",
                              "selected": None, "reason_codes": [cause, "needs_caller_selection"]})
    return decisions


def _without_transient_evidence(value: Any) -> Any:
    if isinstance(value, list):
        return [_without_transient_evidence(item) for item in value]
    if isinstance(value, dict):
        if value.get("record_encoding") == "columns+value_pool":
            records = [{key: item for key, item in record.items()
                        if key not in _TRANSIENT_EVIDENCE_KEYS}
                       for record in _expand_records(value)]
            return _compact_records(records)
        return {key: _without_transient_evidence(item) for key, item in value.items()
                if key not in _TRANSIENT_EVIDENCE_KEYS}
    return value


def semantic_projection(snapshot) -> dict:
    """Return the exact cache semantic input, excluding only nonce/time/transport health."""
    snapshot = validate_routing_snapshot(snapshot)
    projection = {key: copy.deepcopy(value) for key, value in snapshot.items()
                  if key not in {"snapshot_id", "created_at", "expires_at", "evidence_hash"}}
    projection["evidence"] = _without_transient_evidence(projection["evidence"])
    canonical_ids = {packet["packet_id"]: f"packet-{index}"
                     for index, packet in enumerate(projection["packets"])}
    projection["packet_ids"] = [canonical_ids[packet_id] for packet_id in projection["packet_ids"]]
    for packet in projection["packets"]:
        packet["packet_id"] = canonical_ids[packet["packet_id"]]
    return projection


def _descriptor_value(value: Any, depth=0) -> Any:
    if depth > 4:
        raise EvidenceError("backend descriptor is too deeply nested")
    if value is None or isinstance(value, (bool, int)):
        return value
    if isinstance(value, float) and math.isfinite(value):
        return value
    if isinstance(value, str) and len(value) <= 500 and not any(ord(ch) < 32 for ch in value):
        return value
    if isinstance(value, list) and len(value) <= 32:
        return [_descriptor_value(item, depth + 1) for item in value]
    if isinstance(value, dict) and len(value) <= 32:
        output = {}
        for key, item in value.items():
            if not isinstance(key, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}", key):
                raise EvidenceError("backend descriptor has an invalid key")
            if any(part in key.lower() for part in ("secret", "credential", "api_key", "prompt_text")):
                raise EvidenceError("backend descriptor must not contain credentials or prompt text")
            output[key] = _descriptor_value(item, depth + 1)
        return output
    raise EvidenceError("backend descriptor contains unsupported data")


def semantic_key(snapshot, backend_descriptor) -> str:
    """Hash every value that can change advice, including backend contract versions."""
    if not isinstance(backend_descriptor, dict) or not _DESCRIPTOR_KEYS <= set(backend_descriptor):
        raise EvidenceError("backend descriptor requires backend/model/effort/prompt/schema/privacy versions")
    descriptor = _descriptor_value(copy.deepcopy(backend_descriptor))
    if len(encoded(descriptor)) > MAX_METADATA_BYTES:
        raise EvidenceError("backend descriptor exceeds size limit")
    return digest({"snapshot": semantic_projection(snapshot), "backend": descriptor})
