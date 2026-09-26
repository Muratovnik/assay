# Evaluation protocol and evidence boundary

Evaluator-only material for developing the method, never executor instructions.
The paired corpus specifies behavior; its presence and passing structural tests
are not executed model runs. All published cases were visible during development
and are regression examples, not an unseen evaluation set.

## Prepare a bounded case

Use the existing `tools/eval_assets.py prepare` with `cases.json`, one case ID and
an evidence directory outside canonical source. The preparer writes named inputs,
the prompt and optional explicitly selected method snapshots, with a digest. Keep
rubric, other cases, earlier answers and result traces out of executor inputs.

The schema uses `id`, `prompt`, `context` and optional inline `files` for inputs;
`required` and `reject` are coordinator-only grading fields in `rubric.json`.
Discovery uses `expected_methods` and `avoid` there, not in input metadata.
Source code and tests that are part of the user's fixture are ordinary task
inputs, distinct from this grading key.

### Separate frozen evidence from the editable subject

The returned packet is an immutable control, including `inputs/`, method snapshots
and the manifest. Retain its digest outside it and verify it before and after the
run with the existing audit packet verifier. Do not execute an edit inside that
packet: a legitimate repair of `inputs/adapter.py` would fail byte-integrity
postflight. Do not regenerate the manifest to conceal those changed inputs.

For a local execution case, copy only `packet/inputs/` into a fresh sibling working
directory, using ordinary file copies, not hard links or symlinks. The coordinator
can use `shutil.copytree(packet / "inputs", workspace)` with a new destination.
Preserve fixture-relative names; paths in the prompt refer to this working copy.
Verify that its initial bytes match the frozen inputs, and use it as the task's
working directory. Give the executor the unchanged prompt/context and the selected
runtime methods. Keep outputs and traces outside the frozen packet. Reuse this
same setup for each configuration, with a fresh working copy on every run.

Afterward, verify the frozen packet with the original retained digest, then inspect
the working copy's changes and actual command results against the case's permitted
paths and required behavior. These are separate checks: immutable input integrity
must not reject authorized output changes, while a correct output must not excuse
changed input evidence or out-of-scope writes. Final byte equality cannot exclude
transient writes. Record effective read/write boundaries and missing trace evidence;
a copy and an instruction do not establish enforced isolation.

### Match the evidence mode to the case

RDC-02, RDC-03, RDC-06 and RDC-10 are local execution cases with complete inline
subjects. Their required results include actual permitted edits, not merely a plan.
RDC-01 uses the same adapter inputs as RDC-02 but permits only a plan: no edits or
test execution. Other task cases are explicitly synthetic decision exercises.
They ask for a justified next action, decision or handoff from supplied observations,
not invented execution on an absent repository. Their rubric actions are prospective.

RDC-06 contains a partially repaired adapter and its selected U1/U2 plan so continued
work can preserve U1 while finishing U2. RDC-10 contains the faulty adapter, original
passing but insufficient test, contract and review context. Inspect the resulting
regression tests as well as the repaired behavior; a candidate must not get credit
for only rephrasing F1. The coordinator can use the known/unknown/similar-ID contract
from RDC-02 to challenge RDC-10's result outside the executor's packet. The skill
case is an authoring exercise: source edits and self-review are not fresh behavioral
runs of that authored skill.

Publication exercises assess reasoning about identity, replay, capability and
completion. They supply no live credentials, repository or publication tool and
must not be graded as live integration runs. Missing execution capability in a
local execution case is a confounder, not permission to invent success or silently
substitute a decision-only score. No new runner, Git client, paid campaign or
publication emulator is introduced by this corpus.

### Check discovery separately

Select `discovery_cases` for the activation question. To test native discovery,
use an already authorized disposable client setup with the intended method catalog
and ordinary user prompt; do not explicitly load the target skill or tell the
executor which method to select. Retain actual loader evidence and the effective
client configuration. A method-selection answer or explicit snapshot load tests a
different property. Without a qualified native setup, keep discovery NOT VERIFIED
and report any reasoning exercise separately; do not install into global roots.

