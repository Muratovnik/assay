# Coverage and maintenance

Use for completeness claims, reviews and updating an existing map. Completeness
is relative to the recorded product revision, scope and independent inventory.

## Trace both directions

For every inventoried goal, find a scenario and recognizable outcome or explicit
gap. For each significant screen/state/control, find its scenario uses or a
reasoned disposition. Reconcile against entry-point and consumer sources, not
the number of cards. A partial inventory cannot prove whole-product coverage.

Check relevant alternative/direct entry, blank data, validation, pending/success,
partial failure, retry, cancellation, departure and return. Include material
combinations, such as a late save after switching records, not every possible
combination for every button. Use the supported contract rather than inventing
failure modes or unsupported devices.

Keep broken links, missing evidence, product defects and inapplicability separate.
A stale frame link is a document defect; an unexecuted transition is a gap; a known
wrong runtime result can be documented faithfully but is not intended behavior.
Missing documentation does not prove a feature is absent. An intended/proposed
recovery must not silently finish an observed path that has no known recovery.
Check each entry, not only the successful main path, and mark unknown outcomes.

Challenge a plausible omission with the defect still present. Two same-screen
export actions must survive deduplication, while a decorative icon needs no
fabricated scenario. Visited URLs or successful screenshots can hide a menu-only
action. Trace these relationships in the existing document/canvas; do not build
a graph validator as a substitute for inspecting the sources.

## Give downstream consumers a usable contract

For [operations UI delivery](../../operations-ui-delivery/SKILL.md), pass the goal,
state/action links, source-backed retained outcomes, changeable presentation and
unresolved decisions. Consolidating screens can preserve a scenario; dropping an
obscure entry can break it. Outcomes, not old coordinates, govern the redesign.

For [test writing](../../test-writing/SKILL.md), pass prerequisites, the real
boundary, action/result and expected-behavior authority separately from observations.
Mark mocks, failures and unverified execution. The test author owns assertions;
this map is not a circular oracle. Keep existing fixtures and the test stack.

A read-only review uses these criteria without editing the application or reviewed
artifact. An independent verdict belongs to
[independent audit](../../independent-audit/SKILL.md); label a self-check as such.

## Update without a second synchronization system

Inspect the prior handoff/build and changes to requirements, source owners,
shared controls and supported paths. Use existing source diffs, project notes and
actual frame readback to identify affected scenarios. Do not implement a map-diff
CLI or a custom interchange schema. One changed label need not restart the survey;
changed behavior must not inherit old verification without checking applicability.

Keep stable names/links across reordering and renaming. Retired items need a reason
and replacement reference where useful; do not reuse their identity for another
function. Keep original capture provenance. Updating a date does not make a stale
screenshot or trace current.

Before a Figma write, use the existing adapter procedure to confirm target identity
and current nodes. Preserve designer comments and manually maintained proposal
layers. Reuse task-owned nodes; removal from the current subset is not permission
to delete them. Resolve partial writes through readback before retrying. Keep any
working cross-references in the existing task or supported node metadata, not a
new database or maintained synchronization service.

When a screenshot changes, recheck the annotations against the actual image. When
state meaning changes, revisit scenarios, sources, reverse links and downstream
consumers, not just the picture. A change to a requirement used only to justify an
inventory exclusion still reopens that exclusion; unchanged scenario prose does
not prove a retirement decision remains valid.

## Report what the evidence establishes

Report scoped inventory dispositions, observed/source-only paths, conflicts,
blocked actions, missing captures and unexamined surfaces. Tool success and
readback are not behavioral acceptance. Authored, placed in Figma, visually
inspected and approved are different results. Keep material limits in the
actual designer-facing artifact, not only its accompanying message.
