# Long-horizon planning

Use for work spanning milestones, migrations, external dependencies or handoffs.
A long autonomous session is not itself evidence of a sound long-term roadmap.

## Keep two connected levels

Maintain the overall outcome and milestone dependencies; detail the next ready
stage in implementation units. Later stages carry outcomes, important interfaces,
unknowns and conditions for refinement, not speculative file-by-file code.
Refine a stage when its prerequisite evidence or owner decisions arrive. Do not
hide a known required deliverable merely because its internal design is deferred.

For each milestone establish its result, conditions to start and finish, major
uncertainties, affected consumers and reason for its position. Distinguish a real
external dependency from a preferred order. Critical blockers and unavailable
owners stay visible. Cycles require a contract decision or compatible intermediate
state, not arbitrary ordering. Use the existing project tracker or task rather
than introducing a competing roadmap.

Where integration is the principal uncertainty, prefer an early working slice
through the affected boundaries, with a representative and risky case. A probe,
pilot and production increment have different acceptance and retention conditions.
A backend-only change does not need invented UI work to be called end-to-end.
A mechanical, well-understood migration need not repeat an unnecessary prototype.

For actual calendar commitments distinguish a required deadline, an estimate and
the allowed investment. Identify assumptions about capacity, external owners and
lead times before offering dates. Unknown resources remain unknown. Prioritize
required outcomes and risk-reducing work before optional polish, subject to the
user's actual priorities; do not impose another team's sprint length.

## Staged adoption and retirement

Follow the existing [reuse and migration](../../code-change/references/reuse-and-migration.md)
criteria for behavior ownership, compatibility, completion scope and the record of
switched consumers. This procedure owns sequencing and refinement, not a second
migration inventory.

Define compatibility while old and new coexist, the evidence permitting retirement,
and a safe recovery path where the change is consequential. An irreversible step
needs prerequisite validation, a recovery/compensation strategy or explicit risk
acceptance; do not promise a rollback that cannot restore the relevant data.

## Example: migrate shared controls

1. Establish the in-scope controls, consumers and preserved interaction contracts.
2. Validate a representative and a risky integration with the actual primitive.
3. Migrate remaining consumers by the confirmed pattern, recording exceptions.
4. Remove the old mechanism only after its active consumers are accounted for.
5. Reconcile the complete requested scope and actual regression evidence.

Initially detail the integration stage; later stages retain their outcomes and
entry/exit conditions. If the risky case cannot preserve focus behavior, settle
configuration, a justified adaptation or an owner-approved exception before broad
propagation. Do not keep migrating because the easy case passed.
