# Scope and readiness

Use when the goal, constraints, repository facts or an unknown could change the
plan. Scale reconnaissance to that decision; no whole-project inventory by default.

## Recover the actual contract

Identify the consumer outcome, required behavior, non-goals, adopted decisions,
authority and acceptance source. A suggested mechanism is not necessarily the
underlying need. Reuse supplied context and resolve questions from available
project evidence before asking the user. Ask only for a consequential choice
that cannot be resolved; continue independent safe work where possible.

For an existing project, inspect its instructions, relevant implementation,
important callers, configuration and checks. Label paths as verified existing,
proposed new or not yet inspected. Search results alone do not establish runtime
use. For a new project, describe intended boundaries without pretending they exist.
When access is missing, deliver a bounded provisional plan with a discovery step,
not invented files, line numbers, interfaces or test commands.

Keep an explicit requirement distinct from a preference, an assumption and a
possible improvement. Carry exact version, compatibility, data and environment
constraints into affected units. Incidental debt goes outside the active scope;
necessary enabling work needs a clear connection to the requested result.

## Check material changes to the contract

Keep the desired outcome, chosen means, continuing constraints and authority of
this task distinct. For a decision that changes acceptance, retain its source,
date/scope, what it preserves or changes, and the basis for the decision in the
existing plan or decision record. An author's `accepted` label or notification
of an owner is not evidence that a reduced outcome was authorized. Direct owner
instruction, delegated competence or the project's accepted review process can
supply that basis; do not demand a fresh approval for each delegated detail.

Read accessible source decisions before resolving a consequential conflict.
Agreement among a specification, plan and task list can repeat the same mistaken
interpretation. Compare their material changes with the source, not just each
other. Apply an older preference only to its actual family, stage and period;
a newer requirement does not retroactively make prior permitted work defective.
Distinguish supported authority, contradicted authority and unavailable evidence.
An incomplete historical record alone proves neither consent nor a violation.
Keep unresolved material choices visible and continue independent authorized work.

A surviving product goal is not perpetual execution permission. A current narrow
review or faithful transfer can leave a broader goal unfinished without authorizing
its implementation. Preserve that remainder and its continuation condition rather
than dropping it or silently expanding the current assignment. No extra tracker,
mandatory approval field or fixed document schema is required.

## Classify unknowns by the next decision

| Unknown | Treatment |
| --- | --- |
| Answer available in the project, documentation or accepted decisions | Resolve the consequential fact before depending on it. Reuse sufficient verified evidence. |
| Answer needs an experiment or integration | Plan a bounded probe with the question, allowed effects, discriminating observation, cleanup/recovery and next decision. |
| Answer belongs to an external owner or unavailable system | Name the dependency, owner or explicitly unassigned status, needed answer and continuation condition. Do not invent a policy or date. |

For each material unknown record what it could change and which work is safe
before it is answered. A local helper name rarely blocks a milestone. An unknown
compatibility guarantee can block retiring the old implementation. Use working
assumptions only when the consequences are bounded and the disconfirmation path
is explicit; do not label an assumption as an approved decision.

An investigation unit can be ready even when later implementation is conditional.
Do not demand resolution of every future detail, and do not hide a blocker in an
unqualified 'ready' verdict. A unit is ready when its prerequisite decisions,
inputs and authority are sufficient for its next action, and it has a meaningful
completion check. This is a decision criterion, not an obligatory status machine.

## Example: missing retry contract

The user requests a retryable import. Reading existing request/response handling
can establish the present behavior. Whether a timed-out import already committed
may need an integration probe; the plan must not assume that retry is harmless.
A server-side deduplication policy might belong to another owner. Plan the
read-only investigation now, identify that decision, and keep unrelated UI work
ready if it does not depend on the answer. Do not replace the request with a
new backend architecture merely because one possible solution uses it.
