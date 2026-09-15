# Selection

Use for grouped, nested, filtered, paginated or bulk selection. Resolve membership
and action scope before choosing the visual checkbox state.

## Separate membership, selection and effect

State what the control selects: visible rows, a page, all filtered matches,
descendants, or references to whole lists. Decide whether selecting a parent
selects descendants, selects only the parent, or merely summarizes children.
Expansion, membership and selection are separate concepts. Explain implicit
parent-to-child effects before an operation where that distinction matters.

- Failure: select-all appears to affect visible rows but applies to hidden data,
  or selecting a group misses unloaded members while claiming completeness.
- Decision: use the product's intended scope consistently in state, counts and
  action confirmation. Define how filter, pagination, loading and membership
  changes affect the selection. An API or library supporting several modes does
  not require exposing them all. Implement the agreed mode; leave additional
  selection modes and exclusions outside the change unless required by the task.
- Valid control: visible-page and filter-wide selection are both legitimate.
  Selecting a container resource need not select its children, even when deleting
  that container will affect them. A saved live query may admit new matches while
  remaining independent of subsequent changes to the visible filter; live
  membership and rebasing the query are separate product choices.
- Check: select, collapse, filter, change page and load more; reconcile item/group
  counts with the exact population affected by the operation.

## Keep selection, display order and execution priority separate

Selecting a row should not silently move it or change processing priority unless
that is the agreed behavior. Apply a default presentation sort without erasing
persisted user ordering. Keep supported bulk selection available where users
need it; its checked/mixed state and effect must use the same population.

- Failure: choosing a category and selecting its visible rows drops hidden
  selections, or sorting the table rewrites the execution queue.
- Decision: update the intended set/order only. Distinguish selecting the current
  matching items from storing a live category reference that admits future items.
- Valid control: an explicit reset, requested priority change or an intentional
  selected-first view may change order or membership. Do not impose a universal
  category sort, stable sort or ban on priority numbers.
- Check: select some, filter, select/clear the scoped set, then restore the view.
  Verify hidden selections, row position and persisted execution order as applicable.

## Avoid indistinguishable selection controls

Before adding a neighboring selection control, compare its population, lifetime
and committed effect with existing controls. "Select visible items now" and
"Follow this category as it changes" may initially produce the same rows while
having different future effects. Make that difference apparent at the choice;
do not expose both merely because the data model supports both. If only one is
needed by the agreed task, keep the other out of its primary workflow. If effects
are identical, prefer one clear control unless separate access points serve a
real task. Do not silently merge distinct operations or replace live membership
with a snapshot to simplify presentation.

Check whether the user can predict the affected items now and after membership
changes from the labels and context. Exercise both operations with a new member
or filter change; a matching initial count does not prove redundancy.

## Represent partial knowledge truthfully

When a parent summarizes a known set, distinguish none, some and all selected.
Use the primitive's indeterminate/mixed state for some selected, including its
accessible state; a changing explanatory badge is not a substitute. Determine
the next activation's effect deliberately instead of inheriting an accidental
checkbox cycle.

Unknown or unloaded membership is not automatically partial selection, zero,
or all. Query the authoritative selection summary when available, or expose the
limitation without making a complete-set claim. Keep disabled-item constraints
and unavailable bulk-action reasons understandable.

- Failure: selecting one child makes the parent look fully selected, or a count
  of loaded records is labeled as the total.
- Valid control: a binary checkbox for an independent parent object may remain
  binary; it must not pretend to summarize the descendants.
- Check: none/one/some/all, constrained items and unknown membership, using both
  pointer and keyboard. Verify accessible state and count, not only the glyph.

## Keep the selected contents inspectable

Summaries must still allow the user to inspect and edit the composition. For
chips or compact labels, allocate space for state changes; wrap, summarize or
provide an operable disclosure according to the task. A `+n` marker that cannot
reveal the hidden values is not a usable summary. Avoid losing identity when
labels repeat or localized names are long. Stable geometry does not require a
fixed-height box that clips enlarged text.

## Primary references

- [WAI-ARIA APG: checkbox and mixed state](https://www.w3.org/WAI/ARIA/apg/patterns/checkbox/)
- [Cloudscape: nested resources](https://cloudscape.design/patterns/resource-management/view/table-with-nested-resources/)
- [Cloudscape: grouped resources](https://cloudscape.design/patterns/resource-management/view/table-with-grouped-resources/)

Cloudscape deliberately uses different selection scopes for nested resources and
grouped resources. Preserve that distinction as a design question; neither model
is a universal rule for every tree.
