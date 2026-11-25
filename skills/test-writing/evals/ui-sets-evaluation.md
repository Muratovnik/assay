# UI sets and absence checks: rationale and evaluation

Maintainer material for one method change, not runtime instructions or a run
report. The cases are synthetic and public. A paired pilot ran them on
2026-11-25; its outcome is below, followed by a candidate that states two of the
points in the skill file and the plan of its repeat run.

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

## Candidate: the rule in the skill file

The candidate adds one sentence to `SKILL.md`, after the negative-case rule under
"Implement without manufacturing success", which loads with the skill rather
than on a reading condition: pair a
check that an element is absent with a control in which the same locator finds
it present, and assert a collected set's size against the fixture before an all,
none, minimum or maximum claim over it. The reference keeps the detail and the
selection point unchanged; the sentence restates only those two of its points.
That reading the sentence will change the W11 test is a hypothesis this repeat
tests.

## Repeat run design

Volume: 10 sessions on Sonnet at medium effort and at most 2 judge sessions on
Opus at high effort.

- Arms: the parent of the commit that adds this section, whose
  `skills/test-writing` outside `evals/` is the 0.51.0 text, against that commit.
  Both arms load test-writing explicitly with the same code-change bytes.
- Cases and repeats: W11 three runs per arm and W12, the nearby valid control,
  two runs per arm. Fix the run order before starting and alternate the arms.
- Packets and harness as in the first pilot: the whole frozen tree of each arm
  without `skills/*/evals`, its own directory, no MCP servers, no instruction
  files and a shell limited to `python -m unittest`.
- Grading: the rubric's verification probes on every saved test file, then the
  `assess` items blind to the arm, by one grader. Record from the trace whether
  `SKILL.md`'s new sentence was in context and whether `boundary-choices.md` was
  read, and tokens, turns and wall time per run.
- Hard requirement: as in the first pilot, every probe result in the rubric
  holds and the production file is unchanged.
- Effect: the candidate meets W11's hard requirement in at least two more of its
  three runs than the baseline and has no more W12 failures than the baseline.
- No effect: a W11 difference of one or none. Both arms at none means the
  sentence did not change the assertion either: read the saved tests and traces
  for an attempted presence control before revising text; another paraphrase is
  not the next step.
- Harm: the baseline ahead on W11 by two or more, or a W12 failure only in the
  candidate.

An infrastructure failure is replaced once; it is not a result for either arm.
The repeat will not show behaviour on another model or effort, under automatic
selection rather than explicit loading, or a difference smaller than two runs of
three. W11 and W12 are selection cases that informed this candidate, so a pass is
tuning evidence, not held-out evidence, and W10 and W07 are not rerun.

## Repeat run outcome (2026-11-25)

- Compared: frozen plugin trees at `103d651` (baseline) and `1712507`
  (candidate), without `skills/*/evals`. They differ only in
  `skills/test-writing/SKILL.md`, by the candidate sentence.
- Volume: 10 subject sessions, all observed as Sonnet at medium effort, and two
  blind judge sessions on Opus at high effort. No session failed, so none was
  replaced.
- Departures from the design: two workers ran the arms of each pair side by
  side in a fixed order, and, as in the first pilot, the packets were not built
  with `tools/eval_assets.py prepare`.
- Hard requirement, baseline and candidate: W11 0 and 3 of 3, W12 2 and 2 of 2.
  Every baseline W11 test again passed with `role="alert"` removed from the
  error; every candidate W11 test failed on that change.
- Reading the saved W11 tests, knowing the arm: a presence control with the same
  locator in 0 of 3 baseline tests and 3 of 3 candidate tests. A set-size
  assertion was in all three tests of both arms, so the repeat shows nothing
  for that half of the sentence.
- Blind judge: on W11 the presence-control item was not met in 3 of 3 baseline
  runs and met in 3 of 3 candidate runs, and the candidate was judged better in
  all three pairs. On W12 every item was met in both arms and both pairs were
  ties.
- Trace: the new sentence was in context in all five candidate runs and in no
  baseline run. The reference was read in none of the 10 runs.
- Cost, summed over a cell's runs, baseline and candidate: W11 25 and 20 turns,
  6,798 and 5,845 output tokens, 79.6 s and 57.0 s; W12 17 and 18 turns, 5,275
  and 6,091 output tokens, 50.5 s and 52.5 s.
- Verdict: effect, a W11 difference of three with no W12 failure in either arm.
  The sentence is kept.
