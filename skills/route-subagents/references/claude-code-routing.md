# Claude Code mechanics

Use native Agent/subagent mechanisms and the active client's supported fields.
Select the child model and effort from the task and quota criteria in the
entrypoint; request them through the supported per-child controls. Inheritance
is suitable only when its effective settings match that selection. If an effort
control is unavailable, report the limitation instead of claiming it was set.
Do not persist dated aliases or model rankings or change global configuration
to route one child.

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

Primary references: [subagents](https://code.claude.com/docs/en/sub-agents),
[model configuration](https://code.claude.com/docs/en/model-config) and
[worktrees](https://code.claude.com/docs/en/worktrees).
Recheck live documentation or installed help before prescribing a setting.
