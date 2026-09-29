#!/usr/bin/env python3
"""Claude hook adapter: attest caller identity and gate registered native calls."""
from __future__ import annotations

import copy
import json
import os
from pathlib import Path
import secrets
import sys
import time

# `python -I` intentionally ignores the working directory and PYTHONPATH. Import
# only this installed script's sibling package, not files from the user's cwd.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from route_evidence.claude_agents import check_record, resolve_variant
from route_evidence.core import EvidenceError, digest
from route_evidence.pipeline import arguments
from route_evidence.pipeline_config import ADVISOR_TOOLS, ROOT_TOOLS, ROUTING_TOOLS, settings
from route_evidence.pipeline_store import PipelineStore
from route_evidence.service import load_config

MAX_INPUT = 1024 * 1024
SPAWN_TOOLS = {"Agent", "Task"}


def output(event, **fields):
    return {"hookSpecificOutput": {"hookEventName": event, **fields}}


def deny(reason):
    return output("PreToolUse", permissionDecision="deny", permissionDecisionReason="Assay: " + reason)


def _identity(event):
    session = event.get("session_id")
    agent = event.get("agent_id")
    if not isinstance(session, str) or not session or len(session) > 200:
        raise EvidenceError("host_session_identity_missing")
    if agent is not None and (not isinstance(agent, str) or not agent or len(agent) > 200):
        raise EvidenceError("host_agent_identity_invalid")
    return session, agent


def observe_effort(run, event):
    raw = event.get("effort")
    if raw is None:
        return
    level = raw.get("level") if isinstance(raw, dict) else None
    if not isinstance(level, str) or level not in {"low", "medium", "high", "xhigh", "max"}:
        raise EvidenceError("invalid_observed_effort_object")
    run["observed_effort"] = level
    if level != run["route"]["effort"]:
        run["route_mismatch"] = True


