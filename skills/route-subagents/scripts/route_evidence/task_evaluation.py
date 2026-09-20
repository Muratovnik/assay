"""Offline diagnostics on already measured answers; never generates a model answer."""
from collections import defaultdict
from statistics import mean

from .core import digest, number, epoch, EvidenceError
from .task_evidence import validate_corpus, tokens, cosine


def evaluate(document, unit="api_usd", overhead=None):
    corpus = validate_corpus(document)
    if overhead is not None:
        number(overhead, "overhead")
    groups = defaultdict(list)
    for row in corpus["records"]:
        for obs in row["observations"]:
            if not obs["complete"] or obs["score"] is None or obs["costs"].get(unit) is None:
                continue
            key = (obs["comparison_basis"], obs["metric"], obs["cost_scope"], obs["unit_basis"].get(unit))
            groups[key].append((row, obs))
    reports = []
    for cohort, items in groups.items():
        by_task = defaultdict(dict)
        task_meta = {}
        for row, obs in items:
            key = digest(row["query"].strip().casefold())
            task_meta[key] = row
            route = (obs["model"], obs["effort"])
            if route in by_task[key] and by_task[key][route] != obs:
                raise EvidenceError("duplicate prompt has conflicting observations")
            by_task[key][route] = obs
        routes = set.intersection(*(set(v) for v in by_task.values())) if by_task else set()
        keys = sorted(by_task)
        train, test = keys[::2], keys[1::2]
        if len(routes) < 2 or len(train) < 3 or not test:
            reports.append({"comparison_basis": cohort[0], "status": "insufficient_coverage", "tasks": len(keys), "routes": len(routes)})
            continue
        routes = sorted(routes, key=str)
        baseline = min(routes, key=lambda r: (-mean(by_task[k][r]["score"] for k in train),
                                               mean(by_task[k][r]["costs"][unit] for k in train)))
        results, abstentions = [], 0
        for key in test:
            neighbors = sorted(((cosine(tokens(task_meta[key]["query"]), tokens(task_meta[t]["query"])), t)
                                for t in train if set(task_meta[t]["task_types"]) & set(task_meta[key]["task_types"])), reverse=True)
            neighbors = [t for sim,t in neighbors[:32] if sim >= .15]
            selected = baseline
            if len(neighbors) >= 3:
                predicted = {r: mean(by_task[t][r]["score"] for t in neighbors) for r in routes}
                eligible = [r for r in routes if predicted[r] >= predicted[baseline] and predicted[r] > 0]
                if eligible:
                    selected = min(eligible, key=lambda r: mean(by_task[t][r]["costs"][unit] for t in neighbors))
                else:
                    abstentions += 1
            else:
                abstentions += 1
            results.append((by_task[key][baseline], by_task[key][selected]))
        q_base = mean(b["score"] for b,_ in results)
        q_new = mean(r["score"] for _,r in results)
        saving = mean(b["costs"][unit] - r["costs"][unit] for b,r in results)
        reports.append({"comparison_basis": cohort[0], "metric": cohort[1], "cost_scope": cohort[2],
            "unit_basis": cohort[3], "status": "offline_observation", "train_tasks": len(train), "test_tasks": len(test),
            "baseline": list(baseline), "baseline_quality": q_base, "selected_quality": q_new,
            "gross_saving_per_task": saving, "net_saving_per_task": saving-overhead if overhead is not None else None,
            "quality_losses": sum(r["score"] < b["score"] for b,r in results), "abstentions": abstentions,
            "sample_supports_benefit": overhead is not None and saving > overhead and q_new >= q_base})
    return {"schema_version": 1, "status": "diagnostic_only", "unit": unit, "reports": reports,
            "model_calls": 0, "limitations": ["single_small_split_not_statistical_proof", "not_native_advisor_evaluation",
                "public_response_costs_not_subscription_quota", "lexical_baseline_only", "no_activation_authority"]}


def forecast(rows, unit="api_usd", minimum=3):
    """Walk forward through completed chains, never use future or same-time outcomes."""
    groups = defaultdict(list)
    for row in rows:
        key = (row["model"], row["effort"], row["comparison_basis"], row["metric"], row["unit_basis"].get(unit))
        groups[key].append(row)
    reports = []
    for key, values in groups.items():
        values.sort(key=lambda r: epoch(r["observed_at"]))
        seen, history, errors = set(), [], []
        for row in values:
            chain = row.get("chain_id", row["task_id"])
            if chain in seen:
                raise EvidenceError("duplicate chain in chronological evaluation")
            seen.add(chain)
            if not row["complete"] or row["costs"].get(unit) is None:
                continue
            before = [r for r in history if epoch(r["observed_at"]) < epoch(row["observed_at"])]
            if len(before) >= minimum:
                predicted = mean(r["costs"][unit] for r in before)
                actual = row["costs"][unit]
                errors.append((actual, predicted, predicted-actual))
            history.append(row)
        reports.append({"model": key[0], "effort": key[1], "comparison_basis": key[2], "unit_basis": key[4],
            "status": "observed" if errors else "insufficient_coverage", "chains": len(values),
            "predicted_chains": len(errors), "coverage": len(errors)/len(values),
            "mean_absolute_error": mean(abs(e) for _,_,e in errors) if errors else None,
            "underestimated_chains": sum(e < 0 for _,_,e in errors),
            "largest_underestimate": max((max(0,-e) for _,_,e in errors), default=None),
            "highest_actual_cost": max((a for a,_,_ in errors), default=None)})
    return {"schema_version": 1, "status": "diagnostic_only", "unit": unit, "reports": reports,
            "model_calls": 0, "counterfactual_savings": None, "method": "strictly_earlier_same_cohort_mean"}
