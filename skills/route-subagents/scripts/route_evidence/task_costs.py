"""Observed chain costs and conditional estimates; never converts tokens to quota."""
from __future__ import annotations

import copy
import math
from collections import defaultdict
from itertools import combinations
from statistics import mean

from .core import EvidenceError, number
from .advice_contracts import _safe_name, _pair

UNITS = {"input_tokens", "cached_input_tokens", "output_tokens", "reasoning_output_tokens",
         "api_usd", "quota_units", "duration_seconds"}
CATEGORIES = {"routing", "worker", "verification", "coordination"}


def validate_cost_observation(value):
    """One immutable terminal receipt covers a whole packet chain, including failures."""
    keys = {"schema_version", "complete", "initial_route", "comparison_basis", "unit_basis", "events"}
    if not isinstance(value, dict) or set(value) - (keys | {"comparison_task"}) or keys - set(value) or value["schema_version"] != 1:
        raise EvidenceError("invalid cost observation schema")
    out = copy.deepcopy(value)
    if type(out["complete"]) is not bool:
        raise EvidenceError("cost complete must be boolean")
    out["initial_route"] = _pair(out["initial_route"], "initial_route", partial=False)
    if not out["initial_route"]:
        raise EvidenceError("initial route is required")
    if "comparison_task" in out:
        _safe_name(out["comparison_task"], "comparison_task")
    out["comparison_basis"] = _safe_name(out["comparison_basis"], "comparison_basis")
    basis = out["unit_basis"]
    if not isinstance(basis, dict) or set(basis) - UNITS:
        raise EvidenceError("invalid unit basis")
    for unit, label in basis.items():
        _safe_name(label, "unit_basis")
    events = out["events"]
    if not isinstance(events, list) or not 1 <= len(events) <= 256:
        raise EvidenceError("cost events require 1..256 observations")
    seen = set()
    for event in events:
        if not isinstance(event, dict) or set(event) != {"event_id", "category", "resources"}:
            raise EvidenceError("invalid cost event")
        ref = _safe_name(event["event_id"], "event_id")
        if ref in seen or event["category"] not in CATEGORIES:
            raise EvidenceError("duplicate cost event or invalid category")
        seen.add(ref)
        resources = event["resources"]
        if not isinstance(resources, dict) or not resources or set(resources) - UNITS:
            raise EvidenceError("invalid cost resources")
        for unit, amount in resources.items():
            if amount is not None:
                number(amount, unit)
                if unit.endswith("tokens") and type(amount) is not int:
                    raise EvidenceError("token counts must be integers")
                if unit in {"api_usd", "quota_units"} and unit not in basis:
                    raise EvidenceError("priced resources require a unit basis")
        for subset, total in (("cached_input_tokens", "input_tokens"),
                              ("reasoning_output_tokens", "output_tokens")):
            if resources.get(subset) is not None and (resources.get(total) is None or resources[subset] > resources[total]):
                raise EvidenceError("resource subset exceeds total")
    if out["complete"] and {e["category"] for e in events} != CATEGORIES:
        raise EvidenceError("complete chain requires all cost categories, including observed zeros")
    return out


def chain_totals(observation):
    obs = validate_cost_observation(observation)
    units = set().union(*(e["resources"] for e in obs["events"]))
    # Missing resources in even one event make that chain's total unknown.
    totals = {u: (sum(e["resources"][u] for e in obs["events"])
                  if all(e["resources"].get(u) is not None for e in obs["events"]) else None)
              for u in units}
    components = {}
    for category in sorted(CATEGORIES):
        rows = [e for e in obs["events"] if e["category"] == category]
        components[category] = {u: (sum(e["resources"][u] for e in rows)
                                     if rows and all(e["resources"].get(u) is not None for e in rows) else None)
                                for u in units}
    return {"totals": totals, "components": components, "complete": obs["complete"],
            "comparison_basis": obs["comparison_basis"], "unit_basis": obs["unit_basis"]}


def distribution(values):
    values = sorted(values)
    if not values:
        return None
    return {"mean": mean(values), "min": values[0], "max": values[-1],
            "p90": values[max(0, math.ceil(.9 * len(values)) - 1)], "n": len(values),
            "method": "empirical_not_confidence_interval"}


