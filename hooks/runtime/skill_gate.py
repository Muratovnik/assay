"""Hold a Claude turn or subagent report to the Assay skills it announces; never route, authorize or launch work.

The skill check asks the agent to announce a skill it starts applying in one
sentence naming it as `assay:<name>`. This gate records which skills the
session actually loaded (Skill tool calls and reads of a SKILL.md) and, when
the turn announces a skill that was never loaded, continues the turn once with
hook feedback saying so. The feedback is not a block: Claude Code shows no hook
error for it. It judges nothing about whether the announced skills were the
right choice.

An announcement usually opens an earlier message of the turn, so on Stop the
gate reads the tail of the transcript, as the hooks reference suggests for
conditions the input alone cannot settle. The same read finds loads the
records miss: a continued, resumed or forked session gets a new session id,
and compaction re-attaches the skills it keeps. The transcript is written
asynchronously, so it is a best-effort source; an unreadable one leaves the
gate exactly as strict as the records alone.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import time

TTL = 86_400
MAX_RECORDS = 128
MAX_SCAN = 4_096
# Bytes read back from the end of a transcript, in blocks.
MAX_TRANSCRIPT = 16 * 1024 * 1024
BLOCK = 256 * 1024
# The previous format, a leading "Assay: name, name" line, still counts.
LEGACY = re.compile(r"^[\W_]*assay[\W_]*:[\W_]*(.*)$", re.I)
CODE_SPAN = re.compile(r"`([^`\n]+)`")
QUALIFIED = re.compile(r"assay:([a-z][a-z0-9-]{0,63})(?![\w-])")
NAME = re.compile(r"(?:assay:)?([a-z][a-z0-9-]{0,63})")
SKILL_FILE = re.compile(r"[\\/]skills[\\/]([a-z][a-z0-9-]{0,63})[\\/]SKILL\.md$")
# The host channel through which a subagent may deliver its report.
HANDBACK = "SubagentHandback"


def _key(event):
    session, agent = event.get("session_id"), event.get("agent_id")
    if not isinstance(session, str) or not session or len(session) > 200:
        return None
    if agent is not None and (not isinstance(agent, str) or not agent or len(agent) > 200):
        return None
    # The root and each subagent keep separate records: a worker's load does
    # not satisfy the root's reply, and the reverse.
    return hashlib.sha256(json.dumps(["skill-gate", session, agent]).encode()).hexdigest()


def _load(tool, data, names):
    if not isinstance(data, dict):
        return None
    if tool == "Skill" and isinstance(data.get("skill"), str):
        match = NAME.fullmatch(data["skill"].strip())
    elif tool == "Read" and isinstance(data.get("file_path"), str):
        match = SKILL_FILE.search(data["file_path"])
    else:
        return None
    return match[1] if match and match[1] in names else None


def loaded_name(event, names):
    """The Assay skill a PreToolUse event loads, or None."""
    return _load(event.get("tool_name"), event.get("tool_input"), names)


def declared(text, names):
    """Skills a message's first line announces: `assay:<name>` in code spans, or the legacy "Assay:" line."""
    if not isinstance(text, str):
        return []
    line = next((line.strip() for line in text[:MAX_SCAN].splitlines() if line.strip()), "")
    tokens = [match[1] for span in CODE_SPAN.findall(line) for match in QUALIFIED.finditer(span)]
    legacy = None if tokens else LEGACY.match(line)
    if legacy:
        names_found = (NAME.fullmatch(token.strip(".*`'\"")) for token in re.split(r"[\s,;()]+", legacy[1]))
        tokens = [name[1] for name in names_found if name]
    found = []
    for token in tokens:
        if token in names and token not in found:
            found.append(token)
    return found


def _lines(path):
    """Complete transcript lines, newest first, from at most MAX_TRANSCRIPT trailing bytes."""
    with Path(path).expanduser().open("rb") as stream:
        position = stream.seek(0, 2)
        floor, rest = max(0, position - MAX_TRANSCRIPT), b""
        while position > floor:
            size = min(BLOCK, position - floor)
            position -= size
            stream.seek(position)
            parts = (stream.read(size) + rest).split(b"\n")
            rest = parts.pop(0)
            yield from reversed(parts)
        if floor == 0:
            yield rest  # A line cut by the byte bound is incomplete and skipped.


def _prompt(entry, content):
    """A user entry that starts a turn, unlike a tool result, meta entry or compaction summary."""
    if entry.get("isMeta") or entry.get("isCompactSummary") or entry.get("isVisibleInTranscriptOnly"):
        return False
    if isinstance(content, str):
        return True
    blocks = [block for block in content or [] if isinstance(block, dict)]
    return (any(block.get("type") == "text" for block in blocks)
            and not any(block.get("type") == "tool_result" for block in blocks))


