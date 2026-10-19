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

## Limits

These files establish input and rubric structure only. They do not run a model,
measure recall of real friction, prove that users accept more proposals, or show
automatic discovery. A small paired comparison can support adopting the method
for its tested cases; it does not establish general quality or savings.
