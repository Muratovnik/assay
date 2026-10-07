"""Host-attested routing and dispatch. No models, launch APIs or new transports."""
from __future__ import annotations

import copy
import os
import secrets
from pathlib import Path

from .claude_agents import (ADVISOR_PROFILE, ALIAS_KIND, launch_model, resolve_variant,
                            unconfirmed_changes)
from .core import EvidenceError, digest, epoch, timestamp
from .pipeline_config import ADVISOR_TOOLS, PROTOCOL, ROOT_TOOLS, configured_inventory, settings
from .pipeline_store import PipelineStore

MAX_PROMPT_BYTES = 64 * 1024
RECEIPT_SECONDS = 300


def arguments(value: dict) -> dict:
    """Match the host's supplied arguments to Python's optional defaults."""
    return {k: v for k, v in value.items() if k != "host_receipt" and v is not None}


def compact(response: dict) -> dict:
    keep = {"schema_version", "status", "usage", "decision_id", "snapshot_id", "expires_at",
            "cache_hit", "launch_verified", "task_evidence_status", "telemetry_status", "reason",
            "inventory_warnings"}
    result = {k: copy.deepcopy(v) for k, v in response.items() if k in keep}
    result["schema_version"] = PROTOCOL
    if "decisions" in response:
        fields = {"packet_id", "status", "decision_type", "selected", "reason_codes"}
        result["decisions"] = [{k: copy.deepcopy(v) for k, v in d.items() if k in fields}
                               for d in response["decisions"]]
        for original, decision in zip(response["decisions"], result["decisions"]):
            provenance = original.get("selection_provenance", {})
            if "caller_override" in provenance:
                decision["selection_provenance"] = {k: copy.deepcopy(v) for k, v in provenance.items()
                    if k in {"source", "verification", "explicit_source", "caller_override"}}
    return result


def launch_requests(value, packet_ids):
    if not isinstance(value, dict) or set(value) != set(packet_ids):
        raise EvidenceError("launch_requests_must_cover_every_packet")
    result = copy.deepcopy(value)
    for request in result.values():
        if (not isinstance(request, dict) or set(request) - {"profile", "prompt", "description", "run_in_background", "isolation"}
                or not {"profile", "prompt"} <= set(request)):
            raise EvidenceError("invalid_launch_request")
        if (not isinstance(request["profile"], str) or request["profile"] == ADVISOR_PROFILE
                or not isinstance(request["prompt"], str) or not request["prompt"].strip()
                or len(request["prompt"].encode("utf-8")) > MAX_PROMPT_BYTES):
            raise EvidenceError("invalid_launch_request")
        if "description" in request and (not isinstance(request["description"], str) or not 1 <= len(request["description"]) <= 100):
            raise EvidenceError("invalid_launch_description")
        if "run_in_background" in request and type(request["run_in_background"]) is not bool:
            raise EvidenceError("invalid_launch_background")
        if "isolation" in request and request["isolation"] != "worktree":
            raise EvidenceError("invalid_launch_isolation")
    return result


def launch_stub(attempt_id: str, native_input: dict) -> dict:
    """The small Agent input the root sends; the host hook substitutes the rest.

    The root never repeats a registered prompt, so it cannot alter it and does
    not spend output tokens copying it byte for byte.
    """
    stub = {k: copy.deepcopy(v) for k, v in native_input.items() if k != "prompt"}
    stub["prompt"] = f"Assay registered launch {attempt_id}. The host supplies the registered packet input."
    return stub


def with_model(native_input: dict, variant: dict, route: dict) -> dict:
    """Name the route's model in the Agent call unless the definition pins one.

    An effort definition carries no model; the stub the root sends shows it.
    """
    model = launch_model(variant, route)
    if model:
        native_input["model"] = model
    return native_input


