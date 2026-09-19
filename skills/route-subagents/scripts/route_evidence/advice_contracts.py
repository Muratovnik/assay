"""Bounded wire contracts for routing advice.

The contracts contain structured routing facts only.  Evidence remains data:
none of its strings can grant execution authority or alter the eligible set.
"""
from __future__ import annotations

import copy
import json
import math
import re
from typing import Any, TypeAlias

from .core import EvidenceError, digest, encoded, epoch, effort, number, text

RoutingSnapshot: TypeAlias = dict[str, Any]
AdvisorResult: TypeAlias = dict[str, Any]

MAX_PACKETS = 8
MAX_CANDIDATES_PER_PACKET = 64
MAX_SEMANTIC_BYTES = 24 * 1024
MAX_METADATA_BYTES = 4 * 1024
MAX_FEATURES = 16
MAX_CAPABILITIES = 32

SUPPORTED_CONSTRAINTS = {
    "max_cost_usd",
    "max_duration_seconds",
    "min_score",
    "quality_loss_pp",
}
PROVENANCE = {"caller", "observed", "unknown"}
_SAFE_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:+/-]{0,127}$")
_REASON = re.compile(r"^[a-z0-9][a-z0-9_.:-]{0,95}$")
_FEATURE_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:+-]{0,127}$")
_PROHIBITED_FEATURE_NAMES = {"prompt", "instruction", "instructions", "message", "source_code",
                             "code", "path", "task_text", "freeform_text"}
_PROHIBITED_FEATURE_SUFFIXES = ("_prompt", "_instruction", "_instructions", "_message",
                                "_source_code", "_code", "_path", "_task_text", "_freeform_text")

DEFAULT_POLICY = {
    "schema_version": 1,
    "policy_version": "routing-policy-v1",
    "fallback": "caller-baseline",
    "unknown_evidence": "warn",
    "strict_unknown_constraints": [],
    "max_packets": MAX_PACKETS,
    "max_candidates_per_packet": MAX_CANDIDATES_PER_PACKET,
    "max_snapshot_bytes": MAX_SEMANTIC_BYTES,
}
COMPACT_EVIDENCE_ENCODING = {
    "candidate_ref": "candidates index",
    "candidate_row": "ref,pool-index...",
    "axis_ref": "expense_axes index",
    "expenses": "axis-ref,value pairs",
    "frontier_or_unmeasured": "axis-ref list",
    "dominated_by": "axis-ref:[candidate-ref]",
    "constraint": "name,limit,observed,status",
    "source_records": "columns,pool-index rows",
    "unmeasured": "candidate-ref list",
}


class AdviceLimitError(EvidenceError):
    """A configured advisor bound was exceeded without truncating its input."""

    def __init__(self, code: str, snapshot: RoutingSnapshot):
        super().__init__(code)
        self.code = code
        self.snapshot = copy.deepcopy(snapshot)


def _object(value: Any, field: str, allowed: set[str], required: set[str] = frozenset()) -> dict:
    if not isinstance(value, dict):
        raise EvidenceError(f"{field}: expected an object")
    unknown = set(value) - allowed
    missing = required - set(value)
    if unknown:
        raise EvidenceError(f"{field}: unknown fields: {', '.join(sorted(unknown))}")
    if missing:
        raise EvidenceError(f"{field}: missing fields: {', '.join(sorted(missing))}")
    return value


def _safe_name(value: Any, field: str) -> str:
    value = text(value, field)
    if not _SAFE_NAME.fullmatch(value):
        raise EvidenceError(f"{field}: expected a bounded identifier")
    return value


def _reason_codes(value: Any, field: str) -> list[str]:
    if not isinstance(value, list) or len(value) > 8:
        raise EvidenceError(f"{field}: expected at most 8 reason codes")
    result = []
    for item in value:
        if not isinstance(item, str) or not _REASON.fullmatch(item):
            raise EvidenceError(f"{field}: invalid reason code")
        if item in result:
            raise EvidenceError(f"{field}: duplicate reason code")
        result.append(item)
    return result


