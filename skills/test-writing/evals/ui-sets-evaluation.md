# UI sets and absence checks: rationale and evaluation

Maintainer material for one method change, not runtime instructions or a run
report. The cases are synthetic and public. A paired pilot ran them on
2026-11-25; its outcome is below.

## Decision and gap

At `6242086` the UI section of the boundary-choices reference asked for stable
roles, names or test hooks only for interaction. Nothing on the writing side
asked which elements an assertion collects, for the size of that set before an
every, none, minimum or maximum claim, or for a presence control behind an
absence check. Test-audit already investigates vacuous domains, so the defect
could be caught in review but nothing prevented it while writing. The change adds
those three points to the UI section and widens the skill's reading condition
from "UI interaction" to "UI tests": a render-and-assert test with no interaction
is where such sets are collected. Test-audit is unchanged; its criterion is the
review side of the same rule.

That the missing rule caused the observed defects is a hypothesis. No trace
showed whether the reference was read when those tests were written.

## Cases and controls

| Case | Protected outcome | Legitimate work an overbroad rule would reject |
| --- | --- | --- |
| W10 | Entries by contract hooks; every/none checks fail on an empty legend; hidden series checked by names the same query finds | Exact name lists as the size check; role or test id |
| W11 | The valid-address absence check has an invalid-address control with the same locator | The control is test-only work within scope |
| W12 | Row order checked with the row count, so a row-less table fails | No test ids and frozen production: roles are correct, no hooks are added, and zero rows is the right expectation for an empty list |
| W07 (existing) | Absence of a send paired with an exact-once send | A non-UI test gains no DOM ceremony |

Each verification probe was run against three hand-written test files before the
rubric was frozen: one following the new points, one vacuous and one selecting by
class. Following the points passed every restyle and failed every defect probe.
The vacuous file passed the empty, shown-hidden, always-alert, lost-role and
row-less probes. The class-selected file failed the restyle. These runs calibrate
the probes; they say nothing about a model's behaviour.

## Paired pilot design

- Arms: `skills/test-writing` at `6242086` against the commit that adds this file.
  Both arms load test-writing explicitly with the same `skills/code-change` bytes,
  which test-writing links to.
- Cases and repeats: W10, W11, W12 and W07, two runs per case per arm, 16 sessions,
  under one model and effort pair the owner agrees for both arms.
- Packets: `python tools/eval_assets.py prepare --cases <cases file> --case <id>
  --method <arm>/skills/test-writing --method <arm>/skills/code-change
  --output-parent <evidence directory>`; the executor installs nothing and runs no
  `git`.
- Grading: run the rubric's verification probes on each saved test file, then the
  `assess` items. Record from the trace whether `boundary-choices.md` was read
  before the test was written.
- Hard requirement: every probe result in the rubric holds and the production file
  is unchanged; W07 meets its existing rubric.
- Effect: the candidate meets the hard requirement in at least two more of the six
  W10-W12 runs than the baseline and has no more W12 or W07 failures.
- No effect: a difference of one or none, including both arms at five or six of
  six, where the rules were already followed, or both at one or none. In the
  second case, read the traces for the reference read before revising any text.
- Harm: the baseline ahead by two or more, or a W12 or W07 failure only in the
  candidate.

Record tokens, turns and wall time per run. An infrastructure failure is replaced
once; it is not a result for either arm.

## Pilot outcome (2026-11-25)

- Compared: frozen plugin trees at `9783731` (baseline) and `e16ef87`
  (candidate). Outside `evals/`, their `skills/test-writing` difference is
  byte-identical to the planned difference from `6242086`, and the code-change
  bytes are the same in both arms. Each session loaded test-writing explicitly
  in its own directory, with no MCP servers, no instruction files and a shell
  limited to `python -m unittest`.
- Volume: 16 sessions, two per case per arm, all observed as Sonnet at medium
  effort; no invalid run, so none was replaced.
- Departure from the design: the packets were not built with
  `tools/eval_assets.py prepare`; every session had the whole frozen plugin
  tree without `skills/*/evals`.
- Grading: the rubric's verification probes on every saved test file, then the
  `assess` items blind to the arm, by one grader. W07 has no rubric probes; its
  hard requirement was its three items and an unchanged `sender.py`.
- Hard requirement, baseline and candidate: W10 2 and 2 of 2, W11 0 and 0 of 2,
  W12 2 and 2 of 2, W07 2 and 2 of 2; W10 to W12 4 of 6 in both arms. Every W11
  test passed with `role="alert"` removed from the error: the valid-address
  absence check had no control in which the same locator finds the error, and
  the grader marked the presence-control item not met in all four W11 runs.
- The reference was read in none of the 16 runs, 0 of the 8 candidate runs.
  Of the changed text, only the widened reading condition was in the
  candidate's context, and it caused no read.
- In 15 of the 16 runs, in both arms, the executor tried to run its own mutants
  or controls through the shell and was refused; such a self-check might have
  caught W11.
- Cost: baseline 63 turns, 212 s, 19,705 output tokens and USD 0.78 at API
  prices; candidate 62 turns, 211 s, 19,866 and USD 0.77.
- Verdict: no effect, a difference of none at four of six in both arms. No
  harm: no W12 or W07 failure in either arm.

The pilot does not test the three points themselves, since no run read them; it
shows that the reference does not reach a UI test through its reading
condition. W11 fails in the base method, so it remains the case for a change
that places the size and presence-control rule where the work reads it.
