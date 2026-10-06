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

## Establish a necessary capability

Before choosing how to implement a change that introduces or relies on a
guarantee no existing check covers — untrusted input at a boundary, a persisted
state format or an external contract — establish which capability provides that
guarantee, whether an existing one already does, and what remains unprovided.
A fix inside a boundary that is already enforced and checked does not need this
step.

Start from the consumer: which inputs or states it must accept or reject and how
a correct result differs from a plausible imitation. Then find the existing owner
of that guarantee on the reachable path, such as a validator, schema, type,
migration guard or check, and confirm the path actually invokes it. A capability
present elsewhere in the project does not cover this path. Three outcomes are valid:

- an existing capability covers the guarantee: use it and add no competitor;
- it is missing and providing it is within the task's authority: provide it as
  part of the change, preferring a fitting existing mechanism;
- providing it exceeds the authority: deliver the authorized part and report the
  unprovided guarantee as an unverified remainder, not as an optional extra.

An improvement the requested result does not need stays a separate optional
proposal and widens nothing. Example: an import endpoint whose consumer must
reject malformed records has no validation on that path; the validator, existing
or new, belongs to the requested guarantee. Control: fixing an off-by-one error in
a date parser that existing tests already cover changes nothing at that boundary.

## Conditions the project should supply

Some conditions decide which choice is right but rarely appear in a request. Look
for them before a decision that depends on them; an absent condition is not a
license to substitute the usual value.

| Condition | Observable fact: extract it yourself | Owner decision: do not infer it |
| --- | --- | --- |
| Stage and horizon | Release tags, migrations, consumers in other packages | Expected lifetime; whether a prototype may be replaced |
| Criticality and risk | Deployment and data-handling configuration | Criticality, user base, acceptable risk and reversibility |
| Critical areas | Protected paths and required gates in configuration | Which areas need extra care |
| Dependencies | Installed versions, lock files, existing internal components | Dependency policy: licenses, bans, preferred components |
| Public contracts | Package exports, CLI flags, schemas, events | Which contracts external consumers rely on |
| Checks | Test locations, project gates, CI configuration | Required depth beyond the project's own gates |
| Extensions and research | Announced roadmap items in project documents | Expected extension directions; question type and known validity threats |

Extract an observable fact before asking about it. For a missing owner decision,
name the assumption in the result and continue safe work; ask only when the
assumption changes a choice that is costly to reverse. Keep each condition's
source and date or revision; name a stale condition stale instead of applying it
silently. The values belong in the project's own instructions; this method holds
no project values.

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