def _feature_atom(value: Any, field: str) -> Any:
    if value is None or isinstance(value, bool):
        return value
    if isinstance(value, int) and not isinstance(value, bool) and 0 <= value <= 1_000_000:
        return value
    if isinstance(value, float) and math.isfinite(value) and 0 <= value <= 1_000_000:
        return value
    if isinstance(value, str) and len(value) <= 64 and _FEATURE_NAME.fullmatch(value):
        return value
    if isinstance(value, list) and len(value) <= 16:
        values = [_feature_atom(item, field) for item in value]
        if any(isinstance(item, (dict, list)) for item in values):
            raise EvidenceError(f"{field}: nested feature values are not supported")
        return values
    raise EvidenceError(f"{field}: expected a bounded scalar or identifier list")


def _pair(value: Any, field: str, *, partial: bool) -> dict:
    if value is None:
        return {}
    value = _object(value, field, {"model", "effort"})
    if not value:
        return {}
    if not partial and set(value) != {"model", "effort"}:
        raise EvidenceError(f"{field}: model and effort are both required")
    result = {}
    if "model" in value:
        result["model"] = text(value["model"], field + ".model")
    if "effort" in value:
        result["effort"] = effort(value["effort"])
        if result["effort"] is None:
            raise EvidenceError(f"{field}.effort: must be explicit")
    return result


def _constraints(value: Any, field: str) -> dict:
    if value is None:
        return {}
    value = _object(value, field, SUPPORTED_CONSTRAINTS)
    result = {}
    for key, raw in value.items():
        upper = 1 if key == "min_score" else 100 if key == "quality_loss_pp" else None
        result[key] = number(raw, field + "." + key, upper=upper)
    return result


def _requirements(value: Any, field: str) -> dict:
    if value is None:
        value = {}
    value = _object(value, field, {"capabilities", "constraints", "delegation_allowed"})
    capabilities = value.get("capabilities", [])
    if not isinstance(capabilities, list) or len(capabilities) > MAX_CAPABILITIES:
        raise EvidenceError(f"{field}.capabilities: expected at most {MAX_CAPABILITIES} identifiers")
    capabilities = [_safe_name(item, field + ".capability") for item in capabilities]
    if len(set(capabilities)) != len(capabilities):
        raise EvidenceError(f"{field}.capabilities: duplicate capability")
    delegation = value.get("delegation_allowed", True)
    if not isinstance(delegation, bool):
        raise EvidenceError(f"{field}.delegation_allowed: expected boolean")
    return {"capabilities": capabilities,
            "constraints": _constraints(value.get("constraints"), field + ".constraints"),
            "delegation_allowed": delegation}


def _candidate_capabilities(value: Any, field: str) -> list[dict]:
    if value is None:
        return []
    if not isinstance(value, list) or len(value) > 100:
        raise EvidenceError(f"{field}: expected at most 100 candidate capability records")
    result, seen = [], set()
    for index, item in enumerate(value):
        name = f"{field}[{index}]"
        item = _object(item, name, {"model", "effort", "route_expressible", "capabilities"},
                       {"model", "effort", "route_expressible", "capabilities"})
        model = text(item["model"], name + ".model")
        level = effort(item["effort"])
        if level is None:
            raise EvidenceError(name + ".effort: must be explicit")
        if (model, level) in seen:
            raise EvidenceError(f"{field}: duplicate candidate capability record")
        seen.add((model, level))
        if not isinstance(item["route_expressible"], bool):
            raise EvidenceError(name + ".route_expressible: expected boolean")
        values = item["capabilities"]
        if not isinstance(values, dict) or len(values) > MAX_CAPABILITIES:
            raise EvidenceError(name + f".capabilities: expected at most {MAX_CAPABILITIES} entries")
        normalized = {}
        for key, state in values.items():
            key = _safe_name(key, name + ".capability")
            if state is not True and state is not False and state is not None:
                raise EvidenceError(name + ".capabilities: values must be true, false, or null")
            normalized[key] = state
        result.append({"model": model, "effort": level,
                       "route_expressible": item["route_expressible"],
                       "capabilities": normalized})
    return result


