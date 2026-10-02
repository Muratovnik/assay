# Assignment packet examples

These examples describe the assignment sent by the primary to a worker. Their
layout is optional: use the fields that control the actual boundary. An advisory
question can be a short paragraph; complex writers and reviews benefit from an
explicit record. The worker's final result follows the separate
[required result template](outcome-and-repair-contracts.md#required-result-packet).

```text
Outcome / question and original objective:
Delegation purpose and expected use of the result:
Why delegate now; dependency or reconsideration trigger when deferred:
Primary-owned work while this runs (or why sequential isolation is useful):
Expected effect: change_required | no_change_acceptable | read_only_finding
Relevant root, base or snapshot, owned dirty inputs:
Selected model and reasoning effort, brief task/quota rationale:
Read scope, owned paths/hunks and runtime write set:
Shared decisions, dependencies and reserved generated outputs:
Acceptance evidence and permitted checks:
Excluded actions and escalation conditions:
Useful return and evidence pointers:
```

These are assignment/plan notes, not additional routing API parameters. Follow
[delegation planning](delegation-planning.md) when the split or timing is unclear.
Finalize relevant notes in the execution prompt before preparing the route;
never append them to an already authorized immutable launch input.

Record model and effort with the launch even when inheritance implements the
selection; no model matrix is needed. Explain ordered implementation steps only
when their order matters.
Distinguish decisions the worker must preserve from local choices it can make.
The worker must not spawn additional agents or change task/memory coordination
state; the primary owns those decisions. Write ownership alone grants no
publication, installation or external-action authority.

Use that result template to report the typed outcome, delivery evidence,
executed checks, source identity and unresolved issues.
Report incidental effects instead of asserting unchanged state from final
file hashes alone. A stopped process and a successful assignment are different.

Keep returns compact enough for their named consumer: result, changed boundary,
decisive evidence pointers, unresolved assumptions and next dependency. Retain
large logs in the permitted evidence location instead of forwarding them through
every packet. For an interrupted or resumed assignment, use
[planning continuation](../../implementation-planning/references/continuation.md)
to reconcile current bytes, completed effects and present authority before replay.

For review add the role-required mode, original brief, frozen contracts,
candidate identity, scoped risk and receipts for primary-owned stateful gates.
Do not supply the preferred verdict. For a finding repair send its location,
observed/required behavior, affected diff and named control, preserving the
unchanged authority and contracts.
