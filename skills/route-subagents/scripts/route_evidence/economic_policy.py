"""Select among task-adequate routes using comparable measured costs."""
from __future__ import annotations

import math
from graphlib import CycleError, TopologicalSorter
from itertools import combinations

from .advice_contracts import _compact_candidate
from .core import digest
from .decision_contracts import packet_cohort_ids, question_bindings

# Reasoning levels by spend, across clients. A level outside it orders nothing.
EFFORT_SPEND = ("none", "minimal", "low", "medium", "high", "xhigh", "max")


def _primary_measurements(snapshot, packet, refs, candidates):
    """Fresh primary rows of the given routes, one mapping per cohort."""
    measured = []
    for cohort in snapshot["evidence"]["cohorts"]:
        if cohort["cohort_id"] not in packet_cohort_ids(snapshot, packet, "primary"):
            continue
        rows = {}
        for candidate in sorted(candidates):
            row = _compact_candidate(cohort, refs[candidate]) or {}
            score = row.get("score")
            if isinstance(score, (int, float)) and not isinstance(score, bool) and not row.get("stale"):
                rows[candidate] = row
        if rows:
            measured.append((cohort["cohort_id"], rows))
    return measured


def _quality_floor(measured, adequate):
    """Adequate routes whose interval lies wholly below another adequate route's.

    Such a route is measurably worse than an alternative judged able to do the
    task, so a lower price cannot select it. Overlapping or missing intervals
    exclude nothing: a point gap is not evidence of a real difference. A pair
    that cohorts order both ways excludes neither route.
    """
    found = {}
    for cohort_id, rows in measured:
        for candidate, row in rows.items():
            for other, theirs in rows.items():
                if (row.get("score_high") is not None and theirs.get("score_low") is not None
                        and theirs["score_low"] > row["score_high"]):
                    found.setdefault((candidate, other), []).append(cohort_id)
    conflicts = {pair for pair in found if pair[::-1] in found}
    below = {}
    for (candidate, other), cohorts in sorted(found.items()):
        if (candidate, other) not in conflicts:
            below.setdefault(candidate, []).extend({"cohort_id": c, "measured_below": other} for c in cohorts)
    unknowns = ["quality_interval_conflict"] if conflicts else []
    if below and set(below) >= adequate:
        return {}, ["quality_interval_conflict"]
    return below, unknowns


def _unpriced_choice(snapshot, measured, eligible):
    """Without comparable cost: lower effort within a model, then measured quality.

    A model's lower effort spends fewer reasoning tokens and, having passed the
    quality floor, is not measurably worse. Between models only quality is
    known, read in the one primary cohort that measures most of them.
    """
    routes = {c["candidate_id"]: (c["model"], c["effort"]) for c in snapshot["candidates"]}
    rank = lambda candidate: (EFFORT_SPEND.index(routes[candidate][1]) if routes[candidate][1] in EFFORT_SPEND
                              else None)
    lowest = {candidate for candidate in eligible
              if not any(routes[other][0] == routes[candidate][0] and None not in (rank(other), rank(candidate))
                         and rank(other) < rank(candidate) for other in eligible)}
    cohort = max(measured, key=lambda item: (len(lowest & set(item[1])), item[0]), default=(None, {}))[1]
    scores = {candidate: cohort[candidate]["score"] for candidate in lowest if candidate in cohort}
    spend = lambda c: len(EFFORT_SPEND) if rank(c) is None else rank(c)
    return min(lowest, key=lambda c: (c not in scores, -scores.get(c, 0), spend(c), c)), len(lowest) > 1


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
    refs = {c["candidate_id"]: i for i, c in enumerate(snapshot["candidates"])}
    measured_quality = _primary_measurements(snapshot, packet, refs, adequate) if adequate else []
    below, floor_unknowns = _quality_floor(measured_quality, adequate)
    eligible = adequate - set(below)
    local = next((item for item in snapshot["evidence"].get("task_similarity_evidence", {}).get("packets", [])
                  if item.get("packet_id") == packet["packet_id"]), {})
    paired = local.get("comparison", {})
    objective = packet.get("cost_objective")
    objective_unit = objective["unit"] if objective else paired.get("unit")
    assessment = {**categories, "comparisons": [], "unknowns": [], "status": "no_adequate_route",
                  "objective_unit": objective_unit, "selection_unit": None, "selection_basis": "adequacy_only"}
    if not adequate:
        return None, ["task_adequacy_unknown" if categories["unknown"] else "no_adequate_route"], assessment
    if below:
        assessment["quality_floor"] = {"basis": "published_intervals", "excluded": [
            {"candidate_id": candidate, "cohorts": cohorts} for candidate, cohorts in sorted(below.items())]}
        if len(eligible) == 1:
            # Price cannot choose between one remaining route and worse ones.
            assessment.update(status="quality_floor_selected", selection_basis="quality_floor",
                              unknowns=["alternative_adequacy_unknown"] if categories["unknown"] else [])
            return next(iter(eligible)), ["task_adequate", "quality_floor_applied"], assessment
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
            for candidate in sorted(eligible):
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
    local_preferences, local_comparisons, tradeoffs = _local_preferences(paired, eligible, objective)
    unknowns = [*floor_unknowns, *(["paired_quality_cost_tradeoff"] if tradeoffs else [])]
    local_measured = {candidate for pair in local_preferences for candidate in pair}
    if objective_unit == "quota_units" and local_measured != eligible:
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
        selected, tied = _unpriced_choice(snapshot, measured_quality, eligible)
        assessment["selection_basis"] = "measured_quality_without_cost"
        return selected, ["task_adequate", "comparable_cost_unknown",
                          *(["quality_floor_applied"] if below else []),
                          *(["economic_tie"] if tied else [])], assessment
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
        if any(tuple(sorted(pair)) not in local_preferences for pair in combinations(sorted(eligible), 2)):
            unknowns.append("uncompared_alternatives")
    winners = measured - more_expensive
    if not winners:
        assessment.update(status="cost_cohort_conflict", unknowns=[*unknowns, "cost_cohort_conflict"])
        return None, ["cost_cohort_conflict"], assessment
    selected = min(winners)
    if measured != eligible:
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
    if below:
        codes.append("quality_floor_applied")
    if unknowns:
        codes.append("economic_uncertainty")
    assessment["undominated_candidates"] = sorted(winners)
    if len(winners) > 1 and not {"cost_groups_incomparable", "paired_quality_cost_tradeoff"}.intersection(unknowns):
        codes.append("economic_tie")
    return selected, codes, assessment
