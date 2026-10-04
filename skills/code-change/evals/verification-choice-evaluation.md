# Verification choice: rationale and evaluation

Maintainer material for this method change, not runtime instructions or a model
run report. All shipped inputs, rubrics and synthetic receipts are public working
material. They are not production incidents or unseen final cases.

## Decision and current gap

The requested outcome is better choice of solution and evidence: avoid unnecessary
test work without losing meaningful regression protection, required gates or the
original consumer result. Reducing test count is not an acceptance goal.

The inspected baseline is `14ee6484bcd8c5534060200a1a73d2bad5143d28` (0.13.0).
Test-writing already protects independent expectations and rejects duplicate or
implementation-mirroring coverage. Planning already connects acceptance to the
consumer; test-audit already questions green checks that leave the problem intact.
Their existing criteria remain in place.

The local design gap is earlier: ordinary code changes can reach test authoring
without an explicit choice between existing coverage, a new regression test, a
diagnostic observation and a real consumer check. Not every edit invokes planning.
This supports adding that decision to code-change before test authoring and linking
it from planning, rather than adding another general thinking skill.

No captured failing native-client trajectory was supplied for this change. Missing
criteria, missed conditional reading, conflicting instructions and ignored rules
remain competing explanations for a particular incident. Static source inspection
identifies a method entry-point gap; it does not establish which explanation caused
a reported model failure or that the candidate fixes it. The pilot must inspect
selection, actions and final artifacts separately.

## Sources and transfer decisions

The following primary sources were read on 2026-10-04. Their relevant sections
support design choices, not measured effectiveness of this Assay revision.

