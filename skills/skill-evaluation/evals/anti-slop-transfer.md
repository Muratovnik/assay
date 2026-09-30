# Anti-slop transfer: provenance and evaluation

Maintainer-only material for this bounded transfer. Do not load this document,
case metadata or rubrics while performing a user's UI, code or writing task.
All new cases are synthetic public working/regression data, not private product
incidents, sealed holdouts or evidence that a model improved.

## Decision and source boundary

The baseline is Assay `eebfa847dfc0bd95ff6c0f08162dfad995f18fba`.
The external comparison is anti-slop
`6e28c74d3bbd2bd6547a9ce9cd3c7d0c3f82da9d`, inspected on 2026-09-30.
Sources supply candidate patterns, not authority over Assay's contracts:

- [UI patterns](https://github.com/miqdadbadjuber/anti-slop/blob/6e28c74d3bbd2bd6547a9ce9cd3c7d0c3f82da9d/skills/antislop-ui/SKILL.md):
  transfer implied-state/activity claims and task-based information-display
  questions into the existing UI owners. Preserve justified familiar styling,
  clearly identified demonstrations, analysis without action buttons and the
  distinction between missing evidence and a refuted claim.
- [Comment cleanup](https://github.com/miqdadbadjuber/anti-slop/blob/6e28c74d3bbd2bd6547a9ce9cd3c7d0c3f82da9d/skills/antislop-code/SKILL.md):
  transfer bounded comment editing and information-value assessment, not its
  one/two-line limit or removal of useful issue/version reasoning. Add explicit
  source-comment discovery and preserve machine-active and observable text.
- [Copy examples](https://github.com/miqdadbadjuber/anti-slop/blob/6e28c74d3bbd2bd6547a9ce9cd3c7d0c3f82da9d/skills/antislop-copywriting/SKILL.md):
  use the risk of an unsupported specific replacement as a regression target.
  Assay already owns factual and qualifier preservation; do not add a second
  writing filter or treat example rewrites as evidence for product claims.

The adaptations and fixtures are newly written. No upstream scripts, installer,
core policy, mandatory mode interview, typography blacklist or accessibility
threshold implementation is imported. Normative accessibility criteria remain
with the existing standards-backed procedures; the comparison project is not a
substitute for those sources.

## Owning methods and executable integrity checks

| Area | Runtime owner | Input-only supplement | Evaluator rubric |
| --- | --- | --- | --- |
| Implied claims, data basis and demo context | [UI content](../../ui-delivery/references/content-and-recovery.md#verify-what-the-presentation-implies) | [UI cases](../../ui-delivery/evals/anti-slop-cases.json) | [UI rubric](../../ui-delivery/evals/anti-slop-rubric.json) |
| Task-based dashboards and valid familiar composition | [Visual judgment](../../ui-delivery/references/visual-judgment.md#judge-information-displays-by-their-question) | The same UI supplement | The same UI rubric |
| Bounded comment/docstring edits and audit routing | [Comment procedure](../../code-change/references/comments-and-docstrings.md), [entry point](../../code-change/SKILL.md), [audit consumer](../../independent-audit/references/code-quality.md) | [Comment cases](../../code-change/evals/comment-editing-cases.json) | [Comment rubric](../../code-change/evals/comment-editing-rubric.json) |
| Unsupported specificity and meaning preservation | [Text writing](../../text-writing/SKILL.md#preserve-what-the-text-says) | [Copy cases](../../text-writing/evals/claim-preservation-cases.json) | [Copy rubric](../../text-writing/evals/claim-preservation-rubric.json) |

Each decision case belongs to a causal pair; its counterpart changes the relevant
condition rather than requiring a preferred phrase. The UI supplement covers
status, baseline validity, simulation context, dashboard purpose, real visual
defects versus familiar styling, and absent versus contrary evidence. Comments
cover informational value, workaround relevance, semantic authorization and
observable docstrings. Copy covers benefit evidence, pricing facts and qualifier
preservation. Comment discovery prompts include nearby documentation, ordinary
prose and read-only audit routes.

`tools/test_anti_slop_assets.py` reuses `eval_assets.check_pair` for these files,
checks pair membership and requires nonempty evaluator criteria. It is discovered
by the existing unit-suite gate in `tools/check.py --all`, including the UI
supplement without changing the legacy UI corpus or adding a new runner. The
non-UI supplements are also discovered by `tools/eval_assets.py check`.

```text
python -B -m unittest discover -s tools -p test_anti_slop_assets.py
python -B tools/check.py --all
python .github/relkit.pyz audit
```

These commands check package/corpus integrity, not interpretation of prose or
behavior of a model. Pair membership does not prove causal isolation or a good
oracle; manually review that distinction before a comparison.

## Optional bounded comparison

No paid calls, delegation, service, hook or client configuration change is
required or authorized by adding these assets. With an independently authorized
budget, start with one relevant pair rather than running the whole collection.
Compare actual baseline and candidate bytes with the same input, surrounding
instructions, client, tools, permissions and settings. Keep outputs and execution
receipts outside the published source; inspect changes rather than trusting a
model's completion report.

For code and text, the existing `tools/eval_assets.py prepare` command accepts the
supplement's case file and a selected case ID. Include only explicitly selected
method roots. For UI use the existing [UI evaluation protocol](../../ui-delivery/evals/evaluation.md):
pass only the chosen case's prompt and context with the selected method. The
inline packet command does not currently accept `ui-delivery`; do not claim that
it prepared a UI packet or build a replacement harness to conceal that limit.
Rubrics, pair labels, metadata and previous answers stay outside executor inputs.
Actual filesystem isolation is a separate property that must be recorded.

For discovery, expose the actual enabled collection and send only a selected
`ASCD` prompt without a method hint. Explicitly loading code-change or describing
its route does not establish automatic discovery. These source changes do not
prove that every client will select the intended procedure.

Grade decision correctness, evidence fidelity, authorized effects and delivery
separately. A case about supplied UI facts is not a rendered UI test. A hand
walkthrough is self-review, not independent execution. Comment-only file edits
need their actual language/tooling checks when exercised. Prepare fresh unseen
variants before any generalization claim; these published cases cannot be final
held-out evidence. Record untested behavior and inconclusive comparisons rather
than converting structural checks into quality or token-saving claims.
