# Content and recovery

Use when choosing names, explanatory copy, status vocabulary or error handling.

## Let the control carry its meaning

Name objects and actions in terms the user recognizes. Keep an action's wording
consistent from entry point through confirmation and result. Put identity fields
where they establish the object being created or edited. Prefer a label that
explains the action over a paragraph teaching the user to interpret it.

- Failure: redundant introductory/helper sentences repeat the visible label;
  internal service terminology becomes navigation; a generic cross ambiguously
  means close, remove a reference or delete the underlying object.
- Decision: retain the words needed for choice, scope, consequence or recovery;
  remove narration that adds none of them. Align label, icon, location and effect.
- Valid control: unfamiliar concepts, costly/irreversible effects and repair
  instructions can require explanation. Progressive disclosure can move secondary
  help, but must not hide information needed to make the current choice safely.
- Check: ask what a user can predict from the actual control before reading a
  separate explanation. Use real localized content; do not fix one language by
  enforcing English casing or punctuation rules everywhere.

Inspect the complete local group, not each string alone: title, tab, selected
filter, action, count and status can repeat the same noun or fact until useful
content is crowded out. Keep information that changes the current choice; put
background explanation in existing help/documentation when it is not needed at
that point. A generic all-items filter need not be repeated as a second heading.

A familiar contextual command may use an icon with an accessible name and a
discoverable explanation, following [Interaction](interaction-and-layout.md#make-disclosed-help-usable).
An unfamiliar or consequential action may still need visible wording. Separate
navigation from refresh/edit and make the destination/effect predictable. Remove
redundant persistent success narration without hiding pending, failed or stale
state. Check the whole header at realistic width; shortening every button into
an unexplained icon is not an acceptable density fix.

## Connect a count to the action it describes

When a nearby count describes exactly the population a command acts on, consider
one control that combines action and count instead of unrelated status fragments.
Keep its effect apparent through suitable wording or a recognizable contextual
icon and accessible name. A resource noun and number alone can look like passive
status or navigation. Keep configuration and refresh distinct when their effects
differ; grouping must not silently change the operation's scope.

Check the counted population against the actual affected objects, including
selection/filter changes and supported loading, failure or partial outcomes.
Retain meaningful pending/error/freshness feedback; an unknown count is not zero.
For async identity or propagation changes use [Data lifecycle](data-lifecycle.md).
Judge the complete rendered group and activate the real command: a shorter header
or a button containing a badge alone does not establish clarity or correct scope.

A global total may legitimately remain separate from an action on selected items.
Do not insert every nearby metric into a button, imply all items are affected
when only a subset is, or mandate icons where a visible verb is needed.

## Do not collapse distinct states into one decoration

Give each relevant state a truthful meaning: loading has no result yet; empty is
a successful result with no items; zero matches comes from a filter; unavailable
or failed reads do not establish emptiness. Show pending work and partial failure
without falsely announcing success. Retained data during refresh needs an
understandable freshness/error indication when it may no longer be current.

- Failure: an unavailable count is rendered as zero; one boolean uses Yes while
  another uses an unexplained dash; first-open failures look like an empty app.
- Decision: define the semantic vocabulary at the shared owner. Distinguish false,
  unknown and not applicable wherever the distinction changes interpretation.
  Display the same meaning consistently, including accessible text.
- Valid control: a documented dash can mean not applicable; it should not also
  silently mean false, missing or failed. A spinner may suit a short local action;
  structural loading placeholders suit content whose shape is known.
- Check: exercise initial load, refresh success/failure, genuinely empty and
  filtered-empty data, stale data and partial results. Verify the result reported
  to the user agrees with the authoritative operation.

When implementing async results or shared refresh, use
[Data lifecycle](data-lifecycle.md) for result identity, intermediate states and
propagation. Consistent status wording does not prove that consumers update.

When a result is unavailable because a prerequisite is missing, give the relevant
reason and supported next step in the working context. Verify that completing
that step can reach the result; use the data-lifecycle check for the actual
calculation path. A clearer message alone does not repair a permanently blocked
calculation. Do not invent a repair action when no user action can resolve it.

## Announce meaningful updates

Make relevant search results, completion, waiting and error status available
without requiring visual observation or moving focus away from ongoing work.
Use the existing semantic announcement mechanism with enough object/action
context. Do not announce every cell refresh or turn the whole changing screen
into a live region; not every content change is a status message.

Check the resulting announcement and focus during an applicable async operation,
including repeated updates. Visible text or an `aria-live` attribute by itself
does not qualify assistive behavior; distinguish inspected semantics from an
executed assistive-technology check. For focusable restriction reasons and
composite controls use [Accessibility](accessibility-and-composites.md).

## Keep recovery in the user's working context

Attach fixable errors to their controls or affected object. Offer the appropriate
retry, edit, authorization route or other supported repair near the failed task.
On form submission, associate errors with their controls, make the first actionable
error reachable and preserve entered values. Use [Forms](forms-and-input.md) when
validation timing or input/submission handling changes. System-level failures may
need a form-level message rather than a fabricated field error. A diagnostics page can explain details without being
the only place the user can discover or recover from a failed operation.

- Failure: disabled Save gives no reason; a failed submit discards input; the user
  has to recreate selection to retry a bulk action.
- Valid control: a genuinely unmet prerequisite can disable an action when the
  reason and next step are available. Completed items in a partial batch should
  not necessarily be repeated with the failed ones.
- Check: fail once after entering realistic data, repair the relevant cause and
  finish. Inspect preserved input/selection and actual completed versus pending
  effects, not just the disappearance of an error toast.

## Primary references

- [Anthropic: user-facing interface language](https://github.com/anthropics/skills/blob/53048666b05b4799081517d00e09e0a2dd688678/skills/frontend-design/SKILL.md)
- [Cloudscape: validation and recovery](https://cloudscape.design/patterns/general/errors/validation/)
- [Cloudscape: loading and refreshing](https://cloudscape.design/patterns/general/loading-and-refreshing/)
- [Cloudscape: table states](https://cloudscape.design/patterns/resource-management/view/table-view/)
- [WCAG: status messages](https://www.w3.org/WAI/WCAG22/Understanding/status-messages.html)
