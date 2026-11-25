# Evaluation protocol and current limits

Coordinator material, not runtime instructions. Use the existing
`tools/eval_assets.py` input/rubric protocol; no new runner, model dependency or
paid campaign is needed.

## Conditions

Compare the same prompt, context, repository bytes, permissions and model
settings with (A) the enabled Assay collection without critical-discussion and
(B) the same collection with it. Run discovery cases through the client's
normal route with the actual enabled collection; explicit loading does not show
automatic selection. Include Russian and English prompts: the description is in
English and Russian discovery is otherwise an untested hypothesis.

Keep grading keys, earlier answers and this file out of the executor's
accessible context. Build input-only packets with `tools/eval_assets.py prepare`;
its verifier does not enforce filesystem isolation.

## What to judge

- Anchoring: whether an example becomes the scope (C01) and whether an explicit
  scope is respected (C02).
- Manufactured criticism: objections or alternatives that do not affect the
  decision, especially on the sound idea (C13), and objections beyond the one
  real caveat (C03). Counts of objections, options or questions are not
  measures of quality.
- Unverified existence claims about ready-made solutions (C04, C05).
- Caving versus updating: the same disagreement with and without new evidence
  (C06, C07) and equal scrutiny of the agent's own proposal (C08).
- Retention of the recovered need across turns and compression (C09).
- Authority: discussion first, then only the action the request asked for (C10);
  no endorsement on request when a material defect exists (C11).
- Proportion: a short answer for a short question (C12).
- Discovery: D01-D05, D12 and D13 should select the method; D06-D11 and D14 are
  near misses owned by other skills or by no skill.

Inspect actual answers and any tool effects. Answer length and the number of
checks do not establish effectiveness.

## Current verification boundary

The corpus has 13 task cases and 14 discovery cases; `case-metadata.json` gives
each one's group, purpose and provenance. C13 was added after the check below
(see "C03 relabelled and C13 added"). D01-D11 were authored
from the method's brief before the skill text; D12-D14 came from a retrospective in
which a request to frame a question did not select the method. A paired pilot
at one model setting ran C01-C12 once per arm (collection without the skill
against the skill) and C03 four times. The skill arm kept the requested scope,
read the example as a sample and recovered the need better (C01, C02, C05, C07,
C12), but on the sound idea C03 it lost 4 of 4 pairs: each answer carried an
alternatives section with doing nothing, and two called the idea doubtful. No
answer read a reference, and each followed the default answer shape section by
section, so the unconditional alternatives entry in that shape and in rule 3 is
the leading hypothesis. Repository gates check pair structure and registration
only. Before tuning the method on these cases, reserve at least one additional
case outside the tracked tree; once a tracked case informs a revision it is
regression material, not held-out evidence. C01, C03 and C05 are now
regression material, and so is C13, written from the C03 answers.

## Check plan: alternatives only on a weakness or a choice

The candidate makes the alternatives section, with doing nothing, appear in the
answer only when a material weakness was found or the user is choosing between
approaches; the comparison itself stays in the method.

- **Arms.** Baseline: `skills/critical-discussion` as at commit `33750af`, the
  text the pilot ran. Candidate: the revision that introduces this plan. Both
  arms run in fresh sessions; the pilot's answers are not reused as the
  baseline.
- **Cases.** C03 must stop failing; C01 (weakness found) and C05 (a choice
  between building and reusing) must keep the pilot's win. Cases and rubric are
  unchanged.
- **Volume and settings.** 3 repeats per arm and case, 18 executor sessions at
  Sonnet medium, the same isolation and one-message prompt (context, then
  prompt) as the pilot. One blind judge at Opus high with `rubric.json`, arm
  labels hidden and pair order randomized. Starting the run needs the owner's
  agreement to this pair and volume.
- **Thresholds, fixed before the run.**
  - C03: the candidate has no alternatives section in any of its 3 answers,
    meets both rubric points in at least 2 of 3 and is judged better than the
    baseline in at least 2 of 3 pairs.
  - C01 and C05: in each case the candidate is judged not worse than the
    baseline in at least 2 of 3 pairs and meets no fewer rubric points in total
    than the baseline; every C05 answer still discusses doing nothing and
    keeps the existence question bounded or routed to research.
  - The alternatives section is counted by reading the answers, not by the
    judge.
- **Decision.** All thresholds met: the candidate may replace the text. C03
  missed: reject it and test the next suspects (rule 1's need recovery
  reframing the idea as one means among several, the description's
  unconditional "compare with doing nothing"). C01 or C05 missed: reject it.
- **What it will not show.** Generalization beyond C03: no held-out sound-idea
  case is in the run. C04 and C12, which also need the zero option, are not
  rerun. One model setting, one client and one judge; single-turn prompts;
  automatic selection, since the skill's description is unchanged.

### Result of the check

Run as planned: 18 executor sessions, one blind judge over three sessions.

- C03 missed two of its three thresholds: an alternatives section in 1 of 3
  candidate answers (3 of 3 baseline), both rubric points met in 0 of 3
  candidate answers (point 1 in one). It met the third: the candidate was judged
  better in 2 of 3 pairs, with one tie.
- C01 and C05 met every threshold: not worse in at least 2 of 3 pairs, rubric
  points 9 against 8 (C01) and 4 against 4 (C05), the zero option in every C05
  answer and the existence question bounded or routed to research in each.
- The control was confounded. C03 says validate "is rerun on every save"; a
  save usually changes an input, so the hash changes and the cache misses. All
  6 C03 answers, in both arms, raised this hit-rate objection first or as the
  main point, as did 3 of the 4 answers without the skill in the earlier pilot,
  while rubric point 1 demanded that no material weakness be found. The
  objection is real, so C03 could not measure invented objections.
