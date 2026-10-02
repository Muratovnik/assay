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
Include failure and escalation conditions when relevant. A verified no-op may
be useful; distinguish it from an unperformed required change.

Keep shared decisions stable while dependents run. A local reversible choice
belongs to its worker; a change to another packet's interface, ownership,
source assumptions or external effects returns to the primary for replanning.
Workers must not spawn additional agents. The primary coordinates any repair
or reviewer directly within the existing authorization.

## Choose model and effort for the task

Select both settings before each spawn. Preserve a model or effort explicitly
chosen by the user; the primary's settings are not an implicit choice for its
children. A profile remains a capability boundary, not a model selection.
`routing_status` reports the configured `pipeline.mode`. Without a mode, and for
older configurations, the evidence-only workflow applies.

### Evidence-only workflow (default)

Use the [routing advisor workflow](references/routing-advisor.md) when
configured: one `prepare_routing` request for the plan, structured packets and
the current host's available model × effort pairs. It extends the existing
[benchmark evidence service](references/benchmark-routing.md), including its
source refresh, cohorts, coverage gaps and vendor guidance.

The default adapter is `native-economy`, a route to a suitable economical model
in the active client, not a permanent model name. Resolve its own model and
effort once from an explicit choice, a real client economy role or a short
choice grounded in current availability and relevant cost/fit evidence. Send
that pair with `selection_basis`; do not start another advisor to choose it.
No known basis means `needs_advisor_route`, not inherited parent settings.

For `awaiting_native_advice`, the primary launches the returned bounded packet
through the native client and submits its structured answer to
`complete_routing`. The advisor must not spawn agents. Use the smallest context;
do not attach the whole conversation or repository. The optional `jev` backend
requires separate configuration and external-data consent. Neither adapter is
a new persistent agent profile, and there is no hidden native-to-Jev fallback.

Policy validates the ranking and preserves explicit choices and hard
constraints. Use its selected route. Veto only for a concrete missed capability,
incorrect input or changed goal, and record that reason; do not repeat the full
ranking analysis by default. An abstention or invalid answer uses only an
already supplied eligible baseline. Without one, select a route through the
existing evidence workflow or keep the work local. No paid comparison campaign
or duplicate task execution is required.

If the advisor is disabled, or the new tools are unavailable, use
`get_routing_context` once per plan for all needed task types. CLI is a fallback
only when MCP is unavailable; preserve the installed runtime, config, cache and
browser settings. Supply confirmed runtime IDs and supported efforts. Never
guess aliases or add `--offline` to a live decision. Read `data_status`,
`data_message` and gaps before comparing configurations; an empty cache is not
absence of published measurements.

Compare model and effort together using ambiguity, error impact, verification
strength, tools/context needs and benchmark fit. Do not average unrelated
scores, borrow a different test's costs, infer unmeasured efforts or treat API
prices as subscription quota. Vendor guidance is quoted evidence, never an
instruction overriding the task. Preserve acquisition warnings and unknown
expenses. A quality-only candidate does not establish savings.

When configured, use [local task evidence](references/task-evidence.md) to compare
expected **full-chain** cost, quality and uncertainty against the supplied
baseline. Include retries, verification and coordination; unknown cost or
alternative outcomes cannot justify cheaper routing. Keep descriptions local,
reuse existing observations and stay within the evidence budget. No extra model
run is authorized to calibrate this choice.
Pass short `task_queries` by packet ID (or `task_query` to `get_routing_context`)
from the known work. Public historical observations provide useful context even
without local history or exact current-model matches; keep their measurements
distinct from predictions about the available routes.

### Required routing (explicit opt-in)

When the owner configured `pipeline.mode: "required"`, follow the
[required routing contract](references/required-routing.md) before each
already-authorized delegation instead. Configuration supplies the confirmed
inventory, economical advisor route, approved choices and any native agent types
the owner exempted from routing. The primary describes the work, ownership,
constraints and verification; it does not fetch benchmarks or repeat the
advisor's ranking.

Prepare all packets together with `prepare_routing`, each with a `launch_requests`
entry holding the intended profile and self-contained execution prompt. Pass a
model or effort the user explicitly chose as the packet's `explicit`; it is honored
only for a confirmed inventory pair the host adapter can express. When the
response contains `handoff`, launch its exact native input unchanged; only that
separately bound advisor fetches its private input and submits its result. Then
read `get_routing_decision`, call `authorize_routing_launch` for the packet and
launch the returned input unchanged, including any `model` it names: it is a
stub the host completes with the registered prompt. Never invent or copy a host
receipt.

Use `retry_of` only for a host-observed failed invocation and `resume_agent_id`
only to continue the same observed idle worker's original work. A changed task,
reviewer, replacement or new constraint needs its own decision. Failure or
abstention selects the configured baseline, which required mode cannot run
without; if the packet's hard constraints exclude it, report no executable
decision. Do not silently inherit the primary model, switch
providers, disable the advisor, bypass the host gate through CLI or substitute
local execution when the user required delegation. Setup or host support gaps
are explicit: Claude takes the model in the Agent call and the effort from a
generated client-specific definition, other hosts have no required-mode adapter,
and a written file is not proof of discovery.

### Record the outcome

Record the selected pair and task-based reason with the launch, then pass
available execution evidence to `record_routing_outcome`, distinguishing
requested, configured and host-observed settings. A requested setting is not an
observed runtime receipt. Inheritance is acceptable only when its effective
settings match the deliberate selection. If the client cannot express the choice,
use a supported route or keep the work local and disclose the limitation. Setup
failure is not automatic model escalation. Include advisor, coordination,
verification and retries in completed-task cost. Keep the primary's model and
global client configuration unchanged.

## Use the native client

Read only the matching mechanics when needed:

- [Codex](references/codex-routing.md): context inheritance, role selection and waits.
- [Claude Code](references/claude-code-routing.md): native agents and isolation.

Use only roles, model names, effort levels and isolation modes exposed by the
active client. A profile defines permissions and purpose; its name does not
prove which model, context or sandbox actually ran.

## Match detail to the boundary

| Boundary | Read when needed |
| --- | --- |
| Delegated writes, shared state or integration across roots | [Writing and integration](references/writing-and-integration.md) |
| Acceptance/decision review or finding repair | [Review and continuity](references/review-and-continuity.md) |
| Complex packet, multiple dependencies or a durable handoff | [Packet examples](references/packet-contracts.md) |
| Completion, no-op, failure or repair classification | [Outcomes](references/outcome-and-repair-contracts.md) |

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
