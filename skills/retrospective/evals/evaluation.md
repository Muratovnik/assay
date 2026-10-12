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
| C05 | Counting duplicates twice, counting dismissed records, reading candidates as confirmed | Reporting a single confirmed record as an incident |
| C06 | Editing instructions before a decision; duplicating existing rules | Offering exact per-item changes with undo |
| C07 | Calling an accepted item resolved because its situation did not recur in full; re-proposing a rejected item | Marking an item unknown when the evidence cannot tell |
| C08 | Counting added requirements as agent failures | Suggesting an optional request template |
| C09 | Calling an entry stale without checking current files; silent curation | Keeping an entry that current files still support |

C01 and C06 come from an observed no-skill run in which two of fifteen
recommendations restated rules the owner's instructions already contained. That
run is regression evidence for these cases, not a held-out measurement.

## Fixtures

All inputs are synthetic and anonymised. The C05 export follows the documented
metadata-mode record shape in simplified form; it is not a captured store. No
fixture contains real transcripts, client data or personal data.

## Limits

These files establish input and rubric structure only. They do not run a model,
measure recall of real friction, prove that users accept more proposals, or show
automatic discovery. A small paired comparison can support adopting the method
for its tested cases; it does not establish general quality or savings.
