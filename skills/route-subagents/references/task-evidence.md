# Task evidence and expected full cost

This optional extension adds local observations to the existing advisor. It
does not assign workers, change model availability or call another model. The
objective is lower expected cost through acceptance at adequate quality,
including attempts, retries, verification and coordination. A cheap first
answer alone is not evidence of economy. Worker model names remain inventory
inputs; no historical model is mapped to a newer family member.

## Enable with a relevant public corpus

Add to a **v2** client configuration, retaining its other settings:

```json
"task_evidence": {
  "enabled": true,
  "mode": "lexical",
  "min_similarity": 0.15,
  "neighbors": 32,
  "minimum_observations": 3,
  "deadline_seconds": 2,
  "retain_descriptions": false
}
```

Absent configuration means disabled. Preserve the previous configuration and
revision before changing the file; keep the registered Python, cache and browser
arguments. Reconnect the server after editing configuration. With the extension
enabled, `auto_download` defaults to true: the first eligible MCP task-evidence
request starts public corpus preparation in the background if no index exists.
No model invocation or background collection of private tasks occurs.

To prepare it before routing, use the same Python, configuration and cache as MCP:

```sh
python skills/route-subagents/scripts/benchmark_router.py --config CONFIG --cache-dir CACHE task-setup
```

This command waits and reports `ready` (exit 0), or a specific unavailable state
(exit 2). It can prefetch before enabling the extension. CLI `context`, `prepare`
and `task-context` also prepare a missing corpus when enabled; unlike the persistent
MCP server, these short-lived commands wait for initial preparation.

The shipped source manifest pins LLMRouterBench revision `0e5af1b` and SHA-256
checksums for 13 LiveCodeBench model result files. It streams the upstream release
(approximately 1.28 GB), keeps selected fields locally, and installs 528 of 1055
tasks using the same deterministic query split as offline evaluation. The other
527 tasks are excluded from the working index. This is coding evidence, not
coverage for every task type or every current model. No dataset is redistributed
inside Assay. Unknown effort and unpriced USD remain unknown.

Preparation has its own 180-second process deadline and socket/size limits;
the local retrieval deadline remains separate. `acquisition` in routing evidence
and `routing_status` distinguishes `downloading`, `present`, `missing_offline`,
`missing`, and `failed`. `present` means a file exists; bounded retrieval validates
its checksum and schema before use. Routing continues while downloading and uses
the corpus on a subsequent request. Failure preserves existing routing and waits
five minutes before an automatic retry; `task-setup` explicitly retries sooner.
Concurrent clients share a lock, writes are atomic, and an existing imported corpus
is never replaced automatically. Reconnect/shutdown cancels an unfinished worker;
completed indexes survive reconnects and do not download again.

Set `auto_download: false` for manual-only provisioning. `--offline` never fetches
even with automatic provisioning enabled. Installation of skill links alone does
not download data; enabled routing or explicit setup does. Semantic model weights
are still a separate explicit installation.

Lexical search needs only the existing Python runtime. It uses Unicode words
and cosine similarity, not translation. The threshold and minimum sample count
are resource/coverage bounds, not calibrated probability or confidence levels.
A relevant public corpus is useful without local chain history: it shows which
historical models handled similar tasks and at what measured response cost.
Enable that advisory context with automatic preparation or explicit import. Local
history progressively adds current workflow cost estimates; it is not an
activation prerequisite. Enabling public context does not establish measured
subscription savings or justify transferring old scores to new models.

Rollback: set `task_evidence.enabled` to false and reconnect. Previous requests,
benchmark cache and history remain usable. Corpus removal, if needed, is limited
to the owned `task-evidence` subdirectory of the chosen cache, never the cache
root. There is no private embedding or query cache to clean up.

## Inputs and privacy

`prepare_routing` accepts these optional fields in addition to the existing
structured packets, inventory, constraints and advisor route:

```json
{
  "task_queries": {"fix-cache": "Repair invalidation across two asynchronous workers"},
  "cost_objectives": {
    "fix-cache": {"unit": "quota_units", "unit_basis": "attributed-window-v1", "overhead": null}
  }
}
```

Keys must identify existing packets. Descriptions are at most 4096 UTF-8 bytes
each; form them from the existing task, without another LLM call. Never send
secrets or raw tool output. The evidence-only `get_routing_context` accepts
`task_query` and `features` for its single context packet. A request without a
query can still use exact structured local-history features.

`overhead` is the **incremental** cost of adding retrieval/advice compared with
the supplied baseline, in the specified unit and basis. Do not charge already
included chain routing costs twice. Null means unmeasured; it cannot establish
net savings. Only `api_usd` and genuinely attributable `quota_units` support the
paired economy comparison. An account-wide quota change during concurrent work
is not a per-packet observation. Tokens, latency and dollars stay separate axes.

Raw query text is used in a bounded local subprocess via stdin, without storing
or echoing it. It is absent from snapshots, handoffs, portable envelopes and
Jev input. Native clients may retain **tool arguments in their own logs**;
Assay does not control those logs. Local cost summaries reach the native advisor;
Jev's existing external projection removes local-history and comparison blocks.
Public structured evidence still requires Jev's existing consent. Corpus text
is untrusted data and never enters the advisor prompt.

