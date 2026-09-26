---
name: code-change
description: Implement or refactor code with clear responsibilities, controlled state and effective quality checks. Use for changes affecting code structure, shared logic or tooling; skip prose-only edits and read-only audits.
license: MIT
metadata:
  assay-optional-skills: "evidence-research implementation-planning independent-audit software-architecture test-writing ui-delivery"
---

# Code change

Make the requested change easier to understand and safely change again. Assess
the resulting code and its consumers, not just the patch size or green commands.

## Establish the working contract

Read the request, owner instructions, affected callers and effective project
configuration. Separate required behavior, adopted conventions and proposed
improvements. Apply an agreed convention within its actual scope; do not turn
a later preference into a historical violation. Existing inconsistency is
evidence to investigate, not permission to choose whichever style is convenient.

Retain supported behavior during refactoring, including exports, input shapes,
side effects, errors and lifecycle. Name intentional behavior changes separately.
Use existing project boundaries and primitives. A small repair does not authorize
unrelated cleanup, dependency replacement, shared-package extraction or policy
changes. Complete necessary in-scope repairs without inventing approval gates.

For an explicit plan or consequential sequencing, dependencies or handoff, use
available [implementation-planning](../implementation-planning/SKILL.md) with the
scope, inspected consumers, shared contracts and required checks established here.
Planning sequences the work; boundary decisions follow the next section, and a
plan-only request grants no implementation authority.

## Responsibilities and interfaces

For material decisions about ownership, contracts, dependency direction or file
placement, use [software architecture](../software-architecture/SKILL.md). It owns
the shared boundary criteria; this method owns implementing the authorized change
and checking its callers. A request for an architecture proposal belongs directly
to that method and does not authorize implementation.

Apply the resulting owner/contract/placement decisions to code and consumers
together. For an already justified local repair, preserve its established boundary
without launching system-wide design. If the architecture method is unavailable,
keep the existing contract and report any material design gap; do not silently
install it or invent a replacement policy.

## State and effects

Give mutable state an identifiable owner, lifetime and mutation interface. Keep
derived values derived when recomputation is appropriate; avoid independently
writable copies requiring callers to remember synchronization. A cache or editable
draft is valid when its invalidation or reconciliation contract is explicit.

Keep effects, subscriptions and cleanup with the operation or lifecycle that owns
them. Make initialization, reset, failure and disposal understandable. Shared
mutable module state needs intentional shared semantics; scenario-local mutation
is not a defect. Prefer explicit transitions over chained assignments when those
assignments hide distinct state owners or couple future changes.

## Use only the relevant detail

- When a repair needs causal diagnosis or a persistent reproducer, use
  [diagnostic reproducers](references/diagnostic-reproducer.md). An already
  justified narrow fix does not require a new debugging campaign.
- Before a material decision to add, retain or change reusable behavior or
  standard visual states, or deliver a staged adoption, read
  [reuse and migration scope](references/reuse-and-migration.md). A dependency or
  shared location does not establish delegation or completion of the outcome.
- For TypeScript/Vue style choices, read the
  [conventions profile](references/typescript-vue-conventions.md). Its adoption
  boundary matters; it is not a universal language standard.
- For Vue components, reactive state or composables, read
  [Vue structure](references/vue-structure.md).
- For quality-tool changes, relocated files, or claims that checks enforce a
  rule, read [effective quality checks](references/effective-quality-checks.md).
- For test changes, use [test-writing](../test-writing/SKILL.md), including its
  fixture and suite maintenance procedure. For consequential package/platform
  choices, use [evidence-research](../evidence-research/SKILL.md).

These are the corresponding methods, not additional assignments. A requested
audit uses [independent-audit](../independent-audit/SKILL.md) with these criteria;
this implementation skill neither grants repair authority to an auditor nor
requires an audit or delegation for every edit.

## Inspect the final structure

Read the resulting affected units with their important callers and tests.
Reconsider accumulated responsibilities even when today's diff is small, and judge
each new or changed boundary by the architecture method's
[extraction criteria](../software-architecture/references/file-placement.md#evaluate-both-sides-of-extraction);
moving CSS or renaming a helper does not itself improve maintainability. Check that
state ownership is clearer, avoid speculative extensibility and keep cleanup
proportional to the actual burden within scope.

Run relevant owner checks and verify behavior at affected boundaries. For test
design use the test method above; do not equate a file move with unchanged check
coverage. Report the concrete responsibility/guarantee improved and evidence or
remaining gaps. No mandatory new architecture document or metric target.

The `evals/` cases and rubrics are evaluation data, not runtime instructions;
do not read them while performing a user's implementation task.
