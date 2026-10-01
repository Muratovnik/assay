# Delegation patterns and counterexamples

Read the pattern relevant to a candidate from
[delegation planning](delegation-planning.md). These examples are not a fixed team,
minimum number of workers, model policy or permission to delegate.

## Independent research

**Use:** split questions whose answers can be established separately. For a
repository change, one worker might map current client limitations while the
primary inspects local integration points. Return source identities, findings,
uncertainties and their consequences for the pending decision.

**Do not split yet:** several failing tests may share one underlying cause.
Establish the common boundary first rather than assigning each symptom to a
writer. Independent evidence gathering can still be useful without simultaneous
repairs. Do not repeat the worker's source survey in the primary by default.

## Context isolation

**Use:** a bounded investigation needs many logs, documents or repository files,
while the primary needs a compact finding with addressable evidence. Give the
worker the question and sufficient access, not all conversation history.
Sequential delegation is valid when isolation is the actual benefit.

**Keep local:** one short lookup already in context does not justify briefing,
launching and integrating another agent. A task needing continuous exchanges
about the primary's evolving assumptions may not have a useful isolated boundary.

## Cohesive implementation

**Use:** delegate an outcome with a stable interface and clear ownership. Let the
worker perform its permitted local cycle of understanding, implementation,
focused checks and repair. The primary owns shared decisions and final integration.

**Defer or serialize:** the outcome depends on an unresolved contract, or writers
share a database, port, generated output or other mutable resource. Different
source paths are not enough. Follow [writing and integration](writing-and-integration.md),
which owns the resource and acceptance guarantees.

## Independent verification

**Use:** a material risk benefits from a distinct evidence challenge. Specify the
risk and original acceptance without giving the desired verdict. Dispatch once
the decision or candidate to check exists, not merely because implementation
started. Use [review and continuity](review-and-continuity.md) for the existing
reviewer modes, tool boundaries and same-finding repair.

**Keep local:** a deterministic check fully answers a small question, or a second
review would repeat the same evidence without a distinct risk. Do not require an
implementer-plus-reviewer pipeline for every minor edit. A late ceremonial review
does not replace early useful delegation that the primary already duplicated.

## Competing hypothesis

**Use:** progress is blocked by a specific uncertain explanation. Ask for evidence
that could refute a named alternative, with a stopping condition and a useful
return even when the hypothesis is false. The primary compares the resulting
evidence, not a vote between agents.

**Keep local or reframe:** "try again" with the same inputs and no discriminating
question merely repeats the work. Do not start agents until one gives a preferred
answer, and do not automatically escalate the model after a tooling failure.

## Batch of related changes

**Use:** group small changes that share a contract and verification method into
one checkable outcome. A worker can update several related consumers together
rather than receiving one spawn per file or tool call.

**Separate or retain:** unrelated changes with different ownership and acceptance
are not one bounded packet just because both are small. Conversely, a short
linear edit may be cheaper and clearer locally. Neither file count nor the
presence of several steps decides the boundary.

## Example across a task's lifetime

A request asks for a researched repository change with subagents. After enough
reconnaissance to frame the work, the primary can delegate a bounded external
comparison while retaining local architecture inspection. Once a shared contract
is chosen, a previously deferred implementation can become ready. If the stable
candidate has a material risk, an independent check can then become useful.

Each launch has a different readiness condition and a named use for its result.
This is not an instruction to launch all three roles or run them concurrently.
The primary must integrate findings, preserve resource boundaries and close the
actual outcomes rather than treating the number of launches as success.
