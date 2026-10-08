# Comparative evidence for Assay skills

Assessment date: **2026-10-08**. Assay **0.17.2**, commit
`94c517b0aac9ba2575086bf9aead1cc828aadb0d`.

Assay has a substantial collection of evaluation inputs and useful checking
utilities, but broad effectiveness and savings claims remain unsupported. The
strongest retained comparisons concern specific writing revisions. A new,
frozen comparison of five small execution/review tasks provides direct evidence
about adding the current collection in this host, with important limits on
sample size, exposure, discovery and cost.

This report connects the repository evidence, a targeted review of primary
research, the new comparison, and the resulting repair. It is an assessment
record, not a new runtime policy or a ranking of the skills. Its conclusions do
not depend on treating case counts, instruction compliance or a polished answer
as successful delivery.

## Repository evidence at the reviewed baseline

The baseline census covers all 14 skills in [the catalog](../../catalog.toml) at Assay **0.17.2**, commit `94c517b0aac9ba2575086bf9aead1cc828aadb0d`. It inspected every `SKILL.md`, inventoried the evaluation JSON collections, and examined their protocols, relevant tools and tests, and retained writing records. It did not semantically regrade every case or search private result stores. “No retained run located” below is limited to those examined repository surfaces.

The [primary-corpus inventory](skill-effectiveness/inventory.json) records 449
case specifications and their source identities, excluding auxiliary, discovery
and trigger collections. These counts are navigation and coverage information,
not 449 executed or independent tasks and not a measure of skill quality.

Four kinds of evidence must remain distinct. **Authored cases and rubrics** specify intended decisions. **Structural checks** validate matters such as matching IDs, allowed input fields and packet integrity. **Executable utility or fixture tests** exercise the particular program, interaction or assertion they contain. **Recorded model outputs and comparable trials** can support behavioral conclusions for their actual tasks and conditions. Passing the first three does not establish the fourth; a successful load also does not establish that the method improved delivery. These distinctions follow the repository's [evaluation boundary](../evaluation.md) and [paired-comparison criteria](../../skills/skill-evaluation/references/paired-pilot.md).

### Mechanisms, available evidence and discriminating comparisons

The final column proposes the next observation that could change an assessment. It is not a quality ranking, a mandatory campaign, or a prediction that a skill will win.