def handle(event: dict, config: dict, *, clock=time.time, environment=None):
    mode = settings(config)
    name, tool = event.get("hook_event_name"), event.get("tool_name")
    if mode["mode"] == "evidence-only":
        return (output("SessionStart", additionalContext="Assay routing is explicitly evidence-only. No mandatory launch guard or isolated-advisor guarantee is active.")
                if name == "SessionStart" else {})
    if config.get("client") != "claude" or not mode["state_dir"]:
        if name == "PreToolUse" and (tool in SPAWN_TOOLS or tool == "spawn_agent"):
            return deny("required routing adapter/setup is unavailable; configure it or explicitly select evidence-only mode")
        if name == "SessionStart":
            return output(name, additionalContext="Assay required routing needs a configured Claude adapter. Do not report enforcement or fall back to root benchmark ranking.")
        return {}
    session, agent = _identity(event)
    config_hash = digest(config)
    store = PipelineStore(Path(mode["state_dir"]), clock=clock)
    prefix = "mcp__" + mode["mcp_server"] + "__"
    operation = tool[len(prefix):] if isinstance(tool, str) and tool.startswith(prefix) else None
    relevant = name in {"SessionStart", "SessionEnd", "SubagentStart", "SubagentStop"} or tool in SPAWN_TOOLS or operation in ROUTING_TOOLS or agent
    if not relevant:
        return {}
    with store.transaction() as tx:
        if name == "SessionStart":
            tx.put("session", session, {"session_id": session, "config_hash": config_hash}, clock() + 86400)
            return output(name, additionalContext="Assay required routing is configured. Before authorized delegation use prepare_routing, launch only its registered advisor input, then get_routing_decision and authorize_routing_launch. Do not read or rerank benchmark snapshots in the root. Worker routing uses generated model/effort definitions; no root settings change.")
        if name == "SessionEnd":
            for kind, id_key in (("decision", "decision_id"), ("attempt", "attempt_id")):
                for record in tx.values(kind):
                    if record["session_id"] == session:
                        tx.delete(kind, record[id_key])
            for record in tx.values("agent"):
                if record["session_id"] == session:
                    tx.delete("agent", session + ":" + record["agent_id"])
            tx.db.execute("DELETE FROM records WHERE kind='receipt' AND json_extract(payload, '$.session_id')=?", (session,))
            tx.delete("session", session)
            return {}
        registered = tx.get("session", session)
        if not registered or registered["config_hash"] != config_hash:
            if name == "PreToolUse" and (tool in SPAWN_TOOLS or operation in ROUTING_TOOLS):
                return deny("hook session not registered for this configuration; reconnect the client")
            return {}
        if name == "SubagentStart":
            agent_type = event.get("agent_type")
            candidates = [r for r in tx.values("attempt") if r["session_id"] == session
                          and r["config_hash"] == config_hash and r["state"] == "reserved"
                          and r["variant"]["name"] == agent_type and clock() < r["expires"]]
            if len(candidates) == 1 and agent:
                run = candidates[0]
                run.update(state="started", agent_id=agent)
                run.pop("input", None)
                tx.put("attempt", run["attempt_id"], run, clock() + 86400)
                tx.put("agent", session + ":" + agent, run, clock() + 86400)
            # Start is observation, not permission: never pretend to block it.
            return {}
        run = tx.get("agent", session + ":" + agent) if agent else None
        if name == "SubagentStop":
            if run:
                observe_effort(run, event)
                run["state"] = "finished"
                tx.put("agent", session + ":" + agent, run, clock() + 86400)
                tx.put("attempt", run["attempt_id"], run, clock() + 86400)
            return {}
        if name in {"PostToolUse", "PostToolUseFailure"} and tool in SPAWN_TOOLS:
            matches = [r for r in tx.values("attempt") if r.get("tool_use_id") == event.get("tool_use_id")
                       and r["session_id"] == session and r["config_hash"] == config_hash]
            if len(matches) == 1:
                dispatched = matches[0]
                dispatched["host_returned"] = True
                if name == "PostToolUseFailure":
                    dispatched["state"] = "failed"
                else:
                    # Native result layouts can vary. Do not invent an agent ID
                    # or a model when the host supplies no structured value.
                    response = event.get("tool_response")
                    if isinstance(response, dict):
                        observed_id = response.get("agentId", response.get("agent_id"))
                        if isinstance(observed_id, str) and observed_id:
                            dispatched["agent_id"] = observed_id
                    status = response.get("status") if isinstance(response, dict) else None
                    previous_state = dispatched["state"]
                    dispatched["state"] = (previous_state if status == "async_launched" and previous_state in {"finished", "failed"}
                                           else "running" if status == "async_launched" else "finished"
                                           if status == "completed" else previous_state)
                    dispatched.pop("input", None)
                    if isinstance(response, dict):
                        model = response.get("resolvedModel")
                        if isinstance(model, str) and model:
                            dispatched["observed_model"] = model
                            if model != dispatched["route"]["model"]:
                                dispatched["route_mismatch"] = True
                        used = response.get("modelsUsed")
                        if isinstance(used, list) and any(m != dispatched["route"]["model"] for m in used):
                            dispatched["route_mismatch"] = True

                tx.put("attempt", dispatched["attempt_id"], dispatched, clock() + 86400)
                if dispatched.get("agent_id"):
                    tx.put("agent", session + ":" + dispatched["agent_id"], dispatched, clock() + 86400)
                if dispatched["role"] == "advisor" and name == "PostToolUse":
                    response = event.get("tool_response")
                    if isinstance(response, dict) and isinstance(response.get("content"), list):
                        # Preserve the documented Agent output shape and its
                        # telemetry, replacing only the advisor's report blocks.
                        safe = copy.deepcopy(response)
                        safe["content"] = [{"type": "text", "text": json.dumps({
                            "decision_id": dispatched["decision_id"], "status": "read_registered_decision"})}]
                        return output(name, updatedToolOutput=safe)
            return {}
        if name != "PreToolUse":
            return {}
        supplied = event.get("tool_input")
        if not isinstance(supplied, dict):
            return deny("invalid tool input")
        if agent and tool in SPAWN_TOOLS:
            return deny("workers and advisors must not spawn agents")
        if run:
            if run.get("route_mismatch"):
                return deny("observed model differs from the registered route")
            if run["role"] == "advisor" and tool == "SubagentHandback":
                state = tx.get("decision", run["decision_id"])
                submitted = bool(state and state.get("completion_hash"))
                message = json.dumps({"decision_id": run["decision_id"], "status": "submitted" if submitted else "not_submitted"})
                safe = {**supplied, "message": message}
                # Avoid a second free-text report channel in newer clients.
                if "summary" in safe:
                    safe["summary"] = message
                return output(name, updatedInput=safe)
            if run["role"] == "advisor" and operation not in ADVISOR_TOOLS:
                return deny("advisor may only fetch its own input and submit its result")
            observe_effort(run, event)
            tx.put("agent", session + ":" + agent, run, clock() + 86400)
            tx.put("attempt", run["attempt_id"], run, clock() + 86400)
            if run.get("route_mismatch"):
                return deny("observed agent effort differs from the registered route")
        if tool in SPAWN_TOOLS:
            candidates = [r for r in tx.values("attempt") if r["session_id"] == session
                          and r["config_hash"] == config_hash and r["input_hash"] == digest(supplied)
                          and clock() < r["expires"] and r["state"] in {"prepared", "reserved"}]
            if len(candidates) != 1:
                return deny("no valid registered launch matches these exact arguments; call authorize_routing_launch")
            dispatched = candidates[0]
            tool_id = event.get("tool_use_id")
            if not isinstance(tool_id, str) or not tool_id:
                return deny("host tool-use identity missing")
            if dispatched["state"] == "reserved" and dispatched["tool_use_id"] != tool_id:
                return deny("launch attempt already consumed")
            # SubagentStart does not carry the parent's tool-use ID. Serialize
            # only the tiny unbound-start interval, not the agents' execution.
            pending = [r for r in tx.values("attempt") if r["session_id"] == session and r["state"] == "reserved"
                       and r["variant"]["name"] == dispatched["variant"]["name"]
                       and r["attempt_id"] != dispatched["attempt_id"] and clock() < r["expires"]]
            if pending:
                return deny("another launch of this definition is awaiting its native start event")
            current = resolve_variant(mode, dispatched["variant"]["profile"], dispatched["route"], environment=environment)
            if current != dispatched["variant"]:
                return deny("agent definition changed; prepare routing again")
            check_record(Path(mode["agents_dir"]), dispatched["variant"])
            if "resume" in supplied:
                original = tx.get("agent", session + ":" + supplied["resume"])
                if (not original or original["role"] != "worker" or original["decision_id"] != dispatched["decision_id"]
                        or original["packet_id"] != dispatched["packet_id"]
                        or original["attempt_id"] != dispatched.get("continuation_of")):
                    return deny("continuation identity or scope changed")
                dispatched["agent_id"] = supplied["resume"]
            dispatched.update(state="reserved", tool_use_id=tool_id)
            tx.put("attempt", dispatched["attempt_id"], dispatched, clock() + 86400)
            if "resume" in supplied:
                tx.put("agent", session + ":" + supplied["resume"], dispatched, clock() + 86400)
            return {}  # Defer to normal host permissions; never auto-allow.
        if operation in ROUTING_TOOLS:
            if operation in ROOT_TOOLS and agent:
                return deny("root-only routing operation")
            if operation in ADVISOR_TOOLS and (not run or run["role"] != "advisor"
                                               or run["decision_id"] != supplied.get("decision_id")):
                return deny("advisor identity is not bound to this decision")
            token = secrets.token_urlsafe(32)
            receipt = {"session_id": session, "agent_id": agent, "config_hash": config_hash,
                       "tool": operation, "arguments_hash": digest(arguments(supplied))}
            tx.put("receipt", digest(token), receipt, clock() + 30)
            return output(name, updatedInput={**supplied, "host_receipt": token})
    return {}


def main():
    event = None
    try:
        raw = sys.stdin.buffer.read(MAX_INPUT + 1)
        if len(raw) > MAX_INPUT:
            raise EvidenceError("oversized_event")
        event = json.loads(raw)
        if not isinstance(event, dict):
            raise EvidenceError("invalid_event")
        config_path = os.environ.get("ASSAY_ROUTING_CONFIG")
        config = load_config(Path(config_path)) if config_path else {}
        result = handle(event, config)
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except (EvidenceError, OSError, ValueError, TypeError, RecursionError):
        # A guard error must never turn into a successful unguarded spawn. Do
        # not echo payloads, paths or other untrusted/private input in errors.
        if isinstance(event, dict) and event.get("hook_event_name") == "SessionStart":
            print(json.dumps(output("SessionStart", additionalContext="Assay routing setup is invalid or unavailable. Required delegation remains blocked; inspect the configured doctor output.")))
            return 0
        print("Assay routing guard could not validate the operation.", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
