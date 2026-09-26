# Routing advice over the existing evidence service

The advisor ranks current client model × effort pairs for structured packets.
Assay builds its input from the existing benchmark comparisons and applies a
deterministic policy to its answer. The native client still owns permissions,
launch, interruption and quota. Neither MCP nor CLI launches an agent, changes
the primary model or enforces a per-child token allowance.

The optional [task evidence extension](task-evidence.md) adds local query retrieval
and historical full-chain cost/quality estimates. It is disabled by default;
missing evidence preserves this workflow and never implies subscription savings.

## Enable for one client

Config v1 remains evidence-only. Create a separate v2 file, preserving the old
bytes and the current MCP command, environment and link targets for rollback:

```sh
python skills/route-subagents/scripts/benchmark_router.py migrate-config --source OLD_CONFIG --output NEW_CONFIG --enable-advisor
```

The output must not already exist. This command preserves client, preferences
and dated inventory, and changes no registration or launch argument. Point the
existing server registration at the new file and reconnect the client, retaining
its Python environment, cache, browser settings and timeout. A minimal v2 file:

```json
{
  "schema_version": 2,
  "client": "codex",
  "preferences": {},
  "advisor": {"enabled": true, "backend": "native-economy"},
  "policy": {"fallback": "caller-baseline", "unknown_evidence": "warn"},
  "telemetry": {"mode": "metadata", "retention_days": 30}
}
```

Use the actual host label. No model name or effort is stored in a neutral
profile. `native-economy` means an economical route in that client's current
catalog; it is not a model alias or local inference. Its computation uses the
native provider and consumes that account's quota.

`routing_status` is read-only: it reports backend, enablement, pending count,
optional SDK presence and retention. A missing tool in an already running
client may require reconnection. Use the same configured CLI as a fallback;
do not create another server or silently switch providers.

## Prepare and finish native advice

Call `prepare_routing` once for the plan, up to eight packets. Supply the actual
inventory on the first call as with `get_routing_context`. Resolve the advisor's
own pair once, in this order: explicit user choice; an actual client economy-role
binding; otherwise a short choice from available cost and fitness evidence.
There is no invented cheapest-model API or recursive advisor call.

Illustrative request; replace model/effort values with confirmed runtime values:

```json
{
  "packets": [{
    "packet_id": "parser-change",
    "task_types": ["implementation", "tests"],
    "features": {
      "phase": {"value": "implementation", "provenance": "caller"},
      "ambiguity": {"value": "low", "provenance": "caller"},
      "verification": {"value": "deterministic-tests", "provenance": "observed"}
    }
  }],
  "available": [{"model": "runtime-model", "efforts": ["low", "high"]}],
  "advisor_route": {
    "model": "runtime-model",
    "effort": "low",
    "selection_basis": {"source": "evidence", "reason_code": "bounded_ranking", "evidence_refs": ["cohort-id"]}
  }
}
```

Features are bounded scalars or identifier lists, each with `caller`, `observed`
or `unknown` provenance. `features: {}` is valid; missing facts remain unknown.
Do not send task prose, code, paths, credentials or raw tool outputs. Optional
packet fields are `explicit` (model and/or effort), `baseline` (both),
`requirements` and `capabilities`. A requirement can declare:

```json
{
  "requirements": {"delegation_allowed": true, "capabilities": ["shell"], "constraints": {"max_cost_usd": 2}},
  "capabilities": [{"model": "runtime-model", "effort": "low", "route_expressible": true, "capabilities": {"shell": true}}]
}
```

These declarations must reflect the current client. Capability values are
`true`, `false` or `null`; unknown evidence is not proof of capability. Optional
benchmark constraints retain their cohort and units. A measured violation is
excluded with a reason. Unknown measurements warn by default; use
`policy.strict_unknown_constraints` to fail closed for named constraints.
`policy.unknown_evidence="strict"` applies strict handling to all declared numeric
constraints. A required capability always needs a positive declaration.
The original benchmark response is unchanged by advisor filtering.

