# Catalog diagnostic comparison

This study asks what supplying Assay changes in the delivered result on fixed
tasks. It is a diagnostic screen of the catalog at
`94c517b0aac9ba2575086bf9aead1cc828aadb0d`, not a population estimate or a
certification of native client behavior. The cases and requirements were fixed
before subject execution. The plan and packet manifests preserve their bytes.

## Design and outcomes

[The plan](comparison-plan.json) assigns seven substantive tasks to four
conditions: no supplied Assay (`00`), the first method (`10`), the second (`01`),
and both (`11`). Each family also has a separate bounded control in `00` and
`11`. There are 42 assigned trials on 14 task inputs, with one fresh worker per
assignment. A repeat is not substituted for an unfavorable answer.

| Block | First method | Second method | Observed scope |
| --- | --- | --- | --- |
| B1 | code-change | test-writing | Delivered public CSV exporter and its regression protection |
| B2 | test-audit | independent-audit | Contract-grounded audit of source, tests and release claims |
| B3 | software-architecture | implementation-planning | Grounded architecture and executable plan; no implemented architecture |
| B4 | ui-delivery | product-flow-mapping | Local interface changes and journey map; browser evidence has its own availability status |
| B5 | evidence-research | skill-evaluation | Supplied-source synthesis and evaluation decisions; no live retrieval |
| B6 | technical-writing | text-writing | Product README and an ordinary announcement for different readers |
| B7 | research-driven-change | route-subagents | Handoff, readiness and evidence decisions; no native dispatch or lifecycle execution |

These pairs give each catalog entry a singleton condition; the writing and
lifecycle pairs were chosen for coverage, not because synergy was established.
They do not cover every optional peer, all pairings or full-collection effects.

[Cases](comparison-cases.json) contain only tasks, context and project inputs.
[Requirements](comparison-rubric.json) belong to the evaluator. They derive from
the task and its adopted contract, not from skill vocabulary, headings, number of
checks or answer length. All substantive cases have eight atomic requirements;
controls have four. Preserve each requirement as `met`, `refuted` or
`not_verified`. No soft average offsets a refuted mandatory outcome, and missing
evidence is not a failure imputed as zero.

The strict delivery outcome requires all applicable mandatory requirements to be
met. A partial requirement count is diagnostic detail. A fraction or contrast is
reported only with its stated denominator; an unknown requirement leaves an
interval of possible values, not an invented point score. Source inspection,
executed artifact behavior and verified reporting history are different evidence.

For a fully observed, higher-is-better outcome on the same case:

```text
A - none = Y10 - Y00
B - none = Y01 - Y00
bundle - none = Y11 - Y00
B added to A = Y11 - Y10
A added to B = Y11 - Y01
interaction = Y11 - Y10 - Y01 + Y00
```

These are single-case descriptive contrasts. A bounded scale can produce a
negative additive interaction because of its ceiling. One trial per cell cannot
estimate stochastic variance. Seven different method pairs do not constitute
seven replications of the same interaction. No aggregate ranking of the methods,
population confidence interval, equivalence claim or significance claim follows.

## Valid controls and calibration

The simple controls detect unnecessary expansion after exposure. Some controls
legitimately call for their method, such as auditing a test oracle or copyediting
a note. Their metadata therefore says `routine`; they are not a measurement of
native false activation or a universal instruction to skip those skills.

Before execution, an independent fixture/rubric review checked all assignments,
source arithmetic, solvability and legitimate alternative outputs. It identified
and removed two unjustified architecture requirements: a prescribed order for
integration checks and a mandatory explicit comparison of alternatives. The
browser criterion was clarified to accept the task's explicit blocker-reporting
branch. No subject output informed these changes. The final rubric digest is
recorded in the plan.

Deterministic evaluator controls use the original faulty public exporter, a
corrected exporter, a valid alternate implementation and weak tests. A grader
must distinguish assertion failure from setup failure and accept the supported
alternate. A report's assertion that a command ran cannot be established by the
coordinator running it later. Semantic assessment uses the original task,
requirements and saved artifacts; candidate identity and other scores are withheld
from the first review. Residual unblinding from output content remains possible.
Additional assessments are sensitivity checks, not independent ground truth.

Keep calibration, code finalization, assessment and any adjudication dates and
identities in the evidence record. Do not describe a later checker implementation
as frozen before the first subject merely because its contract was already fixed.
Any post-execution rubric repair needs a new measurement identity, rationale from
the original contract and consistent regrading of all affected saved conditions.

