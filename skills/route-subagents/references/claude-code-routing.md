# Claude Code mechanics

Use the [required routing contract](required-routing.md) for actual setup and
calls. Claude's Agent schema has no per-invocation effort field in this adapter.
Generate an immutable definition for each requested profile/model/effort pair
using `tools/assay.py claude-routes`; route via the returned `subagent_type`, not
an invented Agent argument or changed root/global effort. Generation is explicit,
conflict-safe and separate from discovery. Canonical profiles remain neutral.

The separately bound native advisor fetches its private snapshot directly and
submits the structured answer itself. The primary uses only the compact handoff,
decision and exact authorized worker input. It does not copy benchmarks, forge
results, start another provider's CLI or select a fallback. Only a separately
configured eligible baseline can recover a failed advisor; otherwise no launch.

Requested settings and model/effort fields in frontmatter are not observations.
The hook observes the `effort.level` object and structured Agent `resolvedModel`
and `modelsUsed` when available. Conflicting environment overrides and observed
mismatches are rejected rather than silently treated as the requested route.
Unknown remains unknown. Parent permissions and actual tool access still govern.

Ordinary Agent calls do not imply filesystem isolation. Use native worktree
isolation where supported for parallel writers and verify the resulting root.
Separate runtime resources as well as source. A built-in batch workflow is
appropriate only when its decomposition and branch/publication behavior fit
the authorized task; availability alone is not permission to run it.

Check hook effects before calling a worktree isolated. Claude keeps
CLAUDE_PROJECT_DIR at the launching project while hook input cwd follows the
worktree. A hook may therefore still touch the main checkout or shared state;
inspect its actual paths and ownership without changing unrelated registrations.

Use native progress and waiting with returned identities. For an existing routed
worker, request `authorize_routing_launch` with its `resume_agent_id`; the host
checks the same idle worker, original packet and unchanged definition. A direct
unregistered resume or new task under an old identity is not permitted.
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
