#!/usr/bin/env python3
"""Claude hook adapter: attest caller identity and gate registered native calls.

The plugin runs this script for spawns, advisor hand-backs, routing MCP calls
and subagent lifecycle events. Generated routed definitions also run it from
their own frontmatter with `--scope agent` for their ordinary tool calls.
Without an explicit required-mode configuration it returns no decision at all.
"""
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
from route_evidence.pipeline import RECEIPT_SECONDS, arguments
from route_evidence.pipeline_config import ADVISOR_TOOLS, ROOT_TOOLS, ROUTING_TOOLS, settings
from route_evidence.pipeline_store import PipelineStore
from route_evidence.service import load_config

MAX_INPUT = 8 * 1024 * 1024
SPAWN_TOOLS = {"Agent", "Task"}
HANDBACK = "SubagentHandback"
DAY = 86400
# Fields that describe what the host actually ran, as opposed to what was
# authorized. They move with an agent when its attribution is corrected.
RUNTIME_FIELDS = ("agent_id", "state", "observed_model", "observed_effort", "route_mismatch", "binding")


def output(event, **fields):
    return {"hookSpecificOutput": {"hookEventName": event, **fields}}


def deny(reason):
    return output("PreToolUse", permissionDecision="deny", permissionDecisionReason="Assay: " + reason)


def routing_operation(tool, server=None):
    """The routing MCP operation a tool name addresses, if any."""
    if not isinstance(tool, str) or not tool.startswith("mcp__"):
        return None
    prefix, _, name = tool.rpartition("__")
    if name not in ROUTING_TOOLS or (server is not None and prefix != "mcp__" + server):
        return None
    return name


def plugin_owned(tool, server=None):
    """Tools the plugin hook handles; the agent-scope hook leaves them alone."""
    return tool in SPAWN_TOOLS or tool == HANDBACK or routing_operation(tool, server) is not None


def guarded(event):
    """Operations that must be refused when the guard cannot validate them."""
    return event.get("hook_event_name") == "PreToolUse" and (
        event.get("tool_name") in SPAWN_TOOLS or routing_operation(event.get("tool_name")) is not None)


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


def _unrouted(event, mode):
    """A root launch of a native agent type the owner exempted from routing."""
    supplied = event.get("tool_input")
    if event.get("agent_id") is not None or not isinstance(supplied, dict):
        return False
    return (supplied.get("subagent_type") or "general-purpose") in mode["unrouted_agents"]


def _save(tx, session, run, clock):
    tx.put("attempt", run["attempt_id"], run, clock() + DAY)
    if run.get("agent_id"):
        tx.put("agent", session + ":" + run["agent_id"], run, clock() + DAY)


def _bind_start(tx, session, config_hash, agent, agent_type, clock):
    if not agent:
        return
    candidates = [r for r in tx.values("attempt") if r["session_id"] == session
                  and r["config_hash"] == config_hash and r["state"] == "reserved" and not r.get("agent_id")
                  and r["variant"]["name"] == agent_type and clock() < r["expires"]]
    if not candidates:
        return
    # SubagentStart carries no parent tool-use ID. Launches of one definition
    # share model, effort and permissions, so bind them in reservation order;
    # the Agent result, which names both IDs, corrects the packet attribution.
    run = min(candidates, key=lambda r: (r.get("reserved_at", 0), r["attempt_id"]))
    run.update(state="started", agent_id=agent, binding="unique" if len(candidates) == 1 else "start_order")
    run.pop("input", None)
    _save(tx, session, run, clock)


def _swap_runtime(first, second):
    for key in RUNTIME_FIELDS:
        a, b = first.get(key), second.get(key)
        a_present, b_present = key in first, key in second
        first.pop(key, None)
        second.pop(key, None)
        if b_present:
            first[key] = b
        if a_present:
            second[key] = a