## Import measured public answers

For another corpus, import explicit local files. The import command itself never
downloads data; automatic preparation above only fills an absent working index.

```sh
python skills/route-subagents/scripts/benchmark_router.py --config CONFIG --cache-dir CACHE task-import --file CORPUS.json
python skills/route-subagents/scripts/benchmark_router.py --config CONFIG --cache-dir CACHE task-import --file RELEASE_SLICE --manifest MANIFEST.json
```

`RELEASE_SLICE` is a directory or tar archive of selected LLMRouterBench result
files. The adapter reads archives without extracting them and rejects links,
special files, traversal and conflicting task/model repeats. The selected slice
is bounded to 256 MiB of input, 32 MiB per file; the normalized corpus is limited
to 15000 tasks and 32 MiB. CLI normalized JSON uses the existing 8 MiB input
limit. Select a small relevant slice; do not route against a full raw release.

Example manifest (replace the example source, revision and harness with verified
ones; do not infer effort or pricing from model names):

```json
{
  "source": {
    "id": "llmrouterbench", "revision": "verified-revision",
    "url": "https://huggingface.co/datasets/NPULH/LLMRouterBench",
    "license": "unspecified", "use": "local-only"
  },
  "datasets": {
    "livecodebench": {
      "task_types": ["implementation"], "metric": "published-score",
      "harness": "unknown", "efforts": {}, "priced_models": []
    }
  }
}
```

`priced_models` is an explicit declaration that a result's `cost` is a known
API price. Some release files contain zero for **unpriced** local inference;
without this declaration USD is null, not free. Record the dated pricing basis
in the source revision. A license value of `unspecified` documents uncertainty,
not permission to redistribute. Check the source dataset and result licenses
before using a slice; keep uncertain material local.

Normalized corpus schema version 1:

```json
{
  "schema_version": 1,
  "source": {
    "id": "example", "revision": "r1", "url": "https://example.org/data",
    "license": "CC0-1.0", "use": "local-only"
  },
  "records": [{
    "task_id": "case-1", "task_types": ["implementation"], "features": {},
    "query": "Repair cache invalidation",
    "observations": [{
      "model": "observed-model-id", "effort": null,
      "metric": "pass-at-1", "comparison_basis": "harness-revision",
      "score": 1, "cost_scope": "response", "complete": true,
      "costs": {"input_tokens": 100, "output_tokens": 40, "api_usd": null},
      "unit_basis": {}
    }]
  }]
}
```

Scores retain their named source metric on the 0..1 scale; incompatible scales
require explicit normalization before import. Missing scores and costs are
null. Atomic indexed storage includes a content fingerprint. Identical imports
are idempotent; corruption returns unavailable rather than an empty success.

Historical pool coverage/all-pass/all-fail patterns and per-model observations
are separate from current candidate estimates. `public_coverage` includes a
compact table (`columns`, `rows`, `cost_units`) of sample counts, known scores,
mean source scores, mean observed costs and missing/partial coverage. At most
16 historical routes per cohort are included in stable identity order, with
`omitted_routes` reported explicitly. Source metrics, scope and unit basis stay
separate. These rows remain visible when no historical model matches inventory.
Current `public` and `local` estimates include observed groups only;
`unknown_current_candidates` declares missing candidate IDs for each layer, or
`"all"` when every eligible current candidate is unmeasured. This avoids spending
the shared context budget repeating empty groups for a large model × effort pool.
Unknown effort cannot match a current model × effort pair.
Public response cost cannot prove the cost of an agent's complete work chain.

For an English code corpus in lexical mode, supply a concise English description
of the already known subtask. The coordinator can phrase it directly; no extra
translation model call is needed. A Russian-only lexical query is not translated
by the service. Similarities and historical outcomes are context for the existing
advisor, never an automatic assignment or fixed mapping to a newer model.

## Record complete chains through the existing history

Use `record_routing_outcome`, retaining its normal observed/requested routes,
execution reference and acceptance evidence. An additional terminal field:

```json
"cost_observation": {
  "schema_version": 1, "complete": true,
  "initial_route": {"model": "observed-model-id", "effort": "low"},
  "comparison_basis": "client-tools-context-oracle-v1",
  "unit_basis": {"api_usd": "dated-tariff-v1"},
  "events": [
    {"event_id": "routing-1", "category": "routing", "resources": {"api_usd": 0.01}},
    {"event_id": "attempt-1", "category": "worker", "resources": {"api_usd": 0.02}},
    {"event_id": "retry-1", "category": "worker", "resources": {"api_usd": 0.08}},
    {"event_id": "verify-1", "category": "verification", "resources": {"api_usd": 0.03}},
    {"event_id": "integrate-1", "category": "coordination", "resources": {"api_usd": 0.04}}
  ]
}
```

