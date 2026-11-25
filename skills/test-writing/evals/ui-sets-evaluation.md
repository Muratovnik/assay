# UI sets and absence checks: rationale and evaluation

Maintainer material for one method change, not runtime instructions or a run
report. The cases are synthetic and public; none has been run by a model.

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

## Owed paired pilot

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