def _rebind(tx, session, dispatched, observed_id, clock):
    """Attribute the agent the host names to the call that actually started it."""
    other = tx.get("agent", session + ":" + observed_id)
    if other and other["attempt_id"] != dispatched["attempt_id"]:
        sibling = tx.get("attempt", other["attempt_id"])
        if sibling and sibling["variant"]["name"] == dispatched["variant"]["name"]:
            # Start order gave this agent to a sibling launch of the same
            # definition. Exchange what each actually ran; a sibling left
            # without an agent is still awaiting its own start event.
            _swap_runtime(dispatched, sibling)
            if "agent_id" not in sibling:
                sibling["state"] = "reserved"
            _save(tx, session, sibling, clock)
    if dispatched.get("agent_id") != observed_id:
        dispatched["agent_id"] = observed_id
    if dispatched["state"] in {"prepared", "reserved"}:
        dispatched["state"] = "started"
    dispatched["binding"] = "host_result"
    return dispatched


def _observe_return(tx, event, session, config_hash, name, clock):
    tool = event.get("tool_name")
    matches = [r for r in tx.values("attempt") if r.get("tool_use_id") == event.get("tool_use_id")
               and r["session_id"] == session and r["config_hash"] == config_hash]
    if len(matches) != 1:
        return {}
    dispatched = matches[0]
    response = event.get("tool_response")
    observed_id = response.get("agentId", response.get("agent_id")) if isinstance(response, dict) else None
    if isinstance(observed_id, str) and observed_id and dispatched.get("agent_id") != observed_id:
        dispatched = _rebind(tx, session, dispatched, observed_id, clock)
    dispatched["host_returned"] = True
    dispatched.pop("input", None)
    if name == "PostToolUseFailure":
        dispatched["state"] = "failed"
    else:
        # Native result layouts can vary. Do not invent an agent ID or a model
        # when the host supplies no structured value.
        status = response.get("status") if isinstance(response, dict) else None
        previous_state = dispatched["state"]
        dispatched["state"] = (previous_state if status == "async_launched" and previous_state in {"finished", "failed"}
                               else "running" if status == "async_launched" else "finished"
                               if status == "completed" else previous_state)
        if isinstance(response, dict):
            model = response.get("resolvedModel")
            if isinstance(model, str) and model:
                dispatched["observed_model"] = model
                if model != dispatched["route"]["model"]:
                    dispatched["route_mismatch"] = True
            used = response.get("modelsUsed")
            if isinstance(used, list) and any(m != dispatched["route"]["model"] for m in used):
                dispatched["route_mismatch"] = True
    _save(tx, session, dispatched, clock)
    if dispatched["role"] == "advisor" and name == "PostToolUse" and tool in SPAWN_TOOLS:
        if isinstance(response, dict) and isinstance(response.get("content"), list):
            # Preserve the documented Agent output shape and its telemetry,
            # replacing only the advisor's report blocks.
            safe = copy.deepcopy(response)
            safe["content"] = [{"type": "text", "text": json.dumps({
                "decision_id": dispatched["decision_id"], "status": "read_registered_decision"})}]
            return output(name, updatedToolOutput=safe)
    return {}


def _release(tx, event, session, config_hash, clock):
    """Auto mode denied a reserved launch before it ran; it may be sent again."""
    for run in tx.values("attempt"):
        if (run.get("tool_use_id") == event.get("tool_use_id") and run["session_id"] == session
                and run["config_hash"] == config_hash and run["state"] == "reserved" and not run.get("agent_id")):
            run["state"] = "prepared"
            run.pop("tool_use_id", None)
            run.pop("reserved_at", None)
            tx.put("attempt", run["attempt_id"], run, run["expires"])
    return {}


