# Retrospective routing telemetry

A useful retrospective follows the task, selected route, native execution attempts
and acceptance criteria. Local history keeps these facts separately so missing
execution evidence does not become a successful model selection.

## Enable useful local history

In the existing routing configuration, choose the history lifetime and dataset:

```json
{
  "telemetry": {"mode": "full", "retention_days": 180, "dataset": "production"},
  "task_evidence": {"retain_descriptions": true}
}
```

These are sections of a complete configuration, not a replacement configuration.
Default metadata history retains task types, structured features, selected pairs,
policy version, hashes and references. `retain_descriptions` separately permits
the validated `task_spec`, including its goal, criteria and verification. Full
mode also retains the redacted decision snapshot for diagnostic replay. Off
disables persistence. Production, smoke, test and unspecified are explicit
dataset labels; old history remains unspecified.

For automatic native capture, create `routing-telemetry.json` in this plugin's
native plugin-data directory, or set `ASSAY_ROUTING_TELEMETRY_CONFIG` to an
absolute binding file:

```json
{"config": "/absolute/routing-config.json", "cache_dir": "/absolute/benchmark-evidence"}
```

Use the same client configuration and cache as its MCP registration. Paths are
installation-specific local configuration. The binding is opt-in and changes no
model settings or routing mode. For a Claude evidence-only configuration it also
names the configuration whose launches the hook checks: a launch without both a
model and an effort is refused, as [Claude Code mechanics](claude-code-routing.md#evidence-only-launch-check)
describes. Unless telemetry is `off`, every Claude Agent launch, linked or not,
also records what its alias and effort ran as. Reconnect the client after changing an installed hook
manifest or MCP implementation. Hooks doctor reports `routing_telemetry_bound`;
this is configuration evidence, not a successful run.

## Link the actual worker

In evidence-only mode, preserve `telemetry_links[packet_id]` as a separate line
in the worker prompt or message. It looks like `[assay-routing:decision-id/packet-id]`.
The hook associates that explicit link with the native session and tool-use ID,
then with the returned worker ID. Each launch has its own attempt reference.
The pending launch identity expires after one day or the decision's expiry,
whichever comes first; ordinary long foreground calls remain attributable.
The launch prompt and outputs are not copied to history. An unrelated or unbound
worker transcript is never opened. Required routing can use its existing
host-bound attempt records directly.

At SubagentStop, the hook reads only the native-provided worker transcript, with
a 16 MiB limit. It imports identity, route evidence and usage, retaining a content
hash and provenance. It does not follow ancestor transcript paths or save the
transcript path in history, permissions, code or messages. Claude response models and Codex
`thread_settings_applied` are different evidence: applied host settings do not
prove the provider's resolved model. A missing model stays unknown. Partial
imports leave aggregate usage unknown. Hook failures preserve the existing
permission result and report a telemetry diagnostic.
Native stop effort and returned `resolvedModel`, when present, are retained as
host settings with their event provenance. Comparisons use only observed fields;
effort alone does not imply that a model was observed.
If the same native worker is reused across attempts, its cumulative transcript
has no verified per-call boundary. Request models and usage for the later attempt
stay unknown with `native_identity_reused_across_attempts`; native return timing,
aggregate usage and host settings remain available. Earlier attempts are preserved.

When a synchronous worker stops before the launch tool returns its worker ID,
the hook gives the stop path in its private rendezvous database a ten-minute
expiry; the next transaction removes expired entries. It opens the path only after the exact returned identity matches,
then removes the pending entry. This temporary path is not retained in history.

Without a launch link, record an exact `execution_ref` and `runtime` through
`record_routing_outcome`. Runtime contains `client`, `session_id` and the worker's
`thread_id` or `agent_id`. Supplying an absolute worker `transcript_path` imports
its evidence locally. Existing terminal receipts stay immutable; imported
observations and later assessments are separate records with the decision's
expiry. Repeated imports are deduplicated by native event identity.

For Codex, use the UUID returned by `spawn_agent` as `runtime.thread_id` and the
observed parent session as `runtime.session_id`. For Claude, use the Agent
receipt's `agentId` as `runtime.agent_id` and the native parent session ID.
Do not use a task name, role path or guessed UUID. If no native ID
is available, record the lifecycle receipt without runtime and keep the gap
visible; that receipt cannot bind a transcript. A linked launch whose output
has no worker identity reports a capture diagnostic instead of silently losing
the link. Codex JSON-string and object spawn receipts are supported.

The importer reads Codex `token_usage_record.payload.response_id` as a unique
request identity. A legacy `token_count` after an observed response is a counter
notification, not a second request; reset counters can have a different
baseline. A legacy notification reporting unmatched nonzero usage leaves a
partial import. Legacy-only cumulative/reset logs remain supported. Claude
message IDs identify requests across repeated chunk UUIDs; result aggregates
never add a second copy of directly observed assistant usage.

## Assess results and read the report

Completion is a lifecycle fact. For acceptance, supply `assessment` to
`record_routing_outcome`, or use `telemetry-assess`. Each assessment names the
exact decision, packet, execution reference, a new assessment ID, source
`user` or `verification`, and criterion results:

```json
{
  "decision_id": "decision-id", "packet_id": "parser", "execution_ref": "attempt-id",
  "assessment_id": "review-1", "source": "verification",
  "criteria": [{"id": "roundtrip", "status": "pass", "evidence_refs": ["roundtrip-check"]}]
}
```

Criterion IDs come from the retained task specification. Acceptance requires all
criteria to pass with evidence references. A referenced failure rejects the
attempt; incomplete or unreferenced results remain unknown. References describe
provenance; the store does not independently verify their contents. A corrected
review uses a new assessment ID and preserves the previous review.

```text
python skills/route-subagents/scripts/benchmark_router.py --config CONFIG --cache-dir CACHE telemetry-report --dataset production
python skills/route-subagents/scripts/benchmark_router.py --config CONFIG --cache-dir CACHE telemetry-assess --request ASSESSMENT.json
python skills/route-subagents/scripts/benchmark_router.py --config CONFIG --cache-dir CACHE telemetry-observe --request OBSERVATION.json
```

`OBSERVATION.json` names `decision_id`, `packet_id`, `execution_ref`, `runtime`
and an absolute `transcript_path`; an explicit import requires a previously bound
receipt with that exact identity. These operations make no model or network call.
Capture the report's JSON output in a private export when it needs to outlive
history retention.

Use `--since` (inclusive) and `--until` (exclusive), with ISO 8601 timestamps,
to select decisions in a time window. All retained attempts of those decisions
remain linked. Narrow the window when an export exceeds the 8192-record bound.

The report includes task context, selection and reasons, attempts, observations,
reviews and dataset groups. Coverage denominators distinguish retained context,
executed attempts, applied settings, provider models and evaluated acceptance.
First-attempt acceptance keeps an initial failure visible after a successful
retry. Route mismatch is evaluated only where comparable execution evidence
exists. Unknown quality has a null rate, never zero or 100 percent. Evaluated
attempts may be a selected sample; their rate is not a causal accuracy estimate.
Worker tokens are not whole-chain cost, and unexecuted alternative routes supply
no counterfactual quality or proof of optimality.
Native completed Agent returns can also provide duration and final-request worker
usage. `worker_return_usage` stays separate from deduplicated request usage;
the report never adds these overlapping observations together or treats that
return's usage as the whole run.

History expires with its configured retention and is pruned on owned writes.
Reports exclude expired records even before pruning. `task-purge-descriptions`
removes optional task text and full diagnostic snapshots from owned history;
separate exported reports have their own lifetime.
