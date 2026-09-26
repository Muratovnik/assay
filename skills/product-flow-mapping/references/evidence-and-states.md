# Evidence, states and safe observation

Use when attributing behavior, deciding whether two views are different states,
or preparing captures. Keep source authority and verification level independent.

## Model what changes the task

A scenario has a goal, actor, prerequisites, entries, steps, branches and terminal
outcomes. A screen has a purpose. A state adds conditions that change available
actions, their meaning, results or recovery. An action names its real element,
availability, affected object/scope and observable effect. A transition links
before-state, action or system event, condition, after-state and result.

Treat system events separately from controls: scheduled completion, session
expiry or a late response may change state without a click. Do not invent a
button for such an event. Preserve unchanged-state actions and different actions
sharing endpoints. Reuse one action identity on several screens only when its
meaning, scope and effect really agree; otherwise describe the contextual actions
separately. A common label alone does not establish shared behavior.

Selection of another interchangeable record need not create
a distinct state; a record with different permissions or validation may do so.

For each consequential action explain prerequisites, what it changes or leaves
unchanged, pending/partial failure, retry and exit/return as applicable. A parent
Save and panel Apply may have different scopes. Do not assume persistence,
propagation, undo or navigation merely from a label. Use existing owner behavior
criteria through [UI acceptance](../../operations-ui-delivery/references/scenario-testing.md)
when judging correctness rather than duplicating them.

## Keep claims and evidence separate

Maintain three layers: observed, intended and proposed. For each material claim,
record its source(s), verification (executed, read, unverified or blocked), and
unresolved conflict. Source types include adopted requirement, documentation,
code, runtime observation and inference. Reading a test or a handler is not
execution. An intended outcome needs an adopted requirement, not a screenshot
of the implementation doing something different.

Record source revision/location and the conditions that matter: data, permissions,
entry path, runtime/build and observation scope. A screenshot is evidence of the
visible state only. Pair behavior claims with a trace or action/result observation;
a screenshot filename, HTTP success or toast does not prove committed data.
Where available, use the existing [Playwright trace](https://playwright.dev/docs/trace-viewer)
rather than creating a new recorder.

An old executed trace is not automatically applicable to the current build.
Retain its original revision and identify what needs rechecking; an older adopted
requirement or external reference need not share the application version. Never
refresh provenance merely to make a checker accept the map.

Keep conflicts explicit, including implementation/documentation disagreement.
Do not select code as universally authoritative or rewrite requirements to match
current output. Inferred scenarios remain provisional until independently grounded.
A source-supported incomplete result can be useful without claiming full verification.

## Capture the state that was actually present

For browser captures use the existing
[browser checks](../../operations-ui-delivery/references/browser-checks.md).
They own readiness, virtualized/lazy content, before-helper observations and
capture scope. A fixed sleep or network idle is not a universal readiness test.

Associate each image with its state, exact capture/build identity, viewport or
region, dimensions, readiness observation, timestamp and redaction review.
Declare whether it depicts before or after the described action. Open menus and
dialogs through a supported path when reachability is being claimed. A fixture,
component story or mocked failure is labeled simulated and cannot prove the
ordinary runtime path. Missing captures get explicit placeholders, never generated
pictures presented as screenshots.

Callouts reference action IDs, not only visual numbers. Their coordinates belong
to one image hash/dimensions; replacing an image invalidates its callouts until
checked. Keep an unmarked sanitized image plus editable annotations when useful.
An image of a scroll region must not imply the whole document was inspected.

## Bound effects and publication

Identify consequential actions before exploring: deletion, payments, invitations,
account changes, installing updates, device configuration, delivery or secret
rotation. Use only explicitly authorized disposable resources. Source-only
analysis can explain a dangerous action without executing it. Masking a screenshot
after a live operation does not undo that operation.

Review screenshots, DOM, traces, locators and text for secrets and private records
before export. Password fields are not the only risk: subscription URLs, device
addresses and identifiers can appear in status text or downloads. Use synthetic
demonstration data; do not upload raw traces automatically. A redaction flag is a
recorded human/tool review decision, not a secret-detection guarantee.

The map does not authorize source-code edits, installing vendor tools, changing
client settings or sending data to a third-party canvas. Honor the actual task's
artifact destination and publication permission.