def validate_packets(packets: Any) -> list[dict]:
    """Validate and normalize caller-supplied structured task packets."""
    if not isinstance(packets, list) or not packets or len(packets) > MAX_PACKETS:
        raise EvidenceError(f"packets: expected 1..{MAX_PACKETS} packets")
    result, seen = [], set()
    allowed = {"packet_id", "task_types", "features", "explicit", "baseline",
               "requirements", "capabilities"}
    for index, raw in enumerate(copy.deepcopy(packets)):
        field = f"packets[{index}]"
        raw = _object(raw, field, allowed, {"packet_id", "task_types", "features"})
        packet_id = _safe_name(raw["packet_id"], field + ".packet_id")
        if packet_id in seen:
            raise EvidenceError("packets: duplicate packet_id")
        seen.add(packet_id)
        task_types = raw["task_types"]
        if not isinstance(task_types, list) or not task_types or len(task_types) > 6:
            raise EvidenceError(field + ".task_types: expected 1..6 task types")
        task_types = [_safe_name(item, field + ".task_type") for item in task_types]
        if len(set(task_types)) != len(task_types):
            raise EvidenceError(field + ".task_types: duplicate task type")
        features = raw["features"]
        if not isinstance(features, dict) or len(features) > MAX_FEATURES:
            raise EvidenceError(field + f".features: expected at most {MAX_FEATURES} structured features")
        normalized_features = {}
        for key, item in features.items():
            key = _safe_name(key, field + ".feature")
            lowered = key.lower()
            if lowered in _PROHIBITED_FEATURE_NAMES or lowered.endswith(_PROHIBITED_FEATURE_SUFFIXES):
                raise EvidenceError(field + ".features: prompts, code, paths, and free-form text are not supported")
            item = _object(item, field + ".features." + key, {"value", "provenance"},
                           {"value", "provenance"})
            provenance = item["provenance"]
            if provenance not in PROVENANCE:
                raise EvidenceError(field + ".features: invalid provenance")
            normalized_features[key] = {
                "value": _feature_atom(item["value"], field + ".features." + key + ".value"),
                "provenance": provenance,
            }
        result.append({
            "packet_id": packet_id,
            "task_types": task_types,
            "features": normalized_features,
            "explicit": _pair(raw.get("explicit"), field + ".explicit", partial=True),
            "baseline": _pair(raw.get("baseline"), field + ".baseline", partial=False),
            "requirements": _requirements(raw.get("requirements"), field + ".requirements"),
            "capabilities": _candidate_capabilities(raw.get("capabilities"), field + ".capabilities"),
        })
    return result


def normalize_policy(overrides: Any = None) -> dict:
    if overrides is None:
        return copy.deepcopy(DEFAULT_POLICY)
    overrides = _object(overrides, "policy", set(DEFAULT_POLICY))
    policy = {**copy.deepcopy(DEFAULT_POLICY), **copy.deepcopy(overrides)}
    if policy["schema_version"] != 1 or policy["policy_version"] != "routing-policy-v1":
        raise EvidenceError("policy: unsupported schema or policy version")
    if policy["fallback"] not in {"caller-baseline", "none"}:
        raise EvidenceError("policy.fallback: unsupported fallback")
    if policy["unknown_evidence"] not in {"warn", "strict"}:
        raise EvidenceError("policy.unknown_evidence: expected warn or strict")
    strict = policy["strict_unknown_constraints"]
    if not isinstance(strict, list) or any(item not in SUPPORTED_CONSTRAINTS for item in strict):
        raise EvidenceError("policy.strict_unknown_constraints: unsupported constraint")
    if len(set(strict)) != len(strict):
        raise EvidenceError("policy.strict_unknown_constraints: duplicate constraint")
    policy["strict_unknown_constraints"] = sorted(strict)
    bounds = (("max_packets", 1, MAX_PACKETS),
              ("max_candidates_per_packet", 1, MAX_CANDIDATES_PER_PACKET),
              ("max_snapshot_bytes", 1024, MAX_SEMANTIC_BYTES))
    for key, minimum, maximum in bounds:
        value = policy[key]
        if type(value) is not int or not minimum <= value <= maximum:
            raise EvidenceError(f"policy.{key}: expected integer in {minimum}..{maximum}")
    return policy


