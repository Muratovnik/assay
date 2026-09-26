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

These are sections/pages, not three mandatory files. Do not construct a design
system or reproduce the old UI as editable components for documentation. Raster
captures are sufficient; descriptions, callouts and connections should remain
editable in a destination that supports them.

Each pair has two neighboring frames. The left contains stable step/scenario
names, purpose and prerequisites, before-state, action or system event, element
identity, availability/scope, result and applicable next/cancel/error links.
Name the claim layer and verification with source references. The right shows
the matching capture with numbered, editable callouts and a named action legend.
Label BEFORE or AFTER only when the capture's moment is known; otherwise make
that limit explicit. A missing image is labeled not captured, not silently blank.

A complex dialog or result can need its own pair. Same-screen copy/download still
has a result description; a fake destination is unnecessary. Shared controls can
have one explanation linked from their actual uses. A useful crop is acceptable
when linked to its parent screen and identified as a region.

Keep existing behavior, intended constraints and redesign proposals separate.
A designer may combine screens while preserving outcomes: old screenshots are
not a fidelity requirement. Cross-layer relations are not confirmed next steps;
do not join a proposed Retry to an observed error as a current executable path.

Keep screen purposes, state conditions, and actions' roles/effects/scopes in the
reader-facing index, including significant controls without a mapped scenario.
Information in working notes does not compensate for omitting it from the actual
deliverable. Give related steps unambiguous names and navigable links.

## Use the connected capture and Figma tools directly

Take screenshots and available traces with the connected browser tools, following
[evidence and states](evidence-and-states.md). Write the requested Figma artifact
through the connected adapter. With Figwright, read the
[Figwright procedure](../../operations-ui-delivery/references/figwright.md) before
its first operation; it owns connection/file identity, vendor documentation,
operation schemas, partial failures and verification. With another authorized
adapter, use its own documentation and actual schema.

Construct the description frame, screenshot frame, editable annotations and
links through documented operations, working directly from the scenario
explanation and the captured image. Existing maintained templates and ordinary
task-scoped tool calls are valid.

Confirm the exact file/page and allowed sections. Keep stable scenario/step names
in the supported node naming/metadata or existing project notes. Preserve manual
notes, components, comments and proposal layers; this task does not authorize
replacing the whole document. Existing access is usable without requesting new
permissions that the operation does not need.

Pilot a representative pair and a risky case (long text, alternative branch or
missing capture) before bulk placement. Use
[visual judgment](../../operations-ui-delivery/references/visual-judgment.md)
for readability, image aspect ratio, callout placement and composed acceptance.
Read back actual affected nodes and inspect the composition after the last write.
Successful tool acknowledgements are not proof of usable frames or working links.

On resume, follow the adapter's identity/readback procedure and
[maintenance](coverage-and-maintenance.md). Reuse task-owned nodes, do not duplicate
all cards or delete absent ones merely because the current task covers a subset.
Changing an image requires checking its annotations again, not retaining stale
coordinates on trust.

## Missing access and acceptance

Check available connected tools before concluding a capability is absent. When
runtime or Figma writing is unavailable, preserve useful scenario text in the
requested conversation or existing document and retain actual captured images.
State which observations or writes remain blocked, and do not call a text/capture
handoff a completed Figma delivery. No adapter installation, new account
permissions or unrelated application changes follow from this gap.

Answer from the handoff alone: why enter, what to use, what changes or is retained,
where to go next, how to cancel/recover and what remains unverified. Then use the
reverse index to find all uses of a shared control. Resolve ambiguity rather than
adding more screenshots.

## Method sources

- [NN/g: wireflows](https://www.nngroup.com/articles/wireflows/) combines screen context with actions and state changes.
- [NN/g: prototype specifications](https://www.nngroup.com/articles/prototype-specifications/) informs functional annotations alongside images.
- [Overflow](https://overflow.io/) and [Supademo branches](https://docs.supademo.com/customize/chapters/conditional-branching) inform navigable paths, not evidence that a product supports them.

These are presentation patterns, not experimental proof that this format removes
all misunderstandings. Tool mechanics stay with their existing owners.
