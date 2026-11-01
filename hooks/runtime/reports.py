"""Hold a Claude turn that changed code or wrote a plan to the report lines its skills ask for.

A hook cannot judge whether a check was the right one or whether something
already existed, but it can see that the line stating it is missing. Each row
pairs a sign in the turn's own tool calls with a line the final message or the
written plan must carry: a table row or a line labelled `Verified` or `Not
verified` after editing code, a `What already exists` section in a plan file.
Localized labels count.
There is no row for the reuse line: whether a reuse decision was taken is not
visible in the tool calls, and a `Reuse: not applicable` line written to satisfy
the check reports no decision. On Stop or SubagentStop the turn
continues once with one note naming each missing line. It is never a block, runs
no model and stores nothing. A write made through a shell command is seen only
when the turn stages the file with `git add`. While a background launch of the
main session's turn still runs, the verification line is not asked for yet.
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
    Row("report-verification", "code-change", "the final message has no verification report",
        "a table `Status | Check | Result` with a `Verified` row per material check, labels in the reply's language"),
    Row("plan-existing", "implementation-planning", "the plan has no section on what already exists",
        "a `What already exists` section: capabilities and solutions considered, where they were looked for, why "
        "each fits or not"),
)
RULES = tuple(row.rule for row in ROWS)

MAX_TEXT = 65_536
MAX_ITEMS = 3
# A label at the start of a line, optionally in a list item or bold.
LABEL = r"^[ \t]*(?:[-*+][ \t]+)?(?:\*\*|__)?(?:{})(?:\*\*|__)?[ \t]*:"
# The same label as the first cell of a table row.
CELL = r"^[ \t]*\|[ \t]*(?:\*\*|__)?(?:{})(?:\*\*|__)?[ \t]*\|"
STATUS = r"not[ \t]+verified|verified|не[ \t]+проверено|проверено"
VERIFIED = re.compile(LABEL.format(STATUS) + "|" + CELL.format(STATUS), re.I | re.M)
EXISTING = re.compile(r"^[ \t]*#{1,6}[ \t]+(?:\d+[.)][ \t]*)?(?:what already exists|что уже есть)\b", re.I | re.M)
# A file that holds behavior: source, a test or an interface.
CODE = frozenset({"midturn-code-change", "midturn-test-writing", "midturn-ui-delivery"})
# What the client answers when a launched command or agent keeps running after the call returns.
BACKGROUND = re.compile(r"(?:Command running in background with ID: |Async agent launched successfully)")
LAUNCH_ID = re.compile(r"(?:with ID: |agentId: )([\w-]+)")
NOTIFICATION = "<task-notification"
# The names a notification gives its task.
NOTIFIED = re.compile(r"<(?:task-id|tool-use-id)>([^<\s]+)</")
MAX_NOTIFICATION = 4_096
# The paths of `git add`, up to the end of that command.
GIT_ADD = re.compile(r"\bgit(?:\s+-C\s+\S+)?\s+add\s+([^;&|\n]+)")


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


def _relayed(content):
    """Whether a prompt entry is a background task's notification and not the owner's message."""
    return isinstance(content, str) and content.lstrip().startswith(NOTIFICATION)


def _entries(path, subagent):
    """A transcript's entries newest first, back to the turn's prompt or the latest compaction."""
    entries = []
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
        if entry.get("type") == "user" and _prompt(entry, content) and (subagent or not _relayed(content)):
            break
        entries.append(entry)
    return entries


def _background(entries):
    """(index of the oldest background launch or -1, whether one still runs) over a turn's entries, newest first."""
    notified, failed, launches, oldest = set(), set(), {}, -1
    for index, entry in enumerate(entries):
        message = entry.get("message")
        content = message.get("content") if isinstance(message, dict) else None
        attachment = entry.get("attachment")
        queued = attachment.get("prompt") if isinstance(attachment, dict) and attachment.get("type") == "queued_command" else None
        for text in (content, queued):
            if isinstance(text, str) and NOTIFICATION in text[:MAX_NOTIFICATION]:
                notified.update(NOTIFIED.findall(text[:MAX_NOTIFICATION]))
        for block in content if isinstance(content, list) else []:
            if not isinstance(block, dict):
                continue
            if block.get("type") == "tool_result":
                ident = block.get("tool_use_id")
                if block.get("is_error"):
                    failed.add(ident)
                    continue
                result = block.get("content")
                if isinstance(result, list):
                    result = " ".join(part.get("text", "") for part in result if isinstance(part, dict))
                if isinstance(result, str) and BACKGROUND.match(result):
                    launches.setdefault(ident, {ident}).update(LAUNCH_ID.findall(result[:MAX_NOTIFICATION]))
                    oldest = index
            elif block.get("type") == "tool_use" and block.get("id") not in failed:
                data = block.get("input")
                if isinstance(data, dict) and data.get("run_in_background") is True:
                    launches.setdefault(block.get("id"), {block.get("id")})
                    oldest = index
    return oldest, any(not names & notified for names in launches.values())


def turn(path, *, subagent=False):
    """(edited code files, plans without the section, whether a background launch still runs) of the turn at a tail.

    None when the transcript cannot be read. Files are named by their last path part.
    An edit that an earlier message of the turn already reported with its line is
    not named again. A subagent's report or a queued notification does not start
    a turn, so without this one report would be asked for again after every relayed
    message that follows it. A notification delivered as a prompt starts one, unless
    a background launch of this turn comes before it: a stop made to wait for that
    launch asked for nothing, so the edits before the notification are still due.
    """
    if not isinstance(path, str) or not path or len(path) > 4_096:
        return None
    edited, plans, written = [], {}, set()
    verified = False  # A later message of the turn already carries the line.
    try:
        entries = _entries(path, subagent)
        oldest, running = _background(entries)
        for index, entry in enumerate(entries):
            message = entry.get("message")
            content = message.get("content") if isinstance(message, dict) else None
            if entry.get("type") == "user":
                if _prompt(entry, content) and index >= oldest:
                    break
                continue
            if entry.get("type") != "assistant" or not isinstance(content, list):
                continue
            # Newest first within the message too, so a later edit is seen before the write it follows.
            for block in reversed(content):
                if isinstance(block, dict) and block.get("type") == "text" and isinstance(block.get("text"), str):
                    verified = verified or bool(VERIFIED.search(block["text"][:MAX_TEXT]))
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
                if PLAN.search(target) and target not in written:
                    if EXISTING.search(text):
                        written.add(target)  # This write or a later edit holds the section.
                    elif tool == "Write":
                        plans.setdefault(target, name)
                        written.add(target)
    except (OSError, ValueError):
        return None
    return _oldest_first(edited), _oldest_first(list(plans.values())), running


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
    edited, plans, running = scan
    # A stop to wait for a background task is not the final message; a subagent that stops has finished.
    waiting = running and name == "Stop"
    shown = {"report-verification": ("edited", edited if not (waiting or VERIFIED.search(last)) else []),
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
        f"Assay report check: something the skill below asks for after {who}'s changes is missing:", *lines,
        "Add only what is missing, without repeating the answer; for a plan, add the section to the plan file. "
        "A report states what was done: when no check ran, a `Not verified` row says so instead, with the reason."])}}
