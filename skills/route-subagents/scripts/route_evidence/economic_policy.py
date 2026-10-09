"""Select among task-adequate routes using comparable measured costs."""
from __future__ import annotations

import math
from graphlib import CycleError, TopologicalSorter
from itertools import combinations

from .advice_contracts import _compact_candidate
from .core import digest
from .decision_contracts import packet_cohort_ids, question_bindings


def _benchmark_preferences(comparisons):
    preferences = {}
    for comparison in comparisons:
        rows = comparison["values"]
        cheapest = min(row["value"] for row in rows)
        comparison["winners"] = sorted(row["candidate_id"] for row in rows if row["value"] == cheapest)
        for left, right in combinations(rows, 2):
            pair = tuple(sorted((left["candidate_id"], right["candidate_id"])))
            winners = preferences.setdefault(pair, set())
            if left["value"] != right["value"]:
                winners.add(min((left, right), key=lambda row: row["value"])["candidate_id"])
    return preferences


def _local_preferences(paired, adequate, objective):
    preferences, comparisons, tradeoffs = {}, [], set()
    if (paired.get("unit") not in {"api_usd", "quota_units"}
            or objective and paired["unit"] != objective["unit"]):
        return preferences, comparisons, tradeoffs
    for row in paired.get("pairwise_comparisons", []):
        if objective and row["unit_basis"] != objective["unit_basis"]:
            continue
        left, right = row["left_candidate_id"], row["right_candidate_id"]
        if left not in adequate or right not in adequate or min(row["left_quality"], row["right_quality"]) <= 0:
            continue
        pair = tuple(sorted((left, right)))
        winners = preferences.setdefault(pair, set())
        comparisons.append(row)
        cost, quality = row["cost_delta"], row["quality_delta"]
        if (cost > 0 and quality <= 0) or (cost == 0 and quality < 0):
            winners.add(left)
        elif (cost < 0 and quality >= 0) or (cost == 0 and quality > 0):
            winners.add(right)
        elif cost != 0:
            tradeoffs.add(pair)
    return preferences, comparisons, tradeoffs


def _comparison_gaps(selected, measured, preferences, tradeoffs):
    successors = {candidate: set() for candidate in measured}
    for pair, preferred in preferences.items():
        for winner in preferred or (() if pair in tradeoffs else pair):
            successors[winner].update(candidate for candidate in pair if candidate != winner)
    reachable, pending = {selected}, [selected]
    while pending:
        for candidate in successors[pending.pop()] - reachable:
            reachable.add(candidate)
            pending.append(candidate)
    unresolved = measured - reachable
    if not unresolved:
        return []
    unknowns = ["cost_groups_incomparable"]
    dependencies = {candidate: set() for candidate in unresolved}
    for pair, preferred in preferences.items():
        for winner in preferred:
            for loser in set(pair) - {winner}:
                if winner in unresolved and loser in unresolved:
                    dependencies[loser].add(winner)
    try:
        tuple(TopologicalSorter(dependencies).static_order())
    except CycleError:
        unknowns.append("cost_cohort_conflict")
    return unknowns


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
    local = next((item for item in snapshot["evidence"].get("task_similarity_evidence", {}).get("packets", [])
                  if item.get("packet_id") == packet["packet_id"]), {})
    paired = local.get("comparison", {})
    objective = packet.get("cost_objective")
    objective_unit = objective["unit"] if objective else paired.get("unit")
    assessment = {**categories, "comparisons": [], "unknowns": [], "status": "no_adequate_route",
                  "objective_unit": objective_unit, "selection_unit": None, "selection_basis": "adequacy_only"}
    if not adequate:
        return None, ["task_adequacy_unknown" if categories["unknown"] else "no_adequate_route"], assessment
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
    benchmark = _benchmark_preferences(comparisons)
    local_preferences, local_comparisons, tradeoffs = _local_preferences(paired, adequate, objective)
    unknowns = ["paired_quality_cost_tradeoff"] if tradeoffs else []
    local_measured = {candidate for pair in local_preferences for candidate in pair}
    if objective_unit == "quota_units" and local_measured != adequate:
        unknowns.append("quota_cost_unknown")
    # A paired chain observation supersedes a benchmark preference for those
    # exact routes only. It cannot promote a winner over unpaired alternatives.
    # Dollar order is only contextual when the requested quota unit is measured.
    active_benchmark = {} if objective_unit == "quota_units" and local_preferences else benchmark
    preferences = {**active_benchmark, **local_preferences}
    if not preferences:
        assessment.update(status="cost_comparison_unknown", comparisons=groups["primary"] or groups["supporting"],
                          unknowns=[*unknowns, "comparable_cost_missing",
                                    *(["alternative_adequacy_unknown"] if categories["unknown"] else [])])
        # This is a qualified adequacy choice, not an asserted economic optimum.
        return min(adequate), ["task_adequate", "comparable_cost_unknown"], assessment
    more_expensive = set()
    measured = set()
    for pair, preferred in preferences.items():
        measured.update(pair)
        for winner in preferred:
            more_expensive.update(candidate for candidate in pair if candidate != winner)
    assessment["comparisons"] = comparisons
    if local_comparisons:
        assessment["local_comparison"] = {"unit": paired["unit"], "pairwise_comparisons": local_comparisons}
        unknowns.append("observational_cost_transfer")
        if any(tuple(sorted(pair)) not in local_preferences for pair in combinations(sorted(adequate), 2)):
            unknowns.append("uncompared_alternatives")
    winners = measured - more_expensive
    if not winners:
        assessment.update(status="cost_cohort_conflict", unknowns=[*unknowns, "cost_cohort_conflict"])
        return None, ["cost_cohort_conflict"], assessment
    selected = min(winners)
    if measured != adequate:
        unknowns.append("adequate_cost_unmeasured")
    if categories["unknown"]:
        unknowns.append("alternative_adequacy_unknown")
    unknowns.extend(_comparison_gaps(selected, measured, preferences, tradeoffs))
    local_selection = any(selected in pair and (preferred or pair not in tradeoffs)
                          for pair, preferred in local_preferences.items())
    benchmark_selection = any(selected in pair and pair not in local_preferences for pair in active_benchmark)
    status = ("paired_local_chain_comparison" if local_selection else "measured_subset_comparison"
              if benchmark_selection else "cost_preference_unknown")
    assessment.update(status=status, unknowns=unknowns,
                      selection_unit=paired["unit"] if local_selection else "api_usd" if benchmark_selection else None,
                      selection_basis="paired_chain_cost" if local_selection else "benchmark_cost"
                                      if benchmark_selection else "adequacy_only")
    codes = ["task_adequate", "paired_chain_cost_selected" if local_selection else "benchmark_cost_selected"
             if benchmark_selection else "cost_preference_unknown"]
    if unknowns:
        codes.append("economic_uncertainty")
    assessment["undominated_candidates"] = sorted(winners)
    if len(winners) > 1 and not {"cost_groups_incomparable", "paired_quality_cost_tradeoff"}.intersection(unknowns):
        codes.append("economic_tie")
    return selected, codes, assessment
