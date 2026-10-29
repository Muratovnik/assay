# Friction signals

Classify each signal before counting it. The class decides whether it can
support a rule at all.

## What counts

| Signal | Example evidence | Notes |
| --- | --- | --- |
| Correction | "That is not what I asked", "you forgot the commits" | Compare with the earlier request before calling it a mismatch |
| Redirect | The user stops work and points elsewhere | Often an over-reach: an action beyond the request |
| Abandoned approach | Work started, then dropped after failure or objection | Check whether the drop was the user's choice |
| Unanswered question | A direct question followed by a reply that does something else | Count once per question |
| Tool, hook or check failure | Error output, silent hook errors, failing gate | Repeated identical errors in one session are one incident |
| Permission refusal | A blocked action the user had to approve or redo | Separate a policy false positive from a correct block |
| Reopened or reverted work | Reopened task, revert commit, re-edited rule | Read why before counting |
| Repeated request | The user asks for the same multi-step routine again and again | A candidate for a reusable procedure, not a failure |

## Efficiency and capability signals

Work can meet every requirement and still waste time or budget. These signals
count only with a record of what was spent:

| Signal | Example evidence | Notes |
| --- | --- | --- |
| Measured wait | Gate or tool timings; a run repeated on unchanged input with the same result | Count the avoidable part. A required run is the step's price, not friction |
| Step repeated by hand | The same manual sequence in several sessions | Check whether a tool, command or procedure already does it |
| Re-derived fact | The same fact found again by trial or search in independent sessions | If a stored note already holds it, the norm exists and was not applied |
| Model or effort not matched to the task | A lookup run on the largest model at maximum effort; a cheaper route whose results had to be redone | Read the launch records and the outcome, not a price list |
| Cache misses | Cache read share, cache writes and cost from usage records | A cost signal; the aggregate rule below applies |
| Unused client or tool capability | Documentation or help output showing a feature that does the manual step | Confirm the feature exists in the version actually in use |

Waiting, long sessions and many tool calls alone are context, not friction. They
become a signal only with a measured avoidable cost, such as a repeated
identical run, a manual step a tool already does or a fact found again. A sense
that the work could be faster is not evidence.

A cost, quota or cache claim needs an aggregate over the period's sessions,
compared by condition on comparable tasks. One session or a few chosen pairs is
a hypothesis: a saving that looks clear in each case can be a tie or a loss in
the aggregate. Keep wall time, billed cost and subscription quota apart.

## Distinguish before counting

Sort each candidate into one of these categories:

- **reported mismatch** — the result did not meet a requirement stated earlier;
- **changed requirement** — the user added or changed a requirement; not an
  agent failure;
- **preference** — a legitimate taste the earlier request did not state;
- **disagreement** — the user and agent differ on a judgment; record both sides;
- **uncertain** — the context does not show which.

Only reported mismatches, failures and refusals support a rule about the agent.
Changed requirements and repeated requests may support a template or a clearer
request format instead. Efficiency signals support a change to the working
system — a gate, a tool, a stored fact, a route or a setting — and each such
change is weighed against what it could cost in quality or safety.

## Counting

- One incident counts once, however many messages, retries or errors repeat it.
- Independent means a different session or task, not a later turn of the same one.
- Keep the same friction under one name across sessions; do not split it to look
  less frequent or merge different causes to look more frequent.
- A correction after a context compaction may be caused by the compaction. Say so
  as a hypothesis; do not assume it.
