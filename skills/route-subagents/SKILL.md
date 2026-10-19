---
name: route-subagents
description: Prepare and route bounded Codex or Claude subagent packets after the user or an explicitly invoked workflow has already authorized delegation. Select client-native routes, ownership, isolation, return contracts, and oracles; parallelism alone is never permission to spawn.
license: MIT
metadata:
  assay-optional-skills: "code-change implementation-planning independent-audit skill-evaluation"
---

# Route subagents

Keep the primary session's model and effort unchanged. Select each child's
model and reasoning effort for its task and quota budget. A semantic profile
defines a capability boundary; it does not choose the child model or effort.

## Confirm authorization

This skill does not grant permission to delegate. Continue only when the user
explicitly requested subagents, delegation, or parallel agent work, or explicitly
invoked a workflow whose contract delegates work. A project instruction may
narrow that authority but must not infer or broaden it.

Independent packets, multiple repositories, possible speedup, specialized
tools, and context isolation are decision inputs, not authorization. When the
request does not authorize delegation, keep the work in the primary task and do
not spawn.

Only the primary/root agent may spawn subagents. Every worker packet must say
that the worker must not spawn additional agents. The primary spawns any
reviewer, replacement, or repair worker directly; delegation is one level deep.
The primary holds the user's authorization, the route choice and acceptance; a
child launched by a worker would skip all three and inherit its launcher's
settings, and every extra layer adds cost and unchecked errors. A worker that
needs another agent names that step in its report. Some clients allow nesting
by default; the client references say how to stop it.

## Select a useful packet

Decide what to delegate and when before selecting its model. For an explicit
request to use subagents, or unclear work boundaries, read
[delegation planning](references/delegation-planning.md) before substantial solo
work. Do not leave useful delegation until the primary has already solved it.

Within already-authorized delegation:

1. Identify a checkable outcome and how the primary will use it, not a persona,
   file count or an arbitrary fraction of the task. The primary retains
   acceptance, shared decisions and integration.
2. Compare the benefit of independent progress, specialist evidence, context
   isolation or independent verification with briefing, coordination and repair.
   A sequential worker can be useful; parallelism is a separate decision.
3. Choose `local`, `delegate_now`, `delegate_after` with a concrete readiness
   trigger, or `blocked` with the missing capability. Use the existing plan when
   a record is needed; these are decision labels, not a new runtime schema.
4. Before dispatch, verify each material readiness trigger against its current
   source and consumer, using [delegation planning](references/delegation-planning.md).
   Prepare ready packets before doing their work locally. State what the primary
   retains while they run. Respect actual dependency, shared-state and budget
   limits; do not invent a fixed worker count or repeat the worker's assignment.
5. Reconsider at newly ready dependencies, changed scope or evidence, an
   unexpected failure, and material verification. Do not replan after every tool
   call. Integrate and check results rather than counting launches as delivery.

An explicit request to use subagents calls for useful delegation when feasible,
not merely permission to consider it. Explain a genuine no-benefit or capability
limit instead of a ceremonial launch. If delegation is required, a later local
fallback in this skill does not override that requirement.

Read the actual owner instructions and target state before assigning work.
Define the outcome, source identity, smallest sufficient read scope, write
ownership, dependencies, exclusions and evidence required for completion.
Name the Assay skills the packet's work needs; the worker loads them before the
work and starts its report with the `Assay:` line, see
[packet examples](references/packet-contracts.md).
Include failure and escalation conditions when relevant. A verified no-op may
be useful; distinguish it from an unperformed required change.

Keep shared decisions stable while dependents run. A local reversible choice
belongs to its worker; a change to another packet's interface, ownership,
source assumptions or external effects returns to the primary for replanning.
Workers must not spawn additional agents. The primary coordinates any repair
or reviewer directly within the existing authorization.

## Choose model and effort for the task

