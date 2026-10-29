# Evidence sources

Read a source only when the user permits it and the client can reach it. No
single source is required; name the ones that were unavailable. These are kinds
of evidence, not products: apply the same checks to whatever implements them.

## Before reading any source

- **Confirm the scope key.** Stores often expect a short project name, an
  identifier or a path in one exact form. Query a scope you know has records
  first; a wrong key usually returns an empty success, not an error.
- **Bound the read.** Prefer counts, filters and date ranges over full listings.
  A listing without a limit can exceed the context window on its own.
- **Aggregate, then sample.** Count signals across the whole period first, then
  read only the passages that decide a candidate. Record the sampling rule.
- **Keep a reading ledger.** For each source: what was read in full, what was
  aggregated, what was sampled and what was skipped, with the reason.
- **Exclude the current session** from evidence about past work; it contains
  this review itself.

## Session transcripts

Client session logs are the richest source and the largest. Stream them; do not
load whole files. A one-off script that extracts user messages, tool errors,
hook errors, permission refusals and compaction markers is usually enough —
write it to a disposable location and do not ship it.

- User messages carry most corrections. Read them in full for the period before
  sampling agent replies.
- Read the agent reply that preceded a correction only to confirm what was
  corrected; do not grade the whole conversation.
- Subagent or worker transcripts are separate files; say whether they were read.
- Duplicate entries with identical timestamps are usually logging artifacts, not
  repeated requests.

## Version-control history

Reverts, a fix shortly after a feature, repeated edits of one plan or rule, and
commit messages that name a correction are signals. Commit volume alone is not.
Read history in each repository where the work happened; a parent workspace's
log does not include its children's.

## Planning and task records

Reopened items, guard overrides, blocked reasons and closing summaries that admit
an omission are signals. An item that took long is not a signal by itself.

## Friction digests and summary lines

Some owners keep a digest of working-system friction, or end each task summary
with a line naming the friction it met. Read both before transcripts: they are
small and already point to their evidence. Each line is a candidate, not a
finding, on equal terms with a signal found in a transcript:

- keep a line only if it names an external signal; drop one that records only an
  impression, such as "felt slow";
- count lines from one task as one incident, and a line that reinforces an
  earlier one as a separate occurrence only when it comes from another task;
- open a transcript or record only to confirm a line that decides a proposal;
- a summary that says no friction shows only that nothing was recorded, and a
  summary without the line is a gap in the reading ledger.

## Memory stores

Stored lessons and notes are evidence of what was learned, not of what
happened. Use them to find norms that already exist and to check whether a
lesson held. For a review of the store itself, use
[memory retrospective](memory-retrospective.md). A store's own summarizing or
reflection feature may be disabled or produce nothing; the review's synthesis is
done by the working model from retrieved records either way.
