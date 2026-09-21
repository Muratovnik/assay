# Interaction and layout

Use for hit areas, actual gestures, popup geometry or composed overlays.
Inspect the control in its real container. Read only the relevant sections;
animation mechanics belong to [Motion](motion-and-transitions.md).

## Align feedback and the hit area

Hover, cursor, focus and active feedback must describe the action at that location.
Do not make a static heading or blank form-group area look editable when only a
child responds. Separate row selection, expansion, editing and deletion so nested
actions do not propagate accidentally. Preserve useful associated labels and
genuinely clickable whole rows; hover alone cannot carry essential information.

For row details, inspect the resting presentation before hovering or clicking:
can the user identify where and how to open the object? Use a fitting visible
link, labeled action or recognizable disclosure with accessible semantics; a
hidden handler on one unmarked cell is insufficient. Then exercise that trigger
by pointer and keyboard, keeping selection, drag and other row actions separate.
A clear dedicated link is valid; do not make the whole row clickable or add a
chevron everywhere. A test aimed at a known hidden coordinate proves activation,
not that the user can discover it.

Place a row's indicator in relation to what actually opens or expands. A leading
tree expander and a trailing details indicator imply different interactions;
do not add a second apparent target when the row already has one coherent action.
Respect the product's placement and reading direction. Check row, indicator and
nested actions together; no universal right-side chevron follows.

Probe inside, at the edge and outside the intended target, including nested icons
and spacing; check keyboard and supported touch access. For frequent controls,
consider actual target size, travel distance, stable placement and nearby actions.
A center click can pass despite a dead strip at an expected edge. Adjust placement
or expand the hit area without overlapping a neighboring command.

A physical screen edge may stop a pointer; an internal panel boundary does not.
Use platform/input guidance without equating CSS pixels, points and dp or minimum
size with comfort. Test relevant window states. System insets, touch gestures,
window frames and controls inside content can legitimately need padding; no
universal edge-placement or zero-padding rule follows.

## Enforce availability through the gesture

A disabled attribute may leave a drag engine, row handler or keyboard command
active. Synchronize the actual mechanism with current availability, including
changes while mounted, and prevent forbidden effects at their responsible owner.
Attempt the real gesture and assert unchanged draft/order/data when forbidden,
then verify the allowed control. Direct helper calls or attribute assertions do
not prove enforcement. Read-only content can still allow copying or details.

For an action that never becomes available, also use the prerequisite-to-action
check in [Actions and scope](actions-and-scope.md#put-frequent-work-where-it-is-needed).

## Provide an alternative to dragging

When a supported operation uses drag, establish equivalent permitted outcomes
through keyboard and a single pointer without dragging. These are separate
requirements: a keyboard shortcut alone does not help a touch user unable to
hold and move. Use fitting move/assign commands or the existing component's
alternative, preserving scope, ordering and availability constraints.

Complete the same operation by each relevant route and inspect the actual effect.
Do not add custom controls for ordinary browser scrolling, or erase applicable
exceptions where a trajectory is essential to the operation.

## Make disclosed help usable

For content revealed on hover or focus, check that users can reach and read it,
move the pointer onto it where applicable, dismiss obstructing content and keep
it visible until they finish. Essential information needs an available route on
supported non-hover input too. Interactive links/actions need a suitable popover
or other component, not a tooltip that disappears when approached.

Inspect the rendered trigger and disclosure together: anchor distance, padding,
wrapping, background/text contrast and hierarchy of real values. A comma-joined
list may need a compact structured presentation when identities become hard to
scan. Use existing surface tokens; a themed portal or correct position alone
does not prove readable content. Check focus/pointer opening, pointer transfer,
dismissal and long values in the actual container. Do not add help that merely
repeats a clear label or force every short value into a list.

## Design geometry across transitions

Size by content's job: a compact trigger may open a wider popup that remains
anchored and within the viewport. Use existing positioning facilities for clipping
ancestors, scroll containers, collisions and long values. Reserve appropriate
space for badges/validation or choose a compact disclosure; do not hide identity
or shrink text into illegibility to keep a screenshot stable.

Compare applicable rest, hover, focus, selected, loading and error geometry with
short/long values and narrow/zoomed views. Intentional expansion or localization
reflow is valid. Inspect transient rendered elements: portaled content and drag
previews can lose inherited fonts, theme or table widths. Check the active element
against its intended anchor; a deliberately compact drag summary need not clone
the row. Animated geometry additionally needs the Motion procedure above.

## Resolve coexisting states

Where states can coexist, define their combined result and the owner of each:
selection does not disappear under hover, focus stays distinguishable over
selected or invalid, and a disabled item keeps its selected identity where the
product says so. Check the meaningful combinations for text, icon-plus-text and
icon-only forms of the same family; the default form passing does not clear a
new combination. Do not install one universal priority order or a full
Cartesian product of states. An intended runtime overlay is judged by its
behavior; accidental overlap of examples on a canvas belongs to
[Visual judgment](visual-judgment.md#inspect-geometry-at-the-affected-depth).

## Treat overlays as one composed interaction

Choose modality from the task. Establish which layer owns focus, Escape, outside
interaction, scroll locking and backdrop emphasis. Use the shared layer primitive
instead of arbitrary z-index or independently accumulated backdrops. Nested menus
and popovers are part of the composition; nested dialogs are not categorically
wrong, and deliberate depth differs from accidental double dimming.

Enter from the real trigger, tab through, open/dismiss a nested surface, continue
editing, then close the parent. Check one coherent active interaction, no duplicate
traps or double Escape dismissal, correct scroll/background behavior, preserved
input and logical returned focus. If the trigger disappeared, choose a meaningful
next target. For changes to panel placement or inline/overlay adaptation, also
use [Workspace](workspace-consistency.md#support-the-task-with-panels).

## Primary references

- [WAI-ARIA: modal interaction](https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/)
- [W3C: target size and exceptions](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html)
- [W3C: non-drag alternatives](https://www.w3.org/WAI/WCAG22/Understanding/dragging-movements.html)
- [W3C: hover/focus content](https://www.w3.org/WAI/WCAG22/Understanding/content-on-hover-or-focus.html)
- [Affordances: target geometry](https://github.com/Intense-Visions/harness-engineering/blob/5cd661d74a7cb4e3b4164a8c7fb36d75e298fd0f/agents/skills/claude-code/design-affordances/SKILL.md)
- [Impeccable: controls and clipping](https://github.com/pbakaus/impeccable/blob/54f0e641c600f4dd6c199323ae64996ead8cb5ec/.agents/skills/impeccable/reference/operate.md)
- [Vercel: implementation checks](https://github.com/vercel-labs/web-interface-guidelines/blob/e3d624baaf29dc1fc645aff3e38f03e564d2d6b1/command.md)

Adapt principles; do not import platform values or framework mandates wholesale.
