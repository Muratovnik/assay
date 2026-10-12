"""Hold a Claude reply or subagent report to the Assay skills it names; never route, authorize or launch work.

The skill check asks the agent to start its final reply with "Assay: ...".
This gate records which skills the session actually loaded (Skill tool calls
and reads of a SKILL.md) and, when the reply names a skill that was never
loaded, continues the turn once with hook feedback saying so. The feedback is
not a block: Claude Code shows no hook error for it. It reads the hook input
only, never the transcript, and it judges nothing about whether the named
skills were the right choice.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import time

TTL = 86_400
MAX_RECORDS = 128
DECLARATION = re.compile(r"^[\W_]*assay[\W_]*:[\W_]*(.*)$", re.I)
NAME = re.compile(r"(?:assay:)?([a-z][a-z0-9-]{0,63})")
SKILL_FILE = re.compile(r"[\\/]skills[\\/]([a-z][a-z0-9-]{0,63})[\\/]SKILL\.md$")
MAX_SCAN = 4_096


def _key(event):
    session, agent = event.get("session_id"), event.get("agent_id")
    if not isinstance(session, str) or not session or len(session) > 200:
        return None
    if agent is not None and (not isinstance(agent, str) or not agent or len(agent) > 200):
        return None
    # The root and each subagent keep separate records: a worker's load does
    # not satisfy the root's reply, and the reverse.
    return hashlib.sha256(json.dumps(["skill-gate", session, agent]).encode()).hexdigest()


def loaded_name(event, names):
    """The Assay skill a PreToolUse event loads, or None."""
    tool, data = event.get("tool_name"), event.get("tool_input")
    if not isinstance(data, dict):
        return None
    if tool == "Skill" and isinstance(data.get("skill"), str):
        match = NAME.fullmatch(data["skill"].strip())
    elif tool == "Read" and isinstance(data.get("file_path"), str):
        match = SKILL_FILE.search(data["file_path"])
    else:
        return None
    return match[1] if match and match[1] in names else None


def declared(text, names):
    """Skills named on the reply's leading "Assay:" line; none when it has no such line."""
    if not isinstance(text, str):
        return []
    lines = [line.strip() for line in text[:MAX_SCAN].splitlines() if line.strip()]
    match = DECLARATION.match(lines[0]) if lines else None
    if not match:
        return []
    found = []
    for token in re.split(r"[\s,;()]+", match[1]):
        name = NAME.fullmatch(token.strip(".*`'\""))
        if name and name[1] in names and name[1] not in found:
            found.append(name[1])
    return found


def apply(event, client, names, directory, *, clock=time.time):
    """Record a load on PreToolUse; on Stop or SubagentStop return continuation feedback or {}.

    A subagent's tool calls carry its agent_id, and so does its SubagentStop, so
    a worker's report is held to the skills that worker loaded.
    """
    if client != "claude" or not directory:
        return {}
    name, key = event.get("hook_event_name"), _key(event)
    if key is None or name not in {"PreToolUse", "Stop", "SubagentStop"}:
        return {}
    if name == "SubagentStop" and not event.get("agent_id"):
        return {}
    from route_evidence.pipeline_store import PipelineStore
    with PipelineStore(Path(directory) / "skill-gate", clock=clock).transaction() as tx:
        record = tx.get("loads", key) or {"skills": []}
        if name == "PreToolUse":
            skill = loaded_name(event, names)
            if skill and skill not in record["skills"]:
                records = tx.values("loads")
                if len(records) >= MAX_RECORDS and not tx.get("loads", key):
                    tx.delete("loads", min(records, key=lambda item: item["at"])["id"])
                now = clock()
                tx.put("loads", key, {"id": key, "at": now, "skills": [*record["skills"], skill]}, now + TTL)
            return {}
        if event.get("stop_hook_active"):
            return {}  # One continuation at most; never trap the turn.
        missing = [skill for skill in declared(event.get("last_assistant_message"), names)
                   if skill not in record["skills"]]
    if not missing:
        return {}
    listed = ", ".join(missing)
    who = "this subagent" if name == "SubagentStop" else "this session"
    # Stated as facts, not commands: the client continues the turn under the
    # same loop limits as a block, and an imperative out-of-band message is
    # what prompt-injection defenses are wary of.
    return {"hookSpecificOutput": {"hookEventName": name, "additionalContext": (
        f"Assay skill gate: the reply's Assay line names {listed}, and {who} has not loaded "
        f"{'that skill' if len(missing) == 1 else 'those skills'}. The skill check expects each named skill "
        "to be loaded (skill tool or its SKILL.md) and the work checked against it before the final reply, "
        "which starts with the Assay line again.")}}
