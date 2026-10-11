"""What a Claude host ran for a requested model alias and effort.

The Agent call takes a model alias and an effort level. Its hooks report the full
model ID the alias resolved to (`resolvedModel`) and the level that actually ran
(`effort.level`), which can be lower when a model lacks the requested one. These
observations stand in for a maintained alias table: use refreshes them, they
expire, and nothing here guesses a mapping that was not observed.
"""
from __future__ import annotations

import time
from pathlib import Path

from .core import EvidenceError, digest, loads, timestamp
from .pipeline_store import PipelineStore

DIRECTORY = "host-observations"
PENDING_SECONDS = 86400
KEEP_SECONDS = 30 * 86400
MAX_REPORTED = 32


def _store(root, clock):
    return PipelineStore(Path(root) / DIRECTORY, clock=clock)


def _text(value):
    return value if isinstance(value, str) and 0 < len(value) <= 200 and value.isprintable() else None


def _response(value):
    if isinstance(value, str):
        try:
            value = loads(value)
        except EvidenceError:
            return {}
    return value if isinstance(value, dict) else {}


def _effort(tx, launched, applied, now):
    tx.put("effort", digest({"model": launched["model"], "requested": launched["requested"]}),
           {**launched, "applied": applied, "observed_at": timestamp(now)}, now + KEEP_SECONDS)


def observe(event, root, *, clock=time.time):
    """Record one Agent launch request, its return or its stop.

    A launch is keyed by its tool use; its worker by the agent ID the return
    names. A foreground worker can stop before its call returns, so either
    order completes the effort observation.
    """
    name, session = event.get("hook_event_name"), _text(event.get("session_id"))
    if not session:
        return
    now = clock()
    if name == "SubagentStop":
        agent, effort = _text(event.get("agent_id")), event.get("effort")
        level = _text(effort.get("level")) if isinstance(effort, dict) else None
        if agent and level and _store(root, clock).path.exists():
            with _store(root, clock).transaction() as tx:
                key = digest({"session": session, "agent": agent})
                launched = tx.get("launched", key)
                tx.delete("launched", key)
                if launched:
                    _effort(tx, launched, level, now)
                elif tx.values("requested"):
                    tx.put("stopped", key, {"applied": level}, now + PENDING_SECONDS)
        return
    tool = _text(event.get("tool_use_id"))
    if event.get("tool_name") not in {"Agent", "Task"} or not tool:
        return
    key = digest({"session": session, "tool": tool})
    if name == "PreToolUse":
        supplied = event.get("tool_input")
        if not isinstance(supplied, dict) or supplied.get("resume") or supplied.get("subagent_type") == "fork":
            return
        requested = {"model": _text(supplied.get("model")), "effort": _text(supplied.get("effort"))}
        if any(requested.values()):
            with _store(root, clock).transaction() as tx:
                tx.put("requested", key, requested, now + PENDING_SECONDS)
        return
    if name not in {"PostToolUse", "PostToolUseFailure"} or not _store(root, clock).path.exists():
        return
    response = _response(event.get("tool_response"))
    with _store(root, clock).transaction() as tx:
        requested = tx.get("requested", key)
        tx.delete("requested", key)
        if not requested or name == "PostToolUseFailure":
            return
        resolved = _text(response.get("resolvedModel"))
        if requested["model"] and resolved:
            tx.put("alias", requested["model"], {"alias": requested["model"], "model": resolved,
                                                 "observed_at": timestamp(now)}, now + KEEP_SECONDS)
        agent = _text(response.get("agentId", response.get("agent_id")))
        if requested["effort"] and agent:
            launched = {"model": resolved, "requested": requested["effort"]}
            worker = digest({"session": session, "agent": agent})
            stopped = tx.get("stopped", worker)
            tx.delete("stopped", worker)
            if stopped:
                _effort(tx, launched, stopped["applied"], now)
            else:
                tx.put("launched", worker, launched, now + PENDING_SECONDS)


def summary(root, *, clock=time.time):
    """Latest alias resolutions and effort applications, newest first; empty when none."""
    store = _store(root, clock)
    if not store.path.exists():
        return {"aliases": [], "efforts": []}
    with store.transaction() as tx:
        aliases, efforts = tx.values("alias"), tx.values("effort")
    newest = lambda rows: sorted(rows, key=lambda row: row["observed_at"], reverse=True)[:MAX_REPORTED]
    return {"aliases": newest(aliases), "efforts": newest(efforts)}