def _dispatch(tx, event, session, config_hash, mode, clock, environment):
    supplied = event["tool_input"]
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
    if "input" not in dispatched:
        return deny("launch attempt already started")
    current = resolve_variant(mode, dispatched["variant"]["profile"], dispatched["route"], environment=environment)
    if current != dispatched["variant"]:
        return deny("agent definition changed; prepare routing again")
    check_record(Path(mode["agents_dir"]), dispatched["variant"])
    resume = dispatched["input"].get("resume")
    if resume is not None:
        original = tx.get("agent", session + ":" + resume)
        if (not original or original["role"] != "worker" or original["decision_id"] != dispatched["decision_id"]
                or original["packet_id"] != dispatched["packet_id"]
                or original["attempt_id"] != dispatched.get("continuation_of")):
            return deny("continuation identity or scope changed")
        dispatched["agent_id"] = resume
    dispatched.update(state="reserved", tool_use_id=tool_id)
    dispatched.setdefault("reserved_at", clock())
    tx.put("attempt", dispatched["attempt_id"], dispatched, clock() + DAY)
    if resume is not None:
        tx.put("agent", session + ":" + resume, dispatched, clock() + DAY)
    # The registered input replaces the stub. No permission decision is added:
    # the client's ordinary permission flow evaluates the substituted input.
    return output("PreToolUse", updatedInput=copy.deepcopy(dispatched["input"]))


def _agent_scope(event, config, mode, clock):
    """Frontmatter hook of a routed definition: its ordinary tool calls only."""
    if event.get("hook_event_name") != "PreToolUse" or plugin_owned(event.get("tool_name"), mode["mcp_server"]):
        return {}
    if not mode["state_dir"]:
        return {}
    session, agent = _identity(event)
    if agent is None:
        return {}
    with PipelineStore(Path(mode["state_dir"]), clock=clock).transaction() as tx:
        run = tx.get("agent", session + ":" + agent)
        if not run or run["config_hash"] != digest(config):
            return {}
        if run.get("route_mismatch"):
            return deny("observed model differs from the registered route")
        if run["role"] == "advisor":
            return deny("advisor may only fetch its own input and submit its result")
        observe_effort(run, event)
        _save(tx, session, run, clock)
        if run.get("route_mismatch"):
            return deny("observed agent effort differs from the registered route")
    return {}


