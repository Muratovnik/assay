---
name: retrospective
description: Review a period of agent work for recurring friction, reconcile it with the rules already in force and propose evidence-backed, owner-routed changes for the user to decide. Use on an explicit retrospective, reflection or lessons-review request, including a review of stored memory; skip single-incident debugging, diagnosing one skill's behavior, usage statistics and routine note-taking.
license: MIT
metadata:
  assay-optional-skills: "evidence-research implementation-planning skill-evaluation"
---

# Retrospective

Turn a bounded period of work into decisions the user can accept or reject, each
tied to records of what actually happened. This is a review method, not a store,
scheduler, hook or memory service. It changes nothing until the user decides.

## Frame the review

Run only on an explicit request. Establish the period, the projects or scope, the
evidence sources the user permits and a reading budget. Locate the previous
retrospective's decisions if the owner keeps them, usually in their planning item
or the record they name. State what is out of scope rather than silently sampling
it away. A review the user scopes to stored memory or lessons uses
[memory retrospective](references/memory-retrospective.md).

## Gather external evidence

Build candidates from signals outside the model's own reasoning: user
corrections and redirects, abandoned approaches, tool, hook and check failures,
permission refusals, reopened or reverted work. Re-reading your own earlier
answers and finding them weak is not evidence; without an external signal, there
is no finding.

Read each source by [evidence sources](references/evidence-sources.md): confirm
the scope key returns known records, aggregate before sampling, and keep a list of
what was read, sampled and not read. An empty result is a scope or access
question before it is an absence of problems.

## Form candidates

Classify signals by [friction signals](references/friction-signals.md). Count one
incident once, however many messages repeat it. A **pattern** needs the same
friction in at least two independent sessions or tasks; three or more is a strong
pattern. A severe incident seen once is reported as an **incident**: show it, do
not promote it into a rule. Each candidate cites its records — session, message
time, commit, task or memory entry — and separates the observation, its
interpretation and a cause hypothesis.

## Reconcile with what is already in force

Before proposing anything, search the owner's instructions, skills, checks,
hooks and stored lessons for a norm that already covers the candidate. Decide one
of:

- **absent** — no norm covers it; a new rule or check may be proposed;
- **not applied** — the norm exists but was not loaded, was loaded and not
  followed, or a check let the failure through; propose repairing that route or
  check, not a reworded copy of the rule. A skill's own failure goes to
  [skill-evaluation](../skill-evaluation/SKILL.md);
- **conflicting** — two norms disagree; propose resolving the conflict;
- **covered and working** — record the evidence that it holds.

A paraphrase of an existing rule does not fix an execution failure. Without a
trace of what was loaded and applied, the layer stays `unknown`.

## Propose and let the user decide

Write proposals by [proposals and tracking](references/proposals-and-tracking.md):
evidence, layer, destination chosen by the owner's own routing instructions, the
exact change and how to undo it. Present them for a decision per item — accept,
defer or reject. Apply an accepted item only through the owner's normal tools and
gates, one item at a time; a rejected or deferred item changes nothing. Record the
decisions where the owner keeps planning records so the next review can check
them. Save only confirmed lessons to memory, never raw signals.

Check the previous retrospective's accepted items: **resolved** when the friction
stopped in the new evidence, **recurring** when it returned, **unknown** when the
evidence cannot tell.

## Deliver

Report, in this order: scope and sources actually read, sampled and skipped;
patterns; single incidents; candidates already covered; proposals for decision;
status of earlier proposals; limits and open hypotheses. Use pointers to records
instead of copying transcripts; quote only the minimum a decision needs, and
treat personal and client data as the owner's data rules require.

This method grants no write, delegation, settings, installation or publication
authority, and it never enables data collection. Plans and recommendations it
produces are proposals until the user accepts them. For a substantial comparison
of external practice, use available [evidence-research](../evidence-research/SKILL.md);
for sequencing accepted changes, use [implementation-planning](../implementation-planning/SKILL.md).

`evals/` holds evaluation data for maintainers; never read it while performing a
user's retrospective.
