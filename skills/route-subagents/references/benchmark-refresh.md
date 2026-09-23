# New models, matching gaps and preferred data sources

Read when a newly available model is missing from routing evidence, when
publisher names differ from native IDs, or when maintaining a source adapter.
The [benchmark service](benchmark-routing.md) remains the owner of acquisition,
cache and comparable cohorts; this adds no service or model-discovery daemon.

## Exact publisher correspondences

The CursorBench adapter retains the publisher's `model` and adds a reversible
`model_identity` annotation. `scripts/route_evidence/model_names.py` owns the
reviewed correspondences: Opus 5.5, Opus 5, Fable 5.1, Fable 5 and Sonnet 5 to
their exact `claude-*` identifiers. The rule records its source URL. Cursor's
[Opus 5.5](https://cursor.com/docs/models/claude-opus-5-5),
[Opus 5](https://cursor.com/docs/models/claude-opus-5),
[Fable 5.1](https://cursor.com/docs/models/claude-fable-5-1),
[Fable 5](https://cursor.com/docs/models/claude-fable-5), and
[Sonnet 5](https://cursor.com/docs/models/claude-sonnet-5) pages document those IDs.

These rules apply only to CursorBench, not every source using similar text.
Routing recomputes the correspondence instead of trusting an imported annotation.
A caller's confirmed `evidence_names` can still bind a native runtime alias. If
literal/caller and reviewed matches point to different runtime models, the row
is excluded as `ambiguous_model_identity`; neither binding wins silently.

No fuzzy search, edit distance, rolling-alias resolution, date-suffix removal,
provider-prefix stripping or version interpolation is performed. An unlisted
release keeps lexical matching. Fast variants remain separate; GPT-5.6 results
never become GPT-6 results. Effort is parsed separately and must match a setting
the caller supplied. Missing effort stays unknown, not `medium` or `max`.

## Inventory-aware lazy refresh

Supply the real host's current `available` list. The server still does not
query or infer the host's model catalogue. Both `get_routing_context` and the
advisor's `prepare_routing` acquire context through the same service.

For each relevant benchmark, the existing cache stores bounded fingerprints
of the inventories it has successfully checked. Each model entry's exact
lexically normalized names and supported efforts form one fingerprint. Adding
a model, confirmed alias or effort can request one check before the 24h TTL
expires. Reordering entries/efforts or removing a model alone does not.

A successful 200 or 304 records the check even when the new model has no row.
Its absence must not trigger a fetch on every recommendation. The check history
survives reconnects and holds at most 256 entries per source, evicting the
oldest checks first; an evicted entry can be checked again under the same
throttle. Old cache envelopes without this
history receive one check rather than an invented historical inventory.

Inventory-triggered checks have a five-minute per-source cooldown. Further new
entries return `refresh=inventory_deferred` and `next_inventory_refresh_at`;
a later ordinary request retries when eligible. Nothing runs on a schedule.
`Retry-After`, failure backoff, existing OS locks and the shared refresh deadline
still apply. Failed or cancelled checks never certify the inventory. A cancelled
early check retains its cooldown and last-good data without manufacturing a
publisher failure. Offline requests do not change check history.

Only the relevant benchmark sources this host can fetch receive these keys. A
browser-only source keeps its TTL while the browser adapter is disabled, rather
than recording a check that cannot succeed as a publisher failure; enabling the
browser makes it eligible again. Generic/model-specific guides retain their
existing TTL and scope filtering. The default advisor cache
is downstream of this acquisition step, not an alternative to it. An early
check is reported as `refresh_reason=inventory_changed`; a successful fetch is
still not evidence of complete model/effort coverage.

## Interpret the diagnostics

`sources[].model_matching` survives compact responses and advisor projection:

| Per-model status | Established scope |
| --- | --- |
| `source_unavailable` | No usable source snapshot; model presence has not been checked |
| `stale_disallowed` | Old data exists but the caller prohibited using it |
| `source_not_requested` | Supplied source is outside these task types |
| `no_matching_model_name` | No unambiguous name match in this snapshot and inventory |
| `no_matching_effort` | The model matched, but no observed effort matches a supplied setting |
| `harness_filtered` | Name/effort matched, but the caller's harness filter excluded the rows |
| `matched` | At least one usable row; not complete primary-cohort coverage |

Matched names retain the source/canonical spelling, correspondence rule and
reference. Unrelated names have an exact count plus at most 12 examples with a
truncation flag; relevant matches and ambiguous names are not silently dropped.
Neither an unmatched string nor `no_matching_model_name` proves that a publisher
has never evaluated the model. Inspect the source, verify a correspondence, or
retain the gap. Existing `unmeasured`, excluded efforts and cohort coverage still
apply. Conflicting rows resolving to one cohort/configuration remain errors,
not duplicated votes or a reason to choose the higher score.

## Prefer publisher data to a rendered page

Prefer a documented public JSON endpoint or an owner-maintained GitHub result
artifact over HTML or browser extraction when it supplies the same benchmark
revision, population, efforts and metric units. Task repositories, submission
examples and third-party mirrors do not by themselves establish current scores.
Do not guess endpoints from URL patterns or downgrade to an older benchmark.

Terminal-Bench 4.0 now tries Harbor's anonymous `leaderboard-read` API before
the opt-in browser route. The contract is grounded in the publisher's
[read client](https://github.com/harbor-framework/harbor/blob/9faf488373fbeea62ccca682dd2dbba5dab1d08c/src/harbor/hub/leaderboards.py),
[public application configuration](https://github.com/harbor-framework/harbor/blob/9faf488373fbeea62ccca682dd2dbba5dab1d08c/src/harbor/auth/constants.py),
and [4.0 board schema](https://github.com/harbor-framework/terminal-bench/blob/3b5caaa4863d64dda7f0957bf4fc2d4f019202d4/leaderboard/leaderboard.yaml).
The public application identifier is not a user credential; no Harbor SDK,
login, bearer token or credential-file read is involved.

The adapter checks board ID, version/name, visibility, complete pagination,
row uniqueness and metadata drift within one time/byte budget. Accuracy and its
interval retain the published percentage units. Run-total cost and tokens stay
in `aggregate_usage`, outside per-task expense comparisons; release dates do not
become evaluation dates. Inconsistent or malformed data fails closed.

`sources[].acquisition` records the actual API URL and paging scope. Browser
fallback is allowed only when already enabled, the endpoint is unavailable or
refuses the anonymous read (401/403, such as a rotated application key), and
time remains. The browser then reads the same public leaderboard page rather
than a protected resource, and the result retains the preferred-source failure.
Rate limits, Retry-After, redirects, other client errors or invalid data do not
authorize browser fallback. Cache identity changes invalidate derived old data.

DeepSWE already uses public JSON. The registered FrontierCode, CursorBench and
Atlas routes remain unchanged where no equivalent public result endpoint has
been verified. This is a discovery limit, not a claim that such endpoints do
not exist. Schema/fixture tests do not qualify live connectivity: use the
existing online `--force smoke --source terminal-bench` in the installed
environment before claiming this API works there. Do not bypass access controls
or silently remove failed sources from the reported coverage.
