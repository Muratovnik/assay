# Revision-diagnostic evaluation supplement

Coordinator-only protocol for the `revision-cases.json` / `revision-rubric.json`
pairs in text-writing and technical-writing. Do not include rubrics, this protocol,
unit tests or the decision journal in executor packets. The existing
`tools/eval_assets.py prepare` command can freeze an input-only case and selected
method roots; it supplies no filesystem isolation or model execution by itself.

## Two different kinds of evidence

`python -B -m unittest discover -s skills/text-writing/evals -p test_revision_check.py`
checks extraction, reports, statuses, read-only CLI behavior and declared limits.
It does not establish skill discovery, reader preference, task success or lower
model costs. `tools/check.py --all` includes it alongside the existing gates.

The named revision pairs are proposed behavioral regression/control inputs, not
captured model results. They were written with the implementation and are not a
holdout. Before a material behavioral claim, reserve different tasks before tuning,
then run the previous method and candidate under comparable input, permissions,
model, effort, invocation and tool conditions using an already authorized runner.
Do not create a new platform or start a paid campaign to satisfy this document.

## Report dimensions separately

Use the existing dimension names, not a new combined quality score:

| Dimension | Evidence to inspect |
| --- | --- |
| meaning_preserved | Numbers in their roles, units, source relations, negation, bounds, modality, deadlines and attribution. |
| task_and_genre_fit | Reader's goal, requested scope/length, organization and useful navigation. |
| editorial_restraint | Kept author voice and terminology; unnecessary corrections and false alarms on controls. |
| authorized_effects | Actual reads/writes/commands; review alone must not trigger execution or installation. |
| final_delivery | Final artifact, not the accompanying promise or an unrequested service report. |

Record each dimension as `supported`, `refuted`, `unverified` or `not-applicable`,
with a concrete observation and evidence location. Do not average away a meaning
failure or unauthorized action. Compare candidate/baseline differences and their
confounders; keep unsuccessful attempts. A valid control becoming overedited is
negative evidence even when the metric moves in the preferred direction.

Optional style measurements belong in a separate observation field with language,
coverage, before/after values and limits. No human/AI percentage or style-band pass
counts toward the dimensions. Reader preference requires actual reader responses;
an LLM judge's preference must be labeled as such and kept separate. Cost, tokens,
time and retries come only from captured runs, with missing values left unknown.

## Stop and decide

A bounded implementation can be structurally accepted without claiming a writing
improvement. Record retain/weaken/remove/defer decisions with the applicable case
and valid control using the skill-design rule-decision format. Keep raw evidence
outside canonical skills and never recycle answers into later executor inputs.
Do not re-run an unchanged deterministic case to produce a more attractive result.
