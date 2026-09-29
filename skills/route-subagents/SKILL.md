---
name: route-subagents
description: Prepare and route bounded Codex or Claude subagent packets after the user or an explicitly invoked workflow has already authorized delegation. Select client-native routes, ownership, isolation, return contracts, and oracles; parallelism alone is never permission to spawn.
license: MIT
metadata:
  assay-optional-skills: "independent-audit skill-evaluation"
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

Within already-authorized delegation, keep one checkable outcome per worker.
Use a worker when independent work, specialist evidence or context isolation
helps the task; keep short linear work local. The primary retains acceptance,
cross-packet decisions and integration. Choose by the decisions and evidence
the work needs, not a permanent classification of a model as strong or weak.

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

Use the [required routing contract](references/required-routing.md) before each
already-authorized delegation. The primary describes the work, ownership,
constraints and verification; it does not fetch benchmarks and repeat the
advisor's ranking. Configuration, not an argument authored by the primary,
supplies the confirmed inventory, economical advisor route and approved choices.
A profile remains a capability boundary, not a model selection.

Prepare all packets together with `prepare_routing`, including a `launch_requests`
entry containing the intended profile and self-contained execution prompt for
each packet. Raw execution prompts stay out of the advisor's evidence input.
The host hook supplies its own receipt; do not invent or copy that receipt.
An approved explicit choice, a single eligible pair or a valid cache hit avoids
unnecessary advisor inference but still requires a registered worker launch.

When the response contains `handoff`, launch its exact native input unchanged.
Only that separately bound advisor may fetch its private input and submit its
structured result with `complete_routing`. The primary never forwards benchmark
snapshots or submits an answer on the advisor's behalf. The advisor must not
spawn agents. Its own route is configured once; no recursive routing is allowed.

Read `get_routing_decision` after the native advisor completes, then call
`authorize_routing_launch` for the packet and launch the returned input unchanged.
The native guard checks session, scope, expiry, immutable definition and attempt
identity. Use `retry_of` only for a host-observed failed invocation;
`resume_agent_id` only continues the same observed idle worker's original work.
A changed task, reviewer, replacement or new constraint needs its own decision.

Use the selected pair. A concrete missed constraint or changed goal calls for a
corrected request, not a second root-side ranking. Failure or abstention permits
only a separately configured eligible baseline; otherwise report no executable
decision. Do not silently inherit the primary model, switch providers, disable
the advisor, use CLI as an unauthenticated bypass or substitute local execution
when the user required delegation. Preserve the primary model and settings.

Setup or host support gaps are explicit. Claude uses generated client-specific
model/effort definitions; a written file is not proof of discovery or effective
permissions. Other hosts must not claim Claude's enforcement guarantees.
`evidence-only` is a separately authorized configuration mode, never a failure
fallback. Its [comparative evidence workflow](references/benchmark-routing.md)
is diagnostic/manual and does not provide mandatory isolated routing.

The [advisor reference](references/routing-advisor.md) owns structured features,
policy, evidence bounds, cache and optional diagnostic backends. When configured,
[local task evidence](references/task-evidence.md) adds historical full-chain
cost and uncertainty without extra model trials. Keep unknown expenses unknown;
API prices are not subscription quota. Record outcomes through
`record_routing_outcome`, distinguishing requested, configured and host-observed
settings. Include advisor, coordination, verification and retries in completed-task
cost. No new paid comparison campaign is authorized by this skill.

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
