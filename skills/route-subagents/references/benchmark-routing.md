# Benchmark evidence context for model and effort selection

This local tool prepares published measurements for comparison. **It does not
select a configuration.** It does not run models, launch subagents, measure
subscription quota or change native client settings. The same application
service powers a stdio MCP server and a maintenance CLI. No paid router,
personal benchmark campaign or always-running updater is needed.

## Use from an agent

Prefer the MCP tools when configured:

- `get_routing_context(task_types=[...])` fetches missing sources, refreshes
  stale sources and returns the comparable measurements, their conditions and
  their gaps for every requested task type. Normal responses omit raw rows;
  `details=true` adds them. `details` never reveals a constraint that the
  normal response withheld.
- `routing_status()` reports installation, inventory, guide and cache age
  without any network request. It does not claim to have launched a browser.

The response has three parts that must not be mixed: comparable measurements,
quoted vendor guidance, and the reasons to doubt either of them.

Ask **once per plan**, listing every task type you are about to staff. Shared
parts — inventory, sources, warnings — are returned once, and each task type
gets its own comparisons. Call again for a new class of work, a changed
inventory, expired evidence, or when compaction dropped the content; a snapshot
identifier does not replace facts the session can no longer see.

On the first call, supply `available` from the **current host's** model
catalogue. The server remembers it for this connection and asks again after 24
hours; also resend it whenever the host's provider, available models or alias
resolution changes. Invalid input cannot replace a previously valid inventory.

Example input (fictional model names, not recommendations):

```json
{
  "task_types": ["implementation", "tests"],
  "available": [
    {"model": "frontier-a", "efforts": ["low", "high"]},
    {"model": "economy-b", "efforts": ["max"]}
  ]
}
```

No quality policy is required, and none is assumed. `constraints` is optional
and accepts `min_score` (0..1), `quality_loss_pp`, `max_cost_usd`,
`max_duration_seconds`, exact `harness` and `allow_stale`. A declared limit is
reported per candidate as `within`, `exceeds` or `unknown` — it never removes a
candidate from the context, and a per-call value does not persist to the next
call. `quality_loss_pp` compares against `quality_delta_pp`, the measured
distance from the best observed score **inside one cohort**; it is a caller
policy, not a learned optimum or a guarantee about the current task.

MCP does **not** expose a host model catalogue automatically. `--client` labels
the connection; it is not discovery. Codex's documented App Server `model/list`
can supply an inventory to a caller, but this adviser does not start another
Codex instance or silently read undocumented host files. In either client the
primary supplies a confirmed inventory once, not a permanent model ranking.

`evidence_names` may list verified publisher spellings for an exact runtime
model. Only lexical spelling is normalized. Never guess which concrete version
a rolling alias represents. Unknown effort is not low, adaptive or the default;
unmeasured efforts are not interpolated. Missing matches remain explicit.

Preserve the user's explicit model/effort choice. This tool never overrides
native authorization or proves which configuration actually ran. A known primary
quality gap or failed limit stays visible even when that source has no measured
cost. Do not turn incomplete evidence into a claim of savings.

## Install and connect once

Python 3.11+ is required. Core CLI operations use the standard library. MCP uses
the pinned official Python SDK; browser acquisition is a separate optional
installation. Work in a user-approved isolated environment:

```sh
python -m venv .cache/routing-env
# Activate using the normal command for your shell, then:
python -m pip install -r skills/route-subagents/scripts/requirements-mcp.txt
python skills/route-subagents/scripts/benchmark_router.py doctor
```

Use the environment's Python executable explicitly in native client settings.
For POSIX its relative path is `.cache/routing-env/bin/python`; for Windows it is
`.cache/routing-env/Scripts/python.exe`. Use absolute paths after resolving the skill
installation; the host's working directory need not be the repository.

A local JSON config may store preferences, without storing a model matrix:

```json
{"schema_version":1,"client":"codex","preferences":{"objective":"cost_usd","quality_loss_pp":3,"allow_stale":true}}
```

The value 3 is an example, not a benchmark-derived default. Use separate client
configs for Codex and Claude. A conflicting `--client` override is rejected.
Optionally add `inventory: {available: [...], observed_at: "...Z"}` with the
actual confirmation time. Otherwise the agent supplies it on the first call.
Neither config nor inventory belongs in tracked source.

