# Review and replan

Use when reviewing a plan or when requirements, assumptions, interfaces, checks
or external constraints change. Keep the original brief and actual authorization
as the acceptance source, not the plan's own checklist.

## Review the substance

Check groundedness, scope, justified decisions, feasible dependencies, shared
contracts, unit acceptance and the readiness of the next action. Trace requirements
to planned results/checks and units back to their purpose. Challenge a consequential
failure or recovery scenario and a nearby valid case where a restriction might
be too broad. Do not grade headings, word count or the number of tasks as quality.

Separate a blocking gap, a legitimate later unknown and an optional improvement.
Explain which result is affected and what evidence or decision would resolve it.
An unavailable future measurement need not block shipping verified behavior unless
the brief makes it a prerequisite. Missing evidence is not proof of failure.

A sound small plan need not undergo fixed repeated passes or numeric scoring.

## Replan the affected work

Trigger reconsideration for a changed requirement, falsified assumption,
incompatible interface, meaningful failed check or changed resource/dependency.
First determine whether the result violates an unchanged requirement or the owner
has actually changed that requirement. Existing code is not authority to rewrite
the brief retroactively until it appears correct.

Identify affected decisions, units, downstream dependencies and acceptance evidence.
Keep still-valid work and record why other evidence became stale. Update scope,
sequence, contracts and checks together; preserve stable IDs and note superseded
units or split relationships. A plan revision does not silently renew permissions.
Do not reopen unrelated resolved questions or repeat an unchanged research survey.

Keep a compact decision history: what changed, why, its source/owner, consequences
and remaining question. Use the existing task, not a second log. Where ownership
or authority is unresolved, keep that dependency explicit and continue independent
work only within the current permission boundary.

## Example: synchronous result becomes a background job

An approved move to asynchronous processing changes more than the endpoint. Review
pending, departure/return, failure, retry and result retrieval contracts as applicable.
The old immediate-success test may remain useful for a different path, but it does
not establish the new job lifecycle. Retain valid unrelated validation tests and
update affected units and checks. Without approval for that behavior change, a
background-job implementation is a deviation to investigate, not a reason to
silently rewrite the requested synchronous contract.

## Delivery

State the scoped conclusion, blocking gaps, still-ready work and continuation
conditions. 'Implementation exists', 'checks executed' and 'required result verified'
are different claims. Preserve partial, blocked and unavailable evidence explicitly.
Acceptance of a plan does not prove implementation or authorize publication.
