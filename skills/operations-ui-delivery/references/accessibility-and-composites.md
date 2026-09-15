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

- Failure: sorting or virtual row reuse leaves focus bound to a different object;
  a checkbox changes selection but also opens details; a grid role lacks navigation.
- Check: enter, move, activate and leave by keyboard; then sort, remove or reload
  the focused item and inspect the logical next focus and selected identity. Check
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
- [APG: keyboard conventions and disabled controls](https://www.w3.org/WAI/ARIA/apg/practices/keyboard-interface/)
- [WCAG: focus not obscured minimum](https://www.w3.org/WAI/WCAG22/Understanding/focus-not-obscured-minimum.html)
