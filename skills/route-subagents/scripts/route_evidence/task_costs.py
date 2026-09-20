"""Observed chain costs and conditional estimates; never converts tokens to quota."""
from __future__ import annotations

import copy
import math
from collections import defaultdict
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
    """Paired observed tasks only; no cheap recommendation from incomparable samples."""
    fallback = {"status": "insufficient_evidence", "baseline": baseline, "recommended": None,
                "unit": unit, "net_benefit": None}
    if not baseline or unit not in {"api_usd", "quota_units"} or overhead is None:
        return fallback
    number(overhead, "routing overhead")
    pair_by_id = {c["candidate_id"]: (c["model"], c["effort"]) for c in candidates}
    if baseline not in pair_by_id:
        return fallback
    indexed = defaultdict(dict)
    ambiguous = set()
    for r in rows:
        if r.get("complete") and r.get("score") is not None and r["costs"].get(unit) is not None:
            key = (r["task_id"], r["comparison_basis"], r["metric"], r["cost_scope"], r.get("unit_basis", {}).get(unit))
            pair = (r["model"], r["effort"])
            if key in indexed[pair]:
                ambiguous.add((pair, key))
            indexed[pair][key] = r
    for pair, key in ambiguous:
        del indexed[pair][key]
    base = indexed[pair_by_id[baseline]]
    comparisons = []
    for ref, pair in pair_by_id.items():
        if ref == baseline:
            continue
        other = indexed[pair]
        keys = base.keys() & other.keys()
        # Comparing response observations cannot prove agent-chain economy.
        keys = [k for k in keys if k[3] == "chain" and k[4] is not None
                and (unit_basis is None or k[4] == unit_basis)]
        cohorts = defaultdict(list)
        for k in keys:
            cohorts[k[1:]].append(k)
        for cohort, common in cohorts.items():
            if len(common) < minimum:
                continue
            quality_delta = mean(other[k]["score"] - base[k]["score"] for k in common)
            saving = mean(base[k]["costs"][unit] - other[k]["costs"][unit] for k in common) - overhead
            comparisons.append({"candidate_id": ref, "n": len(common), "quality_delta": quality_delta,
                "net_benefit": saving, "comparison_basis": cohort[0], "metric": cohort[1], "unit_basis": cohort[-1],
                "supported": quality_delta >= 0 and saving > 0 and mean(other[k]["score"] for k in common) > 0})
    supported = [c for c in comparisons if c["supported"]]
    # Never select a winner by comparing distinct tariffs/metrics/cohorts.
    if supported and len({(c["comparison_basis"], c["metric"], c["unit_basis"]) for c in comparisons}) == 1:
        best = max(supported, key=lambda c: c["net_benefit"])
        return {**fallback, "status": "paired_observational", "recommended": best["candidate_id"],
                "net_benefit": best["net_benefit"], "comparisons": comparisons}
    return {**fallback, "comparisons": comparisons}