def candidate_id(model: str, level: str) -> str:
    return "cand_" + digest({"model": model, "effort": level})[:24]


def _compact_candidate(comparison: dict, candidate_ref: int) -> dict | None:
    columns, pool = comparison.get("candidate_columns", []), comparison.get("candidate_value_pool", [])
    for row in comparison.get("candidate_rows", []):
        if row[0] != candidate_ref:
            continue
        result = {columns[0]: candidate_ref}
        for index, column in enumerate(columns[1:], 1):
            result[column] = pool[row[index]]
        return result
    return None


def _observed_constraint(comparison: dict, candidate: dict, name: str) -> float | None:
    if name == "min_score":
        return candidate.get("score")
    if name == "quality_loss_pp":
        return candidate.get("quality_delta_pp")
    axis = {"max_cost_usd": "cost_usd", "max_duration_seconds": "duration_seconds"}[name]
    axes = comparison.get("expense_axes", [])
    expenses = candidate.get("expenses", [])
    for axis_ref, value in expenses:
        if type(axis_ref) is int and 0 <= axis_ref < len(axes) and axes[axis_ref] == axis:
            return value
    return None


def _constraint_states(evidence: dict, task_types: list[str], candidate_ref: int,
                       limits: dict[str, float]) -> dict[str, set[str]]:
    states = {name: set() for name in limits}
    cohorts = {cohort.get("cohort_id"): cohort for cohort in evidence.get("cohorts", [])
               if isinstance(cohort, dict)}
    for task in evidence.get("tasks", []):
        if task.get("task_type") not in task_types:
            continue
        ids = list(task.get("primary_cohort_ids", []))
        # Support evidence never fills missing primary coverage.
        if not ids or task.get("missing_primary"):
            for name in limits:
                states[name].add("unknown")
        for cohort_id in ids:
            comparison = cohorts.get(cohort_id)
            candidate = _compact_candidate(comparison, candidate_ref) if comparison else None
            for name, limit in limits.items():
                observed = _observed_constraint(comparison, candidate, name) if candidate else None
                if observed is None:
                    state = "unknown"
                elif name == "min_score":
                    state = "within" if observed + 1e-12 >= limit else "exceeds"
                else:
                    state = "within" if observed <= limit + 1e-9 else "exceeds"
                states[name].add(state)
    return states


