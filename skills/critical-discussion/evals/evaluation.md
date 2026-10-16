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
- Discovery: D01-D05 should select the method; D06-D11 are near misses owned by
  other skills or by no skill.

Inspect actual answers and any tool effects. Answer length and the number of
checks do not establish effectiveness.

## Current verification boundary

The corpus has 12 task cases and 11 discovery cases, authored from the method's
brief before the skill text. No case has been run. Repository gates check pair
structure and registration only. Before tuning the method on these cases,
reserve at least one additional case outside the tracked tree; once a tracked
case informs a revision it is regression material, not held-out evidence.
