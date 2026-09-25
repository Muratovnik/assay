# Continuation and handoff

Use across sessions, handoffs or interrupted non-atomic work. An atomic short edit
needs no persistent ledger. Use the authorized task/document/tracker as the source
of planning state; do not add a task database or copy the whole repository.

## Preserve sufficient context

Record the exact selected task and project/artifact identity, original constraints,
important decisions and their reasons, actual changes, check results with their
scope, unresolved dependencies and next action. Include exact version or digest
when needed to distinguish the artifact a result applies to; do not invent a Git
identity for a non-Git design artifact. Link authoritative context and include the
critical details a new executor needs, rather than requiring the old chat.

Separate planned, implemented and verified claims. A commit is a change receipt,
not a behavior check. A checkbox without evidence does not establish completion.
Keep failure, unavailable proof and explicitly deferred work distinguishable.
Use whatever existing statuses express these meanings; do not require new labels
or a fixed state-machine schema.

For a long document, keep a short orientation and load the current stage plus its
shared constraints and prerequisite decisions. Do not reread every future detail,
or omit a shared contract to save context. Selective reading is a mechanism to
check, not an assumed token saving.

## Reconcile before continuing

Resolve the selected task exactly. If its identifier or source is unavailable,
report that rather than silently selecting a nearby plan. Inspect the current
artifact and relevant drift, preserving unrelated work. Recorded progress is a
hypothesis; the current project establishes what now exists. Confirm which prior
checks still apply and refresh only affected evidence.

Before repeating an interrupted operation, determine whether its effects already
occurred. A missing success receipt is not evidence that an operation failed.
For a potentially committed migration, remote creation or submission, inspect the
actual effect or use the owner's supported idempotency/reconciliation mechanism.
If the state cannot be determined, block that replay and identify the next safe
observation; do not guess or claim a reversible operation without a recovery path.
Continue from the last verified boundary, not the first unchecked box blindly.
Adapter reconnect and transport mechanics remain with the adapter.

If multiple authorized executors contribute, keep one identifiable owner of the
shared plan or the tracker's existing coordination mechanism. Give contributors
bounded units and merge their evidence; do not let independent whole-document
rewrites overwrite each other. This grants no delegation or new locking service.

## Example: missing receipt after a remote import

The old note says 'send import', the process stopped, and the remote resource now
exists under the recorded operation key. Inspect that resource and its state before
sending again. Preserve the established result, check remaining acceptance and
continue with the next uncompleted outcome. If no supported lookup can settle
whether the import committed, report the ambiguity and seek the appropriate owner
or safe reconciliation path. Do not retry merely to obtain a cleaner transcript.
