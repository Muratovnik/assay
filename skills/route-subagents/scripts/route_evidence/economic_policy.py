"""Select among task-adequate routes using comparable measured costs."""
from __future__ import annotations

import math

from .advice_contracts import _compact_candidate
from .core import digest
from .decision_contracts import packet_cohort_ids, question_bindings


def select_adequate(snapshot, packet, result):
    bindings = question_bindings(snapshot)
    categories = {key: [] for key in ("adequate", "inadequate", "unknown")}
    for answer in result["answers"]:
        packet_id, candidate_id = bindings[answer["name"]]
        if packet_id == packet["packet_id"]:
            categories[answer["choice"]].append(candidate_id)
    for values in categories.values():
        values.sort()
    adequate = set(categories["adequate"])
    assessment = {**categories, "comparisons": [], "unknowns": [], "status": "no_adequate_route"}
    if not adequate:
        return None, ["task_adequacy_unknown" if categories["unknown"] else "no_adequate_route"], assessment
    local = next((item for item in snapshot["evidence"].get("task_similarity_evidence", {}).get("packets", [])
                  if item.get("packet_id") == packet["packet_id"]), {})
    paired = local.get("comparison", {})
    recommended = paired.get("recommended")
    rows = paired.get("comparisons", [])
    supported = next((row for row in rows if isinstance(row, dict) and row.get("candidate_id") == recommended
                      and row.get("supported") is True), None) if isinstance(rows, list) else None
    if (paired.get("status") == "paired_observational" and recommended in adequate
            and paired.get("baseline") in adequate and paired.get("unit") in {"api_usd", "quota_units"}
            and supported is not None):
        benefit = supported.get("net_benefit")
        if (type(benefit) in (int, float) and math.isfinite(benefit) and benefit > 0
                and supported.get("unit_basis") and type(supported.get("n")) is int and supported["n"] > 0):
            assessment.update(status="paired_local_chain_comparison", local_comparison=paired,
                              unknowns=["observational_cost_transfer", "uncompared_alternatives"])
            return recommended, ["task_adequate", "paired_chain_cost_selected", "economic_uncertainty"], assessment
    refs = {c["candidate_id"]: i for i, c in enumerate(snapshot["candidates"])}
    groups = {"primary": [], "supporting": []}
    for role in groups:
        for cohort in snapshot["evidence"]["cohorts"]:
            if cohort["cohort_id"] not in packet_cohort_ids(snapshot, packet, role):
                continue
            axes = cohort["expense_axes"]
            if "cost_usd" not in axes:
                continue
            axis = axes.index("cost_usd")
            by_basis = {}
            for candidate in sorted(adequate):
                row = _compact_candidate(cohort, refs[candidate]) or {}
                value = next((value for index, value in row.get("expenses", []) if index == axis), None)
                basis = row.get("cost_basis")
                if (value is None or isinstance(value, bool) or not isinstance(value, (int, float))
                        or not math.isfinite(value) or value < 0 or not basis or row.get("stale")):
                    continue
                group = by_basis.setdefault(digest(basis), {"cohort_id": cohort["cohort_id"],
                    "axis": "cost_usd", "cost_basis": basis, "values": []})
                group["values"].append({"candidate_id": candidate, "value": value})
            groups[role].extend(by_basis.values())
    comparisons = [g for g in groups["primary"] if len(g["values"]) > 1]
    if not comparisons:
        comparisons = [g for g in groups["supporting"] if len(g["values"]) > 1]
    if not comparisons:
        assessment.update(status="cost_comparison_unknown", comparisons=groups["primary"] or groups["supporting"],
                          unknowns=["comparable_cost_missing"])
        # This is a qualified adequacy choice, not an asserted economic optimum.
        return min(adequate), ["task_adequate", "comparable_cost_unknown"], assessment
    more_expensive = set()
    measured = set()
    for comparison in comparisons:
        rows = comparison["values"]
        cheapest = min(row["value"] for row in rows)
        ids = {row["candidate_id"] for row in rows if row["value"] == cheapest}
        comparison["winners"] = sorted(ids)
        measured.update(row["candidate_id"] for row in rows)
        # Disjoint cost groups cannot contradict one another. Preserve every
        # within-group strict preference instead of intersecting their minima.
        more_expensive.update(row["candidate_id"] for row in rows if row["value"] > cheapest)
    assessment["comparisons"] = comparisons
    winners = measured - more_expensive
    if not winners:
        assessment.update(status="cost_cohort_conflict", unknowns=["cost_cohort_conflict"])
        return None, ["cost_cohort_conflict"], assessment
    selected = min(winners)
    unknowns = (["adequate_cost_unmeasured"] if measured != adequate else [])
    if categories["unknown"]:
        unknowns.append("alternative_adequacy_unknown")
    if len(winners) > 1 and any(not winners <= {row["candidate_id"] for row in group["values"]}
                              for group in comparisons):
        unknowns.append("cost_groups_incomparable")
    assessment.update(status="measured_subset_comparison", unknowns=unknowns)
    codes = ["task_adequate", "benchmark_cost_selected"]
    if unknowns:
        codes.append("economic_uncertainty")
    assessment["undominated_candidates"] = sorted(winners)
    if len(winners) > 1 and "cost_groups_incomparable" not in unknowns:
        codes.append("economic_tie")
    return selected, codes, assessment
