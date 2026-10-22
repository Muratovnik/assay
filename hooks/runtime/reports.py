"""Hold a Claude turn that changed code or wrote a plan to the report lines its skills ask for.

A hook cannot judge whether a check was the right one or whether something
already existed, but it can see that the line stating it is missing. Each row
pairs a sign in the turn's own tool calls with a line the final message or the
written plan must carry: a `Verified:` or `Not verified:` line after editing
code, a `Reuse:` line after creating a source file, a `What already exists`
section in a plan file. Localized labels count. On Stop or SubagentStop the turn
continues once with one note naming each missing line. It is never a block, runs
no model and stores nothing. A write made through a shell command is seen only
when the turn stages the file with `git add`.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
import re

from .branches import PLAN, WRITES, _written
from .midturn import SEPARATOR, SHELLS, classify
from .skill_gate import _lines, _prompt


@dataclass(frozen=True)
class Row:
    rule: str  # The ID that disabled_rules turns off.
    skill: str  # The skill whose report contract the line belongs to.
    missing: str  # What the note says is absent, completed by the files.
    line: str  # The form of the line the skill asks for.


ROWS = (
    Row("report-verification", "code-change", "the final message has no verification line",
        "`Verified: <check> — <environment> — after <change>` per material check and `Not verified: <what> — <why>` "
        "per gap"),
    Row("report-reuse", "code-change", "the final message has no reuse line",
        "`Reuse: …` from references/reuse-and-migration.md, or `Reuse: not applicable — <why>`"),
    Row("plan-existing", "implementation-planning", "the plan has no section on what already exists",
        "a `What already exists` section: capabilities and solutions considered, where they were looked for, why "
        "each fits or not"),
)
RULES = tuple(row.rule for row in ROWS)

MAX_TEXT = 65_536
MAX_ITEMS = 3
CREATED = "File created successfully"
# A label at the start of a line, optionally in a list item or bold.
LABEL = r"^[ \t]*(?:[-*+][ \t]+)?(?:\*\*|__)?(?:{})(?:\*\*|__)?[ \t]*:"
VERIFIED = re.compile(LABEL.format(r"not[ \t]+verified|verified|не[ \t]+проверено|проверено"), re.I | re.M)
REUSE = re.compile(LABEL.format(r"reuse|переиспользование"), re.I | re.M)
EXISTING = re.compile(r"^[ \t]*#{1,6}[ \t]+(?:\d+[.)][ \t]*)?(?:what already exists|что уже есть)\b", re.I | re.M)
# A file that holds behavior: source, a test or an interface.
CODE = frozenset({"midturn-code-change", "midturn-test-writing", "midturn-ui-delivery"})
# The paths of `git add`, up to the end of that command.
GIT_ADD = re.compile(r"\bgit(?:\s+-C\s+\S+)?\s+add\s+([^;&|\n]+)")


def _result_text(block):
    content = block.get("content")
    if isinstance(content, list):
        content = " ".join(item.get("text", "") for item in content if isinstance(item, dict)
                           and isinstance(item.get("text"), str))
    return content if isinstance(content, str) else ""


def _staged(command):
    """Code files a shell command stages with `git add`: the trace a shell edit leaves."""
    names = []
    for match in GIT_ADD.finditer(command[:MAX_TEXT]):
        for token in match[1].split():
            token = token.strip("'\"")
            if token and not token.startswith("-") and classify(token) in CODE:
                names.append(SEPARATOR.split(token)[-1])
    return names


def _oldest_first(names):
    """Names collected newest first, deduplicated, in the order the turn wrote them."""
    return list(dict.fromkeys(reversed(names)))


def turn(path, *, subagent=False):
    """(edited code files, created source files, plans without the section) of the turn at a transcript's tail.

    None when the transcript cannot be read. Files are named by their last path part.
    An edit or a new file that an earlier message of the turn already reported with
    its line is not named again. A subagent's report or a task notification does
    not start a turn, so without this one report would be asked for again after
    every relayed message that follows it.
    """
    if not isinstance(path, str) or not path or len(path) > 4_096:
        return None
    edited, created, plans, written, created_ids = [], [], {}, set(), set()
    verified = reused = False  # A later message of the turn already carries the line.
    try:
        for raw in _lines(path):
            try:
                entry = json.loads(raw) if raw.strip() else None
            except ValueError:
                continue
            if not isinstance(entry, dict) or (entry.get("isSidechain") and not subagent):
                continue
            if entry.get("type") == "system" and entry.get("subtype") == "compact_boundary":
                break
            message = entry.get("message")
            content = message.get("content") if isinstance(message, dict) else None
            if entry.get("type") == "user":
                if _prompt(entry, content):
                    break
                for block in content if isinstance(content, list) else []:
                    if (isinstance(block, dict) and block.get("type") == "tool_result" and not block.get("is_error")
                            and _result_text(block).startswith(CREATED)):
                        created_ids.add(block.get("tool_use_id"))
                continue
            if entry.get("type") != "assistant" or not isinstance(content, list):
                continue
            # Newest first within the message too, so a later edit is seen before the write it follows.
            for block in reversed(content):
                if isinstance(block, dict) and block.get("type") == "text" and isinstance(block.get("text"), str):
                    verified = verified or bool(VERIFIED.search(block["text"][:MAX_TEXT]))
                    reused = reused or bool(REUSE.search(block["text"][:MAX_TEXT]))
                    continue
                if not isinstance(block, dict) or block.get("type") != "tool_use":
                    continue
                tool, data = block.get("name"), block.get("input")
                if not isinstance(data, dict):
                    continue
                if tool in SHELLS and isinstance(data.get("command"), str) and not verified:
                    edited.extend(reversed(_staged(data["command"])))
                if tool not in WRITES:
                    continue
                target = data.get("notebook_path" if tool == "NotebookEdit" else "file_path")
                if not isinstance(target, str) or not target or len(target) > 4_096:
                    continue
                name, kind, text = SEPARATOR.split(target)[-1], classify(target), _written(tool, data)
                if kind in CODE and not verified:
                    edited.append(name)
                if kind == "midturn-code-change" and tool == "Write" and block.get("id") in created_ids and not reused:
                    created.append(name)
                if PLAN.search(target) and target not in written:
                    if EXISTING.search(text):
                        written.add(target)  # This write or a later edit holds the section.
                    elif tool == "Write":
                        plans.setdefault(target, name)
                        written.add(target)
    except (OSError, ValueError):
        return None
    return _oldest_first(edited), _oldest_first(created), _oldest_first(list(plans.values()))


def stopped(event, rules=RULES, skills=None):
    """Continuation feedback on Stop or SubagentStop naming each report line this turn's changes call for, else {}."""
    name = event.get("hook_event_name")
    if name not in {"Stop", "SubagentStop"} or event.get("stop_hook_active"):
        return {}
    if name == "SubagentStop" and not event.get("agent_id"):
        return {}
    rows = [row for row in ROWS if row.rule in rules and (skills is None or row.skill in skills)]
    last = event.get("last_assistant_message")
    if not rows or not isinstance(last, str):
        return {}
    last = last[:MAX_TEXT]
    path = event.get("agent_transcript_path") if name == "SubagentStop" else event.get("transcript_path")
    scan = turn(path, subagent=name == "SubagentStop")
    if not scan:
        return {}
    edited, created, plans = scan
    shown = {"report-verification": ("edited", edited if not VERIFIED.search(last) else []),
             "report-reuse": ("created", created if not REUSE.search(last) else []),
             "plan-existing": ("wrote", plans)}
    lines = []
    for row in rows:
        verb, files = shown[row.rule]
        if files:
            lines.append(f"- {row.skill}: this turn {verb} {', '.join(files[:MAX_ITEMS])} and {row.missing}; the "
                         f"skill asks for {row.line}.")
    if not lines:
        return {}
    who = "this subagent" if name == "SubagentStop" else "this session"
    return {"hookSpecificOutput": {"hookEventName": name, "additionalContext": "\n".join([
        f"Assay report check: a line the skill below asks for after {who}'s changes is missing:", *lines,
        "Add only the missing lines, without repeating the answer; for a plan, add the section to the plan file. "
        "A line states what was done, so a check that did not run is a `Not verified` line."])}}
