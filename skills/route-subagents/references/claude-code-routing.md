# Claude Code mechanics

Use native Agent/subagent mechanisms and the active client's supported fields.
Select the child model and effort from the task and quota criteria in the
entrypoint; request them through the supported per-child controls. Inheritance
is suitable only when its effective settings match that selection. The Agent
call's `model` accepts only the aliases `sonnet`, `opus`, `haiku` and `fable`
and takes precedence over a definition's model; a full ID fails the call's
validation. Claude Code 2.1.292+ takes a per-invocation `effort` for non-fork
agents; the active tool schema shows the field, and the environment override
still wins. Without the field, report the limitation instead of claiming the
effort was set. Do not persist dated aliases or model rankings or
change global configuration to route one child.

After rejection or service failure, apply [routing failure](routing-failure.md)
before a native launch. An explicit model with omitted effort can still inherit
the session's maximum effort. `CLAUDE_CODE_SUBAGENT_EFFORT` (Claude Code 2.1.316+)
replaces that inheritance with one default level, which is no per-child choice;
express both settings through the actual supported
controls or establish deliberate matching inheritance. An unavailable router
does not make either setting a valid default.

Choose a built-in or semantic role by purpose and effective permissions.
Explore can fit codebase lookup, but its role name does not identify its model:
without a model or effort control it can inherit the parent's settings. Name a
model in the call when the parent's is not the deliberate choice; its effort
follows the session unless an exposed call field or selected definition sets it.
Verify the actual binding when it matters. Custom
profiles should describe stable capabilities and omit model/effort defaults
unless the owner deliberately pins them.

