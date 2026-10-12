# Proposals and tracking

A proposal is a decision the user can make in one reading. A direction such as
"add a rule about X" is not a proposal until it says where, what and how to undo.

## Write each proposal

| Field | Content |
| --- | --- |
| ID | Stable within this review, for example `P3`, reused when tracking it later |
| Evidence | Record pointers and counts: which sessions, tasks or commits |
| Status | Pattern (with count) or single incident |
| Existing norm | The norm found during reconciliation, or "none found" with where you searched |
| Layer | absent, not loaded, loaded and not applied, check missed, conflicting, or unknown |
| Destination | The place the owner's own instructions route this kind of lesson to |
| Change | The exact text, check, setting or procedure step to add, edit or retire |
| Undo | How to revert it if it does harm |
| Risk | A legitimate case the change could wrongly block |

Choose the smallest change for the layer:

- **absent** — add a rule, check or procedure step;
- **not loaded** — repair discovery or the instruction that should route to the
  existing norm;
- **loaded and not applied** — strengthen the check or the moment the norm is
  applied; a skill's behavior goes to skill-evaluation;
- **check missed** — repair the check so it fails on this case;
- **conflicting** — propose which norm wins and retire or narrow the other;
- **covered and working** — no change; keep the evidence.

Prefer editing or retiring an existing entry over adding a near-duplicate.
Never rewrite a whole instruction file to apply one proposal.

## Let the user decide

Present proposals together, highest-evidence first, and ask for a decision per
ID: accept, defer or reject. Do not apply anything before that answer. Apply
accepted items one at a time through the owner's normal tools and checks, and
report each result. A rejected proposal is a decision, not a failure; keep its
reason so a later review does not re-propose it without new evidence.

## Record decisions without a new store

Keep the decisions where the owner already keeps planning records — an issue,
task or planning item the user names — with proposal IDs, decisions, applied
changes and their commits or references. Save to memory only lessons the user
confirmed. Do not create a retrospective log, processed-entries file or report
directory unless the user asks for one.

## Track earlier proposals

At the start of a review, read the previous decisions. For each accepted item:

- **resolved** — the friction did not recur in the new period's evidence;
- **recurring** — it returned; link the new evidence and reconsider the layer;
- **unknown** — the evidence cannot tell, for example the source was not read
  or the situation did not arise.

Absence of complaints is not resolution unless the situation actually arose.
