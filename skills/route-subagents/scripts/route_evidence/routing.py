"""Evidence-local comparison context. This module never selects a configuration."""
from __future__ import annotations

import copy
from collections import defaultdict
from .core import METRICS, EvidenceError, effort, identity, number, text
from .guides import matching_models
from .model_names import matching_diagnostics, resolve_model

TASK_TYPES = {
    "implementation": {"primary": [("deepswe", "all"), ("frontiercode", "extended")], "support": ["cursorbench"]},
    "hard-implementation": {"primary": [("deepswe", "all"), ("frontiercode", "main")], "support": ["cursorbench"]},
    "investigation": {"primary": [("swe-atlas-qna", "all")], "support": ["cursorbench"]},
    "terminal": {"primary": [("terminal-bench", "all")], "support": []},
    "refactoring": {"primary": [("swe-atlas-refactoring", "all")], "support": ["cursorbench", "frontiercode"]},
    "tests": {"primary": [("swe-atlas-tw", "all")], "support": ["deepswe"]},
}
# Caller-declared task limits. They annotate candidates; they never remove one.
CONSTRAINTS = (("max_cost_usd", "cost_usd"), ("max_duration_seconds", "duration_seconds"))


def validate_request(request):
    if not isinstance(request, dict):
        raise EvidenceError("request must be an object")
    allowed = {"task_types", "client", "available", "min_score", "max_cost_usd",
               "max_duration_seconds", "quality_loss_pp", "allow_stale", "harness"}
    if set(request) - allowed:
        raise EvidenceError("unknown request fields: " + ", ".join(sorted(set(request) - allowed)))
    types = request.get("task_types")
    if not isinstance(types, list) or not 1 <= len(types) <= len(TASK_TYPES):
        raise EvidenceError("task_types must list 1..%d task types" % len(TASK_TYPES))
    if len(set(types)) != len(types):
        raise EvidenceError("duplicate task type")
    for value in types:
        text(value, "task_type")
        if value not in TASK_TYPES:
            raise EvidenceError("unknown task type: " + value)
    text(request.get("client"), "client")
    # Every threshold below is optional. A missing one means the caller stated no
    # policy, not that this tool may invent a universal balance on their behalf.
    for field in ("min_score", "max_cost_usd", "max_duration_seconds", "quality_loss_pp"):
        if request.get(field) is not None:
            upper = 1 if field == "min_score" else 100 if field == "quality_loss_pp" else None
            number(request[field], field, upper=upper)
    if "allow_stale" in request and not isinstance(request["allow_stale"], bool):
        raise EvidenceError("allow_stale must be boolean")
    if request.get("harness") is not None:
        text(request["harness"], "harness")
    available = request.get("available")
    if not isinstance(available, list) or not available or len(available) > 100:
        raise EvidenceError("available must be a nonempty current-client inventory (at most 100 entries)")
    aliases, models = {}, set()
    for item in available:
        if not isinstance(item, dict) or set(item) - {"model", "evidence_names", "efforts"}:
            raise EvidenceError("inventory entry supports model, evidence_names, efforts only")
        model = text(item.get("model"), "model")
        if model != item["model"] or model in models:
            raise EvidenceError("duplicate or whitespace-padded inventory model")
        models.add(model)
        names = item.get("evidence_names", [])
        efforts = item.get("efforts")
        if not isinstance(names, list) or len(names) > 20 or not isinstance(efforts, list) or not 1 <= len(efforts) <= 32:
            raise EvidenceError("inventory requires 1..32 efforts and at most 20 evidence names")
        for level in efforts:
            if level is None:
                raise EvidenceError("client effort must be explicit; unknown is not a default")
            effort(level)
        if len(set(map(effort, efforts))) != len(efforts):
            raise EvidenceError("duplicate inventory effort")
        for name in [model, *names]:
            key = identity(text(name, "evidence name"))
            if not key:
                raise EvidenceError("evidence identity must contain Latin letters or digits")
            if key in aliases and aliases[key] != model:
                raise EvidenceError("ambiguous evidence alias in client inventory")
            aliases[key] = model
    return request


def source_ids(request):
    ids = set()
    for name in request["task_types"]:
        spec = TASK_TYPES[name]
        ids |= {s for s, _ in spec["primary"]} | set(spec["support"])
    return sorted(ids)


