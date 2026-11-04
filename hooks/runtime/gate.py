"""Answer a Claude tool call that no hook check can answer or record, before the hook loads its checks.

The Claude hook runs before every tool call, and most of those calls are ones
no check reads: a search, an MCP tool, a shell command that neither fetches nor
reruns a scenario. For them the full path loads the rules, the routing modules
and the stores only to print an empty reply. `quiet` names those calls from the
event alone, with the predicates the checks themselves use, so the entry can
print that reply at once. Anything it cannot judge goes the full path: an error
here never answers a call.

It may send more calls the full path than needed; it must never answer one the
full path would answer or record. Codex events always take the full path.
"""
from __future__ import annotations

import json
import sys

from .predicates import LOADED_SKILL, QUESTION, SHELLS, WEB, WRITES, classify, external, reading_profile, signature

MAX_INPUT = 1024 * 1024
# The command lines of a Claude event run that argparse reads exactly as written here.
ENTRIES = (["--client", "claude"], ["event", "--client", "claude"])
# Calls a check reads whatever their input: a launch and its routing, the hand-back hold, a skill load,
# a fetch or search and a question to the owner.
FULL = frozenset({"Agent", "Task", "SubagentHandback", "Skill", QUESTION, *WEB})


def read(argv):
    """The hook input of a Claude event run, or None for any other run, which leaves standard input unread."""
    if list(argv) not in ENTRIES:
        return None
    try:
        return sys.stdin.buffer.read(MAX_INPUT + 1)
    except Exception:
        return None  # The full path reads it again and reports the failure.


def _pairs(items):
    out = {}
    for key, value in items:
        if key in out:
            raise ValueError("duplicate key")  # The full path refuses it, so it decides.
        out[key] = value
    return out


def _constant(value):
    raise ValueError("non-finite number")


def quiet(raw):
    """Whether the full path would answer this Claude event with {} and record nothing; False when unsure."""
    try:
        if not isinstance(raw, bytes) or len(raw) > MAX_INPUT:
            return False
        return _quiet(json.loads(raw.decode("utf-8"), object_pairs_hook=_pairs, parse_constant=_constant))
    except Exception:
        return False


def _quiet(event):
    if not isinstance(event, dict) or event.get("hook_event_name") != "PreToolUse":
        return False
    tool = event.get("tool_name")
    if not isinstance(tool, str):
        return False
    role = event.get("agent_type")
    if role is not None and (not isinstance(role, str) or reading_profile(role)):
        return False  # A reading role is held to its tools.
    if role is None and event.get("agent_id") is not None:
        return False  # A subagent's role is known only from the record its start left.
    if tool in FULL:
        return False
    data = event.get("tool_input")
    data = data if isinstance(data, dict) else {}
    if tool == "Read":
        path = data.get("file_path")
        return not (isinstance(path, str) and LOADED_SKILL.search(path))
    if tool in WRITES:
        return classify(data.get("notebook_path" if tool == "NotebookEdit" else "file_path")) is None
    if tool in SHELLS:
        command = data.get("command")
        return external(command) is None and signature(command) is None
    return True
