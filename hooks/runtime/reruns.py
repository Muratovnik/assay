"""Point a Claude agent that keeps rerunning one scenario at code-change's diagnostic reproducers.

A run that fails on a new setup error each time looks like progress: every
result differs, so a loop detector that waits for identical errors or a non-zero
exit stays silent. The reference already says when repeated runs should give way
to tracing the consumer's prerequisites; in the observed loops it was not open.
On PreToolUse, when a shell call runs the same script or test command for the
fifth time since the owner's last message and the reference was not read since
the latest compaction, the agent gets one note naming it. Results and exit codes
are not read. Background runs end their turn and the next one starts with a
task notification, so only a message from the owner starts the count again; a
compaction does not, because the runs it summarizes still happened.

At most one note per scenario, owner message and agent, kept as one hashed key like
the mid-turn note's. It is never a block and runs no model.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import time

from .branches import REFERENCE_PATH
from .midturn import SHELLS, _path
# What a command line runs is decided in predicates, which the hook entry reads before loading this module.
from .predicates import (INLINE, INTERPRETERS, MODULES, PREFIX, RUNNERS, SCRIPT, SEGMENT,  # noqa: F401
                         SUBCOMMANDS, TAIL, TESTING, VALUED, WRAPPERS, _program, _run, _script, _short, _tokens,
                         signature)
from .skill_gate import _lines, _prompt

RULE = "rerun-diagnostic-reproducer"
RULES = (RULE,)
SKILL, REFERENCE = "code-change", "diagnostic-reproducer.md"
THRESHOLD = 5
TTL = 86_400
MAX_RECORDS = 128
MAX_COMMAND = 65_536
MAX_EVIDENCE = 80


def _owner(entry, content):
    """A message the owner typed, unlike a task notification, a peer's message or a compaction summary."""
    if not _prompt(entry, content):
        return False
    if "turnOrigin" in entry:
        return entry["turnOrigin"] == "human"
    if "promptSource" in entry:
        return entry["promptSource"] != "system"
    text = content if isinstance(content, str) else " ".join(
        block.get("text", "") for block in content if isinstance(block, dict) and isinstance(block.get("text"), str))
    return not text.lstrip().startswith("<task-notification>")


def scan(path, wanted, current=None, *, subagent=False):
    """(earlier runs of wanted, reference read, owner message id) from a transcript's tail, or None.

    Runs are counted back to the owner's last message, across compactions; the
    reference counts as read only after the latest compaction.
    """
    if not isinstance(path, str) or not path or len(path) > 4_096:
        return None
    runs, read, owner, counting, reading = 0, False, None, True, True
    try:
        for raw in _lines(path):
            try:
                entry = json.loads(raw) if raw.strip() else None
            except ValueError:
                continue
            if not isinstance(entry, dict) or (entry.get("isSidechain") and not subagent):
                continue
            kind = entry.get("type")
            if kind == "system" and entry.get("subtype") == "compact_boundary":
                reading = False
            message = entry.get("message")
            content = message.get("content") if isinstance(message, dict) else None
            if kind == "user" and counting and _owner(entry, content):
                counting = False
                owner = entry.get("promptId") or entry.get("uuid")
                owner = owner if isinstance(owner, str) and len(owner) <= 200 else None
            if not counting and not reading:
                break
            if kind != "assistant" or not isinstance(content, list):
                continue
            for block in content:
                if not isinstance(block, dict) or block.get("type") != "tool_use" or not isinstance(block.get("input"), dict):
                    continue
                tool, data = block.get("name"), block["input"]
                if reading and tool == "Read" and isinstance(data.get("file_path"), str):
                    match = REFERENCE_PATH.search(data["file_path"])
                    read = read or bool(match and (match[1], match[2]) == (SKILL, REFERENCE))
                elif tool in SHELLS and isinstance(data.get("command"), str):
                    command = data["command"][:MAX_COMMAND]
                    read = read or (reading and SKILL in command and REFERENCE in command)
                    if counting and block.get("id") != current and signature(command) == wanted:
                        runs += 1
    except (OSError, ValueError):
        return None
    return runs, read, owner


def _identity(event):
    session, agent = event.get("session_id"), event.get("agent_id")
    if not isinstance(session, str) or not session or len(session) > 200:
        return None
    if agent is not None and (not isinstance(agent, str) or not agent or len(agent) > 200):
        return None
    return session, agent


def _key(*parts):
    return hashlib.sha256(json.dumps(["rerun-note", *parts]).encode()).hexdigest()


def text(wanted, number):
    return (f"Assay rerun note: this call is run {number} of the same scenario ({wanted[:MAX_EVIDENCE]}) since the "
            f"owner's last message. The assay:{SKILL} reference references/{REFERENCE} governs when repeated runs "
            "should give way to tracing the consumer's prerequisites; it has not been read in this context.")


def checked(event, rules, names, directory, *, clock=time.time):
    """The note for a shell call that reruns one scenario a fifth time while the reference is unread; else {}."""
    if (event.get("hook_event_name") != "PreToolUse" or RULE not in rules or SKILL not in names or not directory
            or event.get("tool_name") not in SHELLS or not isinstance(event.get("tool_input"), dict)):
        return {}
    identity = _identity(event)
    wanted = signature(event["tool_input"].get("command"))
    if identity is None or wanted is None:
        return {}
    found = scan(_path(event), wanted, event.get("tool_use_id"), subagent=event.get("agent_id") is not None)
    if not found:
        return {}
    runs, read, owner = found
    if read or runs + 1 < THRESHOLD:
        return {}
    from route_evidence.pipeline_store import PipelineStore
    key = _key(*identity, owner, wanted)
    with PipelineStore(Path(directory) / "rerun-note", clock=clock).transaction() as tx:
        if tx.get("note", key):
            return {}
        records = tx.values("note")
        if len(records) >= MAX_RECORDS:
            tx.delete("note", min(records, key=lambda item: item["at"])["id"])
        now = clock()
        tx.put("note", key, {"id": key, "at": now}, now + TTL)
    return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "additionalContext": text(wanted, runs + 1)}}