def route(row):
    return row["runtime_model"], row["effort"]


def routes_json(values):
    return [{"model": model, "effort": level} for model, level in sorted(values)]


def dominates(a, b, axis):
    """Pareto within ONE cohort and ONE expense axis; never across benchmarks."""
    if a.get("score_low") is not None and b.get("score_high") is not None:
        quality_ok = a["score_low"] >= b["score_high"]
    else:
        quality_ok = a["score"] >= b["score"]
    return quality_ok and a[axis] <= b[axis] and (a["score"] > b["score"] or a[axis] < b[axis])


def constraint_flags(row, request, delta_pp):
    """Report every declared limit, including the ones this candidate fails."""
    flags = []
    if request.get("min_score") is not None:
        flags.append({"constraint": "min_score", "limit": request["min_score"], "observed": row["score"],
                      "status": "within" if row["score"] + 1e-12 >= request["min_score"] else "exceeds"})
    if request.get("quality_loss_pp") is not None:
        flags.append({"constraint": "quality_loss_pp", "limit": request["quality_loss_pp"], "observed": delta_pp,
                      "status": "within" if delta_pp <= request["quality_loss_pp"] + 1e-9 else "exceeds"})
    for limit, field in CONSTRAINTS:
        if request.get(limit) is None:
            continue
        observed = row.get(field)
        status = "unknown" if observed is None else "within" if observed <= request[limit] else "exceeds"
        flags.append({"constraint": limit, "limit": request[limit], "observed": observed, "status": status})
    return flags


def describe_cohort(key, by_route, expected, request):
    rows = list(by_route.values())
    best = max(r["score"] for r in rows)
    measured_axes = [axis for axis in METRICS if any(r.get(axis) is not None for r in rows)]
    frontiers = {}
    for axis in measured_axes:
        priced = [r for r in rows if r.get(axis) is not None]
        frontiers[axis] = {route(r) for r in priced if not any(dominates(o, r, axis) for o in priced)}
    candidates = []
    for row in sorted(rows, key=lambda r: (-r["score"], r["runtime_model"], r["effort"])):
        # Quality distance replaces the removed threshold: the caller reads the
        # real gap in this cohort instead of a percentage this tool would guess.
        delta_pp = round((best - row["score"]) * 100, 4)
        expenses = {axis: row[axis] for axis in METRICS if row.get(axis) is not None}
        unmeasured = [axis for axis in measured_axes if row.get(axis) is None]
        dominated = [{"axis": axis, "model": other["runtime_model"], "effort": other["effort"]}
                     for axis in measured_axes if row.get(axis) is not None
                     for other in rows if other.get(axis) is not None and dominates(other, row, axis)]
        candidates.append({
            "model": row["runtime_model"], "effort": row["effort"], "score": row["score"],
            "score_low": row.get("score_low"), "score_high": row.get("score_high"),
            "quality_delta_pp": delta_pp, "expenses": expenses,
            "expense_evidence": "none" if not expenses else "partial" if unmeasured else "measured",
            "unmeasured_expenses": unmeasured, "cost_basis": row.get("cost_basis"),
            "evaluated_at": row.get("evaluated_at"),
            "frontier": [axis for axis in measured_axes if route(row) in frontiers[axis]],
            "dominated_by": dominated, "stale": row["stale"],
            "constraints": constraint_flags(row, request, delta_pp),
            "source_url": row["source_url"]})
    return {"source_id": key[0], "version": key[1], "subset": key[2], "harness": key[3],
            "protocol": key[4], "metric": key[5], "best_observed_score": best,
            "measured_candidates": len(rows), "comparative": len(rows) > 1,
            "expense_axes": measured_axes,
            "missing_candidates": routes_json(expected - by_route.keys()),
            "candidates": candidates, "observations": rows,
            "comparison_basis": "point estimates within this cohort; no statistical non-inferiority claim"}


