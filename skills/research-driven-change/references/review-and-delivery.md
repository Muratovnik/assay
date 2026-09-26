# Review and delivery

Use when the active change receives feedback, verification becomes stale, or the
request includes a remote proposal. This method routes the next action and
accounts for delivery. [Independent audit](../../independent-audit/SKILL.md) owns
audit criteria and verdicts; [planning](../../implementation-planning/SKILL.md)
owns replanning and continuation. Neither a review finding nor this workflow gives
an auditor authority to repair the subject.

## Give review the actual contract

Supply the original requested outcome, current constraints and approved decisions,
exact subject/revision, in-scope changes and relevant check results. The executor's
summary and its green commands are evidence, not a replacement acceptance contract.
Respect the reviewer's read boundary and keep evaluator grading keys outside
executor inputs. Disclose self-review; a fresh context alone is not an independent
oracle. No additional reviewer, delegation or audit gate is mandatory for every
edit; use the review depth the request and its consequences justify.

Carry the audit's verdict and coverage limits as well as its findings. An empty
finding list with unexamined required areas is not a cleared review. Conversely,
a complete supported clean review does not need invented findings or another
approval ritual. The audit method owns that distinction; preserve it on return.

## Route feedback to its cause

Validate technical feedback against the subject and applicable criteria before
changing anything. Keep a supported finding separate from a preference, a question
or a proposed new requirement.

| Supported situation | Next responsible work |
| --- | --- |
| Implementation violates an agreed result | Bounded repair and affected checks under the implementation owner |
| A test can pass with the reported defect intact | [Test audit](../../test-audit/SKILL.md), then authorized [test writing](../../test-writing/SKILL.md) and necessary implementation repair |
| The plan omitted an agreed requirement | [Review and replan](../../implementation-planning/references/review-and-replan.md) for affected units |
| A source premise or compatibility assumption was refuted | Targeted [research](../../evidence-research/SKILL.md), decision review and affected replan |
| A reported defect is contradicted by the contract and evidence | Explain the counterevidence and retain valid behavior |
| Feedback proposes new scope | Record the proposal under the owner's contract-change process; do not silently absorb it |

A repeated complaint calls for recovery of the previous hypothesis and acceptance
check through
[continuation](../../implementation-planning/references/continuation.md#carry-a-goal-across-different-tasks).
It is not a fixed retry counter or permission for a broad rewrite. Preserve
unresolved alternatives when the cause is unknown. Stop the affected loop when no
new discriminating evidence or ready authorized action exists, or when its agreed
resource boundary is reached. Report the remainder instead of rephrasing the same
rule until a favorable verdict appears. A clean review is valid.

## Keep checks attached to the checked result

After a repair or incoming change, compare the current subject with the revision
and inputs each result checked. Refresh affected evidence; do not reuse an earlier
PASS across relevant drift. Unaffected evidence may remain valid with its scope
stated. File existence, a successful commit and a reviewer's assertion cannot stand
in for behavior checks. Distinguish changed, structurally checked, behaviorally
exercised and supported by a comparison.

For published work also distinguish local verification, hosted CI, review and
merge. Pending, failed and unavailable checks have different meanings. A local
pass does not establish hosted CI success, and an empty list of checks does not
establish that all required checks ran. Name unverified requirements explicitly.
For an integration result, retain the base and head or tested merge identity and
relevant configuration, not only the feature head. A changed base can invalidate
integration evidence even when the feature commit is unchanged; retain local
checks only for the inputs they actually covered.

## Publish only the requested proposal

For a requested pull request or equivalent proposal, inspect available owner tools
and effective permissions before declaring publication unavailable. Preserve
unrelated work. Establish the exact repository, base, head and current remote
state, including an existing proposal for that task. Reuse it when the request
continues that proposal; do not create a duplicate or update a neighboring branch.
Follow owner commit and publication rules rather than assuming a fixed Git client,
branch convention, model or hosted service.

Before updating a shared head, compare it with the revision the local candidate
was based on. Use the owner's conditional update or non-overwriting mechanism.
If another change arrived, preserve it, reconcile the affected work and checks,
and retry only from the reconciled state; do not force an old candidate over it.

Describe the need, significant decisions and source context, actual changes,
checks and limits in the proposal. Link larger authorized research instead of
copying it. Publish only relevant material; exclude secrets, private traces and
withheld grading keys. Test fixtures intentionally shipped as evaluator assets are
not withheld keys, but must still stay out of executor packets.

After creation or update, read back the remote proposal and compare its identity,
base/head and revision with the intended delivered candidate. Correct branch names
alone do not prove the checked bytes were delivered. If they differ, reconcile
before attributing local results to the remote state. A successful local commit or
an attempted API call is not a publication receipt. If the response was lost, use
[reconciliation before replay](../../implementation-planning/references/continuation.md#reconcile-before-continuing)
to observe whether the effect already happened. Do not retry an ambiguous remote
creation merely to obtain a cleaner receipt.

Read available CI/review state for the relevant revision when it bears on the
claim being delivered. Do not wait indefinitely or promise future monitoring. A
requested draft can be delivered with explicit outstanding checks. Conversely,
when a green or review-cleared proposal was requested, an unresolved check leaves
that endpoint open even if the PR exists. Creation does not authorize merging,
changing repository policy or releasing.

## Report the endpoint actually reached

State what exists, where and at which revision, what the applicable checks prove,
and which requested outcomes remain. When publication really is blocked, deliver
the authorized local result and explain the boundary. A branch, patch or archive
is a different result from a PR, never proof that a PR exists. Use a requested
fallback only after the relevant publication route has been tried or its concrete
permission/capability limit established. Do not abandon a working publication path
in favor of an easier archive. Do not reclassify unperformed work as deliberately
deferred without the owner's decision.
