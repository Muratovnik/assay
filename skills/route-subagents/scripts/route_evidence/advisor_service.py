"""Bounded advisor lifecycle shared by CLI and MCP. Never launches an agent."""
from __future__ import annotations

import asyncio
import copy
import importlib.metadata
import re
import threading
import time
import uuid
from collections import OrderedDict

from .advice import build_snapshot, decide, semantic_key
from .advice_contracts import validate_packets, validate_result
from .advisor_config import settings
from .core import EvidenceError, digest, encoded, epoch, timestamp
from .history import HistoryStore
from .routing import brief


class AdvisorWorkflow:
    def __init__(self, service, config=None):
        self.service = service
        self.settings = settings(config)
        self.advisor = self.settings["advisor"]
        self.policy = self.settings["policy"]
        self.clock = service.clock
        self.history = HistoryStore(service.cache.root, clock=self.clock, **self.settings["telemetry"])
        from .task_evidence import TaskEvidence
        self.task_evidence = TaskEvidence(service.cache.root, (config or {}).get("task_evidence"),
                                          history=self.history, clock=self.clock)
        from .task_bootstrap import CorpusProvisioner
        self.task_evidence.provisioner = CorpusProvisioner(self.task_evidence, offline=service.offline)
        self.history.retain_descriptions = self.task_evidence.config["retain_descriptions"]
        self._states = OrderedDict()
        self._cache = OrderedDict()
        self._lock = threading.RLock()
        self._jev = None

    def status(self):
        try:
            sdk = importlib.metadata.version("typesafe-sdk")
        except importlib.metadata.PackageNotFoundError:
            sdk = None
        with self._lock:
            self._expire()
            pending = sum(s["state"] in ("prepared", "awaiting_native_advice", "requesting_provider")
                          for s in self._states.values())
        return {"enabled": self.advisor["enabled"], "backend": self.advisor["backend"],
                "native_route": "caller_must_resolve", "jev_enabled": self.advisor["jev"]["enabled"],
                "external_data_consent": self.advisor["jev"]["external_data_consent"],
                "optional_sdk_version": sdk, "telemetry": copy.deepcopy(self.settings["telemetry"]),
                "pending": pending, "max_pending": self.advisor["max_pending"],
                "usage": "diagnostic_only" if self.service.offline else "routing",
                "launches_agents": False,
                "task_evidence": {**{k: self.task_evidence.config[k] for k in
                                  ("enabled", "mode", "deadline_seconds", "retain_descriptions", "auto_download")},
                                  "acquisition": self.task_evidence.provisioner.status()}}

    def _expire(self):
        now = self.clock()
        for state in self._states.values():
            if state["state"] in ("prepared", "awaiting_native_advice", "requesting_provider") and now >= state["expires"]:
                state["state"] = "expired"
        for key in list(self._cache):
            if now >= self._cache[key]["expires"]:
                del self._cache[key]
        # Pending entries are never evicted to make room for another request.
        while len(self._states) > 128:
            removable = next((key for key, value in self._states.items()
                              if value["state"] not in ("prepared", "awaiting_native_advice", "requesting_provider")), None)
            if removable is None:
                break
            del self._states[removable]

    def _finish(self, state, result=None, *, reason=None, cache=False):
        snapshot = state["snapshot"]
        decisions = decide(snapshot, result, reason=reason, offline=self.service.offline)
        if reason in ("snapshot_expired", "inventory_changed", "configuration_changed"):
            # A baseline validated against old state is no longer an executable
            # fallback. Reprepare instead of quietly authorizing the old pair.
            for decision in decisions:
                decision.update(status="no_decision", selected=None, reason_codes=[reason, "reprepare_required"],
                                fallback={"status": "needs_revalidation", "selected": None, "reason": reason})
        response = {"schema_version": 1, "decision_id": state["id"], "snapshot_id": snapshot["snapshot_id"],
                    "status": "decided" if all(d.get("selected") for d in decisions) else "no_decision",
                    "usage": "diagnostic_only" if self.service.offline else "routing",
                    "decisions": decisions, "expires_at": snapshot["expires_at"],
                    "advisor_result": result, "launch_verified": False}
        if "task_evidence_status" in state:
            response["task_evidence_status"] = state["task_evidence_status"]
        if self.service.offline:
            response["status"] = "diagnostic_only"
        state.update(state=response["status"], response=response, result_hash=digest(result), result=copy.deepcopy(result))
        if not self.service.offline:
            try:
                self.history.write_decision(state["id"], snapshot, result, decisions,
                                            retrieval_seconds=state.get("retrieval_seconds"))
            except (EvidenceError, OSError):
                response["telemetry_status"] = "write_failed"
        if cache and result is not None and state.get("cache_key"):
            self._cache[state["cache_key"]] = {"result": copy.deepcopy(result), "expires": state["expires"],
                                               "packet_ids": snapshot["packet_ids"]}
            while len(self._cache) > 64:
                self._cache.popitem(last=False)
        return copy.deepcopy(response)

    async def prepare_routing(self, packets, *, available=None, constraints=None, advisor_route=None, portable=False,
                              task_queries=None, cost_objectives=None):
        packets = validate_packets(packets)
        from .task_evidence import validate_queries
        task_queries = validate_queries(task_queries, [p["packet_id"] for p in packets])
        task_types = list(dict.fromkeys(t for packet in packets for t in packet["task_types"]))
        request = self.service.prepare(task_types, available=available, constraints=constraints)
        if "status" in request:
            return {**request, "usage": "setup_required"}
        now = self.clock()
        with self._lock:
            self._expire()
            pending = sum(s["state"] in ("prepared", "awaiting_native_advice", "requesting_provider")
                          for s in self._states.values())
            if pending >= self.advisor["max_pending"]:
                return {"status": "busy", "reason": "pending_limit", "usage": "setup_required"}
            decision_id = uuid.uuid4().hex
            state = {"id": decision_id, "state": "prepared", "expires": now + self.advisor["pending_seconds"],
                     "inventory": copy.deepcopy(self.service._inventory), "request": request,
                     "settings_hash": digest(self.settings)}
            self._states[decision_id] = state
        try:
            context = brief(await self.service.context(request))
            now = self.clock()
            deadlines = [state["expires"], epoch(state["inventory"]["observed_at"]) + 86400]
            # Only known source freshness has a deadline. Missing measurements
            # remain unknown and cannot manufacture a freshness guarantee.
            deadlines.extend(epoch(source["last_success_at"]) + self.service.cache.ttl
                             for source in context.get("sources", []) if source.get("last_success_at"))
            state["expires"] = min(deadlines)
            limit_reason = None
            try:
                snapshot = build_snapshot(context, packets, policy=self.policy, client=self.service.client,
                                          created_at=timestamp(now), expires_at=timestamp(max(now, state["expires"])))
                if self.task_evidence.config["enabled"]:
                    from .task_evidence import attach_summary
                    retrieval_started = time.monotonic()
                    summary = await self.task_evidence.async_summarize(snapshot["packets"], snapshot["candidates"], task_queries, cost_objectives)
                    state["retrieval_seconds"] = time.monotonic() - retrieval_started
                    snapshot = attach_summary(snapshot, summary)
                    state["task_evidence_status"] = (summary["status"] if "task_similarity_evidence" in snapshot["evidence"]
                                                       else "omitted_snapshot_budget")
            except EvidenceError as exc:
                snapshot = getattr(exc, "snapshot", None)
                if snapshot is None:
                    raise
                limit_reason = str(exc).split(":", 1)[0]
            state["snapshot"] = snapshot
            with self._lock:
                if self.service.offline:
                    return self._finish(state, reason="offline")
                if state["expires"] <= now:
                    return self._finish(state, reason="snapshot_expired")
                if limit_reason:
                    return self._finish(state, reason=limit_reason)
                preflight = decide(snapshot, reason="advisor_required")
                if all(d.get("decision_type") in ("explicit_user_choice", "single_eligible")
                       or not p["eligible"] for d, p in zip(preflight, snapshot["packets"])):
                    return self._finish(state, reason="no_advisor_needed")
                if not self.advisor["enabled"]:
                    return self._finish(state, reason="advisor_disabled")
                task_packets = snapshot["evidence"].get("task_similarity_evidence", {}).get("packets", [])
                if len(task_packets) == len(snapshot["packets"]) and task_packets and all(
                    p.get("comparison", {}).get("comparisons") and
                    all(c["net_benefit"] <= 0 for c in p["comparison"]["comparisons"]) and
                    p["comparison"].get("baseline") and
                    {c["candidate_id"] for c in p["comparison"]["comparisons"]} ==
                    {c["candidate_id"] for c in snapshot["candidates"]} - {p["comparison"]["baseline"]}
                    for p in task_packets):
                    return self._finish(state, reason="cost_no_benefit")
            if self.advisor["backend"] == "native-economy":
                from .advisors.native import prepare_native
                try:
                    handoff = prepare_native(snapshot, advisor_route, available=request["available"])
                except EvidenceError:
                    return self._finish(state, reason="invalid_advisor_route_or_payload")
                if handoff.get("status") == "needs_advisor_route":
                    response = self._finish(state, reason="needs_advisor_route")
                    response.update(status="needs_advisor_route", setup=handoff)
                    state["response"] = copy.deepcopy(response)
                    return response
                descriptor = handoff.get("descriptor") or {
                    "backend": "native-economy", "model": advisor_route["model"], "effort": advisor_route["effort"],
                    "prompt_version": "native-ranking-v1", "schema_version": 1, "privacy_profile": "native-structured"}
                state["advisor_route"] = copy.deepcopy(advisor_route)
                state["descriptor"] = descriptor
                state["cache_key"] = semantic_key(snapshot, descriptor)
                cached = self._cached(state)
                if cached is not None:
                    return cached
                state["state"] = "awaiting_native_advice"
                response = {"schema_version": 1, "status": "awaiting_native_advice", "usage": "routing",
                            "decision_id": decision_id, "snapshot_id": snapshot["snapshot_id"],
                            "expires_at": snapshot["expires_at"], "handoff": handoff,
                            "launch_verified": False}
                if "task_evidence_status" in state:
                    response["task_evidence_status"] = state["task_evidence_status"]
                if portable:
                    response["envelope"] = self._envelope(state)
                return response
            from .advisors.jev import JevAdapter
            if self._jev is None:
                self._jev = JevAdapter(self.advisor["jev"], clock=self.clock)
            descriptor = self._jev.descriptor()
            state["descriptor"] = descriptor
            state["cache_key"] = semantic_key(snapshot, descriptor)
            cached = self._cached(state)
            if cached is not None:
                return cached
            state["state"] = "requesting_provider"
            try:
                result = await self._jev.recommend(snapshot)
                result = validate_result(snapshot, result)
            except EvidenceError as exc:
                return self._finish(state, reason=getattr(exc, "code", "advisor_failed"))
            if self.clock() >= state["expires"]:
                return self._finish(state, reason="snapshot_expired")
            if self.service._inventory and self.service._inventory["available"] != state["inventory"]["available"]:
                return self._finish(state, reason="inventory_changed")
            return self._finish(state, result, cache=True)
        except asyncio.CancelledError:
            with self._lock:
                state["state"] = "interrupted"
            raise
        except BaseException:
            with self._lock:
                state["state"] = "failed"
            raise

    def _cached(self, state):
        with self._lock:
            hit = self._cache.get(state["cache_key"])
            if hit is None or self.clock() >= hit["expires"]:
                return None
            result = copy.deepcopy(hit["result"])
            result["snapshot_id"] = state["snapshot"]["snapshot_id"]
            packet_map = dict(zip(hit["packet_ids"], state["snapshot"]["packet_ids"]))
            for ranking in result["rankings"]:
                ranking["packet_id"] = packet_map[ranking["packet_id"]]
            result = validate_result(state["snapshot"], result)
            response = self._finish(state, result)
            response["cache_hit"] = True
            state["response"] = copy.deepcopy(response)
            return response

    def _envelope(self, state):
        payload = {key: copy.deepcopy(state[key]) for key in (
            "id", "snapshot", "inventory", "request", "settings_hash", "advisor_route", "descriptor", "cache_key")}
        payload["schema_version"] = 1
        if len(encoded(payload)) > 262144:
            raise EvidenceError("portable_envelope_limit_exceeded")
        return {"payload": payload, "checksum": digest(payload),
                "authority": "integrity_only_not_execution_permission"}

    def _restore(self, decision_id, envelope):
        from .advice_contracts import validate_routing_snapshot
        if not isinstance(envelope, dict) or set(envelope) != {"payload", "checksum", "authority"}:
            raise EvidenceError("invalid portable envelope")
        if len(encoded(envelope)) > 262144 or digest(envelope["payload"]) != envelope["checksum"]:
            raise EvidenceError("portable envelope checksum mismatch")
        payload = copy.deepcopy(envelope["payload"])
        required = {"schema_version", "id", "snapshot", "inventory", "request", "settings_hash",
                    "advisor_route", "descriptor", "cache_key"}
        if not isinstance(payload, dict) or set(payload) != required or payload["schema_version"] != 1 or payload["id"] != decision_id:
            raise EvidenceError("portable envelope identity mismatch")
        snapshot = validate_routing_snapshot(payload["snapshot"])
        if len([s for s in self._states.values() if s["state"] in
                ("prepared", "awaiting_native_advice", "requesting_provider")]) >= self.advisor["max_pending"]:
            raise EvidenceError("pending_limit")
        if payload["settings_hash"] != digest(self.settings) or snapshot["client"] != self.service.client:
            raise EvidenceError("portable envelope configuration changed")
        if snapshot["policy_hash"] != digest(self.policy):
            raise EvidenceError("portable envelope policy changed")
        from .routing import validate_request
        validate_request(payload["request"])
        if payload["request"]["client"] != snapshot["client"]:
            raise EvidenceError("portable request client mismatch")
        if not isinstance(payload["inventory"], dict) or set(payload["inventory"]) != {"available", "observed_at"}:
            raise EvidenceError("portable inventory invalid")
        if payload["inventory"].get("available") != payload["request"]["available"]:
            raise EvidenceError("portable envelope inventory mismatch")
        from .core import effort
        pairs = sorted((entry["model"], effort(level)) for entry in payload["request"]["available"]
                       for level in entry["efforts"])
        if pairs != sorted((c["model"], c["effort"]) for c in snapshot["candidates"]):
            raise EvidenceError("portable snapshot inventory mismatch")
        if self.service._inventory and self.service._inventory["available"] != payload["inventory"]["available"]:
            raise EvidenceError("current inventory changed")
        now = self.clock()
        if not -60 <= now - epoch(payload["inventory"]["observed_at"]) < 86400:
            raise EvidenceError("portable inventory expired")
        if snapshot["policy"] != self.policy or semantic_key(snapshot, payload["descriptor"]) != payload["cache_key"]:
            raise EvidenceError("portable envelope semantic mismatch")
        # Revalidate the bootstrap route without running anything.
        from .advisors.native import prepare_native
        if prepare_native(snapshot, payload["advisor_route"], available=payload["request"]["available"]).get("status") == "needs_advisor_route":
            raise EvidenceError("portable advisor route missing")
        payload.update(state="awaiting_native_advice", expires=epoch(snapshot["expires_at"]))
        self._states[decision_id] = payload
        return payload

    def complete_routing(self, decision_id, advisor_result, *, envelope=None):
        if not isinstance(decision_id, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,199}", decision_id):
            raise EvidenceError("invalid decision_id")
        if not isinstance(advisor_result, dict):
            raise EvidenceError("advisor_result must be an object")
        with self._lock:
            self._expire()
            state = self._states.get(decision_id)
            if state is None and envelope is not None:
                state = self._restore(decision_id, envelope)
            if state is None:
                return {"status": "expired", "decision_id": decision_id, "reason": "unknown_or_restarted_connection"}
            if self.service.offline:
                return self._finish(state, reason="offline")
            if "response" in state:
                normalized = validate_result(state["snapshot"], advisor_result)
                if state["result_hash"] != digest(normalized):
                    raise EvidenceError("conflicting completion")
                return copy.deepcopy(state["response"])
            if state["state"] != "awaiting_native_advice" or self.clock() >= state["expires"]:
                return {"status": "expired", "decision_id": decision_id, "reason": "snapshot_expired_or_cancelled"}
            if state["settings_hash"] != digest(self.settings):
                return self._finish(state, reason="configuration_changed")
            if self.service._inventory and self.service._inventory["available"] != state["inventory"]["available"]:
                return self._finish(state, reason="inventory_changed")
            try:
                result = validate_result(state["snapshot"], advisor_result)
                route = state["advisor_route"]
                if (result["backend"] != "native-economy" or result["requested_model"] != route["model"]
                        or result["resolved_model"] != route["model"] or result["effort"] != route["effort"]):
                    raise EvidenceError("advisor route mismatch")
            except EvidenceError:
                return self._finish(state, reason="invalid_advisor_result")
            return self._finish(state, result, cache=True)

    def record_routing_outcome(self, decision_id, execution):
        if self.service.offline:
            return {"status": "diagnostic_only", "decision_id": decision_id, "recorded": False}
        return self.history.record_outcome(decision_id, execution)
