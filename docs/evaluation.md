# What the evaluations establish

**English** · [Русский](ru/evaluation.md) · [简体中文](zh-CN/evaluation.md)

Every skill ships an `evals/` directory. It is worth being precise about what
those files prove, because the honest answer is narrower than "the skill works".

## What is in an evals directory

A skill's evaluation data is inputs and grading criteria kept apart from each
other: `cases.json` (or a differently named case collection) holds the task
prompts and their context, and `rubric.json` holds what a good answer must and
must not contain. Some skills add a `trigger-cases.json` for the separate
question of whether the skill should activate at all, and `evaluation.md`
describes how a run is set up.

`independent-audit` keeps its cases in its own fixture layout rather than the
paired JSON files. `skill-evaluation` now has paired decision and discovery cases,
separate evaluator-only metadata and a run protocol. Its manual
`research-and-transfer.md` specifications remain available for source-backed
transfer scenarios; those specifications are not executed results.
The workflow corpus covers CSV analysis, typo fixes, authentication changes,
report generation and read-only verification. Corpus files define tasks and
protocols; they are not records of completed executions.

They are evaluation data, not runtime instructions. A skill's own text says so:
while performing a user's task, the skill must not read its own cases or rubrics.
Reading the grading key is how a method starts scoring well without getting
better.

## What the gates check

`python tools/eval_assets.py check` validates primary and auxiliary input/rubric
pairs, including `ui-delivery`: case ids, rubric references, allowed fields and
portable inline input paths. It also checks `independent-audit` fixture paths
through the existing file-backed protocol.

Labelled triggers are checked separately. `skills/ui-delivery/evals/trigger-cases.json`
requires unique ids, nonempty prompts and rationales, and boolean labels. The
legacy `skills/independent-audit/evals/trigger-evals.json` format keeps prompt/boolean records
without ids and declares an execution status. These labels are evaluator data;
generic `prepare` rejects them before allocating an executor packet. Validation
does not execute fixtures or run a model.

Utility suites do execute, without running models. The audit packet suite
(`skills/independent-audit/evals/test_prepare_case.py`) builds frozen input-only
packets and verifies that preparation excludes rubrics, other cases and previous
answers, and that a packet's manifest digest matches what was actually written.
Skill snapshots preserve exact bytes of `SKILL.md`, the optional
`agents/openai.yaml` adapter and resources under `references`, `assets`, `scripts`,
`templates` and `examples`, in singleton and composed packets. Evaluator stores
such as `evals` stay outside the resource allowlist. Linked resources and special
files are rejected before packet allocation.
The preservation suite (`skills/technical-writing/evals/test_text_check.py`) runs
that skill's shipped `text_check.py` against fixture pairs and holds it to its
documented contract: which regions each mode compares, which exit code each
outcome produces, and that the check leaves both input files untouched.

`tools/test_eval_assets.py` also exercises inline packet preparation and metadata
validation, including invalid-input rejection and exclusion of coordinator keys.
These checks establish structural consistency and the specific utility behavior
asserted by the tests. They do not establish semantic case independence, correct
grading expectations, effective access isolation or answer quality.

## What is deliberately not proven

No model is run in CI. There is no score in this repository, no leaderboard and
no claim that a skill improves outcomes by some percentage. Measuring that needs
authorized comparable runs against a frozen baseline, and a result would belong to the client,
model and date it was measured on rather than to the skill.

Static files also cannot prove discovery. That a skill is installed where a
client documents its skill root does not prove the client loaded it, and a model
saying it used a skill is not evidence that it did. `tools/native_smoke.py`
exists for exactly this gap: it inspects a captured client run and reports
whether the loader events actually occurred. Its verdict is deliberately narrow,
and for Codex it returns `unverified` because there is no qualified mapping from
its events to a skill activation.

The same caution applies to sandboxes. An agent profile's adapter asks for a
read-only sandbox; whether the session honoured it is a property of the run, not
of the file. Verify the effective policy rather than reading the adapter.

## If you want to evaluate a skill yourself

Use the frozen-packet preparer so the method under test sees only inputs:

