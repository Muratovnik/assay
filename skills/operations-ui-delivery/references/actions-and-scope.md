# Actions and scope

Use when placing actions, reorganizing create/edit flows, or changing an object's
scope. A compact answer in the task is enough; a new specification is not required.

## Make the action match the user's object

Establish which object is viewed, which will change, who else consumes it, and
when the change is committed. A list embedded in a local editor may be a shared
reference, a local override or a copy. Similar presentation does not make those
operations interchangeable. If current evidence cannot resolve the intended
meaning, ask about that effect rather than silently choosing a data model.

- Failure: editing an embedded list changes other configurations without any
  indication that the source is shared.
- Decision: expose the actual scope at the decision point and distinguish
  editing the shared source from creating a local variant when both are supported.
  Do not invent copy/override functionality to avoid a necessary product choice.
- Valid control: an explicitly labeled shared-source editor should update its
  consumers; silently making a copy would also be wrong.
- Check: act from two consuming contexts and verify the intended changed and
  unchanged objects, including cancel and save boundaries.

## Put frequent work where it is needed

Choose prominence within each task context. A frequent action such as refresh,
edit or resolve should not require opening unrelated settings. Offer contextual
actions for the item being handled and bulk actions when the task genuinely
applies to a collection. Distinguish bulk scope from a row's scope. Group secondary
operations by purpose; a menu is useful when it reduces noise without hiding the
primary task. Avoid duplicating whole control sets across competing locations.

- Failure: a Problems view identifies an item but makes the user search elsewhere
  for its repair, or exposes only one-by-one handling for a supported bulk task.
- Decision: provide the supported action or a direct route to its correct owner,
  with enough context preserved to complete it.
- Valid control: rare advanced operations may belong in a submenu. Independent
  forms on a settings page can each have their own primary action.
- Check: start where the user encounters the need, with realistic content density;
  complete it without instructions about an unrelated screen. Verify permission
  constraints and unavailable-action reasons, not just button presence.

When a frequent action or selection pattern is shared by several flows, inspect
those points of need before declaring the redesign complete. A refresh button
in a library does not establish that users can refresh from a composer. Reuse
the authorized action and its scope; a direct route to the owner can be sufficient
when it preserves context. Do not duplicate every rare control on every screen.

For an action reported as always unavailable, establish its real prerequisites
and an eligible starting state. Fulfill supported prerequisites through the UI
while it stays mounted; verify the action becomes available, activate it normally
and inspect the intended effect. A disabled-state assertion or directly enabling
the component in a fixture bypasses this check. Explain legitimate restrictions;
do not remove permission checks or invent a user repair for an external constraint.
Where recovery is supported, also check availability after completion or failure
so a pending flag cannot leave the action permanently locked.

## Make transitions apparent

After Add or Edit, the next step should be apparent in the current working
context. Prefer a nearby inline surface for a small local edit; use a page or
multi-step flow when complexity, comparison or recovery calls for it. A bounded
modal is legitimate for a focused interruption. Choose the surface from the task,
not from a universal preference for drawers or dialogs.

- Failure: Add inserts a form below a long list outside the viewport with no
  visible feedback; a row's delete cross looks like the new form's close control.
- Decision: place or reveal the editor deliberately and manage focus when the
  workflow moves there. Give remove, cancel, dismiss and delete distinguishable
  meanings and hit areas. Resolve the actual effect and reversibility before
  choosing safeguards: an ambiguous cross proves an affordance problem, not
  irreversible deletion. Label the intended effect; retain the owner's existing
  confirmation or undo model where applicable.
- Valid control: an offscreen append can be appropriate if the user receives a
  perceivable result and an explicit way to reach it without losing their place.
- Check: open, enter, cancel, retry and save from the actual trigger; confirm which
  data survives, which object changes, and where focus/scroll end up.

## Return to what the action replaced

Choose the landing state from the actual entry path, not the number of records
alone. Distinguish three cases:

- Replaced object: Add or Edit took over an area showing an object. Cancel
  discards the draft and restores that object with logical focus, or the owner's
  fallback if it no longer exists. Do not leave a blank area or keep an emptied
  editor open in place of returning.
- Inline disclosure: the surrounding list stays visible and remains the work
  area. Cancel may collapse the short input row to its trigger and return focus
  there. No displaced object has to be restored.
- Empty workspace: the form is the work area. Omit Cancel when there is no real
  destination or dismissible step; preserve a genuine route/modal exit when one
  exists. A duplicate Add trigger may be hidden or visibly unavailable under the
  product's policy. Neither presentation is a universal requirement.

A whole-form Clear is not a substitute for leaving the form; see
[Forms](forms-and-input.md#do-not-offer-a-whole-form-reset). Preserve an existing
necessary discard safeguard, but do not add a confirmation for an untouched draft.

- Failure: Cancel removes the selected object from the work area permanently,
  or Clear wipes all fields while the user still cannot leave the editor.
- Check: select an object, open the form, enter a draft and cancel using the real
  control. Verify the landing content and focus, no write, an empty draft on
  reopening and usable entry actions. If the object disappeared meanwhile, check
  the agreed fallback. An empty-field assertion alone misses both failures.
- Valid control: exercise inline collapse and the supported empty-workspace
  policy separately. A screenshot cannot establish absence of a write, and a
  successful replaced-object case does not qualify every departure path.

## Preserve drafts across departure

Distinguish edited draft, pending save and confirmed saved state. For affected
object switches, panel close, navigation, Back or reload, establish the existing
preserve, save, discard or recovery contract before wiring dismissal. Include
session interruption when that return path is supported. A warning is useful
only when work would otherwise be lost; use the owner's existing mechanism.

Check edit A -> leave for B -> return, and cancel an offered departure. Inspect
both the draft and committed record, focus and ability to continue. A saved-state
badge or a successful explicit Cancel test does not qualify every exit path.
If save is still pending, use [Data lifecycle](data-lifecycle.md#reconcile-writes-and-retries)
so a late reply cannot overwrite a newer draft. Browser unload prompts alone
are not reliable draft persistence across all supported shutdown paths.

An already confirmed autosave or disclosure that loses no work need not interrupt
the user. Do not add confirmations to every transition, invent local persistence
for sensitive input or silently reinterpret Close as Save.

## Preserve the journey during redesign

Inventory the supported tasks and entry points touched by a replacement, including
saved filters, board/graph views, back/deep-link behavior and cold start. Account
for them in the new composition before removing old navigation. Do not preserve
duplicate widgets solely because they existed; preserve the supported outcome.
An owner-approved feature retirement is a valid counterexample to preservation.
Check both an existing user's saved context and a first visit, not only the new
screen reached through a development URL.

## Primary references

- [Pajamas: contextual button hierarchy](https://design.gitlab.com/components/button/)
- [Cloudscape: global and in-context actions](https://cloudscape.design/patterns/general/actions/)
- [Cloudscape: choosing a creation flow](https://cloudscape.design/patterns/resource-management/create/)
- [Cloudscape: unsaved changes](https://cloudscape.design/patterns/general/unsaved-changes/)
- [MDN: limits of beforeunload](https://developer.mozilla.org/en-US/docs/Web/API/Window/beforeunload_event)

These are pattern references, not dependencies or permission to import their
layout, thresholds or component APIs.