Requested settings and model/effort fields in frontmatter are not observations:
the hook reads the `effort.level` object of a stop and the structured Agent
`resolvedModel` when the host provides them, see
[observed alias resolutions](#observed-alias-resolutions). Unknown remains
unknown. Parent permissions and actual tool access still govern.

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

## Contents

- [Route-table launches](#route-table-launches)
- [Evidence-only launch check](#evidence-only-launch-check)
- [Launches from a subagent](#launches-from-a-subagent)
- [Files a subagent writes](#files-a-subagent-writes)
- [Waiting inside a background worker](#waiting-inside-a-background-worker)
- [Observed alias resolutions](#observed-alias-resolutions)
- [Model upgrades and completion](#model-upgrades-and-completion)
- [Transcripts route-report reads](#transcripts-route-report-reads)

## Route-table launches

With a [route table](route-table.md) configured, start the Agent call's
`description` with the class name, then a colon or a space, the child's
[name](../SKILL.md#name-each-child) and the usual short summary
(`code: parser errors — show the failing line`), and pass that class's `model`
alias and `effort` in the same call. The hook reads only the class, so it does
not check the name. Without a table the description starts with the name
(`parser errors — show the failing line`). The call's model outranks a
definition's model and its effort outranks a definition's `effort`, so a
profile's frontmatter does not change the pair. `CLAUDE_CODE_EFFORT_LEVEL` outranks the call's effort: the hook
refuses a routed launch while that variable names another level.
`CLAUDE_CODE_SUBAGENT_MODEL` applies only to a call without a model and
`CLAUDE_CODE_SUBAGENT_EFFORT` only to a launch that names no effort, which a
routed launch never is. A fork, a `resume`, the built-in `web-fetch` agent and a type in
`pipeline.unrouted_agents` keep their settings and are not checked; a project
or user definition that pins both settings is no exemption here, because the
call's pair replaces them.

## Evidence-only launch check

Without a route table, this weaker check applies. The Agent tool takes a
per-call `effort` only when an instruction asks for a level, and a child
launched without a model or an effort runs with the session's or an environment
default. When the Assay hook finds an evidence-only Claude routing
configuration, through `ASSAY_ROUTING_CONFIG` or the plugin's routing binding
(`routing.json` in its data directory), that configuration is such an
instruction: the hook refuses an Agent launch that does not name both `model`
and `effort`, and its reason names what is missing. These launches pass:

- a fork, which shares the parent's context and settings by design;
- a `resume` of an existing worker, which keeps its settings;
- the built-in `web-fetch` agent, which Claude Code offers in place of the
  WebFetch tool and tells the model to call like one; with or without a table
  it gets no routing note or launch reminder either;
- a type listed in `pipeline.unrouted_agents`;
- a type whose nearest project or user definition (`.claude/agents/<type>.md`)
  pins both in its frontmatter, `inherit` excepted. A plugin agent's definition
  is not read; its call names both.

`pipeline.explicit_routes: "off"` disables the check. Without a configuration or
binding, ordinary delegation is unchanged; a configuration that cannot be read
or validated, including one written for an older schema, refuses the launch. The
check establishes that a launch named both settings, not which model ran.

## Launches from a subagent

Since Claude Code 2.1.219 a subagent can launch subagents of its own, up to
three layers below the main conversation. Such a child skips the primary's route
choice, so with an evidence-only Claude configuration the hook refuses any Agent
call whose input carries an `agent_id`, a fork's and a `resume` included, before
the checks above, even with `pipeline.explicit_routes: "off"`. The refusal tells
the worker to do the step itself or name it in its report. To stop nesting at the
client as well, set `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH` to `1`: a subagent
then gets no Agent tool, and a fork's call fails. See the
[nesting documentation](https://code.claude.com/docs/en/sub-agents#let-subagents-spawn-their-own-subagents).

## Files a subagent writes

Claude Code 2.1.318 refuses a subagent's Write when the file name matches
`/^(REPORT|SUMMARY|FINDINGS|ANALYSIS).*\.md$/i`, with the text "Subagents should
return findings as text, not write report files". The check is in the client, not
a hook. So a [packet](packet-contracts.md) asks for findings as text, and a file
it needs beside the report takes a name that starts with none of those words.

## Waiting inside a background worker

A background subagent waits for a long run in a foreground loop that ends
before the client takes the call away. The packet line:

> A subagent waits for a long run in the foreground: `timeout 170 bash -c
> 'until <the run has ended>; do sleep 5; done'`, sent with the tool's `timeout`
> set to 200000, and again until the run ends. The client moves a background
> subagent's call to the background at 180 s, and any call at the tool's own
> timeout, 120 s unless set. After 30 minutes of waiting in total, or when the
> run is queued behind a machine-wide lock, end your turn once and name the
> run's output file.

The form is named because a bare foreground `sleep` is blocked by the Bash
tool, and the tool's `timeout` because without it the call moves to the
background at 120 seconds. In a probe on Claude Code 2.1.328 three such loops in
a row returned inside the worker's turn, the parent got no notification in nine
minutes, and each next request read the worker's context from cache. The move
at 180 seconds was observed for a background subagent, not in `claude -p`.

A worker that instead ends its turn while its own command or Monitor runs sends
the parent a task-notification with status `completed`, the summary "is waiting
on its own background work" and a note that the same task-id will notify again.
The parent answers each notification with a full model turn. A live probe on
2.1.317 still gave one parent turn per stop; see
[#105928](https://github.com/anthropics/claude-code/issues/105928) and
[#103359](https://github.com/anthropics/claude-code/issues/103359). Each Monitor
event and each Monitor expiry resumes the worker the same way, so a Monitor
re-armed every few minutes wakes the parent at every expiry: in one measured
window 10 workers re-armed 859 times. A hand-back sent before the work is done
costs a parent turn as well.

For the wait the [packet](packet-contracts.md) asks for:

- Start the run with `run_in_background` and give it its own deadline, such as
  the runner's timeout, so that a hang ends it too. The loop's condition reads
  the run's output file or the marker the run leaves at its end.
- Do not stream progress lines into the wait.
- Keep a Monitor for a worker that acts on each event, such as stopping a run
  at its first failure. Its filter prints only the lines the worker acts on.

The limits come from the prompt cache. On 2.1.309 a background subagent's
requests used the 5-minute prompt cache, and the main conversation's used the
1-hour one. A pause past 5 minutes makes the worker's next request write its
whole context again, at 1.25 times the input price; a cache read costs 0.05
times the input price on Opus 5.5 and Sonnet 5.5, and 0.1 times on most other
models; see
[pricing](https://platform.claude.com/docs/en/build-with-claude/prompt-caching#pricing).
Each loop is one request that reads the worker's context from cache, so at a
read multiplier of 0.1 about 12 loops, some 35 minutes, cost what one rewrite
does. Past that the worker ends its turn once: the run's end is then one
notification and one rewrite. The 30 minutes are this calculation, not a
measurement.

## Observed alias resolutions

The call accepts only aliases, while routing evidence names full model IDs.
With the plugin's routing binding (`routing.json`, see
[bind the configuration](route-table.md#bind-the-configuration-to-the-hooks)),
every Claude Agent launch the hook does not refuse records the requested alias and
effort, the `resolvedModel` its return reports and the `effort.level` its stop
reports, under the binding's `cache_dir`. `routing_status` and `get_routing_context`
return the latest as `host_observations`: `aliases` maps an alias to the ID it ran as, and `efforts`
pairs a requested level with the applied one, which is lower when the model
lacks the requested level. Pass the alias whose observed resolution is the
selected ID. Without an observation the client's own model listing is the
source, and the first launch records the result. Observations expire after 30
days and are not a registry: a new resolution replaces the old one.

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

Assay's Claude `evidence-reviewer` projection is a bounded reader for that
reason: it has only `Read`, `Grep` and `Glob`, names the oracle and skill
discovery unavailable, and returns `refused` without snapshot-bound receipts for
the named oracle. Give it those receipts, and pass audit criteria such as the
installed `independent-audit` `SKILL.md` and `references/bounded-review.md` by
path, since it cannot load the skill. The Codex reading projection also treats
shell oracles and skill loading as unavailable and reads supplied receipts.
The plugin-wide profile hook denies mutating tools for a confirmed reading
role. It keeps the tools that role's projection lists and `SubagentHandback`,
the channel that returns its report; it does not change the primary's or a
writing worker's permission mode.
Confirm native discovery and hook execution separately from generated bytes.

Primary references: [subagents](https://code.claude.com/docs/en/sub-agents),
[model configuration](https://code.claude.com/docs/en/model-config) and
[worktrees](https://code.claude.com/docs/en/worktrees).
Recheck live documentation or installed help before prescribing a setting.

## Transcripts route-report reads

[`route-report`](route-table.md#building-and-reviewing-the-table) reads files
Claude Code writes for its own use. Their layout below was observed on Claude
Code 2.1.31x; it is not a documented interface and can change in any release,
so the command reads each field defensively and counts the lines it skips.

- A subagent run is `<projects-dir>/<project>/<session>/subagents/agent-*.jsonl`
  with a sibling `agent-*.meta.json` that holds the launch's `description`,
  its `model` alias, `effort` and `agentType`. The class and the child's name
  come from `description`, read exactly as the launch check reads it.
- Each line carries the `sessionId` of the session that wrote it. A forked
  session's folder holds copies of the parent's subagent files, without a meta
  file, whose lines keep the parent's id; those lines are skipped, since the
  parent already counts them, and a file with no line of its own is no launch.
  A child resumed in the fork appends its own lines, which are read.
- Usage is `message.usage` on assistant lines. One message is written on
  several lines, so usage is counted once per `message.id`, from its last line:
  an earlier line can hold a smaller output count. When
  `usage.iterations` is present it splits the request; an iteration of type
  `advisor_message` is an advisor call, counted apart from the child's tokens.
- Cache writes come from `cache_creation.ephemeral_5m_input_tokens` and
  `ephemeral_1h_input_tokens`; without that split, `cache_creation_input_tokens`
  counts as 5-minute writes.
- Tool calls are distinct `tool_use` ids; start and end are the first and last
  `timestamp` of the file's own lines.
- A child's report is the `message` of a `SubagentHandback` call. A child that
  is resumed keeps writing to the same file and hands back once per round, so
  one file can hold several reports; a child that made no such call has one
  report, its last assistant text. A call whose `tool_result` carries
  `is_error` did not reach the caller, as when a hook holds a hand-back for a
  recheck, and counts only when the child sent no other. Minutes run from the file's first timestamp
  to its last and so include the wait between rounds.
- A child's requests are its launch prompt and the coordinator's messages: the
  `user` lines that are not tool results, `isCompactSummary` or `isMeta`, except
  that an `isMeta` line whose `origin.kind` is `coordinator` counts. The `cwd`
  and `gitBranch` on each line are
  the session's, not the worktree the child worked in, so commits are what link
  a review to its subject.