## Compare against the actual current method set

For the added-method comparison, the baseline is Assay at
`28fd8817fcc408d07fbfd2ac7ad47c4fd9ae218a`, before this skill was introduced. Candidate
is the selected revision with the method and conditional integration changes. A
comparison of this review repair can instead use `3aef16cd94e480aeebe0a993bf0008eff4bfd3cf`
as its explicitly different baseline. Keep the comparison question and both source
identities in the record; "parent" alone changes meaning after another commit.

Use each revision's actual method bytes. Taking today's linked child skills and
merely removing the new directory is not the old baseline. The current coordinator
can prepare the same case input twice with `--method` paths to the respective
frozen method sets; the old preparer need not know about the new corpus. Keep model,
instructions, task inputs, tools and effective permissions comparable. Load only
relevant criteria owners, not every skill as a penalty. An explicit load tests
execution with the method, not automatic discovery.

A small initial pilot can use four tasks in both configurations (eight runs):
plan-only boundaries, local adapter implementation, affected-only continuation,
and ambiguous publication. This is a proposed budget, not an authorization or a
completed experiment. Where runs are authorized, reserve a new variant before
tuning; once inspected for tuning it becomes regression evidence. Retain failed
attempts and confounders, not only successful runs. A changed model or client is a
new condition, not evidence that an earlier result transfers automatically.

Grade preservation of the goal and qualifications, justified next action, scoped
effects, concrete verification and actual endpoint. Count necessary user
corrections and avoidable repeated work when the trace supports them. Do not use
word count, number of stages, skill invocations or formatted documents as proxies
for useful outcomes. Token or cost comparisons require observed full-chain
accounting; unknown subscription use stays unknown.

## Coverage and controls

- Plan-only versus local implementation: RDC-01/02; skill behavior versus
  executable adapter work: RDC-03/02.
- Retaining an adequate solution versus adopting a needed compatible mechanism:
  RDC-04/05; source qualification and untrusted instructions: RDC-22/27.
- Executable continuation versus a changed-premise decision: RDC-06/07; wrong
  selected subject: RDC-08; an explicitly chosen owner and one plan: RDC-23.
- Incorrect feedback versus an executable repair: RDC-09/10; ineffective oracle,
  scope expansion and refuted premise: RDC-11/12/13; loop exhaustion: RDC-24.
- Previous write authority does not authorize today's audit: RDC-14 and
  DISC-audit-only. Readiness, authority and availability are graded separately.
- Lost receipt with an observed effect versus unresolved effect: RDC-15/16.
  Changed revision versus valid requested draft: RDC-17/18; empty checks: RDC-26.
- Untried relevant capability versus concrete permission block: RDC-19/20;
  selected existing proposal and unrelated work: RDC-21.
- Complete synthetic chain through a review repair and current publication:
  RDC-25. This is a delivery-account exercise, not a native publication run.
- Concurrent head and changed integration base: RDC-28/29. Incomplete clean audit
  versus complete clean control: RDC-30/31; no finding quota in either case.
- Discovery includes full cycles, research-plus-plan, resume, isolated research,
  prose repair, read-only audit, idea discussion, code-only work, another owning
  workflow and standalone behavioral assessment.

The shared gate checks case/rubric identity and input structure. The unit suite
prepares every case, checks frozen byte integrity and key exclusion, and verifies
that adding optional method snapshots leaves task inputs unchanged. That is not a
comparison against a baseline method set. It also checks native registration,
reference targets, editable-copy separation, and executable adapter controls,
including a repair that the original green tests missed. None of these operations
grade model answers or establish independence, automatic activation, quality
improvements or savings. Report real runs and their limits separately; never turn
the corpus into a scoreboard.