```text
python tools/eval_assets.py prepare --cases skills/<skill>/evals/cases.json --case <id> --output-parent <your evidence directory>
```

Retain the returned manifest digest somewhere outside the packet, then verify the
packet with `skills/independent-audit/evals/verify_packet.py` before and after
the run. Comparing a method against a baseline means using the baseline's own
frozen directory from its revision, not today's copy of the skill.

## Small paired comparisons

For an initial method-change comparison, use the existing
[paired-pilot procedure](../skills/skill-evaluation/references/paired-pilot.md).
It distinguishes discovery, decisions, preserved valid behavior and total cost.
A small diagnostic sample is not a score for the library or evidence of general savings.

The collection's [workflow transition probes](../skills/skill-evaluation/evals/workflow-evaluation.md)
pair dependency, integration, lifecycle, replay and evidence decisions with valid
neighboring conditions, plus composed-transition and small-task controls. They
are public synthetic working inputs and a run protocol, not executed model
results. Their read-only decision cases do not establish real dispatch or cleanup.

The [small execution comparison](../skills/skill-evaluation/evals/workflow-execution.md)
adds three tasks requiring delivered changes: a public CLI whose helper test is
already green, an inert spelling correction and a small authorization repair.
It separates natural discovery from a diagnostic forced-method run and grades
actual artifacts and consumer outcomes. Its fixture tests exercise known faulty
and repaired programs, not a model. This is a prepared pilot, not a completed
behavioral experiment.

For previously captured commands, the optional
[receipt reuse procedure](how-to/reuse-verification.md) compares exact commands
and named current inputs without another execution. Matching those inputs does
not prove environment equivalence, complete input selection or task acceptance.
Keep raw receipts private and retain their original identity.

## Evaluator-only case metadata

An optional `case-metadata.json` sits beside `cases.json`; an auxiliary
`<prefix>-cases.json` uses `<prefix>-case-metadata.json`. Existing pairs without
metadata remain supported. Metadata has `schema_version: 1`, the same
`skill_name`, and exactly the same case collections and IDs as its input file.
Every record contains the following nonempty, trimmed string fields:

| Field | Meaning |
| --- | --- |
| `id` | Matching case ID within its collection. |
| `group` | Cases sharing an incident, template, project or expected answer; unrelated cases use distinct groups. |
| `purpose` | `routine`, `regression`, `challenge` or `should-not-fire`. |
| `source` | Provenance, including whether the case is synthetic. |
| `rationale` | Why this case belongs in the intended task population. |
| `split` | `working`, `selection` or `final`. |
| `exposure` | `public`, `development` or `sealed`. |

The checker rejects unknown or missing fields, invalid classifications, unmatched
IDs, orphan sidecars and declared groups crossing splits within one skill's main
and auxiliary corpora. A final case must be declared sealed. This declaration
is not proof of access restrictions: a public file does not become secret by
changing a label. The repository check therefore accepts only `public` records;
the other exposures and the final role describe evaluator-side corpora kept
outside the repository. The checker cannot discover undeclared semantic
relatedness or verify representativeness. All shipped `skill-evaluation` cases
are explicitly public working material, never a private final set.

`prepare` does not load or copy sidecars or rubrics. It still accepts only `id`,
`prompt`, `context` and `files` on the input side. This is a packaging boundary,
not a guarantee that an executor cannot access the original repository elsewhere.
The source digest identifies inputs, not the measurement version: retain rubric,
judge configuration, metadata and split/exposure history separately in the
coordinator's existing evidence record.

Cases kept with the [feedback recorder](how-to/feedback-capture.md) are not
evaluation data. One enters an `evals/` corpus only by hand, after sanitizing,
with `purpose` set to `regression` or `should-not-fire` and a `source` naming the
reviewed record; no recorded case becomes an evaluation case, rule or method
change automatically.

## From a pilot to iterative improvement

For a new or materially changed corpus or evaluator, use
[evaluation design](../skills/skill-evaluation/references/eval-design.md). When a
request needs several candidate changes, use
[bounded iterative improvement](../skills/skill-evaluation/references/iterative-improvement.md).
Neither adds a runner, a model campaign or a requirement to publish results.
