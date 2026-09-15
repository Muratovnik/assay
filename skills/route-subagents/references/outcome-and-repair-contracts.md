# Outcome and repair contracts

Use these contracts for every delegated packet. They classify what happened;
they do not replace the primary's inspection or oracle.

## Expected effect

Choose exactly one before spawn:

- `change_required`: acceptance requires an owned artifact change.
- `no_change_acceptable`: a verified no-op may be the correct result.
- `read_only_finding`: the packet must not mutate durable state.

An expected effect is part of the packet, never inferred from the worker's
report after it returns.

## Worker outcome

Classify exactly one:

- `launch_failed`: the worker never began useful task execution.
- `refused`: the worker began but stopped on safety, authority, capability,
  ownership, or packet validity.
- `expected_no_change`: no owned artifact changed, the packet allowed that, and
  the named oracle confirms the conclusion.
- `unexpected_no_change`: a change was required but no qualifying artifact
  changed, regardless of process exit code.
- `partial`: useful in-scope work exists, but an acceptance criterion, owned
  output, or required oracle remains incomplete.
- `complete`: every packet-owned output and required investigation is delivered,
  and the assignment's acceptance conditions are met. This is distinct from the
  verdict or exit code of the subject being investigated.

`complete` and `expected_no_change` require delivery evidence. A model's claim,
terminal exit code, config entry, or spawned-thread presence alone is
insufficient.

## Capability evidence ladder

Report the highest rung actually observed:

1. `configured`: a file or registration requests the capability.
2. `binding_visible`: the active client exposes the binding or role.
3. `live_call_or_spawn_observed`: one real invocation selected it and returned.
4. `delivery_verified`: the resulting artifact/no-op and oracle were inspected.

Do not promote a lower rung with inferred metadata or create a persistent
attestation ledger. Record only the evidence needed by the current run.

## Required result packet

Use the six headings below, in this order, for the worker's final result so the
primary can compare results and spot missing evidence. Keep entries concise;
use evidence pointers instead of repeating logs or the assignment. Explicitly
mark unavailable evidence, checks not run, or no unresolved issues. The optional
[assignment examples](packet-contracts.md) do not make this result format optional.
If the assigned role requires its own result contract, follow that contract and
carry the applicable information there without adding a duplicate report.

```text
OUTCOME
- launch_failed | refused | expected_no_change | unexpected_no_change | partial | complete

EXPECTED EFFECT
- change_required | no_change_acceptable | read_only_finding

DELIVERY
- Exact changed artifact/diff, verified no-op, or finding set.

ORACLE
- Command/check, exit code or verdict, and decisive evidence.

SOURCE AND IDENTITY
- Base/result identifiers and exact worker/task identity when exposed.

UNRESOLVED
- Missing criteria, changed assumptions, and residual risk.
```

For a writer expected to deliver working behavior, a failed required check
prevents completion. For an audit or requested reproduction, a demonstrated
subject failure can be the correct complete result. Keep assignment completion,
subject verdict, and observed check exit/result separate. An audit with missing
required investigation is partial even if one defect was found.

Reject internally inconsistent combinations, including `complete` with an unmet
assignment acceptance condition, `expected_no_change` for `change_required`, or a
read-only finding with unexplained mutation.

## Repair delta

For a focused correction, send only:

```text
REPAIR DELTA
- Location: exact file, hunk, output, or finding identifier.
- Observed: current behavior or evidence.
- Required: smallest sound correction.
- Oracle: exact check that proves the correction.
```

Keep frozen decisions, ownership, source identity, and out-of-scope boundaries
unchanged. If any must change, re-plan instead of calling it a repair.

After each focused repair:

- accept only after the primary reruns the sound oracle;
- select a different capability or configuration only for a demonstrated
  reasoning or task-shape mismatch;
- re-plan for ownership, interface, source, authority, or isolation failures;
- continue only when the repair produced a new material diff, oracle result, or
  corrected assumption and the owned oracle can still converge;
- stop or re-plan when the same sound oracle fails again without new evidence,
  rather than repeating the same prompt as a vote.
