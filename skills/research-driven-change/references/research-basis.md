# Research basis and transfer decisions

Maintainer material, not a prerequisite for executing the method. The design
research was read on 2026-09-26 and reconciled with Assay source at
`28fd8817fcc408d07fbfd2ac7ad47c4fd9ae218a` (0.7.0). Linked upstream branches are
mutable. These sources establish documented mechanisms, not measured superiority,
token savings or a guarantee that an instruction will be followed.

## Local fit and existing owners

The recurring consumers are skill-behavior changes assessed by `skill-design` and
executable/tooling changes implemented by `code-maintenance`, both following
research and leading to review and delivery. Their conditional return links use
one handoff method with distinct domain criteria. This capability is not a second
implementation of research, planning or skill evaluation.

Assay already owns [continuation](../../implementation-planning/references/continuation.md),
[contract changes](../../implementation-planning/references/scope-and-readiness.md#check-material-changes-to-the-contract)
and [skill transfer](../../skill-design/references/research-and-transfer.md).
Retain those owners rather than copying their rules. The new boundary is deciding
which supported and authorized transition is next and whether the requested
endpoint was attained.

## Examined mechanisms

- **Compound Engineering:** [lfg](https://github.com/EveryInc/compound-engineering-plugin/blob/main/skills/lfg/SKILL.md)
  and [ce-plan](https://github.com/EveryInc/compound-engineering-plugin/blob/main/skills/ce-plan/SKILL.md)
  separate stages and returns to an owning workflow. Adapt the returned result,
  evidence and outstanding work, not its whole autonomy policy or required stage
  sequence. The inspected ce-plan blob was
  `0e244c0f1e9f01748e7d698102cca4b0c72b1743`. Local check: a full delivery request
  continues after research, but a plan-only request does not execute.
- **OpenSpec:** [OPSX](https://github.com/Fission-AI/OpenSpec/blob/main/docs/opsx.md)
  describes dependent artifacts, a research-first example and nonlinear updates.
  Adapt entry at the unresolved dependency and affected-only updates. Do not add a
  schema engine or treat file presence as sufficient readiness. Local check: a
  valid existing plan avoids a new survey; a stale premise refreshes its dependents.
- **Spec Kit:** [idea assessment](https://github.github.io/spec-kit/reference/agentic-assessment.html)
  and [agentic SDD](https://github.github.io/spec-kit/reference/agentic-sdd.html)
  separate evaluation of an idea from execution and describe consistency work.
  Adapt evidence against a proposal and an explicit remaining gap. Reject an
  obligatory document set or an unlimited convergence loop. Local check: retaining
  an adequate solution is valid, but does not fabricate implementation delivery.
- **Superpowers:** [brainstorming](https://github.com/obra/superpowers/blob/main/skills/brainstorming/SKILL.md)
  distinguishes work depth; [receiving code review](https://github.com/obra/superpowers/blob/main/skills/receiving-code-review/SKILL.md)
  checks feedback before acting. Adapt proportionality and reasoned rejection of
  incorrect feedback, not extra approval rituals over an already authorized task.
  [Issue 895](https://github.com/obra/superpowers/issues/895) is an individual report
  of overly detailed plans and duplicated test instructions, not an effectiveness
  estimate. Local check: a valid neighboring case survives a proposed safeguard.
- **HumanLayer:** [research_codebase](https://github.com/humanlayer/humanlayer/blob/main/.claude/commands/research_codebase.md)
  documents current code with exact references and historical context. The
  inspected blob was `543bf509c2995cdd4ff319efc60d06a9e1789b96`. Adapt the identified
  subject and portable evidence. Do not import mandatory parallel agents or assume
  that describing local code replaces researching alternatives. Local check: one
  selected project/revision remains identifiable after a handoff.
- **GSD Core:** [verify and ship](https://github.com/open-gsd/gsd-core/blob/next/docs/how-to/verify-and-ship.md)
  was examined on `next`, not established as an installed stable release. Adapt
  verification freshness, gap closure and separate proposal/merge claims, not the
  executor, fixed context budgets or implicit approval. Local check: an old pass
  does not certify a changed revision, while a requested draft may retain pending
  CI without being mislabeled green.
- **Oldhand:** [README](https://github.com/berwinsingh/oldhand) describes inspecting
  existing solutions before local implementation and end-to-end verification.
  Reading scope was the README, not an implementation audit. Adapt local fit and
  the actual endpoint; reject permanent model choices or an imported universal
  dependency/license policy. Local check: a popular but incompatible candidate is
  not adopted solely because it is popular.

Evaluation setup also draws a limited comparison with
[Anthropic's skill creator](https://github.com/anthropics/skills/blob/main/skills/skill-creator/SKILL.md#running-and-evaluating-test-cases):
it separates prior skill snapshots from per-run outputs. Retain that distinction
between immutable evidence and an editable subject without importing a parallel-run
policy or adding an evaluation service. The local packet verifier protects the original
snapshot; an authorized repair is assessed in a separate working copy.

The small, explicit handoff account also fits the failure modes described in
[Anthropic's long-running agent experiments](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents):
premature completion and lost context. That report is bounded experimental
experience, not evidence that this Assay method improves every model or task.

## What must be tested separately

The evaluator corpus has plan-only/full-delivery controls, skill and adapter
consumers, retain/adapt decisions, resume and feedback cases, publication evidence
and negative activation. It specifies how to challenge this design; it is not a
record of executed model runs. Use the existing evaluator packet tooling and a
frozen current-Assay baseline. A manual walkthrough is self-review, structural
gates validate packaging, and neither proves discovery or behavioral improvement.