| Skill and intended mechanism | Evidence located at the reviewed revision | Next useful discriminator |
| --- | --- | --- |
| [code-change](../../skills/code-change/SKILL.md): connect the contract, implementation, consumers and sufficient verification | Executable fixture controls; a [historical code-to-documentation report](../../skills/technical-writing/evals/evaluation.md#observed-artifacts-and-decision) in which both conditions succeeded. Later [verification guidance](../../skills/code-change/evals/verification-choice-evaluation.md#verification-status-and-continuation) has no recorded native comparison. | Deliver a public operation whose helper tests already pass; preserve a nearby trivial edit and a legitimate authorization path. |
| [implementation-planning](../../skills/implementation-planning/SKILL.md): ground units, dependencies, acceptance and continuation | Planning/lifecycle cases and packet/consumer-link checks; [authoring records no model or outcome comparison](../../skills/implementation-planning/evals/evaluation.md#current-evidence). | Have a downstream executor complete the next unit, including a real changed premise or interruption. |
| [software-architecture](../../skills/software-architecture/SKILL.md): choose owners, contracts and placement from requirements and alternatives | Decision/discovery cases and packaging checks; [comparison remains proposed](../../skills/software-architecture/evals/evaluation.md#bounded-comparison-when-execution-is-available). | Distinguish one shared policy from similar syntax serving separate policies, then inspect the affected consumers. |
| [test-writing](../../skills/test-writing/SKILL.md): justify the oracle and expose meaningful defects without freezing private implementation | [Executable task inputs](../../skills/test-writing/evals/cases.json) and [semantic rubrics](../../skills/test-writing/evals/rubric.json); no retained model result located. | Challenge generated tests with a known defect and a valid implementation change, retaining the task's write scope. |
| [test-audit](../../skills/test-audit/SKILL.md): check both false acceptance and false rejection in an existing suite | [Supplied suites and decision cases](../../skills/test-audit/evals/cases.json); no retained model result located. | Identify a wrong expectation while accepting justified public-API assertions and a deliberately narrow no-crash check. |
| [independent-audit](../../skills/independent-audit/SKILL.md): compare the actual subject with its brief under read-only authority | File-backed cases and [executed-program/packet test machinery](../../skills/independent-audit/evals/protocol.md#mechanical-checks); no retained audit-executor result located. | Pair an actual violation with a valid scoped pilot; assess final coverage, evidence fidelity and authorized effects together. |
| [evidence-research](../../skills/evidence-research/SKILL.md): locate sources and preserve claim support, qualifications and alternatives | [Synthetic source packets and supplied traces](../../skills/evidence-research/evals/evaluation.md), explicitly described as specifications. | Compare retrieval from a fixed searchable corpus with direct provision of the same evidence; inspect final claims and table cells. |
| [research-driven-change](../../skills/research-driven-change/SKILL.md): preserve one outcome through research, decisions, execution and delivery | Complete local adapter subjects, synthetic transition cases and [mechanical controls](../../skills/research-driven-change/evals/evaluation.md#coverage-and-controls); no retained model comparison located. | Complete an authorized adapter change and continuation, while preserving a paired plan-only boundary. |
| [ui-delivery](../../skills/ui-delivery/SKILL.md): connect actions, states, shared components and composed visual results | Supplied-fact cases, a [reported historical repair/discovery episode](../../skills/ui-delivery/evals/evaluation.md), and [synthetic Chromium fixture results](../../skills/ui-delivery/evals/browser/README.md#evidence-from-authoring-this-change); no located old/new agent comparison. | Require discovery and repair through the real UI action, then inspect interaction and the final render against valid neighboring behavior. |
| [product-flow-mapping](../../skills/product-flow-mapping/SKILL.md): connect goals, controls, states and evidence in both directions | Task/discovery/transfer cases and [packaging checks](../../skills/product-flow-mapping/evals/evaluation.md#current-verification-boundary); no retained model run located. | Find an omitted same-screen action without inventing a journey for decoration; verify the requested handoff answers a consumer's question. |
| [route-subagents](../../skills/route-subagents/SKILL.md): bound authorized work, routing, ownership and integration | Prospective decisions and [hook/routing machinery](../../skills/route-subagents/evals/evaluation.md); no retained full-chain skill comparison located. | Observe useful dispatch and integrated delivery against a legitimate local-work control, including coordination, repair and verification costs. |
| [skill-evaluation](../../skills/skill-evaluation/SKILL.md): diagnose failure layers and preserve comparable measurement | [Evaluation-decision cases](../../skills/skill-evaluation/evals/evaluation.md), workflow specifications and executable toy controls; no located model comparison of this skill. | Distinguish a changed grader from an improved method and a hard failure from a valid alternative. Corpus ownership does not make every stored workflow a test of this skill. |
| [technical-writing](../../skills/technical-writing/SKILL.md): select content for the reader and review the delivered artifact | [Retained baseline/candidate outputs](../../skills/technical-writing/evals/relevance-study.md#results) with bounded comparative support; preservation tests establish narrower structural properties. | Extend to a new document family with necessary explanatory detail and a clear valid control; add ordinary prompting if testing the value of the skill itself. |
| [text-writing](../../skills/text-writing/SKILL.md): compose for purpose while preserving retained or required meaning | [One recorded email pair and an explicit preservation control](../../skills/text-writing/evals/evaluation.md#selection-and-preservation-alignment--2026-10-08); both email conditions passed. | Test an uncued writing task against a preserve-all or copyedit control, checking commitments and conditions rather than preferred wording. |

### What the retained writing comparisons establish

The [2026-10-08 study](../../skills/technical-writing/evals/relevance-study.md) compares changes against **an earlier Assay method**, commit `1dbb7435d5349cb00cb4a2c8ffb5e00a2d703c03`. It does not compare skilled execution with ordinary prompting without a skill. At the reviewed revision, technical-writing's runtime matches the selected **D** snapshot and text-writing matches **text-correction**. The [evidence record](../../skills/technical-writing/evals/relevance-evidence.json) retains source and method identities, variant patches, packet manifests, output texts and assessment history. The census reproduced the recorded hashes for **all 25 output texts and all six method maps**, and matched the reviewed runtime files to D and text-correction. Hash agreement establishes byte consistency, not model identity, correct grading or access isolation.

Attribution to the actual variant matters. The [results and exposure record](../../skills/technical-writing/evals/relevance-study.md#task-families-and-exposure) distinguishes the following observations:

- **D on the Tolmach review, w04:** the baseline missed two content-selection defects; D identified them. This was an exposed incident diagnostic. B had already detected the defects; C's report then exposed repetition, which informed D's more explicit finished-report check.
- **D on the museum review, f03:** this task was separately authored after D's source freeze and paired with the baseline after selection. Both found the substantive defects; D avoided the baseline's surplus inventory of unaffected passages. This is one new paired transfer observation, not a population estimate or proof of an independent execution environment.
- **D on the export guide, f01:** its later run was an exposed regression after C's held-back output revealed a duplicate claim. D preserved the required meanings, with a minor source-footer note retained in the assessment. It is not another unseen final result. The printer control and broader drafting observations belong to C or earlier variants, not D.
- **Text-writing on t01:** baseline and text-correction both selected appropriate recipient-facing facts. The correction-only preservation control retained every explicitly required fact. These observations support compatibility on those tasks; they demonstrate **no comparative behavioral gain** for the text-writing correction.

The study records fresh child contexts with requested `gpt-6.1-sol` and `high`, but no independently observed resolved model revision, complete file-read trace, natural discovery result, tokens, quota, cost or comparable latency. The filesystem was shared and bounded by instructions. Independent review contributed to selected assessments, but did not make the environment isolated or remove shared assumptions. Earlier adverse outcomes and oracle corrections remain in the record. The published cases are now exposed working regressions, regardless of their historical reserved roles. See [execution conditions](../../skills/technical-writing/evals/relevance-study.md#execution-design), [adverse results](../../skills/technical-writing/evals/relevance-study.md#adverse-results-and-their-disposition) and [reproduction limits](../../skills/technical-writing/evals/relevance-study.md#published-assets-and-reproduction).

## What outside research adds

The review used both available web search engines, exact Assay/repository-name
searches, and targeted searches for skills, repository instructions, planning,
external feedback, routing and multi-agent execution. It followed primary papers
to methods, results, appendices and relevant released code. No external study of
Assay's own effectiveness was located in that bounded search. This is not a
systematic review, an exhaustive absence claim or an independent rerun of the
papers. The [foundational studies](README.md) supply context; this assessment
checks the narrower transfer question against the versions below.

The rows deliberately preserve different interventions, baselines and outcome
units. They cannot be averaged into an Assay effect size. `pp` means percentage
points, not relative percentage improvement.

### Similar interventions: skills and repository instructions

| Primary source and checked version | Comparison and reported result | Limits that change its interpretation |
| --- | --- | --- |
| [SkillsBench](https://arxiv.org/html/2602.12670v4), Li et al., v4, 2026-06-14; §§3–5, Tables 2–3 and 16, Appendix N | 87 tasks, 18 model/harness configurations, three selected trials per condition. Curated skills raise the main mean verifier reward from 33.9 to 50.5 (+16.6 pp). Strictly solved trials are separately reported as 31.3 to 47.7. | Task-matched, high-quality skills and selection against no-separation tasks limit transfer to a general method collection. Main “PassRate” includes fractional rewards. Healthy-first selection excludes some attempts, and eight configurations lack reported dollar costs, limiting operational cost inference. No length-matched control; comparisons of different task groups do not identify an optimal skill count or length. |
| [SWE-Skills-Bench](https://arxiv.org/html/2603.15401v1), Han et al., v1, 2026-03-16; §§3–4, Table 2 | Claude Code/Haiku 4.5, 49 skills, 565 generated repository tasks. The unweighted mean of per-skill binary pass rates is 89.8→91.0% (+1.2 pp), with reported mean token overhead +10.5%. Thirty-nine skills have zero observed delta, seven positive and three negative. | Twenty-four skills score 100% in both conditions. Requirements and tests are model-generated and skill-matched; expensive repositories are excluded. No repeated-run uncertainty is disclosed. Placement descriptions differ, and actual usage was not independently audited here. The headline is not a pooled task proportion; zero observed change does not prove irrelevance. |
| [Evaluating AGENTS.md](https://arxiv.org/html/2602.11988v3), Gloaguen et al., v3, 2026-09-29; §§3–5, Tables 1–3 | Four configurations on 300 SWE-bench Lite and 138 CTXbench tasks. Generated files change mean resolution by −0.5/−2 pp (`p=.87/.37`) and raise mean cost by 20%/23%. Developer files add 2.4 pp on CTXbench (`p=.21` versus none), also at higher cost. | One completion per condition/task; Python repository repair. These nonsignificant resolution differences do not establish equivalence, harm in every case or absence of maintainability benefits. Following extra instructions can add work without a demonstrated success gain. An AGENTS file differs from conditionally selected Assay skills. |
| [On the Impact of AGENTS.md](https://arxiv.org/html/2601.20404v2), Lulla et al., v2, 2026-03-30; §§3.1–4, Table 1 | GPT-5.2-Codex on 124 small PR tasks from ten content-selected repositories. With root instructions, median time falls 28.64% and median **output** tokens fall 16.58% (both reported `p<.05`). | Reported median total tokens rise 1.29%. Correctness is explicitly outside scope; a 50-task sanity check only excludes obvious trivial outputs. Tasks derive from PR diffs. This is a useful efficiency counterpoint, not established quality-preserving, total-token or billed savings. It uses different tasks and metrics from Gloaguen's study. |
| [Skills in the Wild](https://arxiv.org/pdf/2604.04323v1), Liu et al., v1, 2026-04-06; §§3–4, Figure 1 and Table 2 | 84 SkillsBench and 89 Terminal-Bench tasks, three repeats, three model/harness combinations. For Opus 4.6, curated skills yield 51.2 versus 35.4 without skills; retrieval without curated skills falls to 38.4. Kimi and Qwen means in the latter setting are slightly below their no-skill baselines. | Shares SkillsBench tasks with the original benchmark. No reported uncertainty establishes those small negative differences as harm. The [released aggregator](https://github.com/UCSB-NLP-Chang/Skill-Usage/blob/03446d16f7b659ccc93ac5bd512f62e9b7fabb45/scripts/calculate_results.py), inspected at an April 8 commit, averages float rewards and excludes unscored failures; original raw trials were not reconciled. Query-specific refinement adds an exploration pass without an equal-compute retry control. |
| [SkillCorpus](https://arxiv.org/html/2607.15557v6), Wang et al., v6, 2026-08-26; §4, Table 1, Limitations and Ethics | Curated corpus plus learned retrieval/selection; two Qwen backbones across two harnesses, three repeats, 407 tasks. Pooled SkillsBench **binary** success gain is +7.5 ± 2.3 pp (standard error). Other benchmarks use continuous or hybrid judging. | A bundled pipeline rather than a skill-format ablation. Different investigators still reuse SkillsBench tasks. The paper reports no task-specific contamination audit; curation judgments lack human validation, and some task-level judgment noise is large relative to effects. The uncertainty is not a 95% confidence interval. |

These studies support testing relevance, selection and unnecessary instruction
overhead. They do not supply a numeric expected benefit for Assay. In particular,
the realistic-retrieval result does not contradict the curated-skill result:
the available material, selection route and task match changed.

### Revision evidence and adverse mechanisms

| Primary source and checked version | Observed comparison | Limits and transfer |
| --- | --- | --- |
| [Agent Skill Evolution](https://arxiv.org/html/2610.04832v1), Wang et al., v1, 2026-10-04; §§3.2–3.4, 5.2, 6.2, Tables 4–5 and 7 | Revised versus old skill bodies on 80 rule-needing tasks from 57 repositories. Required actions rise 23 pp across four agent configurations; blinded human correctness gains 10 pp [95% CI 4,17] across the three judged configurations. Sonnet's 6 pp [−6,18] is inconclusive. | Mechanically checkable directives and tasks generated to require them select for the revision's relevance; reasoning modes are disabled. Unclear judged pairs are excluded. The approximately 50% episode-token overhead compares **old body with metadata only**; revised-versus-old changes are −2.3% to +3.0%, all intervals crossing zero. On-demand loading retains about half the action gain. This supports selected revisions, not adding rules everywhere. |
| [Probe-and-Refine](https://arxiv.org/html/2606.20512v2), Shepard and Albrecht, v2, 2026-06-19; §§3–4, 6–9, Tables 4–5, 9, 11–12 | Qwen 3.5-35B-A3B, 500 SWE-bench Verified tasks, 200-step budget: four executions yield mean resolution 33.0% for tuned guidance, 28.3% for static guidance and 25.5% unguided. | The executions reuse once-generated guidance; they are not four tuning replications. Deployment prompt tokens increase about 56%, plus preparation. Lower-budget and Nemotron conditions regress; transferred Qwen guidance reaches 13.2% on Nemotron. No length-matched control or resolved contamination audit. Positive evidence for one tuning setup coexists with adverse transfer. |
| [Agent Skills Can Be Harmful](https://arxiv.org/html/2608.11888v1), Dong et al., v1, 2026-08-12; §III, Tables I–II, §V, §VII-B | New Opus 4.6/OpenCode executions on reused skills-benchmark tasks yield 307 selected adverse cases: 125 functional and 182 efficiency regressions. Efficiency cases require both token/time ratios above one and at least one above two. | The 307 are selected from adverse candidates, not a neutral prevalence or net-effect sample. The 20,664 figure counts potential comparisons, with tasks/runs reused. Manual attribution and stochastic variation limit causality; repeated attribution is not repeated task execution. The taxonomy motivates checking excessive procedure and incompatibility, not claiming general harm from independent new tasks. |

These additional studies preserve the distinction between a skill's availability,
a change to a selected directive, and tuning an entire repository context. New
investigators or executions can add evidence while sharing the original task
corpus. No pooled effect across these units is justified.

### Mechanisms: planning, checks and delegation

| Primary source and checked version | Observation relevant to Assay | Transfer decision |
| --- | --- | --- |
| [Harness Design](https://arxiv.org/html/2609.20804v1), Fan et al., v1, 2026-09-17; §§2–4, Tables 3–4 | 176 matched settings, four models, two executable benchmarks. At the tested T4/128K setting, planning helps the weakest model by 11.6/4.5 pp at higher cost; the two strongest tested models trade small accuracy losses for lower cost, while the 120B model has mixed cost effects. Paired McNemar tests use multiplicity correction. | Preserve conditional planning and measure both completion and cost. The implemented harness intervention does not prove the value of Assay's prose or justify an always-plan rule. |
| [From Plan to Action](https://arxiv.org/html/2604.12147v3), Liu et al., v3, 2026-08-07; Figures 5, 11 and 15 | 21,120 trajectories, four models, eight plan variants. Standard planning helps in the studied setup; additional early phases can hurt. The displayed reminder results are mixed. | Do not import a universal five-step reminder. Figure 15b in the [PDF](https://arxiv.org/pdf/2604.12147v3), printed page 10, shows R1 resolved cases falling 196→13 while the other three models improve, despite prose describing consistent improvement. This unresolved plot/prose conflict prevents that transfer. |
| [Scaling Agent Systems](https://arxiv.org/html/2512.08296v3), Kim et al., v3, 2026-04-08; §§4–5, Appendix B | 260 configurations, five architectures, six benchmarks. Centralized delegation helps the finance task, while every reported multi-agent variant declines on PlanCraft and the tested SWE-bench subset. | Retain task-structure and integration criteria. Coding subsets have only 20 instances each; cost coverage differs by benchmark. Neither a universal delegation advantage nor a fixed routing threshold follows. |
| [RouteLLM](https://arxiv.org/html/2406.18665v4), Ong et al., v4, 2025-02-23; §§3.2, 5.1–5.3 | Preference-trained query routing is compared with random routing. Data augmentation matters for transfer beyond the training distribution. The main trade-off includes the fraction of strong-model calls. | Calibrate routing locally against a simple comparator. Strong-call fraction is not total advisor, dispatch, integration, repair and verification cost; it cannot establish Assay workflow savings. |
| [Intrinsic self-correction](https://arxiv.org/html/2310.01798v2), Huang et al., ICLR 2024; §§3–5 | On the studied older models and reasoning tasks, unsupported self-correction often fails or degrades an initially correct answer; oracle-stopped correction is a different condition. | Separate self-review from independent evidence. Do not turn a result on older models into a timeless inability claim. |
| [CRITIC](https://arxiv.org/html/2305.11738v4), Gou et al., ICLR 2024; §4, Tables 1–2 | Tool-assisted feedback can improve some reasoning/program outcomes, but the tool condition is not uniformly beneficial across model/task cells. | Preserve external consumer checks while checking the oracle itself. A tool call or passing weak assertion is not automatic correctness. |
| [SCoRe](https://arxiv.org/html/2409.12917v2), Kumar et al., v2, 2024-10-04; §6.1, Table 2 | Multi-turn reinforcement learning improves self-correction on the studied math and code tasks. This changes model weights and uses training rewards. | A counterexample to universal self-correction pessimism, not evidence that a prompting-only Assay method works. |

The practical transfer is already represented in Assay: conditional depth,
task-based planning, checks at real consumer boundaries, calibrated evaluators,
preserved valid controls and accounting for complete delegated work. No new
runtime rule is justified by importing these effect sizes. The literature also
does not justify deleting those conditions after an inconclusive local pilot.

## New comparison: explicit Assay availability versus the common host

### Frozen question and allocation

The comparison asks whether adding the current Assay collection changes the
delivered result on the existing five
[workflow execution groups](../../skills/skill-evaluation/evals/workflow-execution.md).
It tests a collection-level instruction to use applicable methods. It does not
isolate individual skills or measure the skill-evaluation method merely because
that skill owns the corpus.

The original [protocol](skill-effectiveness/protocol.json) was frozen before the
first trial at `2026-10-08T20:45:16.294663+00:00`. Its SHA-256 is
`5643723bf27109524b3250f53ae15e74e3b0c9ea3653f7c9bb26afc7eaa9a1ed`.
All five public synthetic groups were included, with one fresh execution per
arm/group: **ten allocations, no outcome-driven reruns or tuning**. Debugging
within a trial remained part of that trial. Seed `20261008` randomized case and
within-pair order; executions were sequential.

| Setting | A | B |
| --- | --- | --- |
| Task | Same frozen input-only case and separate writable project copy | Same |
| Common instructions and tools | Inherited host guidance plus the bounded task dispatcher | Same |
| Method condition | Explicitly do not load Assay or other skill packages | Explicitly inspect the current Assay collection and use applicable entrypoints/references |
| Requested model/effort | `gpt-6-astra`, `ultra`; fresh context, `fork_turns=none` | Same |
| Trial authority | Case-controlled edits; no worker delegation, browsing, installation or publication | Same |
| Method bytes | No Assay in the task packet | All 14 catalogued skill directories, including runtime helpers/assets, excluding `evals/` and bytecode |

A is a strong common-host comparator, not a bare model without methodological
guidance. The host instructions were inherited rather than fully exported, and
may overlap Assay's criteria. B adds both method availability and an explicit-use
instruction; there is no length-matched placebo. Requested model settings are
recorded, but a resolved model version is not independently attested.

### Inputs, access and measurements

The existing `tools/eval_assets.py prepare` generated frozen task-only packets.
Their manifests and the separately retained runtime manifest identify the
bytes. The preparer's documented method snapshot is narrower than the complete
runtime collection, so this comparison supplied a separate complete runtime
copy rather than treating that snapshot as a full installation. Rubric,
metadata, other cases and prior responses were excluded from task packets.

Fresh contexts and separate projects did **not** enforce filesystem isolation.
Read restrictions were instructions; other workspace paths remained technically
accessible. The evaluator and protocol designer had seen all cases. These are
public working inputs, with no hidden test or independent production sample.
Complete host-authenticated file-read/tool traces were unavailable, so natural
discovery, actual branch loading and treatment adherence remain unverified.

The fixed [rubric](../../skills/skill-evaluation/evals/workflow-execution-rubric.json)
was used for content and required outcomes. Artifact replay ran the real public
operations on disposable copies, with independently stated expected values.
It inspected the whole final project difference, preserved rows and allowed
operations, and challenged delivered regression tests by restoring the original
defect in a separate copy. Extra input variants diagnose hardcoding and
preservation; they are evaluator controls, not new task groups or extra trials.
The existing
[fixture calibration](../../tools/test_workflow_execution_fixtures.py)
also distinguishes faulty and repaired programs.

WX-05 received separate condition-blinded model grading of answer content
against its original brief and rubric, frozen before unblinding. It used the
same requested model/effort and is not an independent human replication. The
coordinator checked final bytes for both answers; the blind grading did not
infer process compliance from an unchanged snapshot. Objective artifact replay
was unblinded. No model judge score is substituted for executable checks.
The WX-05 judgment used one presentation without repeated grading or an
order-sensitivity check; it does not establish judge reliability.

### Results

Results are recorded in [outcomes.json](skill-effectiveness/outcomes.json).
The table separates the requested outcome from differences in supporting work.
“Met” below concerns observed artifacts and answer content, not authenticated
compliance with every process restriction.

| Case and consumer boundary | A | B | Difference supported by retained artifacts |
| --- | --- | --- | --- |
| WX-01: public CSV export, stable case-insensitive order with all rows and fields | Met | Met | Both delivered the caller fix and a public-command regression test. Each suite passed on the delivered source and rejected the original fault. |
| WX-02: inert README spelling correction | Met | Met | Both limited the final change to the requested spelling; command and meaning preserved. |
| WX-03: tenant authorization and meaningful regression protection | Met | Met | Both preserved matching-admin deletion and rejected all three denied combinations without record mutation. Each regression suite rejected the original fault. |
| WX-04: dynamic renderer/configuration/CSV pipeline reaches stdout and file | Met | Met | Both repaired the connected defects. B additionally retained a regression test; A retained the repaired artifact and a final-command record. |
| WX-05: read-only assessment of retained verification after a source change | Met | Met | Blind grading found both answers substantively correct. Both retained arithmetic evidence, identified stale and weak report evidence, and returned the permitted review. Both final projects equal their inputs. |

All ten allocated trials completed. **Both conditions met the observed required
outcome in each of the five groups: A 5/5, B 5/5.** There was no observed advantage
in required task outcomes. The useful difference in WX-04 was a retained
public-command regression test: it passed on B's delivered source and failed
when replay restored the original invalid renderer. That is evidence about the
test's discrimination, not proof that adding Assay caused a general maintenance
benefit. No repeat, new failure distribution or cost observation establishes
that broader claim.

Replay confirmed the exact `Orders: 2; total: 15\n` stdout and file for both
WX-04 artifacts, and a separate three-row input produced `Orders: 3; total: 18\n`.
The CSV checks retained duplicate rows, quoted/multiline fields and casefold
ties. Both WX-03 projects also retained two bytecode cache files after their
reported test commands; those files remain in the artifact inventory. There
were no missing trial results, and packet, dispatch and runtime bytes matched
their frozen identities after execution. Final byte equality does not establish
the absence of transient writes or outside reads.

### What this sample cannot establish

One execution per arm/group does not estimate model variance. Five heterogeneous,
purposively selected public toy groups do not estimate a production task
distribution, an individual-skill effect or portability across hosts/models.
Repeated controls within a group are not independent sample units. A result in
which both arms meet the task is neither superiority nor equivalence evidence;
a saturated task set has little ability to distinguish strong executors.

Billed tokens, monetary cost, subscription quota and comparable end-to-end
latency were not available. They remain missing values, not zero. Task wall time
would mix orchestration and other activity and is not reported as an efficiency
estimate. A longer answer or an additional test is not by itself improvement or
waste. Retained command files support narrow claims but are not authenticated
complete worker traces; successful replay validates an artifact now, not every
claimed earlier command.

## Repair justified by the assessment

The evidence census exposed a concrete structural gap in
[`tools/eval_assets.py`](../../tools/eval_assets.py): the common checker and
inline preparer omitted `ui-delivery`, although its main input/rubric pair fits
the supported schema. The labelled UI triggers and legacy audit triggers also
escaped the common structural check. This is a validator defect, not evidence
that the associated methods are ineffective.

The repair adds UI to the existing paired-corpus path and validates the two
retained labelled-trigger formats separately, without changing their schema.
Labels remain evaluator-only: the input-side validator still rejects them before
allocating an executor packet. Existing pair, metadata and duplicate-ID checks
are reused; no model runner or dependency is added.

The new regression tests failed against the original implementation: valid UI
preparation was rejected, and malformed omitted corpora were accepted. With the
repair, all 19 focused tests passed. The suite includes restored-valid controls,
rejects string/integer substitutes for Boolean labels, checks malformed prompts
and mismatched IDs, and verifies that labels cannot enter prepared task inputs.
Both owner gates passed for the repair, and a separate focused review found no
confirmed defect. These results support the tool contract only. Runtime skill
instructions, catalog membership and version are unchanged.

## Decisions and the next discriminating work

**Retain the methods without claiming collection-wide benefit.** Existing
conditional guidance is consistent with relevant mechanisms, and the evidence
does not support a blanket rewrite. Preserve the positive writing observations
at their actual variant/task scope and the null comparisons alongside them.

**Fix the demonstrated checking omission.** This improves coverage of the stated
validation contract. It does not convert structural validation into behavioral
evaluation or repair an unmeasured discovery problem.

**Use targeted comparisons before broader claims.** The all-skill matrix names
candidate discriminators. A more informative next study should sample distinct
real task families from the intended workload, recover the original requirements
without leaking solutions, and include difficult cases plus legitimate simple
tasks. Native discovery and explicit loading need separate conditions. Record
the effective host, model, permissions and actual read/dispatch events when
available. Keep artifact acceptance, false rejection, user corrections,
authorized effects and complete cost as separate outcomes.

For a material candidate change, freeze baseline, treatment, rubric and budget
before execution; separate development groups from untouched final groups and
avoid sharing an incident/template across splits. Calibrate objective checks
with a known fault and a valid alternative; for judgment-dependent qualities,
use blinded review and retain disagreements and corrected grading. Retain every
allocation, including setup failure and retries, with separate capability and
operational denominators. Choose repetition and sample size from the claim,
minimum useful effect and available precision, not a universal case-count rule.
Report paired differences with uncertainty only for the population and grouping
the design supports. A prespecified quality/cost trade-off is needed before
declaring a slower but more careful workflow better.

This is a proposed extension of the evidence, not a campaign executed by this
PR. The existing [paired-pilot](../../skills/skill-evaluation/references/paired-pilot.md)
and [evaluation-design](../../skills/skill-evaluation/references/eval-design.md)
procedures already own these choices; the report adds no parallel policy.
The companion [comparison guide](../how-to/compare-skills.md) distinguishes
whole-collection, named-skill, revision, discovery and ablation studies. Its
general condition labels differ from this experiment: here B is the explicit
condition, corresponding to the guide's forced diagnostic C.

## Evidence access and reproduction

The public source records the frozen protocol, source identities, assessment
rules and derived outcomes. The separate evidence archive retains task packets,
runtime bytes/manifests, dispatches, final responses, final projects, available
worker command records, blind grading and artifact replay. Responses were
preserved from returned final messages; they are not exported, authenticated
host transcripts. Raw records stay outside source and future executor inputs.
Archive identity and availability are recorded with the final results.
The separate file is `assay-skill-effectiveness-evidence-2026-10-08.zip`
(694,499 bytes; SHA-256
`3bf22dd1c412c4113f8162cbad49847ac1e4ce2f6d4f4f31a0d5a0d667f51ba5`).
It was saved for the requesting maintainer; this repository does not provide a
public download of the raw archive. Its internal manifest was checked against
all 353 retained files.

With the archive, run its `replay.py` against this checkout and the extracted
comparison directory to repeat the artifact checks. It does not launch models
or overwrite retained projects. The absolute working paths in original
dispatches are historical; a fresh behavioral replication must prepare new
packets and record its own paths and host conditions. Original model executions
cannot be reconstructed from hashes, and the public derived record alone does
not substitute for access to the retained artifacts.

```text
python -B /path/to/comparison/replay.py /path/to/assay-checkout /path/to/comparison /path/to/new-replay.json
```

This report extends the [initial evidence/protocol proposal](https://github.com/Muratovnik/assay/tree/221e002981b2087a9c40867eaedf86c7e9f6e14a).
Its companion guide is retained. The integration adds executed comparisons and
historical writing evidence, distinguishes fractional from binary success and
output from total tokens, and separates the cost of revising a body from the
cost of loading it. The original proposal remains in Git history.

The source-level repair is reproducible with the existing isolated tooling
environment and owner commands:

```text
python -B -m unittest tools.test_eval_assets
python -B tools/check.py --all
python .github/relkit.pyz audit
```

These checks qualify their named utilities and repository boundaries. They do
not rerun this behavioral comparison or establish a general effectiveness score.