def derive_packet(packet: dict, candidates: list[dict], evidence: dict, policy: dict) -> dict:
    """Derive eligibility from immutable facts; evidence prose is never interpreted."""
    cap_by_pair = {(item["model"], item["effort"]): item for item in packet["capabilities"]}
    declared = evidence.get("declared_constraints", {})
    required_constraints = ({key: value for key, value in declared.items()
                             if key in SUPPORTED_CONSTRAINTS}
                            if isinstance(declared, dict) else {})
    for key, value in packet["requirements"]["constraints"].items():
        if key not in required_constraints:
            required_constraints[key] = value
        elif key == "min_score":
            required_constraints[key] = max(required_constraints[key], value)
        else:
            required_constraints[key] = min(required_constraints[key], value)
    eligible, excluded, warnings = [], [], []
    for candidate_ref, candidate in enumerate(candidates):
        reasons, cautions = [], []
        model, level = candidate["model"], candidate["effort"]
        explicit = packet["explicit"]
        if "model" in explicit and explicit["model"] != model:
            reasons.append("explicit_model_mismatch")
        if "effort" in explicit and explicit["effort"] != level:
            reasons.append("explicit_effort_mismatch")
        if not packet["requirements"]["delegation_allowed"]:
            reasons.append("delegation_not_allowed")
        capability = cap_by_pair.get((model, level))
        if capability and not capability["route_expressible"]:
            reasons.append("route_not_expressible")
        values = capability["capabilities"] if capability else {}
        for name in packet["requirements"]["capabilities"]:
            state = values.get(name)
            if state is False:
                reasons.append("missing_capability:" + name)
            elif state is not True:
                reasons.append("unknown_capability:" + name)
        states = _constraint_states(evidence, packet["task_types"], candidate_ref,
                                    required_constraints)
        for name, observed in states.items():
            if "exceeds" in observed:
                reasons.append("constraint_exceeded:" + name)
            elif not observed or "unknown" in observed:
                code = "constraint_unknown:" + name
                if policy["unknown_evidence"] == "strict" or name in policy["strict_unknown_constraints"]:
                    reasons.append(code)
                else:
                    cautions.append(code)
        item = {"candidate_id": candidate["candidate_id"], "reasons": sorted(set(reasons))}
        if item["reasons"]:
            excluded.append(item)
        else:
            eligible.append(candidate["candidate_id"])
            if cautions:
                warnings.append({"candidate_id": candidate["candidate_id"],
                                 "reasons": sorted(set(cautions))})
    return {**copy.deepcopy(packet), "eligible": eligible, "excluded": excluded, "warnings": warnings}


def snapshot_identity(snapshot_without_id: dict) -> str:
    return "snap_" + digest(snapshot_without_id)[:32]


def _validate_candidates(value: Any) -> list[dict]:
    if not isinstance(value, list) or not value or len(value) > 100:
        raise EvidenceError("snapshot.candidates: expected 1..100 candidates")
    result, seen_pairs, seen_ids = [], set(), set()
    for index, raw in enumerate(value):
        raw = _object(raw, f"snapshot.candidates[{index}]", {"candidate_id", "model", "effort"},
                      {"candidate_id", "model", "effort"})
        model = text(raw["model"], "candidate.model")
        level = effort(raw["effort"])
        if level is None:
            raise EvidenceError("candidate.effort must be explicit")
        expected_id = candidate_id(model, level)
        if raw["candidate_id"] != expected_id:
            raise EvidenceError("candidate_id does not match model and effort")
        if (model, level) in seen_pairs or expected_id in seen_ids:
            raise EvidenceError("duplicate snapshot candidate")
        seen_pairs.add((model, level)); seen_ids.add(expected_id)
        result.append({"candidate_id": expected_id, "model": model, "effort": level})
    if result != sorted(result, key=lambda item: (item["model"], item["effort"])):
        raise EvidenceError("snapshot candidates must be deterministically ordered")
    return result


