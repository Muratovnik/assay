"""Local execution evidence and retrospective views of immutable routing history."""
from __future__ import annotations

import copy
import hashlib
from pathlib import Path

from .core import EvidenceError, digest, encoded, epoch, loads
from .history import (_identifier, _read_json, _receipt_refs, _record_key, _route,
                      _supported_fields, import_history, runtime_identity,
                      _file_parts, _refuse_link_ancestors, _stream_context, _redacted_json)

MAX_RECORDS = 8192
MAX_TRANSCRIPT_BYTES = 16 * 1024 * 1024


def records(store, *, kinds=None, decision_ids=None, predicate=None):
    if store.mode == "off" or not store.root.exists():
        return []
    _refuse_link_ancestors(store.root)
    result = []
    keys = {_record_key(d) for d in decision_ids} if decision_ids is not None else None
    for path in store.root.iterdir():
        parts = _file_parts(path.name)
        if parts is None:
            continue
        if kinds is not None and parts[0] not in kinds:
            continue
        if keys is not None and parts[1] not in keys:
            continue
        value = _read_json(path)
        store._validate_record(value, value.get("decision_id"), parts[0])
        if _record_key(value["decision_id"]) != parts[1]:
            raise EvidenceError("history filename does not match decision")
        if parts[0] == "outcome":
            store._read_outcome_record(path)
        elif parts[0] in {"observation", "assessment"}:
            if path.name != f'{parts[0]}-{parts[1]}-{digest(value.get("supplement_id"))}.json':
                raise EvidenceError("supplement filename does not match identity")
        if epoch(value["expires_at"]) > store.clock() and (predicate is None or predicate(value)):
            if len(result) >= MAX_RECORDS:
                raise EvidenceError("retrospective record limit exceeded; narrow the dataset or time range")
            result.append(value)
    return result


def append(store, kind, decision_id, packet_id, execution_ref, supplement_id, data):
    if store.mode == "off":
        return {"status": "disabled", "persisted": False}
    if kind not in {"observation", "assessment"}:
        raise EvidenceError("unknown history supplement")
    decision = store.read(decision_id)
    if decision is None or epoch(decision["expires_at"]) <= store.clock():
        raise EvidenceError("supplement requires a live retained decision")
    _identifier(packet_id, "packet_id")
    _identifier(execution_ref, "execution_ref")
    _identifier(supplement_id, "supplement_id")
    if packet_id not in {d["packet_id"] for d in decision["decisions"]}:
        raise EvidenceError("supplement packet is not part of decision")
    value = store._base(decision_id, kind)
    value.update(packet_id=packet_id, execution_ref=execution_ref, supplement_id=supplement_id,
                 data=_redacted_json(data, kind), expires_at=decision["expires_at"],
                 dataset=decision.get("dataset", "unspecified"))
    path = store.root / f"{kind}-{_record_key(decision_id)}-{digest(supplement_id)}.json"
    return store._write_immutable(path, value)


def assess(store, request):
    _supported_fields(request, {"decision_id", "packet_id", "execution_ref", "assessment_id",
                               "source", "criteria"}, "assessment")
    if request.get("source") not in {"user", "verification"}:
        raise EvidenceError("assessment.source must be user or verification")
    decision = store.read(request["decision_id"])
    if decision is None:
        raise EvidenceError("unknown assessment decision")
    packet = next((p for p in decision["snapshot"]["packets"] if p["packet_id"] == request["packet_id"]), None)
    criteria = (packet or {}).get("task_spec", {}).get("criteria")
    if not criteria:
        raise EvidenceError("assessment requires retained task acceptance criteria")
    attempts = [r for r in records(store, decision_ids={request["decision_id"]}) if r["decision_id"] == request["decision_id"]
                and r.get("packet_id") == request["packet_id"]]
    execution_ref = request["execution_ref"]
    if not any((r.get("execution_ref") == execution_ref or
                r.get("execution", {}).get("execution_ref") == execution_ref)
               and (r.get("data", {}).get("status") in {"completed", "failed", "interrupted"}
                    or r.get("execution", {}).get("status") in {"completed", "failed", "interrupted"})
               for r in attempts):
        raise EvidenceError("assessment requires an exact terminal attempt")
    supplied = request.get("criteria")
    if not isinstance(supplied, list) or not 1 <= len(supplied) <= 8:
        raise EvidenceError("assessment requires 1..8 criterion results")
    expected = {c["id"] for c in criteria}
    clean, seen = [], set()
    for item in supplied:
        if not isinstance(item, dict):
            raise EvidenceError("criterion result must be an object")
        _supported_fields(item, {"id", "status", "evidence_refs"}, "criterion result")
        ident = _identifier(item.get("id"), "criterion.id")
        if ident not in expected or ident in seen:
            raise EvidenceError("unknown or duplicate acceptance criterion")
        seen.add(ident)
        status = item.get("status")
        if status not in {"pass", "fail", "unknown"}:
            raise EvidenceError("criterion status must be pass, fail or unknown")
        refs = _receipt_refs(item.get("evidence_refs"), "criterion.evidence_refs")
        clean.append({"id": ident, "status": status if refs else "unknown", "evidence_refs": refs})
    statuses = {c["status"] for c in clean}
    verdict = ("rejected" if "fail" in statuses else "accepted"
               if seen == expected and statuses == {"pass"} else "unknown")
    return append(store, "assessment", request["decision_id"], request["packet_id"], execution_ref,
                  request["assessment_id"], {"source": request["source"], "criteria": clean, "verdict": verdict})


