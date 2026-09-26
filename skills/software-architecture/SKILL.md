---
name: software-architecture
description: Design and assess application, site or library boundaries, contracts and file placement. Use for architecture proposals, structural decisions and architectural review criteria; skip routine local edits, prose polishing, implementation sequencing and audit authority or verdicts.
license: MIT
---

# Software architecture

Choose and assess boundaries by the requirements they protect, not by a preferred
pattern or folder tree. This is the shared architectural method for direct design,
implementation decisions and independent review; it is not an implementation
workflow, automatic audit gate or a second source of product requirements.

## Establish the decision and authority

Recover the requested outcome, scope, adopted rules, available evidence and
allowed effects. Reuse supplied answers and inspect relevant existing artifacts
before asking for missing facts. Resolve only uncertainty capable of changing a
material decision; name nonblocking assumptions and continue useful work.

A proposal or placement question does not authorize application changes. A request
that already authorizes implementation needs no extra approval ceremony. Use
[code-maintenance](../code-maintenance/SKILL.md) for that work, and available
[implementation-planning](../implementation-planning/SKILL.md) to sequence adopted
decisions into units and handoffs; the boundary decisions stay here. For an
independent review, [independent-audit](../independent-audit/SKILL.md) owns
read-only authority, evidence, coverage and verdicts; it consumes these criteria,
not the implementer's conclusions. Follow the current task's stricter boundary
without recursively starting another workflow or creating an automatic reviewer
assignment.

## Select only the needed procedure

| Decision | Read |
| --- | --- |
| Understand existing owners, dependencies, state or execution | [Current architecture](references/current-architecture.md) |
| Compare designs or materially change system boundaries | [Architecture design](references/architecture-design.md) |
| Place, split or share code and choose its public surface | [File placement](references/file-placement.md) |
| Assess a proposal or implemented architecture | [Architecture assessment](references/architecture-assessment.md) |
| Apply explicitly adopted FSD, or evaluate it as a named candidate | [FSD profile](references/fsd-profile.md) |
| A concrete boundary decision needs an explanatory contrast | The relevant section of [worked examples](references/architecture-examples.md) |

Do not read every reference for every edit. Local placement does not require a
system design exercise; a small site does not imply distributed-system sections.
Observe framework/build conventions before choosing organization. Verify material
version-sensitive premises through the project's official documentation or the
available [evidence-research](../evidence-research/SKILL.md) method. Existing,
still-applicable evidence need not be researched again.

## Preserve the decision contract

Connect each material decision to its requirement or scenario, responsible owner,
public contract, placement, check and condition for reconsideration. Include the
cost and the simplest viable alternative; do not manufacture alternatives or
numerical requirements. Physical, semantic, deployment and trust boundaries are
different choices. A module need not be a service, package or separate repository.

Keep observed implementation, documented intent, inference and unknowns distinct.
Likewise distinguish proposed, owner-adopted and implementation-verified decisions.
A walkthrough or future test is not execution evidence. File counts, cycles and
pattern labels prompt investigation; only an applicable contract or supported
consequence justifies a defect. Explicit owner constraints still apply.

Return the smallest useful result in the requested artifact or conversation. Keep
durable invariants and rationale together; label inventories with their revision
instead of maintaining a second complete tree by hand. No mandatory ADR, diagram,
score, scanner, new dependency, model choice or subagent process.

`evals/` contains input corpora, grading keys and evaluation records, not task
instructions. Do not read it while designing, implementing or auditing a user's
system. Source attribution there is for method maintenance, not mandatory runtime
reading.
