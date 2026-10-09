# Public entry writing and maintenance durability

Evaluator-only follow-up to [grounded relevance](relevance-study.md). The subject
is the Assay writing method, including writing reached during repository work.
Game Design is an observed incident, not a repository changed by this study.

## Problem and source boundary

The reported Game Design About sentence was “Seven composable game design
methods and original playable examples.” At the inspected
[revision](https://github.com/Muratovnik/gamedesign-skills/tree/a0db5af71146586cf861881670c991ad94d87e2b),
the catalog and complete bundle did contain seven skills. The count was not a
factual error. It was an incidental snapshot placed in the project's enduring
identity. A new skill would create another introductory claim to maintain
without changing what the package is for.

The [README](https://github.com/Muratovnik/gamedesign-skills/blob/a0db5af71146586cf861881670c991ad94d87e2b/README.md)
had other independent problems. It called the product “methods” before making
clear that these are instructions for agents. Its Quick start was a contributor
sequence of environment setup, tests and archive preparation. A runnable example
showed a game consumer, but did not show how to apply a skill to the reader's own
game. Descriptions such as “consumed data change” required the reader to translate
internal ownership language into a design task. “Independent learning” appeared
as an output where the supported deliverable was playable learning material;
a human learning outcome would require observations.

A rewrite must preserve the complete-bundle requirement, direct entry into any
skill, conditional use of separately pinned Assay methods, permission boundaries,
native-client qualification limits and legal notices. Their placement and depth
still depend on the operation being documented; preservation does not require
copying every contract into the introduction. Exact numbers and revisions have
useful roles in those contracts. This is not a rule to remove counts, examples,
setup instructions or qualifications everywhere.

Description ownership is a separate issue. The
[renderer](https://github.com/Muratovnik/gamedesign-skills/blob/a0db5af71146586cf861881670c991ad94d87e2b/tools/render.py)
owns the plugin description and projects it into package manifests. GitHub About
is independently maintained external metadata. Editing a generated file would
not survive regeneration, and editing a README would not publish an About change.
The current bundle-size assertions in package validation are intentional product
invariants; an editorial correction does not authorize weakening them.

Public files and history do not recover the original agent's loaded instructions.
The study therefore separates the source audit, fresh behavioral reproduction,
and hypotheses about the historical cause.

## Review of the previous repair

Baseline is Assay `94c517b0aac9ba2575086bf9aead1cc828aadb0d` (0.17.2).
Its writing core already says that true facts can be irrelevant, rejects invented
reader concerns and reviews individual clauses. Adding that same norm again would
not explain the new incident.

The audit found more specific gaps:

- Repository and package descriptions had no explicit writing owner. Research,
  implementation and independent-audit entries did not hand their writing portions
  to the writing methods. The ordinary audit hook could suggest independent-audit,
  but this is a competing hint, not proof of interception or failed loading.
- The technical method distinguished document types but did not explicitly
  distinguish a standing description from a maintained inventory or dated record.
  Its client prompt emphasized fact checking without the same content-selection
  emphasis as its ordinary-prose counterpart.
- Text-writing's product-copy reference could turn every capability into a benefit
  story. Its language examples approved contrasts locally without establishing
  that the reader needed them. One Russian example repeated the same exclusion.
- The README method's conditional structure was sound, but “first use” did not
  explicitly distinguish applying the product from maintaining its repository.
- Prior acceptance was too easy to overread. The selected D method had only three
  recorded executions, including no README draft or metadata task. Twenty-five
  executions across earlier variants are not twenty-five tests of D.

The previous evidence also called a final source footer “editorial surplus” while
passing relevance with a minor note. A comparable baseline footer passed cleanly.
A new blinded assessment of both saved outputs accepted both as concise provenance
for that source-based guide. This does not prove all provenance footers useful.
It resolves the record by withdrawing the unsupported confirmed-surplus reading,
not by declaring a small confirmed failure acceptable. The historical raw outputs
and verdicts remain intact; the new assessment and original disagreement are
retained in this study's evidence.

## Research transfer

Primary sources were used to distinguish design choices, not to infer a successful
Assay change from someone else's benchmark. This was a focused review, not a
systematic literature census. Versions below matter: later revisions of two
papers differ from the earlier headlines.

| Source | Transfer to this change | Limit or rejected transfer |
| --- | --- | --- |
| [Google: timeless documentation](https://developers.google.com/style/timeless-documentation) | Choose detail according to the role and update basis of a statement; keep meaningful change information in its appropriate context. | Stable prose is not vague prose. Dates, current operational restrictions and release changes can be essential. |
| [Google: documentation best practices](https://google.github.io/styleguide/docguide/best_practices.html) | Maintain useful documentation alongside its source and distinguish historical decisions from current guidance. | This does not imply deleting a useful document because another page overlaps it. |
| [Diataxis: quality](https://diataxis.fr/quality/) | Check whether a document works for its reader as well as whether individual claims are accurate. | A fluent result or a numeric checklist total cannot certify the reader's complete path. |
| [Good Docs: README](https://www.thegooddocsproject.dev/template/readme) | Orient a new reader and provide a route appropriate to the actual product. | Do not copy every template heading or impose a sales story on metadata. |
| [Evaluating AGENTS.md, v3](https://arxiv.org/html/2602.11988v3) | Distinguish missing instructions from followed instructions that add unhelpful work. | In its coding tasks, generated-versus-none and developer-versus-none success differences were not significant; developer files outperformed generated ones. Length bins were observational. This is not evidence that shortening these writing skills will improve prose. |
| [SkillsBench, v4](https://arxiv.org/html/2602.12670v4) | Consider post-access failure, displacement of a useful default and unnecessary procedure as different mechanisms. | Its compactness comparison used different task groups, including a small longest group. It does not isolate shortening the same method or establish a universal rule-count limit. |
| [IFScale, v1](https://arxiv.org/html/2507.11538v1) | Instruction density is a possible stressor to test when there is local evidence. | Keyword-inclusion degradation is not a general semantic-writing threshold, nor proof of a coherence collapse. No length-only rewrite was chosen here. |
| [LLMBar, v2 / ICLR 2024](https://arxiv.org/pdf/2310.07641v2) | Challenge a grader with attractive, supported text that answers the wrong request. | A determinate defect needs a task-based reason; optional editorial preferences cannot become universal gold wording. |
| [MT-Bench judge study, v4](https://arxiv.org/html/2306.05685v4) and [length-controlled AlpacaEval, v2](https://arxiv.org/pdf/2404.04475v2) | Treat verbosity and candidate order as possible evaluator confounders; inspect the actual added meaning. | Do not transfer old models' failure rates to this model, infer accuracy from agreement, or force equal output length in a deletion-sensitive task. |
| [Anthropic: agent evaluations](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents) | Use task outcomes, retained trajectories where available, calibrated semantic judgment and deterministic checks for different properties. | A model judge does not become a human reader study, and static checks do not establish prose quality. |

The supplied software-engineering and research-quality documents reinforced the
separation of truth, requirements, usefulness and evidence. The reasoning-control
document supported separating availability, loading, compliance and outcomes.
Its source list was not treated as independently verified research. The supplied
Unity/Blender note led to [Scenario's skill collection](https://github.com/scenario-labs/skills),
whose role/goal navigation was a useful design example, not evidence for importing
its execution policies or promotional claims.

Comparable repositories supplied concrete alternatives:
[Anthropic skills](https://github.com/anthropics/skills) establishes the repository's
role and routes; [Sentry skills](https://github.com/getsentry/skills) names its team
and development use; [Superpowers](https://github.com/obra/superpowers) identifies
the category and describes the user-facing workflow. None was adopted wholesale
or certified as an ideal README. The deprecated state observed in
[OpenAI's old skills repository](https://github.com/openai/skills) is a useful
counterexample: a changing lifecycle fact can belong before the usual introduction.

[Vale](https://docs.vale.sh/) and [write-good](https://github.com/btford/write-good)
provide useful configurable style checks. Their documented default checks do not
decide whether a true fact belongs in this reader's description. No word blacklist,
new lint dependency or semantic-score proxy was added.

## Planned alternatives and implementation

The plan separates owner selection, content decisions, source maintenance and
acceptance. It was written before the comparisons; the evidence retains its
allocation records and subsequent changes.

**A: entry repair.** Explicitly assign product documentation and repository/package
descriptions to technical-writing, including the writing portion of a larger task.
Add conditional handoffs from research-driven-change, code-change and
independent-audit, with optional-peer metadata. Keep code-only changes, source
comments, commit records and ordinary progress messages outside this writing phase.
Align the technical client prompt with selection as well as retained-claim checking.

**B: entry plus content repair.** Extend A with a surface/lifetime decision where
content is selected; preserve exact operational detail and maintained inventories.
Find canonical description producers and affected independent surfaces. Clarify
product first use in the README reference, and inspect the continuous reader path.
Condition the product-copy benefit example and English, Russian and Chinese
contrast examples on the reader's actual question. Remove the duplicated Russian
exclusion. Preserve the narrower copyedit and explicit preserve-all contracts.

**C: delivery observation.** A working README trial left a check-generated handout
in the delivered copy despite claiming only the requested files changed. Add a
conditional instruction to separate requested output from temporary check products
and inspect the saved state. This did not resolve the next observed mismatch.

**D: composition and final state.** Two working reviews reported reading technical
writing guidance but still ended with a broad audit inventory. Independent-audit owned a
competing report format. Scope that format: the writing owner controls the delivery
of a narrow prose review, while acceptance and release audits retain their needed
coverage. Require the final file inventory after effectful checks, separately from
a command's reported success. The next release-folder draft had the correct scope.

**E: scope-based reference selection.** Source review found another overlap:
independent-audit routed “repository readers” to the broad repository/release
procedure and README prose to technical-writing. The leaf also ended with an
unconditional readiness-report instruction. Select that procedure by the requested
readiness, lifecycle or distribution decision, rather than the filename README;
carry relevant evidence into a writing finding without adding a readiness report.
This also makes the rule's owner explicit instead of relying on competing formats.

D's next review passed its original rubric in an independent assessment. The
assessor treated its unrelated package-installation sentence as optional tightening.
E was already proposed from the source overlap; that sentence is not retrospectively
reported as an independently confirmed D failure. The record preserves both the
primary's relevance concern and the assessor's interpretation.

**F: procedural depth and existing entry links.** Independent assessment of E's
Game Design rewrite rejected an explanation of a binding-tool flag. The nearby
authorization instructions were needed; the optional tool's syntax was detached
from a command or decision offered by the page. Keep procedure-specific detail
with the operation it explains when a page links to a separate procedure, retaining
the conditions that affect the present route. This targets the depth decision,
not that flag's spelling or a ban on permission warnings.

Assessment coverage also needed repair. The pinned release guide links to
`README.md#quick-start` for contributor environment setup. GDIAG2 adds an explicit
criterion for that route; its source files and request are identical to GDIAG's,
apart from the case ID. A later byte comparison corrected an erroneous preparation
note that had described the file as missing: it was already in the original
packets. The gap was in explicit assessment, not unavailable source evidence.
Both baseline and F receive the same sources and extended key. The runtime checks known
incoming links when changing a section's purpose, without requiring an unrelated
repository-wide link census. GDIAG and GDIAG2 stay separate executions in one
incident group. Earlier passes are not relabeled as coverage of the new criterion.

These changes replace or qualify the conflicting local instructions. They do not
add a required report, claim ledger, extra model call, external review stage,
installation step or recursive rewrite loop to ordinary writing. Existing hooks,
README layouts, preservation scripts and product package invariants are unchanged.

## Measurement and acceptance

The existing `tools/eval_assets.py prepare` materialized input-only packets. Each
packet also received the complete frozen runtime collection, including required
assets and scripts, and a catalog of its real descriptions. Executors were asked
to select methods from that catalog; the caller did not force the writing method. They could
read only their packet and output copy by instruction. Keys, other cases, histories,
candidate labels and earlier answers stayed outside the allowed reads. This is an
instruction-bounded shared filesystem, not attested isolation or an installed
Codex/Claude discovery test.

All requested executor configurations were `gpt-6-astra` with `ultra` effort. The
effective backend revision, complete token/cost records and host-attested read
traces were unavailable. A returned list of references is an executor self-report.
Hook-generated first-stage hints were copied from the unchanged actual hook into
the review and research contexts; this tests the handoff from the supplied hint,
not native hook installation. Literal wrapper text is retained for later runs;
the first incident trio has its original packet bytes and a boundary summary,
but not a byte-complete orchestration message.

Each prepared execution has a run ID and frozen input/method identity. Failed,
interrupted and unexecuted allocations remain distinguishable. A continuation
interrupted two D tasks: one retained only an unchanged copy of its inputs, the
other only its target's starting heading. Neither supplies a completed success.
Changes prompted new candidate identities;
unchanged outputs were not retried until a preferred result appeared.

### Cases and grouping

The real Game Design rewrite is an exposed diagnostic. Its rubric was formalized
after the first task was launched but before any result inspection; it is not an
unseen selection or final test. Other task families include release-folder onboarding
and editorial review, code and generated catalog maintenance, a crash-recovery
explanation, Chinese public copy with a useful audience-specific contrast, and a
code-only boundary. The research-to-change task extends the catalog family and
does not add an independent group. The rename follow-up starts from a supplied
coherent later state, not a previous executor's actual output.

An independent author reserved final groups before selection. Their hashes and
exposure history are retained separately from task content. After publication all
these cases are public working material; their historical pre-exposure status does
not make later reuse unseen evidence.

The original reservation contains ordinary prose only. An independent overlap
review, performed without seeing its execution results, found that one criterion
in the Russian pilot note repeats a calibration decision: preserve attribution
and the lack of measurements when reporting an observation of a shorter queue.
That component is exposed evidence, and the case is partly calibration-related.
Its new numerical units, attendance comparison and recommendation still add task
coverage. The visitor and bounded-correction cases reuse some source motifs but
ask for different operations; those relationships are disclosed too. No claim of
three wholly calibration-independent final groups follows from the old split plan.
Original criteria and results are retained rather than dropping the shared item.

After selecting F and opening those tasks, the plan added two technical groups
from a fresh author who received no methods, prior cases or outputs. This extension
was declared before its tasks were prepared or graded, but after some original
final outputs had been read. It is not retroactively part of the initial reservation.
It allocates one baseline and one F execution per new group, with no unchanged
retry for a preferred answer. The runtime remains frozen across both collections.

### Semantic assessment and mechanical evidence

Independent assessments use anonymized results, the exact task, its sources and
atomic criteria, with quotations for verdicts. Candidate labels and methods are
withheld. Full documents are assessed, including supporting clauses, conditions,
navigation and reader path. Semantic judgment is separate from executable examples,
file-scope comparisons and regeneration checks. A concise no-issue review is valid;
finding count, length and preferred wording are not acceptance proxies.

The calibration set contains context reversals: the same true detail can be useful
in an internal evidence note and extraneous on a visitor sign; an exact capacity or
required supported revision can matter where a live inventory total does not. It
also contains legitimate contrast, attribution, warnings, generated ownership and
alternate presentation. The original assessment agreed with 20 authored decisions
and called one visitor-caption example ambiguous. That item is retained as an
ambiguity and excluded from any binary calibration denominator. This is agreement
with authored criteria, not measured evaluator accuracy or a human reader study.

Calibration and D's review adjudication exposed a remaining assessment weakness:
an unnecessary clause can escape if a grader asks only whether the whole report
is a process recital or whether a word limit was specified. Before reading E's
working outputs or opening final tasks, a separate relevance-assessment clarification
required the reader function and consequence of additions to be assessed directly.
It permits meaningful context, style, explanation and limits, and does not demand
new facts in every sentence. Brevity cannot justify unrelated content. Original
rubric scores remain intact; assessments under this clarification are identified
separately. It is not claimed to predate earlier executions.

Mechanical checks use saved copies, never repair the submitted trials. For catalog
changes, regenerate and compare the submitted outputs, then add another preset or
change a source-owned title/dimension. The intended summary should still describe
the product while the computed inventory and reference follow the changed source.
For a code-only request, compare unaffected files and the Python syntax outside the
requested function. For onboarding, distinguish the pristine release route from
re-running a command in a workspace where a previous output already exists.

Two trials retained `handout.md` despite cleanup/scope claims. A fresh reconstruction
of the release with the submitted requested edits ran successfully; the README's
command was not thereby disproved. The defect was the delivered state and conflicting
scope claim. One executor later supplied an apparent successful unlink/check sequence
as its own report, but no attested trajectory resolved why the file remained. Small
separate parent/child deletion probes did not reproduce a general persistence fault.
The study claims neither a hidden platform bug nor a demonstrated ignored instruction.
Acceptance of later output uses independently inspected final files.

The mixed-work rubric originally combined adequate maintainer prose with actual
historical check execution in item 10. Its artifact/content assessment can pass
while the original item and aggregate remain UNKNOWN because the judge packet
lacks a retained execution history. Final-state probes establish the properties
they inspect, not who ran an earlier command. The published rubric separates the
artifact and execution assessments; original keys and UNKNOWN verdicts remain
unchanged. No global execution PASS is inferred from an artifact PASS, and missing
history is not reported as fabrication or an absent requested document.

## Results and selected change

The comparison is a bounded diagnosis across successive revisions, not a
balanced benchmark or a success-rate estimate. Each row identifies the version
that actually produced its outputs. Completed but ungraded trials remain saved
without receiving an inferred semantic pass.

| Method | Decisive observed result | Consequence |
| --- | --- | --- |
| Baseline | The original incident retained the incidental count in its introduction and About text (`d01`). The generated-catalog task retained a five-item summary after a sixth item was added (`d07`). The narrow review appended a process inventory (`d12`). | These are separate content, maintenance and report-scope failures. |
| A: entry | The incident still retained the count despite reporting the writing owner (`d02`). | Better entry instructions alone did not fix content selection. |
| B: surface | The incident passed its inspected content criteria (`d03`); its handoff criterion stayed unknown because the judge packet lacked that handoff. The catalog update and later source mutation passed (`d06`), while the review still appended a process inventory (`d13`). One onboarding output retained an unrequested file (`d05`). | Content improvement did not establish sound composition or delivery. |
| C: delivery | Another onboarding output retained the same unrequested file despite cleanup claims (`d16`). Pristine first use worked. | An instruction about temporary products was insufficient without observing final saved state. |
| D: composition | The narrow review passed its original rubric (`d21`); the next onboarding copy had the requested file scope and a working first-use route (`d22`, mechanical checks). | Preserve these gains, while resolving the remaining source-level overlap in audit reference selection. |
| E: scope | The review and onboarding artifacts passed (`d27`, `d30`). The mixed task's artifact and content passed, with historical execution unknown (`d28`). The incident rewrite was rejected for the detached option explanation (`d29`). | Repair the decision about procedural depth rather than waive the remaining short passage. |
| F: depth | On the incident with the extended key, every criterion and the separate content assessment passed (`d33`); the paired baseline still failed the introductory-count criterion (`d32`). The substantial recovery guide passed all its criteria (`d35`). The mixed task passed artifact/content assessment and saved-state regeneration/mutation checks (`d34`), with historical execution still unknown. | Initially select F for reserved transfer checks; the later ordinary-prose failure withdraws that acceptance. |

The detailed recovery guide retained the 72-hour retention basis, opaque cursors,
event identity, atomic application/checkpointing and the consequences of a crash.
The catalog probe preserved computed inventory and exact dimensions while removing
the incidental total from the standing description. These checks matter because
a deletion-only strategy could make short copy pass while damaging technical use.

Other controls retain their actual version identities: B's Chinese task preserved
the useful seat-versus-book distinction; E's code-only task left prose untouched.
They are supporting evidence for unchanged components, not additional F executions.

F was selected at `2026-10-08T19:09:33.675472+00:00`, before the original reserved
tasks were opened. Its complete runtime manifest has SHA-256
`b8f207e71f219466b7b7585f3a1f33f555b5889e45ab68ca1dd051e1e799bcdf`.
The digest identifies the exact saved manifest bytes, whose entries identify each
runtime file. That historical selection and its unchanged snapshot remain in the
record; they do not make a failed final result acceptable.

### Ordinary-prose transfer rejected F

The original reserved collection produced six complete outputs: one baseline and
one F result for each case. Both versions passed the visitor artifacts and bounded
room correction. The baseline Russian decision note passed; F's note (`d40`) was
rejected under original criterion 10 and the separate content criterion. Its last
sentence repeated the immediately preceding statement that further observations
might still be needed. All necessary limits concerning units, attribution and the
proposed trial remained useful; they were not the rejected material. Delivery
scope passed for all six outputs. The partly exposed queue-attribution criterion
was not the defect that caused this rejection.

This failed result withdrew F's acceptance. Two executions in the newly opened
technical extension were already active and were retained; its two unstarted
allocations were cancelled with that reason. The exposed collections became
diagnostic material for subsequent changes, regardless of their outcomes.

**G: contribution across the complete text.** The ordinary-prose owner had received
entry and example corrections, but its main content review still said only to
repair repeated conclusions. It now checks the contribution of supporting clauses
and compares their meaning with nearby conditions and the ending. A necessary
qualification stays where it limits a claim; expressing the same limit again in
different words is not additional evidence or caution. A warning at a separate
action and a useful recap of a long argument retain their distinct reader roles.

Source review also found an unhelpful teaching example in the composition leaf:
after describing a prototype, it added absent production metrics without a task
that needed them. G keeps the actual contribution and makes deployment or outcome
qualification conditional on that question. Technical-writing instructions remain
unchanged from F. No repeated word, caveat, summary or uncertainty is prohibited
as a category.

G's new working execution on the exposed Russian case passed every original
criterion and the separate content/delivery assessments (`d46`). The completed
technical extension outputs also passed: baseline's restoration runbook (`d42`)
and F's audio-replacement help (`d43`). Their paired allocations were cancelled;
these two successes do not establish a paired comparison or become G executions.

**H: useful endings across language profiles.** Independent source review then
found that the Chinese profile treated an ending without a next action as a defect
cue, while the shared method explicitly allowed a recap that aids understanding
or recall. The English and Russian definitions used a similar cue. H aligns those
three definitions with the ending's contribution and supplies a Chinese example
of an explanatory recap. The source report retains the inconsistency and its
resolution. This is a confirmed source conflict, not an inferred behavioral
failure of G.

H leaves G's main content decisions and F's technical instructions unchanged. Its
Russian working execution passed the original and separate artifact assessments
(`d47`). A further Chinese editorial control passed all six original criteria and
the separate content/delivery assessments (`d48`). It preserved a useful recap and
identified an adjacent duplicate, testing both sides of the revised distinction.
This is exposed working material, not reserved transfer evidence or broad language
qualification.

H was selected at `2026-10-08T19:51:34.939476+00:00`. Its complete runtime manifest
has SHA-256 `35b3ec8b99e34a85c0d3d7fd98cb6e1944faee5bf9586fb457b423b488568825`.
Every working runtime file matched that snapshot before renewed task content was
opened. The earlier F and G observations keep their original identities; they are
evidence about unchanged components, not additional H executions.

### Renewed transfer on the selected method

A fresh author prepared two task groups without reading the methods, incident,
earlier cases or outputs: a Russian production decision memo and a detailed API
guide. The new memo requires reconciling commercial revisions, expenditure versus
cash limits, production rates, deadlines and contingent decisions. The API guide
requires a complete upload and verification path, exact protocol boundaries,
recovery from uncertain responses and usable reference detail. Both test whether
the method can retain consequential depth while selecting useful content.

The author package was sealed before H selection. Filenames were visible in a
directory listing before selection; requests, source bodies and criteria were
opened afterward. This limited metadata exposure is recorded explicitly. No
runtime edit followed it. One baseline and one H execution were allocated per
group, with their order reversed between groups. The original keys remain intact,
and independent assessments receive anonymized copies, all source documents and
the separate content criterion. The memo pair shares an assessor; the API outputs
use separate fresh assessors for parallel review under the same key. Neither
assessment requires a relative winner. The new groups are not a continuation of
the retired F extension.

Both production memos passed all 21 original criteria and the separate content
and delivery assessments (`d49`, baseline; `d51`, H). The H result distinguishes
service expenses, the initial payment and peak cash commitment, keeps the
commissioning conditions and customer commitments, and assigns the temporary
solution's exit. Its source-grounded supporting detail was assessed by its role
in that decision, without a brevity preference. This pass is evidence of preserving
necessary depth; the equally accepted baseline does not establish an H advantage
on the new memo.

Both API guides passed all 32 original criteria and the separate content and
delivery assessments (`d50`, H; `d52`, baseline). The H guide carries a complete
create, append, commit, retrieve and byte-verification route, with exact chunk
boundaries, fixed deadlines, state-dependent recovery and capacity accounting.
The independent assessment accepted its supporting explanations by their
operational function. The equal baseline result supports a preservation check,
not a claimed advantage on this transfer case. All 272 quoted API evidence spans
and 178 memo spans were independently checked against their packet files.

The selected H snapshot therefore has two accepted exposed working/control
executions and two accepted renewed executions. Its new comparison covers a
decision memo and a detailed technical guide; it does not establish a general
success rate, a human readership result or native-client discovery. Earlier
technical gains remain attributed to their producing snapshots. No confirmed
artifact defect remains open in the selected snapshot's inspected results.

Across the whole diagnosis, 52 executions were allocated: 46 completed, two were
interrupted and four were cancelled before execution. Those totals include the
baseline and successive candidates. They are not 46 passes of H. The published
case collection contains 17 cases, with related variants assigned to their actual
groups rather than counted as independent tasks.

### Repository validation

The initial full repository check found one integration omission: the audit
packet test's explicit criteria-root fixture did not include the two newly linked
writing methods. Adding those roots preserved the existing link-resolution and
isolation assertions. The repaired packet suite passed its 33 tests, and the next
`python -B tools/check.py --all` passed every repository gate. This test-only
repair leaves all measured runtime snapshots and execution packets unchanged.

The publication scanner subsequently reported 13 generic-key matches on three
verified content hashes in the saved evidence. Their values reproduce the two
synthetic memo output hashes and the fictional API source hash. The scanner
configuration filters only that rule, those exact values and the named durability
evidence files; inherited detection remains enabled. Offline controls confirmed
that other values at the same paths and the same hashes outside those paths
remain detected. Original evidence bytes and the initial failed audit are kept.
The subsequent `python .github/relkit.pyz audit` passed with that configuration.
The evidence record separates each local gate's actual snapshot from the later
compiled assessments and the published PR's checks.

## Published assets and reuse

| Asset | What it preserves |
| --- | --- |
| [Technical cases](durability-cases.json), [rubric](durability-rubric.json), [metadata](durability-case-metadata.json) | Public requests and sources, separate assessment criteria, and task grouping/exposure. |
| [Ordinary-prose cases](../../text-writing/evals/durability-cases.json), [rubric](../../text-writing/evals/durability-rubric.json), [metadata](../../text-writing/evals/durability-case-metadata.json) | Tasks owned by text-writing, including useful contrast, evidence-based Russian prose and bounded edits. |
| [Evidence](durability-evidence.json) | Exact method manifests and patches, source blobs, reconstructible input packet maps, allocations, exposure corrections, observations and independent source/evidence reviews. |
| [Original outputs](durability-outputs.json) | Saved changed texts plus file hashes, including rejected and interrupted results; unchanged files come from the identified input copy. |
| [Assessments](durability-judgments.json) | Original atomic verdicts and quoted evidence, with later clarifications and adjudications kept separate. |
| [Source notice](durability-NOTICE.md) | Attribution and license for the pinned real-project material. |

The manifest digests in the evidence identify exact retained JSON bytes. The
packet map records how to reconstruct its ordered headers, runtime-prefixed file
hashes and other supplied paths. Exact non-runtime text payloads, including the
available-skill catalogs, are stored under their hash keys alongside source blobs.
It is not a claim that the preparation service or
all executor reads were attested. The assessment manifest records packet/result
identities and requested settings when retained; four older assessment settings
stay unknown rather than inheriting a common study preference.

All published cases are now public working material. They can be reused for
development, but another unseen-transfer claim needs new, independently prepared
task groups. Keep assessment keys outside an executor's permitted inputs. The
existing preparation utility can materialize a case; the study's complete-runtime
catalog supplementation and bounded execution wrapper are separately recorded in
the evidence. No new model runner or mandatory runtime review process was added.
