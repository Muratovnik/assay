# Executable evidence examples

Evaluator-only synthetic fixtures. These exercise browser observations and selected
oracles, not an agent's discovery, design ability or repair of a production app.
They do not replace the supplied-fact corpus or its rubric. Do not expose this
folder, fault variants or assertions to an executor in a supposedly blind trial.

## What is implemented

| Source distinction | Executable slice | Limit |
| --- | --- | --- |
| C105/C106; P9 | Replaced-object Cancel, lost-object and Clear-only faults; inline Cancel; two explicit empty-workspace policies | Synthetic single-screen state, not the historical product run or every departure |
| C17/C18 | Immediate Add/reveal versus a silent offscreen editor and an intentional feedback/open path | Keyboard route and application focus are checked before a repairing helper action |
| P3; C47/C48 | Save while a supporting panel stays open; an obstructing layer; a valid modal prerequisite | Real pointer and keyboard completion on valid variants, not all layer compositions |
| P1 target-switch variant | B finishes before A; the old result must not be attributed to B | Controlled service promises, not transport, same-context refresh or calculation-path qualification |
| P3; C103/C104 | A neighboring panel changes available width without resizing the viewport; draft and completion survive | Fixture-specific compact layout, not a universal breakpoint/layout rule |
| State-specific axe | Hidden faulty control is absent from the initial scan, then detected after opening; labeled control is valid | Only the explicitly selected button-name rule; no full accessibility claim |

`browser.test.mjs` checks real Chromium interactions and outcome assertions.
Known-bad variants must fail the named outcome assertion (`ERR_ASSERTION`); a
launch/selector/timeout error is not accepted as defect detection. The fixtures
are loaded as local HTML, with no external navigation or live data. The async
fixture controls a service promise rather than injecting the rendered result.

`evidence.test.mjs` checks metadata, deduplication, narrowly scoped waivers,
expiry, inconclusive results and adapter error propagation. Its fake builder
qualifies adapter wiring only. `axe.test.mjs` separately uses the real
`@axe-core/playwright` engine; missing dependencies fail rather than silently skip.

The previous P9 specification's no-header empty state is one fixture policy,
not a requirement on every product. C105's rubric does not require header absence
and remains unchanged; it still rejects loss of the replaced object and Clear
as a substitute for Cancel. Both hidden and disabled duplicate Add controls are
exercised here, with a working first-object submit.

## Run

Source validation remains the repository's existing three commands. This optional
qualification uses Node's built-in test runner plus Playwright, not a new product
framework. Do not install node_modules in the canonical skill or linked client
projection. Copy the skill into a disposable directory and install dependencies
there, preserving the `assets/playwright` and `evals/browser` relative paths.
The [workflow](../../../../.github/workflows/ui-evidence.yml) performs exactly that
with explicit dependency versions and no dependency lifecycle scripts.

In that disposable copy, with the dependencies installed above it:

```text
node --test skills/ui-delivery/evals/browser/evidence.test.mjs
node --test skills/ui-delivery/evals/browser/browser.test.mjs
node --test skills/ui-delivery/evals/browser/axe.test.mjs
```

By default Playwright uses its managed Chromium. `UI_TEST_CHROMIUM` can name an
already installed browser; record its actual version and do not call that the
same environment as CI's pinned Playwright distribution. No browser is downloaded
by the tests themselves. The CI workflow explicitly installs its browser.

The source-fingerprint command has independent standard-library tests:

```text
python -m unittest tools/test_ui_context.py
```

## Evidence from authoring this change

On Linux, Node 22.16.0, the available Playwright core
`1.57.0-beta-1764944708000` and system Chromium `144.0.7559.96`, the local browser
suite passed 19 cases, including the deliberate fault controls. Eight pure-JS
adapter/triage tests and four Python source-fingerprint tests also passed.
These are counts of executed tests, not a quality score or an improvement estimate.

The initial attempt to navigate to a synthetic hostname was blocked by the host
before any UI assertion. The fixtures were changed to local HTML and controlled
service promises, then rerun; no browser security policy was changed. This is a
harness correction, not an application bug or an additional passing experiment.

The real axe integration was not executed locally: its package was unavailable
and external package downloads were unavailable in the authoring container.
The separate integration test and CI job are provided, but their existence is
not a pass. CI uses different, explicitly pinned versions and must be inspected.
The full repository source-validation commands were not run locally because the
private repository could be read through the connector but not cloned into the
container. The existing `Check` workflow remains unchanged and authoritative.

No old/new agent comparison, automatic skill-discovery trial, real-product UI
acceptance, cross-browser evaluation, screen-reader check or visual approval was
performed. The composition pilot remains opt-in and unqualified. The source
fingerprint tool proves only named-path/byte identity, not context-search benefit.

Promote a relevant case into an actual product's existing fixtures only after its
policy, state and data owners are established. Preserve the fault and valid
control; do not claim these known regression examples are held-out data.