def _validate_compact_evidence(evidence: dict, candidates: list[dict]) -> None:
    if evidence.get("projection_version") != 1:
        raise EvidenceError("snapshot evidence requires projection_version=1")
    if evidence.get("encoding") != COMPACT_EVIDENCE_ENCODING:
        raise EvidenceError("snapshot evidence encoding is unsupported")
    sources = evidence.get("sources")
    if (not isinstance(sources, dict) or sources.get("record_encoding") != "columns+value_pool"
            or set(sources) != {"record_encoding", "columns", "value_pool", "rows"}):
        raise EvidenceError("snapshot evidence source table is invalid")
    source_columns, source_pool, source_rows = sources["columns"], sources["value_pool"], sources["rows"]
    if (not isinstance(source_columns, list) or len(set(source_columns)) != len(source_columns)
            or any(not isinstance(key, str) for key in source_columns)
            or not isinstance(source_pool, list) or not isinstance(source_rows, list)):
        raise EvidenceError("snapshot evidence source table is invalid")
    for row in source_rows:
        if (not isinstance(row, list) or len(row) != len(source_columns)
                or any(type(ref) is not int or not 0 <= ref < len(source_pool) for ref in row)):
            raise EvidenceError("snapshot evidence source row is invalid")
    cohorts = evidence.get("cohorts")
    if not isinstance(cohorts, list):
        raise EvidenceError("snapshot evidence cohorts must be an array")
    cohort_ids = set()
    for cohort in cohorts:
        if not isinstance(cohort, dict):
            raise EvidenceError("snapshot evidence cohort must be an object")
        cohort_id = cohort.get("cohort_id")
        if not isinstance(cohort_id, str) or cohort_id in cohort_ids:
            raise EvidenceError("snapshot evidence cohort identity is invalid")
        without_id = {key: value for key, value in cohort.items() if key != "cohort_id"}
        if cohort_id != "cohort_" + digest(without_id)[:24]:
            raise EvidenceError("snapshot evidence cohort identity mismatch")
        cohort_ids.add(cohort_id)
        columns, rows, pool = (cohort.get("candidate_columns"), cohort.get("candidate_rows"),
                               cohort.get("candidate_value_pool"))
        if (not isinstance(columns, list) or not columns or len(set(columns)) != len(columns)
                or columns[0] != "candidate_ref" or "constraints" not in columns
                or not isinstance(rows, list) or not isinstance(pool, list)):
            raise EvidenceError("snapshot evidence cohort matrix is invalid")
        seen_refs = set()
        for row in rows:
            if not isinstance(row, list) or len(row) != len(columns):
                raise EvidenceError("snapshot evidence cohort row is invalid")
            candidate_ref = row[0]
            if (type(candidate_ref) is not int or not 0 <= candidate_ref < len(candidates)
                    or candidate_ref in seen_refs):
                raise EvidenceError("snapshot evidence candidate reference is invalid")
            seen_refs.add(candidate_ref)
            if any(type(ref) is not int or not 0 <= ref < len(pool) for ref in row[1:]):
                raise EvidenceError("snapshot evidence value reference is invalid")
        missing = cohort.get("missing_candidate_refs")
        if (not isinstance(missing, list) or len(set(missing)) != len(missing)
                or any(type(ref) is not int or not 0 <= ref < len(candidates) for ref in missing)):
            raise EvidenceError("snapshot evidence missing-candidate reference is invalid")
    tasks = evidence.get("tasks")
    if not isinstance(tasks, list):
        raise EvidenceError("snapshot evidence tasks must be an array")
    for task in tasks:
        if not isinstance(task, dict):
            raise EvidenceError("snapshot evidence task must be an object")
        text(task.get("task_type"), "snapshot evidence task_type")
        for key in ("primary_cohort_ids", "supporting_cohort_ids", "coverage_cohort_ids"):
            refs = task.get(key)
            if (not isinstance(refs, list) or len(set(refs)) != len(refs)
                    or any(ref not in cohort_ids for ref in refs)):
                raise EvidenceError("snapshot evidence task cohort reference is invalid")
        if any(ref not in task["primary_cohort_ids"] for ref in task["coverage_cohort_ids"]):
            raise EvidenceError("snapshot evidence coverage must reference a primary cohort")
        unmeasured = task.get("unmeasured_candidate_refs")
        if (not isinstance(unmeasured, list) or len(set(unmeasured)) != len(unmeasured)
                or any(type(ref) is not int or not 0 <= ref < len(candidates) for ref in unmeasured)):
            raise EvidenceError("snapshot evidence unmeasured candidate reference is invalid")


