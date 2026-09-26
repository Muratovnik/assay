# Evidence, states and safe observation

Use when attributing behavior, deciding whether two views are different states,
or preparing captures. Keep source authority and verification level independent.

## Model what changes the task

A scenario has a goal, actor, prerequisites, entries, steps, branches and terminal
outcomes. A screen has a purpose. A state adds conditions that change available
actions, their meaning, results or recovery. An action names its real element,
availability, affected object/scope and observable effect. A transition connects
before-state, action or system event, condition, after-state and result. These
are things to explain in the handoff, not a serialization schema to implement.

Treat system events separately from controls: scheduled completion, session
expiry or a late response may change state without a click. Do not invent a
button for such an event. Preserve unchanged-state actions and different actions
sharing endpoints. Reuse one action identity on several screens only when its
meaning, scope and effect really agree; otherwise describe the contextual actions
separately. A common label alone does not establish shared behavior.

Selection of another interchangeable record need not create a distinct state;
a record with different permissions or validation may do so. For consequential
actions explain what changes or stays unchanged, pending/partial failure, retry
and exit/return as applicable. A parent Save and panel Apply may have different
scopes. Do not infer persistence, propagation or undo merely from a label. Use
[UI acceptance](../../operations-ui-delivery/references/scenario-testing.md)
when judging correctness rather than duplicating those criteria.

## Keep claims and evidence separate

Distinguish observed, intended and proposed behavior. For a material claim, record
its sources, whether it was executed, read, unverified or blocked, and unresolved
conflicts. Source types include adopted requirements, documentation, code, runtime
observations and inference. Reading a test or handler is not execution. An intended
outcome needs an adopted requirement, not a screenshot of different behavior.

Keep source revision/location and relevant data, permissions, entry path and
runtime/build with the observation. A screenshot supports the visible state;
a trace or action/result observation supports behavior. A filename, HTTP success
or toast does not alone prove committed data. An old trace is not automatically
applicable to the current build. Retain its revision and say what needs rechecking;
an older adopted requirement need not share the application's version.

Keep implementation/documentation disagreement explicit. Neither code nor
recordings automatically settle correct behavior. Inferred scenarios remain
provisional until grounded; useful source-only work need not claim verification.

## Capture with the existing browser setup

Use the available Playwright/browser connection and the project's existing
fixtures. Read [browser checks](../../operations-ui-delivery/references/browser-checks.md)
for readiness, virtualized/lazy content, before-helper observations and capture
scope. Use the tool's supported screenshot mechanism; do not write a capture or
image-export pipeline. A fixed sleep or network idle is not universal readiness.

Keep existing screenshot attachments and available traces with the scenario.
Use Playwright's existing [Trace Viewer](https://playwright.dev/docs/trace-viewer)
for inspection; where a test report is needed and Playwright Test is in use,
use its [built-in reporter](https://playwright.dev/docs/test-reporters#html-reporter).
Do not create a custom report or mandate recording every action for a small task.
A browser connection need not have Playwright Test or its reporter installed.

Associate the image or attachment with the state, build, viewport/region,
readiness and capture moment. Use the existing artifact identity/path; no custom
manifest or hash checker is required. Open menus and dialogs through a supported
path when claiming reachability. A fixture, component story or mocked failure
is labeled simulated and cannot prove ordinary runtime behavior. Missing captures
get explicit placeholders, never invented screenshots.

Label BEFORE or AFTER only when timing is known. An unchanged-state copy/download
needs an action/result observation; the image alone cannot establish its moment.
Create editable callouts in the requested design artifact, linked to named actions
and the specific image. Replacing that image requires rechecking their placement.
A region screenshot must not imply the whole document was inspected.

## Bound effects and publication

Identify consequential actions before exploring: deletion, payments, invitations,
account changes, updates, device configuration, delivery or secret rotation.
Use only authorized disposable resources. Source analysis can explain a dangerous
action without executing it. Masking an image after a live action cannot undo it.

Review screenshots, DOM, traces, locators and text for secrets and private records
before sharing. Subscription URLs, device addresses and identifiers can appear
outside password fields. Prefer safe demonstration data and existing redaction
capabilities; never upload raw traces automatically. A recorded redaction decision
is not a guarantee that all secrets were detected.

The map does not authorize source-code edits, installing vendor tools, changing
client settings or additional sharing. Honor the actual artifact destination and
publication permission; use existing authorized connections within that scope.
