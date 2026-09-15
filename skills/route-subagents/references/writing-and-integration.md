# Writing and integration

Use for delegated changes that share a checkout, generated output, runtime
resource or contract. The primary owns integration and coordination. Keep
ordinary read-only work outside this procedure.

Only that primary may spawn subagents. Every worker must be told not to spawn
additional agents; the primary creates reviewers and repair workers directly.

## Establish the source and effect boundary

Record the actual Git root, relevant base/HEAD and owned dirty bytes. Include
staged, untracked or ignored inputs only where they affect the packet. A status
listing alone does not identify dirty content. Multiple independent roots need
their relevant source vector; an ambient parent HEAD is not their identity.
Preserve user work; never auto-stash, reset or clean it to obtain a convenient base.

Choose between:

- Advisory: inspect or experiment only in authorized disposable resources;
  return evidence without changing the subject or durable external state.
- Shared checkout: schedule one writer per shared source/runtime surface.
  The primary and other workers do not write that surface until it returns.
  Independent repositories may proceed only when their contracts and runtime
  write sets are disjoint. File ownership alone does not prove isolation.
- Isolated checkout: parallel writers use separate worktrees or equivalent
  immutable snapshots, with integration retained by the primary.

Include effects of tests, imports, generators, package managers and hooks in
the write set. A checkout does not isolate a database, cache, port or service.
Use unique task-owned runtime resources where collisions are possible. If a
surface cannot be isolated or safely scheduled, keep that part advisory or local.

## Delegate a writer

Agree on the outcome, source identity, owned paths/hunks, shared decisions and
acceptance evidence. Freeze shared contracts only when another packet depends
on them. A commit, content digest or existing version can identify the contract;
do not invent a second version scheme. Invalidate affected dependent work when
its assumption changes; unrelated packets continue.

The worker may choose local reversible implementation details and run focused
checks within its scope. Stop and report drift, an unowned write or a changed
interface, schema, dependency, authority or external effect. Do not hide the
mismatch by broadening the packet or weakening a check. Keep routine
inspect/implement/test/repair cycles in the worker; return material deltas.

For a worktree, verify the owning repository, registered worktrees, target
ownership and canonical path before use. Refuse foreign directories or links;
do not delete them as preflight. Reproduce relevant dirty inputs in an explicit
snapshot or use a single writer. A worker commit requires applicable authority;
otherwise a detached checkout or exact diff can carry the result. Shared
generated outputs belong to one owner, normally integration.

## Integrate and close

Compare returned base, contract assumptions and actual changes. Integrate in
dependency order and resolve semantic conflicts deliberately. Preserve
pre-existing generated/user content unless exact replacement ownership and
rollback are established. Regenerate eligible shared outputs once.

Use focused checks while iterating, then owner-required repository, cross-root
and live checks for the stable integrated candidate. A child's green run does
not establish that integration succeeded. Reuse unaffected evidence after a
bounded repair; repeat broader checks when the change invalidates their coverage.

Use the [review procedure](review-and-continuity.md) when independent acceptance
review is requested or required by the owner contract. Task decomposition itself
does not add a review gate. Review cannot authorize push, publication, migration
or live data changes.

Preserve returned work until inspected and integrated or explicitly disposed
of. Reconcile worktrees, exact worker identities, dirty paths, task claims and
owned processes/ports/data before closure. Clean up only verified owned
resources through the owner's reversible mechanism; disclose retained residue.
Neither a per-turn Stop hook nor a session-end notification proves integration,
acceptance or successful cleanup.
