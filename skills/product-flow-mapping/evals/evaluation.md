# Evaluation protocol and current limits

Coordinator material, not runtime instructions. Use the existing
`tools/eval_assets.py` input/rubric protocol. No new runner, report system, model
dependency or paid campaign is introduced. The method bundles no exporter.

## Conditions

Compare the same scoped input, repository bytes, permissions, runtime/data and
model settings using (A) the existing UI method and ordinary authoring, and (B)
that method with product-flow-mapping. Use the same existing browser/Playwright
and Figwright capabilities on both sides. Explicit loading does not demonstrate
automatic discovery; run discovery cases through the normal client route.

Record actual client/model, relevant skill revisions, tool failures, corrections
and cost only when available. Build input-only packets with the existing
`tools/eval_assets.py prepare`, using named cases and explicit method roots.
Its verifier does not enforce filesystem isolation. Keep grading keys, prior
answers and execution history out of the executor's accessible context.

Preserve unused transfer cases before tuning. Once a case informs changes it is
regression evidence, not held-out evidence; reserve another when needed. A large
parallel campaign is not required. C01/C03 plus C11 provide a bounded comparison;
C19/C20 check direct tool reuse and the legitimate missing-access alternative.

## Evaluate the actual handoff

Judge missing known tasks/controls/branches, unsupported claims, faithful source
use, authorized effects and whether the designer can answer from the deliverable.
Trace goal -> action -> result and control -> scenario separately. Counts of cards
or successful tool operations do not establish semantic completeness.

Inspect tool results and actual Figma frames or the explicitly limited text/capture
result. A custom viewer is not progress when an existing Figma tool is available;
a Playwright test report is evidence rather than a substitute for the ordered
canvas. Neither missing access nor repetitive placement justifies building a
renderer, interchange schema or wrapper service for this skill.

Check a plausible defect and a nearby valid case: omitted Download versus a
decorative separator; simulated versus ordinarily reached state; retained outcome
versus obsolete layout; use of existing authorized access versus new permissions;
ordinary task-scoped tool calls versus a new maintained runtime. Keep source and
canvas identity, manual notes, branch meaning and unverified claims intact.

T01/T02 exercise the UI-redesign and test-writing consumers. The ordinary-text
example demonstrates their shared scenario contract, not a completed agent run.
T03 retains the valid native-only recording case; do not mandate Playwright for
surfaces it cannot inspect. T04 checks retirement without erasing manual notes.

## Current verification boundary

`tools/test_product_flow_mapping.py` checks registration/native projection,
input/rubric structure, consumer links and removal of the rejected export system.
These are packaging tests, not semantic grading, live tool tests or a model
comparison. Existing repository checks cover links and generated registration.
The pre-existing UI evidence workflow is unchanged from the PR base; it is not
a new product-flow acceptance claim.

The corpus contains 20 task cases, 8 discovery cases and 4 transfer cases. C15-C18
came from self-review; C19-C20 cover the owner's reuse correction. Revised cases
are regression material. Preparing/checking them does not mean a model ran them.
Keep future receipts outside skill inputs and report actual runs and limitations.
No improvement in coverage, quota use or cross-client discovery is claimed.
