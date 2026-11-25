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
  decision, especially on the sound idea (C03). Counts of objections, options or
  questions are not measures of quality.
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

The corpus has 12 task cases and 14 discovery cases. The first 11 were authored
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
regression material.

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
