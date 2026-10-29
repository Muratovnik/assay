# Evaluation protocol and current limits

Coordinator material, not runtime instructions. Use the existing
`tools/eval_assets.py` input/rubric protocol; no new runner, model dependency or
paid campaign is needed.

## Conditions

Compare the same scoped input, permissions and model settings using (A) the
enabled collection without retrospective and (B) the same collection with it.
Build input-only packets with `tools/eval_assets.py prepare`, using named cases
and explicit method roots. Its verifier does not enforce filesystem isolation;
keep grading keys, prior answers and execution history out of the executor's
reach. Explicit loading does not demonstrate automatic discovery: run the
discovery cases through the normal client route with the full collection
enabled, because D03–D05 are near misses other methods or no method should own.

## What the cases protect

| Case | Defect it detects | Nearby valid behavior it must allow |
| --- | --- | --- |
| C01 | Proposing a reworded copy of a rule that already exists | A proposal that changes when or how the existing rule is checked |
| C02 | Promoting one severe incident into a general rule | Proposing a targeted fix labelled as an incident |
| C03 | Findings derived from self-review without external evidence | Naming the sources that would make a review possible |
| C04 | Reporting "no lessons" from a wrong scope key | Reporting an empty store after a confirmed-correct key |
| C06 | Editing instructions before a decision; duplicating existing rules | Offering exact per-item changes with undo |
| C07 | Calling an accepted item resolved because its situation did not recur in full; re-proposing a rejected item | Marking an item unknown when the evidence cannot tell |
| C08 | Counting added requirements as agent failures | Suggesting an optional request template |
| C09 | Calling an entry stale without checking current files; silent curation | Keeping an entry that current files still support |

C01 and C06 come from an observed no-skill run in which two of fifteen
recommendations restated rules the owner's instructions already contained. That
run is regression evidence for these cases, not a held-out measurement.

## Fixtures

All inputs are synthetic and anonymised. No fixture contains real transcripts,
client data or personal data.

## Recorded comparison

A first paired run used C01 and C07, one executor configuration and explicit
loading, graded by the maintainer after all runs. Both conditions reached the
substantive answers: without the method the executor still found the norms
supplied in C01's inputs and tracked C07's earlier decisions correctly. The
method added a reading ledger, an explicit cause layer, exact changes with undo
and a per-item decision request, at roughly ten percent more tokens. Neither
case reproduced the failure to look for norms that are not handed over; a new
case should place the norm in the repository rather than the inputs. C01 and
C07 are now exposed regression cases.

## Efficiency-signal pilot — 2026-10-29

The method had counted only failures and corrections, and it called waiting
context rather than friction. The candidate adds a class of efficiency and
capability signals that need a measured avoidable cost: a wait, a step repeated
by hand, a fact found again, a model or effort that did not fit, cache misses
and a tool feature that covers manual work. It also asks for an aggregate before
a cost or quota conclusion. Digest lines and the friction lines of task
summaries become candidate sources. Each proposal names what it could cost in
quality or safety, a gate is weakened only with evidence that it catches no real
failures, and an accepted efficiency change is tracked by its measurement before
and after.

Six new public cases test it:

| Case | Defect it detects | Nearby valid behavior it must allow |
| --- | --- | --- |
| RE01 | Dismissing measured waste without a user complaint | Keeping the commit gate while removing repeated identical runs |
| RE02 | Adopting a cost setting from three chosen session pairs | Deferring until the period's records are aggregated |
| RE03 | Ignoring digest and summary lines, or counting a wait as context | Dropping a line that records only an impression |
| RE04 | Moving a slow gate that caught real defects to a weekly run | Repairing a gate whose failures were all false positives |
| RE05 | Inventing friction from long sessions and many tool calls | Naming the measurements that would locate a cost |
| RE06 | Calling a cheaper route resolved while its results are redone | Marking an unmeasured change unknown |

RE01–RE05 ran first on the 0.33.0 bytes, before the candidate was written.
RE06 was held back until the candidate was final. C03 and C07 were rerun as
regressions. Each case ran once per condition from a prepared packet, through
headless Claude Code 2.1.304 with `--safe-mode --restricted --strict-mcp-config`.
That run loads no CLAUDE.md, installed skill, hook or MCP server and keeps the
file tools inside the packet; a probe confirmed both. The executor was Opus 5.5
at medium effort with `Read`, `Glob` and `Grep`, and every run read the method
and its three references. One grader, Opus 5.5 at high effort under the same
isolation, graded all sixteen answers. It read only the prompt, inputs, answer
and criteria in shuffled folders, not the method, the manifest or the condition
key.

| Case | 0.33.0 | Candidate |
| --- | --- | --- |
| RE01 | 5 pass, 1 partial | 6 pass |
| RE02 | 4 pass | 4 pass |
| RE03 | 4 pass, 2 partial | 6 pass |
| RE04 | 4 pass, 1 partial | 4 pass, 1 partial |
| RE05 | 3 pass | 3 pass |
| RE06 | 4 pass | 4 pass |
| C03 | 2 pass | 2 pass |
| C07 | 3 pass | 3 pass |

The clearest difference is RE03. Under 0.33.0 the executor counted the repeated
gate runs as a pattern and then weakened them: "By the method, waiting time is
context, not friction." The candidate counted the same runs with their cost and
held a doc-only skip back until there was evidence that the gate catches nothing
there. On RE01 and RE04, 0.33.0 left one proposal without a quality cost. On
RE04 the candidate's speed-up named its cost and ruled out running only the
tests for changed code. The grader marked it partial on the first criterion: it
rejected the weekly run because the gate caught a data-loss defect, but did not
say outright that such defects would reach the main line. Without the method's
help, 0.33.0 already aggregated the cost pairs in RE02, counted the redos in
RE06 and refused invented friction in RE05, so those cases sit at the ceiling
for this executor. Executor cost was 1.21 USD for 0.33.0 and 1.29 USD for the
candidate across eight runs each.

This is one run per cell with one executor configuration and one grader. It can
show the contradiction the old sentence caused and the absence of a regression
on these cases; it does not measure recall of real friction or any saving. The
[cases](efficiency-cases.json), [criteria](efficiency-rubric.json),
[exposure metadata](efficiency-case-metadata.json) and
[evidence](efficiency-evidence.json) are now exposed regression cases; RE06,
the held-back case, is exposed too. The evidence holds answers, grades, packet
digests and method hashes.

## Limits

These files establish input and rubric structure only. They do not run a model,
measure recall of real friction, prove that users accept more proposals, or show
automatic discovery. A small paired comparison can support adopting the method
for its tested cases; it does not establish general quality or savings.
