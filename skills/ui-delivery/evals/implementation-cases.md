# Practical UI skill evaluation specifications

Evaluator-only. These specify tasks to prepare in an existing component/browser
harness; no executable fixture or run is supplied here. Use an isolated copy with
synthetic data and its existing commands. Do not modify a live product or install
a framework to run this corpus. A skill edit does not authorize a model campaign.

## Prepare the packet and evidence

Choose a relevant pair below. Retain its initial source, lockfiles, fixture data,
skill bytes and baseline identity. Establish that the defective variant exposes
the specified failure and the control does not before grading an executor.
Run old/candidate/ordinary-instructions conditions with comparable tools, budgets
and inputs when that comparison is authorized. Fix the run count before starting.

Give the executor the user request, owner instructions, startup/test commands,
permitted source and raw UI evidence. Keep this document, grading tests, causal
diagnosis, sibling answer and previous outputs outside its accessible inputs.
Do not claim enforced blindness or isolation if the actual harness lacks it.
The request authorizes fixes only inside that isolated task, with no dependency,
client-config, live-data or external mutation. Supply the existing product policy;
do not make a missing policy an accidental puzzle.

Score discovery, correct repair, preserved control behavior, verification fidelity
and unnecessary edits/cost separately. A described fix is not an implemented one;
a locator rewrite or skipped test is not proof the product was repaired. Inspect
the final artifact and observed actions, not just the closing report. Keep failed
attempts and harness faults distinct. Primary-author walkthroughs are self-review,
not fresh executor evidence.

## P1: Updating derived results

Executor request: "The estimate flashes when refreshed. Inspect and correct the
user experience, keeping estimates tied to the chosen target. Verify the change."

- Defective fixture: the state owner retains a valid result during same-context
  refresh; the consumer blanks it while pending. An existing test waits for
  settlement and checks only the final result. Provide controllable responses.
- Valid control: changing target deliberately withholds the old target's number;
  an older request can complete after the new target's response.
- Oracle: observe the same-context value throughout a held refresh, including
  failure/freshness feedback. Change target and release responses in reverse
  order; the current view must never attribute the old result to the new target.
  Inspect both model and composed consumer effects.
- Boundary variant for a later run: source data changes without selection-ID
  changes; an already-open consumer must update through the existing signal.

Reachability variant: supply sets A={a,b}, B={b,c} whose complete inputs should
produce intersection {b}; the broken eligibility path always reports insufficient
data. Also provide complete disjoint inputs with expected zero and an incomplete
input that can be repaired through an existing local action. Observe the computed
result and recovery without injecting the answer or reloading. A mocked final
response alone cannot pass this variant. Respect legitimate partial-result policy.

Availability variant for P1: an eligible user chooses a source through the UI,
but refresh remains disabled or stays pending after failure. Observe the mounted
prerequisite-to-enabled transition, activate normally and verify the scoped result
and supported retry. Contrast a read-only role with a truthful restriction. An
injected enabled prop or direct handler call does not qualify the actual path.

## P2: Actual gesture and transient geometry

Executor request: "Read-only rows can still move, and the drag preview looks
broken. Repair the interaction and verify the allowed workflow still works."

- Defective fixture: a disabled handle does not disable the installed drag
  mechanism. Its detached row preview loses column widths and font context.
  Existing tests assert the attribute and original row geometry only.
- Valid control: read-only still allows copying and details. Allowed reorder
  has a deliberately compact, approved multi-row preview rather than a row clone.
- Oracle: attempt the actual gesture in both availability states; inspect draft
  and persisted order. Measure/inspect the active preview against its own design
  contract. Do not count direct reorder-helper calls as gesture evidence.
- Boundary variant: availability changes while the component remains mounted;
  the mechanism must follow the current state rather than its initial setting.

Discovery variant for P2: an unmarked cell alone opens details; tests know its
hidden coordinate. Assess the resting visible indication and accessible trigger,
then ordinary pointer/keyboard opening with independent selection/drag/delete.
Contrast a clear dedicated link: neither whole-row clicking nor an extra chevron
is mandatory. Activation success alone is not a discovery verdict.

## P3: Workspace consumers and scroll

Executor request: "Creating and editing the same item feel inconsistent after
the layout change. Fix the affected workspaces, including wide windows and scroll."

- Defective fixture: create and edit reuse a table, but only create receives the
  bounded shell. An existing geometry suite omits edit. Include empty and dense
  tables, a long accessible hidden label, and an open/closed secondary panel.
- Valid control: a separate long help document uses document scrolling; a truly
  overflowing navigation menu must remain scrollable. Detail viewing serves a
  different task and need not become an editor.
