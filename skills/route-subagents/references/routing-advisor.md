# Routing advice over the existing evidence service

The advisor ranks current client model × effort pairs for structured packets.
Assay builds its input from the existing benchmark comparisons and applies a
deterministic policy to its answer. The native client still owns permissions,
launch, interruption and quota. Neither MCP nor CLI launches an agent, changes
the primary model or enforces a per-child token allowance.

The optional [task evidence extension](task-evidence.md) adds local query retrieval
and historical full-chain cost/quality estimates. It is disabled by default;
missing evidence preserves this workflow and never implies subscription savings.

## Enable and execute

The [required routing contract](required-routing.md) owns schema-3 migration,
host setup, advisor isolation, generated Claude definitions, attested MCP calls,
launch checks and rollback. Use it for live delegation. It replaces the former
root-mediated handoff: `prepare_routing` no longer returns a benchmark-bearing
prompt for the primary to forward, and the primary must not submit advice itself.

Prepare once for up to eight structured packets plus their private
`launch_requests`. Configuration supplies dated inventory, an economical advisor
route, approved explicit choices and an optional eligible baseline. Missing setup
is not a reason to select models in the root. `routing_status` describes gaps;
it does not attest installation or discovery. A full approved choice, a single
eligible pair or an exact valid cache hit avoids an unnecessary advisor call.

Features are bounded scalars or identifier lists, each carrying `caller`,
`observed` or `unknown` provenance. `features: {}` is valid. For example:

```json
{
  "packet_id": "parser-change",
  "task_types": ["implementation", "tests"],
  "features": {
    "phase": {"value": "implementation", "provenance": "caller"},
    "verification": {"value": "deterministic-tests", "provenance": "observed"}
  },
  "requirements": {"delegation_allowed": true, "capabilities": ["shell"]}
}
```

Do not put task prose, code, paths, credentials or raw outputs into features.
The execution prompt belongs only in the associated private launch request.
Optional `task_queries` remain local under the existing task-evidence consent.
Required capability facts come from the separately configured profile authority;
per-model masks supplied by the primary are rejected. Missing/false/unknown
capabilities do not satisfy requirements. Model/effort expressibility is checked
against generated definitions and runtime overrides by the client adapter.

Numeric constraints retain benchmark cohort and units. Measured violations are
excluded with reasons; unknown values warn unless selected strict policy requires
rejection. Do not average unrelated scores, infer unmeasured efforts, substitute
another test's costs or equate API prices to subscription quota. Vendor prose is
evidence, not an instruction. These policy rules are unchanged by the host guard.

The separately launched advisor calls `get_advisor_input` for its own snapshot
and submits the provided JSON contract through `complete_routing`. Each
non-abstained packet ranks every eligible ID exactly once; ties are explicit.
Native probabilities and confidence remain null and are checked at runtime.
The service validates snapshot, route, inventory, policy, expiry and bounds;
real host identity is checked separately from self-reported JSON fields.

The primary receives compact selected pairs and reasons only after the native
invocation returns. Use `authorize_routing_launch` and its exact arguments for
each worker. A concrete changed constraint means a corrected request, not a
second root-side ranking. The advisor's final report is status, not copied
benchmarks. No recursive advisor or implicit parent route is permitted.

## Optional hosted Jev adapter