def observe_transcript(store, request, *, source="explicit_native_log", status=None):
    _supported_fields(request, {"decision_id", "packet_id", "execution_ref", "runtime", "transcript_path"},
                      "execution observation")
    runtime = runtime_identity(request["runtime"])
    decision = store.read(request["decision_id"])
    if decision is None or decision["snapshot"]["client"] != runtime["client"]:
        raise EvidenceError("execution client does not match retained routing decision")
    if source != "native_hook":
        bound = [r for r in records(store, kinds={"outcome"}, decision_ids={request["decision_id"]}) if r["record_type"] == "outcome"
                 and r["decision_id"] == request["decision_id"] and r["packet_id"] == request["packet_id"]
                 and r["execution"].get("execution_ref") == request["execution_ref"]]
        if not bound or any(r["execution"].get("runtime") != runtime for r in bound):
            raise EvidenceError("native import requires an exact previously bound execution identity")
    peers = bound_attempts(store, runtime["client"], runtime["session_id"],
                          runtime.get("agent_id") or runtime.get("thread_id"),
                          execution_ref=request["execution_ref"], allow_ambiguous=True)
    if any(a["decision_id"] != request["decision_id"] or a["packet_id"] != request["packet_id"]
           or a["execution_ref"] != request["execution_ref"] for a in peers):
        # A resumed worker log can contain earlier calls. Without a native call
        # boundary its complete transcript cannot be attributed to one attempt.
        data = {"source": source, "runtime": runtime, "import_status": "partial", "requests": [],
                "effective_settings": [], "gaps": ["native_identity_reused_across_attempts"]}
        if status is not None:
            data["status"] = status
        return append(store, "observation", request["decision_id"], request["packet_id"], request["execution_ref"],
                      "boundary-" + digest({"runtime": runtime, "execution_ref": request["execution_ref"], "status": status}), data)
    path = Path(request["transcript_path"])
    if not path.is_absolute():
        raise EvidenceError("execution transcript must be an absolute explicitly supplied file")
    _refuse_link_ancestors(path)
    if not path.is_file() or path.stat().st_size > MAX_TRANSCRIPT_BYTES:
        raise EvidenceError("execution transcript missing or exceeds 16 MiB observation limit")
    with path.open("rb") as stream:
        content = stream.read(MAX_TRANSCRIPT_BYTES + 1)
    if len(content) > MAX_TRANSCRIPT_BYTES:
        raise EvidenceError("execution transcript exceeded observation bound while reading")
    imported = import_history([path], _contents={0: content})
    raw_hash, contexts, states = hashlib.sha256(), [], {}
    matched_thread = runtime.get("thread_id") or runtime.get("agent_id")
    read_bytes = 0
    if content:
        for raw in content.splitlines(keepends=True):
            read_bytes += len(raw)
            if read_bytes > MAX_TRANSCRIPT_BYTES or len(raw) > 2 * 1024 * 1024:
                raise EvidenceError("execution transcript exceeded observation bound while reading")
            raw_hash.update(raw)
            try:
                value = loads(raw.decode("utf-8"))
            except (UnicodeError, EvidenceError):
                continue
            if not isinstance(value, dict):
                continue
            if runtime["client"] == "codex":
                _, thread, _, _ = _stream_context(value, states, 0, "codex")
                payload = value.get("payload", {})
                if (thread == matched_thread and value.get("type") == "event_msg"
                        and isinstance(payload, dict) and payload.get("type") == "thread_settings_applied"):
                    applied = payload.get("thread_settings", payload)
                    if not isinstance(applied, dict):
                        continue
                    route = _route({"observed": {"model": applied.get("model"),
                                    "effort": applied.get("reasoning_effort", applied.get("effort")),
                                    "service_tier": applied.get("service_tier")}}, "observed")
                    if route:
                        contexts.append({"route": route, "provenance": "native:thread_settings_applied"})
    matches = []
    for event in imported["requests"]:
        if event["client"] != runtime["client"]:
            continue
        if runtime["client"] == "codex":
            match = event.get("thread_id") == matched_thread
        else:
            match = (event.get("session_id") == runtime["session_id"] and
                     (event.get("thread_id") == matched_thread or
                      source == "native_hook" and event.get("thread_id") is None))
        if match:
            matches.append(event)
    if any(e["code"] == "inherited_owner_boundary_unknown" for e in imported["errors"]):
        contexts = []
    if not matches and not contexts:
        raise EvidenceError("execution transcript has no attributable evidence for this worker identity")
    data = {"source": source, "source_hash": raw_hash.hexdigest(), "runtime": runtime,
            "import_status": imported["status"], "requests": matches, "effective_settings": contexts,
            "gaps": sorted({e["code"] for e in imported["errors"]})}
    if status is not None:
        data["status"] = status
    ident = "native-" + digest({"runtime": runtime, "source_hash": data["source_hash"],
                                "execution_ref": request["execution_ref"], "status": status})
    return append(store, "observation", request["decision_id"], request["packet_id"], request["execution_ref"], ident, data)


