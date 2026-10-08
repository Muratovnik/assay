# Catalog diagnostic for Assay skills

Evidence review date: 2026-10-08 UTC. Assay source under study:
`94c517b0aac9ba2575086bf9aead1cc828aadb0d`.

This record separates three questions: whether the evaluation machinery measures
what it claims; what Assay changes on the actual compared tasks; and what stronger
claims still need another execution environment or a different sample. Literature
about other skills informs the design; its improvements are not Assay results.

## Existing Assay evidence

The starting revision already contains behavioral evidence. Describing every
`evals/` directory as merely prepared fixtures would overlook it. The records below
have different tasks, methods, models and selection histories and are not pooled.

| Record | Retained executions | What it can establish | Important boundary |
| --- | --- | --- | --- |
| [Technical-writing relevance study](../../skills/technical-writing/evals/relevance-study.md), on main | 25 real outputs: earlier-Assay baseline 8, A 4, B 4, an ordinary-text correction 2, C 4, D 3 | Concrete output differences and regressions during one method's development | Historical versions and repeatedly exposed tasks; not 25 trials of D and not catalog-wide efficacy |
| [Durability study, PR 23](https://github.com/Muratovnik/assay/pull/23), reviewed at head `8549727763e7e5c9305d8563c5f18bb9bf76c2ba` | 52 allocations: 46 completed, 2 interrupted, 4 cancelled; 48 retained output records include partial outputs | Further candidate corrections and preserved adverse evidence | Unmerged at review time; final H has four runs. Baseline also passes both new task comparisons, so this pair establishes no advantage for H |
| [Full-catalog comparison, PR 24](https://github.com/Muratovnik/assay/blob/f951f07eb57d9d270d973a411082524d01f2b290/docs/research/skill-effectiveness.md#results), reviewed at head `f951f07eb57d9d270d973a411082524d01f2b290` | 10 completed executions over five workflow groups, one no-Assay/full-catalog pair per group | Both arms met the observed required artifact/content outcomes in all five groups; the full-catalog WX-04 artifact additionally retained a discriminating public-command regression test | Unmerged at review time; explicit full-catalog exposure, public synthetic tasks, shared filesystem, incomplete process/loading observability, and no measured cost or equivalence conclusion |
| [Catalog diagnostic protocol](../../skills/skill-evaluation/evals/comparison-protocol.md) | 42 completed assignments over 14 inputs: 28 substantive-task outputs and 14 simple-control outputs | Same-task no-Assay, singleton and pair comparisons across all 14 catalog entries | One completion per condition; explicit exposure, synthetic public working tasks, shared host and incomplete native observability |

The relevance study's baseline is the earlier Assay technical-writing and
text-writing runtime at `1dbb7435d5349cb00cb4a2c8ffb5e00a2d703c03`, as its
[comparison contract](../../skills/technical-writing/evals/relevance-study.md#implementation-plan-and-comparison)
states. Those revision comparisons do not estimate the effect of adding Assay to
ordinary prompting without Assay.

The existing relevance output hashes and manifests were checked. The PR 23 audit
also checked its nine method manifests, 52 packet digests and retained output
payloads, including interrupted records. These checks establish retained byte
identity and accounting. They do not establish the semantic truth of every grade,
absence of outside reads, effective model settings, or an untouched final sample.
The two historical writing studies request a different model/effort from this
diagnostic and are kept as historical evidence.

PR 24 also retains a [review of 16 primary studies](https://github.com/Muratovnik/assay/blob/f951f07eb57d9d270d973a411082524d01f2b290/docs/research/skill-effectiveness.md#what-outside-research-adds)
and its own [frozen protocol](https://github.com/Muratovnik/assay/blob/f951f07eb57d9d270d973a411082524d01f2b290/docs/research/skill-effectiveness/protocol.json)
and [derived outcomes](https://github.com/Muratovnik/assay/blob/f951f07eb57d9d270d973a411082524d01f2b290/docs/research/skill-effectiveness/outcomes.json).
Its comparison adds the full catalog to a common-host baseline, whereas this
diagnostic supplies singletons and pairs on different tasks. Its five observed
successes per arm concern artifacts and answer content; actual skill loading and
complete process adherence remain unverified. The present diagnostic separately
retains unresolved historical and browser criteria. These outcome totals cannot
be pooled or ranked against one another. PR 24's raw archive was delivered
separately to the maintainer; its public derived records do not provide a raw
evidence download. This review located
`assay-skill-effectiveness-evidence-2026-10-08.zip`, listed at 694,499 bytes,
matching the size in PR 24's derived record. Two authorized download attempts
returned HTTP 403. This review therefore could not verify the archive's SHA-256,
internal manifest or trial-to-artifact bindings.

Their exposure contracts also differ. The relevance study deliberately supplied
method text and references, prohibited source/skill command execution, and added
both README templates to every applicable task manifest before execution. That
limited intervention is documented, rather than evidence that the newly found
snapshot defect silently damaged those runs. PR 23 instead retains nine full
method manifests of 182 runtime files each, including scripts, assets, templates
and examples. Its packet reconstruction uses those complete manifests; its later
writing-peer fixture correction did not change the study packets. PR 24's
[exposure record](https://github.com/Muratovnik/assay/blob/f951f07eb57d9d270d973a411082524d01f2b290/docs/research/skill-effectiveness.md#inputs-access-and-measurements)
already identifies the stock preparer's narrower snapshot and supplies a
separate complete runtime copy, including helpers and assets. The snapshot repair
below therefore did not repair a truncated treatment in that earlier comparison.
These different exposure contracts remain part of each study's scope.

## Repairs required before trusting the comparison

### Complete runtime exposure

The packet preparer copied `SKILL.md`, UI metadata and `references/`, but omitted
runtime `scripts/`, `assets/`, `templates/` and `examples/`. The generic inline-case
preparer reuses that function. A packet could pass its byte-integrity check while
silently supplying an incomplete method. For example, technical-writing's
templates and text checker were missing, as were runtime resources of other
methods. A singleton result could then reflect broken packaging or an outside
read to recover a missing file.

The repair copies an explicit runtime-directory allowlist, rejects indirect and
special files before allocating a packet, and continues excluding evaluation
data. Tests compare each actual catalog skill's complete runtime inventory with
its singleton and full-collection packet; they also include evaluator-key decoys,
binary assets, imported scripts, symlinks and a FIFO. The comparison packets were
prepared only after this repair. Runtime skill instructions were frozen during
the campaign.

The original pinned function fails the targeted controls: five tests produce nine
expected failing subtests. At preparation time, the repaired packet suite passed
36 tests and the generic inline consumer passed 16. This is a demonstrated
infrastructure correction. It is not evidence that the skills improve task
outcomes. The exact receipts are retained in the
[execution ledger](../../skills/skill-evaluation/evals/comparison-evidence.json).

### Reuse of PR 24's corpus validator repair

PR 24 had already identified and [repaired a separate corpus-validation omission](https://github.com/Muratovnik/assay/blob/f951f07eb57d9d270d973a411082524d01f2b290/docs/research/skill-effectiveness.md#repair-justified-by-the-assessment):
`tools/eval_assets.py` excluded `ui-delivery` from its shared checker and preparer,
and omitted the retained labelled UI and legacy audit trigger formats. The
current branch still contained that defect. This change reuses PR 24's exact
`tools/eval_assets.py` and `tools/test_eval_assets.py` repair, adding UI to the
existing paired checks and validating labelled triggers separately. Labels remain
evaluator-only and are rejected before any executor packet is allocated.

Independent reproduction applied the original PR's tests to a separate copy of
this branch. Valid UI preparation failed, while blank UI prompts, mismatched
case/rubric IDs, blank trigger prompts and string/integer substitutes for Boolean
labels escaped checking. The three added tests exposed those failures. With the
two-file repair, all 19 focused tests and the corpus check passed, including
restored-valid and label-exclusion controls. The repaired file bytes match the
pinned PR 24 files.

This later validation correction does not change the 42 assignments' frozen
packets, subject outputs, rubric or scores. It repairs the corpus utility contract
without rerunning subjects or adding evidence of skill effectiveness.

### A false acceptance in the new CSV checker

Independent integration review found that the initial checker saved the submitted
test-suite result but did not use its verdict. A constructed exporter reversed
the order only for three-row inputs. It passed the checker's longer Unicode and
empty-input probes; its own public regression failed by assertion. Nevertheless,
the checker marked all seven observable CSV requirements `met`. Its original
11-test calibration had missed that failure mode.

The repair adds an independent public invocation of the supplied three-row input
and consumes the submitted-suite verdict. The demonstrated wrong order now
refutes the ordering criterion. A red submitted suite without an independently
localized violation remains an explicit unresolved contradiction; it does not
arbitrarily refute a guessed requirement. That contradiction participates in
acceptance and cannot be erased by the report's per-criterion counts. Valid
in-place sorting, alternate CSV quoting and a correct implementation rejected by
an implementation-specific test are included as neighboring controls. The revised
calibration passes 16 tests.

Both checker versions, the false-acceptance reproducer and its corrected result
are preserved. All eight saved artifacts covered by deterministic checks were
rechecked under the revised version, including every affected comparison arm.
No subject was rerun and no criterion status changed. All four actual CSV
submissions' suites pass. A later repair to measurement is not presented as
pre-execution code, and the original adverse evidence remains visible.

### Post-study Windows portability repair

The first [hosted qualification run](https://github.com/Muratovnik/assay/actions/runs/37859453187)
at publication head `f61dcea802572fefcd193ea03c86834f62afc838` passed all ten
Linux gates, the full-history publication audit and Linux plugin-manifest
validation. Windows passed nine gates but failed six comparison controls. Five
failures came from a real public Python invocation being retained as a Windows
command-line string, while the checker recognized only argument lists. The
sixth came from fixture construction translating canonical LF source bytes to
CRLF before a strict source-preservation check.

The post-study repair retains the supplied argument vector, correlates it with
the actual subprocess audit event and requires a successfully launched process.
Public-command credit also requires the known Python executable and the exact
subject script in the script position; a matching filename used as data, a shell
wrapper or an unclassified string does not establish that boundary. Canonical
fixture inputs are written as bytes. The raw-byte preservation requirement stays
strict. The expanded local calibration passes 22 tests, including real spaced-path
invocations, constructed Windows command representations, deceptive arguments,
failed launches and a deliberate LF-to-CRLF mutation that remains refuted.

Historical measurement version v2 remains the retained checker with SHA-256
`89f598c3a1d2a12c0215b95375e06ca15803a5e004cae89b7f871db6642686aa`.
The working-tree implementation is a separate post-study revision. Historical
v1/v2 sources, their sixteen receipts, the blinded grading inputs and the frozen
design, evidence, grades and publication commitments remain unchanged. The
failed hosted run is retained alongside subsequent validation; it is not removed
from the qualification history.

A separate [post-study validation record](../../skills/skill-evaluation/evals/comparison-portability-validation.json)
binds the new checker, exact input inventories and raw receipt digests for all
eight previously checked artifacts: R23/R24, R33/R34 and R35–R38. One new checker
invocation per saved artifact, with no retries, reproduces every historical v2
deterministic verdict: 40 `met`, zero `refuted` and eight `not_verified` over 48
requirements. All four applicable submitted-suite assessments remain `met`.
These comparisons use the old deterministic receipts, not the later semantic
grades. Each checker exits `2` because one criterion remains unverified by that
deterministic measurement; that expected outcome is not recoded as full delivery
success.
The replay was on Linux and does not substitute for hosted Windows qualification.
Its exact raw receipts remain privately retained under the published digests.

### Restoration and evidence accounting

The same review found a linked-parent restoration path and insufficient rejection
of empty or inconsistent study records. Restoration now checks every existing
ancestor for links/reparse points before creating a new directory. Existing work
is never overwritten. Validation rejects empty populations, lost declared cases
or arms, duplicate identities, contradictory case/arm fields, malformed records,
wrong output/receipt bindings and missing measurement versions. The final
assessment check also binds the raw judgments to their actual blinded inputs and
requires an explicit record for disagreements or changes to shared judgments.

These are corrections to the evaluation machinery discovered during this work.
The skill methods under comparison remained fixed. Structural acceptance of the
evidence ledger establishes its accounting and reproducibility, not the semantic
truth of every judgment or a general effectiveness claim.

## What the external evidence supports

This was a targeted primary-source review, not an exhaustive systematic review.
Discovery covered paired agent-skill benchmarks, repository instructions,
skill-induced failures and existing execution products. Current paper revisions
were opened; an older abstract's stronger wording was not used in place of the
September revision of the AGENTS.md study. Vendor documentation establishes
offered capabilities, not verified operation on this host.

| Primary record | Finding in its own population | Transfer to this study |
| --- | --- | --- |
| [SkillsBench, v4](https://arxiv.org/html/2602.12670v4), 2026-06-14 | 87 tasks, 18 model–harness configurations, three selected trials per condition; mean verifier reward 33.9% → 50.5%, including partial credit. Strictly solved trials are separately 31.3% → 47.7%. Thirteen tasks have negative aggregate lift. | Compare matched outcomes and retain harm. Healthy-first selection excludes some attempts. Task selection rejects comparisons without measurable separation, which limits population transfer. Its one/2–3/4+ skill buckets contain different tasks, so they do not demonstrate composition effects or a three-skill ceiling. |
| [Tessl scale study](https://arxiv.org/html/2606.17819v1), 2026-06-16 | Approximately 500 skills, 1,000 synthetic tasks and 19 configurations. For Opus 4.8, goal rubric scores are 93.3 → 97.5, instruction scores 59.8 → 88.0, solver cost $2.66 → $3.26. | Separate goal quality, instruction fidelity and cost. Single-judge, explicitly relevant tasks and excluded repository/MCP/stateful workflows limit transfer to Assay. These scores are not binary success percentages. |
| [NVIDIA ACES](https://arxiv.org/html/2608.20614v1), 2026-08-20 | 947 scored pairs from 58 of 64 skills across four harnesses; composite lift 0.2134, outcome-only lift 0.1799, 87 negative composite pairs. Supporting skills remain fixed while the target changes. | Declare whether the intervention is a singleton, marginal addition or bundle. Do not count skill-specific process compliance as independent outcome benefit. Live judge calibration and repeat coverage remain limited. |
| [Skill-induced failures](https://arxiv.org/html/2608.11888v1), 2026-08-12 | Selected failure mining retains 125 functional failures and 182 efficiency regressions from 665 labelled candidates. Functional cases include 38 with/no-skill and 87 cross-skill comparisons. Excess procedure appears in 114 efficiency cases. | Preserve adverse artifacts and test unnecessary expansion on routine tasks. Cross-skill compares different skills, not their bundle. This deliberately selected corpus gives mechanisms, not a population rate of harmful skills. |
| [Evaluating AGENTS.md, v3](https://arxiv.org/html/2602.11988v3), 2026-09-29 | LLM-generated context changes success by −0.5 and −2 points, with p=.87 and p=.37; costs rise 20% and 23%. Developer context adds 2.4 points versus none, p=.21. | The reported correctness differences versus no context are not statistically established. More instruction compliance and more work do not establish user value; repository context is also a different intervention from a supplied skill. |
| [AGENTS.md efficiency study, v2](https://arxiv.org/html/2601.20404v2), 2026-03-30 | On 124 small PR tasks in ten repositories, median time is 98.57 → 70.34 seconds and output tokens 2,925 → 2,440. Comprehensive correctness evaluation is explicitly outside scope. | Keep this favorable efficiency evidence alongside adverse evidence. It does not establish preserved quality at lower cost. The two AGENTS.md studies use different tasks and endpoints, so their results are not a direct contradiction. |

The findings support comparative evaluation, not a universal positive or negative
verdict on skills. The intervention, task population and measured endpoint differ
substantially. Stronger models may already satisfy simple contracts; the baseline
must still run. Replacing it with an assumed weak answer would manufacture lift.

### Existing products and workflows

| Implementation | Useful existing behavior | Decision and constraint |
| --- | --- | --- |
| [Anthropic skill-creator](https://raw.githubusercontent.com/anthropics/skills/main/skills/skill-creator/SKILL.md) | Candidate/baseline execution, timing and token capture, assertion review and blinded output comparison | Suitable for small native authoring pilots. Its description optimization repeatedly selects on a 60/40 split's “test” score; that set functions as selection evidence, not untouched final evidence. Moving main was reviewed, not a pinned commit. |
| [NVIDIA SkillEvaluator Tier 3](https://docs.nvidia.com/skills/skillevaluator/tier3-live-evaluation), over Harbor | Native paired agent runs, fixed support skills, group mode, custom graders and task environments | Reuse where its agent and sandbox prerequisites exist. Keep raw jobs explicitly. Its [documented Codex effort](https://docs.nvidia.com/skills/skillevaluator/agents-and-sandboxes) is `high`; that cannot silently stand in for this request's `ultra`. Documentation alone does not prove local isolation or readiness. |
| [Promptfoo agent-skill guide](https://www.promptfoo.dev/docs/guides/test-agent-skills/) | Matched task/permission fixtures, repeated native-provider runs, raw traces, skill-used assertions and outcome/cost checks | A viable documented route for a later native campaign. A successful `SKILL.md` read is a loading observation, not proof of correct application or goal completion. |
| [Tessl CLI evaluation](https://docs.tessl.io/reference/cli-commands) | Task directories, context commits, selected skills, variants, repetitions, solver/judge configuration and forced-activation control | Record its actual defaults and access surface. Hosted execution and the present native child-worker diagnostics are different environments. |

These products were inspected, not installed or executed for this report. The
directly relevant options already remove the need to create another model runner.
Assay adds task data, narrow deterministic checks and retained evidence. Its
existing public-working/selection/untouched-final distinction is retained.

## Design of the catalog comparison

The [plan](../../skills/skill-evaluation/evals/comparison-plan.json) freezes the
source revision, input and rubric digests, 42 packets, requested settings and
dispatch order. [Cases](../../skills/skill-evaluation/evals/comparison-cases.json)
hold only tasks and project files.
[Requirements](../../skills/skill-evaluation/evals/comparison-rubric.json) and
[metadata](../../skills/skill-evaluation/evals/comparison-case-metadata.json)
remain evaluator-side. They are public synthetic working material, not a sealed
final test set. No output from these 42 assignments informed the fixed task or
rubric.

Each substantive task has four conditions: no supplied Assay, A, B, A+B. Each
family also has a different simple control with no Assay and A+B. This gives each
of the 14 skills a singleton observation, but does not test every pair or the
whole catalog as a single intervention. The writing and lifecycle pairs were
selected for coverage; synergy was not assumed.

| Family | A | B | Consumer result examined |
| --- | --- | --- | --- |
| B1 | code-change | test-writing | Public CSV export, preservation and discriminating regression tests |
| B2 | test-audit | independent-audit | Contract-grounded tenant-archive audit and lawful neighboring behavior |
| B3 | software-architecture | implementation-planning | Concurrent workspace ownership and a bounded implementation plan |
| B4 | ui-delivery | product-flow-mapping | Selection/filter/export interface and journey map |
| B5 | evidence-research | skill-evaluation | Reconciliation of supplied study records and a justified evaluation decision |
| B6 | technical-writing | text-writing | Product README plus a separate Russian announcement |
| B7 | research-driven-change | route-subagents | Readiness, dependency, uncertain-effect and publication decisions |

The controls examine expansion after explicit exposure. Some legitimately need
their method, such as auditing a correct test or editing a note. They are labelled
`routine`, not presented as natural false-activation cases. Architecture and
lifecycle outputs are decisions and plans; they do not establish that a proposed
architecture or a real dispatch lifecycle ran successfully.

### Executor and grading

Every subject is a fresh native child, requested as `gpt-6-astra` with `ultra`
reasoning and no inherited parent conversation. Platform instructions and tools
remain part of the baseline. The fixed randomization seed `20261008` determines
case-block and arm dispatch order, not the model's sampling seed. The platform
permits four active agents including the coordinator, so at most three subjects
run concurrently. Work directories are separate; the filesystem is shared.

The task and environment are matched across arms; the assigned method paths
change. Methods include their full runtime resources. Workers may select relevant
references inside those paths. There is no exported full trajectory, effective
model-version receipt, enforced exclusion of evaluator paths or native discovery
trace. Explicit instructions to read a supplied skill cannot measure autonomous
selection from an installed catalog.

There are eight atomic task requirements per substantive task and four per
control. Each is `met`, `refuted` or `not_verified`. Strict success requires all
mandatory outcomes; partial counts cannot offset a failed requirement. Unknown
evidence is preserved, not silently scored as zero or success. Claims about
earlier worker actions need earlier action evidence; the coordinator's later
rerun does not establish that the worker ran it.

The CSV grader executes the public command and tests on disposable copies. Its
calibration includes the original defective exporter, a correct repair, a valid
inline-sort alternative, weak smoke tests, setup errors, skipped tests and a
wrong `.lower()` implementation. Browser controls identify source preservation
without calling it a performed click. Independent semantic assessment sees the
task, requirements and saved outputs without the treatment mapping or another
reviewer's grades. Content can still partially reveal the treatment. Additional
assessments measure sensitivity; model consensus is not independent truth.

After all subject outputs were captured, four separate semantic controls were
constructed from B5's original task and requirements: two valid answers in
different forms and two partially invalid answers with controlled substantive
errors. Their answers and 32 expected criterion labels were frozen before either
assessment. A separate review checked that oracle against the source contract.
The controls are mixed into the blinded assessment packets, giving each assessor
46 packets and 312 judgments, but remain outside the 42-execution performance
denominator. They calibrate source arithmetic, inference and wording variation
on B5; they do not calibrate every family or establish a human ground truth for
history and browser judgments.

The checker was completed after the first subjects started, against the already
fixed contract and separate calibration examples. It is not labelled pre-frozen
code. Any later scoring correction must identify the contract defect, preserve
the original judgment and re-evaluate all affected conditions consistently.

### Reading the comparisons

For a fully observed outcome on the same task, the effects are `A − none`,
`B − none`, `A+B − none`, `A+B − A`, and `A+B − B`. The additive interaction is
`Y11 − Y10 − Y01 + Y00`. It is a single-task descriptive contrast on the chosen
scale. A ceiling can produce a negative interaction without a harmful bundle.
Seven different method pairs are not seven repeats of the same interaction.

One trial per cell provides no estimate of stochastic variance. No population
confidence interval, significance test, equivalence conclusion or per-skill
leaderboard is justified. The observed bytes supplied with a method are not its
tokens consumed; elapsed coordinator time is not generation latency. Usage,
billed cost, subscription quota and cost through accepted delivery are unknown.

## Results and evidence ledger

All 42 planned assignments completed, with one saved output per assignment. There
were no subject reruns, substituted answers, excluded allocations, interrupted
subjects or cancelled subjects in this diagnostic. The
[computed results](../../skills/skill-evaluation/evals/comparison-results.json)
come from the [retained judgments](../../skills/skill-evaluation/evals/comparison-grades.json),
not from the subjects' declarations of success.

The diagnostic **does not establish an improvement in substantive delivered
quality from supplying Assay**. The baseline already satisfies the observable
content requirements on these tasks. Missing history and browser evidence leaves
many complete-delivery outcomes unresolved. That is not proof of equivalence,
zero effect, lack of value on harder tasks, or incorrect subject behavior.

### Substantive tasks

Each cell reports **met / refuted / not verified**, out of eight mandatory
requirements. A and B refer to the named pair in the design table. These counts
are descriptive components of one output; seven satisfied requirements do not
compensate for an eighth unresolved requirement.

| Family | No supplied Assay | A only | B only | A+B | Unresolved component |
| --- | --- | --- | --- | --- | --- |
| B1: CSV repair | 7 / 0 / 1 | 7 / 0 / 1 | 7 / 0 / 1 | 7 / 0 / 1 | Historical execution claims; later independent behavior checks pass |
| B2: authorization audit | 7 / 0 / 1 | 7 / 0 / 1 | 7 / 0 / 1 | 7 / 0 / 1 | Reported earlier test execution |
| B3: concurrent-workspace plan | 7 / 0 / 1 | 7 / 0 / 1 | 7 / 0 / 1 | 7 / 0 / 1 | Explicit no-edit conduct, beyond matching final code bytes |
| B4: interface repair and flow | 7 / 0 / 1 | 7 / 0 / 1 | 7 / 0 / 1 | 7 / 0 / 1 | Actual rendered keyboard behavior |
| B5: supplied-evidence synthesis | 7 / 0 / 1 | 7 / 0 / 1 | 7 / 0 / 1 | 7 / 0 / 1 | Claimed earlier Python calculations/checks |
| B6: README and announcement | 7 / 0 / 1 | 8 / 0 / 0 | 7 / 0 / 1 | 8 / 0 / 0 | Earlier demo execution claimed by the baseline and B-only output |
| B7: workflow decisions | 7 / 0 / 1 | 7 / 0 / 1 | 7 / 0 / 1 | 7 / 0 / 1 | Actual absence of prohibited launches/mutations, beyond the decision text |

For B1, all four exporters satisfy the independently executed ordering,
preservation and regression checks, including the repaired three-row check.
For B2, all four audits identify the authorization and oracle defects and preserve
the legitimate neighboring behavior. B3 supplies sound state ownership,
compatibility, interruption handling and distinguishing planned checks in each
condition. None of those plans is evidence of an implemented concurrent system.
B4's source-determinable selection/filter/export behavior is supported; a precise
browser-blocker report satisfies its separate reporting alternative without
establishing keyboard behavior.

All B5 conditions reconcile the supplied fictional Method Z study correctly:
three versus four successes among six paired rows, two improvements and one
regression, with the confounded model comparison and selection exposure kept separate.
Those numbers belong to the synthetic task's input, **not to Assay's measured
effect or cost**. B7's supported result is a bounded decision about readiness,
dependencies, uncertain effects and an unfinished PR; no actual downstream
multi-agent workflow was part of that task.

B6's difference is in evidence availability for an execution-honesty clause.
R09 and R11 do not assert that the example commands were executed. R10 and R12
do assert earlier demo execution, for which no independent historical receipt is
available. The README and announcement content is supported in all four cases.
This criterion concerns product CLI/test-command claims; R11's separate static
inspection claim is not thereby established as an independently observed action.
Counting the unknown histories as failures would manufacture a writing-quality
advantage. This observation supports neither a skill ranking nor a claim of
intentional false reporting.

### Simple controls

Each cell uses the same three-status notation, now out of four requirements.
These are separate bounded tasks, not repetitions of the substantive tasks.

| Family/control | No supplied Assay | A+B | Interpretation |
| --- | --- | --- | --- |
| B1: README spelling correction | 4 / 0 / 0 | 4 / 0 / 0 | Supported bounded answers in both conditions |
| B2: correct refund-boundary test | 3 / 0 / 1 | 3 / 0 / 1 | Correct no-defect conclusions; no-edit history remains unknown |
| B3: private-helper placement | 3 / 0 / 1 | 3 / 0 / 1 | Correct local placement; conservative no-implementation scope |
| B4: interface label change | 4 / 0 / 0 | 4 / 0 / 0 | Supported label and source-preservation outcomes |
| B5: three-fact release summary | 3 / 0 / 1 | 3 / 0 / 1 | Bounded source-supported paragraph; conservative no-new-study scope |
| B6: short note edit | 4 / 0 / 0 | 4 / 0 / 0 | Supported editing outcomes and final input preservation |
| B7: launch decision | 3 / 0 / 1 | 3 / 0 / 1 | Correct bounded decision; actual no-launch history remains unknown |

The saved control answers show no refuted requirement or observed unnecessary
expansion in the delivered content. They cannot establish the absence of hidden
extra work or a cost penalty, because complete action and usage records are
missing. They also do not measure natural skill selection from an installed
catalog.

### Missing-evidence bounds and assessment sensitivity

For B1–B5 and B7's substantive tasks, each output's satisfied-requirement fraction
can only be bounded by `[7/8, 1]`. Any two-arm difference is consequently bounded
by `[-1/8, +1/8]`, and the additive four-arm interaction by `[-1/4, +1/4]`.
These are logical missing-evidence bounds, **not statistical confidence
intervals**. B6's A-minus-baseline and bundle-minus-baseline bounds are
`[0, +1/8]`; both contain zero and concern the mixed content/reporting endpoint
described above. Adding B to A gives an observed zero on this task's fully
assessed requirement scale. It does not establish that B has no value elsewhere.
The JSON results retain every stated contrast without replacing unknowns by a
point estimate.

Across all subject judgments, the final accounting is **246 met, zero refuted
and 34 not verified out of 280 requirements**. Eight of the 42 outputs meet every
mandatory requirement; the other 34 have unresolved complete-delivery outcomes.
These totals audit the evidence denominator. Pooling unlike tasks and different
skills would not yield a meaningful catalog success rate or treatment effect.

The two initial blinded assessments agree on **278 of 280 subject statuses**.
They agree on 254 `met` and 24 `not_verified` statuses and disagree on two B2
control judgments. On the separate 32 calibration requirements, J1 matches 31
expected labels and J2 matches 32. The one mismatch concerns whether a fabricated
billing observation also violates the execution-evidence part of B5-M-7, beyond
its definite cost and conclusion defects. The wider reading is defensible, so
this is recorded as scope sensitivity rather than proof of assessor error.
These small, constructed controls establish neither broad judge accuracy nor
independent human ground truth.

The final adjudication retains both initial assessments and ten explicit
original/final decisions. Two resolve the B2 disagreements. Four correct a
shared oversight in B3's substantive task: both assessors treated matching final
files as proof of compliance with the owner's explicit no-edit prohibition.
Four further decisions apply a conservative historical reading to B3 and B5
controls whose compact criteria can also support a delivery-only reading. Those
four are labelled scope ambiguities, not unequivocal shared errors. Under the
recorded narrower alternative, the totals become 250 met and 30 not verified,
with 12 fully met outputs; the relevant paired controls still have matching
statuses. No comparative winner depends on this choice. Calibration expectations
and original assessor scores remain unchanged.

### Retained records

The execution ledger contains all 42 completed allocations, their packet and
source inventories, output contents, 84 coordinator execution observations,
measurement implementations and both deterministic-receipt versions for all
eight checked outputs. The assessment ledger adds the exact task/output/rubric
bindings for 46 blinded packets, both initial assessments, the four separately
constructed controls, the scoped review and final adjudication. Its public
validator checks that no subject, requirement, receipt version or changed
consensus disappears from the result.

These records make the delivered artifacts, assessment disagreements and
arithmetic inspectable. They do not supply a missing native trajectory, observed
backend identity, technical access boundary or independent cost measurement.

### Publication copy and original commitments

The repository's [command-record policy](../../tools/README.md#capture-one-authorized-command)
requires raw records to remain private and a separate reviewed publication copy
to be redacted where necessary. The first publication audit rejected local home
paths in the captured browser errors and canonical task identifiers. The original
records were retained and publication copies redacted under that policy. The
[publication manifest](../../skills/skill-evaluation/evals/comparison-publication.json)
binds the exact original and public file digests and lists each affected field,
blob, byte offset, replacement category and dependent digest update.

Across 572 content-addressed blobs in both ledgers, **553 remain byte-identical
to their originals**. Nineteen change: thirteen through literal path/identifier
replacement and six through dependent inventory/mapping hashes. The visible
replacements are `agent:` for 132 canonical task prefixes and
`[PLAYWRIGHT_CACHE]/` for 13 cache prefixes. Subject changes are limited to R08's
displayed worker identifier and the browser diagnostics in R13–R16's answers and
receipts. Three captured coordinator-script copies also normalize task identifiers;
these copies are explicitly identified as derivatives, not the exact scripts
that executed. No task input, task source code, rubric, original assessment judgment,
deterministic measurement receipt, final grade or adjudication changes.

Original observed output sizes remain in `output_utf8_bytes` and
`answer_utf8_bytes`; affected runs separately carry their `published_*` sizes.
The original evidence SHA-256 is
`6ab574002d7184954565e2b6b2e9b68554419568a3f859c29f70df8df656d015`;
the original assessment ledger SHA-256 is
`062930d3eaf6a6006b87ecb3f1c948baccd353792901800bed6059974a7a7139`.
Both exact originals are retained outside the public repository. Replaying the
reviewed transformation against them reproduced every public byte; the public
check validates the derivative's identities, replacement locations, counts and
bindings. A reader with only the public repository can verify the published
evidence but cannot independently reconstruct the omitted private prefixes.
Original commitments do not remove that verification boundary.

### Narrow filtering of verified digests in history scans

PR 24's [hosted history audit](https://github.com/Muratovnik/assay/actions/runs/37847070691/job/113550473050)
reported 17 `generic-api-key` matches in fetched PR 23 evidence. Those matches
reduce to three SHA-256 artifact identities, reproduced from the two retained
memo outputs and an OpenAPI fixture. This diagnostic reuses PR 23's exact
[scanner configuration](https://github.com/Muratovnik/assay/blob/8549727763e7e5c9305d8563c5f18bb9bf76c2ba/.betterleaks.toml),
with its [recorded digest disposition](https://github.com/Muratovnik/assay/blob/8549727763e7e5c9305d8563c5f18bb9bf76c2ba/skills/technical-writing/evals/durability-evidence.json).
The full-history invocation and default detection rules remain enabled.

The filter requires all three conditions: the `generic-api-key` rule, a path
matching `skills/technical-writing/evals/durability-(evidence|outputs|judgments).json`
at a path boundary, and one of exactly the three verified digest values recorded
in that configuration. It does not exclude the files or all SHA-256 values.
Positive controls still detect a different value at an allowed path and the
same three known digests at another path. This is a scoped scanner configuration
change supported by reproduced artifacts and detection controls; it is separate
from the publication-copy redaction and is not an assertion that hosted CI has
passed for this diagnostic.

## Claim boundaries and remaining requirements

| Claim | Evidence needed beyond this diagnostic | Concrete barrier or design gap |
| --- | --- | --- |
| Native skill discovery and correct routing | Observed client events under the actual installed catalog, with relevant and decoy cases | Codex/Claude CLIs were not found; this host exposes explicit child task assignment without a qualified exported skill-load trace |
| Clean exclusion of grading keys and sibling outputs | Effective per-run access restrictions and an audited executor policy | Separate directories and read restrictions here are instructions on a shared filesystem |
| Rendered UI and keyboard behavior | Actual browser actions and rendered evidence | Installed Playwright has no browser executable; the task-local Chromium download failed with a truncated archive and lock error |
| Cross-model or production-population improvement | Independent task/project groups, a declared population, justified repeats and observed model settings | The fixed screen has one trial per cell on constructed tasks and only requested, not resolved, model settings |
| Monetary or total delivery savings | Tokens, pricing/billing receipts, failed attempts, judging, repair and accepted-delivery costs | These usage/billing/trajectory receipts are not available from the native collaboration interface |
| Full multi-agent and research-to-PR effectiveness | Actual dispatch, reconciliation, cleanup and publication endpoints in controlled tasks | B7 deliberately evaluates decisions only; its report is not an executed workflow |
| Untouched final validation after candidate selection | Separate access-controlled task groups not reused during development | Published working fixtures cannot become a holdout by changing their metadata |

These boundaries are unresolved claims, not successful checks. A diagnostic PR
can make the evidence and infrastructure repair reviewable without certifying the
whole product. A broader campaign should reuse an existing native runner, retain
all allocations and raw results, preserve supporting skills for marginal tests,
and measure the actual requested endpoint. Further prose or another fixture
alone cannot close those execution and sampling gaps.

## Reproduction

Use the frozen plan and the [protocol](../../skills/skill-evaluation/evals/comparison-protocol.md).
The existing `tools/eval_assets.py prepare` accepts zero, one or two `--method`
arguments, copies runtime resources and excludes evaluator-only data. Keep its
returned manifest digest outside the packet and verify it before and after use.
Recreating task bytes does not recreate a stochastic model completion.

The deterministic calibration uses:

```text
python -B -m unittest discover -s skills/skill-evaluation/evals -p test_comparison_checks.py -v
python -B skills/skill-evaluation/evals/comparison_checks.py --case B1-M --work /absolute/path/to/retained/work
```

The second command executes submitted Python only in disposable copies. It is
not an operating-system sandbox; review untrusted external submissions before
using it. Exit `2` means missing evidence, including the worker-history criterion,
even when observable code behavior passes.

This command uses the current post-study checker. The execution ledger retains
the exact earlier v1/v2 source blobs and their original receipts for historical
measurement review; the portability validation record identifies the later
implementation separately.

Repository structural and utility checks are separate:

```text
python -B skills/skill-evaluation/evals/comparison_report.py check
python -B skills/skill-evaluation/evals/comparison_report.py summary
python -B skills/skill-evaluation/evals/comparison_report.py materialize R35 /absolute/new/output-directory
python -B tools/check.py --all
python .github/relkit.pyz audit
```

`check` verifies the study bindings and compares the saved result with its
recalculation. `summary` emits all per-case counts and missing-evidence contrasts.
`materialize` restores one saved output into a new directory without executing
it; linked ancestors and existing destinations are rejected. The comparison
fixture gate exercises evaluator and evidence-validator controls, while the
comparison evidence gate validates the retained campaign. Neither launches new
subjects.

The narrow [publication utility](../../skills/skill-evaluation/evals/comparison_publication.py)
replays the declared copy/redaction with the original two ledgers, unchanged
design files, pinned original digests and a separately retained literal-rule
file. Its `--help` lists those explicit inputs. It requires a new plain output
directory and preserves the originals in a separate private subdirectory. It is
not needed to inspect or recalculate the public results.

They validate the published assets and specific tested utilities. They do not run
models or replace the study's outcome evidence. Research foundations remain
[background sources](README.md), not automatic proof that Assay implements their
ideas effectively.
