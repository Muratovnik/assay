---
name: product-flow-mapping
description: Reconstruct, document, review or update existing product journeys and their screens, states and controls for redesign, handoff or coverage analysis. Use when behavior must be discovered and traced to evidence; skip visual styling, new-product ideation, backend-only work and local edits with an already sufficient scenario contract.
license: MIT
---

# Product flow mapping

Explain what a person can accomplish, which interface actions support it and
what actually happens. Deliver a navigable, evidence-linked map, not a gallery
of pages, a new design or an assertion that existing behavior is correct.

## Establish the task and authority

Recover audience, product/build identity, scope, required format and allowed
access. Reuse known decisions and inspect available sources before asking.
Distinguish mapping, updating a map and read-only review. A mapping request
allows the requested documentation, not edits to the application, production
mutations, credential extraction, installations, unrequested sharing or independent agents.
Existing authorized connections can serve scoped reads and the requested destination;
using one is not permission to obtain new access or change account settings.
Use authorized disposable data for consequential actions. Missing runtime or
canvas access narrows claims; it need not block a useful source-backed result.

Separate three layers throughout: observed implementation, owner-adopted intent,
and proposed changes. A code/document conflict stays visible until resolved;
neither source wins automatically. A recorded path is not its own acceptance
oracle. Goals inferred from controls are hypotheses, not user research.

## Use existing tools, not a new delivery system

This skill owns discovery and explanation, not capture, rendering or export
infrastructure. Use the existing browser/Playwright setup for actions, screenshots
and available traces; use the existing Figwright adapter for an authorized Figma
handoff. Read their owning procedures below before the relevant operation.
Do not add an Assay exporter, renderer, intermediate schema, graph validator,
wrapper CLI, recorder or another test stack for this workflow. Task-specific
steps through the existing tools are normal use, not a new reusable runtime.

Keep descriptions in the requested destination or the project's existing notes.
A missing capability calls for checking the available tools and documenting the
gap, not building a substitute. A test report is evidence, not the requested
Figma deliverable. Preserve useful text and captures without claiming canvas work.

## Select the needed procedure

| Decision | Read |
| --- | --- |
| Recover tasks, entry paths, controls and boundaries from an existing product | [Discovery](references/discovery.md) |
| Distinguish states, actions and evidence; inspect or capture behavior safely | [Evidence and states](references/evidence-and-states.md) |
| Check omissions, reconcile conflicts or update an existing map | [Coverage and maintenance](references/coverage-and-maintenance.md) |
| Prepare designer-facing pairs, reverse indexes or an authorized canvas update | [Handoff](references/handoff.md) |

Read only applicable branches. The optional [scenario template](templates/scenario.md)
is a writing aid, not a machine-readable format or mandatory document for a single
question. Research history and `evals/` are not runtime reading.

## Reconstruct and connect

1. Establish an independent inventory from requirements/documentation and actual
   entry points, screens and control owners. Work from goals down to actions and
   from controls back to goals. Do not derive the completeness denominator from
   the cards already written.
2. Connect each scenario's actor, goal and starting conditions to actions,
   observable results and relevant alternatives. Preserve distinct same-screen
   actions, dialogs, background work, external effects and departure/return.
   Do not manufacture every conceivable state or device combination.
3. Attach source identity, relevant conditions and evidence to consequential
   claims. Separate specified, source-read, executed and unverified results.
   A screenshot shows a state; it does not prove how it was reached or what an
   action saved. Redact before sharing and keep simulated states labeled.
4. Check both directions: each scoped task has a supporting path or named gap;
   each significant control/state has a purpose or explicit disposition. Check
   omissions and contradictory evidence, not just broken links. A narrow task
   stays narrow; a broad one names unexamined surfaces and conditions.
5. Present at the requested depth. Use stable names/links and a screen/control-to-
   scenario index for a large handoff. Keep existing facts apart from redesign
   decisions. Report scope, material findings, gaps and actual delivered locations.

## Consumers and ownership

For a redesign, give [operations-ui-delivery](../operations-ui-delivery/SKILL.md)
the scenarios, state/control links, retained outcomes and unresolved decisions.
That skill owns UI quality, capture mechanics and canvas operations; this one
owns discovering and explaining the behavior. A screenshot handoff does not
require reconstructing the old UI as editable components.

For scenario-based tests, give [test-writing](../test-writing/SKILL.md) the same
paths with their requirement sources and observation limits. It owns test
boundaries and justified expectations; an observed bug must not become the
expected result. [Implementation planning](../implementation-planning/SKILL.md)
can consume the map when sequencing is requested, without starting a new plan
for every mapping task. These are conditional consumers, not automatic workflows.

Before finishing, trace one consequential path in both directions and challenge
one material omission or conflicting source. A same-screen download is not a
missing navigation edge, and a decorative icon need not become a scenario.
Successful tool calls, a complete-looking canvas and a manual walkthrough do not
prove exhaustive coverage, usability or user approval.
