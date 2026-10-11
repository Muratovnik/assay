"""Opt-in passive execution capture; permission and launch arguments stay with routing."""
from __future__ import annotations

import os
import re
from pathlib import Path
import time

from route_evidence.advisor_config import settings
from route_evidence.core import EvidenceError, digest, read_document, number, epoch, loads
from route_evidence.history import HistoryStore, _refuse_link_ancestors, _identifier, _usage, _route
from route_evidence.pipeline_config import settings as pipeline_settings
from route_evidence.pipeline_store import PipelineStore
from route_evidence.service import load_config
from route_evidence.telemetry import append, bound_attempts, observe_transcript

LINK = re.compile(r"(?m)^\[assay-routing:([A-Za-z0-9_.:-]{1,200})/([A-Za-z0-9_.:-]{1,200})\]$")


def spawn_response(value):
    if isinstance(value, str):
        try:
            value = loads(value)
        except EvidenceError:
            return {}
    return value if isinstance(value, dict) else {}


def configuration(environment):
    location = environment.get("ASSAY_ROUTING_TELEMETRY_CONFIG")
    if not location:
        data = environment.get("PLUGIN_DATA") or environment.get("CLAUDE_PLUGIN_DATA")
        if not data:
            return None
        location = str(Path(data) / "routing-telemetry.json")
        if not Path(location).exists():
            return None
    path = Path(location)
    if not path.is_absolute():
        raise EvidenceError("routing telemetry configuration must be absolute")
    _refuse_link_ancestors(path)
    raw = read_document(path)
    if not isinstance(raw, dict) or set(raw) != {"config", "cache_dir"}:
        raise EvidenceError("routing telemetry binding requires config and cache_dir")
    for value in raw.values():
        if not isinstance(value, str) or not Path(value).is_absolute():
            raise EvidenceError("routing telemetry binding paths must be absolute")
        _refuse_link_ancestors(Path(value))
    return raw


