"""Hold a Claude subagent's hand-back to the checks its stop would run.

A subagent that reports through SubagentHandback delivers the report when it
calls the tool, before SubagentStop fires, so feedback at the stop cannot change
what the parent received, and in observed sessions it rarely reached the
subagent at all. On PreToolUse of the hand-back the runtime runs the stop checks
on a stop event built here: the subagent's own transcript, with the report as
the final message. When a check has feedback, the first hand-back is refused
with it and the retry passes. A refused hand-back that is never repeated leaves
the parent without the report, so the reason says the next call goes through,
and without the plugin data directory, where the key is kept, nothing is
refused. At most one refusal per subagent and request, kept as one hashed key
like the mid-turn note's. After a hand-back the stop checks stay silent.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import time

from .midturn import _identity, _path
from .skill_gate import HANDBACK, _lines, _prompt

TTL = 86_400
MAX_RECORDS = 128
MAX_REPORT = 65_536


def handing_back(event):
    """Whether this is a subagent's PreToolUse of SubagentHandback with a report to check."""
    data = event.get("tool_input")
    return (event.get("hook_event_name") == "PreToolUse" and event.get("tool_name") == HANDBACK
            and isinstance(event.get("agent_id"), str) and isinstance(data, dict)
            and isinstance(data.get("message"), str))


def stop_event(event):
    """The SubagentStop event the stop checks would see if this report ended the turn."""
    return {**event, "hook_event_name": "SubagentStop", "stop_hook_active": False,
            "agent_transcript_path": _path(event), "last_assistant_message": event["tool_input"]["message"][:MAX_REPORT]}


def _key(*parts):
    return hashlib.sha256(json.dumps(["handback-hold", *parts]).encode()).hexdigest()


def held(event, feedback, directory, *, clock=time.time):
    """The refusal of a first hand-back that the stop checks have feedback for, else {}."""
    text = (feedback or {}).get("hookSpecificOutput", {}).get("additionalContext")
    identity = _identity(event)
    if not text or not directory or identity is None:
        return {}
    from route_evidence.pipeline_store import PipelineStore
    key = _key(*identity)
    with PipelineStore(Path(directory) / "handback-hold", clock=clock).transaction() as tx:
        if tx.get("hold", key):
            return {}
        records = tx.values("hold")
        if len(records) >= MAX_RECORDS:
            tx.delete("hold", min(records, key=lambda item: item["at"])["id"])
        now = clock()
        tx.put("hold", key, {"id": key, "at": now}, now + TTL)
    return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
            "permissionDecisionReason": (
                "Assay held this hand-back once, so the report has not reached the parent yet. The check below "
                "was written for an answer already delivered, so its advice not to repeat the answer does not "
                "apply here:\n" + text + "\nAct on it, then call SubagentHandback again with the complete report, "
                "not only the added lines, corrected where the check changes it. That call goes through.")}}


def handed_back(event):
    """Whether the subagent stopping now delivered its report through SubagentHandback in this turn.

    A refused hand-back delivered nothing, so a subagent that stops after one still gets
    the stop's feedback, which reaches a subagent that has not handed back.
    """
    path = event.get("agent_transcript_path")
    if event.get("hook_event_name") != "SubagentStop" or not isinstance(path, str) or not path or len(path) > 4_096:
        return False
    refused = set()
    try:
        # Newest first: a call's result is met before the call itself.
        for raw in _lines(path):
            try:
                entry = json.loads(raw) if raw.strip() else None
            except ValueError:
                continue
            if not isinstance(entry, dict):
                continue
            message = entry.get("message")
            content = message.get("content") if isinstance(message, dict) else None
            if entry.get("type") == "user" and _prompt(entry, content):
                return False
            for block in content if isinstance(content, list) else []:
                if not isinstance(block, dict):
                    continue
                if block.get("type") == "tool_result" and block.get("is_error"):
                    refused.add(block.get("tool_use_id"))
                elif (entry.get("type") == "assistant" and block.get("type") == "tool_use"
                      and block.get("name") == HANDBACK and block.get("id") not in refused):
                    return True
    except (OSError, ValueError):
        return False
    return False