def transcript(path, names, *, subagent=False, loads_needed=lambda announced, loaded: True):
    """(announced, loaded) from a transcript's tail, or None when it cannot be read.

    Announced: skills the first lines of this turn's messages announce, newest
    first. Loaded: Skill calls and SKILL.md reads since the latest compaction,
    plus the skills that compaction re-attached; an older load did not survive
    it. The scan stops at the turn's start when loads_needed(announced, loaded)
    is false.
    In the main transcript a subagent's entries are skipped.
    """
    if not isinstance(path, str) or not path or len(path) > 4_096:
        return None
    announced, loaded, in_turn = [], set(), True
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
                break
            attachment = entry.get("attachment")
            if kind == "attachment" and isinstance(attachment, dict) and attachment.get("type") == "invoked_skills":
                for skill in attachment.get("skills") or []:
                    name = NAME.fullmatch(skill.get("name", "")) if isinstance(skill, dict) and isinstance(
                        skill.get("name"), str) else None
                    if name and name[1] in names:
                        loaded.add(name[1])
                continue
            message = entry.get("message")
            content = message.get("content") if isinstance(message, dict) else None
            if kind == "user" and in_turn and _prompt(entry, content):
                in_turn = False
                if not loads_needed(announced, loaded):
                    break
            if kind != "assistant" or not isinstance(content, list):
                continue
            for block in content:
                if not isinstance(block, dict):
                    continue
                if block.get("type") == "tool_use":
                    data = block.get("input")
                    skill = _load(block.get("name"), data, names)
                    if skill:
                        loaded.add(skill)
                    if in_turn and block.get("name") == HANDBACK and isinstance(data, dict):
                        announced += declared(data.get("message"), names)
                elif block.get("type") == "text" and in_turn:
                    announced += declared(block.get("text"), names)
    except (OSError, ValueError):
        return None
    return list(dict.fromkeys(announced)), loaded


def loaded(event, client, names, directory, *, clock=time.time):
    """Skills the records say this session or subagent loaded, oldest first; never raises."""
    if client != "claude" or not directory:
        return []
    key = _key(event)
    if key is None:
        return []
    try:
        from route_evidence.pipeline_store import PipelineStore
        with PipelineStore(Path(directory) / "skill-gate", clock=clock).transaction() as tx:
            record = tx.get("loads", key)
    except Exception:
        return []
    return [skill for skill in (record or {}).get("skills", []) if skill in names]


def _save(tx, key, skills, clock):
    records = tx.values("loads")
    if len(records) >= MAX_RECORDS and not tx.get("loads", key):
        tx.delete("loads", min(records, key=lambda item: item["at"])["id"])
    now = clock()
    # The expiry slides with use: a long session keeps its loads.
    tx.put("loads", key, {"id": key, "at": now, "skills": skills}, now + TTL)


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
    if name != "PreToolUse" and event.get("stop_hook_active"):
        return {}  # One continuation at most; never trap the turn.
    from route_evidence.pipeline_store import PipelineStore
    store = PipelineStore(Path(directory) / "skill-gate", clock=clock)
    if name == "PreToolUse":
        skill = loaded_name(event, names)
        if skill:
            with store.transaction() as tx:
                record = tx.get("loads", key) or {"skills": []}
                if skill not in record["skills"]:
                    _save(tx, key, [*record["skills"], skill], clock)
        return {}
    with store.transaction() as tx:
        record = tx.get("loads", key)
    known = set(record["skills"]) if record else set()
    announced = declared(event.get("last_assistant_message"), names)
    path = event.get("agent_transcript_path") if name == "SubagentStop" else event.get("transcript_path")
    scan = transcript(path, names, subagent=name == "SubagentStop",
                      loads_needed=lambda turn, found: any(skill not in known | found for skill in [*announced, *turn]))
    if scan:
        announced = list(dict.fromkeys([*announced, *scan[0]]))
    missing = [skill for skill in announced if skill not in known and not (scan and skill in scan[1])]
    found = sorted(scan[1] - known) if scan else []
    if record or found:
        with store.transaction() as tx:
            current = (tx.get("loads", key) or {"skills": []})["skills"]
            _save(tx, key, [*current, *[skill for skill in found if skill not in current]], clock)
    if not missing:
        return {}
    listed = ", ".join(missing)
    who = "this subagent" if name == "SubagentStop" else "this session"
    # Stated as facts, not commands: the client continues the turn under the
    # same loop limits as a block, and an imperative out-of-band message is
    # what prompt-injection defenses are wary of.
    return {"hookSpecificOutput": {"hookEventName": name, "additionalContext": (
        f"Assay skill gate: this turn announces {listed}, and {who} has not loaded "
        f"{'that skill' if len(missing) == 1 else 'those skills'}. The skill check expects each announced "
        "skill to be loaded (skill tool or its SKILL.md) and the work checked against it. The answer already "
        "given stands: after loading, one short line is enough when nothing changes, otherwise only the "
        "corrections that would change the user's code, conclusions or decisions, without repeating the "
        "answer or the announcement. A line that only mentioned a skill without applying it needs one line "
        "saying so.")}}
