# Discriminating probes

Use only probes needed by the scoped claim. Preserve source identity and report
the exact command, input, result and environment that support the conclusion.
An unexecuted suggestion is not a reproduction.

## Is the expected result justified?

Compare the assertion with the actual owner requirement and supported consumer.
If implementation and test share a wrong boundary, demonstrate the contract's
counterexample. Do not infer expected behavior solely from method names, the
latest implementation, generated docstrings or a second model's agreement.

Inspect helpers that calculate expected values. Shared production logic can
hide the same defect on both sides; a smaller independently specified reference
or trusted vector is different. Round-trip agreement alone does not establish
compatibility with an external format. Properties need valid domains, meaningful
generated cases and evidence that filters do not exclude every interesting input.

## Does the assertion detect the protected fault?

Choose a relevant missing effect, wrong branch, wrong value or prohibited action.
Prefer a known bug/fix pair when compatible and safely available. Otherwise a
small mutation or injected dependency failure in an authorized disposable copy
can discriminate the claim. Keep the unmodified valid control.

Run the same test under comparable conditions and inspect which assertion
fails. Do not count collection errors, incompatible dependencies or unrelated
failures as proof of fault detection. A timeout may reflect a meaningful liveness
failure or a harness problem; establish which before giving detection credit.

| Intended version | Known faulty version | What is established, after diagnosing the result |
| --- | --- | --- |
| Pass | Relevant assertion fails | Evidence of detecting this fault, not every defect. |
| Relevant assertion fails | Pass | Possible wrong-behavior lock-in; first verify the intended contract and version compatibility. |
| Pass | Pass | This fault was not detected; the test may protect another guarantee or the change may be equivalent. |
| Fail | Fail | Undiagnosed: setup, oracle or either version may be wrong. Not automatically a false assertion. |

For mutation reports, record selected population and separate survivors,
equivalent changes, timeouts, compile failures, skipped and untested cases.
Do not impose universal 100% scores or edit production merely to eliminate an
equivalent mutant. Detection quality is independent of whether the intended
behavior was justified in the first place.

## Would valid alternatives be rejected?

Identify a concrete behavior-preserving alternative: reorganized helpers,
another internal class, equivalent DOM structure or a different legal call
sequence. Demonstrate the false rejection through a safe copy or decisive
coupling evidence. Do not call an actual public API, protocol, accessibility or
architecture-contract change a harmless refactor.

For presence/absence rules, follow what the rule protects and the population it
should constrain. A banned string in a source file need not be a forbidden
runtime dependency; an unreferenced name search need not prove unused code.
Conversely, an exact exported name or release-format field can be intentional.

## Does the transition gate protect new work and permit completion?

For a suppression or migration gate, take the probes from the
[exclusion and end-state checks](../../code-maintenance/references/effective-quality-checks.md#check-exclusions-and-the-reachable-end-state).
The verdict stays here and covers both directions: a new violation the gate admits
is false acceptance, and a cleared or last-removal state it rejects is false
rejection. An illustrative checker establishes only the example's result; do not
count it as production protection or as evidence that a model will choose this
procedure.

## Are observations real and stable?

Follow outputs and side effects beyond mock calls where the claim requires it.
Saving through a stub does not prove durable storage. A hidden button does not
prove access is rejected. A screenshot does not prove a request was persisted.
Tests that set focus, scroll, call a private handler or repair state before
asserting may manufacture the supposed application behavior; inspect the state
immediately after the actual action at the claimed boundary.

Match the fixture to the defect's causal scale. A tiny fixture can validate local
arithmetic while leaving information density, decision workload, pagination or
bulk recovery entirely untested. Compare zero, one, several and a realistic
large case when behavior changes with cardinality. Do not demand artificial
scale when the approved contract imposes a small maximum.

For layout, distinguish containment from utility. A panel can avoid overflow and
still be too narrow to perform the task. For competing states, assert the
required precedence or absence in the same transition; seeing each label in a
different phase does not establish an uncluttered hierarchy. For state shared
across screens, follow the persisted value to each affected consumer rather than
crediting only its editor.

For suspected nondeterminism, isolate data and clock/random sources, reproduce
with a recorded seed/order, and inspect shared-state cleanup. Keep intentional
steps within one stateful scenario distinct from accidental inter-test order.
Retries and quarantine can be an explicit temporary owner policy, but must not
erase observed failures or masquerade as repaired regression protection.

Check whether snapshots were reviewed, important differences normalized away,
tests filtered out, exceptions swallowed, assertions unawaited, or counts inflated
by duplicate cases. Diagnose no-assertion cases by their claim: crash detection
may be valid, while claiming saved data from the same smoke would overstate it.

## Bound the conclusion

Use test-history churn or smell scanners to choose investigations, not as an
automatic defect classifier. A failed harness attempt and corrected attempt
are separate receipts. Source inspection can decisively establish a bad oracle
without a live run; do not invent execution. Missing required runtime evidence
remains a gap. Preserve failures and report the population actually examined.
