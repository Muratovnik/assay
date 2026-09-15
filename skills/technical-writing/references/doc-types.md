# Document types and their completeness

Pick the type from the reader's situation, then apply that type's checklist and
no other. The common failure is demanding a quickstart from an explanation or a
narrative from a reference table.

**Qualification status.** No type has been exercised against a model yet.
README and how-to are the types this method was written for first and carry
most of its evaluation cases; the remaining checklists are conditional
material, backed by an authored control case only where the evaluation data
names one (reference, runbook, translation) and by none otherwise. Use them as
a completeness prompt, and say so if a reader asks what has been validated.

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

Never mix in the how-to's alternatives; a learner who must choose is stuck.

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

A runbook missing rollback or escalation is incomplete even if every step is
correct; those two sections are what make it safe to follow at 03:00.

## ADR and RFC

- Context and the constraints that bound the decision.
- Real alternatives, including the one that was almost chosen.
- The decision — or the proposal, if it is a proposal.
- Consequences, including the ones the team dislikes.
- Status, exactly as it stands.

**Never promote `Proposed` to `Accepted`.** Status is a record of what the
owners decided, not a formatting choice; the same goes for `Superseded` and
`Deprecated`. If a document reads as accepted but is labelled proposed, report
the contradiction and let the owner resolve it. Editing an ADR's history
sections is likewise out of bounds: they are a record, not draft text.

## Release notes and changelog

- Written from the actual diff between the two releases, not from the commit
  log and not from the plan.
- User-facing changes only: what someone using the product will notice.
  Internal refactors appear only when they change behaviour, performance or
  support.
- Compatibility first: breaking changes, removed options, changed defaults,
  required migration steps, each with what to do about it.
- Fixes described by the symptom the user saw, not by the internal cause.
- Versions and dates that match the release metadata.

When a generated changelog is the project's contract, do not hand-edit it;
improve the commit subjects that feed it.
