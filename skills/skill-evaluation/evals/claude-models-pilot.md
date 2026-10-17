# Claude model pilot, 2026-10-17

A small paired pilot of three Assay skills on three Claude models, run with the
[paired-pilot procedure](../references/paired-pilot.md). It is diagnostic: one
run per cell, three small tasks, no independent grader. It is not a score.

## Setup

- Subject: Assay at `e178c9c`, loaded with `--plugin-dir` into Claude Code 2.1.296
  in headless mode (`claude -p`).
- Models: `claude-haiku-5-5`, `claude-sonnet-5-5`, `claude-opus-5-5`, each at
  effort `medium`.
- Conditions: **base** is Claude Code with its bundled skills and managed plugins
  (19 skills and 4 plugins in the init event) and no user settings
  (`--setting-sources ""`). **skill** is the same plus Assay's 17 skills and hooks.
  So the comparison is bundled skills against bundled skills plus Assay, not no
  skills against a skill.
- Discovery was natural: no task names a skill.
- Tools in both conditions: `Read`, `Glob`, `Grep`, `Skill`. No shell, no writes,
  no web access, no MCP servers. Each run had its own empty working directory
  outside any project, a per-run budget and a tool-call cap. Runs were sequential.
- Tasks, from the shipped corpora:
  - code-change `C02`, wrappers to simplify, recommendations only;
  - evidence-research `E05`, a claim to verify against its source;
  - independent-audit case 1, prepared with `prepare_case.py --without-skill`.
  The prompt pinned the answer language, the same in both conditions.
- Grading rules were fixed before the runs. Each rubric item or assertion was
  graded PASS, PARTIAL or FAIL from the final answer. Without a shell, a
  code-derived demonstration counted for audit assertion 2.

No run hit its cap or budget, read an `evals/` path, or cited a path outside its
inputs.

## Results

| Task | Haiku base | Haiku skill | Sonnet base | Sonnet skill | Opus base | Opus skill |
| --- | --- | --- | --- | --- | --- | --- |
| C02 (3 items) | 3/3 | 3/3 ¹ | 3/3 | 3/3 ² | 3/3 | 3/3 ¹ |
| E05 (2 items) | 2/2 | 2/2 | 2/2 | 2/2 | 2/2 | 2/2 |
| Audit 1 (6 assertions) | 6/6 | 6/6 | 6/6 | 6/6 | 6/6 | 6/6 |

¹ The target skill was not exercised: `independent-audit` was loaded instead of
`code-change`. ² No skill was loaded.

Every cell is at the ceiling, so the pilot shows **no demonstrated improvement on
any rubric criterion** for any model. These tasks are too easy for current models
to separate the conditions.

## Which skill fired

| Task | Haiku | Sonnet | Opus |
| --- | --- | --- | --- |
| C02 | independent-audit | none | independent-audit |
| E05 | evidence-research | evidence-research | evidence-research |
| Audit 1 | independent-audit | independent-audit | independent-audit, test-audit |

`code-change` never fired on C02. In a calibration run on the same task, Haiku
loaded `software-architecture`. The C02 prompt asks for read-only
recommendations, and the `code-change` description skips read-only audits, so
the routing agrees with the descriptions and with the corpus's own discovery
case D03, which sends a read-only audit to `independent-audit`. C01–C14 are
criteria cases graded from the answer; running C02 under natural discovery was
a choice of this pilot, so it says nothing about how `code-change` performs.
Its corpora with write tasks (verification-choice, capability-reuse, full-read)
were not run here.

## What changed besides the score

- Format followed the loaded skill. All three evidence-research answers used
  Answer / Evidence / Limits; the Haiku and Sonnet ones also noted that the
  source has no date or revision. All three audit answers with the skill added
  severities and findings with location, violated contract and consequence;
  Sonnet's also classified each legacy reference, and Haiku's and Opus's ended
  with a side-effects line.
- One adverse cell: Haiku with `independent-audit` on C02 turned a recommendation
  request into an audit with an INCONCLUSIVE verdict. It marked the contract's
  "one caller" claim REFUTED because a two-file folder had no call, treating
  absence in the examined scope as refutation. Its recommendations were still
  correct.

## Cost

Reported `total_cost_usd`, sum of the three tasks per model:

| Model | base | skill | Difference |
| --- | --- | --- | --- |
| Haiku | 0.0099 | 0.0151 | +52% |
| Sonnet | 0.1701 | 0.2549 | +50% |
| Opus | 0.3127 | 0.4829 | +54% |

The 18 runs cost 1.25 USD in total. Wall time and subscription quota were not
measured.

## Limits

- One run per cell; a repeat may route or answer differently, as the Haiku
  calibration run did.
- The coordinator was Claude Opus 5.5, grading outputs that include Opus's own.
- Without a shell the audit could not run the gates, so runtime claims in every
  audit answer were inferred from source in both conditions.
- Harder cases are needed to measure a difference: tasks where the base
  condition fails on these models.
