---
name: operations-ui-delivery
description: Design, repair or review operational UI, or explicitly critique generic visual design. Covers user actions, shared states and visual clarity; skip backend-only work.
license: MIT
---

# Operations UI delivery

Make the next action apparent and its effect predictable. Preserve the product's
language, supported journeys and authoritative state.

## Scope and mode

- Review/audit: inspect the scoped experience and report findings; keep it unchanged.
- Repair: fix the smallest responsible owner and preserve nearby valid behavior.
- Design/build: implement the requested experience; choose reversible details
  without inventing a prior defect or requesting approval for each control.

Honor explicit proposal/approval boundaries. Otherwise complete authorized work;
ask only about consequential unresolved scope, shared effects or feature retirement.
An API capability is not a product-policy decision; an already agreed policy
does not need approval again.

- This automatic skill does not authorize delegation. Use an independent
  reviewer only when the user or an explicitly invoked delegating workflow has
  already authorized subagents. Otherwise keep the review in the primary task
  and do not describe it as independent.

Use owner instructions and existing primitives. Material dependencies need a
concrete gap and proportionate comparison. This skill grants no unrelated backend,
data, installation, hook or client-configuration changes.

## Select a thematic procedure

Read the applicable procedure before its decision. Start with the row matching
the task; add another only for a dependency actually affected. These are internal
procedures executed in this task, not separate agents or new native skill entries.
Reuse sections already read. Links name conditional dependencies, not a reading
chain; do not load the whole directory or evaluation corpus.

| Task or decision | Procedure |
| --- | --- |
| Adding/changing primitive mechanics or adopting a UI library in stages | [Reuse and migration scope](../code-maintenance/references/reuse-and-migration.md) |
| Action placement, draft departure, local/shared effects | [Actions and scope](references/actions-and-scope.md) |
| Forms, validation, typing/paste/autofill, submission | [Forms and input](references/forms-and-input.md) |
| Nested, filtered or bulk selection, counts/order | [Selection](references/selection.md) |
| Hit areas, gestures, popup geometry, modality | [Interaction](references/interaction-and-layout.md) |
| Animation, reveal, collapse, continuity | [Motion](references/motion-and-transitions.md) |
| Tables/grids, composite keyboard behavior, assistive access | [Accessibility and composites](references/accessibility-and-composites.md) |
| Shared screens, navigation state, panels, supported environments | [Workspace](references/workspace-consistency.md) |
| Computed results, async refresh, writes/retries, invalidation | [Data lifecycle](references/data-lifecycle.md) |
| Labels, status meanings, recovery guidance | [Content](references/content-and-recovery.md) |
| Acceptance/regression checks, interaction under realistic load | [Acceptance](references/scenario-testing.md) |
| Visual composition, critique or generic presentation | [Visual judgment](references/visual-judgment.md) |

When implementation changes component responsibilities, shared code or reactive
ownership, use [code-maintenance](../code-maintenance/SKILL.md) for those decisions,
including its conditional Vue procedure. For read-only review, use the applicable
criteria through [code quality verification](../independent-audit/references/code-quality.md)
without changing this task's authority. UI journey rules remain in the procedures above.

## Common execution and finish

1. Establish the outcome, starting state and actual entry path from the brief.
   Before attributing live behavior, identify source/build, runtime and data.
2. Trace affected owners to consumers. Classify missing shared rules, bypassed
   primitives, flow mismatches or local defects. Repeated complaints require
   revisiting that cause and omitted paths, not another isolated patch.
3. Apply the selected procedure and its distinguishing check plus valid control.
   Scale content to the risk; a small repair need not inventory the whole product.
4. Repeat the real action across affected paths, preserving input and save/cancel.
   Reuse matching gate/hook evidence, run missing and owner-required checks. Ask
   whether a check could pass while the complaint remains true. Observe the risky
   state before helpers repair it. For test design, use Acceptance above.

When visual quality matters, use Visual judgment for the composed screen, inspect
the rendered candidate and show a useful preview. A preview does not suspend
authorized work; wait only for an explicit checkpoint or a consequential
unresolved preference. Distinguish supplied facts,
observations, inference and gaps; missing access is not proof that no check ran.

For a cross-screen milestone, run a separate contrarian pass on the exact tested
artifact and challenge at least one stale, failed or recovery state. When
delegation is already authorized, the primary may assign that pass to an
independent reviewer; otherwise the primary runs it directly.

Report the operator outcome, relevant criterion → evidence or gap, actual automated
and visual checks, unresolved risks and owned runtime cleanup. A clean detector,
skill read or existing test is not evidence of a working journey; user approval
is separate from verification. Keep reporting in the existing task, without a
mandatory new document. When revising this skill, use
[evaluation guidance](evals/evaluation.md); it is not part of ordinary UI work.