| Source and reading scope | Transfer | Limit and legitimate control |
| --- | --- | --- |
| [OpenAI model guide: Testing and verification](https://developers.openai.com/api/docs/guides/latest-model#testing-and-verification) | Adapt task-proportionate verification and stop expanding sufficient checks without new evidence. | Vendor guidance for the documented model family is not a universal training diagnosis. Small authorization edits and mandatory gates still need protection (V03, V08). |
| [Claude Code best practices: Explore first, then plan, then code](https://code.claude.com/docs/en/best-practices#explore-first-then-plan-then-code) | Resolve a material uncertainty before committing to an implementation mechanism. | Retain the stated simple-task exception; do not import a compulsory plan mode, approval cycle or new orchestration (V01, V06). |
| [Google: Change-Detector Tests Considered Harmful](https://testing.googleblog.com/2015/01/testing-on-toilet-change-detector-tests.html), examples and conclusion, 2015-01-27 | Retain independent behavioral expectations; avoid a source checksum disguised as regression protection. | Exact wire bytes and supported public symbols can be real contracts, not accidental implementation (V11). |
| [Anthropic: Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents), outcome grading and transcript inspection | Grade task outcomes, evidence and valid alternatives; inspect actions instead of requiring a single trajectory. | Do not import a new runner or infer quality from the number of checks or read events. Native discovery and comparative behavior remain separate evidence. |

No external code, dataset, model route or provider dependency is bundled. The
neutral methods contain no model-specific policy. Keep the explicit test request,
safety/owner gates, authority and existing independent-oracle requirements.

## Ownership and bounded change

Code-change owns selecting sufficient verification and continuing to the requested
delivery. Its short entry rule applies to obvious choices; the new conditional
`references/verification-scope.md` resolves uncertain choices and expanding checks.
Test-writing retains expected behavior, boundaries and assertions. The small added
oracle paragraph distinguishes a hypothesized hidden test from an actual contract.
Planning retains outcome-sized units, dependencies and acceptance, with a link to
the evidence-choice owner. No new skill, hook, CLI, mandatory reviewer, plan file,
TDD sequence, model campaign or generic process engine is introduced.

Retain the existing [contract-drift corpus](contract-drift-protocol.md) and its
requirements/authority coverage. The additional cases isolate verification choices
and their neighboring valid controls instead of duplicating its whole workflow.

## Case coverage and grading

| Inputs | Distinction |
| --- | --- |
| V01 / V03 | A mechanical local edit with sufficient existing tests versus a one-line authorization defect needing missing negative protection. |
| V02 | An existing failing boundary test already protects the requested correction; a second copy adds no guarantee. |
| V04 / V09 | Green helper checks cannot prove a public operation; an unavailable real store cannot be certified by more stub tests. |
| V05 / V06 | A proposed mechanism with unresolved fit versus a supported and already adopted repair. |
| V07 / V08 | A still-applicable receipt versus one invalidated by a later shared behavior change. |
| V10 / V11 | Guessed grader properties versus real restoration requirements, and legitimate exact wire-format assertions. |
| V12 | Explicit useful tests-only work on correct code remains valid without a manufactured production change. |
| VD01-VD04 | Native discovery for bounded implementation, consumer verification, run-only and tests-only requests. |

Use `verification-choice-rubric.json` for evaluator-side assessment. Its requirements
are semantic: an equivalent implementation or useful check can pass without the
suggested wording or one particular command sequence. The original prompt and owner
contract remain authoritative if a rubric expectation is disputed.

Do not use source-keyword presence, required heading counts, a mandatory number of
tests, hidden-test vocabulary or a claimed skill invocation as an outcome grader.
Assess decision correctness, actual result, evidence fidelity, authorized effects
and unnecessary work separately. A correct result without a load event can establish
task success, but not use of this method. A load event alone establishes neither.
Keep execution/collection failures, genuine behavior failures and unavailable
integration distinct. Synthetic receipts in V07/V08 are supplied historical task
evidence, not new executions; check their hashes against the supplied files.

Before trusting rubric application, inspect a known-wrong and nearby valid artifact
for the disputed guarantee. For example, V03 must reject denied deletion that still
mutates data and accept owner deletion; V10 must reject an empty gzip payload and
accept a valid raw fallback. V11 must preserve a real protocol vector. These controls
calibrate expectations; they are not model runs or a new production test framework.

## Existing preparation and diagnostic pilot

Use the repository's existing `tools/eval_assets.py`; additional `*-cases.json`
pairs are already discovered by its evaluation-data gate. No runner change or
instruction-keyword test is necessary for this corpus.

From a complete candidate checkout, with an existing task-owned output directory
outside canonical skill packages, prepare one input and the selected method roots:

```sh
python -B tools/eval_assets.py prepare \
  --cases skills/code-change/evals/verification-choice-cases.json \
  --case V03 --output-parent /path/to/task-owned-packets \
  --method skills/code-change --method skills/test-writing
```

Select all relevant available peer roots for a particular comparison, holding the
root set equal between conditions. Repeat preparation from the frozen baseline
using the same task bytes; do not silently compare absence of all Assay against
this incremental change. Keep input identities and source revisions with receipts.
The emitted manifest establishes packet bytes, not filesystem isolation, discovery,
execution or a correct result. Exclude rubrics, metadata, this protocol, sibling
cases and prior results from executor access, including reachable source checkouts.

A first diagnostic budget is V01, V02 and V03 against baseline and candidate: six
runs through the intended native client, with tools, permissions, model/effort and
surrounding instructions held comparable. For discovery, present the normal enabled
collection and unmodified request, not a prompt forcing the new reference. Prepared
explicit-method runs can diagnose instruction execution but do not prove discovery.
Inspect actual load traces where available. Do not infer a cause from absent traces.

Before further tuning, choose an independent fresh case outside this public corpus
and freeze the remaining budget. Extend toward the paired continuation or consumer
cases only for a named unresolved hypothesis. Public cases are working/regression
evidence; they cannot be relabeled unseen final evidence. Grouped variants must
remain together. A tiny diagnostic pilot cannot establish universal savings,
portability or production failure frequency.

Record baseline/candidate outcomes and remaining user corrections, including failed
attempts. Count full-chain effort when observed; unknown subscription usage stays
unknown. Reject a candidate that merely writes better explanations, removes required
verification, or rejects valid nearby work. If both conditions already succeed, no
improvement is established on that task. Do not rerun unchanged inputs until a
preferred result appears or weaken the rubric to obtain green scores.

## Verification status and continuation

This change authors the method and evaluation assets. A structural pass can establish
valid assets, links and packaging; it cannot establish native discovery or improved
model behavior. Local fixture checks can establish properties of the supplied toy
programs, not that an agent will choose the new procedure.

No fresh native-client comparison, independent review, paid model evaluation or
quota measurement is claimed. Keep local and hosted command receipts with the exact
PR head or tested merge revision in the PR, outside future executor inputs. The next
behavioral evidence is the bounded paired pilot above when a native client and
explicitly bounded run budget are available.
