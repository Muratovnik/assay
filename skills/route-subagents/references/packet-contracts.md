# Assignment packet examples

These examples describe the assignment sent by the primary to a worker. Their
layout is optional: use the fields that control the actual boundary. An advisory
question can be a short paragraph; complex writers and reviews benefit from an
explicit record. The worker's final result follows the separate
[required result template](outcome-and-repair-contracts.md#required-result-packet).

```text
Outcome / question and original objective:
Expected effect: change_required | no_change_acceptable | read_only_finding
Relevant root, base or snapshot, owned dirty inputs:
Selected model and reasoning effort, brief task/quota rationale:
Read scope, owned paths/hunks and runtime write set:
Shared decisions, dependencies and reserved generated outputs:
Acceptance evidence and permitted checks:
Excluded actions and escalation conditions:
Useful return and evidence pointers:
```

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

For review add the role-required mode, original brief, frozen contracts,
candidate identity, scoped risk and receipts for primary-owned stateful gates.
Do not supply the preferred verdict. For a finding repair send its location,
observed/required behavior, affected diff and named control, preserving the
unchanged authority and contracts.
