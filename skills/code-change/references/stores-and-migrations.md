# Shared stores and schema migrations

Read this before changing code that writes to a store more than one request,
process, thread or retry can write at the same time, or before changing a stored
schema or format. Whether atomicity, retry or idempotency belongs to the contract
is decided with the architecture method's
[boundary criteria](../../software-architecture/references/architecture-design.md#define-the-chosen-boundaries);
this procedure implements it once it does. A store only one writer reaches and a
read-only query need none of it.

## Decide and write in one step

A value read, checked in application code and then written leaves a window in
which another writer changes it, and one of the two updates is lost. Make the
check part of the write: an update whose condition holds the expected state or
version, an insert the store rejects on conflict, or a transaction that takes
the write lock before it reads (in SQLite, `BEGIN IMMEDIATE`). Read the result:
no affected row means the condition failed, which is a conflict to report, not
a success.

Enforce uniqueness and other cross-row invariants with a constraint in the store
and handle its violation as the expected conflict; a lookup before the insert
races the same way. Where the contract accepts last-writer-wins, keep it: a
version check there rejects valid concurrent work.

## Effects outside the store

Make no network call, message or file write inside an open transaction: it holds
the locks for the call's duration, and a rollback cannot undo it. Commit the
intent first, make the call, then record its outcome, so a crash between the
steps leaves a state that a retry or reconciliation can find.

An operation that can arrive twice, such as a client retry, a redelivered message
or a replayed webhook, carries a key from its own request or event, stored under
a unique constraint, so the repeat returns the first result instead of repeating
the effect. Pass the same key to an external service that accepts one. Move a
record's state only from the state the transition expects; a duplicate or
out-of-order event then changes nothing or is recorded as a conflict. Two
distinct requests with equal content are not duplicates.

## Migrations

Give each migration a reverse step and run it: apply, reverse and apply again on
a copy holding data in the old shape. Where the reverse step cannot restore data,
say so and name the backup that does. Never edit a migration that may already
have run anywhere; correct it with a new one.

While a release rolls out or back, the previous code runs against the new schema
and reads what the new code writes. Expand first: add tables or nullable or
defaulted columns and keep everything the previous code reads and writes
working. Contract in a later release, once no running version uses the old
shape. A purely additive change needs no extra stage.

## Check it

A single-threaded test cannot show a race. Start 10 to 20 concurrent writers on
the engine the product uses and assert the final state, such as counts, sums and
the absence of duplicates, through the supported read path; a fake store lacks
its [transaction semantics](../../test-writing/references/boundary-choices.md#doubles-and-real-effects).
For a migration, run the round trip above, then the previous release's reads and
writes against the migrated schema. Assertions and fixtures stay with
[test-writing](../../test-writing/SKILL.md).
