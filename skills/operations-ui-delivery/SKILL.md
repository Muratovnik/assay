---
name: operations-ui-delivery
description: Design, build, transfer, edit or review UI and its design artifacts, from operational screens to mockups, component libraries and their code. Covers user actions, shared states, reusable components, editability and visual clarity in any layout mode; skip backend-only work, tool installation and illustration without UI.
license: MIT
---

# Operations UI delivery

Make the next action apparent and its effect predictable, and make the artifact
that promises it hold up: a screen, mockup, component library or its code that
stays accurate, complete, editable and consistent after the last write.
Preserve the product's language, supported journeys and authoritative state.

## Scope and mode

The mode sets what establishes quality and which check applies:

| Mode | Quality source and distinguishing check |
| --- | --- |
| Review/audit | Apply the same criteria to the available evidence; keep the artifact unchanged and mark missing evidence as unverified. |
| Repair / local edit | The changed contract, its dependencies and affected consumers; a shared base widens the check to its uses. |
| New design / redesign | The user's task, product constraints and agreed system; check composition, required states and adaptation. Do not demand similarity to the old screen when change is allowed. |
| Implementation in code | The reference and the behavior contract; check real components, semantics, actions and render in the application. A static capture does not prove interaction. |
| Transfer | The given source and allowed delta; check preserved essential look, behavior and required editability. Do not hide a redesign inside a fidelity claim. |
| Sketch / raster mockup | Meaning, composition and required states at the ordered fidelity. Do not demand instances, a working DOM or a finished library from a picture. |

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
data, installation, hook or client-configuration changes, no writes during a
review-only request and no expansion of product scope.

## Common contract

Establish the user's task, the kind of result, the authoritative source for
each decision and the allowed changes before building or judging. Then hold
four invariants, each owned by one procedure:

- Required states come from the brief, scenarios and source behavior, not from
  the variants that exist: [Workspace](references/workspace-consistency.md).
- A shared base is traced to its real consumers, inward and outward; a master or
  an import does not prove use: [Component system](references/component-system.md).
- Editability is an observable effect; a declared property proves nothing until
  a changed value reaches its receiver: [Component system](references/component-system.md).
- Geometry, theme and composition are judged at the affected depth after the
  last write: [Visual judgment](references/visual-judgment.md).

Report verified, defective, unverified and inapplicable separately, tied to the
exact artifact; clean Git, a green build or a partial audit do not vouch for
the rest: [Acceptance](references/scenario-testing.md).

## Select a thematic procedure

Read the applicable procedure before its decision. Start with the row matching
the task; add another only for a dependency actually affected. These are internal
procedures executed in this task, not separate agents or new native skill entries.
Reuse sections already read. Links name conditional dependencies, not a reading
chain; do not load the whole directory or evaluation corpus.

| Task or decision | Procedure |
| --- | --- |
| Shared base, families, nested reuse, property effect, design-to-code mapping | [Component system](references/component-system.md) |
| Design-system/library information architecture, consumer-facing resources, internal/example/lifecycle separation | [Design-system organization](references/design-system-organization.md) |
| Adding/retaining primitive mechanics or standard visual states; staged library adoption | [Reuse and migration scope](../code-maintenance/references/reuse-and-migration.md) |
| Action placement, draft departure, local/shared effects | [Actions and scope](references/actions-and-scope.md) |
| Forms, field composition, validation, typing/paste/autofill, submission | [Forms and input](references/forms-and-input.md) |
| Nested, filtered or bulk selection, counts/order, control classification | [Selection](references/selection.md) |
| Hit areas, gestures, popup geometry, modality, coexisting states | [Interaction](references/interaction-and-layout.md) |
| Animation, reveal, collapse, continuity, ordered transitions | [Motion](references/motion-and-transitions.md) |
| Tables/grids, composite keyboard behavior, assistive access | [Accessibility and composites](references/accessibility-and-composites.md) |
| Shared screens, navigation state, panels, size owners, supported environments | [Workspace](references/workspace-consistency.md) |
| Computed results, async refresh, writes/retries, invalidation | [Data lifecycle](references/data-lifecycle.md) |
| Labels, status meanings, recovery guidance | [Content](references/content-and-recovery.md) |
| Acceptance/regression checks, evidence after the last write, realistic load | [Acceptance](references/scenario-testing.md) |
| Composed result, sources of truth, tokens/fonts/theme, geometry depth, library readability, assets | [Visual judgment](references/visual-judgment.md) |
| Transferring an interface, selecting its target-system basis, structural replacement or migration | [Design transfer](references/design-transfer.md) |
| Any read or write through the Figwright adapter | [Figwright](references/figwright.md), before the first operation |