def validate_routing_snapshot(snapshot: Any) -> RoutingSnapshot:
    """Validate a portable snapshot and all hashes/derived eligibility."""
    required = {"schema_version", "snapshot_id", "created_at", "expires_at", "client",
                "packet_ids", "inventory_hash", "evidence_hash", "policy_hash",
                "candidates", "packets", "evidence", "policy"}
    snapshot = _object(copy.deepcopy(snapshot), "snapshot", required, required)
    if snapshot["schema_version"] != 1:
        raise EvidenceError("snapshot: expected schema_version=1")
    text(snapshot["client"], "snapshot.client")
    created, expires = epoch(snapshot["created_at"]), epoch(snapshot["expires_at"])
    if expires < created:
        raise EvidenceError("snapshot expiry must not precede creation")
    policy = normalize_policy(snapshot["policy"])
    candidates = _validate_candidates(snapshot["candidates"])
    if not isinstance(snapshot["evidence"], dict):
        raise EvidenceError("snapshot.evidence: expected an object")
    try:
        encoded(snapshot["evidence"])
    except (TypeError, ValueError, RecursionError) as exc:
        raise EvidenceError("snapshot.evidence: not bounded JSON data") from exc
    _validate_compact_evidence(snapshot["evidence"], candidates)
    if snapshot["inventory_hash"] != digest([{"model": c["model"], "effort": c["effort"]} for c in candidates]):
        raise EvidenceError("snapshot inventory hash mismatch")
    if snapshot["evidence_hash"] != digest(snapshot["evidence"]):
        raise EvidenceError("snapshot evidence hash mismatch")
    if snapshot["policy_hash"] != digest(policy):
        raise EvidenceError("snapshot policy hash mismatch")
    raw_packets = snapshot["packets"]
    if not isinstance(raw_packets, list):
        raise EvidenceError("snapshot.packets: expected an array")
    source_packets = []
    for raw in raw_packets:
        if not isinstance(raw, dict):
            raise EvidenceError("snapshot packet must be an object")
        source_packets.append({key: raw[key] for key in
                               ("packet_id", "task_types", "features", "explicit", "baseline",
                                "requirements", "capabilities") if key in raw})
    normalized = validate_packets(source_packets)
    derived = [derive_packet(packet, candidates, snapshot["evidence"], policy) for packet in normalized]
    if raw_packets != derived:
        raise EvidenceError("snapshot packet eligibility or normalization mismatch")
    packet_ids = [packet["packet_id"] for packet in derived]
    if snapshot["packet_ids"] != packet_ids:
        raise EvidenceError("snapshot packet_ids mismatch")
    normalized_snapshot = {**snapshot, "policy": policy, "candidates": candidates,
                           "packets": derived, "packet_ids": packet_ids}
    without_id = {key: value for key, value in normalized_snapshot.items() if key != "snapshot_id"}
    if snapshot["snapshot_id"] != snapshot_identity(without_id):
        raise EvidenceError("snapshot identity mismatch")
    return normalized_snapshot


def _metadata_value(value: Any, field: str, depth: int = 0) -> Any:
    if depth > 4:
        raise EvidenceError(field + ": metadata is too deeply nested")
    if value is None or isinstance(value, bool):
        return value
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    if isinstance(value, float) and math.isfinite(value):
        return value
    if isinstance(value, str):
        if len(value) > 500 or any(ord(ch) < 32 for ch in value):
            raise EvidenceError(field + ": invalid metadata string")
        return value
    if isinstance(value, list) and len(value) <= 32:
        return [_metadata_value(item, field, depth + 1) for item in value]
    if isinstance(value, dict) and len(value) <= 32:
        output = {}
        for key, item in value.items():
            key = _safe_name(key, field + ".key")
            lowered = key.lower()
            if any(part in lowered for part in ("secret", "credential", "api_key", "prompt", "instruction", "source_code", "path")):
                raise EvidenceError(field + ": sensitive or free-form fields are not supported")
            output[key] = _metadata_value(item, field + "." + key, depth + 1)
        return output
    raise EvidenceError(field + ": unsupported metadata value")