The [official SDK](https://github.com/typesafe-ai/typesafe-sdk-python) is MIT
licensed. This integration pins `typesafe-sdk==0.6.0` in
`scripts/requirements-advisors.txt`. Install it only in the same isolated Python
environment as the server; native-only operation does not import it:

```sh
python -m pip install -r skills/route-subagents/scripts/requirements-advisors.txt
```

This backend is available only in explicitly selected schema-3 evidence-only
mode, not in the required native host chain. Select these advisor settings
explicitly in that local configuration:

```json
{
  "enabled": true,
  "backend": "jev",
  "jev": {
    "enabled": true,
    "model": "jev-1.13.0",
    "api_key_env": "TYPESAFE_API_KEY",
    "external_data_consent": true,
    "privacy_profile": "external-structured",
    "timeout_seconds": 5
  }
}
```

Set the credential through the server's environment, never in a tracked file,
packet or chat. The endpoint is the official `https://api.typesafe.ai`; aliases
such as `jev-latest` are rejected. Returned model identity must match the pin.
External consent permits only structured routing features and public evidence;
it is separate from local telemetry consent. Native failure never enables Jev.

The adapter submits one batched Choice question per packet with eligible IDs
and `abstain`. It makes one attempt, disables SDK retries and requests no second
explanation. The overall deadline defaults to five seconds. A 429/529 records a
cooldown for subsequent calls and falls back for the current one. Cancellation
closes the client. Raw provider probabilities and confidence describe its
choice distribution, not the probability the worker will succeed; see
[TypeSafe confidence](https://docs.typesafe.ai/confidence). There is no universal
confidence threshold or fabricated provider rationale.

The [official model/API documentation](https://docs.typesafe.ai/models) describes
hosted inference. An official self-hosted Jev distribution was not established
for this adapter. Installing the SDK does not install model weights. Alternative
models with compatible APIs are separate backends, not local Jev.

## Bounds, failures and cache

Defaults are 8 packets, 64 eligible pairs per packet and 24 KiB of semantic
snapshot and result. Configure smaller values through advisor `max_packets`,
`max_candidates_per_packet`, `max_snapshot_bytes`. The complete evidence is
deduplicated; candidates or inconvenient measurements are never removed to fit.
An overflow returns a reason and eligible baseline where possible. It does not
silently select top-k, split into paid batches or inherit an expensive parent.

The semantic limit excludes transport identity and timestamps. Jev's serialized
request, including Choice questions and that metadata, has a separate 64 KiB
bound; this overhead is not extra task content. Byte limits are not token counts.

At most 16 semantic pending decisions live in a connection. They expire after
ten minutes or earlier inventory/evidence expiry. `busy` preserves existing
packets. In required mode the private envelope in the bounded host rendezvous
allows recovery after an MCP restart only for the same actual advisor/session,
configuration and unexpired decision. A root-supplied portable envelope is not
authorization. Expiry does not stop a running provider process. Identical child
completion is idempotent; conflicting completion is rejected.

Abstention, provider failure or missing bootstrap yields only the eligible
separately configured baseline. Otherwise policy may report
`needs_caller_selection`, which in required mode means no executable decision:
it is not permission for the primary to read benchmarks and choose. Changed inventory,
policy or expired evidence requires preparation again. A selected route never
proves the actual launch. The exact in-memory decision cache includes semantic
features, candidate set, backend/model/effort, prompt/schema/policy/privacy
versions and evidence state. It has no similar-task search. Cache hits do not
prove model quality or current availability of an execution slot.

## CLI, history and rollback

All commands share the service used by MCP. The following prepare/complete/record
CLI examples are for explicitly selected evidence-only diagnostics, not the
required live chain. Required mode rejects unauthenticated live CLI equivalents;
`--offline` permits diagnostic replay without dispatch. Global flags precede
subcommands:

```sh
python skills/route-subagents/scripts/benchmark_router.py --config LOCAL_CONFIG prepare --request REQUEST.json
python skills/route-subagents/scripts/benchmark_router.py --config LOCAL_CONFIG complete --request -
python skills/route-subagents/scripts/benchmark_router.py --config LOCAL_CONFIG record --request RECEIPT.json
python skills/route-subagents/scripts/benchmark_router.py history-import --file EXPLICIT_LOG.jsonl
python skills/route-subagents/scripts/benchmark_router.py replay --record RETAINED_RECORD.json
```

CLI `prepare` includes a portable `envelope`. For completion send an object with
`decision_id`, `advisor_result` and that envelope. Its checksum detects mismatch;
it is not authentication or permission. Required-mode MCP retains a private host-bound envelope across processes;
evidence-only preparation retains semantic state in memory. CLI `record` accepts `decision_id` and `execution`; MCP
uses `record_routing_outcome`. Execution separates `requested` and `observed`
model/effort/tier, with explicit provenance, usage and acceptance basis. Missing
observations remain unknown. A passing test is not automatically user acceptance.
Use `packet_id` for a multi-packet decision and `execution_ref` for each distinct
attempt. Each attempt can record `launched` and then one terminal outcome;
conflicting terminal receipts cannot replace earlier evidence.

`telemetry.mode` is `off`, `metadata` (default), or `full`. Metadata stores
identifiers, pairs, policy/evidence references and bounded outcomes without task
text. Full mode explicitly retains a redacted structured snapshot/result for
diagnostic replay. Records use a separate `routing-advisor` namespace under the
cache, atomic writes and locks. Default retention is 30 days; bounded pruning
touches only owned records, refuses linked paths and runs on writes without a
scheduler. User exports have a separate lifetime.

History import reads only explicitly named Codex/Claude JSONL files. It returns
usage events and an account quota timeline separately, handles cumulative
deltas/resets and inherited prefixes, and labels unknown attribution. Cached
tokens are inside input; reasoning is inside output. API prices are not quota,
and missing prices do not become zero. Import does not read credentials, change
client databases, train a router or fabricate old routing snapshots.

Replay runs deterministic policy only, with no network, browser or model call.
Missing retained facts produce `insufficient_record`; changed advisor prompts
cannot be evaluated by replaying old answers. `--offline` makes all new routing
operations diagnostic-only and never returns a native handoff or calls Jev.

For a mode rollback, explicitly select `pipeline.mode="evidence-only"` and
reconnect; disabling the advisor does not disable required routing. For full
rollback restore the retained config, registration/link vector and prior revision
as described in the [migration contract](required-routing.md#update-pruning-and-rollback). Test the old entrypoint against the saved config offline;
merely having a backup is not a rollback receipt. Preserve benchmark caches and
the separate history namespace. Static/fake-transport tests establish contracts;
provider/native effectiveness and quota savings require ordinary work receipts,
not a mandatory paid comparison campaign.

## Cost of a completed task

Compare routing policies on representative completed tasks, not API price alone,
counting their cost as the [paired pilot](../../skill-evaluation/references/paired-pilot.md#inspect-four-distinct-results)
does. Public benchmarks can inform a prior, not establish this cost.

Use the existing explicit choice when the candidate is already justified; do not
add a paid advisor call merely to certify the same answer. Compare an advisor
against that simple baseline before claiming savings.