def estimates(rows, candidates, *, minimum=3):
    """Group exact routes/conditions/units; partial and unknown outcomes remain visible."""
    result = []
    for candidate in candidates:
        matching = [r for r in rows if r["model"] == candidate["model"] and r["effort"] == candidate["effort"]]
        groups = defaultdict(list)
        for row in matching:
            groups[(row["comparison_basis"], row["metric"], row["cost_scope"],
                    tuple(sorted(row.get("unit_basis", {}).items())))].append(row)
        entry = {"candidate_id": candidate["candidate_id"], "groups": []}
        for (basis, metric, scope, units), group in sorted(groups.items()):
            known = [r["score"] for r in group if r.get("score") is not None]
            full = [r for r in group if r.get("complete", False)]
            cost_units = set().union(*(r["costs"] for r in full)) if full else set()
            costs = {u: distribution([r["costs"][u] for r in full if r["costs"].get(u) is not None]) for u in sorted(cost_units)}
            entry["groups"].append({"comparison_basis": basis, "metric": metric, "cost_scope": scope,
                "unit_basis": dict(units), "observations": len(group), "partial": len(group) - len(full),
                "unknown_quality": len(group) - len(known), "quality": distribution(known),
                "expected_cost": costs, "status": "observed" if len(full) >= minimum and len(known) >= minimum else "insufficient_coverage",
                "selection_bias": "observational_not_causal", "cost_components": {
                    cat: {u: distribution([r.get("components", {}).get(cat, {}).get(u) for r in full
                        if r.get("components", {}).get(cat, {}).get(u) is not None]) for u in sorted(cost_units)}
                    for cat in sorted(CATEGORIES)} if scope == "chain" else {}})
        entry["status"] = "available" if entry["groups"] else "unknown"
        result.append(entry)
    return result


def compare(rows, candidates, baseline, unit, overhead, *, minimum=3, unit_basis=None):
    """Exact paired chain evidence is independent of a caller's fallback route."""
    fallback = {"status": "insufficient_evidence", "baseline": baseline, "recommended": None,
                "unit": unit, "net_benefit": None, "pairwise_comparisons": []}
    if unit not in {"api_usd", "quota_units"}:
        return fallback
    if overhead is not None:
        number(overhead, "routing overhead")
    pair_by_id = {c["candidate_id"]: (c["model"], c["effort"]) for c in candidates}
    indexed = defaultdict(dict)
    ambiguous = set()
    for r in rows:
        basis = r.get("unit_basis", {}).get(unit)
        if (r.get("complete") and r.get("score") is not None and r["costs"].get(unit) is not None
                and r["cost_scope"] == "chain" and basis is not None
                and (unit_basis is None or basis == unit_basis)):
            key = (r["task_id"], r["comparison_basis"], r["metric"], basis)
            pair = (r["model"], r["effort"])
            if key in indexed[pair]:
                ambiguous.add((pair, key))
            indexed[pair][key] = r
    for pair, key in ambiguous:
        del indexed[pair][key]
    paired = []
    for left_id, right_id in combinations(sorted(pair_by_id), 2):
        left, right = indexed[pair_by_id[left_id]], indexed[pair_by_id[right_id]]
        cohorts = defaultdict(list)
        for k in sorted(left.keys() & right.keys()):
            cohorts[k[1:]].append(k)
        for cohort, common in sorted(cohorts.items()):
            if len(common) < minimum:
                continue
            paired.append({"left_candidate_id": left_id, "right_candidate_id": right_id,
                "n": len(common), "comparison_basis": cohort[0], "metric": cohort[1], "unit_basis": cohort[2],
                "quality_delta": mean(right[k]["score"] - left[k]["score"] for k in common),
                "cost_delta": mean(right[k]["costs"][unit] - left[k]["costs"][unit] for k in common),
                "left_quality": mean(left[k]["score"] for k in common),
                "right_quality": mean(right[k]["score"] for k in common)})
    fallback["pairwise_comparisons"] = paired
    # Measured chain costs already include their observed routing events. New
    # incremental overhead belongs only in this legacy baseline-benefit report.
    if baseline not in pair_by_id or overhead is None:
        return fallback
    comparisons = []
    for pair in paired:
        if baseline == pair["left_candidate_id"]:
            ref, sign, quality = pair["right_candidate_id"], 1, pair["right_quality"]
        elif baseline == pair["right_candidate_id"]:
            ref, sign, quality = pair["left_candidate_id"], -1, pair["left_quality"]
        else:
            continue
        quality_delta = sign * pair["quality_delta"]
        saving = -sign * pair["cost_delta"] - overhead
        comparisons.append({"candidate_id": ref, "n": pair["n"], "quality_delta": quality_delta,
            "net_benefit": saving, "comparison_basis": pair["comparison_basis"], "metric": pair["metric"],
            "unit_basis": pair["unit_basis"], "supported": quality_delta >= 0 and saving > 0 and quality > 0})
    supported = [c for c in comparisons if c["supported"]]
    # Never select a winner by comparing distinct tariffs/metrics/cohorts.
    if supported and len({(c["comparison_basis"], c["metric"], c["unit_basis"]) for c in comparisons}) == 1:
        best = max(supported, key=lambda c: c["net_benefit"])
        return {**fallback, "status": "paired_observational", "recommended": best["candidate_id"],
                "net_benefit": best["net_benefit"], "comparisons": comparisons}
    return {**fallback, "comparisons": comparisons}