class RoutingPipeline:
    def __init__(self, service):
        self.service = service
        self.raw_config = service.advisor_config
        self.config = settings(self.raw_config)
        self.config_hash = digest(self.raw_config)
        self.clock = service.clock

    @property
    def required(self):
        return self.config["mode"] == "required"

    @property
    def store(self):
        if not self.config["state_dir"]:
            raise EvidenceError("pipeline_setup_required")
        return PipelineStore(Path(self.config["state_dir"]), clock=self.clock)

    def _inventory_status(self):
        try:
            inventory = configured_inventory(self.raw_config)
        except EvidenceError as exc:
            return {"configured": False, "error": str(exc)}
        if inventory is None:
            return {"configured": False}
        age = self.clock() - epoch(inventory["observed_at"])
        return {"configured": True, "source": "file" if self.config["inventory_file"] else "configuration",
                "observed_at": inventory["observed_at"], "age_hours": round(age / 3600, 2),
                "ttl_hours": self.config["inventory_ttl_hours"],
                "expired": not -60 <= age < self.service.inventory_ttl}

    def setup_gaps(self):
        """What required mode still lacks; each gap blocks registered delegation."""
        if not self.required:
            return []
        from .client_capabilities import contract
        gaps = [] if contract(self.service.client, self.config.get("host"))["strict_adapter"] else ["host_adapter"]
        # Without a baseline an abstaining or failed advisor would leave the
        # packet without a route, so required mode is not set up without one.
        return gaps + [key for key in ("state_dir", "agents_dir", "baseline") if not self.config[key]]

    def alias_observations(self):
        """What the host resolved each alias to, and changes the owner has not confirmed."""
        if not self.config["state_dir"]:
            return []
        with self.store.transaction() as tx:
            records = sorted(tx.values(ALIAS_KIND), key=lambda r: r["alias"])
        try:
            inventory = configured_inventory(self.raw_config)
            confirmed = epoch(inventory["observed_at"]) if inventory else None
        except EvidenceError:
            confirmed = None
        report = []
        for record in records:
            entry = {"alias": record["alias"], "model": record["model"],
                     "observed_at": timestamp(record["observed_at"])}
            if record.get("change"):
                change = record["change"]
                entry["change"] = {"from": change["from"], "to": change["to"],
                                   "changed_at": timestamp(change["changed_at"]),
                                   "confirmed": confirmed is not None and change["changed_at"] <= confirmed}
            report.append(entry)
        return report

    def status(self):
        from .client_capabilities import contract
        supported = contract(self.service.client, self.config.get("host"))["strict_adapter"] is not None
        gaps = self.setup_gaps()
        result = {"protocol_version": PROTOCOL, "mode": self.config["mode"],
                  "host_adapter": "claude" if supported else None,
                  "adapter_capabilities": contract(self.service.client, self.config.get("host")),
                  "state_configured": bool(self.config["state_dir"]),
                  "definitions_configured": bool(self.config["agents_dir"]),
                  "advisor_route_configured": bool(self.config["advisor_route"]),
                  "baseline_configured": bool(self.config["baseline"]),
                  "unrouted_agents": list(self.config["unrouted_agents"]),
                  "inventory": self._inventory_status(),
                  "guard_installed_verified": False, "discovery_verified": False,
                  "runtime_model_observed": None,
                  "status": ("evidence_only" if not self.required else "setup_required" if gaps
                             else "requires_host_receipt"),
                  "setup_gaps": gaps,
                  "no_implicit_root_ranking": self.required}
        if self.required and supported:
            from .claude_agents import route_checks
            result["route_checks"] = route_checks(self.raw_config)
            try:
                result["alias_observations"] = self.alias_observations()
            except EvidenceError as exc:
                result["alias_observations"] = {"error": str(exc)}
        return result

    def host(self, tool: str, supplied: dict):
        if not self.required:
            return None
        if self.service.client != "claude":
            raise EvidenceError("required_routing_host_adapter_unavailable")
        gaps = self.setup_gaps()
        if gaps:
            # The hook issues no receipt for an incomplete setup; name the gap
            # instead of reporting a missing receipt.
            raise EvidenceError("required_routing_setup_incomplete:" + ",".join(gaps))
        token = supplied.get("host_receipt")
        if not isinstance(token, str) or len(token) > 200:
            raise EvidenceError("host_receipt_required")
        with self.store.transaction() as tx:
            record = tx.get("receipt", digest(token))
            if (not record or record["config_hash"] != self.config_hash or record["tool"] != tool
                    or record["arguments_hash"] != digest(arguments(supplied))):
                raise EvidenceError("invalid_host_receipt")
            if tool in ROOT_TOOLS and record.get("agent_id"):
                raise EvidenceError("root_only_routing_operation")
            if tool in ADVISOR_TOOLS:
                if not record.get("agent_id"):
                    raise EvidenceError("advisor_only_routing_operation")
                run = tx.get("agent", record["session_id"] + ":" + record["agent_id"])
                if (not run or run["role"] != "advisor" or run["decision_id"] != supplied.get("decision_id")
                        or run["config_hash"] != self.config_hash):
                    raise EvidenceError("advisor_provenance_mismatch")
                record["run"] = run
            tx.delete("receipt", digest(token))
            return record

    def _decision(self, tx, decision_id, host):
        state = tx.get("decision", decision_id)
        if (not state or state["session_id"] != host["session_id"] or state["config_hash"] != self.config_hash):
            raise EvidenceError("decision_expired_or_session_mismatch")
        return state

    def _authority_inventory(self):
        # Reread on every preparation: the owner confirms the file without a
        # reconnect, while a caller repeating an old list cannot renew it.
        inventory = configured_inventory(self.raw_config)
        if not inventory or not inventory.get("available"):
            raise EvidenceError("configured_host_inventory_required")
        if not -60 <= self.clock() - epoch(inventory["observed_at"]) < self.service.inventory_ttl:
            raise EvidenceError("configured_inventory_expired")
        return inventory

    def _confirmed_names(self, authority):
        """Suspend an alias's confirmed spellings once its resolution changed.

        Until the owner confirms the inventory again, those spellings describe
        the model the alias used to resolve to, not the one it launches now.
        """
        with self.store.transaction() as tx:
            changes = unconfirmed_changes(tx.values(ALIAS_KIND), epoch(authority["observed_at"]))
        if not changes:
            return authority, []
        authority = copy.deepcopy(authority)
        for item in authority["available"]:
            if item["model"] in changes:
                item.pop("evidence_names", None)
        return authority, [{"code": "alias_resolution_changed", "alias": alias, "from": change["from"],
                            "to": change["to"]} for alias, change in sorted(changes.items())]

    def _capabilities(self, packets, available, requests):
        from .core import effort
        for packet in packets:
            explicit = packet.get("explicit") or {}
            approved = self.config["approved_choices"].get(packet["packet_id"])
            if approved:
                if explicit and any(approved.get(k) != v for k, v in explicit.items()):
                    raise EvidenceError("explicit_choice_conflicts_with_configured_choice")
                # A configured choice is binding even if the root omits it.
                packet["explicit"] = copy.deepcopy(approved)
                packet["explicit_source"] = "configuration"
                packet.pop("caller_override", None)
            # A user's own explicit choice stays as supplied. Policy accepts it
            # only for an inventory pair with a generated, expressible variant.
            baseline = packet.get("baseline")
            if baseline and baseline != self.config["baseline"]:
                raise EvidenceError("baseline_requires_configured_authority")
            if not baseline and self.config["baseline"]:
                packet["baseline"] = copy.deepcopy(self.config["baseline"])
            if packet.get("capabilities"):
                raise EvidenceError("runtime_capabilities_are_adapter_owned")
            checked = []
            for model in available:
                for level in model["efforts"]:
                    level = effort(level)
                    cap = {"model": model["model"], "effort": level,
                           "route_expressible": True, "capabilities": copy.deepcopy(
                               self.config["profile_capabilities"].get(requests[packet["packet_id"]]["profile"], {}))}
                    try:
                        resolve_variant(self.config, requests[packet["packet_id"]]["profile"], cap)
                    except EvidenceError:
                        cap["route_expressible"] = False
                    checked.append(cap)
            packet["capabilities"] = checked
        return packets

    def _put_attempt(self, tx, state, role, packet_id, native_input, route, variant):
        attempt_id = secrets.token_hex(16)
        native_input = copy.deepcopy(native_input)
        if os.environ.get("CLAUDE_CODE_DISABLE_BACKGROUND_TASKS") == "1":
            if native_input.get("run_in_background") is True:
                raise EvidenceError("background_tasks_disabled")
            # Claude omits this argument from its tool schema in this mode.
            native_input.pop("run_in_background", None)
        native_input["prompt"] += "\n\nAssay attempt: " + attempt_id
        stub = launch_stub(attempt_id, native_input)
        run = {"attempt_id": attempt_id, "decision_id": state["decision_id"], "packet_id": packet_id,
               "session_id": state["session_id"], "config_hash": self.config_hash, "role": role,
               "input": native_input, "input_hash": digest(stub), "route": dict(route),
               "variant": variant, "state": "prepared", "expires": state["expires"],
               "observed_model": None, "observed_effort": None}
        tx.put("attempt", attempt_id, run, state["expires"])
        return {"attempt_id": attempt_id, "tool": "Agent", "input": stub,
                "requested_model": route["model"], "requested_effort": route["effort"],
                "input_substituted_by_host": True, "launch_verified": False}

    def _reply(self, attempt):
        stub = launch_stub(attempt["attempt_id"], attempt["input"])
        return {"attempt_id": attempt["attempt_id"], "tool": "Agent", "input": stub,
                "input_substituted_by_host": True, "launch_verified": False}

    async def prepare(self, supplied):
        host = self.host("prepare_routing", supplied)
        params = arguments(supplied)
        requests = params.pop("launch_requests", None)
        if not self.required:
            response = await self.service.prepare_routing(**params)
            response["pipeline_mode"] = "evidence-only"
            return response
        if self.service.offline:
            raise EvidenceError("offline_cannot_prepare_dispatch")
        workflow = self.service.advisor_workflow
        if workflow.advisor["backend"] != "native-economy":
            raise EvidenceError("required_pipeline_requires_native_advisor")
        from .advice_contracts import validate_packets
        packets = validate_packets(params["packets"])
        requests = launch_requests(requests, [p["packet_id"] for p in packets])
        authority = self._authority_inventory()
        available = authority["available"]
        if params.get("available") is not None and params["available"] != available:
            raise EvidenceError("inventory_must_match_configured_authority")
        params.pop("available", None)
        authority, warnings = self._confirmed_names(authority)
        available = authority["available"]
        # Preserve the actual observation timestamp, including its remaining
        # freshness budget; a repeated caller list cannot renew the inventory.
        self.service.use_inventory(authority)
        # Validate before iterating or calling any provider.
        self.service.prepare(list(dict.fromkeys(t for p in packets for t in p["task_types"])))
        route = self.config["advisor_route"]
        if params.get("advisor_route") and params["advisor_route"] != route:
            raise EvidenceError("advisor_route_must_match_configuration")
        params["advisor_route"] = route
        params["packets"] = self._capabilities(packets, available, requests)
        response = await self.service.prepare_routing(**params, native_delivery="private")
        if warnings:
            response["inventory_warnings"] = warnings
        if "decision_id" not in response:
            return compact(response)
        internal = workflow.pending_state(response["decision_id"])
        if internal is None or internal["expires"] <= self.clock():
            return compact(response)
        expires = internal["expires"]
        state = {"decision_id": response["decision_id"], "session_id": host["session_id"],
                 "config_hash": self.config_hash, "expires": expires,
                 "inventory": internal["inventory"],
                 "launch_requests": requests, "response": compact(response)}
        with self.store.transaction() as tx:
            if response["status"] == "awaiting_native_advice":
                variant = resolve_variant(self.config, ADVISOR_PROFILE, route)
                native_input = {"subagent_type": variant["name"], "description": "Assay routing advisor", "run_in_background": False,
                                "prompt": f"Routing decision {state['decision_id']}. Call get_advisor_input, then complete_routing. Return only submission status."}
                with_model(native_input, variant, route)
                state["envelope"] = workflow.export_envelope(state["decision_id"])
                state["response"]["handoff"] = self._put_attempt(tx, state, "advisor", None, native_input, route, variant)
            tx.put("decision", state["decision_id"], state, expires)
        return copy.deepcopy(state["response"])

    def advisor_input(self, supplied):
        host = self.host("get_advisor_input", supplied)
        if not self.required:
            raise EvidenceError("isolated_advisor_requires_required_mode")
        with self.store.transaction() as tx:
            state = self._decision(tx, supplied["decision_id"], host)
            if "envelope" not in state:
                raise EvidenceError("advisor_input_no_longer_pending")
            payload = state["envelope"]["payload"]
        from .advisors.native import advisor_input
        return {"decision_id": state["decision_id"], **advisor_input(payload["snapshot"], payload["advisor_route"])}

    def complete(self, supplied):
        host = self.host("complete_routing", supplied)
        params = arguments(supplied)
        if not self.required:
            return self.service.complete_routing(**params)
        with self.store.transaction() as tx:
            state = self._decision(tx, params["decision_id"], host)
            if host["run"].get("route_mismatch"):
                raise EvidenceError("observed_advisor_route_mismatch")
            if "completion_hash" in state:
                if state["completion_hash"] != digest(params["advisor_result"]):
                    raise EvidenceError("conflicting_completion")
                return {"decision_id": state["decision_id"], "status": "submitted"}
            envelope = state.get("envelope")
            if envelope is None:
                raise EvidenceError("native_advice_not_pending")
        result = self.service.complete_routing(**params, envelope=envelope, cache=False)
        with self.store.transaction() as tx:
            state = self._decision(tx, params["decision_id"], host)
            state["response"] = compact(result)
            state["response"]["advisor_provenance"] = {
                "source": "claude-hook-bound-subagent", "attempt_id": host["run"]["attempt_id"],
                "observed_model": host["run"].get("observed_model"),
                "observed_effort": host["run"].get("observed_effort")}
            state["completion_hash"] = digest(params["advisor_result"])
            state.pop("envelope", None)
            tx.put("decision", state["decision_id"], state, state["expires"])
        return {"decision_id": state["decision_id"], "status": "submitted"}

    def _advisor_readiness(self, tx, state):
        advisors = [a for a in tx.values("attempt") if a["decision_id"] == state["decision_id"]
                    and a["role"] == "advisor"]
        if not advisors:
            return True  # Explicit, single-candidate, valid cached or fallback decision.
        run = advisors[0]
        if run.get("route_mismatch"):
            state["response"]["status"] = "no_decision"
            for decision in state["response"].get("decisions", []):
                decision.update(selected=None, status="no_decision", reason_codes=["observed_advisor_route_mismatch"])
            state.pop("envelope", None)
            tx.put("decision", state["decision_id"], state, state["expires"])
            return True
        if run["state"] not in {"finished", "failed"} or not run.get("host_returned"):
            # SubagentStop can precede Agent's final resolvedModel/modelsUsed
            # observation. Do not authorize/cache while that check is pending.
            return False
        if "advisor_provenance" in state["response"]:
            state["response"]["advisor_provenance"].update(
                observed_model=run.get("observed_model"), observed_effort=run.get("observed_effort"))
        # Only advice from a completed, non-conflicting host invocation enters
        # the existing semantic cache. Submission alone is not execution proof.
        if run["state"] == "finished" and state.get("completion_hash"):
            self.service.advisor_workflow.remember_completed(state["decision_id"], state["expires"])
        return True

    def decision(self, supplied):
        host = self.host("get_routing_decision", supplied)
        if not self.required:
            raise EvidenceError("registered_decisions_require_required_mode")
        with self.store.transaction() as tx:
            state = self._decision(tx, supplied["decision_id"], host)
            if not self._advisor_readiness(tx, state):
                return {"schema_version": PROTOCOL, "decision_id": state["decision_id"], "status": "awaiting_advisor_completion"}
            advisors = [a for a in tx.values("attempt") if a["decision_id"] == state["decision_id"]
                        and a["role"] == "advisor"]
            if state.get("envelope") and len(advisors) == 1 and advisors[0]["state"] in {"finished", "failed"}:
                # The advisor actually ended without submitting. An eligible,
                # configured baseline is the only possible fallback; never ask
                # the root to inspect evidence or fabricate an advisor answer.
                result = self.service.advisor_workflow.finish_unanswered(
                    state["decision_id"], state["envelope"], reason="advisor_ended_without_result")
                state["response"] = compact(result)
                state.pop("envelope", None)
                tx.put("decision", state["decision_id"], state, state["expires"])
            return copy.deepcopy(state["response"])

    def _resume(self, tx, supplied, host):
        agent_id = supplied["resume_agent_id"]
        if not isinstance(agent_id, str) or not agent_id or supplied.get("retry_of"):
            raise EvidenceError("invalid_continuation")
        previous = tx.get("agent", host["session_id"] + ":" + agent_id)
        if (not previous or previous["role"] != "worker" or previous["config_hash"] != self.config_hash
                or previous["decision_id"] != supplied["decision_id"] or previous["packet_id"] != supplied["packet_id"]):
            raise EvidenceError("continuation_requires_observed_matching_worker")
        prepared = [a for a in tx.values("attempt") if a.get("continuation_of") == previous["attempt_id"]
                    and a["state"] == "prepared"]
        if len(prepared) == 1:
            return self._reply(prepared[0])
        if previous.get("route_mismatch"):
            raise EvidenceError("continuation_observed_route_mismatch")
        if previous["state"] != "finished":
            raise EvidenceError("continuation_requires_idle_worker")
        variant = resolve_variant(self.config, previous["variant"]["profile"], previous["route"])
        if variant != previous["variant"]:
            raise EvidenceError("continuation_definition_changed")
        state = {"decision_id": previous["decision_id"], "session_id": host["session_id"],
                 "expires": self.clock() + 600}
        # This resumes a known worker's original scope, not a new assignment or
        # renewed evidence-based selection. Keep its original model and effort.
        native_input = {"resume": agent_id, "subagent_type": variant["name"],
                        "description": "Continue registered Assay packet", "run_in_background": False,
                        "prompt": "Continue only the original assigned packet from its current progress. Do not repeat completed changes or expand the scope. If complete, report that status."}
        with_model(native_input, variant, previous["route"])
        reply = self._put_attempt(tx, state, "worker", previous["packet_id"], native_input, previous["route"], variant)
        attempt = tx.get("attempt", reply["attempt_id"])
        attempt["continuation_of"] = previous["attempt_id"]
        tx.put("attempt", reply["attempt_id"], attempt, state["expires"])
        return reply

    def authorize(self, supplied):
        host = self.host("authorize_routing_launch", supplied)
        if not self.required:
            raise EvidenceError("evidence_only_cannot_authorize_launch")
        packet_id, decision_id = supplied["packet_id"], supplied["decision_id"]
        with self.store.transaction() as tx:
            if supplied.get("resume_agent_id"):
                return self._resume(tx, supplied, host)
            state = self._decision(tx, decision_id, host)
            if not self._advisor_readiness(tx, state):
                raise EvidenceError("advisor_completion_not_observed")
            current = self.service.inventory
            if current and current["available"] != state["inventory"]["available"]:
                raise EvidenceError("inventory_changed_reprepare_required")
            decisions = state["response"].get("decisions", [])
            selected = next((d.get("selected") for d in decisions if d["packet_id"] == packet_id), None)
            if not selected:
                raise EvidenceError("packet_has_no_executable_decision")
            request = state["launch_requests"][packet_id]
            variant = resolve_variant(self.config, request["profile"], selected)
            old = [a for a in tx.values("attempt") if a["decision_id"] == decision_id and a["packet_id"] == packet_id]
            retry = supplied.get("retry_of")
            if old and not retry:
                prepared = [a for a in old if a["state"] == "prepared"]
                if len(prepared) == 1:
                    return self._reply(prepared[0])
                raise EvidenceError("attempt_already_dispatched")
            if retry:
                if any(a["state"] in {"prepared", "reserved", "started", "running"} for a in old if a["attempt_id"] != retry):
                    raise EvidenceError("another_packet_attempt_is_active")
                previous = next((a for a in old if a["attempt_id"] == retry), None)
                if not previous or previous["state"] != "failed" or previous.get("retried"):
                    raise EvidenceError("retry_requires_observed_failed_attempt")
                previous["retried"] = True
                tx.put("attempt", retry, previous, previous["expires"])
            native_input = {k: copy.deepcopy(v) for k, v in request.items() if k != "profile"}
            native_input["subagent_type"] = variant["name"]
            with_model(native_input, variant, selected)
            native_input.setdefault("description", "Assay routed packet")
            native_input.setdefault("run_in_background", False)
            native_input["prompt"] += "\n\nDo not spawn additional agents. Return evidence against the packet's acceptance criteria."
            return self._put_attempt(tx, state, "worker", packet_id, native_input, selected, variant)

    def outcome(self, supplied):
        host = self.host("record_routing_outcome", supplied)
        if self.required:
            with self.store.transaction() as tx:
                state = tx.get("decision", supplied["decision_id"])
                owned = state and state["session_id"] == host["session_id"] and state["config_hash"] == self.config_hash
                if not owned:
                    owned = any(a["decision_id"] == supplied["decision_id"] and a["session_id"] == host["session_id"]
                                and a["config_hash"] == self.config_hash and a["state"] != "prepared"
                                for a in tx.values("attempt"))
                if not owned:
                    raise EvidenceError("outcome_has_no_owned_decision_or_attempt")
        return self.service.record_routing_outcome(supplied["decision_id"], supplied["execution"])
