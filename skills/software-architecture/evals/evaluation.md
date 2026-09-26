# Architecture evaluation protocol

Coordinator material, not runtime instructions. The case/rubric pair uses the
existing `tools/eval_assets.py` protocol. No new model runner or scoring service
is introduced. Input files contain briefs and subject evidence; grading criteria
remain in `rubric.json`. Examples under `references/` are teaching material, not
an independent test set or evidence of successful deployments.

## What is being checked

`cases.json` has 21 authored decision cases and nine discovery cases. They cover
proposal/implementation authority, proportionality, common policy versus similar
syntax, single-consumer lifecycle, request state, dynamic discovery, public
exports, effective coverage, dependency edges, debt baselines, conditional FSD,
physical versus actual architecture, deployment and evidence claims. DISC-plan
separates sequencing adopted boundaries, which belongs to implementation planning,
from choosing them.

Each rubric allows semantically equivalent boundaries, paths and interfaces.
Assess the protected contract, consequence and counterexample, not preferred
folder names, report length or architecture vocabulary. A clean scoped audit is
valid. Evidence fidelity, authority and actual delivery are separate from whether
a proposal sounds plausible.

The existing audit corpus already covers generic migration and source-preserving
review. Architecture-specific consumer cases live in this pair rather than
renumbering or converting that file-backed corpus. Its snapshot-link integration
test adds the new criteria root. Do not read legacy expected outputs as task input.

## Freeze the intended route

For a direct design case, prepare only the architecture method and the case:

```sh
python -B tools/eval_assets.py prepare \
  --cases skills/software-architecture/evals/cases.json \
  --case ARC-03-invariant --output-parent <existing-scratch-directory> \
  --method skills/software-architecture
```

For implementation cases, explicitly include `code-change` and architecture.
For independent review cases, explicitly include `independent-audit` and
architecture. Include other linked criteria roots only when the selected task
needs them; recording an explicit set does not prove automatic skill selection.
The preparer copies runtime snapshots, not rubrics, previous responses or eval
scripts. Retain its manifest digest outside the executor packet. Reading access
must be enforced by the external executor; a fresh directory is not a sandbox.

A discovery run uses an input from `discovery_cases` without naming the expected
skill or exposing the rubric. Use the ordinary installed catalog and capture
what was actually loaded. Separately exercise direct design, planning,
implementation and read-only review; the same method has different consumers and
authority.

## Bounded comparison, when execution is available

Start with the two opposite ARC-03 cases and two opposite ARC-04 cases. Compare
four identical tasks against frozen prior behavior and the candidate: eight
responses, sequentially, under comparable model/settings/tools/permissions.
This is an optional proposed pilot, not an executed benchmark or a mandatory
quota. If routing failed first, diagnose that layer before measuring decisions.

The prior version has no standalone architecture method: freeze the relevant
prior maintenance/audit criteria or an ordinary-authoring baseline and disclose
the choice. Do not label candidate bytes with an old revision. Both conditions
must receive the same briefs and any technology evidence. Record source and
packet digests, invocation route, observed reads/writes, decisions, corrections,
failures and available actual usage. Do not infer subscription savings from words.

No supplied case is claimed to be an unseen holdout; all have been authored and
inspected. A future generalization needs a fresh reserved variant before tuning.
Do not rerun an unchanged case until a desired answer appears. A tiny pilot cannot
establish universal gains, model portability or automatic discovery on all clients.

## Delivery evidence

`tools/test_software_architecture.py` and the existing gates check registration,
input/rubric integrity, explicit consumer snapshots, links and packet isolation.
These are structural and tooling checks, not evaluations of a model's judgment.
Keep runtime results and comparison receipts outside canonical source. The PR
reports actual commands and hosted checks independently from unexecuted client
runs. Use distinct claims: authored, structurally checked, discovery observed,
behaviorally exercised and comparison-supported. Missing model runs do not become
successful runs merely because the package or CI is green.
