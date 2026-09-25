# Contract-drift integration evaluation

Coordinator material, not runtime instructions. These 36 synthetic inputs cover
18 decision families across maintenance, planning, audit, UI and test review.
They are stored with maintenance because the integration follows a maintenance
outcome through its consumers; `skill_name` is the existing packet format's
corpus identity, not an instruction to activate maintenance for a read-only task.
No new evaluator, executor, dependency or production policy engine is introduced.

## Evidence boundary

All inputs and rubrics were authored and visible during development. They are
not unseen holdouts. `contract-drift-cases.json` contains only task input;
`contract-drift-rubric.json` retains method choices, family mapping and semantic
criteria for the coordinator. The executor must not see the rubric, this protocol,
the transfer record, sibling cases or the full source checkout during a blinded
run. Packet preparation alone does not enforce that filesystem boundary.

`tools/test_contract_drift.py` checks data separation, paired input integrity,
existing packet preparation and intentionally faulty synthetic gate examples.
The examples are subjects to review, not recommended production checkers. Their
expected failures and false successes must remain distinguishable from setup
errors. Passing these tests proves neither a corrected project gate nor improved
model behavior. The methods instruct the actual project to use its own effective
configuration and safe discriminating probes.

## Prepare only the selected input

Use the existing utility in a complete Assay checkout, with an existing output
parent outside source packages:

```sh
python -B tools/eval_assets.py prepare \
  --cases skills/code-maintenance/evals/contract-drift-cases.json \
  --case drift-01-a --output-parent /path/to/task-owned-packets
```

The output supplies a fresh packet path and a manifest digest to retain outside
executor control. The task source is under `inputs/`. For the executable examples,
copy those inputs to an authorized disposable working directory and run
`python -B check.py` there. Keep the frozen original intact; verify its manifest
again afterward. These examples read only `state.json` and print a result. They
exercise synthetic state, not filesystem discovery or an actual linter.

For a selected-method comparison, explicitly repeat `--method skills/<name>` for
the relevant method roots listed in the rubric. Select the same root set from
each compared revision and hold client/model/tool settings and input bytes fixed.
The coordinator does not feed those rubric fields to the executor. Linked criteria
are not automatically copied: supply a dependency explicitly when the experiment
requires it, or record that it is unavailable. Never copy `evals/` into runtime
method snapshots or install methods in a user's global environment for the test.

Native discovery is a separate experiment: let a fresh supported client see the
normal skill inventory and the unmodified prompt, without forcing method names.
Record whether it actually selects and reads the relevant procedure. A selected
snapshot run cannot establish automatic discovery; a source link cannot either.

## Bounded paired pilot

First run deterministic checks. The proposed initial behavioral pilot uses pairs
T01 (decision authority), T06 (visual ownership) and T13 (broad versus narrow
review): six inputs against baseline and candidate, twelve sequential runs total.
This is a proposed starting budget, not an automatic campaign or a required run
count for every change. Execute only with available tools and an authorized budget.
Do not expand to parallel models, install a harness or repeat until a desired pass.

Baseline is the prior bytes at
`8367566419ee0f4ddb8403514d15b1a251beabcf`, which includes the planning dependency.
Record the actual candidate commit, client/version, observed model and effort,
selected method roots, permitted effects, input/manifest identity and any relevant
runtime differences. Keep the two arms blind to each other's outputs; vary order
without changing task conditions. A revised candidate is a new comparison, not a
retry to erase failure. Unknown subscription/quota costs remain unknown.

Grade source-grounded decisions and allowed effects using the separate rubric.
Do not award points for particular wording, naming the rule or reading a file.
Record missed material violations, false rejection of permitted alternatives,
unresolved authority, unsupported evidence claims and the actual scoped result.
Do not reduce every input to "must find a bug": T14-b, for example, requires an
unresolved authority finding rather than an invented violation; gate controls can
be permitted inputs to a generally insufficient gate. Keep that distinction.

If both arms pass, no improvement is established on that input. If both fail,
revisit the causal explanation or responsible layer. A candidate that detects the
complaint but rejects its lawful neighbor has not met the intended change.
Structural pass, discovery, selected-method outcome, comparison and production
transfer remain separate evidence categories.

After the first comparison, a separate author can prepare new combinations not
used in development, for a separately bounded budget. Do not call existing cases
holdouts or claim generalization before that work is actually done. Follow-up
could combine scope evolution with stale library versions, or exact transfer
with an incomplete official kit; these suggestions are already exposed and are
not themselves held-out test data.

## Requirement coverage

| Families | Protected distinction | Primary procedure owner |
| --- | --- | --- |
| T01-T04 | Decision source, delegated authority, scope evolution and current task | Planning scope and continuation; maintenance consumes these criteria |
| T05-T07 | Import/placement versus actual behavioral and visual ownership | Maintenance reuse; component system |
| T08-T12 | Exclusions, identity, baseline authority, terminal state and coverage | Effective quality checks; test-audit discriminating probes |
| T13-T14 | Subject-driven audit coverage and independently justified criteria | Independent audit and bounded review |
| T15-T16 | Observed UI versus target basis; version-specific design/code mapping | Design transfer and component system |
| T17 | Revisit changed premises without needless migration | Maintenance reuse and planning continuation |
| T18 | Authored fixtures versus actual behavior and cost evidence | Skill-design research/transfer and test-audit |

For all T08-T12 inputs, the toy checker is intentionally incomplete. The unit suite
asserts the observed response and the independent contract fact that makes that
response permitted, a false acceptance or a false rejection. It is not an automatic
grader of a future executor's review, and no test asserts instruction keywords as
proof that a model followed the method.
