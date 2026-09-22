# Claude Code mechanics

Use native Agent/subagent mechanisms and the active client's supported fields.
Select the child model and effort from the task and quota criteria in the
entrypoint; request them through the supported per-child controls. Inheritance
is suitable only when its effective settings match that selection. If an effort
control is unavailable, report the limitation instead of claiming it was set.
Do not persist dated aliases or model rankings or change global configuration
to route one child.

For a [native economy advisor](routing-advisor.md), use the active Claude model
inventory and a supported native Agent route for the returned handoff. Do not
launch another provider's CLI to obtain its economical model. Send only the
bounded snapshot, request the explicit supported effort and return the object
to `complete_routing`. If the client cannot express the route, report that
limitation and use the eligible caller baseline or keep the task local. A prompt
forbidding tools or delegation is not proof of an enforced permission boundary.

Choose a built-in or semantic role by purpose and effective permissions.
Explore can fit codebase lookup, but its role name does not identify its model;
current releases inherit it subject to provider-specific limits. Verify the
actual binding when it matters. Custom profiles should describe stable
capabilities and omit model/effort defaults unless the owner deliberately pins them.

Ordinary Agent calls do not imply filesystem isolation. Use native worktree
isolation where supported for parallel writers and verify the resulting root.
Separate runtime resources as well as source. A built-in batch workflow is
appropriate only when its decomposition and branch/publication behavior fit
the authorized task; availability alone is not permission to run it.

Check hook effects before calling a worktree isolated. Claude keeps
CLAUDE_PROJECT_DIR at the launching project while hook input cwd follows the
worktree. A hook may therefore still touch the main checkout or shared state;
inspect its actual paths and ownership without changing unrelated registrations.

Use native progress, waiting and resume mechanisms with returned identities.
Keep the packet self-contained where independence matters. Do not assume
Codex context-inheritance parameters, effort values or role names work here.
Parent permissions, tool restrictions, environment overrides and MCP exposure
can affect the actual worker; observe the relevant boundary instead of relying
on frontmatter alone.

## Model upgrades and completion

For a changed model or provider binding, inspect the applicable
[registered guidance](model-guidance.md), not a remembered family default.
The [Opus 5.5 prompting guide](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5-5)
recommends calibrating effort and describes unattended runs that can end a turn
with a progress update before the task is complete. These are API/harness
observations, not proof that a native Agent tool exposes the same controls.
Preserve explicit user settings and verify the effective child route.

Check completion against the packet's required result and oracle, not `end_turn`
or the presence of a text update. Continue through the existing native identity
only when required work remains, the next action is authorized, and no user
stop, approval boundary, refusal, budget limit or real blocker intervenes. Keep
continuations bounded by the task budget and require new material progress;
do not replay writes or start replacements just because a turn ended. Reconcile
current artifacts before resuming. An absent visible thinking/progress block is
not itself a stall; use native lifecycle evidence.

The [subagent permission documentation](https://code.claude.com/docs/en/sub-agents#permission-modes)
also describes parent modes that override child `permissionMode`; plugin-supplied
agents do not inherit every metadata capability of project agents. Check the
actual restrictions before claiming a read-only reviewer. Do not alter parent
permissions to make an unsupported child setting appear effective. A bounded
formal reviewer is not required for every informal review; choose the role by
its input and evidence contract, not its name.

Primary references: [subagents](https://code.claude.com/docs/en/sub-agents),
[model configuration](https://code.claude.com/docs/en/model-config) and
[worktrees](https://code.claude.com/docs/en/worktrees).
Recheck live documentation or installed help before prescribing a setting.