def collect(request, evidence):
    """One pass over snapshots: cohorts stay tied to their measured conditions."""
    inventory = {identity(name): c for c in request["available"]
                 for name in [c["model"], *c.get("evidence_names", [])]}
    wanted = set(source_ids(request))
    cohorts, statuses, excluded, seen = defaultdict(dict), [], [], set()
    for source in evidence:
        data = source.get("snapshot")
        sid = source["source_id"]
        if sid in seen:
            raise EvidenceError("duplicate source snapshot: " + sid)
        seen.add(sid)
        match_state = ("source_unavailable" if data is None else
                       "source_not_requested" if sid not in wanted else
                       "stale_disallowed" if source["stale"] and not request.get("allow_stale", True) else "loaded")
        diagnostics = matching_diagnostics(sid, data["rows"] if data else [], request["available"],
                                           state=match_state, harness=request.get("harness"))
        statuses.append({**{k: v for k, v in source.items() if k != "snapshot"},
                         "model_matching": diagnostics,
                         **({"acquisition": data["acquisition"]} if data and "acquisition" in data else {}),
                         "benchmark": data.get("benchmark") if data else None,
                         "version": data.get("version") if data else None,
                         "row_count": len(data["rows"]) if data else 0,
                         "warnings": data.get("warnings", []) if data else []})
        if data is None or sid not in wanted or (source["stale"] and not request.get("allow_stale", True)):
            continue
        if sid != data["source_id"]:
            raise EvidenceError("source envelope and snapshot disagree")
        for row in data["rows"]:
            candidate, annotation, match_error = resolve_model(sid, row["model"], inventory)
            if not candidate:
                # Unmatched examples/counts are in the source diagnostics. An
                # ambiguous reviewed/explicit binding is never silently chosen.
                if match_error == "ambiguous_model_identity":
                    excluded.append({"model": row["model"], "effort": row["effort"],
                                     "source_id": sid, "reason": match_error})
                continue
            if row["effort"] is None or row["effort"] not in list(map(effort, candidate["efforts"])):
                excluded.append({"model": row["model"], "effort": row["effort"],
                                 "source_id": sid, "reason": "unknown_or_unavailable_effort"})
                continue
            if request.get("harness") and identity(row["harness"]) != identity(request["harness"]):
                continue
            key = (sid, data["version"], row["subset"], row["harness"], row["protocol"], row["metric"])
            observed = {**row, "runtime_model": candidate["model"], "model_identity": annotation,
                        "source_url": data["source_url"], "stale": source["stale"]}
            if route(observed) in cohorts[key]:
                # Two source labels cannot become two trials or competing prices
                # for the same runtime configuration after alias resolution.
                raise EvidenceError("multiple evidence labels resolve to one configuration in a cohort")
            cohorts[key][route(observed)] = observed
    return cohorts, statuses, excluded


def task_block(name, cohorts, expected, request):
    spec = TASK_TYPES[name]
    primary, support = set(map(tuple, spec["primary"])), set(spec["support"])
    principals, supporting = [], []
    for key, by_route in sorted(cohorts.items()):
        if (key[0], key[2]) in primary:
            principals.append(describe_cohort(key, by_route, expected, request))
        elif key[0] in support:
            supporting.append(describe_cohort(key, by_route, expected, request))
    present = {(c["source_id"], c["subset"]) for c in principals}
    missing_primary = [{"source_id": sid, "subset": subset} for sid, subset in sorted(primary - present)]
    # Coverage is an intersection over primary cohorts, never a union with
    # supporting results: a competitor missing from one table stays visible.
    complete = expected.copy()
    for comparison in principals:
        complete &= {(c["model"], c["effort"]) for c in comparison["candidates"]}
    if missing_primary:
        complete.clear()
    gaps = []
    if missing_primary:
        gaps.append("missing_primary_source_or_subset")
    if expected - complete:
        gaps.append("incomplete_primary_coverage")
    if any(not c["comparative"] for c in principals):
        gaps.append("noncomparative_singleton")
    if any(r["stale"] for c in principals for r in c["observations"]):
        gaps.append("stale_primary_evidence")
    if any(c["expense_evidence"] != "measured" for p in principals for c in p["candidates"]):
        gaps.append("unknown_primary_expense")
    coverage = [{k: c[k] for k in ("source_id", "version", "subset", "harness", "protocol", "metric",
                                   "measured_candidates", "missing_candidates", "comparative",
                                   "expense_axes")} for c in principals]
    return {"task_type": name, "primary_comparisons": principals, "supporting_comparisons": supporting,
            "coverage": coverage, "missing_primary": missing_primary,
            "unmeasured": routes_json(expected - complete), "evidence_gaps": gaps}


