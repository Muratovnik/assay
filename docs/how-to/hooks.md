# Configure and diagnose command hooks

Assay's plugin hooks are local commands, not prompt/agent hooks. They do not call
models, install dependencies, launch advisors or modify client settings. In Claude
Code the skill gate and the source check read the tail of the session transcript
at `Stop` and `SubagentStop`, and the [mid-turn skill note](#mid-turn-skill-note-in-claude-code)
reads it at `PreToolUse` when the gate's records do not show a skill loaded. Their text and any
subsequent agent work still consume context/quota.
Skills-only installations do not install hooks.

## Install, enable and verify separately

The generated Claude manifest is `hooks/hooks.json`. Codex explicitly selects
`hooks/codex.json` through its plugin manifest. Both invoke one runtime command
per matching event. `PreToolUse` matches every tool, because the reading-role
boundary and the spawn checks need to see each call; result and failure events
match only the native spawn tools, and in Claude Code also `WebFetch` results for
the [source check](#source-checks-in-claude-code).
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
apply. When it starts applying a skill not yet in use in the conversation, or the
set changes, it opens that message with one short sentence in the user's
language that names each skill in backticks and says what it is for:

```text
Using `assay:code-change` and `assay:test-writing` to fix the parser and cover it.
```

It then loads each named skill it has not loaded yet before any other tool call.
A missing tool does not make a skill inapplicable: a skill that needs one is still
announced and loaded, and the agent says what is missing. When no skill applies, or the skills already in use still fit, as in a
follow-up question, a turn after a subagent's notification or a continuation, it
says nothing about skills, and it does not restate the sentence later in the
turn. If it skips a skill the task obviously calls for, it says why in a few
words, without backticks, so the gate below does not read that as an
announcement. The check lists every installed, enabled skill with a one-line cue
from `hooks/activation-rules.toml`. The model judges relevance from the task in
whatever language it is written; the hook reads nothing in the prompt to build
the check. In Claude Code, once the session has loaded skills, the check also
names them (`Already loaded in this session: code-change.`) from the gate's
records, so the agent can tell which skills are already in use.

The check exists because a skill's description is the only automatic route to it,
and that route is unreliable on its own. Claude Code drops the descriptions of the
least-used skills when its listing exceeds the
[character budget](https://code.claude.com/docs/en/skills#skill-descriptions-are-cut-short),
and a model that sees a description can still decide to answer without the skill.
In a [published comparison](https://scottspence.com/posts/measuring-claude-code-skill-activation-with-sandboxed-evals),
a hook that made the model evaluate each skill before acting activated skills far
more reliably than no hook or a plain reminder. That was one author's small,
English-only sample, so treat it as a reason to measure, not as a guarantee.

Earlier versions asked for a line such as `Assay: code-change` at the start of
every reply and again in the final reply, and `Assay: none` when nothing applied.
The line repeated on every turn, including turns that only answered a
subagent's notification. The sentence follows the format Codex uses for its own
skills and Anthropic's
[guidance for Claude](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5#user-facing-progress-updates):
say in one sentence what you are about to do before the first tool call.

The check costs about 2 KB of English text (roughly 500 tokens) on every
prompt, in Claude Code and Codex alike; in Claude Code the list of skills
already loaded adds up to 0.3 KB more. A test keeps it under 2,700 characters
with room for one more skill. It stays in the conversation until
compaction. It is not re-sent when a session resumes or compacts, so after a
compaction the current request's check may survive only in the summary.
In Codex the check adds that Codex's own skill instructions already ask for such
an announcement, so the agent makes one announcement with the exact
`assay:<name>` names rather than two.
A subagent's packet is not a user prompt, so subagents get a variant at their
start instead, see [subagents](#subagents). The agent leaves the sentence out
when a request fixes an exact output format. For scripted runs whose output must
stay clean, such as `claude -p` pipelines, turn the check off with
`disabled_rules: ["skill-check"]` (see below).

### The skill gate in Claude Code

Naming a skill is not loading it: in measured runs an agent sometimes named
`evidence-research` and went straight to the work. In Claude Code a `PreToolUse`
record notes each Assay skill the session loads, through the Skill tool or a read
of its `SKILL.md`. When the turn announces a skill this session has not loaded,
the `Stop` hook continues the turn once with feedback saying so. An announcement
is an `assay:<name>` in backticks on the first line of one of the turn's
messages, or the earlier format's leading `Assay:` line. The feedback asks for the
skill to be loaded and the work checked against it, and says that the answer
already given stands: a single line is enough when nothing changes, otherwise
only the corrections that matter, without repeating the answer. It is
`additionalContext`, not a block, so Claude Code shows it as hook feedback rather
than a hook error and applies its usual limit on stop-hook continuations. The
gate stays silent while `stop_hook_active` is set. It needs the plugin data
directory, so it is inert without hook state.

The announcement usually opens an earlier message of the turn than the final
reply, so the gate reads the tail of the session transcript, as the
[hooks reference](https://code.claude.com/docs/en/hooks) suggests for conditions
the hook input alone cannot settle. The same read finds loads its records miss.
A continued, resumed or forked session has a new session ID and empty records,
but its transcript carries the earlier loads. After a compaction only the skills
the compaction re-attached count, because older loads are no longer in the
context. A record's 24-hour lifetime restarts each time the gate uses it, so a
long session keeps its loads. The transcript is written asynchronously and may
not yet hold the turn's latest messages; the gate reads at most the last 16 MB,
skips the subagents' entries in the main transcript, and stores only skill names.
When the transcript cannot be read, the records alone decide, as before.

The gate guarantees only that an announced skill gets loaded. It cannot tell
whether the agent chose the right skills; a turn without an announcement passes.
A line that only mentions a skill in backticks with the `assay:` prefix can
continue a turn once; the feedback lets the agent answer that in one line. A
subagent's load does not count for the main session. Codex has no gate: its
skill loads are not visible reliably enough to act on. Turn the gate off with
`disabled_rules: ["skill-gate"]`; disabling the check also disables it.

### Subagents

A subagent starts without the main session's loaded skills and never receives
the per-request check. At `SubagentStart`, in Claude Code and Codex, the hook adds
a check for the subagent instead: the skills its packet names apply, it may add
others its work needs, it loads each before the work, through the skill tool or
by reading `<name>/SKILL.md` under the installed `skills` directory, which the
check names for profiles without the skill tool. It opens its first message with
the same one-sentence announcement and does not restate it in its report. The
required-mode routing advisor, whose answer is a fixed structure, gets no check.
In Claude Code the gate above also runs at `SubagentStop`. It reads the
subagent's own transcript, including a report delivered through
`SubagentHandback`: a subagent that announced a skill it did not load continues
once. Codex `SubagentStop` accepts no feedback context, so Codex subagents get
the check only. `disabled_rules: ["skill-check"]` turns off the subagent check as
well.

Phrase rules that matched English/Russian wording were retired: they missed
paraphrases and every other language and needed a rule per phrasing. Only an
explicit skill choice is still recognized deterministically. It adds a short
suggestion naming that skill in front of the check. Explanations, quoted commands
and negative requests do not count as a choice. The CommonMark parser excludes
blockquotes, fenced/indented code, lists and headings, and only the first request
paragraph can make a choice.

### Source checks in Claude Code

A `WebFetch` result is not the page. Claude Code hands the page to a model with the
fetch prompt and returns that model's answer, with short paraphrased quotes, and a
blocked or challenge page can come back as a summary of the block. In a measured
run an agent made seven such fetches of one study, got a challenge page, a 403 and
a 404, and answered from a news article and the abstract; with a shell download
of the same page it found the table the answer depended on.

After the first `WebFetch` result of a request, the `PostToolUse` hook adds a note
saying so: a conclusion that rests on the page needs its text, downloaded with a
shell command such as `curl` or `gh` and read where the conclusion depends on it,
or the answer says it rests on the fetch summary. The note appears once per
request and agent, keyed by the prompt ID Claude Code sends; without one, once per
agent. It needs the plugin data directory, where it keeps one hashed key per
request and agent.

At `Stop` and `SubagentStop` the hook reads the same transcript tail as the skill
gate. When a line of the turn says a file or URL was read in full (`in full`,
`entire`, `end to end`, `целиком`, `полностью` and similar) and names a file
whose `Read` calls returned only part of it, or a URL opened only through
`WebFetch`, the turn continues once with feedback naming what was read. As with
the gate, the answer stands and one line is enough when nothing changes. The
check fires only on positive evidence. A file printed with a shell command leaves
no `Read` in the transcript, and a URL that a shell command also names counts as
downloaded, so neither triggers it. Reads before the latest compaction are not
counted. A subagent's transcript records no line counts, so there a ranged read
counts as reaching the end only when it returned fewer lines than its limit, and
a plain `Read` counts as complete. The skill gate's feedback takes priority at the
same stop. `disabled_rules: ["fetch-note"]` turns off the note after a fetch and
`"read-claims"` the stop check; each works without the other.

### Branch check in Claude Code

A skill routes conditional depth into `references/`, and its `SKILL.md` names when
each reference applies. Loading the skill does not load those references. In two
weeks of observed sessions agents loaded a skill and skipped a reference whose
condition the turn plainly met in about two of three sampled turns. In one of them
an agent loaded `evidence-research`, skipped its `search-and-coverage` reference,
searched once with a candidate list fixed in advance and answered that none of the
existing skills did what the user wanted; the user then found several that did.

At `Stop` and `SubagentStop` the hook reads the same transcript tail and checks a
fixed table. Each row pairs a reference with a sign of its condition that the turn's
own actions or words show:

| Rule | Skill and reference | Sign in this turn |
| --- | --- | --- |
| `coverage-claims` | `evidence-research` → `search-and-coverage` | a line saying that no tool, skill, library or other solution exists, or that none of the candidates qualifies (`none of these skills`, `there is no maintained library`, `ни один из навыков`, `готового решения нет` and similar) |
| `branch-vue-structure` | `code-change` → `vue-structure` | an edited `.vue` file |
| `branch-quality-checks` | `code-change` → `effective-quality-checks` | an edited linter, formatter, type-checker, test-runner, hook or CI configuration file, a tool section written into `pyproject.toml` or `setup.cfg`, or `git mv` |
| `branch-bounded-review` | `independent-audit` → `bounded-review` | an agent launched as a reviewer or auditor, by its type or its description; a worker that fixes or implements findings does not count |
| `branch-implementation-units` | `implementation-planning` → `implementation-units` | a new plan file written with `Write`: one under a `plans` directory or named for a plan |
| `branch-ui-acceptance` | `ui-delivery` → `scenario-testing` and `visual-judgment` | an edited component, markup or style file other than a test |
| `branch-languages` | `technical-writing` → `languages` | a documentation file written with at least forty Cyrillic or Chinese characters, except agent memory notes |

When a row's sign appears in this turn, the session or subagent loaded the skill
since the latest compaction, and the reference was not read in that span by `Read`
or a shell command naming it, the turn continues once. One note names every such
reference with the condition the skill states and the turn's own evidence, quoting
up to two lines or naming up to two files. A skill that compaction re-attached
counts as loaded, but a read before compaction does not count. A session or
subagent that has not loaded the skill is not held to its references, and a sign
from an earlier turn does not count.

The signs are deliberately narrow and still approximate. A write made through a
shell command is not seen. The absence wording can match a documented fact about
the work; one line saying the claim is limited to what was examined answers it.
A condition the transcript cannot show, such as whether a comparison is
consequential, has no row. The skill gate's feedback and a contradicted full-read
claim take priority at the same stop, since a turn continues at most once. Each
rule ID in `disabled_rules` turns its row off; a disabled skill drops its rows too.

### Mid-turn skill note in Claude Code

The skill check arrives once per request, and some work shows its skill only
later: an agent downloaded documentation with `curl` without loading
`evidence-research`, and nothing in the request had named research. The announcement rule above is
a request to the agent; this note is a fact it can act on at the call itself.

At `PreToolUse`, when one tool call shows a sign from the table below and neither
the gate's records nor the transcript tail show that skill loaded by this agent,
the hook adds a note of about 300 characters. It names what the call does (a file
name or a host, never a path or a URL), the skill and the decision that skill
governs there, and says the session has not loaded it. An example, for an edit of
a test file: `Assay skill note: this call edits a test file (test_app.py). The
assay:test-writing skill governs what behavior the test pins and whether it fails
without the fix; this session has not loaded it. The skill check expects it
loaded (skill tool or its SKILL.md) and named in one short sentence.` It is
stated as fact and runs no model.

| Rule | Skill | Sign in one tool call |
| --- | --- | --- |
| `midturn-evidence-research` | `evidence-research` | `WebFetch`, `WebSearch`, or a shell command whose `curl`, `wget`, `Invoke-WebRequest` or `Invoke-RestMethod` targets a non-local URL; a reachability probe (`-I`, output discarded), `gh api` and a local address do not count |
| `midturn-code-change` | `code-change` | an edit or write of a source file (Python, Go, JavaScript and TypeScript, C#, Java, shell and PowerShell scripts and similar) that is not a test, an interface file or generated output |
| `midturn-test-writing` | `test-writing` | an edit of a test file: under `test`, `tests`, `__tests__` or `spec`, named `test_*`, `*_test.*`, `*.test.*` or `*.spec.*`, or `conftest.py` |
| `midturn-ui-delivery` | `ui-delivery` | an edit of an interface file: `.vue`, `.svelte`, `.jsx`, `.tsx`, `.css`, `.scss`, `.sass`, `.less`, `.html` |
| `midturn-technical-writing` | `technical-writing` | an edit of a `README` or of a Markdown, MDX or reStructuredText file under `docs`, except `docs/plans` and `docs/research`; agent instructions, memory notes and change logs do not count |
| `midturn-skill-evaluation` | `skill-evaluation` | an edit of a `SKILL.md`, a skill's `references` or `evals` file, or `activation-rules.toml` |

A path under `node_modules`, `dist`, `build`, `vendor`, `.venv`, a minified, declaration
or generated file, and a scratch directory (`tmp`, `temp`, `scratchpad`, `.private`)
gives no sign. A task worktree under `tmp/worktrees/<name>` is a checkout, so its files do. A
file belongs to one row: a test file gives `test-writing` and not also `code-change`,
an interface file `ui-delivery` and not `code-change`.

The note appears at most once per skill, request and agent. The key is one hashed
entry kept like the fetch note's, from the prompt ID Claude Code sends and the
agent ID, and without a prompt ID it appears once per agent. A skill counts as
loaded when the gate's records show it, otherwise when the transcript tail does:
the Skill tool, a `Read` of its `SKILL.md`, or a skill that a compaction
re-attached. The loads found there are added to the records, so a resumed session
reads the transcript once. A subagent is judged by its own records and its own
transcript, the file under `<session>/subagents/`. A skill read with a shell command is not
seen as loaded, and neither is a write made with one. A routing guard's reply, a read-only profile's
refusal and the launch reminder on the same call take priority and the note is
not given. The note needs the plugin data directory and goes with the skill check:
`disabled_rules: ["skill-check"]` turns it off with the check, and a disabled skill
drops its row.

The option `skill_note_form` in the hook configuration chooses the form. `note`, the
default, gives the text as context beside the call. `deny` refuses the first
matching call with the same text as the reason and passes the repeated call, so
it costs one extra turn and shows the reason in Claude Code as a refusal. Both
forms keep the key, so a skill is named once either way.

Codex gets no note. A Codex agent reads a `SKILL.md` with a shell command such as
`Get-Content`, often inside a longer command or the code-mode `exec` wrapper, and the gate keeps no load
records for it. In a sample of Codex sessions from two weeks, 134 of 463 command items that name a
`SKILL.md` carried Codex's own `read` classification; the other 329 were compound
commands, searches and listings that name the file without loading it. Until the load can be
recognised from the hook input and survives a compaction, a note would either
sound every time or never, so no row is enabled there.

The signs are narrow and approximate. Over two weeks of one owner's sessions, a
sample of up to 20 notes per row had at least 80 % of its notes appropriate
(the skill really applied to what that call was doing). A row on a different
kind of work can behave differently; each rule ID turns its row off.

## Hints do not grant authority

Neither the check nor an explicit-choice suggestion authorizes edits, delegation,
installation or tool use beyond the request; both say so. A suggestion asks to
reuse sufficient existing research/plans and preserve the user's scope. It does
not claim to load a skill or assume that a particular MCP tool exists. Even an
observed Skill load or an announcement would not prove compliance with a method.

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
  "skill_note_form": "note"
}
```

An optional `state_dir` must be absolute. Skill IDs use the catalogue's
`skill/<name>` form; a disabled skill leaves the check and cannot be chosen
explicitly, which does not prevent the user or model from using it directly.
`disabled_rules: ["skill-check"]` turns the per-request check and the gate off
and keeps explicit choices; `"skill-gate"` turns off only the Claude gate, and
`"fetch-note"` and `"read-claims"` the two Claude source checks, and each
rule ID of the branch check table or of the mid-turn note table one of its rows.
`skill_note_form` is `"note"` (the default) or `"deny"`, see the mid-turn note above. The
IDs of the retired phrase rules (`research`, `delegation`, `planning` and the
rest) are still accepted and do nothing, so an existing configuration keeps
working; any other unknown ID is an error.

Small namespaced technical reminder records reuse the existing `PipelineStore`
SQLite transactions, path checks and expiry, not a new storage engine. Each such
hook namespace is capped at 128 records with a 24-hour lifetime. These records
contain hashes, rule IDs, event names and decision classes, never prompts, paths,
arguments or transcript text. The hooks keep no event log and no feedback
records. The options `record_events`, `feedback_capture` and `feedback_trigger`
were removed with them; a configuration that still names one is refused with a
message listing the removed names, so delete them from the file.

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
Before either check it refuses an Agent call made inside a subagent, because only
the primary routes; see
[launches from a subagent](../../skills/route-subagents/references/claude-code-routing.md#launches-from-a-subagent).

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
[required-routing setup](required-routing.md#configure-once-outside-task-execution)
for the session-wide effect and alternatives.
Failure notifications, missing hooks and input too large to parse are not a proven
redaction boundary. Hooks are workflow checks, not isolation against a hostile
client/process. PostToolUse cannot undo work already performed.

### Codex

Hints, read-only preflight and, with a route table in evidence-only mode, a
`spawn_agent` check are supported: the hook refuses a spawn that does not follow
its declared class or would inherit the parent's settings, see
[route-table launches](../../skills/route-subagents/references/codex-routing.md#route-table-launches).
Codex hook input does not name the calling agent, so a child's own spawn is held
only by `agents.max_depth`; see
[launches from a subagent](../../skills/route-subagents/references/codex-routing.md#launches-from-a-subagent). The Claude receipt-injection/private
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
