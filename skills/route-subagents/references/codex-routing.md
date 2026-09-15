# Codex mechanics

Use the active collaboration tool schema as the execution contract. Select the
child model and effort using the task and quota criteria in the entrypoint,
then pass both explicitly where supported. Omitting fields can inherit the
parent's route; omit them only when the effective settings match the deliberate
selection. Do not import a benchmark ranking or fixed escalation ladder.

For a semantic role, choose the requested capability boundary independently of
model choice. Use only combinations exposed by the current tool and distinguish
configured settings from an observed role/model/permission binding.

Choose the smallest sufficient context. A self-contained review packet normally
uses no conversation inheritance. Use a bounded recent-turn count for a needed
delta. In this client's current collaboration schema, omitted `fork_turns` or
`fork_turns="all"` inherits model and effort and does not accept overrides. For
an explicit selection, use `fork_turns="none"` with a self-contained packet or
a supported positive recent-turn count; pass `model` and `reasoning_effort`.
Use full inheritance only when full continuity is material and the inherited
settings also fit the task and budget. Do not discard a cheaper sufficient
selection just to copy history. Recheck the callable schema if that changes.

A spawned worker shares the filesystem unless an isolated checkout has been
prepared. Set its actual root and owned scope; a prompt saying "isolated" does
not create a worktree or isolate services.

Wait through the native event-driven mechanism. A timeout is not evidence of a
stall. Use status listing for recovery or terminal reconciliation, and follow
up for a new decision or repair delta. Resume only the stable identity returned
by the tool. Creating a separate user-facing task is distinct from spawning a
subagent; preserve the user's requested surface.

Primary reference: [Codex subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents).
Consult current documentation and the active schema when a capability is
unclear; this reference records mechanics, not persistent model recommendations.