## Execution and identity

The baseline is the ordinary host's platform and task instructions without Assay
supplied in its task packet. It is not an instruction-free model. Each condition
gets the same project bytes and task, a separate writable copy, and the same
available host tools. The wrapper changes only assigned method paths and unique
working paths. Each subject is a fresh direct child with `fork_turns="none"` and
requested `gpt-6-astra` / `ultra`. There is no observed provider model version,
effective reasoning receipt or generation seed. The seed `20261008` randomizes
task-block order and then condition order inside each block, not model sampling.
Available slots are filled in that dispatch order; at most three subjects run
concurrently. A block's fourth arm starts after capacity becomes available.

The root owns additional launches, preparation, grading and integration.
Subjects must not create children, install dependencies, access external services,
publish or modify unrelated state. Their actual task can further narrow effects.
The immutable packet includes the selected method's full runtime resources;
`evals/`, sibling skills, grading keys and previous answers are excluded. Missing
optional peers are intentionally absent rather than silently copied into the
baseline or singleton. Applicable references remain selectable by the subject.

This is **explicit exposure**, not automatic skill discovery. A supplied packet
or a subject's claim of use is not an observed read. Full native tool trajectories
and effective access enforcement are not exposed by this host. Shared filesystem
access remains: separate directories and instructions do not make grading keys or
other work technically inaccessible. Packet hashes prove the retained byte
inventory, not absence of transient writes or outside reads. These limitations
prevent a clean native causal/discovery claim even if all artifacts are correct.

The standard Codex and Claude CLIs were not found. The installed Playwright
library had no browser executable. A task-local Chromium download failed with an
invalid/truncated archive and a lock error; no browser action or screenshot is
claimed from that failed setup. Every subject receives the same preflight fact
and is instructed not to repeat installation. UI code can still be delivered and
inspected, but keyboard/rendered behavior requires its missing runtime evidence.

## Accounting, changes and stopping

Keep all 42 allocations and every observed launch, completion, partial artifact,
refusal, cancellation and infrastructure error. Preserve an unsuccessful subject
output before diagnosis. Do not discard cases, remove timeouts or rerun unchanged
subjects to select favorable answers. A failure before execution can be repaired
as infrastructure with explicit attempt accounting; a changed task or execution
contract invalidates affected comparisons and requires both arms under the new
measurement. A known subject failure is not reclassified as setup merely because
it hurts a score.

Stop after the fixed assignments, or record the exact capability/authority
barrier for any unfinished allocation. No enforceable per-subject timeout is
available. Coordinator record times are not provider start/end timestamps, so
they are not used for model latency or savings. Token usage, billed cost,
subscription quota, hidden reasoning, queue time and full accepted-delivery cost
remain unknown. Supplied bytes describe exposure volume, not token consumption.

The frozen skill methods are the experimental intervention. Do not rewrite them
mid-study. A demonstrated infrastructure fault can be repaired before packaging;
this study repaired missing runtime resources that would otherwise make the
singleton conditions incomplete. A later behavioral change is a separately
identified candidate with its own comparison. Raw adverse evidence is retained.

## Reproduction and remaining claims

The existing owner command prepares each task with zero, one or both `--method`
arguments; output must be outside the source tree:

```text
python -B tools/eval_assets.py prepare --cases skills/skill-evaluation/evals/comparison-cases.json --case B1-M --output-parent /absolute/evidence --method skills/code-change --method skills/test-writing
```

Retain the returned manifest digest, make a writable copy of `inputs/`, and keep
the immutable packet unchanged. Use the frozen task, wrapper contract, skill
revision and declared host settings. Reproduction on another host is a new run,
not equality with this session's stochastic outputs. The published plan identifies
the actual source bytes; changing only an absolute working path does not change
the task but does change the literal wrapper digest.

An existing native runner such as SkillEvaluator/Harbor, Promptfoo or the
skill-creator workflow can execute a later campaign when its real prerequisites
are met. This repository adds evaluation data and narrow checks, not another
agent execution platform. The [research report](../../../docs/research/skill-effectiveness.md)
compares those alternatives and their limits.

A general effectiveness claim still requires independently sourced task/project
groups for each claimed consumer, justified repeats/sample size, observed client
settings, protected grading access, native discovery with the actual collection,
measured costs through accepted delivery, calibrated outcome judges and untouched
final groups after selection. Routing and research-to-delivery claims require real
root-level execution through their endpoint. This screen supplies none of those
missing claims by inference from a plan, a read event or a green repository gate.