- Oracle: identify consumers from source and actual entry routes. Check create,
  edit, direct load and return where affected; scroll the intended regions.
  Inspect wide/compact composition with the panel open and closed, preserving
  accessible names, input and focus/modality. Zero overflow alone cannot pass.
  Where the panel supports ongoing work, complete the parent's Create/Save while
  it remains open; do not substitute a panel-local Add or dismiss it in setup.
  Inspect useful table/panel height after toolbar wrapping; retain necessary
  status and legitimate differences in task areas rather than forcing equal boxes.
- Boundary variant: a new long localization changes available height while the
  same shell and table are mounted; the useful work area must remain reachable.

Composition variant: breadcrumbs appear after the object title, moving it and
the primary action. Include a long path and a flat page without breadcrumbs.
Check meaningful identity, accessible hidden ancestors and useful area after
navigation/resize. Do not grade a fixed header height or mandatory breadcrumb.
For an already adaptive panel, resize inline → overlay → inline while editing;
check draft, focus/modality and task completion without helper dismissal.

Container variant: a centered capped workspace becomes uncapped on panel open,
moving its title and leading table edge despite passing endpoint-fit tests. The
agreed contract keeps those anchors stable. Check their positions through
open/close on affected editor/library pages and navigation widths, together with
remaining field/column usability. Contrast an intentional comparison-mode reflow.
Review the whole rendered composition as well: primary-next-step prominence,
cramped fields beside unused space and detached help can survive geometry tests.

Column variant for P3: two related tables show the same identity/category fields
but allocate space inconsistently; one includes selection and extra numeric
columns. Supply representative long values and the intended density. Compare at
comparable usable widths and relevant panel states, inspecting boundaries,
truncation, scanning and action access. Contrast a legitimate narrower variant
whose extra fields remain usable. Equal percentages, no overflow or a shared
component name cannot substitute for this composed check.

Action/count variant for P3: an agreed compact header splits a refresh command
from the number of resources it refreshes. Check a fitting combined control's
discoverability, accessible action meaning and actual affected population after
selection/filter changes and pending/failure transitions. Contrast a global total
beside an action on only selected resources. Keep configuration distinct and
unknown/partial state truthful; shorter copy or a badge-presence assertion alone
cannot qualify the result.

Container variant for P3: a form remains in its wide arrangement when an adjacent
drawer reduces its allocated width at an unchanged viewport. Its existing tests
only resize the window. Supply the supported browser contract and intended narrow
layout, which requires a conditional change to the form's Grid/Flex arrangement.
Check the chosen query ancestor and containment sizing, then open/close or resize
the existing neighbor while the form stays mounted. Inspect boundary transitions,
content, focus/input and action access. Keep the layout mechanism distinct from
the condition controlling its styles. Contrast a simple layout with no need for
additional conditional changes and valid shell or reduced-motion media queries.
An `@container` declaration, new split-pane feature or global query migration is
not an acceptance requirement; the real space-dependent behavior is.

## P4: Intermediate transition quality

Executor request: "The navigation label jumps while collapsing and parts of the
details panel pop into place. Correct the transitions without losing usability."

- Defective fixture: a shrinking track wraps the toggle label midway; a portaled
  header mounts at its final position before the panel body arrives. Endpoint
  screenshots pass with animation disabled.
- Valid control: an approved staggered reveal is visually coherent and operable;
  reduced-motion switches instantly. Preserve those behaviors.
- Oracle: inspect a bounded recording or representative intermediate frames in
  normal motion, then the reduced-motion path. Check text, child/parent geometry,
  clipping, focus and supported rapid reversal. Changing duration without fixing
  the transient defect or testing only settled states cannot pass.

Mechanism variant: the product already supports a shared-element transition for
the affected identity change. Ask for a justified implementation using existing
capabilities, with a functional fallback. Contrast a simple local fade already
correctly implemented in CSS: adding an API/library is not required to pass.
Include delayed content and interruption only where these affect the transition.

Object-switch variant for P4: keep the panel open while selecting A → B → A;
hold and fail responses, then release an obsolete response last. A temporary
empty body collapses and re-expands despite passing endpoint screenshots. Check
intermediate anchors, current identity and action ownership. Contrast legitimate
height/scroll changes between different documents; preserving stale content as
the new object or freezing every height does not pass.

## P5: Acquiring a persistent control

Executor request: "The collapse control is hard to hit at the bottom of the
navigation. Improve its placement and verify that adjacent actions still work."

- Defective fixture: the agreed edge target has a dead strip at its expected
  boundary; the test only clicks its center. Supply normal/maximized window
  geometry and the product's target/platform contract.
- Valid control: a control inside the content and a system-safe-area inset must
  remain inset; a panel edge does not stop the pointer like a screen boundary.
- Oracle: inspect actual bounds and activate the expected target edges with
  ordinary pointer events, checking the neighboring command remains separate.
  Verify keyboard access. Do not accept a zero-padding rule, touch-only dimensions
  or minimum-size compliance alone as evidence of improved acquisition.

