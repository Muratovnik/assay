# Contract and reuse drift: transfer decisions

Research scope: 2026-09-25. Implementation baseline:
`8367566419ee0f4ddb8403514d15b1a251beabcf` (planning PR #5), with prior main
`c642a41f9d9c88b252b775514a62fd8c242d7b09`. This is a subject-specific application
of the existing research-and-transfer method, not another rule framework or
runtime checklist. It does not depend on the separate writing-method PR #4.

## Problem and limits of causal attribution

A maintenance outcome can drift through several individually plausible records:
an implementer's narrowed interpretation becomes a decision, a review treats the
decision as the source of acceptance, and a gate protects an intermediate state
without admitting the intended final state. Agreement among the records is not
independent confirmation of the original result or its authorized change.

The motivating report was compared with supplied primary excerpts and static
patches, not a complete execution trace or a current production run. Some existing
criteria already prohibited premature completion and unsupported reuse claims.
The evidence therefore supports testing missing specificity, missed routing,
ignored instructions and weak oracles as distinct explanations; it does not prove
that one more instruction fixes an execution failure. Earlier family-specific
headless preferences and legitimate staged work are counterevidence to a blanket
"all custom styling was forbidden" interpretation.

Private transcripts, file paths, repository snapshots, identifiers and incident
attachments are not reproduced here. Public scenarios are independently authored
synthetic examples preserving only the decision structure. External documentation
below informs a mechanism; it is not evidence of this patch's effectiveness.

## Decisions and observable checks

| Unit | Existing gap or weak boundary | Local transfer and lawful neighbor | Observable check |
| --- | --- | --- | --- |
| P0-A | A decision status could substitute for its authority or source scope | Adapt provenance checks in planning; maintenance and audit keep enough criteria for standalone use. Delegated technical decisions do not require fresh approval. | T01-T04, T14: source-backed scope delta versus pilot, revision or unresolved history |
| P0-B | Delegation examples emphasized mechanics more than standard visual ownership | Extend reuse and component-system criteria to states/themes without banning native controls, facades, branding or deliberately headless families. | T05-T07: trace the actual capability and the precise security/style boundary |
| P0-C | Generic staged-adoption criteria did not discriminate broad exceptions, equal-count substitution or a debt-dependent end state | Extend the existing migration and effective-check procedures; project gates remain project-owned. New authorized exceptions and identity-preserving moves remain possible. | T08-T12, T17: new use, approved basis, last removal, expected coverage and changed premise |
| P1-D | A broad audit could omit system reuse or accept the implementer's reduced premise | Route repeated UI families to existing system criteria; separate decision basis, fitness, conformance and coverage. Narrow reviews remain narrow. | T13-T14: unprompted subject-driven coverage and missing original decision evidence |
| P1-E | Capture or an official kit could be promoted to target-system authority | Distinguish observed UI, intended basis and allowed delta before propagation; inspect version/API/state correspondence. Exact transfer remains exact. | T15-T16: partial mapping and unmapped states versus full correspondence claims |
| P1-F | A new rule or green fixture could be mistaken for repaired behavior | Expand existing transfer/test-audit criteria to challenge false acceptance, false rejection, coverage and terminal states. No model grading by keyword. | T08-T12, T18 plus the separate paired protocol; model outcome remains unverified until run |
| P1-G | Continuity described a plan handoff more clearly than different tasks sharing one goal | Preserve the goal, current authority, verified subset, remainder and version premises in the existing record. Do not resume old writes in a read-only task. | T03, T17: current task boundary and rechecking only affected assumptions |

No additional skill, hook, task database, model router, mandatory approval sequence,
paid design connector or generic debt scanner is introduced. A count of CSS lines,
wrappers, citations or tests is not a completion oracle. Existing canonical owners
keep their responsibilities; short entrypoint changes route the conditional depth.

## Prior work and transfer boundaries

The following reading scope was established in the preceding incident research
on 2026-09-25 and reused here. URLs to moving documentation identify the consulted
method, not a pinned API guarantee. No third-party source, templates or evaluation
samples are copied into the synthetic corpus. No numerical performance claims are
transferred.

- [Superpowers systematic debugging](https://github.com/obra/superpowers/blob/main/skills/systematic-debugging/SKILL.md)
  and [brainstorming](https://github.com/obra/superpowers/blob/main/skills/brainstorming/SKILL.md):
  adapt causal diagnosis, a contrasting working case and separation of need from
  interpretation. Reject universal approval rituals, delegation and fixed retry
  counts as automatic architecture authority.
- [Spec Kit analyze](https://github.com/github/spec-kit/blob/main/templates/commands/analyze.md):
  adapt bidirectional requirement/work/check consistency, adding verification of
  the shared source. Consistent documents can still preserve the wrong goal.
- [OpenSpec](https://github.com/Fission-AI/OpenSpec): adapt visible requirement deltas
  and one current record; do not adopt its CLI, artifact set or an extra tracker.
- [MADR](https://adr.github.io/madr/): adapt the distinctions among decision-makers,
  consulted and informed, plus confirmation of implementation. A filled status
  field does not independently attest authority; delegated decisions remain valid.
- [Atlassian Design System tooling](https://atlassian.design/components/eslint-plugin-design-system/usage):
  adapt concrete component/token/import checks in owner tooling, not framework-
  specific restrictions or a universal ban on native elements and custom styles.
- [ArchUnit freezing rules](https://www.archunit.org/userguide/html/000_Index.html#_freezing_arch_rules)
  and [ESLint suppressions](https://eslint.org/docs/latest/use/suppressions): adapt
  known-debt separation and controlled baseline updates, not a Java dependency or
  the assumption that every suppression scheme identifies violations precisely.
- [ESLint issue 21226](https://github.com/eslint/eslint/issues/21226): a reporter's
  count-based masking example motivates equal-count replacement. That external
  issue was not reproduced here; the supplied Python examples are separate,
  deliberately simplified counterexamples, not tests of ESLint itself.
- [Figma Code Connect](https://developers.figma.com/docs/code-connect/) and
  [Storybook visual tests](https://storybook.js.org/docs/writing-tests/visual-testing):
  adapt explicit design/code correspondence and state comparison. Mapping does not
  prove rendering or delegation, and no paid service becomes a required tool.
- [Long-running agent harnesses](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)
  and [agent evaluations](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents):
  adapt durable partial progress, actual outcomes and balanced invalid/valid cases.
  Reject an automatic harness installation, parallel campaign or generalization
  from different models or settings to this change.

## Evaluation and release claims

The [integration protocol](../../code-maintenance/evals/contract-drift-protocol.md)
keeps 36 inputs separate from semantic rubrics, defines an initially bounded
12-run paired pilot and separates native discovery from selected-method behavior.
All current cases are exposed authoring data, not independent holdouts.

Deterministic checks can establish structural validity, exact packet contents,
postflight byte integrity and the synthetic examples' documented counterexamples.
Only captured executions can establish model selection, behavior or comparative
results. Record actual commands, revision and limits in the PR; do not convert
fixture passes into production regression protection, independent review,
measured quota savings or a guarantee that the incident class is eliminated.
