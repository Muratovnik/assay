"""Preserve native payloads; client identity comes from the installed command."""
from __future__ import annotations

import hashlib
import json

EVENTS = {
    "claude": {"SessionStart", "UserPromptSubmit", "PreToolUse", "PostToolUse", "PostToolUseFailure",
               "PermissionDenied", "SubagentStart", "SubagentStop", "SessionEnd"},
    "codex": {"SessionStart", "UserPromptSubmit", "PreToolUse", "PostToolUse", "SubagentStart",
              "SubagentStop", "PostCompact", "SessionEnd"},
}
ALIASES = {"claude": {"Agent": "spawn", "Task": "spawn"},
           "codex": {"spawn_agent": "spawn", "apply_patch": "edit"}}


def normalize(event, client):
    if client not in EVENTS or not isinstance(event, dict):
        raise ValueError("unknown hook client or invalid event")
    name = event.get("hook_event_name")
    if not isinstance(name, str) or name not in EVENTS[client]:
        return None
    native = event.get("tool_name")
    if native is not None and not isinstance(native, str):
        raise ValueError("invalid native tool name")
    return {"client": client, "event": name, "native_tool": native,
            "operation": ALIASES[client].get(native), "payload": event}


def identity(event, client):
    """No guessed task identity; never merge subagents by parent session alone."""
    session, cwd = event.get("session_id"), event.get("cwd")
    if not isinstance(session, str) or not session or not isinstance(cwd, str) or not cwd:
        return None
    agent = event.get("agent_id")
    if agent is not None and (not isinstance(agent, str) or not agent):
        return None
    # In Codex, use transcript identity as an additional discriminator because
    # not every turn-scoped event carries agent_id. Never read the transcript.
    transcript = event.get("transcript_path") if client == "codex" else None
    if transcript is not None and (not isinstance(transcript, str) or not transcript):
        return None
    if client == "codex" and not agent and not transcript:
        return None  # Parent session alone cannot distinguish Codex workers.
    values = [client, session, cwd, agent, transcript]
    if any(isinstance(v, str) and len(v) > 4096 for v in values):
        return None
    return hashlib.sha256(json.dumps(values, sort_keys=True).encode()).hexdigest()


def event_key(event, client):
    # Claude prompt events have no stable turn id. Hashing their text would
    # confuse a legitimate repeated/new request with duplicate delivery.
    turn = event.get("turn_id") if client == "codex" else None
    tool = event.get("tool_use_id")
    if event.get("hook_event_name") == "UserPromptSubmit" and isinstance(turn, str) and turn:
        return "prompt:" + turn
    if isinstance(tool, str) and tool:
        return event["hook_event_name"] + ":" + tool
    return None
