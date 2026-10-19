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
# The routing checklist, including its failure branch, is added at session
# start only where routing is configured; otherwise it arrives before every
# launch, and the base reminder keeps pointing at the skill that owns it.
ROUTING_SESSION_REMINDER = (
    " Revisit newly ready "
    "dependencies and material verification; do not create token delegations. "
    "Before every authorized subagent launch, including replacements and "
    "reviewers, the root agent must apply route-subagents (possibly named "
    "assay:route-subagents). Reading it earlier is not a routing decision for a "
    "new packet. Select the child model and supported effort deliberately through "
    "its workflow, which weighs full-chain cost against quality using available "
    "evidence, and use the smallest sufficient context. Reuse valid plan evidence. "
    "Preserve explicit user choices. A failed routing request supplies no route; "
    "read routing-failure.md first."
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


def reminder(event: dict, environ=None) -> dict:
    name = event.get("hook_event_name")
    if name == "SessionStart" and event.get("source") in (
        "startup", "resume", "clear", "compact", "fork"
    ):
        routing = (os.environ if environ is None else environ).get("ASSAY_ROUTING_CONFIG")
        context = SESSION_REMINDER + (ROUTING_SESSION_REMINDER if routing else "")
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
