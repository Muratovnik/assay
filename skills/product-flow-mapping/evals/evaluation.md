# Evaluation protocol and current limits

Coordinator material, not runtime instructions. The paired JSON corpora use the
existing `tools/eval_assets.py` protocol. No new runner, model dependency or paid
campaign is introduced. Inputs and rubric keys remain separate.

## Conditions

Compare the same scoped input, repository bytes, permissions, runtime/data and
model settings using (A) the current operations UI method and ordinary authoring,
and (B) that method with product-flow-mapping. Explicit loading does not prove
automatic discovery; use the discovery cases separately through the normal client
route. Record actual client/model/effort, relevant skill hashes, tool failures,
corrections and cost only when available. A refreshed model does not inherit old
quality claims.

Use `tools/eval_assets.py prepare` with the named corpus/case and explicit method
roots to construct input-only packets outside the source checkout. The existing
packet verifier does not enforce filesystem blindness by itself. Exclude rubrics,
prior answers and execution history from the executor's accessible context. Do
not read the keys while performing a mapping task.

Preserve the transfer cases before tuning the initial rules. Once exercised for
tuning, record them as regressions and reserve another case; calling a reused
example held-out would be misleading. No fixed large parallel campaign is required.
A bounded authorized comparison can begin with C01/C03 and the nearby control C11.

## Evaluate outcomes, not artifact size

Judge missing known goals/controls/branches, unsupported claims, provenance
faithfulness, authorized effects and ability to answer a designer's questions
from the result. Check goal -> action -> result and control -> scenario separately.
A scenario count or green graph validator is not semantic completeness.

Inspect created artifacts and tool results, not just the final summary. Preserve
failed attempts and distinguish a harness failure from a bad decision. Test a
plausible defect with a nearby valid control: omitted export versus decorative
separator; simulated state versus an ordinary observed path; retained outcome
versus an old panel arrangement; meaningful local explanation versus full audit.

T01 and T02 exercise the two concrete consuming workflows: UI redesign acceptance
and test-oracle design. The synthetic example and its two handoff views demonstrate
the shared data contract; they are not fresh model runs or Routevane evidence.

## Current verification boundary

`tools/test_product_flow_mapping.py` exercises structural validation, evidence
labels, graph links, same-state actions, image hash/annotation binding, path
confinement, redaction gating, create-only export, manual note preservation,
HTML escaping, change propagation and the two handoff consumers. These are
mechanical tests, not a behavioral comparison or discovery qualification.

The corpus has 18 task cases, 8 discovery cases and 4 transfer cases. C15-C18
were added during self-review as regressions, not as fresh held-out evidence.
Authoring and validating these files does not mean those cases were executed by
a model. Store future receipts and outputs outside skill inputs/source; report
actual runs and gaps in the delivery record. No claim of improved recall, lower
quota use or portability follows from this implementation alone.

The browser probe in `browser/export.test.mjs` runs through the existing UI
evidence workflow. It opens the real exported file with unchanged CSP and local
PNG paths, checks rendered explanations, unique anchors, callout navigation and
wide/narrow composition. It uses only synthetic data. A green result establishes
this exporter path in that browser, not live Figma or Routevane behavior.
