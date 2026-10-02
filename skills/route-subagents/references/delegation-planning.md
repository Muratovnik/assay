# Delegation planning

Use after the skill's authorization check when the user requests subagents,
useful work is being left in the primary, or the split and launch timing are
unclear. This procedure chooses work, not models. The primary keeps the existing
plan, acceptance and integration; no separate planner agent or task store.

## Find useful outcomes before roles

Recover the goal, constraints, current evidence, dependency state and actual
client capabilities. Brief reconnaissance can establish a boundary; it must
not quietly complete the prospective worker's assignment. Reuse sufficiently
current research and plans instead of restarting them.

A candidate needs an outcome or question, the evidence or artifact to return,
and a decision or deliverable that will consume it. If the primary cannot say
how it will use the return, clarify the boundary before dispatch. Uncertainty
can justify a bounded investigation; it does not justify an unbounded task to
"explore everything".

Look for independent questions, context-heavy work with a compact useful return,
a cohesive implementation behind a stable contract, material independent
verification, a falsifiable competing hypothesis, or a batch of related small
changes. For an unfamiliar split, read the relevant
[patterns and counterexamples](delegation-patterns.md), not every pattern.

Compare the prospective benefit with briefing, context transfer, coordination,
verification and likely repair. Do not invent numerical benefit scores, quota
prices, universal worker counts or benchmark runs. Use available budget and
concurrency limits; unknown limits are not permission for unbounded fan-out.
A few independent outcomes are not a reason to add permanent specialist roles.

## Choose the decision and the moment

| Decision | Condition | Required next step |
| --- | --- | --- |
| `local` | The benefit does not justify the handoff, or the work cannot usefully be separated | Keep the outcome with the primary; explain the reason when it matters to an explicit delegation request |
| `delegate_now` | The outcome is useful, inputs sufficient and execution permitted and available | Prepare its bounded packet and route it before duplicating its work locally |
| `delegate_after` | Useful work waits on a named decision, artifact, isolated resource or capacity | Record the specific readiness trigger and revisit when it changes |
| `blocked` | Required delegation cannot execute under the current capability or constraints | Name the missing capability or conflict; preserve the unfulfilled requirement |

These labels annotate an existing outcome-sized unit when needed. They are not
MCP fields, persistent statuses or a mandatory ledger. A simple question can use
one sentence. An instruction to use subagents is stronger than optional
permission: realize useful delegation on suitable work, rather than treating
the possibility of a worker as sufficient compliance. A genuinely trivial task
need not acquire a manufactured assignment. Do not silently replace required
delegation with local completion or ask again for authorization already given.

Decide separately whether the worker should run concurrently. A sequential
context-isolated investigation or independent check can be worth delegating
even while the primary waits. For concurrency, identify ready independent work
the primary retains. Do not assign both primary and worker the same search or
implementation by default. Intentional independent verification has a distinct
question and evidence boundary, not a duplicate unrestricted task.

Different files alone do not prove independence. For writers or shared resources,
use [writing and integration](writing-and-integration.md); it owns isolation and
integration guarantees. Dependent writers wait for a stable shared contract.
Read-only discovery can often proceed while that contract is unresolved.

Before dispatch, inspect the observation behind a material readiness trigger and
confirm it still applies to the packet's source and contract. Use planning's
[dependency and early-boundary criteria](../../implementation-planning/references/implementation-units.md)
for the prerequisite; this procedure owns launch timing. If only a plan, stub or
unrelated green check supports it, defer that dependent writer and route a bounded
investigation where useful. This does not reopen sufficiently verified interfaces
or stop independent packets.

## Prepare once, route through the existing owner

Use the existing [assignment packet](packet-contracts.md). Add the delegation
purpose, expected use, reason for this timing and any readiness trigger only
where they clarify the boundary. The primary's retained work may be a short
note; do not forward the complete task graph or conversation unnecessarily.

Finalize the execution prompt and ownership before `prepare_routing`, batching
ready packets in the existing plan. Then follow the skill's selected routing
mode. Do not add these notes as invented API parameters, mutate an authorized
launch input, choose a new model here, or bypass an unavailable host adapter.
Later newly ready work can need another routing decision; reuse valid evidence
rather than ranking the same routes again for every launch.

## Revisit at meaningful boundaries

Reconsider after initial reconnaissance, when a named prerequisite becomes
ready, when a shared interface stabilizes, when scope or evidence changes, after
an unexpected failure, and before verification of a material risk. Reuse prior
valid decisions. Do not poll a task or replay the whole planning procedure after
each tool call. Deferred work must have a trigger, not "maybe later".

Keep shared decisions stable while dependents run. A worker finding an interface
conflict returns it to the primary rather than widening its authority. Only the
primary can launch a reviewer, replacement or repair worker. Continue the same
worker only within the existing [review and continuity](review-and-continuity.md)
contract; new scope is not a disguised resume.

When a return arrives, inspect the decisive evidence, use the result in its
named consumer and reconcile the owning plan. A well-presented report or a launch
receipt is not a completed outcome. For partial, failed or invalidated work use
[outcomes and repair](outcome-and-repair-contracts.md), not automatic restart,
model escalation or a duplicate full assignment. Check only what needs checking
without repeating the worker's entire job.

Before finishing, reconcile requested outcomes, useful returns, deferred work,
unfulfilled delegation and live resources. Explain a concrete limitation;
absence of a trace is unknown execution, not proof that a model refused the skill.
