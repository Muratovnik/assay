# Routing quality and total cost: independent review

Date: 2026-10-09. Review base:
`a9a7b746c382be1f57cd960be1635ec6b005fc85` on `main`.
Integration base was refreshed to `bffd9ccefa0d41683bf0c7dc2a9ed645cb9ad1b7`
(0.17.3); the intervening evaluation/release changes do not touch the audited
routing implementation or its governing skill instructions.

## Decision and evidence status

Repair the demonstrated selection, evidence and execution defects, and skip
work when a route is already fixed. Keep routing optional and keep ordinary
execution, a fixed route and a verified inexpensive attempt as legitimate
comparison policies. The evidence does not justify a new universal model/effort
default, a learned replacement, compulsory escalation, or deletion of the entire
execution adapter.

This is an engineering correction with local executable evidence. It does not
establish that Assay currently delivers the best quality at the lowest total
cost. Semantic advisor accuracy, current-client execution, accepted worker
results and complete comparative cost/quota receipts were not measured together.
That product-level requirement remains open; passing contract tests is not its
substitute.

The objective and alternatives below were framed before inspecting the current
routing implementation. The implementation was then challenged against that
frame, including cases where the cheapest benchmark route, the supplied baseline
and the cheapest successful complete chain disagree. A further independent
architecture challenge reproduced conflict, equal-price quality and misleading
selection-label defects during integration; these joined the repair plan.

## What routing should optimize

The unit is an accepted task or delegated packet, including its necessary
verification, recovery and integration. Choose among routes that can satisfy
the actual task and permissions. Compare quality and the cost of the complete
outcome, not model prestige, the last call's token count, the number of cheap
launches or agreement with the router's own recommendation.

