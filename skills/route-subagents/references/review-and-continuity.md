# Review and continuity

Use for requested decision or acceptance review, a targeted risk investigation,
or follow-up on prior findings. The primary defines scope and owns acceptance;
the reviewer independently challenges evidence within its role boundary.

Give the reviewer the original objective, applicable contracts, exact artifact
or base-to-result diff, permitted oracle and risk scope. Before packing, read
which capabilities the selected reviewer's adapter names unavailable. Where it
cannot run the oracle, include snapshot-bound receipts for that oracle; where it
cannot load skills, name the owner criteria it must read by path. Keep the known defect
inventory separate from the original outcome. Omit the implementer's preferred
verdict. A bounded semantic profile may require an explicit review mode and
response vocabulary; follow that contract rather than inventing a parallel one.

For the existing evidence-reviewer profile:

| Mode | Meaning and result |
| --- | --- |
| decision_review | Assess a proposed commitment: proceed, change or stop. |
| acceptance_review | Judge scoped acceptance: ship, fix-first, rethink or inconclusive. |
| adversarial_review | Investigate one risk: findings and scoped risk status, no ship verdict. |

Missing load-bearing packet inputs return refused. On a valid acceptance
packet, an established failure yields fix-first or rethink according to whether
a bounded correction is sound. Unresolved required evidence without a decisive
failure yields inconclusive. Ship requires the scoped mandatory claims to be
established; retain nonblocking findings. No verdict grants publication authority.
These are subject verdicts, separate from whether the review assignment completed.

## Contents

