# Architecture and migration

Use for architecture proposals, application structure, ownership changes,
standardization, relocation, discovery and retirement. Follow the actual system;
do not prescribe a service boundary or repository layout merely because it is named.

## Assess architecture without taking implementation authority

Use [software architecture](../../software-architecture/SKILL.md) as the criteria
owner: its [current architecture](../../software-architecture/references/current-architecture.md)
procedure reconstructs owners, dependencies, state and flows, and its
[assessment](../../software-architecture/references/architecture-assessment.md)
procedure separates proposal fitness from implemented conformance. Load only the
relevant branches, not an implementation workflow. This audit keeps authority,
coverage, evidence statuses and the verdict, and treats the implementer's
architectural rationale as a claim to check. Trace the affected owner and discovery
chains below for migration.

## Trace migration through actual consumers

For a staged implementation adoption, verify the
[scope and continuation criteria](../../code-maintenance/references/reuse-and-migration.md#keep-staged-adoption-tied-to-the-request)
against the original brief. A completed pilot establishes only its accepted
subset; an explicitly scoped pilot does not imply whole-system retirement.

For every material object establish:

`old mechanism -> canonical replacement -> consumers switched -> retirement or justified compatibility`

A new directory proves existence, not cutover. Follow callers, registrations, configuration, startup scripts, docs, and observed execution. Verify both required preservation and required absence: retained bytes, loaded configuration, executable routes, and exposed interfaces have different effects. A legitimate backup or compatibility need does not alone justify leaving an old path active or accessible to another consumer. Independently versioned roots need a source vector, not one repository's HEAD presented as the identity of all roots.

For retained compatibility seek its current consumer or requirement, owner, limited purpose, source-of-truth direction, and retirement condition or explicitly supported lifetime. Do not demand retirement when support is required. Missing documentation makes the role uncertain, or establishes a documentation gap if the contract requires it; it does not prove a second implementation. Demonstrate independently authoritative behavior before alleging duplicated truth.

Compare standardization across placement, discovery, configuration, startup, diagnostics, and lifecycle. Record justified differences; shared naming is insufficient, and identical shapes are not always appropriate.

Choose migration scenarios by risk: adding a consumer, renaming the canonical source,
starting a clean client, or independently upgrading or rolling back an owner. Identify
required edits, manual synchronization, crossed boundaries, hidden historical knowledge
and failure detection. For structural relocation, apply the implementation method's
[public-contract preservation criteria](../../code-maintenance/references/reuse-and-migration.md#preserve-structural-and-public-contracts)
as review criteria without changing the subject.

## Investigate legacy references

Derive search terms from the brief, baseline, diff, and former layout: names, paths, launchers, symbols, keys, registrations, aliases. Verify quoting and search coverage, including relevant ignored/generated/external state without sweeping unrelated caches or private data.

Combine text search with dependency/loading analysis, configuration, and appropriate client/runtime observations. Dynamic discovery or external consumers can keep a resource active despite zero imports.

Classify meaningful results:

- CLEAN: the applicable migration contract is met, including consumer use.
- ACTIVE LEGACY: an old mechanism still participates where replacement or retirement was required.
- DEAD REFERENCE: current guidance or configuration points to an obsolete/unavailable target.
- INTENTIONAL TRANSITION: justified compatibility for a real consumer or requirement.
- INTENTIONAL HISTORICAL REFERENCE: retained history, not current operating instructions.
- UNCERTAIN: the role cannot yet be established.

Dispose of consequential false positives explicitly, without listing every harmless match. A dated archive and a current setup command can mention the same path but have different roles. These classifications answer the migration question only; intentional history or transition must still satisfy any applicable audience, distribution, and lifecycle constraints.

## Verify edges and lifecycle

Trace critical chains end to end:

`consumer -> discovery -> configuration -> path/registration -> resource -> execution`

Check ambiguous/duplicate discovery as well as missing nodes. Inspect applicable globs, symlinks, environment variables, working directories, generated registries, and launch conventions. Node existence does not prove the chain works.

Where promised, test reproducible and idempotent clean setup. Can a fresh client find the intended resource? Do diagnostics detect mixed old/new state, wrong identity, and missing consumer exposure, rather than only files? Does documented bootstrap use the new chain?

Do not switch live registrations or restart services to finish an audit. Use an authorized isolated client or report missing integration evidence. Preserve service/data identity; assess rollback against the complete recorded vector, not mixed old/new components.

## Report this mode

Include expected versus actual architecture and an evidence-backed coherence assessment (YES, PARTIAL, NO); a migration matrix with expected/observed state, evidence, and classifications; and unresolved dependencies or integration evidence affecting acceptance. Scale detail to scope. Migration classifications are distinct from claim statuses and the final verdict: one CLEAN path does not accept the whole change.
