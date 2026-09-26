# Prepare a behavior handoff for a redesign

Use [product-flow-mapping](../../skills/product-flow-mapping/SKILL.md) with the
existing product and the requested audience/format. For example:

> Reconstruct the current Routevane user journeys for a designer. Inspect the
> documentation, routes, controls and available runtime without changing the
> app. Relate each task and action to its screen/state, result, alternatives and
> evidence. Use the existing Playwright/browser setup for actions and screenshots,
> and the existing Figwright adapter to build adjacent editable description and
> screenshot frames in the authorized Figma file. Include an overview and reverse
> index. Keep existing behavior, adopted intent and redesign proposals separate.
> Do not create an exporter, intermediate schema or another application. Do not
> send rules to real devices or expose subscription secrets. State unavailable
> observations or writes without inventing a replacement delivery system.

A repository URL alone supplies no running application or target Figma file.
Inspect available project context and connected tools first. While runtime or
canvas access is missing, useful source-backed descriptions can still be prepared;
they are not verified behavior or completed Figma work.

## Work through existing tools

Start with requirements and the actual navigation/control owners. Maintain a
compact inventory in the existing task notes, then connect tasks to actions,
results and important alternatives. Use the optional
[scenario writing aid](../../skills/product-flow-mapping/templates/scenario.md)
only where it helps; no custom JSON format is required.

Use the existing browser/Playwright connection and project fixtures to exercise
authorized paths and capture the relevant states. Retain actual attachments and
available traces; use Playwright's built-in Trace Viewer or existing test report
when needed. Follow the existing
[browser checks](../../skills/operations-ui-delivery/references/browser-checks.md)
for capture readiness and evidence limits. A trace/report is not a design handoff.

For Figma, use the existing
[Figwright procedure](../../skills/operations-ui-delivery/references/figwright.md)
and the installed vendor instructions. Confirm the destination, build a description
frame and an adjacent screenshot frame, add editable numbered callouts and connect
steps. Read back nodes and inspect the composed result. Reuse existing nodes and
preserve manual comments on updates; do not insert an HTML export/import stage.

If the relevant tool is unavailable, retain the descriptions and any genuine
captures in the requested conversation or existing document, and name the remaining
gap. Do not auto-install a tool, change the product or write a replacement exporter.

## Routevane first slice

A starting scope from the product documentation is lists/categories -> profile ->
output formats/forecast -> build -> obtain the result, plus a failed refresh that
preserves the previous published output. The
[Routevane README](https://github.com/Muratovnik/routevane/blob/main/README.md)
is a starting source, not an executed or exhaustive inventory. Check its current
source/build before attributing live behavior. Building, downloading and sending
to a device are different actions; consequential execution requires authorized
disposable resources. A blocked action must not be silently simulated.
