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

Waiting, long sessions and many tool calls are context, not friction, unless the
user objected or work was lost.

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
request format instead.

## Counting

- One incident counts once, however many messages, retries or errors repeat it.
- Independent means a different session or task, not a later turn of the same one.
- Keep the same friction under one name across sessions; do not split it to look
  less frequent or merge different causes to look more frequent.
- A correction after a context compaction may be caused by the compaction. Say so
  as a hypothesis; do not assume it.