For a comparable execution, account for routing, every worker attempt, reused
and repeated context, tools, verification, coordination and remaining repair.
Money, subscription quota, elapsed time and human correction are separate axes.
Missing usage remains unknown; a recorded zero needs an observation. Reasoning
tokens already included in output and cached tokens included in input must not
be counted twice. These accounting boundaries agree with the official
[OpenAI usage documentation](https://developers.openai.com/api/docs/guides/agents-api/observability).
An API-equivalent dollar figure is not itself subscription consumption; see
[Claude Code cost reporting](https://code.claude.com/docs/en/costs).

A stronger model or higher effort is justified by a relevant quality benefit or
lower complete-task expense. No arbitrary scalar weighting of quality, money,
time and quota was introduced. A requested hard constraint stays binding;
an unavailable capability is not repaired merely by raising effort.

## Alternatives considered

| Policy | Useful case | Evidence needed before making it the default |
| --- | --- | --- |
| Ordinary execution without a separate router | Avoids classifier calls, their failure modes and integration cost. | Its accepted outcomes and complete cost on the actual task mix. |
| One fixed configuration | Simple, reproducible control; a moderate configuration may suffice. | Compare inexpensive, moderate and strong configurations; strength is not a quality upper bound. |
| Inexpensive attempt, substantive verification, conditional escalation | Reuses an already necessary check and stops after a sufficient result. | False acceptance, repeatability of side effects, repair cost and contamination from an incorrect first attempt. |
| Deterministic capability/task rules | Real tool, modality, context or expressibility differences determine eligibility. | Task-class boundaries must predict outcomes; keywords and effort names do not prove quality. |
| Semantic advisor or learned predictor | Can distinguish tasks that cheap rules miss. | Relevant comparative outcomes, distribution shift, advisor errors and its own full cost. |
| Adaptive effort during execution | Later evidence can change the useful computation budget. | A supported runtime, trustworthy progress signals and full-trajectory comparisons. |

No option is entitled to survive because it already exists. Conversely, deleting
all routing because some of its economics is unproven would also require a
comparison. The opt-in execution adapter has a separate useful contract: binding
an authorized decision to the actual packet and worker. Its inventory, receipt
and continuation checks do not depend on proving an LLM advisor optimal.

The present simplification removes acquisition and advisor-capacity dependence
where evidence cannot affect the permitted choice. It does **not** automatically
recognize every small task as a fixed route. An ordinary packet with several
eligible pairs still uses recommendations by default. For a known local case,
the existing documented caller override can express a concrete, explained
reason to use a simple route; approved choices and explicitly unrouted native
types serve the corresponding owner-controlled required-mode cases. These are
existing authority paths, not declarations of measured optimality. See the
[advisor contract](../../skills/route-subagents/references/routing-advisor.md)
and [required-mode contract](../../skills/route-subagents/references/required-routing.md).

## Research that changes the decision

The source findings below are conditional results. Their transfer to Assay is
engineering reasoning, not a reproduced Assay experiment. The three supplied
foundational studies informed the review method; their bibliographies were not
treated as newly verified experiments.

| Primary source and inspected scope | Finding relevant to this decision | Transfer limit |
| --- | --- | --- |
| [RouteLLM v4](https://arxiv.org/html/2406.18665v4), 2025-02-23, sections 5.1 and 5.3–5.5, Tables 2–3 and 6–7 | Arena-only routers are close to random on MMLU/GSM8K; relevant augmentation improves them. Its CPT(50%) corresponds to 95%, 92% and 87% of strong-model quality on three different benchmarks. | Training distribution, metric and model pair matter. A blanket 95% quality guarantee would misstate this version. |
| [Ares v1](https://arxiv.org/html/2603.07915v1), 2026-03-09, sections 3 and 4.1–4.3, Tables 1–2 | On TAU-Bench Airline, fixed Medium reports 42% accuracy with 98k reasoning tokens, versus High's 38% with 873k; the trained RL route reports 42% with 133k. On Retail, adaptation has a favorable result. | Point estimates have no displayed uncertainty interval. Reasoning tokens are not complete dollars or quota. A per-step trained router does not directly validate one-time subagent selection. |
| [RouterBench v2](https://arxiv.org/html/2403.12031v2), 2024-03-28, sections 5.1–5.4 and limitations | Cascade evaluation varies errors in an oracle-based judge; predicted-route comparisons include simple controls. | An artificially corrupted oracle is not evidence that Assay has a reliable real verifier. |
| [LLMRouterBench](https://aclanthology.org/2026.findings-acl.1881/), Findings ACL 2026, comparison definitions, section 4, limitations and Appendix Table 12 | The corpus includes code and agent tasks; methods differ in maintaining best-single average quality. | Latency estimates exclude router overhead, networking, batching and caching; best-single is selected retrospectively. It does not supply current Assay task outcomes. |
| [Causal LLM Routing v2](https://arxiv.org/html/2505.16037v2), 2025-12-03, sections 2.1–2.3 | Selected-route feedback lacks outcomes for the alternatives; causal interpretation requires explicit assumptions and coverage. | Ordinary routing logs do not label the chosen route optimal. |
| [Conformal LLM Routing](https://aclanthology.org/2026.acl-srw.70/), 2026, section 3 and limitations | Its relative safety label includes cases where both models fail. | A guarantee relative to the stronger model is not absolute task acceptance; distribution assumptions still matter. |

[FrugalGPT](https://arxiv.org/pdf/2305.05176) and
[AutoMix v5](https://arxiv.org/html/2310.12963v5) were also inspected as cascade alternatives, including
their learned or processed verification signals and limitations. They motivate
testing a cascade where verification is useful, not installing an uncalibrated
self-confidence threshold. Further unrelated leaderboard additions would not
resolve the local questions identified here. The chosen additions are
discriminating regression cases, not a larger model scoreboard.

## Architecture and coverage

| Boundary | What was inspected or exercised | What that establishes |
| --- | --- | --- |
| Inventory and packet preparation | Configuration, eligibility, explicit choices, baseline provenance, fixed routes and numeric constraints. | Hard eligibility and source-acquisition behavior; not completeness of a caller-declared host catalog. |
| Public evidence | API/browser adapters, source revision/cache semantics, score intervals, expense scope, cohorts and vendor excerpts. | Contract-consistent extraction and comparison; not future publisher-layout stability. |
| Native and hosted advice | Current categorical contract, legacy rankings, malformed results, snapshot identity, cache and fallback. | Validated result handling; not semantic adequacy prediction or a live hosted inference result. |
| Deterministic selection | Benchmark groups, paired complete chains, missing data, baseline permutations, tradeoffs and conflicts. | Reproducible selection behavior under specified evidence. |
| Required execution | Real hook entry points with synthetic host events, dispatch, inventory refresh, provisional identity, authoritative returns and continuation. | Adapter state-machine behavior under those events; not native-client conformance. |
| History and cost | Record identity/lifetime, consent, import deduplication, pair construction, unit boundaries and full-chain observations. | Valid handling of recorded data; not unobserved alternatives, actual prices or subscription savings. |
| Resource lifetime | Actual subprocess groups, timeout/cancellation, successful-parent exit and a separate foreign process. | Owned descendant cleanup in the tested environment without stopping the foreign control. |

The implementation retains the existing protocol modes, dependencies, migrations
and compatibility paths. It adds no model list, learned router, model invocation,
paid comparison, global installation or new service. Existing benchmark evidence
remains useful context when its task and measurement scope fit.

## Confirmed defects and repair plan

The first three units address decision quality and cost directly. The remaining
units keep those decisions attached to trustworthy data and the intended worker.
Each repair includes the failing case and a nearby legitimate case, rather than
only checking its own output shape.

| Unit | Reproduced failure | Implemented correction and discriminating control |
| --- | --- | --- |
| R1: complete-chain economics | Benchmark means A=0.20/B=0.50 and paired accepted chains A=2.00/B=0.40 chose B with baseline A, but A with baseline B. A baseline-specific early return also ignored a third route. | Produce baseline-independent exact pair comparisons; apply them only to that pair. Permute baseline, input order and overhead; retain unpaired alternatives and unit/cohort boundaries. |
| R2: adequacy and fallback | A validated inadequate baseline could execute after all candidates were inadequate, or only unknown alternatives remained. | Reject the known-inadequate fallback. Preserve the legitimate explicitly qualified unknown-baseline fallback and distinguish malformed input from validated judgments. |
| R3: conflict, quality and units | A/B contradicted each other while unrelated C beat D; C was presented with no uncertainty. Equal full-chain price ignored strictly better paired quality. Tradeoff-only local evidence carried a cost-winner label. API and quota preferences could share one graph. | Keep disconnected/conflicting evidence visible; honor paired quality improvement at equal cost; distinguish an unresolved tie-break from a supported preference. Select in the requested measured unit, retaining an API fallback as explicitly quota-unknown when necessary. |
| R4: unnecessary routing work | Explicit complete choices, genuine singletons and no-eligible packets still acquired sources and could be blocked by pending-advisor capacity. | Preflight with the normal eligibility/policy validators. Skip acquisition only when evidence cannot change the decision. Numeric limits, partial choices, forced refresh and offline replay retain their required paths. |
| R5: expense scope and uncertainty | Terminal-Bench browser run totals became comparable per-task cost/tokens, while the preferred API retained them separately. Browser score intervals were discarded before Pareto analysis. | Both paths preserve run totals in `aggregate_usage`; unknown per-task expense stays unknown. Preserve percentage intervals. Bump affected adapter revisions to invalidate old derived cache entries. |
| R6: vendor exceptions | More than six callouts or an overlong callout silently lost text. Code examples could become apparent publisher caveats. The initial repair also removed code that was a condition inside an actual warning. | Retain the complete raw inner warning span, including code. Locate actual tags outside fenced/indented/container code, inline literals, comments and escaped markup; enforce bounds on the whole caveat or fail explicitly. Extractor revision 4 invalidates old derived cache entries. |
| R7: historical evidence | Local retrieval bypassed history identity validation and admitted foreign/wrong-schema or future-dated records. | Reuse owned record/filename validation and enforce creation/expiry time at persisted timestamp precision. Valid current history continues to match. |
| R8: usage identity | Distinct sessions sharing usage/timestamp values, or reusing an explicit event identifier, collapsed into one event. Native Codex usage records often omit header identities; copied and referenced forks also require ownership and inherited-counter boundaries. | Scope identities by client/root session/thread using observed native headers and owner markers. Keep per-thread context and deduplicate copied parent usage. Never infer missing ancestor cost or route settings; unresolved nested ownership and missing cumulative baselines produce partial/unknown totals. Reimports, direct request usage and properly marked forks remain valid. |
| R9: partial choices | A model-only explicit choice skipped local evidence even when several efforts remained. | Resolve the actual remaining candidates; skip only a genuinely fixed/empty choice. |
| R10: execution binding | A provisional start-order sibling could be resumed under another packet/model before the authoritative Agent return. Later observations could invalidate a continuation already prepared. | Require authoritative packet/worker binding for continuation and revalidate the latest observations at dispatch. Preserve valid idle same-worker continuation. |
| R11: withdrawn inventory | Removing a configured route after preparation did not invalidate authorization or an already authorized dispatch. A continuation also ignored explicit withdrawal. | Reread inventory/evidence bindings for new decisions and dispatch. Continuation separately requires its exact pair to remain listed, while allowing old timestamps and unrelated inventory changes. Reconfirmation of an unchanged inventory remains valid. |
| R12: decision reporting | Required-mode compact results discarded economic uncertainty, adequacy and fallback detail. | Preserve bounded qualifications and provenance without private measurements or explanation text. |
| R13: legacy malformed advice | A list in legacy packet IDs/rankings or a hosted choice raised raw `TypeError`, bypassing documented invalid-result fallback. | Validate types before set/dictionary operations and use the existing error/fallback path; retain valid legacy behavior. |
| R14: resource cleanup | A successful worker could leave a descendant with redirected pipes; the parent was removed from the process registry, so later cancellation missed it. | Release the owned group before unregistering success, timeout or failure. Verify a detached-pipe child stops while an unrelated process stays alive. |
| R15: invocation lifecycle | Auto-permission denial left a continuation reserved; expiry could roll back its release. A late predecessor result could displace the newer invocation and falsely complete it, permitting duplicate continuation. | Restore the exact idle predecessor on denied launch and retire expired authorization without extending it. Consume an observed start; keep newer invocation ownership across late/redelivered results and preserve inherited route-mismatch evidence. Exercise denial on both sides of expiry and delayed results across multiple generations. |
| R16: concurrent completion | Two services sharing SQLite could each finalize different answers in memory/history before one overwrote the other. | Validate/finalize and commit the bounded local result under one store transaction. Equal submissions share one result; conflicting submissions have one winner and one classified rejection. No model or network call occurs under this transaction. |
| R17: semantic cache identity | Packet IDs were canonicalized at the top level but retained inside attached task evidence, causing avoidable cache misses and repeat advice for a semantically identical renamed request. | Canonicalize the attached evidence IDs in the cache projection only and rebind the result to the actual request. Renamed/swapped IDs hit; changed task, objective, corpus or source revision still misses. |
| R18: evidence budget | The new all-pairs comparison pushed a four-route summary above the existing 6 KiB cap, dropping all its evidence. The committed regression's full summary is 7,728 bytes. | When needed, remove only per-category cost distributions and mark `cost_detail: "totals_only"`. That regression becomes 5,752 bytes with all six pair comparisons and complete quality/total-cost/unknown/cohort fields. Larger summaries still fail visibly at the unchanged cap. |
| R19: shared test-fixture cleanup | A pre-existing decision test manually initialized an asynchronous test helper, then called its cleanup dispatcher without a unittest runner. That dispatcher swallowed its own assertion, so the test passed while leaving its temporary directory for garbage collection. | Forward the helper's cleanup registrations to the active test before setup, including resources allocated before setup failure. A real-test ownership probe retained both directory objects: before the fix one directory survived test cleanup; afterward neither did. No production cleanup defect is inferred from this test-only finding. |

Regression owners are
[policy and dispatch cases](../../tools/test_routing_policy_guards.py),
[evidence boundaries](../../tools/test_routing_evidence_boundaries.py),
[fixed-route paths](../../tools/test_routing_fast_paths.py), and
[process lifecycle cases](../../tools/test_benchmark_service.py), together with
the affected existing integration and compatibility suites. PR-review repairs
add [whole-caveat cases](../../tools/test_routing_guide_caveats.py),
[summary budget controls](../../tools/test_routing_summary_budget.py), and
[shared-store/invocation tests](../../tools/test_routing_pipeline.py).
The final CI warning investigation also corrects the shared helper cleanup in
[decision lifecycle tests](../../tools/test_routing_decisions.py).

The baseline's initial 768-test run reported two Linux process-test failures.
Those two assertions inspected host-mounted `/proc` using namespace-local PIDs,
so they could read an unrelated process. The fixture now records its own
`/proc/self/stat` identity. That corrected control passed before the production
cleanup change. The separate successful-parent orphan test still failed before
the cleanup repair and passed afterward. A fixture defect was not presented as
proof of a production cancellation failure.

The final CI run exposed a separate `TemporaryDirectory` warning. Source review
found the unchanged baseline helper-cleanup defect in R19. A bounded real-test
probe reproduced it while keeping both directory objects alive: the unittest
result was successful, but one directory still existed after its cleanup phase.
After the correction both directories were gone. This confirms the fixture
defect independently of garbage-collection timing; the original CI log did not
identify the allocating test, so attribution of that specific warning remains
an inference. The original production code and public-acquisition receipts are
unaffected by this test-only correction.

For the original six fixed-path tests, the base produced two assertion failures
and three missing-marker errors. The corrected path passed all six; a seventh
control enables task evidence and fails if fixed-route corpus provisioning or
retrieval occurs. Evidence-boundary and policy probes likewise exercised the
old defects before their targeted repairs. These are deterministic behavior
checks, not a paired trial of language-model quality.

### Independent PR review and corrections

[PR #26](https://github.com/Muratovnik/assay/pull/26) first published candidate
`dfeaa3a29c7784ec4b89a2470bd2bd56e595c18d`. Separate reviewers examined decision
economics/evidence, execution/concurrency, and the implementation corrections.
The review found additional defects, including regressions in the initial
guide and summary repairs. These were reproduced and corrected before final
delivery; initial green CI was not treated as proof that the review was finished.
The late-predecessor invocation defect also exists before this PR, whereas the
summary-size regression was introduced by the all-pairs addition.

Shared-store completion was independently exercised with two real service
instances in separate processes, SQLite and history enabled. Equal answers
finalized once; competing answers produced one winner, matching retained
history and semantic-cache data. Acquisition remained fixture-controlled.
This verifies the local commit protocol, not
a live model's answer quality. A separate review repeated cache identity and
budget controls using a nonempty corpus.

Native-history fixtures were derived from the pinned public
[Codex session initialization](https://github.com/openai/codex/blob/2351d9e1b608e6f9d9a3699b71d7eb39ee41cfa4/codex-rs/core/src/session/mod.rs)
and [protocol definitions](https://github.com/openai/codex/blob/2351d9e1b608e6f9d9a3699b71d7eb39ee41cfa4/codex-rs/protocol/src/protocol.rs).
Those sources distinguish root sessions from threads, preserve copied history,
seed inherited counters, and record owner switches; referenced ancestors may
remain outside the selected file. Synthetic fixtures check same/different
roots, direct/cumulative usage, nested copied forks, reimport order and missing
boundaries. A missing owner remains unknown. These are source-grounded importer
checks, not a captured native execution or an automatic ancestor search.

The corrected guide extractor was rerun on the six saved primary response
bodies, with their original SHA-256 hashes verified. Normalized results were
identical apart from extractor revision 4. This revalidation is recorded
separately from the original network acquisition in the observation receipt.
The implementation is a bounded parser for the configured excerpts, not a
general CommonMark/MDX renderer.

The review began with an implementation-independent decision frame. Two PR
reviewers later disclosed an overbroad filename-only search for instruction
files; no out-of-scope file contents or evaluation answers were opened. The
entire process is therefore not described as perfectly blinded or as wholly
repository-contained discovery.

## Verification and remaining acceptance boundary

The corrective candidate passed all eight `python -B tools/check.py --all`
gates: source, unit suite, compatibility, catalog, evaluation data, rendered
clients, audit packets and preservation. Verification used a clean detached
worktree with all 17 corrective paths checked byte-for-byte against the reviewed
candidate. This isolated three untracked bytecode files that reappeared in the
original workspace after deletion with their old modification times. Their
restoring process was not identified; the source check was kept intact.
`python -B tools/assay.py render` reported no changes, and the working-tree
publication audit passed. A clean-history publication audit is also a required
gate. The final commit/tree, that audit and the corrective head's own hosted
results are recorded in [PR #26](https://github.com/Muratovnik/assay/pull/26).

The first published candidate independently passed both Ubuntu/Windows jobs in
[Check](https://github.com/Muratovnik/assay/actions/runs/37903425222) and
[Routing integrations](https://github.com/Muratovnik/assay/actions/runs/37903425223).
The latter installed real Chromium and required the SDK/browser fixtures;
Linux also passed native Claude plugin-manifest CLI validation. Those initial
results are identified separately from the corrective head. Independent
re-review closed the reproduced implementation findings on frozen file hashes;
publication verifies that those bytes match the final tree.

### Live public evidence and corpus check

The [observation receipt](routing-quality-cost-observations.json) records public
URLs, response hashes, adapter revisions, scope checks and precise limits.
The initial local pass completed twelve of thirteen configured production
acquisitions in fresh caches with identical offline rereads. A subsequent
isolated hosted run completed the remaining FrontierCode acquisition through
the same production adapter, so all thirteen now have successful acquisition
and offline-reread observations. The two runs retain separate receipts:

| Source | Live normalized observations | Expense/uncertainty result |
| --- | --- | --- |
| DeepSWE | 70 rows | All score intervals and published mean API costs retained. |
| CursorBench | 68 rows | Per-task cost and token observations retained; responsive duplicates removed. |
| Terminal-Bench public Hub API | 35 rows, complete board | Intervals and aggregate totals retained; no invented per-task expense. |
| SWE Atlas QnA / Test Writing / Refactoring | 24 / 24 / 17 rows | Quality intervals retained; unpublished costs remain unknown. |
| Six vendor guides | Two selected sections each | Current configured extraction and cache paths passed. |
| FrontierCode, subsequent hosted run | 260 rows: 130 Main and 130 Extended | Published API cost per rollout and output tokens retained for all rows; no score intervals in the captured result. |

The [FrontierCode acquisition run](https://github.com/Muratovnik/assay/actions/runs/37910374737)
used the unchanged production `Fetcher`, browser capture, parser and cache on
the corrective code. It observed the selected FrontierCode 1.1 revision and
both dataset subsets, retained hashes of the rendered capture and normalized
snapshot, and verified a new cache instance's exact offline reread with zero
network acquisitions. The operation took approximately 4.4 seconds inside a
90-second owned process scope; browser operations were bounded to 15 seconds.
Returned capture and worker output were each limited to 8 MiB. The production
browser has no total network-transfer byte cap, and the receipt says so.
The original failed local observation remains intact beside this later success.
The temporary probe workflow was removed from its separate audit branch after
the run; it does not change the PR's production code or install a recurring job.

All 35 rows in this live Terminal-Bench snapshot have 330 trials. Unequal trial
counts are therefore not a finding about that snapshot. The browser table still
does not establish all per-row budgets/protocols or supply a normalization
contract; the repair preserves aggregate scope consistently with the API.

The actual pinned public corpus bootstrap completed in 24.192 seconds, checked
all 13 selected member hashes and row counts, imported 1,055 tasks, applied its
declared split, and installed/reloaded 528 tasks with 6,864 observations. It
streamed 224,880,640 compressed bytes before its existing early stop; it did not
download the entire 1,283,503,080-byte archive or recompute its whole-file hash.
All source efforts remain unknown, and 1,584 API-cost observations remain
unknown. These are historical response observations, not measured current-model
or complete-agent-chain outcomes. The pinned repository supplies no license
card/file or dated tariff evidence; that provenance remains unspecified.

No new source defect was confirmed in this live pass. Reachable public
acquisition and the selected corpus's real import/storage path are thus tested,
while the following native/predictive boundaries remain separate.

The local environment has no Claude Code executable or active required-mode
session. The repository explicitly lacks a Codex required-mode adapter; an
installed Codex executable cannot validate the Claude protocol. Current host
model/effort application, hook discovery and private output behavior therefore
need an authorized bounded run in the intended client/version. Synthetic hook
events and configuration inspection cannot close that requirement.

Local Playwright Chromium installation failed: the first mirror supplied a
truncated archive and another returned HTTP 400; a later attempt also failed its
lock wait. Browser-dependent tests remain visibly skipped locally. The hosted
FrontierCode run closes that concrete public-acquisition gap. Hosted fixture
checks and a public-page capture do not establish a signed-in native model
session or future publisher-layout stability.

No comparable accepted-task matrix with complete model/effort and billing/quota
receipts was available. Consequently the review cannot establish either
semantic advisor accuracy or actual total savings. DeepSWE's published means
and free-text cost bases also leave a narrower comparison limitation: literal
basis equality can separate model-specific tariff descriptions, while missing
sample/task-count detail weakens transfer. This review does not invent tariff
equivalence, silently pool groups or classify unknown prices as zero.

### What would close the product-level requirement

Use representative real packets whose acceptance criteria and verification are
defined before examining the routing result. Include a small edit, a bounded
implementation, a difficult investigation and a case needing a genuinely
different capability. Include the nearby cases a proposed policy must
distinguish; task labels alone are insufficient.

Compare ordinary execution, a reasonable fixed configuration, the corrected
router and an inexpensive attempt with verification where retries are permitted.
Use the same substantive inputs, permissions, tools and acceptance criteria;
record actual host model/effort, failures, every attempt, verification,
coordination, remaining correction and missing usage. Keep development cases
separate from fresh evaluation cases. Do not infer an alternative outcome from
the chosen route's success or call an unknown bill zero.

Judge the accepted outcome independently of the router. Report paired quality
and complete cost by task family, uncertainty and uncovered families; do not
hide a quality loss inside an overall average. If the simpler policy is as good
at lower complete cost, simplify or remove the extra routing layer for that
scope. If a learned or adaptive policy improves a covered family, adopt only the
supported boundary and reevaluate after relevant model/runtime changes.

The concrete blockers are access to the intended native host and comparable
outcome/cost observations, not a shortage of public leaderboard names. Until
those are resolved, this change is reviewable engineering work, not a completed
validation of the requested product objective.
