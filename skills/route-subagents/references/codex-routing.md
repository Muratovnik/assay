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

For a [native economy advisor](routing-advisor.md), the primary passes the
handoff's model and effort through `model` and `reasoning_effort`, with
`fork_turns="none"` and the self-contained prompt. The advisor ranks only the
provided snapshot and must not spawn. Submit the returned object to
`complete_routing` before launching the actual worker. A no-tools instruction
is not an enforced sandbox: use a real tool restriction only when the active
schema exposes it. No fixed model or per-child token cap is implied. Snapshot
expiry rejects a late answer; interrupting the running advisor still belongs
to the native client.

A spawned worker shares the filesystem unless an isolated checkout has been
prepared. Set its actual root and owned scope; a prompt saying "isolated" does
not create a worktree or isolate services.

Wait through the native event-driven mechanism. A timeout is not evidence of a
stall. Use status listing for recovery or terminal reconciliation, and follow
up for a new decision or repair delta. Resume only the stable identity returned
by the tool. Creating a separate user-facing task is distinct from spawning a
subagent; preserve the user's requested surface.

## Model upgrades and API boundaries

Use [registered guidance](model-guidance.md) for its declared models, surfaces
and conditions. An Astra-specific prompt observation is not a rule for Sol or
Luna. Reconfirm runtime IDs and supported efforts after an upgrade; identical
effort labels are not evidence of equal compute, quality or subscription cost.
Do not turn a model's API effort range into a native tool capability declaration.

When the task actually involves a direct API adapter, the
[GPT-6 migration guide](https://developers.openai.com/api/docs/guides/latest-model#update-api-and-model-parameters)
recommends Responses for tools; its Sol/Luna Chat Completions function-calling
support is restricted to `reasoning_effort: none`. This API limitation does not
establish a failure or supported override in the active native Codex client.
Check the adapter and endpoint in use before prescribing a migration. Routing
one native child does not authorize editing an API adapter or global settings.

Primary reference: [Codex subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents).
Consult current documentation and the active schema when a capability is
unclear; this reference records mechanics, not persistent model recommendations.
