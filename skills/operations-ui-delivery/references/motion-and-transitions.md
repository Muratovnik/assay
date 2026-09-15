# Motion and transitions

Use when designing or repairing animation, reveal, collapse or movement between
views. Motion should make feedback, state or spatial relationships understandable
while keeping the task responsive. A static surface need not gain animation.

## Choose the mechanism for the transition

Inspect existing motion tokens, primitives and supported runtime first. Identify
what changes: a local visual state, disclosure, layout or the same object moving
between presentations. Use a fitting existing CSS transition for simple local
feedback. Consider View Transitions, shared-element techniques or FLIP when
preserving identity across layouts is the task; use supported sequencing or
animation controls when interruption and dynamic values require them. Resolve
the actual gap before adding a dependency, and verify current API behavior in
primary documentation when implementation relies on it.

An API name is not a quality criterion. Preserve the functional state change when
an effect is unavailable. Choose duration/easing from the action and product's
motion language, not a universal millisecond range. Avoid accidental animation
of layout properties; inspect the resulting layout/performance when changing
them is intentional. Transform-only animation does not prove correct geometry.

## Inspect motion between its endpoints

Inspect the running transition, not just its initial and final screenshots.
A shrinking navigation column can wrap a button label midway; a panel can slide
while its portaled header or children pop into place. Trace mounting, layout
and positioning owners before tuning duration or easing. Coordinate their timing
and geometry so the visible parts preserve their intended relationship.

- Failure: endpoints pass, but text jumps, the header skews or a new content block
  displaces the working area while the panel moves.
- Decision: stabilize affected text/layout or coordinate disclosure with available
  space. Do not shorten an animation merely to conceal its defect.
- Valid control: intentional staged reveals and text reflow can be appropriate;
  reduced-motion mode may switch immediately. Neither requires all elements to
  animate together or a single mandated API.
- Check: capture representative intermediate frames or a bounded recording with
  normal motion. Inspect wrapping, clipping, child/parent alignment and final
  placement. Check opening and closing plus supported reversal/repeated input
  where affected. Inspect late-arriving content if it changes the transition.

Verify that interruption reaches the intended state without losing input,
selection or focus, leaving a stale backdrop or blocking the next action. Check
reduced motion separately while preserving meaningful feedback. Disabled-animation
screenshots cannot qualify normal motion; a smooth recording alone cannot prove
correct committed data or keyboard behavior.

If asynchronous object replacement causes the jump inside an open panel, use
[Data lifecycle](data-lifecycle.md#separate-initial-loading-from-refreshing)
to check pending geometry, result identity and late responses.

For a panel changing its layout or modality, use
[workspace consistency](workspace-consistency.md) and
[composed interaction](interaction-and-layout.md#treat-overlays-as-one-composed-interaction).

## Method references

- [Impeccable: choosing and verifying motion](https://github.com/pbakaus/impeccable/blob/8dac6ae7e020c43ab10ce9b41939f6fd42627b96/.agents/skills/impeccable/reference/animate.md)
- [MDN: View Transitions](https://developer.mozilla.org/en-US/docs/Web/API/View_Transition_API/Using)

These inform mechanism selection, not universal timing, platform support or
permission to install a library.
