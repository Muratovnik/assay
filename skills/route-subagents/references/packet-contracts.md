# Assignment packet examples

These examples describe the assignment sent by the primary to a worker. Their
layout is optional: use the fields that control the actual boundary. An advisory
question can be a short paragraph; complex writers and reviews benefit from an
explicit record. The worker's final result follows the separate
[required result template](outcome-and-repair-contracts.md#required-result-packet).

## Contents

- [Fields](#fields)
- [Skills and authority](#skills-and-authority)
- [Returns](#returns)
- [Waiting for a long run](#waiting-for-a-long-run)
- [Resumed, review and repair packets](#resumed-review-and-repair-packets)
- [Packets for interface work](#packets-for-interface-work)

## Fields

```text
Outcome / question and original objective:
Delegation purpose and expected use of the result:
Why delegate now; dependency or reconsideration trigger when deferred:
Primary-owned work while this runs (or why sequential isolation is useful):
Expected effect: change_required | no_change_acceptable | read_only_finding
Relevant root, base or snapshot, owned dirty inputs:
Selected model and reasoning effort, brief task/quota rationale:
Assay skills the work needs (or none), loaded before the work:
Read scope, owned paths/hunks and runtime write set:
Shared decisions, dependencies and reserved generated outputs:
Acceptance evidence and permitted checks:
Excluded actions and escalation conditions:
Useful return and evidence pointers:
Return budget, where details and long command output go:
```

These are assignment/plan notes, not additional routing API parameters. Follow
[delegation planning](delegation-planning.md) when the split or timing is unclear.
Finalize relevant notes in the execution prompt before preparing the route;
never append them to an already authorized immutable launch input.

## Skills and authority

Name the Assay skills by the packet's own work, not the primary's: a code
worker gets `code-change`, a reviewer `independent-audit`, a test writer
`test-writing`, an interface worker `ui-delivery` with the procedures
[below](#packets-for-interface-work). A worker starts with none of the
primary's loaded skills or its per-request skill check, so a packet without them
leaves the method to chance.
The worker loads each named skill before the work, may add another its work
needs, and names each Assay skill it loaded on the first line of its report, for
example: Used `assay:code-change`. The worker does not read this skill, so the
packet states the instruction with that example. An exact output format the
packet fixes, such as a structured result, takes precedence over the line.

Record model and effort with the launch even when inheritance implements the
selection; no model matrix is needed. Explain ordered implementation steps only
when their order matters.
Distinguish decisions the worker must preserve from local choices it can make.
The worker must not spawn additional agents or change task/memory coordination
state; the primary owns those decisions. Write ownership alone grants no
publication, installation or external-action authority.

## Returns

Use the result template to report the typed outcome, delivery evidence,
executed checks, source identity and unresolved issues.
Report incidental effects instead of asserting unchanged state from final
file hashes alone. A stopped process and a successful assignment are different.

Keep returns compact enough for their named consumer: result, changed boundary,
decisive evidence pointers, unresolved assumptions and next dependency. Retain
large logs in the permitted evidence location instead of forwarding them through
every packet. The worker does not read this skill, so the packet states the
budget: by default about 1,500 tokens for the final message, which carries the
findings, with longer detail in a file in the permitted evidence location that
the return names. The packet has that file named for its content, not as a report
or summary, because some clients refuse a worker's file named that way; see
[Claude Code](claude-code-routing.md#files-a-subagent-writes). The primary
reads that file only when a decision needs it, and asks for a longer return when
the decision depends on it. Without a stated budget, the median final message in
one 129-worker session ran from 9,000 to 23,000 characters by class.

The packet also tells the worker to send long command output, such as a build,
test run or log read, to a file and keep only the lines it acts on: a worker
re-reads everything in its context on every call. In the same session, file reads
through the shell, whatever the target, were 37 % of worker tool output. A later
measurement of that class found about 18 % of it was logs and results; most of the
rest was source and documents.

## Waiting for a long run

When the worker will wait for a long run, such as a build, a test round or a
benchmark, the packet tells it how to wait. Some clients wake the primary every
time a background worker stops while its own work still runs, so each event the
worker waits through costs a primary turn. The worker therefore waits for the
events it acts on: the run's end, whether success, failure or a deadline, and
not a stream of progress lines. A worker that acts on each event, for example by
stopping a run at its first failure, keeps a stream filtered to those events. It
hands back only when the work is done. A periodic wake that keeps the worker's
prompt cache alive can cost less than letting the cache expire; when that
matters, the packet names the interval. In one session a progress stream every
20 seconds woke the primary 7 times in 2 minutes for one worker. The worker does
not read this skill, so the packet states the instruction; the client mechanics
and the cache trade-off are in
[Claude Code](claude-code-routing.md#waiting-inside-a-background-worker).

## Resumed, review and repair packets

For an interrupted or resumed assignment, use
[planning continuation](../../implementation-planning/references/continuation.md)
to reconcile current bytes, completed effects and present authority before replay.

For review add the role-required mode, original brief, frozen contracts,
candidate identity, scoped risk and receipts for primary-owned stateful gates,
and ask for the files, hunks and receipts the reviewer actually read; the
[result rules](outcome-and-repair-contracts.md#required-result-packet) say how a
no-finding return without them counts. Do not supply the preferred verdict. For a finding repair send its location,
observed/required behavior, affected diff and named control, preserving the
unchanged authority and contracts.

## Packets for interface work

A packet that changes a rendered interface names `ui-delivery` and the
procedures its task needs from that skill's
[routing table](../../ui-delivery/SKILL.md#select-a-thematic-procedure): the row
the task matches and the row of each symptom the owner's complaint names, such
as a hanging second line, a ring left after a click or a list that blinks on
refresh. Naming them does not stop the worker from opening another procedure its
work shows it needs. Quote the complaint in the owner's words: a paraphrase into
a fix, such as "move the dot 4 px left", drops the symptom the worker routes by.

The packet asks for measured values with their widths and states, as the skill's
[measurement section](../../ui-delivery/references/visual-judgment.md#measure-alignment-instead-of-judging-a-screenshot)
describes, and for the consumers the defect class reaches, as its
[finish](../../ui-delivery/SKILL.md#common-execution-and-finish) describes; a
screenshot the worker judged itself does not establish alignment. A packet
without an interface follows only the rules above. A review of an interface
change follows [review and continuity](review-and-continuity.md#review-an-interface-change).
