# Architecture assessment

Use as criteria for a proposal review or an implemented system. The
[independent audit](../../independent-audit/SKILL.md) method owns independence,
read-only effects, coverage, evidence statuses and verdicts. Do not create a parallel
severity scale or silently turn self-review into independent evaluation.

## Choose the subject

For a proposal, compare requirements, assumptions, alternatives, boundaries, contracts,
state ownership and proposed checks using [architecture design](architecture-design.md).
A complete proposal is not proof of runtime conformance. Identify missing consequential
decisions without inventing requirements for a different product or scale.

For implementation, reconstruct the relevant [current architecture](current-architecture.md)
and compare it with the adopted contract and required scenarios. Trace entry points,
public interfaces, imports/aliases/re-exports, mutation ownership and critical execution
paths. Read the actual code behind a facade. A target diagram or folder name is not
proof of use; an implementer's explanation is evidence to check, not the verdict.

Review [placement](file-placement.md) when location, sharing or extraction is at issue;
read the [FSD profile](fsd-profile.md) only when adopted or explicitly being evaluated.
Use the auditor's [migration procedure](../../independent-audit/references/architecture-and-migration.md)
for cutover, discovery, preservation, compatibility and retirement.

## Test the material differences

For each concern connect criterion, source location, expected/observed scenario and
consequence. Check who edits authoritative data, which consumers must agree, and how
failure or a likely change crosses boundaries. Seek counterevidence: intentional
shared lifetime, immutable data, supported compatibility, generated projections,
framework discovery, scoped exceptions or equivalent valid architectures.

Distinguish a violated owner-adopted rule, a supported harmful dependency, an optional
improvement, a valid exception and missing evidence. Do not call an unadopted preference
a historical violation. Conversely, an explicit owner constraint still matters even
when the implementation functions or the auditor prefers another design.

Cycles, large files and high fan-in can direct inspection but are not universal defect
thresholds. Claims of absence or inactivity follow the evidence rules of
[current architecture](current-architecture.md). For formal rules apply the
[architectural restrictions](../../code-change/references/effective-quality-checks.md#architectural-restrictions)
of effective checks.

## Return to the owning review

Provide the covered decision or flow, applicable criterion, evidence, supported
finding or valid result, and material unknowns. Keep proposed checks separate from
executed checks and static reasoning separate from observed runtime behavior. The
auditor's report and verdict decide what this coverage establishes.