def build_context(request: dict, evidence: list[dict], guidance=(), guidance_scope="client") -> dict:
    """Comparative context for the requested task types. No configuration is chosen."""
    validate_request(request)
    expected = {(c["model"], effort(e)) for c in request["available"] for e in c["efforts"]}
    cohorts, statuses, excluded = collect(request, evidence)
    declared = {k: request[k] for k in ("min_score", "quality_loss_pp", "max_cost_usd",
                                        "max_duration_seconds", "harness") if request.get(k) is not None}
    note = ("Declared limits annotate candidates; none is removed from this context."
            if declared else "No limits were declared, so no candidate was filtered by policy.")
    return {"schema_version": 2, "client": request["client"], "task_types": list(request["task_types"]),
            "inventory": routes_json(expected),
            "tasks": [task_block(name, cohorts, expected, request) for name in request["task_types"]],
            "sources": statuses, "excluded": excluded,
            "guidance": guidance_block(guidance, guidance_scope, request["available"]),
            "declared_constraints": declared, "constraint_note": note,
            "warnings": ["Context only: no subagent is launched and no native configuration is changed.",
                         "This tool does not select a model or effort; the caller applies it to the task.",
                         "API dollars, token counts and steps are not subscription quota units.",
                         "Benchmark scores are not probabilities of success on this particular task.",
                         "Different harnesses, subsets and benchmark revisions are never averaged.",
                         "Pareto flags hold inside one cohort and one expense axis only.",
                         "Vendor guidance is quoted publisher text, kept separate from measurements.",
                         "Missing or stale evidence is reported, not imputed; unseen configurations may be better."]}


def guidance_block(views, scope, available=None):
    """Quoted vendor material. Never merged into a measurement or a ranking."""
    documents = []
    for view in sorted(views, key=lambda v: v["source_id"]):
        data = view.get("snapshot")
        if data is None:
            documents.append({"guide_id": view["source_id"], "available": False,
                              "source_url": view["source_url"],
                              "reason": view.get("error") or view.get("refresh"),
                              "next_retry_at": view.get("next_retry_at"),
                              "note": "Acquisition gap, not an absence of published guidance."})
            continue
        documents.append({"guide_id": data["guide_id"], "available": True,
                          "publisher": data["publisher"], "document_title": data["document_title"],
                          "canonical_url": data["canonical_url"], "applies_to": data["applies_to"],
                          "retrieved_at": view.get("last_success_at"), "stale": view["stale"],
                          "content_hash": data["content_hash"],
                          "extractor_version": data["extractor_version"],
                          "applicability": copy.deepcopy(data.get("applicability")),
                          "matched_models": matching_models(data.get("applicability"), available),
                          "document_caveats": data["document_caveats"],
                          "sections": data["retrieved_sections"]})
    return {"evidence_type": "vendor_guidance", "scope": scope, "documents": documents,
            "note": ("Quoted publisher documentation with its provenance. It is the vendor's "
                     "position, not an independent measurement and not an instruction that "
                     "outranks the task: excerpts are material to weigh, and a shortened "
                     "excerpt never drops a caveat. Applicability is registered scope, not "
                     "a vendor quotation or verified host capability. Match its model identities, "
                     "documented surfaces and conditions before transferring advice. Model-scoped "
                     "guidance cannot justify advice for candidates outside matched_models. A null "
                     "applicability is legacy unknown scope, not universal support.")}


def brief(result: dict) -> dict:
    """Drop raw rows and snapshots. Candidates, gaps and limits are never truncated."""
    result = copy.deepcopy(result)
    for source in result.get("sources", []):
        data = source.pop("snapshot", None)
        if not data:
            continue
        if "guide_id" in data:
            source.update(document_title=data["document_title"], canonical_url=data["canonical_url"],
                          sections=len(data["retrieved_sections"]),
                          applicability=copy.deepcopy(data.get("applicability")),
                          extractor_version=data["extractor_version"], content_hash=data["content_hash"])
        else:
            source.update(benchmark=data["benchmark"], version=data["version"],
                          row_count=len(data["rows"]), warnings=data.get("warnings", []))
    for task in result.get("tasks", []):
        for comparison in task["primary_comparisons"] + task["supporting_comparisons"]:
            comparison.pop("observations", None)
    return result
