# Two handoffs from one scenario description

This is a synthetic collection-editor example, not an observation of a real
product. Keep it as ordinary text or existing Figma frames. Neither consumer has
been exercised by a fresh agent run merely because this example exists.

## Shared source and scenario

`REQ` is the supplied example requirement: saving succeeds only when the new data
is committed; failure retains the draft and permits retry; cancellation leaves
committed data unchanged. `CODE` is an example source observation: Copy link and
Download do not change the visible collection. No runtime or capture is supplied.
These names identify the example's sources, not invented real repository files.

| Scenario / step | Before | Action or event | Result / after | Basis |
| --- | --- | --- | --- | --- |
| EDIT_FLOW / OPEN | VIEW | Edit | DRAFT is available for input. | Intended from REQ; not executed. |
| EDIT_FLOW / ABANDON | DRAFT | Cancel | VIEW; committed data unchanged. | Intended from REQ; not executed. |
| EDIT_FLOW / COMMIT | DRAFT | Save | PENDING; completion still awaited. | Intended from REQ; not executed. |
| EDIT_FLOW / SUCCESS | PENDING | Save completes | VIEW with committed changes. | Intended from REQ; not executed. |
| EDIT_FLOW / FAILURE | PENDING | Save fails | ERROR; entered input remains. | Intended from REQ; not executed. |
| EDIT_FLOW / RETRY_SAVE | ERROR | Retry | PENDING with the retained draft. | Intended from REQ; not executed. |
| EXPORT_FLOW / COPY_RESULT | VIEW | Copy link | Clipboard changes; visible state unchanged. | Source-read CODE; not executed. |
| EXPORT_FLOW / DOWNLOAD_RESULT | VIEW | Download | Download requested; visible state unchanged. | Source-read CODE; not executed. |

## UI redesign acceptance

Consumer: operations-ui-delivery. Use EDIT_FLOW / FAILURE and its adopted source
REQ. Preserve entered input on failed Save and the retry/cancel outcomes, not the
old panel arrangement. The designer may replace or combine screens.

In the requested Figma file, put this step explanation beside the matching capture
through the connected design adapter. Here no image is supplied: mark it not
captured rather than manufacture a screenshot. An authorized application check
can later obtain that state with the connected browser tools. Label a simulated
failure fixture as such.

## Regression-test design

Consumer: test-writing. Use the same FAILURE step, but justify the expected retained
input with REQ, not a handler or the map author's verdict. Set up a valid draft,
start Save through the relevant boundary, and use the project's existing failure
fixture to check retained input and the supported retry. Exercise the successful
or cancelled nearby case as appropriate. Do not freeze an input-loss bug as intent.

Reuse the existing test runner and fixtures. Reading CODE or this table is not an
executed test. The test-writing method selects the smallest boundary that exposes
the promised result.

## Reverse lookup and updates

VIEW belongs to EDIT_FLOW and EXPORT_FLOW. Copy and Download have different effects
even though both leave the screen unchanged; keep both descriptions. A Save test
alone says nothing about clipboard/download behavior.

Preserve a designer's note beside EDIT_FLOW / FAILURE when updating descriptions
or screenshots. Use the existing frame identity and tool readback. Recheck
consumers after a shared action changes and retain any unresolved source conflict
in the actual deliverable.
