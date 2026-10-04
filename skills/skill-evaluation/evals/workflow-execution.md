# Small execution comparison

Coordinator material, not runtime instructions. The three tasks in
`workflow-execution-cases.json` require delivered edits in disposable Python
projects. The rubric and metadata are separate. All are public working examples,
not production incidents, hidden tests or a measurement of model quality.

## Run the task, not an explanation of the task

Use the existing `tools/eval_assets.py prepare` with one selected case. Run the
executor in a disposable copy of that case's inputs, with only the methods for
that condition available. Keep the frozen packet, grading keys, other cases,
previous answers and evaluator tools outside its accessible roots. The preparer
and a fresh context do not themselves enforce that isolation.

Start with the old collection and candidate through the ordinary client route:
three tasks in two conditions, six sequential runs as an initial diagnostic
budget. Freeze task inputs, skill revision, surrounding instructions, client,
model/effort, tool availability and permitted effects. No paid campaign or
external worker is authorized by this document. Use the existing
[paired pilot](../references/paired-pilot.md); no new runner is required.

Observe relevant load/read events when the client exposes them, but grade the
actual edits and consumer behavior. An attempted load is not a successful read;
a successful read does not establish that a criterion changed a decision. If a
natural route misses, a separately recorded forced-method run can diagnose that
layer; it must not replace the natural-route result or count as automatic
selection. A trace with no qualified mapping remains unverified.

The minimum observations are:

| Case | Consumer observation | Nearby valid work to preserve |
| --- | --- | --- |
| WX-01 | Execute the public export and inspect its output, including stable order, duplicates and quoted fields | Keep the already-correct helper; no broad rewrite |
| WX-02 | Inspect the delivered README and whole diff | A spelling correction needs no test framework or general research |
| WX-03 | Exercise accepted and rejected deletion paths and inspect state after rejection | Matching-tenant administrators must still delete |

`tools/test_workflow_execution_fixtures.py` executes the faulty and repaired toy
programs against independently stated values. It proves that these particular
observations distinguish the controls, not that an agent will perform the right
work. The inline repairs in that test are evaluator data, not executor inputs.
The corpus deliberately gives WX-03 an explicit regression request, whereas
WX-02 gives none. Test count is not a quality target.

Retain final artifacts, actual tool evidence, failures and remaining corrections.
Compare task success, valid alternatives, authorized effects, unnecessary work
and full-chain cost separately. A correct explanation without the requested edit
fails delivery. A good edit without a particular preferred phrase can pass. Both
conditions passing establishes no improvement on that case. An inconclusive
comparison is not a reason to rerun unchanged tasks until a preferred result.

Reserve a different case group outside the source tree before making a claim
about transfer beyond these exposed examples. Current facts about the client and
external state must accompany any real run. Do not infer subscription usage from
API prices or fabricated token counts.

## Local transfer decisions

- [Anthropic skill-creator](https://github.com/anthropics/skills/tree/main/skills/skill-creator)
  and [Agent Skills evaluation](https://agentskills.io/skill-creation/evaluating-skills):
  keep baseline/candidate artifacts and connect authoring to outcome review.
  Do not import mandatory parallel execution or a new report server.
- [Superpowers writing-skills](https://github.com/obra/superpowers/blob/main/skills/writing-skills/SKILL.md):
  test whether a description substitutes for reading and use pressure cases.
  Do not require a method on every trivial edit or grade obedience as success.
- [GSD resume-project](https://github.com/gsd-build/get-shit-done/blob/main/get-shit-done/workflows/resume-project.md):
  recover the selected work before continuing. Assay retains its existing task
  record; its hook only retains a live suggestion for a bounded continuation.
- [OpenSpec CLI](https://github.com/Fission-AI/OpenSpec/blob/main/docs-lab/reference/cli.md):
  give the next decision sufficient context. File existence is not readiness.
- [gstack evidence](https://github.com/garrytan/gstack/blob/main/bin/gstack-evidence):
  reuse evidence by relevant content and exact command. Extend Assay's existing
  receipt utility; do not import another ledger or ignore environment changes.
- [Tessl evaluation framework](https://tessl.io/blog/a-proposed-framework-for-evaluating-skills-research-eng-blog):
  distinguish forced method use from natural discovery. Do not transfer the
  published activation rates or follow-instruction scores to Assay outcomes.

Source review: 2026-10-04. These are bounded mechanism transfers, not results for
this candidate. No external implementation or dependency is copied.

## Evidence boundary for this change

The added Python tests and public fixture controls can be executed without a
model. Structural gates check packaging and data separation. Native discovery,
method adherence, comparative task quality and quota effects require captured
client runs. No such behavioral comparison is claimed by this source change.
