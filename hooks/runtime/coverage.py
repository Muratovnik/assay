"""Point a Claude agent at the coverage reference behind an absence claim it made without reading it.

One note on Stop or SubagentStop, never a block: a line of the turn says that
something does not exist or that none of the options qualifies, the session
loaded evidence-research, and its search-and-coverage reference, which the
skill names for a landscape or a claim of completeness, was not read since the
latest compaction. A session or subagent that has not loaded the skill is not
held to its reference. It reads the transcript tail the skill gate reads and stores nothing.
"""
from __future__ import annotations

import json
import re

from .skill_gate import HANDBACK, NAME, _lines, _load, _prompt

SKILL = "evidence-research"
REFERENCE = "search-and-coverage.md"
REFERENCE_PATH = re.compile(r"[\\/]evidence-research[\\/]references[\\/]search-and-coverage\.md$")
SHELLS = frozenset({"Bash", "PowerShell"})
MAX_CLAIMS = 2
MAX_LINE = 2_000
MAX_QUOTE = 160
# A line saying something does not exist or that no option qualifies, in English or Russian.
ABSENCE = re.compile(
    r"\bno (?:existing|ready-made|off-the-shelf|such)\b|\bnone of (?:them|these|those|the)\b"
    r"|\b(?:does|do)(?:n't| not) (?:yet )?exist\b|\bnothing (?:like (?:this|that|it)|similar|comparable)\b"
    r"|\bnot aware of any\b|\bnowhere\b"
    r"|\bthere (?:is|are) no (?:[\w-]+ ){0,3}(?:tools?|solutions?|skills?|librar(?:y|ies)|packages?"
    r"|alternatives?|projects?|implementations?|options?)\b"
    r"|\bни од(?:ин|на|но|ного|ной)\b|\bнигде\b|\bне существу|\bтакого нет\b|\bничего (?:подобного|похожего)"
    r"|\bнет (?:ни )?(?:готов|существующ|подобн)|\bготов\w* (?:[\w-]+ ){0,2}нет\b", re.I)


def _absent(text):
    return [line for line in text.splitlines() if ABSENCE.search(line[:MAX_LINE])] if isinstance(text, str) else []


def ledger(path, *, subagent=False, needed=False):
    """(claims, loaded, read) from a transcript's tail, or None when it cannot be read.

    Claims: lines of this turn's messages that say something is absent. Loaded
    and read say whether evidence-research was loaded and its coverage
    reference read since the latest compaction, a shell command naming the
    reference counting as a read. Without a claim in the turn, and unless
    needed says the final message holds one, the scan stops at the turn's start.
    """
    if not isinstance(path, str) or not path or len(path) > 4_096:
        return None
    claims, loaded, read, in_turn = [], False, False, True
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
                # Compaction re-attaches the skills it keeps; their references are not re-read.
                loaded = loaded or any(isinstance(skill, dict) and isinstance(skill.get("name"), str)
                                       and (NAME.fullmatch(skill["name"]) or [None, None])[1] == SKILL
                                       for skill in attachment.get("skills") or [])
                continue
            message = entry.get("message")
            content = message.get("content") if isinstance(message, dict) else None
            if kind == "user" and in_turn and _prompt(entry, content):
                in_turn = False
                if not claims and not needed:
                    break  # Nothing to check: earlier loads and reads would go unused.
            if kind != "assistant" or not isinstance(content, list):
                continue
            for block in content:
                if not isinstance(block, dict):
                    continue
                data = block.get("input")
                if block.get("type") == "text" and in_turn:
                    claims += _absent(block.get("text"))
                elif block.get("type") != "tool_use" or not isinstance(data, dict):
                    continue
                elif block.get("name") == HANDBACK and in_turn:
                    claims += _absent(data.get("message"))
                elif _load(block.get("name"), data, {SKILL}):
                    loaded = True
                elif block.get("name") == "Read" and isinstance(data.get("file_path"), str):
                    read = read or bool(REFERENCE_PATH.search(data["file_path"]))
                elif block.get("name") in SHELLS and isinstance(data.get("command"), str):
                    read = read or REFERENCE in data["command"]
    except (OSError, ValueError):
        return None
    return claims, loaded, read


def _quote(line):
    line = " ".join(line.split())
    return "“" + (line if len(line) <= MAX_QUOTE else line[:MAX_QUOTE - 1] + "…") + "”"


def stopped(event):
    """Continuation feedback on Stop or SubagentStop for an absence claim made without the coverage reference, else {}."""
    name = event.get("hook_event_name")
    if name not in {"Stop", "SubagentStop"} or event.get("stop_hook_active"):
        return {}
    if name == "SubagentStop" and not event.get("agent_id"):
        return {}
    last = event.get("last_assistant_message")
    final = _absent(last[:65_536]) if isinstance(last, str) else []
    path = event.get("agent_transcript_path") if name == "SubagentStop" else event.get("transcript_path")
    scan = ledger(path, subagent=name == "SubagentStop", needed=bool(final))
    if not scan:
        return {}
    claims, loaded, read = scan
    claims = list(dict.fromkeys([*final, *claims]))
    if not claims or not loaded or read:
        return {}
    quoted = "; ".join(_quote(line) for line in claims[:MAX_CLAIMS])
    # Stated as facts, as the skill gate's feedback is.
    return {"hookSpecificOutput": {"hookEventName": name, "additionalContext": (
        f"Assay coverage check: this turn says something is absent or that none qualifies ({quoted}), and "
        f"evidence-research's references/{REFERENCE}, which the skill names for a landscape or a claim of "
        "completeness, was not read in this context. Evidence absent from the examined scope is not proof that "
        "it does not exist. The answer already given stands: when the claim is already limited to what was "
        "examined and names that scope, one short line saying so is enough; otherwise only the corrections that "
        "would change the user's conclusion, without repeating the answer.")}}
