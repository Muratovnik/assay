---
name: code-maintenance
description: Implement or refactor code with clear responsibilities, controlled state and effective quality checks. Use for changes affecting code structure, shared logic or tooling; skip prose-only edits and read-only audits.
license: MIT
---

# Code maintenance

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
Code-boundary decisions stay with this method; a plan-only request grants no
implementation authority.

## Responsibilities and interfaces

Group code by the decision or operation it owns and the reasons it changes.
Keep orchestration, domain rules and presentation distinguishable where their
consumers or lifecycles differ. File count and architectural labels do not
establish separation: follow the actual imports, calls and knowledge exchanged.

Extract when the new boundary hides meaningful complexity, isolates a lifecycle
or gives a consumer a coherent operation. Judge the resulting interface and its
callers together. A forwarding wrapper can be useful for compatibility, policy
or a replaceable boundary; it needs no arbitrary minimum size or second adapter.
An extraction that merely spreads the same decisions across files has not
reduced complexity. Remove unnecessary indirection when doing so serves the task.

Prefer the narrowest real owner. Local helpers may stay beside their consumer;
cross-project source needs demonstrated common semantics and compatible lifecycle,
not merely similar syntax. Product rules, import boundaries and release/runtime
contracts remain with the owning project. A lower-layer import is not wrong
without an actual dependency rule or harmful coupling.

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
- Before adding or materially changing a reusable mechanism, or delivering a
  staged adoption, read [reuse and migration scope](references/reuse-and-migration.md).
  Existing names and dependencies do not establish who performs the behavior.
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
Reconsider accumulated responsibilities even when today's diff is small. Size
is a signal to inspect coherence, not a universal line cap. Splitting by line
count, moving CSS or renaming a helper does not itself improve maintainability;
an enforced project cap still applies until the owner changes it.

Check whether a likely next change is localized, state ownership is clearer and
the new interface removes knowledge from callers. Preserve a cohesive large unit
when splitting adds coordination without benefit. Avoid speculative extensibility
and keep cleanup proportional to the actual burden within scope.

Run relevant owner checks and verify behavior at affected boundaries. For test
design use the test method above; do not equate a file move with unchanged check
coverage. Report the concrete responsibility/guarantee improved and evidence or
remaining gaps. No mandatory new architecture document or metric target.

The `evals/` cases and rubrics are evaluation data, not runtime instructions;
do not read them while performing a user's implementation task.
