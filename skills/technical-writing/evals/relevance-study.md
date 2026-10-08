# Grounded content selection: 2026-10-08 study

## Decision and scope

The selected technical-writing revision is **D**: establish the questions a
document needs to answer, select claims and their depth against those questions,
and apply the finished-content check to the artifact actually delivered. A review
has two relevant artifacts: the source being assessed and the report its author
will receive. The accompanying text-writing correction removes an instruction to
keep every supported fact while retaining explicit preservation constraints.

This addresses a demonstrated selection problem. It does not establish that all
future prose will be free of surplus. D passed the exposed Tolmach review, a new
paired review family and an exposed drafting regression. One small source-note
footer remained in the drafting result and is recorded below. Earlier revisions'
failures remain part of the evidence.

The comparator is Assay main at
`1dbb7435d5349cb00cb4a2c8ffb5e00a2d703c03`. The observed Tolmach documents are from
[`b558693326c67d839c948c88126c586cf7c1d482`](https://github.com/Muratovnik/Tolmach/tree/b558693326c67d839c948c88126c586cf7c1d482).
The source review inspected README, CHANGELOG, coverage and package documentation.
It found no historic activation trace establishing which Assay revision, client
or references produced those texts. Published wording is evidence of the defect,
not proof that a particular runtime instruction caused it.

[The evidence record](relevance-evidence.json) contains all 25 writing outputs,
method patches and hashes, input packets' manifests, assessment history and
protocol amendments. It includes the text-writing comparison to keep one record
for the shared experiment. Tolmach excerpts carry their
[upstream attribution and license](relevance-NOTICE.md).

## Diagnosis

The existing method already said that a supported fact need not belong on a page
and required a final relevance review. Repeating that advice alone would not
explain the observed failures. The audit found more specific weaknesses:

| Weakness | Evidence in canonical source or observed behavior | Repair |
| --- | --- | --- |
| Preservation can override selection | The text-writing UI asks to keep every supported fact; its preservation sections also read unconditionally. | Select for the requested purpose, then preserve the meaning of retained or explicitly required material. Keep copyedit and preserve-all scope intact. |
| Examples reward extra explanation by default | Language examples label a dependency reassurance or retry consequence legitimate without a reader condition. | Make their usefulness conditional on a setup, recovery or preview question. The examples still demonstrate valid language. |
| A README opening is required to add a mechanism | The opening instruction demands both the product's job and a distinguishing constraint or mechanism. | Add the latter when it changes suitability or explains otherwise unclear behavior. |
| Relevance can be justified after composing | A true detail can be defended by inventing a reader's concern or a hypothetical comparison. | Establish the document's questions from the task, surface and actual reader work before selecting claims. Add real prerequisites and causal dependencies. |
| Sentence-level approval hides surplus clauses | A useful affected class or destination link can carry an incidental instance or invented rationale. | Select the granularity of claims and inspect substantive additions inside useful sentences. |
| Review output escapes its own check | C detects the Tolmach problems but repeats explanations in the delivered report. | Explicitly apply the existing check to the report and its author-facing purpose. |

An incidental proper name and a precise scope condition can look equally concrete.
Their roles differ. A class-level release note does not need a test fixture's
member name, while an exact target or exception may be indispensable. Likewise,
a link can identify a destination without promising an imagined benefit; a real
choice between alternatives may need that explanation. These distinctions, rather
than a list of Tolmach phrases, form the runtime change.

## Research and transfer decisions

The sources support design choices and measurement distinctions. None provides a
head-to-head result for this Assay revision or proves that the proposed prompt
mechanism must improve every writing task.

| Primary source or maintained method | Relevant contribution | Applied here and limit |
| --- | --- | --- |
| [Roberts, *Information structure in discourse*](https://semprag.org/index.php/sp/article/view/sp.5.6) | Relates discourse relevance to the questions participants are addressing. | Establish document questions before choosing material. This is a pragmatic framework, not an LLM intervention result. |
| [FineSurE](https://arxiv.org/html/2407.00908) | Separates faithfulness, completeness and conciseness and evaluates finer-grained summary content. | Grade truth, needed meaning and surplus separately. A useful sentence's irrelevant clause motivates a finer local check here; that extension is our inference, not the paper's experimental result. |
| [Google Technical Writing: audience](https://developers.google.com/tech-writing/one/audience) | Relates the document's scope to what its reader needs and already knows. | Ground audience assumptions in available context. A role label alone does not establish all prior knowledge. |
| [Diataxis: explanation](https://www.diataxis.fr/explanation/) | Gives understanding, connections, context and alternatives a legitimate place in explanation. | Protect causal explanations and useful examples. An action-only deletion test would make explanatory documents worse. |
| [The Good Docs Project: how-to](https://www.thegooddocsproject.dev/template/how-to) | Uses task-oriented instructions with conditional explanatory elements and expected results. | Treat templates as options selected for a task. Do not turn every available heading into required content. |
| [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) | Distinguishes a curated account of noteworthy changes from a commit log. | Select the affected behavior and consequential upgrade information; do not import every implementation or testing detail. |
| [GOV.UK: writing for user interfaces](https://www.gov.uk/service-manual/design/writing-for-user-interfaces) | Grounds help text in observed needs and places information at the relevant interaction. | Use as a check against unsolicited reassurance. Its transactional-UI guidance is not a universal rule for all technical documents. |

The resulting method uses a bounded content-selection decision and a check of the
finished artifact. It introduces no mandatory extra agent, outline file, deletion
quota, phrase blacklist, model service or repeated polishing loop. Named examples,
negative statements, anticipated failure paths and comparison language remain
available when their relationship to the task is real.

## Implementation plan and comparison

The work followed four decisions: audit positive instructions as well as stated
prohibitions; compare a small alignment fix with a content-selection mechanism;
combine supported repairs while testing their interaction; then verify the actual
delivered artifact and publish the cases as regressions.

| Revision | Frozen change |
| --- | --- |
| Baseline | Current technical-writing and text-writing runtime at the comparator commit. |
| A | Align README opening and language examples with conditional relevance. No change to the core selection method. |
| B | Establish document questions, select claim granularity and check substantive additions. Retain baseline README/language examples to isolate this candidate's source change. |
| C | Combine B with A's alignment; correct an inaccurate description of the Russian language example. |
| D | Keep C's selection mechanism and replace the delivery paragraph to name the finished review report as a subject of the existing check. |
| Text correction | Align the UI prompt and two preservation passages with selection of retained or explicitly required material. |

The source review found the seven runtime file changes coherent: four files in
technical-writing and three in text-writing. The UI file is canonical source,
not a generated client adapter. No template, preservation script, release version
or generated manifest changes are needed.

A and B initially behaved alike on the drafting tasks. The exposed Tolmach review
then separated them: A still accepted the incidental name and the invented
comparison; B detected both. C removed the confirmed positive-instruction
conflicts as well. Its own review output exposed another problem, so D explicitly
bound the check to the delivered report. This is a bundle of source repairs; the
results do not isolate the causal contribution of each individual sentence.

## Execution design

Each writing execution used a fresh native child context with the same requested
configuration, `gpt-6.1-sol` and `high`. This was a caller override to keep the
comparison configuration constant with the earlier experiment; the advisor tools
were unavailable. It was not a measured optimal model choice. The resolved model
revision, token use, quota use, cost and comparable latency were not observed.

The existing `tools/eval_assets.py prepare` utility froze input-only packets and
the selected method. Writers received an ordinary task, product notes and runtime
references, without grading keys, variant names or other outputs. For the README
family, both available README templates were included in every condition's
manifest. The text-writing pair explicitly loaded its skill-local UI prompt in
both conditions. That tests the stated invocation, not automatic client discovery.

The filesystem was shared and bounded by instructions. Packet manifests were
verified unchanged after all 25 executions; that does not establish every outside
read or effect. No product command, skill script, external model service or paid
runner formed part of the writing tasks. Task authorship, discovery and independent
review were additional work and are not represented as free.

### Task families and exposure

| Original ID / public regression | Document and material guards | Historical role |
| --- | --- | --- |
| w01 / TWREL01 | Harbor Jobs release notes: versions, queue limits, SDK scope, conditional shutdown checks and retry timing. | Working; relatively explicit source cues. |
| w02 / TWREL02 | Field Atlas admin-guide README: object relationships, roles, offline form versions and navigation. | Working; revised before any execution. |
| w03 / TWREL03 | Lumen Meter explanation: upload versus indexing versus complete time slots, timestamp conversion and rebuild branches. | Working; revised before any execution. |
| w04 / TWREL04 | Ordinary review of the reported Tolmach excerpts. | Exposed incident diagnostic, never transfer evidence. |
| f01 / TWREL05 | Mosaic Vault choice guide: three real formats, useful comparison and crop example, metadata, permissions and export procedure. | Baseline/C pair held back until C selection; later an exposed D regression. |
| f02 / TWREL06 | Meridian printer replacement: exact firmware, network and identity conditions, two tests and resume/failure paths. | Baseline/C pair held back until C selection. |
| f03 / TWREL07 | Lantern Museum review: missing purchase-channel eligibility, irrelevant icon history, useful names and confirmation conditions. | Separately authored after D's source freeze; baseline/D pair after D selection. |
| t01 / TXTREL01 | Russian volunteer email: changed arrangements, shifts, access and bounded reimbursement among ordinary planning notes. | Working text-writing pair. |
| TW-EN-01-D | Existing explicit preserve-every-fact task. | Exposed text-writing preservation control. |

The first three drafting families have one execution per condition, not repeated
samples establishing a rate. Russian and English are exercised. Chinese example
wording is aligned in source but has no new behavioral qualification.

### Oracle review and corrections

The first authoring review found requirements that exceeded their tasks: an exact
worked example and an optional navigation link were incorrectly mandatory. These
keys were corrected before any w02/w03 execution. Useful named examples were also
protected. Their product notes were revised to mix secondary facts into ordinary
notes instead of labeling them as material to omit. The methods were already
frozen; six prepared v1 packets were never executed. w01's already-used inputs
were not changed.

Nine nearby excerpt pairs and three context/clause probes calibrated the
distinctions. They protect a trace identifier in an exact support handoff while
rejecting it in a general guide, and keep accepted-only export scope while
removing an adjacent serializer filename. These are partial-property comparisons,
not ideal complete answers. Two purportedly true negative examples also contain
unsupported chronology, so they are not pure relevance-only controls.

An initial independent FAIL for run 01 was subsequently corrected to PASS.
The reviewer had rejected a queue-wide-versus-per-worker clarification while
accepting the same operational distinction in calibration W1-P1. The task and key
expressly support that distinction. A numerical example and a more compact
sentence do not justify a different binary result. The original assessment and
reason for correction remain in the evidence. No new writing execution or runtime
change followed that adjudication. Consequently, w01 supplies no comparative
improvement claim.

## Results

All rows below preserve consequential source meaning unless detection itself is
marked failed. Relevance is a separate dimension: a usable and accurate report
can still contain a local surplus finding. A small optional wording improvement
is not automatically a failed task.

| Task | Baseline | A | B | C | D |
| --- | --- | --- | --- | --- | --- |
| w01: release notes | PASS after oracle correction (01) | PASS (02) | PASS (03) | Not run | Not run |
| w02: guide README | PASS (04) | PASS (06) | PASS (05) | PASS; minor optional link-tail note (16) | Not run |
| w03: troubleshooting explanation | PASS (08) | PASS (09) | PASS (07) | Not run | Not run |
| w04: Tolmach review | FAIL to detect both relevance defects (13) | FAIL to detect both (14) | PASS (15) | Correct findings; local report repetition (17) | PASS (22) |
| f01: image export guide | PASS (18) | Not run | Not run | Required meaning PASS; local claim repetition (19) | Exposed regression PASS; minor footer note (25) |
| f02: printer replacement | PASS (21) | Not run | Not run | PASS (20) | Not run |
| f03: museum review | Correct findings; surplus inventory of unaffected text (23) | Not run | Not run | Not run | PASS (24) |

The text-writing baseline (10) already omitted the internal planning clutter. The
correction (11) retained the recipient-facing commitments and conditions too.
The explicit preservation control (12) retained every required fact, including
the four-versus-eleven-minute comparison. This supports compatibility with those
tasks and removes a source contradiction; it does not demonstrate a comparative
behavioral gain from the UI correction.

### Adverse results and their disposition

**A did not repair the original detection problem.** Its changes were useful
source alignment, but the observed review still approved the NPC example and
replaced wording around the link without removing the invented comparison.

**C found the problems and repeated its own explanations.** Run 17 explained
the coverage-link correction again after proposing it and repeated the retained
NPC-name distinction. Independent review correctly noted that existing guidance
already covered repetition; another general prohibition was not warranted.
D instead clarified the check's artifact boundary. Run 22 detects both original
problems and avoids those repeated explanations. Its short consistency assessment
compares two documents, and its source limitation does not invent new user work.

**C's held-back export guide contained a real local duplicate.** Run 19 states
that Original retains embedded metadata and immediately adds that it does not
remove that metadata. The adjacent useful statement about catalogue fields does
not justify the repeated claim. This remains a failed relevance observation for
C, although all export requirements hold. D was frozen before this answer was
read. Its later run 25 is an exposed regression, not a new held-out result.

**The new review pair separates report diagnosis from report content.** Both
23 and 24 find the missing CityPass route and irrelevant design history. Baseline
23 then inventories unaffected paragraphs after already accepting them. D's 24
keeps the findings, concrete replacements and the condition relevant to the
changed opening, without that inventory. This is one paired transfer observation,
not a population estimate.

**The last draft still admits a small editorial cleanup.** Independent review of
run 25 found all R1-R16 preserved and no material surplus claim. It noted the
closing “Based on the supplied …” footer: an unlinked account of source notes
adds little to the published guide and can be removed or replaced by useful source
links. This note is retained rather than describing the answer as flawless. The
format comparison, print-size check and supplier compatibility questions concern
real output properties and were not charged as surplus merely for being detailed.

### Budget and stopping

The initial ceiling was 19 writing executions: nine working comparisons, four
held-back drafting executions, three text-writing checks and three optional
diagnostic/repair executions. The three optional slots were used for the exposed
Tolmach review. C's exact-runtime README/review checks raised the communicated
ceiling to 21. The report-boundary defect led to a communicated three-run D check,
raising it to 24. C's later assessed export failure justified one first D execution
on that now-exposed task, raising the final ceiling to 25.

Each increase was stated before execution and is recorded in the protocol. No
unchanged candidate was repeatedly sampled until a favorable answer appeared.
The final checks leave no unresolved material failure in an executed D artifact,
but the small footer note and unexercised tasks remain limits of the result.

## Published assets and reproduction

The seven [technical cases](relevance-cases.json), their separate
[rubric](relevance-rubric.json) and [metadata](relevance-case-metadata.json) are
public working regressions now. Their historical reserved roles are recorded
above; publishing them makes them unsuitable as future unseen evidence. The
ordinary prose case is in text-writing's corresponding three files. Existing
case inputs, triggers and rubrics are unchanged.

The evidence JSON records each requested configuration, original case ID, public
ID, raw output, output SHA-256 and retained packet-manifest digest. It also retains
the original input corpora, grading keys, superseded preparations and all variant
patches against the baseline. Method maps include the runtime snapshot; packet
manifests identify the smaller set actually supplied. Scripts were not executed.

The original C technical-runtime map hash is
`3f9f556caeb0b983cc9a676a6a0a63dc81f4abe1ea959bd85c4eeb6ac381ca07`;
D is `391bb742e193715a586435e15a7c71f5d66e9150cb82cb3eabf60887bee4bb70`.
These maps use paths relative to technical-writing. The evidence also supplies
normalized maps with the skill-directory prefix and states the hash algorithm.
The shipped runtime was compared byte-for-byte with D plus the frozen text
correction. C's broader drafting results are not relabeled as D executions.

The repository's full check and release audit remain separate structural gates.
They validate packaging, evaluation assets and preservation fixtures; they do not
run these model comparisons or establish natural activation, cross-model
portability, subjective human preference or a guarantee of surplus-free prose.
