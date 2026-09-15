# Architecture and migration

Use for ownership changes, standardization, relocation, discovery, and retirement. Follow the actual system; do not prescribe a registry, service boundary, or repository layout merely because this reference names it.

## Reconstruct ownership and authority

Map material components against the brief:

| Component | Intended owner | Canonical source | Consumers | Discovery/configuration path | Lifecycle owner |
| --- | --- | --- | --- | --- | --- |

Compare expected and observed ownership, dependency direction, and authority. Physical nesting is not ownership; an interface such as MCP does not alone define an independently operated service.

Separate canonical inputs, generated projections, installed state, caches, and history. Similar bytes are not automatically duplicated truth: determine who edits them, how they propagate, and whether independently authoritative copies can diverge.

Select representative scenarios by risk: adding a consumer, renaming the canonical source, starting a clean client, or independently upgrading/rolling back an owner. Identify required edits, manual synchronization, crossed boundaries, hidden historical knowledge, and failure detection. A walkthrough supports reasoning, not a claim that the scenario ran.

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