def handle(event: dict, config: dict, *, scope="plugin", clock=time.time, environment=None):
    mode = settings(config)
    if mode["mode"] != "required" or config.get("client") != "claude":
        # Opt-in only: no configuration, evidence-only and hosts without this
        # adapter keep the client's ordinary behavior and receive no context.
        return {}
    if scope == "agent":
        return _agent_scope(event, config, mode, clock)
    name, tool = event.get("hook_event_name"), event.get("tool_name")
    if name == "PreToolUse" and tool in SPAWN_TOOLS and _unrouted(event, mode):
        return {}  # An owner-listed native agent keeps the normal permission flow.
    if not mode["state_dir"] or not mode["agents_dir"]:
        if name == "PreToolUse" and tool in SPAWN_TOOLS:
            return deny("required routing setup is incomplete; run the routing doctor or select evidence-only mode")
        if name == "SessionStart":
            return output(name, additionalContext="Assay required routing is selected but not set up. Delegation outside configured unrouted agents stays blocked; run the routing doctor.")
        return {}
    session, agent = _identity(event)
    config_hash = digest(config)
    store = PipelineStore(Path(mode["state_dir"]), clock=clock)
    operation = routing_operation(tool, mode["mcp_server"])
    relevant = (name in {"SessionStart", "SessionEnd", "SubagentStart", "SubagentStop", "PermissionDenied"}
                or tool in SPAWN_TOOLS or tool == HANDBACK or operation is not None)
    if not relevant:
        return {}
    with store.transaction() as tx:
        if name == "SessionStart":
            tx.put("session", session, {"session_id": session, "config_hash": config_hash}, clock() + DAY)
            return output(name, additionalContext="Assay required routing is configured. Before authorized delegation use prepare_routing, launch only its registered advisor input, then get_routing_decision and authorize_routing_launch; send the returned Agent input unchanged. Do not read or rerank benchmark snapshots in the root. Worker routing uses generated model/effort definitions; no root settings change.")
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
            if name == "PreToolUse" and (tool in SPAWN_TOOLS or operation is not None):
                return deny("hook session not registered for this configuration; reconnect the client")
            return {}
        # Activity keeps a registration alive; only an idle day retires it.
        tx.put("session", session, registered, clock() + DAY)
        if name == "SubagentStart":
            # Start is observation, not permission: never pretend to block it.
            _bind_start(tx, session, config_hash, agent, event.get("agent_type"), clock)
            return {}
        run = tx.get("agent", session + ":" + agent) if agent else None
        if name == "SubagentStop":
            if run:
                observe_effort(run, event)
                run["state"] = "finished"
                _save(tx, session, run, clock)
            return {}
        if name == "PermissionDenied" and tool in SPAWN_TOOLS:
            return _release(tx, event, session, config_hash, clock)
        if name in {"PostToolUse", "PostToolUseFailure"} and tool in SPAWN_TOOLS:
            return _observe_return(tx, event, session, config_hash, name, clock)
        if name != "PreToolUse":
            return {}
        supplied = event.get("tool_input")
        if not isinstance(supplied, dict):
            return deny("invalid tool input")
        if agent and tool in SPAWN_TOOLS:
            return deny("workers and advisors must not spawn agents")
        if tool == HANDBACK:
            if run and run["role"] == "advisor":
                state = tx.get("decision", run["decision_id"])
                submitted = bool(state and state.get("completion_hash"))
                message = json.dumps({"decision_id": run["decision_id"], "status": "submitted" if submitted else "not_submitted"})
                safe = {**supplied, "message": message}
                # Avoid a second free-text report channel in newer clients.
                if "summary" in safe:
                    safe["summary"] = message
                return output(name, updatedInput=safe)
            return {}
        if run:
            if run.get("route_mismatch"):
                return deny("observed model differs from the registered route")
            if run["role"] == "advisor" and operation not in ADVISOR_TOOLS:
                return deny("advisor may only fetch its own input and submit its result")
            observe_effort(run, event)
            _save(tx, session, run, clock)
            if run.get("route_mismatch"):
                return deny("observed agent effort differs from the registered route")
        if tool in SPAWN_TOOLS:
            return _dispatch(tx, event, session, config_hash, mode, clock, environment)
        if operation in ROOT_TOOLS and agent:
            return deny("root-only routing operation")
        if operation in ADVISOR_TOOLS and (not run or run["role"] != "advisor"
                                           or run["decision_id"] != supplied.get("decision_id")):
            return deny("advisor identity is not bound to this decision")
        token = secrets.token_urlsafe(32)
        receipt = {"session_id": session, "agent_id": agent, "config_hash": config_hash,
                   "tool": operation, "arguments_hash": digest(arguments(supplied))}
        tx.put("receipt", digest(token), receipt, clock() + RECEIPT_SECONDS)
        return output(name, updatedInput={**supplied, "host_receipt": token})


def failure(event, scope, configured):
    """Fail closed only where the guard is the gate; never stall anything else."""
    if scope == "plugin" and guarded(event):
        return deny("routing guard could not validate this operation; run the routing doctor")
    if scope == "plugin" and configured and event.get("hook_event_name") == "SessionStart":
        return output("SessionStart", additionalContext="Assay routing configuration is invalid or unavailable. Registered delegation stays blocked until the routing doctor passes.")
    return {}


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    scope = "agent" if list(argv[:2]) == ["--scope", "agent"] else "plugin"
    raw = sys.stdin.buffer.read(MAX_INPUT + 1)
    try:
        if len(raw) > MAX_INPUT:
            raise EvidenceError("oversized_event")
        event = json.loads(raw)
        if not isinstance(event, dict):
            raise EvidenceError("invalid_event")
    except (ValueError, RecursionError):
        # A conforming host never sends an unreadable event, and its kind is
        # unknown. Only the plugin guard fails closed; payloads are not echoed.
        if scope == "plugin":
            print("Assay routing guard could not read the hook event.", file=sys.stderr)
            return 2
        print("{}")
        return 0
    path = os.environ.get("ASSAY_ROUTING_CONFIG")
    try:
        config = load_config(Path(path)) if path else {}
        result = handle(event, config, scope=scope)
    except Exception:  # noqa: BLE001 - every failure is classified by the operation it guards
        result = failure(event, scope, bool(path))
    # ASCII JSON: a substituted prompt may hold any script, and the host console
    # encoding (for example cp1251) must not decide whether it arrives intact.
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