Preserve a model or effort the user explicitly chose for a child; with a route
table, the [route table reference](references/route-table.md#using-the-table)
says how to launch it. The primary's
settings are not an implicit choice for its children, and a profile remains a
capability boundary, not a model selection. `routing_status` reports the
configured route table and `pipeline.mode`.

### Route table (default)

When the owner configured a [route table](references/route-table.md), each child
launches with the model and effort of its task class. First decide whether
delegating beats doing the work locally: one dependent chain that fits the
primary's context is usually cheaper done there. Then:

1. Read the classes from `routing_status`, or from a refusal that lists them.
2. Choose the class whose description fits the packet's work, not the class
   whose pair you already chose. A stronger class chosen "to be safe" is the
   inheritance the table exists to remove; when two classes fit, take the less
   demanding one. When no class fits, keep the work local or ask the owner for
   a class.
3. Pass that class's model and effort in the spawn call itself and declare the
   class in the call's label field, as the client reference describes. Never
   rely on inherited or default settings.

The Assay hook refuses a launch that does not follow its declared class, or
whose pair inheritance or an environment override would replace. Correct the
class or the pair; do not route around a refusal through another tool, provider
or local fallback presented as delegation.

Without a table, name both a model and an effort in every launch, chosen for the
task and the quota budget, and state the reason in one line; the Claude hook
refuses a launch that does not name both. Suggest that the owner configure a table.
Do not average unrelated benchmark scores, borrow another test's costs or treat
API prices as subscription quota.

If routing is rejected, unavailable or fails, read
[routing failure](references/routing-failure.md) before any launch. A failure
does not justify inheriting the primary's model or maximum effort. Respect the
denied operation.

The [benchmark evidence service](references/benchmark-routing.md) keeps
`get_routing_context` and source refresh for building and reviewing the table.

### Record the outcome

Record the class and its pair with the launch, and the task-based reason for the
class. A requested setting is not an observed runtime receipt: the hooks record
what the host ran an alias and an effort as, and that observation, not the
request, says what ran. If the client cannot express the pair, use a supported
route or keep the work local and disclose the limitation. Setup failure is not
automatic model escalation. Include coordination, verification and retries in
completed-task cost. Keep the primary's model and global client configuration
unchanged.

When a child's result needed rework at a stronger pair, say so in the outcome;
repeated rework in one class is the owner's signal to review that class. Before
dispatching an evidence-reviewer, give its packet the review inputs that
[review and continuity](references/review-and-continuity.md) requires; a
suitable pair does not make the assignment ready.

## Use the native client

Read only the matching mechanics when needed:

- [Codex](references/codex-routing.md): route-table launches, context
  inheritance, role selection and waits.
- [Claude Code](references/claude-code-routing.md): route-table launches, native
  agents, isolation and observed alias resolutions.

Use only roles, model names, effort levels and isolation modes exposed by the
active client. A profile defines permissions and purpose; its name does not
prove which model, context or sandbox actually ran. A routed launch names both
its model and its effort; with a route table the Assay hook checks Claude and
Codex launches against their declared class.

## Match detail to the boundary

| Boundary | Read when needed |
| --- | --- |
| Delegated writes, shared state or integration across roots | [Writing and integration](references/writing-and-integration.md) |
| Acceptance/decision review or finding repair | [Review and continuity](references/review-and-continuity.md) |
| Complex packet, multiple dependencies or a durable handoff | [Packet examples](references/packet-contracts.md) |
| Completion, no-op, failure or repair classification | [Outcomes](references/outcome-and-repair-contracts.md) |
| An unfamiliar split of the work | The relevant pattern in [delegation patterns](references/delegation-patterns.md) |
| A model or client upgrade changes a routing assumption, or vendor advice conflicts across routes | [Model guidance](references/model-guidance.md) |
| A model missing from routing evidence, publisher names unlike native IDs, or a source adapter to maintain | [Benchmark refresh](references/benchmark-refresh.md) |

A simple advisory question needs its question, evidence boundary, authority and
useful return; no repository-wide inventory, interface-version ceremony or
full delivery review is implied. References add only the relevant guarantees.

## Verify and finish

Inspect the returned artifact and decisive evidence. A fluent response, process
exit or task launch does not establish delivery. Recheck affected acceptance
conditions in the integrated result. Reuse valid receipts; run stateful full
gates in the owning primary task, once per stable candidate unless changes
invalidate coverage. A reviewer follows its declared stricter tool boundary.

Use event-driven waits and stable task identities. Send a focused repair delta
for new evidence; do not repeatedly poll unchanged state, restart a silent
worker or repeat an identical prompt to obtain a preferred verdict. Keep logs
addressable outside the main context and return material deltas with pointers.

Before the final handoff, reconcile the requested result, owned changes,
unresolved evidence and live workers/resources. Release only task-owned
resources whose identity is known, after preserving needed work and evidence.
For a restart, record a compact checkpoint in the existing owner task/memory
system; a normal run needs no extra ledger or orchestration runtime.

The retired `orchestrated-delivery` entry point's integration and review
guarantees live in these conditional references. Its old name is historical;
loading this skill or quoting the old workflow does not authorize delegation.
Evaluation inputs under `evals/` are for method maintenance, not live task input.
