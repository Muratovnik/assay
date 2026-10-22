"""Emit bounded native hook context; never route, authorize or launch work."""
from __future__ import annotations

import json
import os
import sys


FAILURE_REMINDER = (
    " If routing is rejected or unavailable, read route-subagents/references/"
    "routing-failure.md before any child launch. A refusal supplies no advice: "
    "do not launch with unresolved model or effort, or inherit maximum settings "
    "as a fallback. Respect the rejected operation; keep unaffected work local "
    "unless a deliberate supported selection passes the local launch preflight."
)
SESSION_REMINDER = (
    "Assay is installed. Apply matching installed skills: read their SKILL.md "
    "and follow the applicable workflow, skip unrelated skills, and when the user "
    "requests subagents use route-subagents before substantial solo work to choose "
    "useful outcomes and launch timing. This reminder does not authorize "
    "delegation; workers must not spawn further agents."
)
# The planning step stays in every session: the request hint recognizes only
# narrow imperatives, and the launch reminder arrives after solo work started.
# The routing checklist is added at session start only where routing is
# configured, through ASSAY_ROUTING_CONFIG or the plugin's routing binding;
# otherwise it arrives before every launch, and the base reminder keeps
# pointing at the skill that owns it.
ROUTING_SESSION_REMINDER = (
    " Before every authorized subagent launch, including replacements and "
    "reviewers, apply route-subagents (possibly named assay:route-subagents). "
    "Start the launch's description with a task class from the route table, "
    "as in `<class>: <task>`, and pass exactly that class's model and effort; "
    "choose the class that fits the work, the less demanding one when two fit. "
    "The table is shown by routing_status and listed in a refusal, which says "
    "what to correct; if routing itself is rejected or unavailable, read "
    "route-subagents/references/routing-failure.md before any launch. "
    "Revisit newly ready dependencies and material verification before launching."
)
# Added after the checklist when the configuration routing resolved to cannot be
# used: its launches are refused, so the session should know before the first one.
ROUTING_PROBLEM = (
    " The routing configuration is refused and every launch it covers is blocked until it is fixed: "
)
DELEGATION_REMINDER = (
    "Assay routing checkpoint: route-subagents is required for every authorized "
    "child launch, including replacements and reviewers. Apply its workflow to "
    "this packet: deliberate model and supported effort, bounded ownership and "
    "return contract, minimal context, cost and quality evidence. Inheriting the "
    "parent model or full history is a choice requiring justification. Reuse "
    "valid plan evidence. Preserve user choices and delegation limits. "
    "Reading the skill alone is not routing."
) + FAILURE_REMINDER
MAX_INPUT_BYTES = 1024 * 1024


def reminder(event: dict, environ=None, *, routing: bool | None = None, problem: str | None = None) -> dict:
    """The reminder for one event.

    `routing` is the hook handler's own resolution of the routing configuration
    (variable or plugin binding) and `problem` says why it cannot be used. Left
    out, as in this script's standalone run, only ASSAY_ROUTING_CONFIG counts.
    """
    name = event.get("hook_event_name")
    if name == "SessionStart" and event.get("source") in (
        "startup", "resume", "clear", "compact", "fork"
    ):
        if routing is None:
            routing = bool((os.environ if environ is None else environ).get("ASSAY_ROUTING_CONFIG"))
        context = SESSION_REMINDER + (ROUTING_SESSION_REMINDER if routing else "")
        if routing and problem:
            context += ROUTING_PROBLEM + problem.rstrip(".") + "."
    elif name == "PreToolUse" and event.get("tool_name") in (
        "spawn_agent", "collaborationspawn_agent", "Agent", "Task"
    ):
        context = DELEGATION_REMINDER
    else:
        return {}
    return {"hookSpecificOutput": {
        "hookEventName": name,
        "additionalContext": context,
    }}


def main() -> int:
    try:
        raw = sys.stdin.buffer.read(MAX_INPUT_BYTES + 1)
        if len(raw) > MAX_INPUT_BYTES:
            raise ValueError("input too large")
        event = json.loads(raw)
        if not isinstance(event, dict):
            raise ValueError("expected object")
    except (ValueError, UnicodeError, RecursionError):
        # Exit 1 reports a non-blocking hook error; never use blocking exit 2.
        print("Assay reminder: invalid or oversized event JSON.", file=sys.stderr)
        return 1
    print(json.dumps(reminder(event)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
