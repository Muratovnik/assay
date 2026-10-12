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

## Local feedback records

Some installations keep reviewed correction records. With Assay's feedback
capture, read them with its `list`, `show` and `export` commands, which need the
absolute parent data directory; its hooks `doctor` prints the configured command.
These commands do not annotate or review, but a store transaction — including
reading — removes records past their retention period, so a review can see
fewer records than an earlier one. In `metadata` mode records hold codes and
identifiers only; do not try to reconstruct text. Count `confirmed` records as
evidence, treat `candidate` records as unreviewed signals, never count
`dismissed` records toward a pattern, and count a `duplicate` with the record it
duplicates. The commands exist only in a full plugin or checkout; a skills-only
installation lacks them. Never enable capture as part of a review.

## Memory stores

Stored lessons and notes are evidence of what was learned, not of what
happened. Use them to find norms that already exist and to check whether a
lesson held. For a review of the store itself, use
[memory retrospective](memory-retrospective.md). A store's own summarizing or
reflection feature may be disabled or produce nothing; the review's synthesis is
done by the working model from retrieved records either way.
