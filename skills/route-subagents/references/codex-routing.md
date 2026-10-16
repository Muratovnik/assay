# Codex mechanics

Use the active collaboration tool schema as the execution contract. Select the
child model and effort using the task and quota criteria in the entrypoint,
then pass both explicitly where supported. Omitting fields can inherit the
parent's route; omit them only when the effective settings match the deliberate
selection. Do not import a benchmark ranking or fixed escalation ladder.

After rejection or service failure, apply [routing failure](routing-failure.md)
before a native launch. A fresh packet with `fork_turns="none"` and explicit
supported model/effort fields avoids accidental parent inheritance. A full fork
needs a deliberate matching selection and known effective parent settings;
the failed routing call cannot establish them.

For a semantic role, choose the requested capability boundary independently of
model choice. Use only combinations exposed by the current tool and distinguish
configured settings from an observed role/model/permission binding.

The published reading profiles disable shell, connectors, goals and further
delegation and mark shell oracles and skill loading unavailable. Supply frozen
artifacts, audit criteria and snapshot-bound receipts; use available reading
tools rather than rerunning gates. A file sandbox alone does not prohibit MCP
task or memory writes. The profile hook denies tools outside its reading list
when the native role or exact worker identity is observed. Parent session alone
never identifies a reviewer. Hooks must be trusted; absent role identity or a
skipped hook leaves enforcement unverified. Confirm it in a fresh client.

Choose the smallest sufficient context. A self-contained review packet normally
uses no conversation inheritance. Use a bounded recent-turn count for a needed
delta. In this client's current collaboration schema, omitted `fork_turns` or
`fork_turns="all"` inherits model and effort and does not accept overrides. For
an explicit selection, use `fork_turns="none"` with a self-contained packet or
a supported positive recent-turn count; pass `model` and `reasoning_effort`.
Use full inheritance only when full continuity is material and the inherited
settings also fit the task and budget. Do not discard a cheaper sufficient
selection just to copy history. Recheck the callable schema if that changes.

For a native economy advisor (`docs/how-to/routing-advisor.md` in the Assay repository), the primary passes the
handoff's model and effort through `model` and `reasoning_effort`, with
`fork_turns="none"` and the self-contained prompt. The advisor ranks only the
provided snapshot and must not spawn. Forward its exact inline prompt, rather
than a file path the no-tools advisor cannot read. Submit the returned object to
`complete_routing` before launching the actual worker. A no-tools instruction
is not an enforced sandbox: use a real tool restriction only when the active
schema exposes it. No fixed model or per-child token cap is implied. Snapshot
expiry rejects a late answer; interrupting the running advisor still belongs
to the native client.

## Route-table launches

With a [route table](route-table.md) configured, start `task_name` with the class
name, then an underscore or the end of the name (`code_parser_fix`), and pass
that class's `model` and `reasoning_effort` with `fork_turns="none"` or a
bounded positive recent-turn count. Omitted or `"all"` fork turns inherit the
parent's settings and ignore the requested ones, so the hook refuses them. A
custom agent file that sets `model` or `model_reasoning_effort` outranks the
call; the hook reads the project's and the user's `.codex/agents/<agent_type>.toml`
and refuses a pinned value that differs from the class's pair. A type in
`pipeline.unrouted_agents` is not checked.

The Assay plugin registers `PreToolUse` for Codex, and current Codex
documentation lists `spawn_agent` among the local function tools that hook can
refuse. The check reads only `task_name`, `agent_type`, `model`,
`reasoning_effort` and `fork_turns`; it never needs the message, which Codex
session files store encrypted. An untrusted hook is skipped without an error,
so confirm the refusal once in a fresh session after installing or upgrading.

## Launches from a subagent

The hook cannot hold delegation to one level here: Codex documents no field in
`PreToolUse` input that names the calling agent, and a subagent's hooks report
the parent's session. The client limit is `agents.max_depth` in
`config.toml`; its documented default, `1`, lets the root spawn children and
stops children from spawning. Public reports say some Codex versions do not
enforce it, so set it explicitly and confirm in a fresh session that a child's
`spawn_agent` call fails before relying on it.

Required routing (`docs/how-to/required-routing.md`, section "One explicit mode") has no Codex adapter.
A Codex configuration that selects it reports the unsupported host and blocks
protected delegation; keep Codex on the evidence-only workflow. The
reminder alone enforces nothing; the launch check above is the hook's
evidence-only guard.

## Required-mode adapter requirements

These are the conditions a future Codex adapter must meet, from observations on
Codex 0.147.0; none of it is implemented. The spawn call already carries `model`
and `reasoning_effort`, so Codex needs no generated definitions for routing.

- **Advisor confinement comes from agent configuration.** There is no tool
  allowlist, only switches that remove capabilities. In the advisor's agent
  file, disabling the shell, apps and goals features, a read-only sandbox and
  `enabled_tools` limited to the two routing tools of the benchmark server took
  effect; `approval_mode = "approve"` on those two tools was needed, or a
  non-interactive run cancels the call.
- **A residual set stays available.** Per-agent `view_image` and code-mode
  switches had no effect, and image generation, plan updates and MCP resource
  reading have no switch; `apply_patch` remains but the read-only sandbox blocks
  its writes. Document that set, and repeat a native probe of the advisor's
  actual tools at adapter acceptance and after every Codex upgrade, because new
  tools arrive enabled.
- **A hook-based guard needs proof first.** Subagents call their tools from
  code mode's `exec` tool. Whether `PreToolUse` sees the calls inside it is not
  established by the historical probe. Current documentation describes hooks
  for nested calls, but the installed client still needs a fresh capture. A
  guard that sees only `exec` would block the routing tools too. An untrusted
  hook is skipped without an error.
- **Output sanitizing needs another route.** Codex `PostToolUse` cannot rewrite
  a tool's output, only block it with feedback, so the advisor's report cannot be
  reduced to a status the way the Claude adapter does it.
- **The inventory comes from the host.** The client's local model cache can be
  stale; the owner confirms what the host actually offers.

## Workers and waits

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

Primary references: [Codex subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents),
[Codex hooks](https://learn.chatgpt.com/docs/hooks) and the
[configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference).
Consult current documentation and the active schema when a capability is
unclear; this reference records mechanics, not persistent model recommendations.
