"""Emit bounded native hook context; never route, authorize or launch work."""
from __future__ import annotations

import json
import sys


SESSION_REMINDER = (
    "Assay is installed. Apply matching installed skills: read their SKILL.md "
    "and follow the applicable workflow; skip unrelated skills. Before every "
    "authorized subagent launch, including replacements and reviewers, the root "
    "agent must apply route-subagents (possibly named assay:route-subagents). "
    "Reading it earlier is not a routing decision for a new packet. Select the "
    "child model and supported effort deliberately, use the smallest sufficient "
    "context, and weigh full-chain cost against quality using available evidence. "
    "Reuse valid plan evidence. Preserve explicit user choices. This reminder "
    "does not authorize delegation; workers must not spawn further agents."
)
DELEGATION_REMINDER = (
    "Assay routing checkpoint: route-subagents is required for every authorized "
    "child launch, including replacements and reviewers. Apply its workflow to "
    "this packet: deliberate model and supported effort, bounded ownership and "
    "return contract, minimal context, cost and quality evidence. Inheriting the "
    "parent model or full history is a choice requiring justification. Reuse "
    "valid plan evidence; do not rerun an advisor for each spawn. Preserve user "
    "choices and delegation limits. Reading the skill alone is not routing."
)
MAX_INPUT_BYTES = 1024 * 1024


def reminder(event: dict) -> dict:
    name = event.get("hook_event_name")
    if name == "SessionStart" and event.get("source") in (
        "startup", "resume", "clear", "compact", "fork"
    ):
        context = SESSION_REMINDER
    elif name == "PreToolUse" and event.get("tool_name") in (
        "spawn_agent", "Agent", "Task"
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