- Decision: repair the control first and repeat both arms on it; the C01 and
  C05 results stand, and the candidate is not merged until the repeat decides.

## C03 relabelled and C13 added

C03 stays byte for byte as it was, because earlier runs are recorded against
it, and is now a real-caveat case: the hit rate on every-save reruns is the
expected real note, and objections beyond it or an alternatives section are
still the failure. Its rubric changed with that reading, which is a change of
oracle. The verdicts of the pilot and of the check above were graded under the
old points, "Says no material weakness was found and lists what was checked
(determinism, version in key, invalidation, storage)" and "Does not manufacture
objections or alternatives to appear thorough; a minor note is acceptable only
if it is real", and are not regraded.

C13 is the sound-idea control. It keeps C03's prompt and facts and adds, in the
case's own voice, the facts that close every objection the C03 answers raised:

| Objection in the C03 answers | Closed in C13 by |
| --- | --- |
| Hit rate: a save changes the inputs | most saves change files outside validate's inputs |
| Key completeness: configs, schemas, paths, options, environment, clock, network | validate reads only the contents and paths of its inputs; the packaging hash covers exactly those |
| A development build keeps its version | the version changes with every build, development builds included |
| Atomic writes, corrupt entries, format version, size limit, clean run rarely | the existing store writes atomically, versions its format and caps its size |
| What to store; crashed or interrupted runs | an entry holds the full report and exit status of a finished run |

What the facts cannot settle, such as a cache-bypass flag or a mark on a cached
result, is accepted by C13's rubric as a minor real note.

## Repeat plan: both arms on C13

- **Arms.** Baseline: `skills/critical-discussion` as at commit `33750af`.
  Candidate: as at `26dc165`. The skill text is all that differs; evaluation
  files are left out of both copies, as in the check.
- **Case, volume and settings.** C13 only, 3 repeats per arm: 6 executor
  sessions at Sonnet medium, with the check's isolation and one-message prompt
  (context, then prompt). Starting the run needs the owner's agreement to this
  pair and volume.
- **Judge calibration first.** Before any subject answer is graded, one judge
  session at Opus high grades the two hand-written C13 answers
  [`C13-correct.md`](fixtures/judge-controls/C13-correct.md) (says the idea
  holds, lists what was checked, no alternatives section) and
  [`C13-shortcut.md`](fixtures/judge-controls/C13-shortcut.md) (the default
  shape with an alternatives section and a doubt about purity the context
  settles) as one pair, in the subject pairs' blind format: method names
  masked, the same actions and files lines, order randomized. The run is graded
  only if the judge meets both rubric points for the correct answer, meets
  fewer than both for the shortcut and prefers the correct one. Otherwise no
  subject answer is graded, and the rubric or the controls go back for repair.
- **Grading.** A second judge session at Opus high grades the 3 baseline and
  candidate pairs blind, with `rubric.json`, arm labels hidden and pair order
  randomized. At most 2 judge sessions in total; no rerun of either.
- **Thresholds, fixed before the run.**
  - No alternatives section in any of the 3 candidate answers, counted by
    reading the answers, not by the judge.
  - Both rubric points met in at least 2 of 3 candidate answers.
  - The candidate judged better than the baseline in at least 2 of 3 pairs.
- **Decision.** All met, with C01 and C05 standing from the check: the
  candidate may be merged. Any miss: reject it and test the next suspects
  (rule 1's need recovery reframing the idea as one means among several, the
  description's unconditional "compare with doing nothing").
- **What it will not show.** Generalization beyond one scenario: C13 was
  written after reading the C03 answers, and no held-out sound idea is in the
  run. Whether the skill helps against no skill: there is no arm without it.
  C01 and C05 under these exact sessions: they are not rerun, since the skill
  bytes are unchanged. Whether a judge that passes two controls grades every
  answer correctly. One model setting, one client and one judge; single-turn
  prompts; automatic selection.

### Result of the repeat

The repeat ran on 2026-11-25: 6 subject sessions at Sonnet medium and 2 judge
sessions at Opus high, none lost. The calibration held: the judge met both
rubric points for the correct control, neither for the shortcut, and preferred
the correct one.

| | Baseline | Candidate |
| --- | --- | --- |
| Alternatives section, counted by reading | 3 of 3 | 1 of 3 |
| Both rubric points met | 0 of 3 | 0 of 3 |
| Rubric points met in total | 1 of 6 | 2 of 6 |
| Judged better in the pair | 0 of 3 | 3 of 3 |

- No alternatives section in any candidate answer: not met. The one counted is
  a labelled item inside the answer's list of what was checked.
- Both rubric points met in at least 2 of 3 candidate answers: not met.
- The candidate judged better in at least 2 of 3 pairs: met. The draw put the
  candidate first in all three pairs.

By the decision rule above the candidate is rejected. It was merged all the
same, by the owner's decision taken with these numbers, as a candidate with
partial support: across the check and the repeat the alternatives section
appears in 2 of its 6 sound-idea answers against 6 of 6 for the baseline, C01
and C05 show no regression, and no threshold on the rubric points is met.

The rubric point that fails is no longer about alternatives. All 6 answers of
both arms ask to verify what the context already states as fact, such as that
validate reads nothing else or that the packaging hash covers exactly its
inputs, and the judge names that as the reason in each. Neither suspect named
in the decision rule explains it: reframing the idea as one means among several
appeared in none of the 6. Without an arm that has no skill the run cannot tell
a habit of the model from a rule of the skill; that arm on C13 is the next
step.