def capture(event, client, environment, *, clock=time.time):
    name = event.get("hook_event_name")
    if name not in {"PreToolUse", "SubagentStop", "PostToolUse", "PostToolUseFailure"}:
        return
    binding = configuration(environment)
    if binding is None:
        return
    config = load_config(Path(binding["config"]))
    if config.get("client") != client:
        raise EvidenceError("routing telemetry client binding mismatch")
    telemetry = settings(config)["telemetry"]
    if telemetry["mode"] == "off":
        return
    store = HistoryStore(Path(binding["cache_dir"]), clock=clock, **telemetry,
                         retain_descriptions=config.get("task_evidence", {}).get("retain_descriptions", False))
    session, agent = event.get("session_id"), event.get("agent_id")
    tool_id = event.get("tool_use_id")
    pending_store = PipelineStore(Path(binding["cache_dir"]) / "routing-telemetry-hooks", clock=clock)
    if name == "PreToolUse":
        if event.get("tool_name") not in {"Agent", "Task", "spawn_agent"} or not session or not tool_id:
            return
        supplied = event.get("tool_input", {})
        prompt = supplied.get("prompt", supplied.get("message")) if isinstance(supplied, dict) else None
        if not isinstance(prompt, str):
            return
        links = LINK.findall(prompt)
        if not links:
            return
        _identifier(session, "native.session_id")
        _identifier(tool_id, "native.tool_use_id")
        resume = supplied.get("resume")
        if resume is not None:
            _identifier(resume, "native.resume")
        if len(links) != 1:
            raise EvidenceError("launch must contain one unambiguous routing telemetry link")
        did, pid = links[0]
        decision = store.read(did)
        if (decision is None or decision["snapshot"]["client"] != client or
                not any(d["packet_id"] == pid for d in decision["decisions"])):
            raise EvidenceError("launch telemetry link does not name a retained client packet")
        with pending_store.transaction() as tx:
            tx.put("launch-link", digest({"session": session, "tool": tool_id}),
                   {"decision_id": did, "packet_id": pid, "session_id": session, "tool_use_id": tool_id,
                    "resume": resume}, min(epoch(decision["expires_at"]), clock() + 86400))
        return
    if name != "SubagentStop":
        if event.get("tool_name") not in {"Agent", "Task", "spawn_agent"}:
            return
        response = spawn_response(event.get("tool_response"))
        if isinstance(response, dict):
            agent = response.get("agentId", response.get("agent_id"))
    if not session:
        return
    _identifier(session, "native.session_id")
    attempts = []
    if name in {"PostToolUse", "PostToolUseFailure"} and tool_id:
        _identifier(tool_id, "native.tool_use_id")
        with pending_store.transaction() as tx:
            link = tx.get("launch-link", digest({"session": session, "tool": tool_id}))
        if link:
            attempts = [{"decision_id": link["decision_id"], "packet_id": link["packet_id"],
                         "execution_ref": "native-" + digest(link),
                         "runtime": {"client": client, "session_id": session, "agent_id": agent,
                                     "tool_use_id": tool_id}}]
    if not agent:
        if name == "PostToolUseFailure":
            for attempt in attempts:
                ident = "hook-" + digest({"attempt": attempt, "event": name})
                append(store, "observation", attempt["decision_id"], attempt["packet_id"], attempt["execution_ref"], ident,
                       {"source": "native_hook", "status": "failed", "tool_use_id": tool_id})
            with pending_store.transaction() as tx:
                tx.delete("launch-link", digest({"session": session, "tool": tool_id}))
        if attempts and name == "PostToolUse":
            raise EvidenceError("native launch receipt missing worker identity; record the native spawn UUID explicitly")
        return
    _identifier(agent, "native.agent_id")
    returned = spawn_response(event.get("tool_response"))
    raw_effort = event.get("effort")
    host_route = _route({"observed": {
        "model": returned.get("resolvedModel") if isinstance(returned, dict) else None,
        "effort": raw_effort.get("level") if isinstance(raw_effort, dict) else None}}, "observed")
    host_settings = ([{"route": host_route, "provenance": "native:" + name}]
                     if host_route else [])
    if name == "SubagentStop" and event.get("agent_transcript_path") and pending_store.directory.exists():
        with pending_store.transaction() as tx:
            launches = [v for v in tx.values("launch-link") if v["session_id"] == session]
            resuming = any(v.get("resume") == agent for v in launches)
            known = bound_attempts(store, client, session, agent, allow_ambiguous=True)
            pending = bool(launches) and (resuming or not known)
            if pending:
                tx.put("pending-stop", digest({"session": session, "agent": agent}),
                       {"session_id": session, "agent_id": agent, "transcript_path": event["agent_transcript_path"],
                        "effective_settings": host_settings}, clock() + 600)
        if pending:
            return
    pipeline = pipeline_settings(config)
    if not attempts and pipeline["mode"] == "required" and pipeline["state_dir"]:
        with PipelineStore(Path(pipeline["state_dir"]), clock=clock).transaction() as tx:
            run = tx.get("agent", session + ":" + agent)
        if run and run.get("role") == "worker" and run.get("binding") != "start_order":
            attempts = [{"decision_id": run["decision_id"], "packet_id": run["packet_id"],
                         "execution_ref": run["attempt_id"],
                         "runtime": {"client": client, "session_id": session, "agent_id": agent}}]
    if not attempts:
        attempts = bound_attempts(store, client, session, agent)
    completed_return = name == "PostToolUse" and isinstance(returned, dict) and returned.get("status") == "completed"
    status = "completed" if name == "SubagentStop" or completed_return else "failed" if name == "PostToolUseFailure" else "launched"
    for attempt in attempts:
        ident = "hook-" + digest({"attempt": attempt, "event": name, "tool_use_id": event.get("tool_use_id")})
        data = {"source": "native_hook", "runtime": attempt["runtime"], "status": status}
        if host_settings:
            data["effective_settings"] = host_settings
        if completed_return:
            if returned.get("totalDurationMs") is not None:
                data["duration_seconds"] = number(returned["totalDurationMs"], "native.totalDurationMs") / 1000
            if returned.get("usage") is not None:
                data["reported_usage"] = _usage(returned["usage"], provenance="native:AgentOutput")
        append(store, "observation", attempt["decision_id"], attempt["packet_id"], attempt["execution_ref"], ident, data)
        transcript = event.get("agent_transcript_path") if name == "SubagentStop" else None
        if transcript:
            observe_transcript(store, {**attempt, "transcript_path": transcript}, source="native_hook", status=status)
        if name == "PostToolUse":
            with pending_store.transaction() as tx:
                stopped = tx.get("pending-stop", digest({"session": session, "agent": agent}))
                tx.delete("launch-link", digest({"session": session, "tool": tool_id}))
                tx.delete("pending-stop", digest({"session": session, "agent": agent}))
            if stopped:
                if stopped.get("effective_settings"):
                    append(store, "observation", attempt["decision_id"], attempt["packet_id"], attempt["execution_ref"],
                           "settings-" + digest({"attempt": attempt, "settings": stopped["effective_settings"]}),
                           {"source": "native_hook", "runtime": attempt["runtime"], "status": "completed",
                            "effective_settings": stopped["effective_settings"]})
                observe_transcript(store, {**attempt, "transcript_path": stopped["transcript_path"]},
                                   source="native_hook", status="completed")