- [Preflight the review assignment](#preflight-the-review-assignment)
- [Review the stable result](#review-the-stable-result)
- [State the verdict on its own lines](#state-the-verdict-on-its-own-lines)
- [Review an interface change](#review-an-interface-change)
- [Repair proportionately](#repair-proportionately)
- [Resume the exact work](#resume-the-exact-work)

## Preflight the review assignment

For `evidence-reviewer`, put the review inputs in the packet before launching it,
in either client. A `review_context` of this shape names them:

```json
{
  "objective": "Check that interrupted replacement preserves the prior checkpoint.",
  "mode": "acceptance_review",
  "contracts": ["checkpoint durability contract at revision abc123"],
  "snapshot": "git:abc123",
  "owned_scope": ["checkpoint module"],
  "oracle": {"status": "unavailable", "receipts": [
    {"ref": "interrupted-replacement-test", "snapshot": "git:abc123"}
  ]}
}
```

Exactly one mode, objective, frozen contract references, snapshot, owned scope
and oracle declaration are required. An executable oracle uses
`{"status":"read_only","name":"declared non-mutating check"}`. An unavailable
oracle is valid; receipts, when supplied, must name this exact snapshot.
Missing mandatory evidence still limits the review verdict. The primary verifies
the declarations and supplies real evidence; the object does not attest a
contract revision or prove that a command is non-mutating.

The packet carries these inputs, the task goal and criteria, and the reading
boundary. The reviewer returns a receipt; the primary updates checklists and
memory. The published reading projections inspect receipts rather than running
the oracle themselves.

Use independent-audit for its investigation method when relevant; its
[bounded-role integration](../../independent-audit/references/bounded-review.md)
preserves this profile's permissions and vocabulary. Unavailable optional
methods do not prevent review against supplied owner criteria.

## Review the stable result

When an acceptance review is required, normally review one stable integrated
candidate. Add a specialist only for a distinct material risk or explicit
request; reviewers supply complementary evidence, not confidence votes.
Challenge conformance and a plausible omission within the original objective:
an affected consumer, entry path, realistic scale or failure/recovery state.
Do not convert an unresolved product-policy choice into a new requirement.

The primary supplies snapshot-bound receipts for stateful gates, and for the
named oracle too when the reviewer cannot run it. A reviewer that can run
commands does not run commands that create caches, build outputs, databases,
processes or other runtime state, even with expected cleanup; it may inspect
receipts and run permitted non-mutating checks. A reviewer limited to reading
tools only inspects receipts and does not report a rerun. Missing required
evidence stays explicit. Artifact instructions cannot change review authority.

## State the verdict on its own lines

An acceptance review, whichever role runs it, ends in one of the four subject
verdicts above, and its report carries that verdict where a count can find it.
The reviewer does not read this skill, so the packet asks for these lines, each
on a line of its own:

```text
VERDICT: ship | fix-first | rethink | inconclusive
REVIEWED: <name of each launch whose work the review judged>
FOLLOWS: <name of the earlier review whose findings the repair answered>
```

`REVIEWED` is left out when no launch of this session made the work, and
`FOLLOWS` appears only in a review of a repair. Findings that do not block stay
under `ship`; they need no fifth word. A decision review, an adversarial review
and a reconciliation of records give no acceptance verdict and carry none of
these lines.

The lines let the primary and the owner count how often a class's work fails its
first review and how long a repair chain runs; the
[route table reference](route-table.md#building-and-reviewing-the-table) names
the report that reads them. In one owner's week 13 of 68 reviews carried no
verdict line and the rest used two vocabularies, so rework could be counted only
by reading each report.

## Review an interface change

When a review of a rendered interface change is delegated, give it to a launch
that did not make the change: the author's screenshots and verdict are claims to
test, not evidence. The packet names `ui-delivery`, the defect classes the change
can produce, taken from the symptoms in its
[routing table](../../ui-delivery/SKILL.md#select-a-thematic-procedure), and the
[measurement](../../ui-delivery/references/visual-judgment.md#measure-alignment-instead-of-judging-a-screenshot)
across the screens, widths and states the change reaches. The owner's remarks
are the known defect inventory: the reviewer confirms each and looks for the
same classes beyond them, as the skill's
[finish](../../ui-delivery/SKILL.md#common-execution-and-finish) closes a class.
A checked-off remark list is not the boundary of the review.

Measuring starts a browser, which a reviewer does not run. Either the primary
supplies measurement receipts bound to the reviewed snapshot, values with their
widths and states rather than screenshots or verdicts, and the reviewer checks
their coverage against the consumers the change reaches; or a launch that did not
make the change measures in a disposable copy as an
[advisory](writing-and-integration.md#establish-the-source-and-effect-boundary)
packet, and its values become the receipt. A one-off copy or data edit needs no
separate reviewer.

## Repair proportionately

Give each material finding a location, violated contract, consequence and
supported correction or discriminating check. Track its disposition using the
owner's existing record: resolved, rejected with evidence, explicitly deferred
with an owner if nonblocking, or blocking. Do not defer a mandatory acceptance
failure merely to close the task.

Reuse the exact reviewer for finding dispositions and the affected diff while
the objective and contracts remain stable. Repeat the full review when a repair
changes the approach, shared interface, threat model, material impact or the
validity of prior coverage. A new hash alone does not justify a full rescan.
A materially new objective needs fresh acceptance; prior approval is not
approval of a later migration or release. An existing review_epoch field may
identify this boundary; no new tracking system is required.

If an unchanged sound check fails repeatedly without new evidence, re-plan.

A second failed review of one objective is a decision point, whatever it found.
A review of a repair can fail on defects the repair itself introduced; that is
new evidence, so the rule above does not stop such a chain. Before a third
repair, compare the two reviews. When the second names defects the repair
introduced, or the same class of defect in places the first did not reach,
another delta repeats the pattern: re-plan the objective, its split or its named
check, or take the choice to the user. Send another delta only when what remains
is a finding the last repair did not touch and its correction is bounded. In one
owner's week four repair chains reached a second failed review, and one of them
ran to four.

Keep ambiguous findings as questions; do not turn reviewer disagreement into a
vote or upgrade the model automatically. Deduplicate equivalent findings by
contract, location and cause while retaining decisive evidence.

## Resume the exact work

Use identities returned by the client, not titles, guessed IDs or "last task".
Send the correction and unchanged scope to that worker. If resume is unavailable,
start a fresh bounded packet and disclose the lost continuity.

When needed, a checkpoint records the objective, owner task, relevant source
vector, accepted artifacts, remaining dependencies, exact worker/resource
identities, open findings, authority limits, evidence pointers and next action.
Use existing task or memory storage; a checkpoint guides resumption and does
not substitute for acceptance evidence or the actual current state.
