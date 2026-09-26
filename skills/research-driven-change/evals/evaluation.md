# Evaluation protocol and evidence boundary

Evaluator-only material for developing the method, never executor instructions.
The paired corpus specifies behavior; its presence and passing structural tests
are not executed model runs. All published cases were visible during development
and are regression examples, not an unseen evaluation set.

## Prepare a bounded case

Use the existing `tools/eval_assets.py prepare` with `cases.json`, one case ID and
an evidence directory outside canonical source. Select `discovery_cases` for the
separate activation question. The preparer writes named inputs, the prompt and
optional explicitly selected method snapshots, with a digest. Verify the packet
before and after the run using the existing audit packet verifier. Keep rubric,
other cases, earlier answers and result traces out of the executor's packet.

The schema uses `id`, `prompt`, `context` and optional inline `files` for inputs;
`required` and `reject` are coordinator-only grading fields in `rubric.json`.
Discovery uses `expected_methods` and `avoid` there, not in input metadata.
Source code and tests that are part of the user's fixture are ordinary task
inputs, distinct from this grading key.

The adapter plan and implementation cases carry executable local fixtures. They
share identical starting files, but grant different effects. A coordinator can
observe whether permitted changes preserve the public interface and satisfy the
provided known/unknown/similar-ID tests. The skill case is an authoring exercise;
source edits do not establish that its behavioral instruction was followed in a
fresh run. Do not use a phrase-search test as a substitute for that distinction.

Publication cases contain explicitly synthetic recorded observations. They test
reasoning about identity, replay, capability and completion; they do not provide
live credentials, authorize real remote mutations or prove GitHub integration.
The executor must distinguish an observed synthetic state from a live operation
performed in its run. If a case needs a tool that the effective run does not
supply, retain that confounder rather than grade invented execution as success.
No new runner, Git client, service, paid campaign or publication emulator is
introduced by this corpus.

## Compare against the actual current method set

Baseline is the existing Assay methods from the frozen parent revision, not an
artificially unassisted model. Candidate is that same set with this method and its
conditional integration changes. Use each revision's actual bytes; taking today's
linked child skills and merely removing the new directory is not the old baseline.
Keep the model, surrounding instructions, inputs, tools and effective permissions
comparable. Load only the relevant criteria owners, not every skill as a penalty.
An explicit load tests execution with the method, not automatic discovery.

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
- Valid continuation versus a changed premise: RDC-06/07; wrong selected subject:
  RDC-08; an explicitly chosen owner and one plan: RDC-23.
- Incorrect versus demonstrated review findings: RDC-09/10; ineffective oracle,
  scope expansion and refuted premise: RDC-11/12/13; loop exhaustion: RDC-24.
- Previous write authority does not authorize today's audit: RDC-14 and
  DISC-audit-only. Readiness, authority and availability are graded separately.
- Lost receipt with an observed effect versus unresolved effect: RDC-15/16.
  Changed revision versus valid requested draft: RDC-17/18; empty checks: RDC-26.
- Untried relevant capability versus concrete permission block: RDC-19/20;
  selected existing proposal and unrelated work: RDC-21.
- Complete synthetic chain through a review repair and current publication:
  RDC-25. This is a delivery-account exercise, not a native publication run.
- Discovery includes full cycles, research-plus-plan, resume, isolated research,
  prose repair, read-only audit, idea discussion, code-only work, another owning
  workflow and standalone behavioral assessment.

The shared gate checks case/rubric identity and input structure. The unit suite
prepares every case, checks byte integrity and key exclusion, verifies that
baseline/candidate packets retain the same inputs, and checks native registration
and reference targets. It also exercises the adapter fixture against the original
defect, an exact-alias control and an overbroad normalization to test its oracle.
None of those operations grade model answers or establish
independence, automatic activation, quality improvements or savings. Report any
real runs and their limits separately; never turn the corpus into a scoreboard.
