# Accessibility and composite interactions

Use when changing table/grid semantics, a composite control's keyboard behavior
or assistive access. Reuse the supported platform primitive before implementing
a custom interaction model. Read only the applicable section.

## Match semantics to the interaction

A reading table can contain ordinary links, buttons and checkboxes without
becoming a grid. Preserve header/cell relationships, names and exposed sort state.
A web ARIA grid has a composite focus model: typically one Tab entry and explicit
movement within it. Adding the role alone does not implement that model. Choose
from the task and existing component contract, not a wish to minimize Tab presses.

For tabs, menus, listboxes and other composites, distinguish focus, selection and
activation; use the applicable platform pattern rather than one arrow/Enter rule
everywhere. Automatic tab activation is appropriate only when the panel appears
without noticeable delay. Manual activation can keep navigation usable otherwise.
Do not capture keys needed to edit text or scroll in that component's context.

Choose a role by what it promises: the keys users may expect and what activation
does. Do not take a role whose promise the component does not keep; when no
platform pattern fits, record why and which conventions it keeps instead. When a
composite keeps DOM focus in an input and marks the highlighted option with
`aria-activedescendant`, as a menu with a filter field may, a screen reader's
touch or virtual cursor does not follow that highlight: check that route
separately. A submenu may open as a preview on pointer hover without taking
focus; opening it from the keyboard moves focus into it.

- Failure: sorting or virtual row reuse leaves focus bound to a different object;
  a checkbox changes selection but also opens details; a grid role lacks navigation.
- Check: enter, move, activate and leave by keyboard, counting the Tab stops on
  the way out: a helper such as a clear button adds one only for a reason the
  task supplies. Then sort, remove or reload the focused item and inspect the
  logical next focus and selected identity. Check
  exposed names, relationships and states with existing accessibility tooling;
  use relevant assistive-technology interaction when claiming that behavior works.
- Valid control: a static table's separate controls can remain in normal Tab
  order. Do not convert it to a grid or auto-select on focus as a blanket repair.

## Keep feedback and focus perceivable

Focus must remain perceivable during keyboard work, including with sticky bars,
panels and scroll containers. Do not confuse an element being in the DOM with
visible focus; verify the relevant target after keyboard movement without a test
helper scrolling it into view first. Apply the agreed accessibility level:
WCAG's minimum focus-not-obscured requirement and full visibility are distinct.

Native disabled controls commonly leave the Tab sequence. If a restriction's
reason is needed, make it available through associated visible context or a
fitting discoverable control. Where a composite convention keeps disabled items
focusable, expose the disabled state and prevent the real action; ARIA alone
does not enforce it. Do not force every disabled control back into Tab order.

In a design artifact, check that text, states, focus and action areas are
distinguishable, and hand the keyboard, focus-order and semantic requirements
to the implementation explicitly; in code, verify they actually execute. A
static mockup does not prove accessibility. Choose numeric thresholds such as
target size or contrast from the adopted platform and standard with its
exceptions, not from a universal button size.

A chart whose values users must read needs a text route to them, and a keyboard
route to individual points where the task compares or inspects points.

For async completion/error announcements use
[Content](content-and-recovery.md#announce-meaningful-updates); exposed text and
a live-region attribute alone do not prove an understandable announcement.
For replacement of dragging use
[Interaction](interaction-and-layout.md#provide-an-alternative-to-dragging).
For contrast themes and non-color state cues use
[Visual judgment](visual-judgment.md#preserve-meaning-across-display-modes).

## Primary references

- [APG: table](https://www.w3.org/WAI/ARIA/apg/patterns/table/)
- [APG: grid](https://www.w3.org/WAI/ARIA/apg/patterns/grid/)
- [APG: tabs](https://www.w3.org/WAI/ARIA/apg/patterns/tabs/)
- [APG: combobox](https://www.w3.org/WAI/ARIA/apg/patterns/combobox/)
- [APG: menu and menubar](https://www.w3.org/WAI/ARIA/apg/patterns/menubar/)
- [Base UI: a filterable menu, worked through keyboard, pointer and screen reader](https://base-ui.com/blog/building-a-filterable-menu)
- [APG: keyboard conventions and disabled controls](https://www.w3.org/WAI/ARIA/apg/practices/keyboard-interface/)
- [WCAG: focus not obscured minimum](https://www.w3.org/WAI/WCAG22/Understanding/focus-not-obscured-minimum.html)
