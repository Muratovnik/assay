# Configure and diagnose command hooks

Assay's plugin hooks are local commands, not prompt/agent hooks. They do not call
models, install dependencies, launch advisors, read transcripts or modify client
settings. Their text and any subsequent agent work still consume context/quota.
Skills-only installations do not install hooks.

User corrections and acceptable examples can be kept as local feedback cases by
an explicit `record` command. See [feedback capture](feedback-capture.md) for
storage modes, the optional correction-hook trigger, review and native
Claude/Codex/Cursor/Gemini adapters. This is separate from the technical reminder
state described below; automatic capture is off by default and nothing confirms
failures automatically.

## Install, enable and verify separately

The generated Claude manifest is `hooks/hooks.json`. Codex explicitly selects
`hooks/codex.json` through its plugin manifest. Both invoke one runtime command
per matching event. `PreToolUse` matches every tool, because the reading-role
boundary and the spawn checks need to see each call; result and failure events
match only the native spawn tools.
Generated definitions used by required routing retain their existing lifecycle.

Use Python 3.11+ as `python` in the client's environment. Recognizing an explicit
skill choice also needs `markdown-it-py` from `hooks/requirements.txt`, installed in
an isolated environment used by that command. Repository contributors already get
this from `requirements-tools.txt`. Assay never installs it automatically. A missing
parser makes explicit choices unrecognized, not permission to bypass a required
routing check; the skill check, the session/delegation reminders and the guard do
not need the Markdown parser.
Optional rule/configuration/state failures retain the basic reminders and never
replace a routing guard response.

After installing/updating the full plugin, inspect the client's hook UI and
execution diagnostics. Codex requires trust of the current definition; updates
can invalidate that trust. Disabled hooks and managed-only policies can prevent
execution. Installing files, passing a unit test or running doctor does not prove
that the client enabled, trusted or invoked the hook.

From the checkout or installed plugin root:

```text
python -I -B hooks/runtime/cli.py doctor --client claude
python -I -B hooks/runtime/cli.py doctor --client codex
```

`doctor --settings <explicit-settings.json>` reads an explicitly supplied client
settings file and lists other pre-tool handlers for review. It does not execute
their commands, inspect hidden managed settings, prove they rewrite inputs, or
edit the file. Review overlapping handlers and remove duplicate Assay registration
through the native plugin/settings interface. Native plugin ownership is the
installation mechanism; this change does not add a second settings installer.

Update/remove/rollback the plugin with its native lifecycle; linked installations
still follow [the existing external-snapshot procedure](upgrade-linked-install.md).
Keep foreign settings unchanged. Do not copy the hook into user settings in addition
to enabling the plugin. After rollback, review trust again. `claude-routes --remove`
and the existing ownership manifest govern generated definitions, not plugin removal.
Persistent plugin data has its own lifetime and is not an install-state database.

## Input language and model-facing language

All Assay-authored hook instructions, restored reminders and diagnostics are in
English, matching the skills. The hooks never match the user's wording to pick a
method, so a request in any language receives the same English context. Do not
localize hook output based on the input language or force user-facing replies
into English. The user's reply-language preference is unchanged.

Explicit selections accept forms such as `Use the skill code-change`,
`Apply the skills independent-audit and code-change` and inline-code native names
such as `assay:code-change`, `$code-change` or `/assay:code-change`. Unknown names
are not installed or guessed. These input aliases do not change canonical names.

## The skill check

Every `UserPromptSubmit` adds the same short **skill check**: the agent decides
from the task itself, not from the tools it has at the moment, which Assay skills
apply. It starts its reply with one line such as `Assay: code-change, test-writing`
or `Assay: none`, loads each chosen skill it has not loaded yet before any other
tool call, and starts its final reply with the same line after tool use. A skill
that needs a missing tool is still loaded, and the agent says what is missing. The
check lists every installed, enabled skill with a one-line cue from
`hooks/activation-rules.toml`. The model judges relevance from the task in
whatever language it is written; the hook reads nothing in the prompt to build
the check.

