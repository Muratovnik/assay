# Architecture method: research and transfer

Maintenance record, not mandatory runtime reading. Research cutoff: 2026-09-25.
Assay baseline: `c642a41f9d9c88b252b775514a62fd8c242d7b09`. The agreed implementation
extracts a standalone method rather than placing design inside code-change.

## Capability and evidenced consumers

The shared capability is choosing and assessing architectural boundaries,
contracts, ownership and placement. Existing code-change already makes
these decisions during changes; existing independent-audit already assesses
ownership, dependencies, discovery and migration. Their source responsibilities
establish concrete demand, not a claim of completed external deployments.

Code-maintenance consumes decisions and keeps implementation, tests and migration
execution. Independent-audit consumes criteria and keeps read-only authority,
independent evidence, coverage and verdicts. Implementation-planning routes boundary
decisions here and keeps sequencing. The method is also directly usable for a
design/placement request. Cross-links are real integration points, while native
selection and improvement still need observed client runs. The authoring contract
counts existing skills and distinct recurring workflows as consumers; a hypothetical
caller is still not evidence.

## Decisions transferred

| Protected decision | Existing coverage and gap | Transfer | Valid control and check |
| --- | --- | --- | --- |
| Separate actual, target and assessed architecture | Maintenance and audit had ownership criteria; target choice lacked an independent entry | Adapt levnikolaevich's separation of current architecture, proposal and assessment, not its complete workflow | A small placement question needs no system design; ARC-01/02/14 |
| Choose boundaries by scenarios and cost | General maintainability criteria existed | Adapt arc42 usage/change scenarios and real alternatives | One feasible option needs no invented competitor; ARC-13 |
| Preserve shared architectural invariants | Audit already distinguished canonical sources/projections | Adapt BMAD Architecture Spine's agreement boundaries, not memlog or reviewer gates | File inventories can remain revision-bound, not permanent duplicate truth; ARC-12/14 |
| Connect decisions to implementation | Implementation/migration already had an owner | Adapt Superpowers file responsibility and interfaces | Do not require every decision to have a new document; ARC-01 |
| Place code by semantic ownership | Keep Assay's narrow owner and meaningful extraction rules, move shared criteria to one method | Adapt FSD's causal growth examples and conditional profiles; reject universal multi-consumer extraction requirement | One lifecycle owner versus trivial expression; ARC-03/04/11 |
| Respect framework reachability and lifetime | Vue and migration procedures existed | Extend Vue organization/SSR and framework discovery examples | Immutable shared data and deliberate framework entry points; ARC-05/06 |
| Preserve exports and effective coverage | Existing migration and effective-check procedures remain canonical | Add Node entry points and architecture-rule controls | Supported facade, separate valid checker; ARC-07/08/09 |
| Adopt checks incrementally without hiding violations | No new scanner is needed | Adapt explicit baseline idea from ArchUnit; use fitting existing project tooling | Agreed debt reduction versus refreeze of new debt; ARC-10 |
| Separate integration from behavioral evidence | skill-evaluation already owns comparison discipline | Reuse existing paired evals and file-backed audit snapshots | Explicit loading is not automatic discovery; discovery cases and packet tests |

These are original Assay instructions informed by the sources below. No upstream
code, instruction file or workflow is vendored. Before any later verbatim/code
transfer, verify the selected revision's license and attribution requirements.
Popularity, source inspection and these synthetic cases are not evidence of
superior task outcomes or lower cost.

## Primary sources and limits

- [Assay authoring contract at the baseline](https://github.com/Muratovnik/assay/blob/c642a41f9d9c88b252b775514a62fd8c242d7b09/AGENTS.md) and its maintenance, audit, skill-evaluation and test-writing methods: preserve existing authority and tooling owners.
- [levnikolaevich architecture proposal](https://github.com/levnikolaevich/claude-code-skills/blob/master/plugins/architecture-suite/skills/ln-23-system-design-proposal-builder/SKILL.md): process comparison, not an executed benchmark.
- [Feature-Sliced Design skill](https://github.com/feature-sliced/skills): v2.1-oriented guidance and educational examples, not a universal framework contract.
- [BMAD architecture](https://github.com/bmad-code-org/BMAD-METHOD): agreement/invariant idea; no mandatory memory system, subprocess or review quorum imported.
- [Superpowers writing plans](https://github.com/obra/superpowers/blob/main/skills/writing-plans/SKILL.md): responsibilities and concrete paths, not mandatory sequential approval gates.
- [arc42 quality scenarios](https://docs.arc42.org/section-10/): distinguish use and change scenarios; no claim of running full ATAM.
- [Vue composables](https://vuejs.org/guide/reusability/composables.html#extracting-composables-for-code-organization) and [SSR](https://vuejs.org/guide/scaling-up/ssr.html#cross-request-state-pollution): organization and request-lifetime controls; actual project version still matters.
- [Next.js structure](https://nextjs.org/docs/app/getting-started/project-structure): special entry files and colocation, not evidence about an unidentified installed version.
- [Node package entry points](https://nodejs.org/api/packages.html#package-entry-points): public export compatibility; validate a real built consumer before claiming preserved operation.
- [dependency-cruiser rules](https://github.com/sverweij/dependency-cruiser/blob/main/doc/rules-reference.md) and [ArchUnit freezing rules](https://www.archunit.org/userguide/html/000_Index.html#_freezing_arch_rules): enforcement/baseline mechanisms, not dependencies added to Assay.

Moving-branch links are navigation aids, not immutable source identities. The
prior research supplied the wider selection; this implementation does not claim
new experiments for every source. More-specific current tool/stack decisions
require checking their installed versions and applicable primary documentation.
