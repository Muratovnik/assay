# Coverage and maintenance

Use for completeness claims, reviews and updating an existing map. Completeness
is relative to the recorded product revision, scope and independent inventory.

## Trace both directions

For every inventoried goal, find a scenario and a recognizable outcome or explicit
gap. For each significant screen/state/control, find its scenario uses or a
reasoned disposition. Reconcile the list against entry-point and consumer sources,
not the number of generated cards. A nonempty but partial inventory cannot prove
whole-product coverage.

Check relevant alternative/direct entry, blank data, validation, pending/success,
partial failure, retry, cancellation, departure and return. Use the supported
product contract instead of inventing all these states for every button. Include
material interactions between conditions, such as a late save after switching
records or returning to a filtered list; avoid a Cartesian test matrix.

Keep structural errors, missing evidence, product defects and inapplicability
separate. A dangling state ID is a map error; an unexecuted transition is a gap;
a known wrong runtime result can be documented faithfully. It must not become
an intended outcome. Mere absence from documentation is not evidence that a
feature does not exist.

Challenge at least one plausible omission with the defect still present. The
nearby control matters: two same-screen export actions must survive deduplication,
while a decorative icon need not acquire a fabricated action. A list of visited
URLs or successful screenshots can pass while a menu-only action is missing.

## Give downstream consumers a usable contract

For [operations UI delivery](../../operations-ui-delivery/SKILL.md), pass goal and
state/action IDs, source-backed retained outcomes, safe-to-change presentation and
unresolved product decisions. Redesign acceptance follows outcomes, not old widget
positions. Screen consolidation can preserve a scenario; deleting an obscure
entry path can break it.

For [test writing](../../test-writing/SKILL.md), pass prerequisites, real boundary,
transition/result and expected-behavior authority separately from observations.
Mark mocks, failures and unverified execution. The test author determines the
assertion; this map is not a circular oracle. Keep existing fixtures and test stack.

For an authorized review, use these criteria without repairing the application
or the reviewed artifact. An independent verdict still belongs to
[independent audit](../../independent-audit/SKILL.md); a self-check is labeled as such.

## Update without erasing history or owner work

Record the prior map/build and inspect changes in requirements, source owners,
shared controls and supported runtime paths. Identify affected scenario/state IDs;
recheck their consumers and retained entry/exit paths. Do not restart the entire
survey for one label change, or retain stale evidence after changed semantics.

Keep stable IDs across sorting and renaming. A genuinely retired item retains a
reason and replacement/tombstone reference in the handoff record. Do not silently
reuse its ID for another function. New IDs are additions, not a reason to replace
all existing cards. Refresh the displayed source/build for changed evidence only;
never make an old screenshot appear freshly captured by updating a date globally.

Before any external write, reconcile target identity and existing notes. Keep
owned generated text/captures separate from designer comments and proposal layers.
Compare desired IDs with actual created/updated IDs, not only counts. Repeated
exports should reconcile the same nodes; removed items need explicit retirement,
not unrequested deletion. A failed write stops dependent updates and requires a
readback before retrying.

If a screenshot hash or dimensions change, invalidate its annotations until
reviewed against the new capture. If state meaning changes, revisit evidence,
steps, reverse index and downstream references, not just the image.

## Report what the evidence establishes

Report scoped inventories and dispositions, verified/source-only paths, conflicts,
blocked actions, missing captures and unexamined surfaces. Structural validation
is not behavioral acceptance; generated/exported, visually inspected and approved
are separate results. Counts describe the recorded inventory, never internet or
whole-product recall. Preserve material limits in the designer-facing artifact,
not only in an accompanying chat message.
