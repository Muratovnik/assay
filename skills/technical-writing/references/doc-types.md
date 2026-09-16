# Document types and their completeness

Pick the type from the reader's situation; use the relevant questions to design
the reading path. For composition use [document design](document-design.md). The common failure is demanding a quickstart from an explanation or a
narrative from a reference table.

A checklist supplies conditional questions, not required headings. Apply it to
what the request actually opens. Information can already be in a prerequisite,
linked reference or parent page. A local review does not inherit every item
from a full publication audit. Do not invent edge cases or procedures to fill
an empty slot. Evaluation status belongs in evaluator documentation, not a
claim that these checklists have been proven for every task.

For the distinction between the four classic types and the reader need behind
each, [Diataxis](https://diataxis.fr/) is the primary source. Take the
distinction, not a mandate to create four documents: a project with one useful
how-to does not need three empty siblings.

## How-to

The reader has a goal and some experience. They need to finish, not to learn.

- The goal, stated as the reader would state it.
- Preconditions: access, versions, state the procedure assumes.
- Numbered steps in the order they must run, each one action.
- The observable result after the final step.
- The errors that actually occur here, and what each one means.
- Where to go next, when the goal is part of something larger.

Out of scope: teaching the concepts, justifying the design, listing every
option. Link to the reference instead of inlining it.

## Tutorial

The reader is learning and may not know what success looks like.

- A controlled starting environment the reader can reproduce exactly.
- One path, with no branching choices to make.
- Checkpoints: what they should see after each stage.
- A small, real result at the end.
- Cleanup, when the tutorial created anything.

Prefer one guided path for a tutorial. Include a necessary platform branch
when the learner cannot complete the task without it; do not hide a real choice.

## Reference

The reader knows what they want and is looking it up.

- Every parameter, its type, its default, whether it is required.
- Constraints, limits, accepted values and units.
- Errors and the conditions that raise them.
- Version applicability, and what changed if it changed.
- Stable, repetitive structure — the same fields in the same order.

Repetition here is the feature. Do not vary the phrasing for elegance, and do
not force a quickstart onto a reference page.

## Explanation

The reader wants to understand why the system is the way it is.

- The problem and the constraints in force when it was solved.
- The mechanism, at the level the reader needs.
- Trade-offs actually accepted, and the options rejected with the reason.
- Boundaries: what this explanation does not cover.

No mandatory installation section, no step list. An explanation that cannot be
executed is not incomplete.

## Runbook

The reader is on call, under time pressure, possibly at night.

- **Symptoms and applicability** — how they know this runbook is the right one.
- **Access** — accounts, roles, hosts, credentials needed before starting, and
  who grants them.
- **Steps** — exact commands, with the environment each one runs against.
- **Verification** — how to confirm the system is healthy again, not merely
  that the command exited 0.
- **Rollback** — how to undo each risky step, and the point of no return.
- **Escalation** — who to wake, with what information, and when to stop trying.

Require recovery, stopping conditions and escalation where the operation's risk
makes them necessary. They need not be separate headings. For an irreversible
step, state the point of no return and the supported fallback; never invent an
undo command. A read-only diagnostic note may legitimately need no rollback.
Report a directly visible destructive step without necessary safeguards even
in a narrow review, but do not require every runbook to match one template.

## ADR and RFC

- Context and the constraints that bound the decision.
- Real alternatives, where they were actually considered; do not invent a runner-up.
- The decision — or the proposal, if it is a proposal.
- Consequences, including the ones the team dislikes.
- Status, exactly as it stands.

**Never promote `Proposed` to `Accepted`.** Status is a record of what the
owners decided, not a formatting choice; the same goes for `Superseded` and
`Deprecated`. If a document reads as accepted but is labelled proposed, report
the contradiction and let the owner resolve it. Editing an ADR's history
sections is likewise out of bounds: they are a record, not draft text.

## Release notes and changelog

- Written from the actual diff between the two releases, using the commit
  log and release record as supporting context, never treating the plan as shipped code.
- User-facing changes only: what someone using the product will notice.
  Internal refactors appear only when they change behaviour, performance or
  support.
- Compatibility first: breaking changes, removed options, changed defaults,
  required migration steps, each with what to do about it.
- Fixes described by the symptom the user saw, not by the internal cause.
- Versions and dates that match the release metadata.

When a generated changelog is the project's contract, do not hand-edit it;
use the approved correction workflow for its inputs. Do not rewrite published
commit history merely to improve phrasing.
