# Designer handoff and paired frames

Use when delivering the map to a designer or updating an authorized canvas.
The requested format wins. One scenario can remain text; a broad redesign needs
an overview, readable step pairs and a reverse index, not a wall of screenshots.

## Organize around goals and results

Use three sections in the existing product design file or requested destination:

- Overview: product vocabulary, scope/revision, scenario groups and major paths.
- Scenarios: goal/actor/entry, then pairs for steps and consequential branches.
- Index and gaps: screen/control -> scenarios, conflicts, unverified surfaces and
  open owner decisions.

These are sections/pages, not three mandatory files. Do not construct a separate
design system or reproduce the old UI in editable components for documentation.
Raster captures are sufficient; descriptions, labels, callouts and connections
should remain editable in the destination that supports them.

Each pair has two neighboring frames. The left contains stable step/scenario ID,
purpose and prerequisites, before-state, action or system event, element identity,
availability/scope, observable result and applicable next/cancel/error links.
Name the claim layer and verification, with concise source references. The right
shows the matching state capture and numbered callouts linked to action IDs.
Label the depicted endpoint BEFORE or AFTER. With identical endpoints and no
timing evidence, label the moment unspecified rather than inventing BEFORE.
Provide a numbered legend with the action names; IDs alone are not a legend.

A large dialog or complex result can need its own pair. An unchanged-screen
copy/download still has a result description; a fake destination is unnecessary.
Shared controls can use a canonical explanation with links from actual uses.
A useful crop is acceptable when linked to its parent screen and labeled as a
region. A missing image is an explicit not-captured state, not a silent blank.

Keep existing behavior separate from intended constraints and redesign proposals.
A designer may replace navigation or combine screens while preserving outcomes;
current screenshots are not a fidelity requirement for a redesign. Do not draw a
continuous current-product path by splicing observed, intended and proposed
transitions. Show cross-layer relations separately from next-step connections.

Keep screen purposes, state conditions and every action's role/effect/scope in the
reader-facing index, including inventoried controls without a mapped scenario.
The JSON containing these facts does not compensate for omitting them from HTML
or canvas frames. Entry/terminal states and source links must remain navigable.
Use unambiguous composite step keys even when IDs contain hyphens.

## Select tools by the actual destination

Reuse [operations-ui-delivery](../../operations-ui-delivery/SKILL.md) for composition,
visual judgment and the documented adapter mechanism. For Figwright, read its
[procedure](../../operations-ui-delivery/references/figwright.md) before using that
adapter. Other adapters use their own current schemas. A portable handoff manifest
is not an executable Figma API request and cannot confirm a write capability.

Confirm file/page identity and permitted destination before a write. Create or
reconcile only task-owned sections. Use stable map IDs in the adapter's supported
metadata or a separate node mapping; the file title alone is insufficient. Keep
manual notes in a separate owner-managed region. Preserve existing pages,
components, comments and proposal layers. No universal tool names or paid service
is required by this skill.

Pilot a representative pair and a risky case (long text, alternate branch, missing
capture) before bulk placement. Check text bounds, image aspect ratio and cropping,
callout targets, source readability and links. Re-read actual nodes after the
last write and export a composed preview. Successful acknowledgements or an image
of an asset do not establish a correct canvas placement.

On resume, compare the recorded target and node IDs with actual state. Reuse
owned nodes; do not duplicate every card or delete old cards merely because they
are absent from the current subset. Reconcile changed screenshots and annotations
as described in [maintenance](coverage-and-maintenance.md).

## Accept as the designer would use it

Select a consequential path and answer from the handoff alone: why enter, which
element to use, what changes, what is retained, where to go next, how to cancel or
recover, and which assertions remain unverified. Then use the reverse index to
find all uses of a shared control. Resolve ambiguity rather than add more screenshots.

Where a readable HTML/package fallback is delivered, name it precisely. It is
not a completed Figma file. The optional [portable map](portable-map.md) provides
validation and offline export without modifying the product or installing tools.

## Method sources

- [NN/g: wireflows](https://www.nngroup.com/articles/wireflows/) combines screen context with actions and state changes.
- [NN/g: prototype specifications](https://www.nngroup.com/articles/prototype-specifications/) motivates functional annotations alongside images.
- [Overflow](https://overflow.io/) and [Supademo branches](https://docs.supademo.com/customize/chapters/conditional-branching) inform navigable paths, not evidence that a product supports them.

These are adapted presentation patterns, not a claim that a particular format
has been experimentally shown to eliminate designer misunderstandings.
