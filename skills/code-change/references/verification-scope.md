# Choose sufficient verification

Use when the evidence choice is uncertain, a diagnostic might become a permanent
test, or verification is expanding or repeating. Choose observations that settle
the affected guarantee. This is neither a test-count target nor an exemption from
an explicit testing request, owner gate or safety requirement.

## Start with the result and the remaining uncertainty

Identify the consumer, required behavior and relevant side effects from the working
contract. What plausible defect could leave the user's problem intact, and what
observation would distinguish it? Inspect relevant existing assertions and check
receipts before adding coverage. A changed test file, code coverage percentage or
passing command does not answer that question by itself.

Choose by consequences and uncertainty, not changed lines. A one-line permission
or persistence change can need substantial protection; a private rename can be
adequately covered by existing tests and static checks. Keep the reasoning in the
existing task when useful, not a mandatory report for each check.

## Match the evidence to the guarantee

| Remaining need | Useful choice |
| --- | --- |
| Existing checks already discriminate the affected behavior | Reuse that coverage; run or reuse receipts according to their relevance to the current candidate. Do not duplicate it to show test activity. |
| A supported behavior or known bug lacks regression protection | Add or repair a test at the smallest boundary that exposes the defect. Use [test-writing](../../test-writing/SKILL.md) for the independent expectation and assertions. |
| The cause, installed API or environment is unknown | Use a bounded diagnostic observation to decide the repair. Keep a permanent test when it protects a continuing guarantee, not merely to preserve every investigative step. |
| Wiring, persistence or a real dependency is part of the promise | Exercise that consumer boundary. Mock-only success or compilation cannot substitute for the promised effect. Pure local behavior need not acquire end-to-end testing. |
| No meaningful new test obligation remains | Make no new test; perform the applicable existing/static/manual checks and mandatory gates. Verify their relevance rather than declaring the change too small to check. |

These choices can combine. An integration regression may need both an existing
unit suite and a new boundary check. A diagnostic can legitimately become a
regression test. Exact names, structure or call order can be supported contracts;
do not weaken their tests just because they inspect structure. Quality of a new
assertion stays with test-writing, not a second oracle policy here.

A temporary reproducer follows [diagnostic reproducers](diagnostic-reproducer.md).
Installed or generated runtime stages follow [runtime boundaries](runtime-boundaries.md).
Read those only when their boundary matters. Reuse safe project tools and resources;
choosing evidence grants no installation, live-data change or broader write scope.

## Expand only for a reason; stop only with sufficient evidence

After a relevant input changes, identify which receipts no longer apply. A shared
contract, check configuration or dependency can invalidate more evidence than the
edited file suggests. Refresh that evidence and retain still-valid results. A
known failed check needs diagnosis of code, test, contract or environment; an
unchanged retry does not erase the failure.

Before reusing a recorded result, identify the required command and guarantee,
checked subject, input population, relevant environment and observed outcome.
Use an existing receipt mechanism when available; no new logger or mandatory
wrapper is needed. A comparison of named file bytes can reject stale evidence,
but cannot discover an omitted dependency or establish oracle relevance. Include
newly relevant files and account for configuration, interpreter, dependencies and
external state. A commit of unchanged tested bytes alone is not invalidation.
A missing or unverifiable receipt is not a passing check; neither should an
unrelated edit force all checks to rerun. Keep the original receipt unchanged.

Once the affected guarantees and required gates have adequate evidence on the
current candidate, continue to the requested delivery. Broaden or repeat checking
for a new relevant change, observed failure, concrete unresolved concern or owner
requirement. Investigating nondeterminism with controlled repeats can be useful;
repeating a stable gate for reassurance is not additional coverage.

Before reporting completion, compare the original outcome with what the checks
actually establish. For example, an export helper's unit test cannot establish
that the public command calls it; a tested computation need not exercise an
unrelated interface. Inspect the relevant caller or exercise that boundary where
needed. Do not silently narrow acceptance to the most convenient passing check.

When a necessary runtime or external check is unavailable, use a suitable available
route if one exists and report the remaining unverified guarantee precisely.
Mock results may establish a narrower fact, not the missing integration result.
Continue independent authorized work without manufacturing success, repeatedly
retrying an unavailable service, or dropping a required deliverable.