def bound_attempts(store, client, session_id, agent_id, *, execution_ref=None, allow_ambiguous=False):
    if not agent_id or not session_id:
        return []
    result = {}
    def matches(record):
        runtime = record.get("execution", record.get("data", {})).get("runtime", {})
        return (runtime.get("client") == client and runtime.get("session_id") == session_id
                and agent_id in {runtime.get("agent_id"), runtime.get("thread_id")})
    for record in records(store, kinds={"outcome", "observation"}, predicate=matches):
        execution = record.get("execution", record.get("data", {}))
        runtime = execution.get("runtime", {})
        if (runtime.get("client") == client and runtime.get("session_id") == session_id
                and agent_id in {runtime.get("agent_id"), runtime.get("thread_id")}):
            ref = execution.get("execution_ref", record.get("execution_ref"))
            if ref:
                key = record["decision_id"], record["packet_id"], ref
                result[key] = {"decision_id": key[0], "packet_id": key[1], "execution_ref": key[2], "runtime": runtime}
    if allow_ambiguous:
        return list(result.values())
    exact = [a for a in result.values() if a["execution_ref"] == execution_ref]
    if exact:
        return exact
    if len(result) > 1:
        raise EvidenceError("worker identity is bound to multiple attempts; no inferred attribution")
    return list(result.values())


