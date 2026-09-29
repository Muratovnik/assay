# Required routing: configuration, execution and migration

This is the live routing contract, protocol 2 in configuration schema 3. It
extends the existing evidence service and policy, not the native agent launcher.
Delegation must already be authorized. The primary owns task scope and acceptance;
a separate economical advisor owns ranking when inference is needed.

## One explicit mode

`pipeline.mode` defaults to `required`, including when an older configuration is
loaded. There is no automatic fallback to root-side benchmark comparison when
an advisor is disabled, unavailable or invalid. `get_routing_context` is not
registered on the required-mode MCP server. Live CLI prepare, complete, record,
context and task-context cannot bypass host attestation. Explicit `--offline`
operations remain diagnostic: they do not issue native dispatch permission.

`evidence-only` must be selected explicitly in a schema-3 configuration. It
exposes the legacy comparative workflow without isolated-advisor or launch
assurances. Changing to that mode is a visible owner decision, not an agent's
recovery action. `advisor.enabled=false` alone does not disable the guard.

The implemented host adapter is Claude Code. Codex and other hosts report
`required_routing_host_adapter_unavailable`; familiar tool names do not make
Claude's hook payloads portable. Their legacy manual workflow requires explicitly
selected evidence-only mode. The optional hosted Jev backend remains available
for that separately configured diagnostic workflow and consent, not as a hidden
required-mode or native-advisor fallback.

## Configure once, outside task execution

Keep the old configuration bytes, MCP registration/environment, link vector and
revision outside managed roots. Migration creates a new file exclusively:

```sh
python skills/route-subagents/scripts/benchmark_router.py migrate-config --source OLD_CONFIG --output NEW_CONFIG
```

Both v1 and v2 inputs are supported. Defaults are schema 3 and required mode;
client, preferences, dated inventory and existing advisor/policy/telemetry options
are preserved where present. Migration neither updates a registration nor
installs files. `--mode evidence-only` is an explicit alternative, not a default.

A configuration example follows. All model names, paths, observation time and
capabilities below are placeholders: use the actual current client inventory and
observed supported combinations, not these names or the date verbatim.

```json
{
  "schema_version": 3,
  "client": "claude",
  "inventory": {
    "available": [
      {"model": "confirmed-economy-id", "efforts": ["low"]},
      {"model": "confirmed-worker-id", "efforts": ["medium", "high"]}
    ],
    "observed_at": "2026-09-29T00:00:00Z"
  },
  "advisor": {"enabled": true, "backend": "native-economy"},
  "telemetry": {"mode": "metadata", "retention_days": 30},
  "pipeline": {
    "mode": "required",
    "state_dir": "/ABSOLUTE/PRIVATE/assay-routing-state",
    "agents_dir": "/ABSOLUTE/PROJECT/.claude/agents",
    "mcp_server": "assay-benchmark-routing",
    "advisor_route": {
      "model": "confirmed-economy-id",
      "effort": "low",
      "selection_basis": {"source": "caller", "reason_code": "bounded_ranking"}
    },
    "variants": [
      {"profile": "general-purpose", "model": "confirmed-worker-id", "effort": "medium"},
      {"profile": "general-purpose", "model": "confirmed-worker-id", "effort": "high"}
    ],
    "profile_capabilities": {},
    "approved_choices": {},
    "baseline": null
  }
}
```

The advisor route is an owner-approved pair supported in the same host inventory,
chosen once from a user choice, confirmed economical client role or relevant
current evidence. `selection_basis.source` records `caller`, `client_role` or
`evidence`; the last can include bounded `evidence_refs`. No fixed model name is
shipped, no advisor chooses itself and no parent route is inherited silently.

`approved_choices` maps packet IDs to complete owner-approved model/effort pairs.
Those choices are binding even if the primary omits `explicit`. A request cannot
invent or contradict them. `baseline` is a complete, separately authorized fallback
pair, subject to all packet constraints; absent or ineligible means no fallback.
The primary cannot narrow the configured inventory or supply per-candidate
capability masks to manufacture a single-candidate shortcut.

Optional `profile_capabilities` maps a profile to confirmed capability booleans,
for example `{"general-purpose":{"shell":true,"network":null}}`. Record only
capabilities verified for that profile under the active parent restrictions;
generated YAML alone does not establish them. Missing/false/unknown does not
satisfy a hard requirement. The adapter checks variant expressibility itself.
Configuration freshness is not renewed by a caller repeating the same list:
inventory expires after 24 hours and must be observed and updated explicitly.

Use the existing isolated authoring environment for generation; PyYAML is already
in `requirements-tools.txt`. Core guards use only the standard library. The MCP
server uses the existing pinned official SDK. No new runtime dependency, alternate
transport, provider launcher or global environment modification is introduced.

```sh
python -B tools/assay.py claude-routes --config NEW_CONFIG
python skills/route-subagents/scripts/benchmark_router.py --config NEW_CONFIG doctor
```

`agents_dir` must be a project or user agent directory actually discovered by the
client. Do not use the plugin's bundled agent directory to assume support for
fields ignored on plugin agents. Names are immutable
`assay-<profile>-<configuration-fingerprint>.md`. Only requested combinations and
the configured advisor are generated, not a Cartesian product of all models.
Existing canonical templates keep their capability restrictions; canonical JSON
profiles still contain no model, effort or runtime state. Internal routing-advisor
and general-purpose templates are execution adapters, not new neutral personas.

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

