# Architecture design

Use for a new system or a material change of boundaries. For existing software,
first apply [current architecture](current-architecture.md) to the affected part.
A local placement decision can use [file placement](file-placement.md) directly.

## Ground the problem

Identify the intended users/consumers, operation or change to support, non-goals,
owner-adopted constraints and support obligations. Include actual delivery and
operating constraints where relevant: existing stack, team/release ownership,
data sensitivity, availability, migration and reversibility. Do not invent traffic,
SLOs, independent teams or external consumers to justify a preferred design.

State material unknowns and what would discriminate the alternatives. Reuse the
brief and repository answers. A missing fact need not block unrelated decisions;
if it determines a costly irreversible choice, keep that choice conditional.

## Compare on scenarios

Select only load-bearing scenarios: a normal operation, a likely change, or a
significant failure. Specify the stimulus/change, context, expected response and
observable criterion as far as evidence allows. Consider quality trade-offs rather
than declaring a design universally scalable, secure or maintainable.

Compare real alternatives including retaining current boundaries or a simpler
arrangement. For each viable option, identify which scenarios it satisfies,
compromises, coordination costs and the evidence behind those judgments. One viable
option needs an explanation of the excluding constraints, not an invented rival.
A bounded spike may answer a concrete uncertainty; it is not authority for a paid
campaign, new tooling platform or repeated testing until a preferred result appears.

## Define the chosen boundaries

For consequential parts decide:

- Responsibilities and reasons for change; the public operation and permitted
  dependencies, including what callers must not know.
- Ownership of data, mutation and lifecycle; derived state, drafts and caches with
  explicit reconciliation rather than accidental competing sources of truth.
- Contracts at the boundary: inputs/outputs, errors, versioning and compatibility;
  atomicity, cancellation, retry or idempotency only where the scenario needs them.
- Runtime, deployment and trust boundaries separately from folders and modules;
  failure isolation, authorization or operating cost where affected.

Decide sharing, extraction and location with [file placement](file-placement.md),
not a universal layer tree.

For decisions multiple implementers must share, state who follows the invariant,
which incompatible choices it prevents, its rationale and how conformance is checked.
Avoid incidental naming mandates unrelated to consistency. Independent implementation
is not permission to introduce services, queues or separately released packages.

## Connect design to delivery

For each material decision retain this chain in the existing plan, design document,
ADR or response, scaled to scope:

`requirement/scenario -> decision -> owner -> public contract -> placement -> check -> reconsideration condition`

Include the simplest rejected alternative and actual complexity cost. Distinguish
proposed decisions from owner-adopted ones and from verified implementation. Keep
rationale with the invariant, not only in a conversation or separate memory system.
Initial file paths guide implementation; label full inventories with the examined
revision and avoid maintaining a second editable copy of the repository tree.

Turning adopted decisions into units, dependencies and acceptance belongs to
available [implementation planning](../../implementation-planning/references/implementation-units.md);
the implementation method owns execution and
[migration](../../code-change/references/reuse-and-migration.md).

## Check fitness before handoff

Walk the selected scenarios through the design, including boundary handoffs and
important failure recovery. Locate decisions that require synchronized knowledge,
leave mutation ownerless or make a required contract untestable. Name support and
migration cost, reversible steps, and the conditions that would change the choice.
Code rollback does not restore migrated data by itself.

Use existing project checks for formalizable restrictions; their effectiveness is
established by [effective quality checks](../../code-change/references/effective-quality-checks.md),
not by configuration presence. Leave unexecuted checks explicitly proposed. A small
site may need only a local owner and a short explanation, not a new architecture file.