def report(store, *, dataset=None, since=None, until=None):
    if dataset is not None and dataset not in {"production", "test", "smoke", "unspecified"}:
        raise EvidenceError("unknown retrospective dataset")
    lower, upper = epoch(since) if since else None, epoch(until) if until else None
    if lower is not None and upper is not None and lower >= upper:
        raise EvidenceError("retrospective since must precede until")
    excluded = 0
    def selected(r):
        nonlocal excluded
        included = ((dataset is None or r.get("dataset", "unspecified") == dataset)
                    and (lower is None or epoch(r["created_at"]) >= lower)
                    and (upper is None or epoch(r["created_at"]) < upper))
        excluded += not included
        return included
    decisions = records(store, kinds={"decision"}, predicate=selected)
    values = decisions + records(store, kinds={"outcome", "observation", "assessment"},
                                 decision_ids={r["decision_id"] for r in decisions})
    supplements, receipts = {}, {}
    for r in values:
        if r["record_type"] == "decision":
            continue
        key = r["decision_id"], r.get("packet_id")
        (receipts if r["record_type"] == "outcome" else supplements).setdefault(key, []).append(r)
    rows = []
    for decision in sorted(decisions, key=lambda d: (d["created_at"], d["decision_id"])):
        packets = {p["packet_id"]: p for p in decision["snapshot"]["packets"]}
        for chosen in decision["decisions"]:
            pid, did = chosen["packet_id"], decision["decision_id"]
            attempts = {}
            for r in receipts.get((did, pid), []):
                ref = r["execution"].get("execution_ref") or "legacy-unidentified"
                a = attempts.setdefault(ref, {"execution_ref": ref, "receipts": [], "observations": [], "assessments": []})
                a["receipts"].append({"created_at": r["created_at"], **r["execution"]})
            for r in supplements.get((did, pid), []):
                ref = r["execution_ref"]
                a = attempts.setdefault(ref, {"execution_ref": ref, "receipts": [], "observations": [], "assessments": []})
                a["observations" if r["record_type"] == "observation" else "assessments"].append(
                    {"created_at": r["created_at"], "id": r["supplement_id"], **r["data"]})
            for a in attempts.values():
                for key in ("receipts", "observations", "assessments"):
                    a[key].sort(key=lambda v: (v["created_at"], v.get("id", "")))
                a["verdict"] = a["assessments"][-1]["verdict"] if a["assessments"] else "unknown"
                events = {e["event_id"]: e for obs in a["observations"] for e in obs.get("requests", [])}
                a["provider_routes"] = list({digest(e["observed"]): e["observed"] for e in events.values() if e["observed"].get("model")}.values())
                a["effective_settings"] = list({digest(c): c for obs in a["observations"] for c in obs.get("effective_settings", [])}.values())
                a["usage_events"] = len(events)
                a["usage"] = {key: sum(e["usage"][key] for e in events.values())
                              if all(key in e["usage"] for e in events.values()) else None
                              for key in {k for e in events.values() for k in e["usage"] if k.endswith("_tokens")}}
                if any(obs.get("import_status") == "partial" for obs in a["observations"]):
                    a["usage"] = None
                a["whole_chain_cost"] = next((r["cost_observation"] for r in reversed(a["receipts"]) if "cost_observation" in r), None)
                a["duration_seconds"] = next((o["duration_seconds"] for o in reversed(a["observations"]) if "duration_seconds" in o), None)
                a["worker_return_usage"] = next((o["reported_usage"] for o in reversed(a["observations"]) if o.get("reported_usage") is not None), None)
            ordered = sorted(attempts.values(), key=lambda a: (min((v["created_at"] for key in ("receipts", "observations") for v in a[key]), default=""), a["execution_ref"]))
            task = packets.get(pid, {})
            selected = chosen.get("selected") or {}
            provider = [route for a in ordered for route in a["provider_routes"]]
            effective = [c["route"] for a in ordered for c in a["effective_settings"]]
            def mismatch(routes):
                comparisons = [route[key] != selected[key] for route in routes for key in ("model", "effort")
                               if route.get(key) is not None and selected.get(key) is not None]
                return any(comparisons) if comparisons else None
            rows.append({"decision_id": did, "packet_id": pid, "created_at": decision["created_at"],
                         "dataset": decision.get("dataset", "unspecified"), "task": task,
                         "selection": chosen, "advisor": decision.get("advisor_result"), "attempts": ordered,
                         "first_attempt_verdict": ordered[0]["verdict"] if ordered else "unknown",
                         "context_retained": bool(task.get("task_spec")),
                         "provider_route_mismatch": mismatch(provider), "effective_route_mismatch": mismatch(effective)})
    evaluated = [r for r in rows if r["first_attempt_verdict"] != "unknown"]
    accepted = sum(r["first_attempt_verdict"] == "accepted" for r in evaluated)
    groups = {}
    for r in rows:
        chosen = r["selection"].get("selected") or {}
        key = (tuple(r["task"].get("task_types", [])), chosen.get("model"), chosen.get("effort"), r["dataset"])
        g = groups.setdefault(key, {"task_types": list(key[0]), "model": key[1], "effort": key[2], "dataset": key[3],
                                    "packets": 0, "evaluated": 0, "accepted": 0})
        g["packets"] += 1
        g["evaluated"] += r["first_attempt_verdict"] != "unknown"
        g["accepted"] += r["first_attempt_verdict"] == "accepted"
    for g in groups.values():
        g["acceptance_rate"] = g["accepted"] / g["evaluated"] if g["evaluated"] else None
    summary = {"packets": len(rows), "decisions": len(decisions), "excluded_filter_decisions": excluded,
               "context_retained": sum(r["context_retained"] for r in rows), "with_attempts": sum(bool(r["attempts"]) for r in rows),
               "with_provider_model": sum(any(a["provider_routes"] for a in r["attempts"]) for r in rows),
               "with_effective_settings": sum(any(a["effective_settings"] for a in r["attempts"]) for r in rows),
               "provider_mismatch_evaluable": sum(r["provider_route_mismatch"] is not None for r in rows),
               "provider_route_mismatches": sum(r["provider_route_mismatch"] is True for r in rows),
               "effective_mismatch_evaluable": sum(r["effective_route_mismatch"] is not None for r in rows),
               "effective_route_mismatches": sum(r["effective_route_mismatch"] is True for r in rows),
               "with_retries": sum(len(r["attempts"]) > 1 for r in rows), "first_attempt_evaluated": len(evaluated),
               "first_attempt_accepted": accepted, "first_attempt_acceptance_rate": accepted / len(evaluated) if evaluated else None,
               "no_decision": sum(r["selection"].get("selected") is None for r in rows)}
    return {"schema_version": 1, "generated_at": store._base("retrospective", "decision")["created_at"],
            "summary": summary, "groups": list(groups.values()), "packets": rows,
            "limits": ["Unobserved execution and acceptance stay unknown.",
                       "Evaluated attempts are a selected sample; acceptance is not causal router accuracy.",
                       "Worker usage excludes advisor, coordination, retries and verification unless separately reported.",
                       "Alternative routes were not executed; counterfactual quality and optimality are unknown."]}