When implementation changes component responsibilities, shared code or reactive
ownership, use [code-maintenance](../code-maintenance/SKILL.md) for those decisions,
including its conditional Vue procedure. For read-only review, use the applicable
criteria through [code quality verification](../independent-audit/references/code-quality.md)
without changing this task's authority. UI journey rules remain in the procedures above.

For explicit delivery planning, cross-screen sequencing or a multi-stage transfer,
use available [implementation-planning](../implementation-planning/SKILL.md) with
the agreed journeys, artifact identity, required states and shared dependencies.
UI criteria and artifact checks remain here.

When an existing product's journeys must first be reconstructed for a broad
redesign, screen/control inventory or designer handoff, use
[product-flow-mapping](../product-flow-mapping/SKILL.md). Consume its stable
scenario/state/action links, retained outcomes and evidence gaps; this skill
retains UI quality, capture and canvas-operation criteria. A local edit with an
already sufficient scenario contract does not need a new product-wide map.

## Common execution and finish

1. Establish the mode, outcome, starting state, authoritative source and actual
   entry path from the brief. Before attributing live behavior, identify
   source/build, runtime and data. Read only the applicable procedures and the
   documentation of the tool in use.
2. Trace affected owners to consumers. Classify missing shared rules, bypassed
   primitives, flow mismatches or local defects. For a systemic change decide
   the shared contracts and migration order first; for a small one find the
   nearest responsible owner. When a reusable library itself changes, preserve
   its consumer-facing organization and public/internal boundary as well as the
   components inside it. Repeated complaints require revisiting that cause and
   omitted paths, not another isolated patch or another master.
3. Apply the selected procedure and its distinguishing check plus valid control.
   When compatibility is unclear, make a bounded reversible probe on a
   representative and a risky case before propagating a mechanism. Scale
   content to the risk; a small repair need not inventory the whole product.
4. Repeat the real action across affected paths, preserving input and save/cancel.
   Reuse matching gate/hook evidence, run missing and owner-required checks. Ask
   whether a check could pass while the complaint remains true. Observe the risky
   state before helpers repair it. For test design, use Acceptance above.

When an authorized multi-step mutation resumes after interruption, reconcile it
with the available [continuation procedure](../implementation-planning/references/continuation.md)
before the next write.

Whenever a rendered or drawn result exists, use Visual judgment for the composed
artifact after the last write and show a useful preview; this applies to
creation, implementation and transfer, not only to an explicit critique. A
preview does not suspend authorized work; wait only for an explicit checkpoint
or a consequential unresolved preference. Distinguish supplied facts,
observations, inference and gaps; missing access is not proof that no check ran.

For a cross-screen milestone, run a separate contrarian pass on the exact tested
artifact and challenge at least one stale, failed or recovery state. When
delegation is already authorized, the primary may assign that pass to an
independent reviewer; otherwise the primary runs it directly.

Report the operator outcome, relevant criterion → evidence or gap, actual
automated and visual checks, unresolved risks and owned runtime cleanup. A clean
detector, skill read, existing test, successful import or matching defaults are
not evidence of a complete transfer, a working journey, an editable system or a
usable library; user approval is separate from verification. Keep reporting in
the existing task, without a mandatory new document. When revising this skill,
use [evaluation guidance](evals/evaluation.md); it is not part of ordinary UI
work.