## P6: Draft, input and mutation ownership

Executor request: "Repair unreliable saving and navigation in this editor using
the existing form and mutation mechanisms. Preserve supported recovery."

- Defective fixture: validation only observes keyup; paste/autofill leaves stale
  availability, composition Enter submits early, and an unrelated button submits.
  A -> B -> A loses a dirty draft. A delayed save overwrites a newer draft; click
  plus Enter produces duplicate effects. A failed optimistic write restores an
  obsolete collection over another successful edit.
- Valid control: exact-phrase confirmation has a legitimate prerequisite;
  confirmed autosave needs no discard prompt; independent writes can coexist.
- Oracle: ordinary supported input and composition completion, error correction,
  draft departure/return and controlled write ordering. Inspect actual effects,
  draft versions and feedback. Model a lost response separately from confirmed
  failure using only the supplied backend guarantees. Do not auto-retry uncertain
  non-idempotent writes or build a new reconciliation service to pass.

## P7: Access across composite and pointer paths

Executor request: "Make these supported table actions usable through keyboard,
pointer and the product's assistive setup without changing their meaning."

- Defective fixture: row recycling moves focus to a different record; a grid role
  lacks its interaction model; a reorder shortcut has no non-drag pointer route.
  A count disclosure is cramped, disappears on pointer transfer and contains an
  unreachable action. Async feedback exists only visually; a disabled reason
  depends on hovering a button skipped by Tab.
- Valid control: a reading table has sufficient native links/checkboxes; optional
  simple help and quiet background updates are appropriate.
- Oracle: follow actual composite keys and inspect identity after sort/delete;
  complete the same permitted reorder by keyboard and non-drag pointer. Read and
  dismiss disclosed content, check focus and contextual announcements with the
  supported assistive setup. Inspect semantics separately from actual assistive
  behavior and record unavailable equipment as a gap, not a pass.

## P8: Collection return, load and supported environment

Executor request: "Repair this collection workflow at its supported size and
input environments, preserving agreed view state and selection policy."

- Defective fixture: a narrower filter leaves an invalid page; detail return
  loses agreed query/sort. At supported large cardinality typing blocks. A wide
  touch device gets hover-only controls and supported contrast mode loses focus.
  A localized date changes meaning after a save/reload round trip.
- Valid control: page change intentionally clears selection; transient help and
  secrets are not in URLs; an unrelated small native table needs no virtualization.
- Oracle: late page -> narrow filter -> detail -> Back, and direct entry under
  the declared contract. Profile observed interaction delay before a justified
  optimization and repeat the affected path; check focus/identity if virtualization
  is used. Use applicable real input, contrast and locale conditions rather than
  inferring them from viewport screenshots. Do not add unpromised platforms.

For P3's composition variant, additionally supply a moved inline summary block
whose bounds fit but help/actions are detached from their fields. Include a
header repeating resource nouns and background documentation. Judge grouping and
actual supported completion in both modes. Honor the supplied icon/indicator
preference while preserving accessible meaning and necessary failure feedback;
contrast a valid tree expander and necessary visible explanation.

## P9: Cancel returns to the replaced object

Executor request: "Cancelling a new connection loses the page, and the form
offers Clear instead of Cancel. Repair the create-and-cancel flow on the page
and verify it."

- Defective fixture: Add replaces the selected object's card with a creation
  form. Variant A: Cancel collapses the whole work area into the Add button and
  never restores the card. Variant B: the form has a whole-form Clear and no
  Cancel. An existing test asserts only that the name field is empty afterwards,
  which both variants pass.
- Valid control: with no saved objects the form is the whole work area and has
  no Cancel; an inline add-row disclosure in a visible list may collapse to its
  trigger; a per-field clear stays.
- Oracle: select an object, open Add, enter a draft and cancel from the actual
  control: the previously shown object is visible and focused, the draft is gone
  on reopen, no write occurred and the header action is usable again. Both
  defective variants must fail this check; the empty-state form shows neither
  Cancel nor the header Add. An empty-field assertion or a screenshot of the
  final list alone cannot pass.
- Boundary variant: the object shown before Add is removed by another actor
  while the draft is open; Cancel lands on the next object or the empty-state
  form, never on a blank area.

Unlike P1-P8, this specification was derived from a repair executed in a product
harness, where the oracle was reproduced against both defective variants before
the fix and passed after it. Fixtures for other harnesses remain to be prepared.

## Limits

These tasks are regression specifications once used to develop the skill. Reserve
additional causal variants before a generalization trial; merely renaming an
object does not make a held-out task. State whether fixtures were prepared, their
oracles reproduced, fresh runs executed, or only this specification reviewed.
No practical pass or quality/cost improvement follows from a valid JSON corpus.