An explicit full choice or a single eligible pair finishes without advisor
inference. Otherwise `awaiting_native_advice` returns `decision_id`, expiry and
`handoff`. Launch exactly that bounded handoff through the primary's native
subagent mechanism. The prompt instructs the advisor to rank only supplied data,
use no tools and create no agents; that instruction is not an enforced sandbox.
Use actual supported restrictions when available. Codex uses a self-contained
packet with `fork_turns="none"`; other clients use their own supported controls.

Submit its JSON object as `complete_routing(decision_id, advisor_result)`. Each
non-abstained packet must rank every eligible candidate ID exactly once. Ties
are explicit groups. Native probabilities and confidence remain null. The
server checks snapshot identity, exact route, inventory, policy, expiry and
result bounds; it never repairs a partial ranking by guessing missing entries.

Use the returned selection for the real worker. Reconsider only a concrete
missed constraint, incorrect input or changed goal, then prepare a new snapshot.
Record that reason rather than paying for a second full ranking debate.

## Optional hosted Jev adapter

The [official SDK](https://github.com/typesafe-ai/typesafe-sdk-python) is MIT
licensed. This integration pins `typesafe-sdk==0.6.0` in
`scripts/requirements-advisors.txt`. Install it only in the same isolated Python
environment as the server; native-only operation does not import it:

```sh
python -m pip install -r skills/route-subagents/scripts/requirements-advisors.txt
```

Select these advisor settings explicitly in the local v2 config:

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

At most 16 pending decisions live in a connection. They expire after ten
minutes or the earlier inventory/evidence freshness deadline. `busy` preserves
existing packets. Restarted or late native replies cannot authorize a launch;
expiry itself does not stop a running cloud advisor. Identical completion is
idempotent and conflicting completion is rejected.

Abstention, provider failure or missing bootstrap yields the eligible caller
baseline, if supplied; otherwise `needs_caller_selection`. Changed inventory,
policy or expired evidence requires preparation again. A selected route never
proves the actual launch. The exact in-memory decision cache includes semantic
features, candidate set, backend/model/effort, prompt/schema/policy/privacy
versions and evidence state. It has no similar-task search. Cache hits do not
prove model quality or current availability of an execution slot.

## CLI, history and rollback

All commands share the service used by MCP. Global flags precede subcommands:

```sh
python skills/route-subagents/scripts/benchmark_router.py --config LOCAL_CONFIG prepare --request REQUEST.json
python skills/route-subagents/scripts/benchmark_router.py --config LOCAL_CONFIG complete --request -
python skills/route-subagents/scripts/benchmark_router.py --config LOCAL_CONFIG record --request RECEIPT.json
python skills/route-subagents/scripts/benchmark_router.py history-import --file EXPLICIT_LOG.jsonl
python skills/route-subagents/scripts/benchmark_router.py replay --record RETAINED_RECORD.json
```

CLI `prepare` includes a portable `envelope`. For completion send an object with
`decision_id`, `advisor_result` and that envelope. Its checksum detects mismatch;
it is not authentication or permission. MCP keeps the prepared state in memory
and needs only the ID. CLI `record` accepts `decision_id` and `execution`; MCP
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

For quick rollback set `advisor.enabled=false` and use existing evidence tools.
For full rollback restore the retained v1 config, registration/link vector and
prior Assay revision. Test the old entrypoint against the saved config offline;
merely having a backup is not a rollback receipt. Preserve benchmark caches and
the separate history namespace. Static/fake-transport tests establish contracts;
provider/native effectiveness and quota savings require ordinary work receipts,
not a mandatory paid comparison campaign.

## Cost of a completed task

Compare routing policies on representative completed tasks, not API price alone.
Count packet preparation, advisor calls, worker attempts, retries, verification
and integration; retain unsuccessful attempts and user corrections. Keep actual
measurements separate from estimates and distinguish API billing from subscription
quota accounting. Public benchmarks can inform a prior, not establish this cost.

Use the existing explicit choice when the candidate is already justified; do not
add a paid advisor call merely to certify the same answer. Compare an advisor
against that simple baseline before claiming savings. A small pilot can reject
a wasteful policy without establishing universal rankings or model superiority.