This example totals 0.18, not 0.02 or 0.08. One immutable terminal receipt covers
the entire packet chain. Retries and escalations retain separate unique events;
`initial_route` identifies the route whose full downstream cost is estimated.
Do not fabricate observed settings from the request. Complete chains require
all four categories, including explicit **observed** zeros. Missing resources
in any event make that unit's total unknown; incomplete chains remain partial.
Shared coordination events must be attributed once, with any allocation method
in the comparison basis. Do not copy a shared event into multiple receipts or
sum packet estimates as a measured plan total. This version exposes per-packet
estimates; a plan's shared-cost allocation remains caller-owned and may be unknown.

Resources: `input_tokens`, `cached_input_tokens`, `output_tokens`,
`reasoning_output_tokens`, `api_usd`, `quota_units`, `duration_seconds`.
Cached input is a subset of input; reasoning is a subset of output. Event count
is not token or quota count. No `cost / success_probability` retry model is used.

History uses the existing retention and metadata/full/off modes. Structured
task features are retained with decisions containing this extension. Existing
usage import still reads only explicitly selected logs; it does not invent
missing acceptance, whole-chain attribution or alternative outcomes. Old
metadata records without task features are not silently relabeled as matches.

Estimates group exact model/effort, client, features, comparison basis, metric,
scope and unit basis. They report empirical mean, range, p90, n, partial chains
and unknown quality. Ranges are not confidence intervals; historical assignment
is observational and may be selection-biased. Encode material context/cache/tool
and acceptance conditions in features and comparison basis; unknown conditions
weaken applicability. Failed chains are included, terminal does not mean accepted.

An optional `comparison_task` on cost observations identifies the same previously
measured task across routes. Only genuinely paired complete chain observations
can yield a net-benefit comparison; do not invent pairs between merely similar
jobs. Duplicate pairs abstain. All-fail samples cannot justify cheaper routing.
Unknown alternatives remain unknown, not failures. These observations do not
authorize new duplicate executions to fill the matrix.

Separate consent `retain_descriptions: true` permits a minimal `task_description`
on a terminal receipt. Full telemetry alone is not consent. Expired decisions
and outcomes never participate, even before physical retention cleanup. On
opt-out set the flag false, then remove retained descriptions explicitly:

```sh
python skills/route-subagents/scripts/benchmark_router.py --config CONFIG --cache-dir CACHE task-purge-descriptions
```

This leaves structured receipts and the public corpus intact. There is no
persistent derived private index. Existing history retention owns receipt removal.

## Bounded diagnostics and interpretation

```sh
python skills/route-subagents/scripts/benchmark_router.py --config CONFIG --cache-dir CACHE task-context --request REQUEST.json
python skills/route-subagents/scripts/benchmark_router.py --config CONFIG --cache-dir CACHE task-evaluate --file HELD_OUT_CORPUS.json --unit api_usd --overhead 0.01
python skills/route-subagents/scripts/benchmark_router.py --config CONFIG --cache-dir CACHE task-forecast --request PACKETS.json --unit quota_units
```

`task-context` takes `packets`, `available`, optional `task_queries` and
`cost_objectives`; after initial corpus preparation it performs only local retrieval,
without benchmark-source refresh or model calls. `task-forecast`
takes only `packets`. It evaluates cost prediction against strictly later retained
chains of the same cohort, reporting coverage, absolute error and costly
underestimates. No alternative execution means no counterfactual savings estimate.

`task-evaluate` deduplicates normalized queries before a deterministic train/test
split, chooses a fixed baseline on training observations, and looks up existing
test outcomes for a lexical cost/quality selector. It reports abstention, quality
losses and net savings only when overhead is supplied. It never updates or
installs the supplied corpus. Keep this qualification corpus separate from the
working index. A small split is diagnostic, not statistical proof, and does not
evaluate future native/Jev responses. Do not tune thresholds on its test results.

Returned `task_similarity_evidence` has schema version 1, retrieval/settings and
corpus identities, separate public/local groups, and explicit status. Maximum
32 neighbors, 3 hashed example references and 6 KiB for **all** packets together,
within the existing snapshot budget. Over-budget evidence is explicitly omitted.
No-match, unavailable and insufficient-coverage preserve the original workflow.
Explicit routes and a sole candidate skip corpus work; a fully covered
nonpositive cost comparison can skip advice and preserve the supplied baseline.
Incomplete coverage cannot suppress consideration of unknown alternatives.

## Optional semantic adapter

The optional CPU adapter uses `scripts/requirements-retrieval.txt` in an isolated
environment, plus explicitly installed local weights. It never downloads weights
at request time or trusts remote model code. Configure `mode: "semantic"`,
`encoder_path` and a pinned `encoder_revision`. One candidate for qualification is
`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`, revision
`e8f8c211226b894fcb81acc59f3b34ba3efd5f42` (Apache-2.0; 384 dimensions).
See the [upstream model card](https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2).

This adapter is experimental: at most 2048 compatible texts per call, cold CPU
load inside the request's cancellable deadline, and the encoder's own token
truncation (128 for that candidate). Keep a revision directory immutable and
change the configured revision when changing weights. There is no persistent
encoder service or vector cache. It can exceed the default two-second budget;
that yields unavailable and the existing workflow. Install size, cold latency,
RAM and RU/EN usefulness must be measured locally before enabling it. Semantic
quality and warm-service performance are not claimed by lexical/core tests.
