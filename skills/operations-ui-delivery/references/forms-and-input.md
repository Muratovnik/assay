# Forms and input

Use when creating or changing a form, validation, input handling or submission.
Follow the existing form primitive and the product's commit contract.

## Follow input through correction

Distinguish untouched, edited, invalid, correcting and submitted states. Choose
validation timing from the cost of the mistake and the user's opportunity to
finish the value. Do not show a wall of errors before entry or retain an obsolete
error after correction. Server rejection may need a field or form-level message;
use [Content](content-and-recovery.md#keep-recovery-in-the-users-working-context)
for recovery placement and accessible error association.

Keep a persistent, programmatically associated label; a disappearing placeholder
is not its replacement. Reveal necessary format/required constraints before they
cause failure. Preserve legitimate intermediate input instead of rejecting every
keystroke that is not yet a complete value. For web inputs, use appropriate native
type, autocomplete and input mode without blocking paste or password managers.
Composition input such as IME is not a sequence of committed single characters:
do not submit or destructively normalize a value while composition is in progress.

- Failure: pasting or autofilling leaves validation stale; Enter commits half an
  IME composition; correcting the last error leaves Save unusable.
- Check: enter realistic data through applicable typing, paste, autofill and
  composition paths, correct a client error, encounter a server error and finish
  with the input retained. Test the final effect, not just an enabled prop.
- Valid control: a product may defer validation until submit or validate a costly
  field earlier. Neither on-blur validation nor a particular native input type
  is universally correct for every locale and value.

## Give submission one owner

Define what submits, what edits and what dismisses. Enter may submit a simple
form but must preserve multiline input and component-specific selection behavior.
Use native semantics: on the web, an unrelated button inside a form needs a
non-submit type. Click and keyboard submission should reach the same authorized
operation. For duplicate activation, pending feedback and result reconciliation,
read [Data lifecycle](data-lifecycle.md#reconcile-writes-and-retries).

Avoid making users hunt for the reason an incomplete form cannot submit. A
genuine prerequisite can disable an action when the reason and next step are
available. Check its transition to available through real input using
[Actions](actions-and-scope.md#put-frequent-work-where-it-is-needed).
An exact confirmation phrase is a legitimate prerequisite; do not impose an
always-enabled Submit or permit a forbidden effect to improve discoverability.

Before adding navigation or panel dismissal, establish what happens to an edited
draft using [departure and return](actions-and-scope.md#preserve-drafts-across-departure).
An error-free form is not evidence that leaving and returning preserves work.

## Do not offer a whole-form reset

A Reset or Clear control that wipes every field is rarely the user's task and
destroys entered work when hit by mistake, most often beside Save. Do not add
one as a stand-in for Cancel: Cancel leaves the form and returns to what it
replaced using [Actions](actions-and-scope.md#return-to-what-the-action-replaced);
clearing the fields keeps the user in a form they meant to leave.

- Failure: a creation form offers Clear and Save but no Cancel, so leaving means
  wiping the fields by hand or navigating away with an unresolved draft.
- Valid control: a per-field clear such as a search box's ×, a filter reset that
  acts on the visible filter set, or a settings "restore defaults" with the
  owner's confirmation or undo model act on one bounded value the user is
  looking at and are legitimate.
- Check: the form has one submit and, when something exists to return to, one
  Cancel; no single control discards all entered values without undo.

## Primary references

- [Cloudscape: validation lifecycle](https://cloudscape.design/patterns/general/errors/validation/)
- [Vercel: form interaction checks](https://github.com/vercel-labs/web-interface-guidelines/blob/e3d624baaf29dc1fc645aff3e38f03e564d2d6b1/README.md#forms)
- [MDN: composition input](https://developer.mozilla.org/en-US/docs/Web/API/Element/compositionstart_event)
- [NN/g: reset and cancel buttons](https://www.nngroup.com/articles/reset-and-cancel-buttons/)

Use relevant principles, not universal submit timing, shortcuts or backend changes.
