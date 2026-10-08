# Effectiveness of Assay skills: comparative evidence and measurement gaps

**Status:** evidence synthesis and repository audit, **not an executed model experiment**.  
**Assay source:** [main at 94c517b0aac9ba2575086bf9aead1cc828aadb0d](https://github.com/Muratovnik/assay/tree/94c517b0aac9ba2575086bf9aead1cc828aadb0d).  
**External search/review:** 2026-10-08. **Outcome:** no measured Assay-specific skill lift, ranking or return on investment can currently be established.

## The answer the evidence supports

There is no defensible statement that Assay's 14 skills improve real task outcomes by a particular amount. The repository supplies substantive task/rubric fixtures and non-model validation, but not paired executions of a fixed model with versus without each skill or the complete collection. The project's own [evaluation contract](../evaluation.md) makes this limitation explicit. A passing validation workflow certifies neither model discovery nor task quality.

Outside Assay, there is **positive evidence that curated skills can help**, and **counterevidence that many software-engineering skills add little or impose overhead**. These results do not cancel each other: they involve different tasks, selection procedures, baseline success rates, evaluators and harnesses. Treating the larger improvement as a guaranteed Assay benefit, or the smaller one as proof that Assay is useless, would commit the same transfer error.

The appropriate current disposition is **retain the existing methods without claiming quantified effectiveness; perform controlled paired comparisons before behavior-changing edits or outcome claims**. A no-change outcome for an individual skill is acceptable. The runnable study procedure and publication criteria are in [Compare Assay skills](../how-to/compare-skills.md).

## 1. Direct published comparisons

### Search and study boundary

This is a **targeted narrative review, not a systematic review or meta-analysis**. On 2026-10-08 the research used current-version arXiv HTML full texts, university and Microsoft Research publication pages, searches for agent-skill outcome benchmarks, skill-induced failures and revisions, and counterevidence about repository context files. Included papers had a describable task population and a comparator or differential method relevant to skills, outcomes, cost or activation. Explicitly distinguished are **direct skills**, **skill revisions and failure analyses**, and **adjacent context-file interventions**. The study unit is an underlying experiment/dataset, not each paper quoting the same benchmark.

The search did not audit all scholarly indexes, references, retractions or unpublished reports; it does **not** establish that these are all available studies. Provider how-to pages are treated as methodology proposals, not independent estimates of Assay efficacy. Older versions of an identified study were not pooled with newer ones; each version, denominator, comparator and reported unit is named below. Null and harmful results were actively retained rather than excluded for failing to show a gain.

The following are reports **about other interventions**. The numbers are as reported by their authors; the papers' experiments have not been independently reproduced for this document.

| Evidence unit (version) | Intervention and comparator | Reported outcome | Why it cannot be an Assay score |
| --- | --- | --- | --- |
| [SkillsBench, arXiv:2602.12670v4, 14 Jun 2026](https://arxiv.org/html/2602.12670v4) | Curated skills vs no skills on 87 tasks, eight domains, 18 model–harness configurations | Mean pass rate 33.9% without, 50.5% with; **+16.6 percentage points**; heterogeneous +4.1 to +25.7 pp by configuration | Skill bundles and verifiers are from SkillsBench, not Assay. Tasks were curated for discriminative power: the construction process rejects those with no measurable between-condition separation. The resulting mean is not a production-frequency-weighted gain. |
| [SWE-Skills-Bench, arXiv:2603.15401v1, 16 Mar 2026](https://arxiv.org/html/2603.15401v1) | 49 publicly available SWE skills, about 565 real-repository task instances at pinned commits; automatic discovery vs absent skill in Claude Code with Claude Haiku 4.5 | Mean success 89.8% without vs 91.0% with, **+1.2 percentage points**; **39/49 skills show no measured pass-rate gain** (24 already perfect in both conditions), seven improve, three worsen; mean tokens 303K to 335K (**+10.5%**) | High baseline success and many saturated cases reduce possible uplift. One model/harness, particular skill selection, generated acceptance machinery and an outcome defined by executable tests; not a comprehensive measure of code quality or Assay behavior. |
| [Evaluating AGENTS.md, arXiv:2602.11988v3, 29 Sep 2026](https://arxiv.org/html/2602.11988v3) | Repository-level context files vs no context across coding agents and two datasets | No statistically significant overall success improvement; inference cost rises by **over 20% on average** in evaluated configurations; some human-authored guidance fares better than generated guidance | **Not a skill experiment**: always-present repository context differs from conditional Assay SKILL.md discovery. It is relevant as a caution about instructions, unnecessary work and cost, not a direct estimate of skill impact. |
| [On the Impact of AGENTS.md Files, arXiv:2601.20404v2, 30 Mar 2026](https://arxiv.org/html/2601.20404v2) | With vs without repository context over **124 PRs in 10 repositories** | Associated with **28.64% lower median runtime** and **16.58% fewer output tokens**, with comparable task completion in the studied setting | **Different experiment, different cost components and outcomes** from the negative AGENTS.md study above; neither measures a conditional Assay skill. The contrast argues against a universal context-overhead law. |
| [Agent Skills Can Be Harmful, arXiv:2608.11888v1, 12 Aug 2026](https://arxiv.org/abs/2608.11888v1) | Differential triage of matched skill-guided and reference runs drawn from SkillsBench and SWE-Skills-Bench | Authors categorize **307 observed adverse cases**: 125 functional failures and 182 efficiency regressions; 67 excessive-verification and 30 heavy-pipeline instances among classified excessive-procedure cases | **Not 307 independent tasks or a failure rate**. Reuses earlier benchmarks and therefore adds mechanism/trace evidence, **not independent efficacy sampling**. Attribution is conditional on paired successful or cheaper references. |
| [Agent Skill Evolution, arXiv:2610.04832v1, 4 Oct 2026](https://arxiv.org/html/2610.04832v1) | First vs last skill revision: 2,608 revision pairs in 3,159 skills; controlled rule-change probes across 21 models and four sandbox agents | Added checkable rules increase required-action rate by **+0.23 on average across four agents**; blind-judged final correctness rises **+0.10 across three assessed agents**. Actual on-demand discovery retains about **51%** of the action gain; loading a full skill body increases episode tokens **about 50%** in these conditions | Recent preprint. Selects mechanically checkable added/deleted rules, often explicit commands or paths; the outcome is **revision-specific**, not all-skill/no-skill uplift or general engineering quality. Some rule improvements cost tokens without detected benefit. |
| [Probe-and-Refine, arXiv:2606.20512v2, 19 Jun 2026](https://arxiv.org/abs/2606.20512v2) | Iteratively tuned repository guidance vs initial static guidance and no guidance, four independent trials of a fixed SWE-bench Verified setup with Qwen3.5-35B-A3B | Mean solve rates **33.0%** (tuned), **28.3%** (initial guidance), **25.5%** (unguided); reported gains primarily improve patch generation/coverage rather than per-patch precision | This is evidence for **controlled guidance tuning in that environment**, not evidence that any Assay skill or generic extra instructions deliver the same improvement. |

### What changes the interpretation

- **Population and selection.** SkillsBench explicitly selects tasks where skills can make a detectable difference. SWE-Skills-Bench samples skills from a different ecosystem and includes numerous tasks with both arms already passing. Neither distribution is the observed distribution of Assay's users.
- **Conflicting efficiency observations.** The Gloaguen and Lulla AGENTS.md studies report opposite average cost directions. Their repositories, tasks, run conditions and token/time measures differ; the existence of both prevents a categorical rule that repository context always increases or always decreases work.
- **Evidence dependence.** The Microsoft Research failure taxonomy analyzes traces from the same two skills benchmarks above; its 307 selected adverse cases add failure mechanisms but must **not** be double-counted as another independent sample for a pooled pass rate.
- **Revision versus availability.** The October 2026 evolution work is unusually direct about added rules and automatic loading, but its intervention is a checkable rule **changed between skill versions**. A gain in rule compliance or required actions is not automatically a gain in task-level correctness or a recommendation to add a rule to Assay.
- **Outcome construct.** Executable correctness, a graded document, an audit's source fidelity, a good architecture decision, and timely authorized delivery require different oracles. Neither token count nor compliance language measures the last four by itself.
- **Treatment composition.** Skill availability, automatic discovery, actual reading, following the relevant criterion, access to extra documents and tool usage are distinct. A test that forces a skill does not estimate natural discovery.
- **Confidence.** Both skills benchmarks are public arXiv reports; published aggregates are not independent replication of each other. AGENTS.md uses a different intervention. No meta-analytic pooled effect is justified.
- **Cost and negative effects.** Overhead can accompany improvement, no change or regression. A narrow gain on difficult cases may be valuable; a repetitive process on trivial cases may be harmful.

The source status and framing follow the existing [research-quality foundation](foundations/research-quality.md) and [LLM behavior-control foundation](foundations/llm-reasoning-control.md), whose methodological models are not Assay-specific test results. [Anthropic's skill-creator guide](https://claude.com/resources/articles/improving-skill-creator-test-measure-and-refine-agent-skills) illustrates a relevant test-and-refine workflow, but is guidance from a skill provider, not a separate efficacy trial of this repository.

## 2. Current Assay evidence inventory

At the pinned revision, [catalog.toml](../../catalog.toml) lists **14 skills**. The table counts entries in each skill's **primary** cases/evals array; it deliberately excludes auxiliary collections, discovery/trigger suites, case variants and regression fixtures. These are **449 test specifications, not 449 executed or independent tasks**. The case population is synthetic or manually assembled and not measured as a representative sample of user work. Its breadth is a coverage lead, not an effect estimate.

| Skill | Primary case specifications | Useful outcome requiring a paired observation | Failure and valid-control pair |
| --- | ---: | --- | --- |
| code-change | 14 | Correct changed executable artifact and preserved contracts | Unsafe behavior caught / equivalent safe existing mechanism retained |
| evidence-research | 32 | Accurate claim-to-source conclusions and bounded uncertainty | Unsupported quantitative claim rejected / properly qualified claim retained |
| implementation-planning | 18 | Ready, traceable dependency units with acceptance tied to actual constraints | Missing prerequisite detected / simple ready edit not delayed |
| independent-audit | 31 | Correct and evidence-bound audit verdict with no unapproved mutation | Material defect detected / legitimate implementation not falsely rejected |
| product-flow-mapping | 20 | Accurate action/state/scenario coverage in the requested handoff | Missing consequential path found / non-navigation action not invented as transition |
| research-driven-change | 31 | Research decision actually reaches authorized change and requested delivery | Unsupported promotion blocked / bounded change completed without excessive ceremony |
| route-subagents | 33 | Valid task-sufficient route and lower measured whole-chain cost at held quality | Unjustified expensive/unsupported selection avoided / user-explicit route preserved |
| skill-evaluation | 24 | Correct diagnosis and comparative result without evaluator leakage | Inflated improvement claim refused / measured useful candidate accepted |
| software-architecture | 21 | Suitable boundaries and contracts with justified total costs | Destructive speculative abstraction avoided / necessary reusable boundary accepted |
| technical-writing | 45 | Reader can use the documented workflow and its meaning remains source-true | Unsupported prerequisite removed / needed prerequisite preserved |
| test-audit | 12 | Correct identification of vacuous or unsound tests without false findings | Weak oracle exposed / justified narrow test retained |
| test-writing | 8 | Regression test rejects plausible defect and admits compatible valid behavior | Bad implementation rejected / equivalent valid implementation passes |
| text-writing | 38 | Audience-fit prose that preserves required facts, scope and meaning | Fabricated certainty removed / important qualifier retained |
| ui-delivery | 122 | Functional/rendered artifact supports scenarios, states and actual interactions | Real failure/recovery state checked / unaffected supported flow retained |
| **Total** | **449** | **No model outcomes measured here** | **Controls are proposed observations, not new passed tests** |

Input locations are under each named **skills/[name]/evals/** directory, normally **cases.json**; independent-audit uses **evals.json**. Separate activation collections or files occur for most skills. The route-subagents primary cases contain no separate activation list at this revision; activation is also exercised by host/tooling tests such as **tools/test_delegation_activation.py**, which are not paired model task executions. The inventory has not independently verified every rubric's content, semantic overlap, difficulty or risk of grading bias.

### What the shipped infrastructure already contributes

- **tools/eval_assets.py** validates packet structure and prepares inputs without including evaluator-only rubrics and sidecars. Its tests check that particular filtering behavior, not that a model never accesses source keys by another route.
- **skills/independent-audit/evals/prepare_case.py** and **verify_packet.py** support a frozen packet with content digests. Digest equality does not enforce read isolation.
- **tools/native_smoke.py** examines captured loader evidence where a qualified mapping exists. At the examined revision Codex skill activation is reported as unverified by this method.
- **skills/skill-evaluation/references/paired-pilot.md** and **eval-design.md** already define comparisons, control cases, evidence split and grader calibration.
- **skills/skill-evaluation/evals/workflow-execution.md** contains five constructed execution/assessment comparisons; **tools/test_workflow_execution_fixtures.py** checks fixture faults and repairs without invoking an agent.
- A green **Check** workflow on the pinned main establishes source checks passed there. It provides no native assistant run, controlled treatment, behavioral verdict or task-cost observation.

Thus the primary gap is **evidence collection and outcome measurement**, not lack of another scoring manifesto or need for a duplicate runner.

## 3. Which comparisons can answer which questions?

| Question | Necessary contrast | May establish | Cannot establish by itself |
| --- | --- | --- | --- |
| Does installing Assay improve user work? | Default client with all allowed Assay skills naturally available vs same client without those skills, keeping project instructions and tools fixed | Whole-collection incremental effect under a named task population, model and date | A causal contribution of any individual skill or internal reasoning mechanism |
| Does a skill contribute when it is needed? | Frozen matching inputs with vs without that skill; hold applicable peer skills and all other settings fixed | Conditional marginal contribution in that chosen context | Whether automatic discovery would have selected it |
| Was automatic discovery the problem? | Natural route vs an explicitly forced, labeled diagnostic read, using the same task | Evidence about missed routing/reading when client traces support it | A production effect of the forced condition |
| Does a new revision improve a skill? | Actual previous skill bytes vs candidate bytes, with frozen task, grader and peers | Bounded local revision comparison | Effect on unseen groups, other models or other task domains |
| Does composition matter? | Full collection vs leave-one-out; optionally a predeclared pairwise interaction | Local incremental difference in the presence of others | An additive ranking of skills or unique skill contribution |
| Is the added process worth its cost? | End-to-end accepted delivery, including retry, feedback, review and corrections | Measured local quality–cost frontier | Savings inferred from fewer source lines or one agent's token count |

Never label a self-report of reading a skill as an activation trace. Read the actual result and its consumer, not just its verbal explanation. A skill may improve error detection while making immediate output longer; an apparently better average score may conceal a forbidden edit or false rejection. Hard contractual violations are separate from a soft average.

## 4. Hypotheses to test, not claimed findings

- **H1: Conditional specialization.** Skills may help more when they provide previously missing domain or process knowledge; easy tasks with strong baselines could show little incremental correctness benefit.
- **H2: Misactivation overhead.** Unnecessary activation may increase total effort and reduce task relevance; a nearby should-not-fire task is needed to detect this.
- **H2a: Relevant-skill overprocedure.** Even a correctly selected skill may induce excessive verification or a heavy pipeline. Cost regressions must be attributed from actual trajectories, not blamed on prompt length alone; pair with a cheaper accepted reference.
- **H3: Redundant criteria.** The full collection can duplicate rules across methods; removing a redundant instruction might reduce overhead, but removing a uniquely useful one could create a regression.
- **H4: Workflow interactions.** One method's apparent contribution can depend on whether discovery, planning, execution, review and publishing are already supplied by a peer or system instruction.
- **H5: Grader blind spots.** A model can satisfy a checklist, test or preferred wording without meeting a user outcome; a material claim needs evidence at the real consumer boundary.

These hypotheses are motivated by the papers, repository design and known limitations of instruction-following research, but **have not been tested as Assay effect mechanisms**. Both positive and negative results must remain publishable. An observed zero on a small pilot is *inconclusive*, not a universal finding of no effect.

## 5. Decision and next evidence

**Retain:** existing 14 skills and their conditional references; the native packet, validator and reviewer tools. No comparative evidence examined justifies deleting, merging or globally rewriting an individual skill.

**Adopt:** a version-pinned evaluation report and a practical [paired measurement protocol](../how-to/compare-skills.md) that separates real outcomes, discovery, material criteria, legitimate controls and total delivery cost.

**Do not adopt:** an externally reported efficacy percentage as an Assay KPI; a leaderboard based on case counts; a blanket rule that short skills or more skill reads must be better; extra mandatory logging/runner infrastructure; a new skill rewrite solely to have a positive change.

**Open evidence:** representative task frequencies, independent accepted-result oracles for open decisions, executable user work across task families, native skill-load traces, held-out groups inaccessible to executors, measured end-to-end costs, repeatability over models/clients and current installation settings. The absence of these records is not evidence of a negative causal effect. The exact source revision and researched external papers make these unknowns reproducible in the next study.

A small diagnosis may support a *specific repair* if it demonstrates the defect and preserves valid work. For a collection-wide or per-skill performance claim, use independent, preselected task groups, matched executions, explicit uncertainty and a holdout after selection. Record negative and inconclusive results, even when they conflict with the expectation that more instructions must help.