def validate_result(snapshot: Any, result: Any) -> AdvisorResult:
    """Validate an advisor response against the exact immutable snapshot."""
    snapshot = validate_routing_snapshot(snapshot)
    required = {"schema_version", "snapshot_id", "backend", "requested_model", "resolved_model",
                "effort", "rankings", "metadata"}
    result = _object(copy.deepcopy(result), "advisor result", required, required)
    if result["schema_version"] != 1 or result["snapshot_id"] != snapshot["snapshot_id"]:
        raise EvidenceError("advisor result schema or snapshot mismatch")
    result["backend"] = _safe_name(result["backend"], "advisor result.backend")
    for key in ("requested_model", "resolved_model"):
        if result[key] is not None:
            result[key] = text(result[key], "advisor result." + key)
    if result["effort"] is not None:
        result["effort"] = effort(result["effort"])
    rankings = result["rankings"]
    if not isinstance(rankings, list) or len(rankings) != len(snapshot["packets"]):
        raise EvidenceError("advisor result requires one ranking per packet")
    packet_map = {packet["packet_id"]: packet for packet in snapshot["packets"]}
    normalized_rankings, seen = [], set()
    for index, item in enumerate(rankings):
        allowed = {"packet_id", "ranking", "ties", "abstained", "reason_codes",
                   "probabilities", "confidence"}
        item = _object(item, f"rankings[{index}]", allowed,
                       allowed - {"ties"})
        packet_id = item["packet_id"]
        if packet_id not in packet_map or packet_id in seen:
            raise EvidenceError("advisor result has unknown or duplicate packet_id")
        seen.add(packet_id)
        packet = packet_map[packet_id]
        eligible = packet["eligible"]
        if not isinstance(item["abstained"], bool) or not isinstance(item["ranking"], list):
            raise EvidenceError("ranking requires array and boolean abstained")
        ranking = item["ranking"]
        if item["abstained"]:
            if ranking:
                raise EvidenceError("abstained ranking must be empty")
        elif len(ranking) != len(eligible) or set(ranking) != set(eligible) or len(set(ranking)) != len(ranking):
            raise EvidenceError("ranking must contain every eligible candidate exactly once")
        ties = item.get("ties", [])
        if not isinstance(ties, list):
            raise EvidenceError("ties must be an array")
        tied, positions = set(), {candidate: pos for pos, candidate in enumerate(ranking)}
        normalized_ties = []
        for group in ties:
            if not isinstance(group, list) or len(group) < 2 or len(set(group)) != len(group):
                raise EvidenceError("tie group requires at least two unique candidates")
            if any(candidate not in positions or candidate in tied for candidate in group):
                raise EvidenceError("tie group contains unknown or repeated candidate")
            group_positions = [positions[candidate] for candidate in group]
            if group_positions != list(range(min(group_positions), max(group_positions) + 1)):
                raise EvidenceError("tie group must be contiguous and follow ranking order")
            tied.update(group); normalized_ties.append(list(group))
        probabilities = item["probabilities"]
        if probabilities is not None:
            if not isinstance(probabilities, dict) or set(probabilities) != set(eligible) | {"abstain"}:
                raise EvidenceError("probabilities require every eligible candidate and abstain")
            total = 0.0
            for key, value in probabilities.items():
                probabilities[key] = number(value, "probability", upper=1)
                total += probabilities[key]
            if not math.isclose(total, 1.0, abs_tol=1e-6, rel_tol=0):
                raise EvidenceError("probabilities must sum to one")
        confidence = item["confidence"]
        if confidence is not None:
            confidence = number(confidence, "confidence", upper=1)
        normalized_rankings.append({"packet_id": packet_id, "ranking": list(ranking),
                                    "ties": normalized_ties, "abstained": item["abstained"],
                                    "reason_codes": _reason_codes(item["reason_codes"], "reason_codes"),
                                    "probabilities": probabilities, "confidence": confidence})
    if seen != set(packet_map):
        raise EvidenceError("advisor result is missing a packet")
    metadata = _metadata_value(result["metadata"], "metadata")
    if not isinstance(metadata, dict):
        raise EvidenceError("metadata must be an object")
    if len(encoded(metadata)) > MAX_METADATA_BYTES:
        raise EvidenceError("advisor result metadata exceeds size limit")
    normalized = {**result, "rankings": normalized_rankings, "metadata": metadata}
    try:
        size = len(encoded(normalized))
    except (TypeError, ValueError, RecursionError) as exc:
        raise EvidenceError("advisor result is not finite JSON") from exc
    if size > snapshot["policy"]["max_snapshot_bytes"]:
        raise EvidenceError("advisor_result_limit_exceeded")
    return normalized
