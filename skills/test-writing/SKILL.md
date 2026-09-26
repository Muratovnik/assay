---
name: test-writing
description: Write or repair automated tests for justified behavior and meaningful regression protection. Skip test execution alone, testing explanations and read-only audits.
license: MIT
metadata:
  assay-optional-skills: "code-change"
---

# Test writing

Protect the intended contract without freezing accidental implementation.
Passing tests are evidence of the assertions exercised, not approval of the
requirements or proof that the whole product works.

## Optional method boundaries

Sibling methods named in metadata supply conditional criteria, not automatic
assignments. Consult only the relevant procedure; the caller keeps its goal,
authority and result. If a peer is absent, do not silently install it or invent its rules.
Justify expected behavior independently of implementation; do not infer test applicability from an unrelated successful command.
Report a consequential missing criterion rather than claiming the full composed
method was completed. Available core work can continue without that claim.

## Establish the oracle and authority

Read the task, owner instructions, affected interface and existing test setup.
Identify the supported consumer, inputs/states, expected result and relevant
side effects. A consumer can be a person, another module or an external client;
testing behavior does not require moving every check to end-to-end level.

Justify non-obvious expectations from the requested behavior, an accepted
contract, a verified bug example or an independently checked reference. Where
possible establish these before studying the implementation. Existing code,
tests, generated documentation and model agreement are clues, not independent
authority for what should happen. Do not derive both actual and expected values
from the same production helper or reproduce an unverified algorithm as truth.
A simple reference expression independently justified by the contract is fine.

If intent is missing, separate observed behavior from proposed behavior. A
characterization test can preserve current compatibility without declaring it
correct. Label that purpose; do not silently turn a known defect into a desired
result. Resolve consequential ambiguity with the owner and continue unambiguous
in-scope work. Do not invent product rules to make an assertion possible.

Respect the requested write scope. Adding tests does not authorize production
repairs, a framework migration, dependency installation, delegation or live
data changes. Preflight test collection, imports, setup and teardown as well as
the command itself. Use task-owned fixtures and safe existing runners.

## Choose an informative set

Reuse the project's maintained framework, fixtures and relevant existing
coverage. Select the smallest boundary that exposes the protected result.
Add higher-level checks when wiring, persistence, UI composition or a real
dependency is part of the guarantee; a mocked unit test cannot establish those.

For each material behavior, name a plausible defect the assertion would catch
and a legitimate implementation change it should tolerate. Cover relevant
partitions, boundaries, error outcomes and state transitions according to risk,
not a fixed number of tests or a requirement for one test per method. Several
assertions may describe one coherent result. Avoid duplicate coverage whose
only benefit is a larger count.

For structural assertions, mocks, UI interaction, snapshots, property tests or
legacy characterization, read [boundary choices](references/boundary-choices.md).
Use only the applicable techniques; none is a mandatory stack.

For shared mutable setup, growing suites or relocated tests, read
[fixtures and suite maintenance](references/suite-maintenance.md).

## Implement without manufacturing success

Make setup, the actual action and observations distinguishable. Setup must not
perform the behavior the application is supposed to provide. Await asynchronous
work and assertions, and verify that the intended test is discovered and runs.
For negative cases, check the required rejection and absence of prohibited
effects, not merely any exception or a missing control in one UI.

When fixing a reproducible bug, ordinarily demonstrate that the regression test
fails for that bug before the fix and passes afterward. If the fix already
exists, use a known bad revision or a narrowly altered disposable copy when
safe and authorized. Never delete or revert valid user work to recreate a
test-first sequence. If no trustworthy failure control is available, describe
the narrower evidence instead of claiming demonstrated regression protection.

Adding coverage to correct existing behavior may pass immediately. Examine its
assertions and a relevant fault control when warranted; do not manufacture a
production change just to satisfy a ritual. For tests-only requests, a valid
new failing test may expose a product defect outside write authority. Report
that state without weakening the test, fixing production silently, or calling
the requested green acceptance complete.

When an old test conflicts with the change, decide whether the code, test,
contract or environment is wrong. Preserve supported compatibility. Replace
accidental constraints with equivalent behavioral protection; update obsolete
expectations only for a justified behavior change. Do not bulk-refresh
snapshots, swallow failures, skip assertions or loosen tolerances merely to
obtain a green run. An intentional, reviewed baseline change remains valid.

## Check the tests and deliver evidence

Run focused tests, relevant integration checks and owner-required gates within
scope. Check assertion failures separately from collection/setup failures,
skips and retries. For timing, randomness or shared-state risk, use controlled
inputs and repeat/order checks as appropriate; retain the failing seed or
sequence. Passing after a retry does not invalidate the first failure.

For load-bearing checks, exercise a known-invalid control and a nearby valid
control when feasible. Targeted mutation can help with missing conditions or
effects, but inspect whether the mutant changes supported behavior and whether
the intended assertion detects it. A timeout, build failure or equivalent
mutant is not clean proof of detection. Do not mutate the live subject or adopt
a campaign framework merely to use this skill.

Report the guarantees added or changed, the source of disputed expectations,
commands/results and any demonstrated failure-to-pass evidence. Distinguish
executed checks from proposed ones and disclose missing required verification.
Coverage and mutation scores describe only their measured population; they do
not certify oracle correctness. Keep the handoff proportionate to the change.

Evaluation inputs and rubrics under `evals/` are coordinator data, not runtime
instructions and must not be read while performing the user's test task.
