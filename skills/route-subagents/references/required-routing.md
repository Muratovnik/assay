# Required routing: configuration, execution and migration

This is the opt-in routing contract, protocol 3 in configuration schema 3. It
extends the existing evidence service and policy, not the native agent launcher.
Delegation must already be authorized. The primary owns task scope and acceptance;
a separate economical advisor owns ranking when inference is needed.

## One explicit mode

`pipeline.mode` defaults to `evidence-only`: without a configuration, for v1 and
v2 files and for a v3 file without a mode, the workflow is the existing one.
`get_routing_context`, the root-mediated advisor handoff and the CLI keep their
behavior, and the plugin hooks return no decision and add no context.

`required` is enabled only by an explicit `pipeline.mode: "required"`. It adds
no automatic fallback to root-side benchmark comparison when an advisor is
disabled, unavailable or invalid. `get_routing_context` is not registered on the
required-mode MCP server. Live CLI prepare, complete, record, context and
task-context cannot bypass host attestation. Explicit `--offline` operations
remain diagnostic: they do not issue native dispatch permission. Changing modes
is a visible owner decision, not an agent's recovery action.
`advisor.enabled=false` alone does not disable the guard.

The implemented host adapter is Claude Code. Codex and other hosts report
`required_routing_host_adapter_unavailable` from the MCP server, and the hook
runtime denies protected Codex spawns and routing operations when required mode
is selected. Familiar tool names do not make Claude's hook
payloads portable. What a Codex adapter must establish first is recorded in the
[Codex mechanics](codex-routing.md#required-mode-adapter-requirements). The optional hosted Jev backend remains available for the
evidence-only diagnostic workflow and its consent, not as a hidden required-mode
or native-advisor fallback.

## Configure once, outside task execution

For private native advisors, start Claude with
`CLAUDE_CODE_DISABLE_BACKGROUND_TASKS=1`. The guard refuses an advisor launch
without that setting before releasing its private input. Claude's
[native switch](https://code.claude.com/docs/en/env-vars) disables background
launches, auto-backgrounding and Ctrl+B for the whole session, including worker
and Bash tasks. Assay does not set it or change client configuration. Foreground
advisor input alone is insufficient: background completion notifications can
carry the raw report outside the PostToolUse replacement. Sessions that need
background workers can use approved routes without an advisor, or explicitly
choose evidence-only mode without the private-return guarantee.

When that switch is set in the MCP process too, registered foreground launch
inputs omit `run_in_background`: Claude removes that field from the active tool
schema. A background request is rejected as `background_tasks_disabled`.
The host still matches every returned launch argument exactly; no argument
coercion or weaker receipt check is used.

The MCP input tools declare `_meta["anthropic/maxResultSizeChars"] = 500000`,
Claude's documented ceiling for inline text results. Without that annotation,
Claude persists a successful result over 50,000 characters to a file; the private
advisor cannot read that file. This client delivery boundary is distinct from
the native snapshot budget and the required-mode store limit. Inputs exceeding
the host's inline ceiling cannot be assessed by this isolated delivery route;
do not grant file tools or treat a file reference as delivered evidence. See
[Claude MCP output limits](https://code.claude.com/docs/en/mcp#raise-the-limit-for-a-specific-tool).

Advisor replacements preserve the mandatory Claude `AgentOutput` fields and
bounded numeric usage. Prompts, citations, report fields and output-file paths are
removed. The guard-failure replacement uses the same native schema; a malformed
or unknown return receives an unverified identity and neutral telemetry, which
must not be treated as execution evidence.

Keep the old configuration bytes, MCP registration/environment, link vector and
revision outside managed roots. Migration creates a new file exclusively:

```sh
python skills/route-subagents/scripts/benchmark_router.py migrate-config --source OLD_CONFIG --output NEW_CONFIG --mode required
```

Both v1 and v2 inputs are supported. Without `--mode required` the result is an
evidence-only schema-3 file that behaves like its source. Client, preferences,
dated inventory and existing advisor/policy/telemetry options are preserved.
Migration neither updates a registration nor installs files.

A configuration example follows. All model names, paths, observation time and
capabilities below are placeholders: use the actual current client inventory and
observed supported combinations, not these names or the date verbatim.

```json
{
  "schema_version": 3,
  "client": "claude",
  "advisor": {"enabled": true, "backend": "native-economy"},
  "telemetry": {"mode": "metadata", "retention_days": 30},
  "pipeline": {
    "mode": "required",
    "state_dir": "/ABSOLUTE/PRIVATE/assay-routing-state",
    "agents_dir": "/ABSOLUTE/HOME/.claude/agents",
    "mcp_server": "assay-benchmark-routing",
    "inventory_file": "/ABSOLUTE/PRIVATE/assay-routing-inventory.json",
    "inventory_ttl_hours": 24,
    "advisor_route": {
      "model": "economy-alias",
      "effort": "low",
      "selection_basis": {"source": "caller", "reason_code": "bounded_ranking"}
    },
    "profiles": ["general-purpose"],
    "variants": [
      {"profile": "general-purpose", "model": "confirmed-full-id", "effort": "high"}
    ],
    "unrouted_agents": {"Explore": "baseline", "Plan": "inherit"},
    "agent_templates": {},
    "profile_capabilities": {},
    "approved_choices": {},
    "baseline": {"model": "worker-alias", "effort": "medium"}
  }
}
```

The inventory file holds `{"available": [{"model": "worker-alias",
"evidence_names": ["Confirmed spelling"], "efforts": ["low", "medium"]}, ...],
"observed_at": "2026-09-29T00:00:00Z"}`. An inventory model is either one of the
model aliases the host's Agent call accepts or a full ID; see the routes below.
The file is kept outside the policy file on purpose: sessions and the MCP server
are bound to the policy configuration, and confirming the inventory must not
require a reconnect. Record that the host still offers the listed models, or
replace the list, with:

```sh
python skills/route-subagents/scripts/benchmark_router.py --config NEW_CONFIG inventory-confirm [--available FILE] [--evidence-name MODEL=LABEL ...]
```

`--evidence-name` records the owner's confirmation that a benchmark source spells
a listed model as `LABEL`, for example a full ID that a source prints as a short
display name. The command then reports, for every inventory model, which cached
sources name it and up to five candidate spellings from sources that do not.
Candidates are advice for the owner: nothing binds a benchmark row until it is
confirmed, and a source that does not name a model may simply not measure it.

Preparation rereads the file. An observation older than `inventory_ttl_hours`
(1 to 720, default 24) refuses preparation; a caller repeating an old list cannot
renew it. An inline `inventory` is still accepted, but changing it changes the
policy configuration, so hosts and the MCP server must reconnect.

The advisor route is an owner-approved pair supported in the same host inventory,
chosen once from a user choice, confirmed economical client role or relevant
current evidence. `selection_basis.source` records `caller`, `client_role` or
`evidence`; the last can include bounded `evidence_refs`. No fixed model name is
shipped, no advisor chooses itself and no parent route is inherited silently.

### Routes: the model in the call, the effort in a definition

The Claude Agent call accepts a `model` but no effort, and only the four aliases
`sonnet`, `opus`, `haiku` and `fable`: a full ID supplied by a hook fails the
call's schema validation before anything launches. So a route travels in two
parts. For a profile listed in `profiles` and an alias model, the call carries
the alias and a generated definition for that profile and effort carries the
effort; one definition serves every alias with that effort. A model the call
cannot carry, such as a full ID, needs a `variants` entry: a definition for that
profile, model and effort, which pins the model in its own file. A variant also
takes precedence over a routed profile for its exact pair. A model without effort
support launches with any effort definition and reports no effort; list it with
one nominal effort, and its absent effort observation stays unknown.

A user's explicit model and effort for a packet travel as its `explicit` pair.
Policy honors it only for a confirmed inventory pair the adapter can express and
otherwise reports `invalid_explicit_choice`; it never substitutes another
pair. `approved_choices` maps packet IDs to owner-approved pairs that bind even
when the primary omits `explicit`; a request that contradicts one is refused.
`baseline` is a complete, separately authorized fallback pair, subject to all
packet constraints, and required mode needs one; see the failure boundaries
below. The primary cannot narrow the configured inventory or supply
per-candidate capability masks to manufacture a single-candidate shortcut.

`unrouted_agents` names native agent types, such as `Explore`, that the root may
launch without routing. They keep the client's ordinary permission flow, but not
the parent's model: the hook sets the call's `model` and leaves every other
field, including `run_in_background`, as the root sent it. A list gives each
type the baseline's model. An object maps a type to `"baseline"`, to
`{"model": ALIAS}` or to `"inherit"`, which keeps the parent's model as an
explicit choice. That model must be an alias the call accepts; a root call naming
a different model is refused, because an explicit choice goes through
`prepare_routing` for a routed profile. The effort of a native type stays the
session's. Generated `assay-` definitions cannot be listed, and a worker or
advisor may not launch any agent. Every other launch in a registered session
must be a registered one.

Optional `profile_capabilities` maps a profile to confirmed capability booleans,
for example `{"general-purpose":{"shell":true,"network":null}}`. Record only
capabilities verified for that profile under the active parent restrictions;
generated YAML alone does not establish them. Missing/false/unknown does not
satisfy a hard requirement. The adapter checks variant expressibility itself.

Use the existing isolated authoring environment for generation; PyYAML is already
in `requirements-tools.txt`. Core guards use only the standard library. The MCP
server uses the existing pinned official SDK. No new runtime dependency, alternate
transport, provider launcher or global environment modification is introduced.

```sh
python -B tools/assay.py claude-routes --config NEW_CONFIG
python skills/route-subagents/scripts/benchmark_router.py --config NEW_CONFIG doctor
```

`agents_dir` must be a project or user agent directory actually discovered by the
client. Plugin agents apply `effort`, but they ignore `permissionMode`, so the
plugin's bundled agent directory would drop a catalogued profile's restrictions;
generated definitions stay in the owner's directory. Names are immutable
`assay-<profile>-<effort>-<configuration-fingerprint>.md`. Generation writes one
definition per routed profile and per effort that the confirmed inventory offers
for an alias, each requested variant and the configured advisor, never a
Cartesian product of all models. A new alias model therefore needs no
regeneration unless it brings an effort nobody generated; doctor reports that
gap. An effort definition drops a template's own `model`, so a launch that
arrived without one could not silently use it. Canonical templates keep their
capability restrictions; canonical JSON profiles still contain no model, effort
or runtime state. `agent_templates` maps a new profile name to an existing user
or project definition file, which is read, never changed, and cannot shadow a
catalogued or internal name. Internal routing-advisor and general-purpose
templates are execution adapters, not new neutral personas.

Generated definitions carry no hook of their own. The advisor's definition lists
only its two routing tools and the native handback, and the host enforces that
list: an unlisted tool is not available to the advisor at all. A worker keeps
its profile's tools; its observed effort is checked when it stops, not midway,
because stopping it mid-task would leave partial changes. Definitions generated
by earlier releases still call the hook with `--scope agent`; that scope now
answers nothing, and `claude-routes --prune` removes those files.

In this mode the plugin's delegation reminder stays silent on Claude launches:
the registered protocol and the guard's refusals already speak for them. The
session reminder and Codex launches keep their reminders.

Set `ASSAY_ROUTING_CONFIG` to the absolute new configuration path in the environment
that launches **both Claude Code and its MCP child**. For example on POSIX:

```sh
export ASSAY_ROUTING_CONFIG=/ABSOLUTE/PRIVATE/routing.json
claude
```

Setting it only on the MCP child does not configure parent hooks. Retain the
installed server's Python executable, browser/cache options and timeout. A
conflicting `--config` is rejected. The actual MCP tool prefix must match
`pipeline.mcp_server`: a plugin-scoped registration may have a different name;
inspect the installed tools rather than copy the example prefix. Install the
updated generated plugin hooks and reconnect. A skill-only install does not
supply those hooks. Do not silently edit global permissions or root effort.

Doctor/status reports configuration, inventory age and support gaps, not
fabricated discovery or effective permissions. `setup_gaps` names what required
mode still lacks. `route_checks` examines every route the configuration can
select before any launch: each variant, each alias pair of a routed profile and
the advisor. It reports whether the pair is in the confirmed inventory, whether
its definition is generated and unmodified without a conflicting environment
override, whether the call carries the model, for which profiles the baseline is
expressible and which model each exempt agent type launches with.
`adapter_capabilities` states what the Agent call can carry, and
`alias_observations` lists what the host resolved each alias to and any change
the owner has not confirmed yet. `model_names` is the spelling report described
with `inventory-confirm`. Doctor
deliberately leaves installation/discovery unverified until there is real client
evidence. Verify with one authorized bounded task in the intended client/version
before asserting native behavior or quota savings.

## Execute the registered chain

Call `prepare_routing` with structured packets and one private execution request
per packet. The existing [advisor feature contract](routing-advisor.md) applies.
For example, with no unverified capability claim:

```json
{
  "packets": [{"packet_id":"parser-change","task_types":["implementation","tests"],"features":{}}],
  "launch_requests": {
    "parser-change": {
      "profile":"general-purpose",
      "prompt":"Implement the authorized parser change in the assigned files. Preserve exclusions and return test evidence. Do not delegate.",
      "description":"Bounded parser change",
      "run_in_background":false
    }
  }
}
```

The root gets only decision identifiers, expiry, compact reasons and either a
completed decision or a small `handoff`. A full approved or explicit choice,
single eligible pair or valid exact cache hit avoids an extra advisor invocation.
The hook inserts a short-lived, one-use receipt tied to the actual host session,
tool and argument hash; it is not a parameter for the model to manufacture. A
receipt lives five minutes, enough for an ordinary permission prompt; allow the
routing tools in advance if approvals routinely take longer.

For a handoff, invoke the returned native `input` unchanged. The launch gate
checks the prepared advisor attempt. `SubagentStart` binds that attempt to the
host's real child identity. Only this child can call `get_advisor_input` for that
decision and submit schema-validated JSON via `complete_routing`. Its allowlist
contains those operations and a sanitized native handback; delegation, arbitrary
MCP access and workspace tools are denied. No benchmark snapshot or ranking is
forwarded through the root prompt. The private advisor prompt revision is v4;
the evidence-only root handoff keeps v3, so their answers never share a cache.

The advisor finishes with status only. Supported `PostToolUse` output rewriting
replaces only its text-content blocks while preserving the native output shape
and telemetry; native handback reports are sanitized too. This does not rewrite
host transcripts or provider telemetry. The primary reads `get_routing_decision`
after the host returns the advisor invocation; submission alone cannot authorize
workers or seed the shared semantic cache.

Then call `authorize_routing_launch(decision_id, packet_id)` and send the exact
returned Agent input. It is a stub without the prompt, and for an alias route it
already names the `model`: the hook recognizes the stub and substitutes the
registered input, so the root neither repeats nor alters a prompt. The gate binds
the packet prompt, profile, definition, model, current configuration, session,
expiry and individual attempt. Altered stubs, another packet's record, model
overrides, expired records and reused attempts are rejected. It returns no
automatic permission grant: normal client approval and permission checks evaluate
the substituted input. Effort stays in the generated definition until the Agent
tool accepts it per call ([open feature request](https://github.com/anthropics/claude-code/issues/77298));
foreground defaults avoid relying on anything else.

Several packets may use the same definition and start in one message. The start
event does not name the parent's tool call, so start order binds provisionally
and the Agent result, which names both the call and the agent, corrects the
attribution. Model, effort and permissions are identical for such siblings, so
only the packet identity can be provisional, and it is settled before continuation
or outcome recording can use it. A launch that auto mode denies is released and
may be sent again. A launch rejected in an interactive permission dialog produces
no host event: its attempt stays consumed, so prepare that packet again.

`retry_of` permits a fresh attempt only after the host observed the earlier
invocation fail and no other attempt is active. `resume_agent_id` continues only
the same observed idle worker, same definition and original packet, without
replaying completed writes or changing scope. An advisor cannot be resumed this
way. A new task, changed constraints, replacement or reviewer needs preparation;
continuation of an existing worker is not a new model-selection decision.

## Observations, failure and privacy boundaries

Requested settings, configured definition bytes and host observations are separate.
The documented hook effort value is an object with a `level`; `SubagentStop`
carries it, `SubagentStart` does not. Agent's structured `resolvedModel` and
`modelsUsed` provide model observations. An observed mismatch invalidates advice
and blocks continuation and further routing calls of that agent; it cannot undo a
tool action the native client already performed. Unknown model/effort remains
null; a self-reported `resolved_model` in the advisor JSON is not host evidence.
An early stop event does not skip the later Agent result check. Conflicting
effort/subagent-model environment overrides are rejected, not changed.

A full ID must be the model the host reports. An alias is resolved by the host,
never guessed: the hook records what `resolvedModel` reported for it, outside any
session, and the first observation establishes that resolution. A different
resolution later is an inventory event, not a mismatch. It is recorded with the
attempt and in `alias_observations`, and until the owner runs `inventory-confirm`
again, preparation drops that alias's confirmed `evidence_names`, because they
describe the model it used to resolve to, and returns an
`alias_resolution_changed` warning. A switch of models inside one run is still a
mismatch.

Required mode is not set up without a configured baseline. Status and doctor
report `setup_required` with the `baseline` gap, routing operations fail with
`required_routing_setup_incomplete`, and the hook refuses every launch except an
exempt type with its own model or `inherit`. Abstention, invalid advice, an advisor that ends without a
result and a disabled advisor select the eligible baseline as a `fallback`
decision whose reason codes name the cause. A baseline that a packet's hard
constraints exclude still means no decision, not root-side selection.
Expiry or configuration/inventory change requires preparation again.

The guard fails closed only where it is the gate. When it cannot load the
configuration or validate a launch or routing call, it denies that call with a
reason. Every other event and tool gets no decision, and a subagent is never kept
from stopping. Some cases stay outside any hook's control: a hook that times out,
a missing `python`, disabled hooks, a client that ignores output rewriting or an
unsupported field lets the native action proceed. These are real compatibility
limits; static configuration does not establish effectiveness.

A bounded SQLite rendezvous under `state_dir` supports hooks and MCP processes
without a new service. Receipts expire after five minutes; private decision data
expires after at most ten minutes or earlier inventory/evidence expiry. Raw attempt
input is removed when the host observes start/return; decision execution prompts
remain only for the decision lifetime. Minimal observed attempt metadata remains
for up to 24 hours to support outcomes and same-worker continuation. A session's
registration lasts a day after its last routing activity. SessionEnd removes that
session's records. Alias observations belong to no session: each lasts 30 days
after its latest observation. Expired data is deleted on the next transaction, not by a
background scheduler; SQLite secure deletion is enabled. Use a private local state
directory and OS access controls, including appropriate Windows ACLs.

Existing optional history/telemetry is separate and retains its configured
consent and lifetime. Full diagnostic retention must be explicit. Report advisor,
coordination, worker, retries and verification when assessing completed-task cost;
final-call token counts alone are not that total. No paid comparison campaign is
required or authorized by setup.

Host receipts prevent ordinary protocol forgery, not a hostile process with full
filesystem/configuration access. This is not a cryptographic sandbox or a security
boundary against a root agent that can rewrite its own environment. Native model
execution, version-specific discovery, effective permissions and observed quality
still require real client receipts. Synthetic hook tests and actual SDK transport
tests are labeled separately from those claims.

## Update, pruning, removal and rollback

Re-run `claude-routes` after changing profiles, templates or configured
combinations, or when the inventory offers an alias effort that has no definition
yet. Generation is idempotent; foreign files, modified owned files and
linked/reparse ancestors are refused. A definition deleted outside Assay simply
ends its ownership and is recreated when still configured. Superseded definitions
remain recorded as retired, never selected. Definitions of an earlier release,
listed in a schema-2 manifest, become retired entries of the current one: no route
selects them, and they stay owned until pruned. `--prune` removes only unchanged owned
inactive variants and retains variants referenced by active runtime records.
`--remove` uninstalls every unchanged owned inactive definition and the manifest,
keeping modified or active ones recorded; once nothing owned remains it deletes
the generation lock file as well. Creation, deletion and final manifest
writes have rollback for recoverable I/O errors; user-authored files are not
overwritten. Do not manually rename a managed definition or edit its file.

For a mode rollback, explicitly set `pipeline.mode` to `evidence-only` and reconnect
both host and MCP; the hooks then return no decision. For revision rollback run
`claude-routes --remove` with the current revision first, then restore the retained
old config, old registration/link vector and old revision together; use the old
revision for its own uninstall operation. Preserve user files and separately
retained history. Protocol-3 runtime records and v4 prompt answers cannot be
reused as old live permissions. Rehearse rollback in an isolated directory, not
against running work.

Primary contracts (verified 2026-09-29):
[Claude hooks](https://code.claude.com/docs/en/hooks) and
[Claude subagents](https://code.claude.com/docs/en/sub-agents). The per-call
model's precedence over a definition, the four accepted aliases, the refusal of
a hook-supplied full ID and effort taken from the definition were observed in
Claude Code 2.1.284; recheck them after a client upgrade.