Doctor/status reports configuration and support gaps, not fabricated discovery
or effective permissions. It deliberately leaves installation/discovery unverified
until there is real client evidence. Verify with one authorized bounded task in
the intended client/version before asserting native behavior or quota savings.

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
completed decision or a small `handoff`. A full approved choice, single eligible
pair or valid exact cache hit avoids an extra advisor invocation. The hook inserts
a short-lived, one-use receipt tied to the actual host session, tool and argument
hash; it is not a parameter for the model to manufacture.

For a handoff, invoke the returned native `input` unchanged. The launch gate
checks the prepared advisor attempt. `SubagentStart` binds that attempt to the
host's real child identity. Only this child can call `get_advisor_input` for that
decision and submit schema-validated JSON via `complete_routing`. Its allowlist
contains those operations and a sanitized native handback; delegation, arbitrary
MCP access and workspace tools are denied by the routing hook. No benchmark
snapshot or ranking is forwarded through the root prompt. The native handoff
prompt revision is v4, so older prompt answers cannot hit the current cache.

The advisor finishes with status only. Supported `PostToolUse` output rewriting
replaces only its text-content blocks while preserving the native output shape
and telemetry; native handback reports are sanitized too. This does not rewrite
host transcripts or provider telemetry. The primary reads `get_routing_decision`
after the host returns the advisor invocation; submission alone cannot authorize
workers or seed the shared semantic cache.

Then call `authorize_routing_launch(decision_id, packet_id)` and use the exact
returned Agent input. The gate binds the packet prompt, profile, model/effort
variant, current configuration, session, expiry and individual attempt. Altered
prompts, another packet's record, model overrides, expired records and reused
attempts are rejected. It returns no automatic permission grant: normal client
approval and permission checks still apply. Explicitly generated definitions and
foreground defaults avoid relying on per-call effort or implicit background mode.

Only the small unbound-start interval for the same definition is serialized,
because native start events do not identify the parent's tool call. Once bound,
workers run concurrently. Different effort variants have different immutable names.
An aborted launch without a host failure event may remain reserved until its
expiry; it must not be converted to a retry by a model-authored failure claim.

`retry_of` permits a fresh attempt only after the host observed the earlier
invocation fail and no other attempt is active. `resume_agent_id` continues only
the same observed idle worker, same definition and original packet, without
replaying completed writes or changing scope. An advisor cannot be resumed this
way. A new task, changed constraints, replacement or reviewer needs preparation;
continuation of an existing worker is not a new model-selection decision.

## Observations, failure and privacy boundaries

Requested settings, configured definition bytes and host observations are separate.
The documented hook effort value is an object with a `level`; Agent's structured
`resolvedModel` and `modelsUsed` provide model observations. An observed mismatch
invalidates advice and blocks further guarded work. Unknown model/effort remains
null; a self-reported `resolved_model` in the advisor JSON is not host evidence.
An early stop event does not skip the later Agent result check. Late discovery of
a mismatch cannot undo a tool action already performed by the native client.
Conflicting effort/subagent-model environment overrides are rejected, not changed.
Use confirmed runtime IDs: unresolved rolling aliases may not match observed IDs.

Abstention, bad output or observed advisor failure allows only the eligible
configured baseline. No baseline means no decision, not root-side selection.
Expiry or configuration/inventory change requires preparation again. Unsupported
fields, disabled hooks or a client that ignores output rewriting are real
compatibility limits; static configuration does not establish their effectiveness.

A bounded SQLite rendezvous under `state_dir` supports hooks and MCP processes
without a new service. Receipts expire after 30 seconds; private decision data
expires after at most ten minutes or earlier inventory/evidence expiry. Raw attempt
input is removed when the host observes start/return; decision execution prompts
remain only for the decision lifetime. Minimal observed attempt metadata remains
for up to 24 hours to support outcomes and same-worker continuation. SessionEnd
removes that session's records. Expired data is deleted on the next transaction,
not by a background scheduler; SQLite secure deletion is enabled. Use a private
local state directory and OS access controls, including appropriate Windows ACLs.

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

## Update, pruning and rollback

Re-run `claude-routes` after changing profiles or configured combinations. Generation
is idempotent; foreign files, modified owned files and linked/reparse ancestors
are refused. Superseded definitions remain recorded as retired, never selected.
`--prune` removes only unchanged owned inactive variants and retains variants
referenced by active runtime records. Creation, deletion and final manifest writes
have rollback for recoverable I/O errors; user-authored files are not overwritten.
Do not manually rename a managed definition or edit its fingerprinted file.

For a mode rollback, explicitly set `pipeline.mode` to `evidence-only` and reconnect
both host and MCP. For revision rollback restore the retained old config, old
registration/link vector and old revision together; use the old revision for its
own uninstall operation. Preserve user files and separately retained history.
Protocol-2 runtime records and v4 prompt answers cannot be reused as old live
permissions. Rehearse rollback in an isolated directory, not against running work.

Primary contracts (verified 2026-09-29):
[Claude hooks](https://code.claude.com/docs/en/hooks),
[Claude subagents](https://code.claude.com/docs/en/sub-agents), and
[per-call effort request](https://github.com/anthropics/claude-code/issues/77298).