Codex registration template (replace capitalized arguments with real paths):

```sh
codex mcp add benchmark-routing -- PYTHON_EXECUTABLE MCP_SCRIPT --config LOCAL_CONFIG
```

Claude Code registration template:

```sh
claude mcp add --transport stdio --scope user benchmark-routing -- PYTHON_EXECUTABLE MCP_SCRIPT --config LOCAL_CONFIG
```

`MCP_SCRIPT` is the absolute path to `scripts/benchmark_mcp.py` inside this skill.
Registration is an explicit user action; link installation does not mutate MCP
settings. For Codex keep `tool_timeout_sec` greater than the server's total
refresh budget plus process-cleanup margin (for example 60 vs the default 30).
The stdio process exists while the host uses it, but makes no scheduled or idle
refresh requests. Logs go to stderr, never protocol stdout.

A spawning hook is deliberately not required. Do not add a browser/network
request to every `PreToolUse`, silently rewrite model arguments, or grant tool
permissions just to route a model. The skill and MCP tool description provide
the entry point; a reminder hook would be advisory, not a quota guard.

See [Codex MCP](https://developers.openai.com/codex/mcp),
[Claude MCP](https://code.claude.com/docs/en/mcp), and the
[official Python SDK](https://py.sdk.modelcontextprotocol.io/).

## CLI and diagnostics

Paths below are relative to the repository; use the resolved installed skill
path elsewhere. Global flags go **before** the subcommand.

Use CLI for routing only when the configured MCP tool is unavailable in the
current session. Use the same Python environment, local config, cache directory,
browser flag and browser environment as the installed server. Report the fallback
reason. Missing tools in an existing session do not establish a broken server.
Do not drop browser/config flags or add `--offline` for convenience or speed.

```sh
python skills/route-subagents/scripts/benchmark_router.py status
python skills/route-subagents/scripts/benchmark_router.py doctor --check-browser
python skills/route-subagents/scripts/benchmark_router.py --config LOCAL_CONFIG --cache-dir LOCAL_CACHE --browser context --request REQUEST.json
python skills/route-subagents/scripts/benchmark_router.py --config LOCAL_CONFIG --cache-dir LOCAL_CACHE --browser context --task-type implementation --task-type tests
python skills/route-subagents/scripts/benchmark_router.py refresh --source deepswe
python skills/route-subagents/scripts/benchmark_router.py --force smoke --source deepswe
```

Here `python` stands for the installed environment's executable; preserve the
server's actual browser configuration instead of copying these example flags
blindly. `status` and `doctor` inspect local state and do not refresh evidence.

### Read acquisition before the decision

Every context response, including compact MCP output, carries
`data_status`, `data_message` and `usage` separately from the evidence
`status`. A valid request refreshes its relevant sources before comparison.

| `data_status` | Meaning and action |
| --- | --- |
| `ready` | All requested sources are loaded and within TTL; inspect decision coverage separately |
| `partial` | Some source is missing, or a forced refresh failed while cached data remains fresh; inspect each source |
| `stale` | Old data remains; freshness was not established and `allow_stale` controls its use |
| `unavailable` | No source data is available; inspect acquisition errors, never infer that publishers have no measurements |
| `offline` | Network refresh was explicitly disabled; `usage=diagnostic_only`, not a live routing result |
| `not_checked` | The client inventory is missing or expired; provide it before any refresh can run |

Each source includes `availability` (`fresh`, `stale`, `missing`), `refresh`,
`error` and `next_retry_at`, even without `details=true`. Preserve acquisition
warnings when summarizing decisions. Respect backoff instead of retrying on
every spawn. Empty primary comparisons with `data_status=ready` mean the loaded
data holds no usable primary match for this request; the same emptiness with
missing or offline data establishes nothing about publishers. Fresh sources can
still leave gaps, because some model/effort combinations or expense metrics were
never published.

### Diagnostic replay only

Use `--offline` only for deliberate cache replay or tests, never to select a
live subagent. Before analysing a fixed snapshot, make an online request for
every tested task type and check its acquisition state. Retain and
report any missing/stale sources; a replay cannot turn them into measurements.

```sh
python skills/route-subagents/scripts/benchmark_router.py --config LOCAL_CONFIG --cache-dir LOCAL_CACHE --offline context --request REQUEST.json
```

Offline replay preserves computed candidates for analysis, but always returns
`data_status=offline` and `usage=diagnostic_only`, even with a fresh complete
cache. Do not configure a normal MCP registration with `--offline`.
The CLI also writes a diagnostic warning to stderr so filtering JSON fields
does not silently hide the disabled refresh. Exit 0 still means a valid replay.

`context --request -` reads bounded JSON from stdin, so a temporary file is
unnecessary. The direct request contract has `client`, `task_types`, `available`
and the optional limits; none of the limits is required. Invalid JSON, unknown fields and
unbounded numbers are errors, not guesses. `status` never refreshes.
`doctor --check-browser` launches a local blank page in an isolated process;
it distinguishes missing package, missing binary, launch failure and timeout.

Options shared by CLI and MCP: `--cache-dir`, `--config`, `--client`,
`--ttl-hours` (24), `--timeout-seconds` (30), `--offline`, `--force`, `--browser`
and `--no-browser`. CLI adds `--details`. Force skips freshness, **not** an active
Retry-After/backoff. A smoke requires online mode and `--force`, checks actual
retrieval rather than cached fixtures, and exits 2 if a source fails or backs off.
It does not bypass site access controls.

CLI exit 0 means a valid result, including `no_evidence` or `needs_inventory`,
not necessarily a recommendation. Invalid input/local failure exits 2; an
interrupted CLI exits 130. MCP input errors are tool errors, not server crashes.

## Task types and context contract

| Task type | Primary evidence | Supporting evidence |
| --- | --- | --- |
| `implementation` | DeepSWE; FrontierCode Extended | CursorBench |
| `hard-implementation` | DeepSWE; FrontierCode Main | CursorBench |
| `investigation` | SWE Atlas Codebase QnA | CursorBench |
| `terminal` | Terminal-Bench | None |
| `refactoring` | SWE Atlas Refactoring | CursorBench; FrontierCode |
| `tests` | SWE Atlas Test Writing | DeepSWE |

Each comparison (cohort) is confined to one source, revision, subset, harness,
protocol and metric. Every measured `model x effort` in a cohort appears as a
candidate; none is dropped by ranking, policy or response size.

| Candidate field | Meaning |
| --- | --- |
| `score` with `score_low` / `score_high` | Published result and its interval, if any |
| `quality_delta_pp` | Distance from the best observed score in this cohort |
| `expenses` | Measured axes only: cost, tokens, duration, steps |
| `expense_evidence` | `measured`, `partial` or `none` — never a substituted value |
| `frontier` | Axes on which nothing in this cohort dominates it |
| `dominated_by` | Who dominates it, per axis |
| `constraints` | Each declared limit as `within`, `exceeds` or `unknown` |
| `stale` | The observation came from data that is past its freshness window |

Pareto holds **inside one cohort and one axis**. Expense axes are never merged
into a single number, and no cross-benchmark cost or averaged percentage is
invented. Overlapping published confidence intervals prevent a dominance claim;
`quality_delta_pp` uses point estimates and is labeled accordingly. A small
difference is not statistical evidence of equivalence.

Coverage is tracked for **every primary cohort and configuration** and is an
intersection, never a union across sources. A singleton is not comparative
evidence. Supporting observations cannot fill a primary gap. `unmeasured` means
incomplete primary coverage, not necessarily absence from every publisher.

| `evidence_gaps` entry | Meaning |
| --- | --- |
| `missing_primary_source_or_subset` | A required primary table is absent from this response |
| `incomplete_primary_coverage` | Some available configuration is unmeasured in at least one primary cohort |
| `noncomparative_singleton` | A primary cohort holds one candidate, so it compares nothing |
| `stale_primary_evidence` | Primary rows came from data past its freshness window |
| `unknown_primary_expense` | A primary candidate has no measured expense on some axis |

The Atlas task types commonly return quality-only candidates, because their
publishers do not supply comparable expense. That is ordinary context, not a
failure to advise. Reading the context is the caller's job: choose by what the
subtask needs, state which measurement supports the choice, and do not present
an unmeasured expense as savings.

## Vendor guidance

Guidance is extracted deterministically from official documentation: no
summarizing model, no paid call, no rewriting. The registry binds each document
to the client it applies to, so a Codex host is never handed Anthropic's effort
advice as if it applied.

| Guide | Publisher | Applies to | Sections |
| --- | --- | --- | --- |
| [Reasoning models](https://developers.openai.com/api/docs/guides/reasoning) | OpenAI | `codex` | Reasoning effort; Controlling costs |
| [Thinking](https://platform.claude.com/docs/en/build-with-claude/thinking) | Anthropic | `claude` | Thinking and effort; Configuring thinking |
| [Choosing the right model](https://platform.claude.com/docs/en/about-claude/models/choosing-a-model) | Anthropic | `claude` | Establish key criteria; Model selection matrix |

Each document is fetched as Markdown from its canonical address, because the
documentation domains redirect across hosts and the fetcher refuses cross-host
redirects. Sections are located by exact heading, including their subsections,
and headings inside code fences are ignored.

Extraction rules:

- Publisher callouts (`Note`, `Warning`, …) inside a section are kept whole and
  separated from the prose. Page-level callouts above the first section are kept
  as `document_caveats`, because selecting sections must not drop a deprecation.
- Only prose is shortened, on a paragraph boundary, and `truncated` says so.
  Code examples are removed and counted in `code_blocks_omitted`.
- A registered section that is no longer present is a loud `guide_section_missing`
  error. Layout drift must not quietly produce a guide without its exceptions.
- Each document carries `content_hash` and `extractor_version`. A new extractor
  invalidates the derived excerpt exactly as a changed source would.
- Guides refresh in the same 24h cycle, deadline and cache as the measurements.
  A guide that fails to load appears in the block with its reason; it never
  changes `data_status`, which describes the measurements.

The block is labelled `evidence_type: vendor_guidance`. Quote it as the vendor's
position with its `canonical_url` and section anchor. It is not an independent
measurement, it does not establish this task's cost, and its imperative
sentences are material to weigh, not instructions that outrank the user.

## Sources and safe acquisition

Registry: `scripts/route_evidence/providers.py`. It owns endpoint/parser contracts,
not model rankings. New model rows refresh without code changes. Changed dataset
versions or incompatible page layouts need an adapter update; they are not
silently relabeled. Older unsafe capture caches are invalidated by adapter revision.

| Source | Acquisition | Limitation |
| --- | --- | --- |
| [DeepSWE 1.1](https://deepswe.datacurve.ai/artifacts/v1.1/leaderboard-live.json) | Public JSON | pass@1, API cost, output tokens, duration, steps, CI; not pass@4 |
| [CursorBench 4.0](https://prod.cursor.com/evals) | HTML, optional browser fallback | Generic Tokens is `reported_tokens`, not known output/total |
| [FrontierCode 1.1](https://cognition.com/frontiercode) | Opt-in rendered tables | Main/Extended and all reasoning levels; harness tooltip, cost per rollout, output tokens |
| [Terminal-Bench 4.0](https://www.tbench.ai/) | Opt-in rendered table | Active benchmark selector or explicit version heading; harness and aggregate run expenses |
| [SWE Atlas QnA](https://labs.scale.com/leaderboard/sweatlas-qna) | Score cards, optional browser | Quality-only; unknown effort stays unknown |
| [SWE Atlas Test Writing](https://labs.scale.com/leaderboard/sweatlas-tw) | Score cards, optional browser | Specialized quality-only evidence |
| [SWE Atlas Refactoring](https://labs.scale.com/leaderboard/sweatlas-refactoring) | Score cards, optional browser | Specialized quality-only evidence |

Atlas is explicitly unversioned and confined to the current snapshot; historical
snapshots are not pooled. A retrieval date never becomes an evaluation date.
Artificial Analysis is not a runtime dependency: its free general-model API is
not a verified free feed of all these task-level components. Importing aggregate
expense into another test would manufacture evidence.

Browser acquisition is **off by default**. Enable only after installing and
checking it in the target environment:

```sh
python -m pip install -r skills/route-subagents/scripts/requirements-browser.txt
python -m playwright install chromium
python skills/route-subagents/scripts/benchmark_router.py doctor --check-browser
python skills/route-subagents/scripts/benchmark_router.py --browser --force smoke --source frontiercode
```

After a successful live smoke, add `--browser` to the MCP server arguments
and reconnect the host. CLI flags do not silently change server preferences.

An explicitly chosen existing Chromium can be provided through the local
`ROUTE_CHROMIUM_EXECUTABLE` environment variable. No signed-in profile is used.
The process uses a fresh context, rejects downloads and unexpected navigation.
Version proof is bound to the active heading/control, not body text. A selected
tab alone is insufficient: the captured panel must contain the new, ready table.
Ambiguous or unchanged transitions fail rather than relabel prior data.
Selectors are best-effort integrations, not a stable publisher API. Local DOM
tests qualify transition logic, **not the current live website**. Until live
smoke passes, keep that source explicitly unavailable; do not bypass blocking.

FrontierCode captures all reasoning levels, including controls added during
hydration, and waits for the changed table before recording a subset. Terminal-
Bench's animated heading is identified by its own text and the named Benchmark
selector. Its displayed aggregate cost and generic tokens are not converted to
per-task expenses or known total/output tokens; release dates are not eval dates.
To keep browser binaries with the isolated environment, set
`PLAYWRIGHT_BROWSERS_PATH` to its absolute `browsers` directory during both
installation and execution, including the MCP registration environment.

## Refresh, deadlines and recovery

Each source has an independent OS lock, atomic last-good envelope and conditional
HTTP validators. `last_success_at` (validated fetch or 304) drives the 24h TTL.
`last_attempt_at`, `data_changed_at`, publisher `source_updated_at` and per-row
`evaluated_at` remain separate. Unchanged 200/304 does not advance data-change
time. Failed fetches preserve last-good data and never extend freshness.

Cache defaults to XDG user cache on POSIX / LOCALAPPDATA on Windows, under
`assay/benchmark-evidence`. Keep cache, configs, logs and imports outside
tracked source. Payloads are size-bounded and validated; corrupt cache is not
partially salvaged. Registry changes invalidate incompatible cached evidence.

A single monotonic deadline applies to the entire refresh, not each source.
Primary sources queue first, at most three load concurrently. DNS, HTTP and
Chromium run in owned process groups. Timeout/cancellation terminates those
processes and descendants; supervisors drain and release locks before returning.
The deadline bounds acquisition, with bounded OS cleanup overhead afterward.
No fetch continues intentionally after the completed/cancelled call. Windows
uses a native Job Object with kill-on-close. A small stdin gate starts the target
only after assignment, so descendants remain owned even after the parent exits.
POSIX uses a new process group per worker. These local lifecycle controls do not
enforce provider-side quota limits.

Failures back off from five minutes to one hour; Retry-After is capped at 24h and
respected under force. Caller cancellation is not charged as a publisher failure.
Offline never starts a fetch worker. Clock reversal marks data stale.
`allow_stale=false` excludes stale data, while the status still shows the gap.

## Import and verification

When the native web tool can read a publisher but local networking cannot,
`ingest --file OBSERVATION.json --observed-at ACTUAL_ISO_TIMESTAMP` accepts an
observation in `validate_snapshot`'s schema. Exact source URL/revision, explicit
model/effort/harness, scores, expense basis and actual retrieval time are required.
Unknown expense remains null. Import cannot replace newer observations with older
ones or convert an agent's prose guess into measured evidence.

Run all repository owner-local gates from `AGENTS.md`. Additional tests are
included by existing `tools/test_*.py` discovery:

```sh
python -B -m unittest discover -s tools -p 'test_benchmark*.py'
```

Core and lifecycle tests use synthetic evidence without models or public network.
Real local Chromium tests exercise delayed DOM updates and version rejection.
The SDK test starts the actual stdio server and checks tools, validation and
connection inventory reuse. The separate Linux/Windows integration CI job sets
`REQUIRE_ROUTING_INTEGRATIONS=1`: missing SDK/browser is a failure there, not a
silent successful skip. Native Codex/Claude discovery and live source usability
still require their actual environments; do not infer them from unit tests.