The check exists because a skill's description is the only automatic route to it,
and that route is unreliable on its own. Claude Code drops the descriptions of the
least-used skills when its listing exceeds the
[character budget](https://code.claude.com/docs/en/skills#skill-descriptions-are-cut-short),
and a model that sees a description can still decide to answer without the skill.
The one-line statement commits the agent to a judgment it can be held to. In a
[published comparison](https://scottspence.com/posts/measuring-claude-code-skill-activation-with-sandboxed-evals),
a hook that made the model evaluate each skill before acting activated skills far
more reliably than no hook or a plain reminder. That was one author's small,
English-only sample, so treat it as a reason to measure, not as a guarantee.

The check costs about 1.6 KB of English text (roughly 400 tokens) on every
prompt, in Claude Code and Codex alike, and it stays in the conversation until
compaction. It is not re-sent when a session resumes or compacts, so after a
compaction the current request's check may survive only in the summary.
Subagents do not receive it; their packets carry their own instructions. The
agent omits the `Assay:` line when a request fixes an exact output format. For
scripted runs whose output must stay clean, such as `claude -p` pipelines, turn
the check off with `disabled_rules: ["skill-check"]` (see below).

### The skill gate in Claude Code

Naming a skill is not loading it: in measured runs an agent sometimes wrote
`Assay: evidence-research` and went straight to the work. In Claude Code a
`PreToolUse` record notes each Assay skill the session loads, through the Skill
tool or a read of its `SKILL.md`. When the reply's leading `Assay:` line names a
skill this session has not loaded, the `Stop` hook continues the turn once with
feedback saying so: the skill is to be loaded and the work checked against it
before the final reply. The feedback is `additionalContext`, not a block, so Claude
Code shows it as hook feedback rather than a hook error and applies its usual limit
on stop-hook continuations. It uses the hook input's final reply text, never the
transcript, and stays silent while `stop_hook_active` is set. It needs the plugin
data directory, so it is inert without hook state.

The gate guarantees only that a named skill gets loaded. It cannot tell whether
the agent named the right skills; `Assay: none` and an answer without the line
pass. A subagent's load does not count for the main session. Codex has no gate:
its skill loads are not visible reliably enough to act on. Turn the gate off
with `disabled_rules: ["skill-gate"]`; disabling the check also disables it.

Phrase rules that matched English/Russian wording were retired: they missed
paraphrases and every other language and needed a rule per phrasing. Only an
explicit skill choice is still recognized deterministically. It adds a short
suggestion naming that skill in front of the check. Explanations, quoted commands
and negative requests do not count as a choice. The CommonMark parser excludes
blockquotes, fenced/indented code, lists and headings, and only the first request
paragraph can make a choice.

## Hints do not grant authority

Neither the check nor an explicit-choice suggestion authorizes edits, delegation,
installation or tool use beyond the request; both say so. A suggestion asks to
reuse sufficient existing research/plans and preserve the user's scope. It does
not claim to load a skill or assume that a particular MCP tool exists. Even an
observed Skill load or an `Assay:` line would not prove compliance with a method.

The session reminder is three sentences: use matching installed skills; when the
user requests subagents, use `route-subagents` before substantial solo work; no
delegation is authorized by it. The rest of the routing checklist is added at
session start only when `ASSAY_ROUTING_CONFIG` is set; otherwise it arrives in the
reminder before each launch.
A required-mode guard reply takes precedence over a suggestion. The runtime never
adds `allow` to advance a workflow and never exempts a launch after repeated
failures. Assay returns no blocking Stop decision; the Claude skill gate above
continues a turn at most once, through feedback. Assay does not ship a hook
that guards project paths; to require approval for edits to tests or check
configuration, see [project guards](project-guards.md).

## Optional state and privacy

Without a data directory, suggestions are stateless. The runtime uses the client's
`PLUGIN_DATA` / `CLAUDE_PLUGIN_DATA` when present. Alternatively set
`ASSAY_HOOK_CONFIG` to an absolute path of an owner-controlled JSON file:

```json
{
  "disabled_rules": [],
  "disabled_skills": ["skill/ui-delivery"],
  "record_events": false
}
```

An optional `state_dir` must be absolute. Skill IDs use the catalogue's
`skill/<name>` form; a disabled skill leaves the check and cannot be chosen
explicitly, which does not prevent the user or model from using it directly.
`disabled_rules: ["skill-check"]` turns the per-request check and the gate off
and keeps explicit choices; `"skill-gate"` turns off only the Claude gate. The
IDs of the retired phrase rules (`research`, `delegation`, `planning` and the
rest) are still accepted and do nothing, so an existing configuration keeps
working; any other unknown ID is an error.

Small namespaced technical reminder records reuse the existing `PipelineStore`
SQLite transactions, path checks and expiry, not a new storage engine. Each such
hook namespace is capped at 128 records with a 24-hour lifetime. These records
contain hashes, rule IDs, event names and decision classes, never prompts, paths,
arguments or transcript text. `record_events: true` enables bounded technical
event recording; it is off by default. Its evidence label is
`command_input_unattested`, not native execution. The separate
`feedback_capture` and `feedback_trigger` options have their own
[content consent, trigger and retention](feedback-capture.md), and do not share
the routing database or these namespace limits.

Scope includes client, session, working directory and agent identity. Codex also
uses transcript *identity* without opening that file; absent both agent and
transcript identity, it abstains from stateful behavior rather than merging all
workers under their parent's session. Codex turn/tool IDs deduplicate replayed
delivery. Delivery is checked transactionally **before** changing active context,
including prompts without a suggestion. An old duplicate cannot overwrite a newer task or
cancel pending restoration; changing rule versions does not create a new native
delivery. This protection lasts only while its bounded record remains retained,
not forever and not across unidentified deliveries. Claude prompt text is never hashed to invent a turn ID: identical words
can be a legitimate new task. Consequently duplicate Claude prompt deliveries
without IDs cannot be reliably suppressed.

A new request replaces the active suggestion, even when it names no skill. A
whole plain continuation such as `continue`, `resume` or `продолжай` can instead
retain an unexpired suggestion for the same identity and fingerprint; the check
is added again either way. Quoted/code/list examples, extra paragraphs and scope
modifiers are not this continuation form. `continue, but only prepare a plan` is
a new request; it clears rather than inherits.
The hook stores only a suggestion, not the task, permission or a `skills_used`
claim. The agent still reconciles the actual work and current authority through
[continuation](../../skills/implementation-planning/references/continuation.md).

Changed rules/skill entrypoint bytes invalidate restoration. Clear/end/expiry
retire context. Claude can restore on supported session resume/compact events.
Codex PostCompact accepts no additionalContext: it only marks restoration pending;
the next supported pre-tool event can include a brief reminder. If a routing
reply owns that event, the undelivered reminder remains pending, whether the
routing reply denies or rewrites the operation. A genuinely new prompt cancels
stale restoration. Without usable identity/data storage, no restoration is claimed.
Cross-plugin content duplication cannot be deduplicated by this runtime.

## Client contracts and model settings

Optional `pipeline.host` in the existing routing config records declared facts:

```json
{
  "surface": "cli",
  "version": "2.1.251",
  "provider": "anthropic",
  "agent_scope": "user"
}
```

These are examples, not discovered local settings. Unknown is the default. Doctor
separates declared host, documented mechanism, configured files and observations.
A manually supplied version is not an independently verified installed version.
Known non-CLI surfaces are not qualified for the strict adapter. Legacy configs
with unknown surface retain the existing guard with explicit unverified status.

### Claude

In evidence-only mode the Agent call carries both the model and the effort
(Claude Code 2.1.292 and later). Without a route table the hook refuses a launch
that does not name both; with one it checks the pair against the declared class, see
[route-table launches](../../skills/route-subagents/references/claude-code-routing.md#route-table-launches).

The frozen required mode predates the per-call effort field: its guard keeps
effort in generated agent frontmatter and rejects a supplied per-call effort even
for exempt agent types. It preserves the existing alias/pinned-model mechanism
and checks immutable definition bytes.
Plugin-scope definitions cannot preserve required permission fields, so the
routing generator rejects that declared scope. Definition presence remains
configured, not proof of discovery or effective permissions.

Model override handling distinguishes pre-2.1.251 CLI precedence, current CLI
precedence and unknown surfaces. Forced overrides remain conflicts. The literal
`inherit` is treated as unset only for a qualified version supporting that rule.
An unresolved `auto` effort cannot prove the selected effort. No global setting
is changed. Model/provider/organization caps still require runtime evidence.

A newly created agent directory may require reconnecting; a file watcher is not
a universal discovery receipt. Higher-priority same-name definitions and managed
settings remain unverified. Use native diagnostics before relying on selection.

Parallel calls may share an effort definition but pass different models. Start
order is provisional until a native return binds agent and tool-use IDs. Effort
and model observations follow the actual agent during rebinding; mismatch is
recomputed rather than copied to the wrong packet. Concurrent unbound advisors
of one definition are refused because private input needs an unambiguous identity.

Advisor handbacks accept only status fields. Unknown successful output envelopes
are rebuilt as a valid native `AgentOutput` with a decision reference and bounded
numeric telemetry, never arbitrary report/error/summary fields. Mandatory prompt
and usage fields remain present with sanitized values, so the client accepts the
replacement. Internal return-processing failures use the same schema.
Private advisor launches require `CLAUDE_CODE_DISABLE_BACKGROUND_TASKS=1` in the
environment that starts Claude. Otherwise the guard denies the launch: background
completion notifications bypass this replacement. See the
[required-routing setup](../../skills/route-subagents/references/required-routing.md#configure-once-outside-task-execution)
for the session-wide effect and alternatives.
Failure notifications, missing hooks and input too large to parse are not a proven
redaction boundary. Hooks are workflow checks, not isolation against a hostile
client/process. PostToolUse cannot undo work already performed.

### Codex

Hints, read-only preflight and, with a route table in evidence-only mode, a
`spawn_agent` check are supported: the hook refuses a spawn that does not follow
its declared class or would inherit the parent's settings, see
[route-table launches](../../skills/route-subagents/references/codex-routing.md#route-table-launches). The Claude receipt-injection/private
advisor protocol is **not** silently advertised as strict Codex routing. The
current documented Codex rewrite requires `allow`, and its native output contract
does not establish Claude's private return-rewriting guarantee. Explicit required
mode therefore denies protected spawns/routing operations on Codex while leaving
ordinary root work available. Evidence-only mode is an explicit owner choice.

Use the exposed tool schema, not an API's fields or Claude effort aliases. For a
read-only check of *supplied effective inputs*:

```text
python -I -B hooks/runtime/cli.py route-preflight --client codex --input route-inputs.json
```

The JSON object contains `expected: {model, effort}`, `supplied` native arguments,
and optionally `definition`, `defaults`, `parent`, `tool_schema`, `spawn_fields`. These
must come from the actual effective custom-agent/configuration/tool surface.
`spawn_fields` explicitly binds `model` and `effort` to argument names in that
reviewed native schema; null marks an unexposed field. Without a binding, the
preflight reports uncertainty instead of assuming that config keys are tool keys.
This command neither discovers hidden config nor grants a dispatch permit. It
checks selected routing fields and exposed enums, not a full JSON Schema validator.
Custom-agent values take precedence; selecting a model without a supplied/default
effort leaves that model's default unresolved, not inherited by assumption. A
custom definition setting only model preserves the previously resolved effort.

`route-preflight` exits 0 only when the supplied routing fields match without
unresolved evidence, 1 for a demonstrated configuration conflict, and 2 for
missing or invalid evidence. A conflict dominates concurrent uncertainty. Even
exit 0 does not verify a native launch; `launch_verified` remains false.

Hosted WebSearch, write_stdin continuation and documented specialized opt-outs
are not covered by these pre-tool hooks. Matcher aliases do not rename native
payloads: `spawn_agent` remains `spawn_agent`, not Claude's `Agent` envelope.

## Offline checks and evidence levels

```text
python -B -m unittest tools.test_hook_contracts tools.test_hook_regressions tools.test_skill_reminder tools.test_routing_pipeline tools.test_claude_variants
python -B tools/check.py --all
python -I -B hooks/runtime/cli.py replay --client codex --input sanitized-events.jsonl
```

Replay processes up to 1,000 bounded JSONL events with no installed configuration,
receipts or state. It cannot spend quota or replay a launch. Its result is labelled
`synthetic_replay`; a saved real event is still only a replay of input, not a fresh
client run. The prompt fixtures and expected results are independently authored.
Replay exits 0 only after processing at least one supported event without a
processing error. A valid event with no applicable hint is a successful check;
an empty input, unsupported event, invalid JSON or failed processing exits 2.
JSON inputs reuse the routing decoder, rejecting duplicate keys and non-finite
numbers rather than silently choosing a conflicting option. Live hook input
errors still exit 1 (non-blocking), not the diagnostic command's exit 2.

Fixtures test routing decisions, state transitions and generated shell commands.
They do not measure skill usefulness, actual client load, sandbox effectiveness,
model adherence or quota savings. No model benchmark/eval is required by this change.
Use ordinary work incidents to add sanitized regressions, and keep native observation
and human assessment separate from a green unit suite.

Replay shows only what the hook emits; the skill check is the same for every
prompt, so it cannot show which skills an agent then chooses. To measure that,
run real requests through the client, for example with a
[`claude plugin eval`](https://code.claude.com/docs/en/plugin-evals) suite whose
cases grade `tool_used: Skill`, in the languages you actually use and with nearby
cases where no skill should load. Such a suite loads only this plugin, so it
measures the check and the descriptions, not competition for the listing budget
in your full installation; check that with `/context` and the listing itself.

## Sources and adopted mechanisms

Contracts were checked against primary documentation on 2026-09-29. A new client
release must requalify affected claims rather than silently inheriting this date.

- [Claude subagents](https://code.claude.com/docs/en/sub-agents): model precedence,
  scope restrictions, discovery, frontmatter effort and event attribution.
- [Claude model configuration](https://code.claude.com/docs/en/model-config) and
  [hooks](https://code.claude.com/docs/en/hooks): environment/cap limits, one writer
  per event, permission-neutral rewrites and post-action observation limits.
- [Codex hooks](https://developers.openai.com/codex/hooks) and
  [subagents](https://developers.openai.com/codex/subagents): trust, aliases,
  PostCompact output, rewrite permissions, coverage and custom config precedence.
- [Claude skills](https://code.claude.com/docs/en/skills): description-based
  invocation and the listing budget that drops descriptions of rarely used skills.
- [Skill activation comparison](https://scottspence.com/posts/measuring-claude-code-skill-activation-with-sandboxed-evals)
  (blog, 2026-02): a hook that makes the model evaluate each skill before acting,
  measured against no hook and a plain reminder. Its keyword-free design replaced
  the earlier declarative phrase suggestions modelled on the
  [diet103 hook README](https://github.com/diet103/claude-code-infrastructure-showcase/blob/main/.claude/hooks/README.md).
- [Superpowers session hook](https://github.com/obra/superpowers/blob/main/hooks/session-start):
  client-specific output and avoiding double injection; not a full-skill dump.

The implementation reuses CommonMark, TOML, SQLite and existing routing ownership.
It adds no model router, general policy engine, custom markdown parser or installer.
