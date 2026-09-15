# Visual judgment

Use for a requested visual critique, distinctive design or cleanup of a generic
interface. Evaluate the actual audience, task, brand and rendered composition.
Reuse supplied visual references; a popular font, component library or color is
not evidence of poor design or of how the work was produced.

Inspect hierarchy, density, alignment, type scale, contrast, spacing and the
relationship between actions and content. Repeated cards, gradients, decorative
icons and generic copy are questions to investigate, not defects by syntax.
Explain what an observed choice obscures, wastes or contradicts in this brief.
Source can confirm a CSS value; pixels and interaction establish its effect.
Label unavailable visual evidence rather than pretending to have seen it.

Judge the composed screen after component fixes: working controls and smooth
motion do not prove a clear next step or useful space allocation. Compare primary
task prominence with maintenance actions, cramped fields with surrounding blank
space, and help/disclosure placement with the text it explains. In empty or
prerequisite states, check whether the next supported action is apparent. Do not
invent missing calculations from a screenshot alone or add explanatory clutter
when the existing controls already communicate the dependency.

For a supplied reference, identify which hierarchy, density, grouping, controls
and visual encodings serve the brief. Separate them from illustrative data or
functions the product does not support. Removing invented features does not
justify dropping useful category markers, bulk actions or spatial relationships.
Compare reference and candidate at comparable viewport and content conditions;
check both the composition and working controls rather than matching CSS values.
This is not a mandate for pixel identity or for implementing fictional features.

Record later user preferences in the product's existing requirements or task
criteria. They govern subsequent work, but do not retroactively make an earlier
reference-matching choice a defect or become universal rules for other products.

Respect intentional consistency. A single system font, repeated layout or
familiar accent can be the right choice. Reusing an appropriate solution across
projects is valid; novelty and a second typeface are not acceptance criteria.
Apply the product's accessibility and behavior contracts even when the requested
change is primarily aesthetic.

For a scoped correction preserve valid structure and tokens. For an authorized
redesign choose a coherent direction and implement it at the agreed scale;
explain only the decisions that help assess the result. Ordinary reversible
choices need no per-control approval. Pause only for an explicit approval
boundary or consequential unresolved preference. A review-only request returns
findings and proposals without editing the product.

Inspect the rendered result when possible and judge it against the original
brief. Show a useful preview without turning it into an automatic stop. Separate
what was observed, checked automatically and actually approved by the user.
If the design already serves the task well, a clean assessment is valid.

## Optional composition pilot for new surfaces

For an authorized new screen or open-ended redesign, a short synthesis pass may
help: identify the main operation and its required nearby information, choose
workspace regions, then implement a representative working slice using actual
content and an important non-happy state. Judge the whole composition before
propagating it to other screens. A dense row, failed form or editor with a panel
is more informative than an isolated decorative card.

This is an opt-in pilot, not a new approval gate or mandatory planning document.
Do not apply it to a local repair, generate a fixed number of concepts, choose a
style randomly, or replace accepted tokens. Its incremental benefit over this
procedure is unmeasured; qualify it with the existing skill-evaluation method
before making it a default. Record accepted choices in the existing product owner.

When repeated source-discovery failures justify it, the optional
[UI source fingerprint command](ui-source-context.md) can verify explicitly named
source paths and bytes. It does not infer authority, create DESIGN.md, or prove
that the implementation follows those sources.

## Preserve meaning across display modes

For affected supported themes and contrast modes, verify meaningful state and
focus remain distinguishable when color or decorative shadows are unavailable.
Use appropriate text, shape, icon or pattern as well as color; do not replace
every cue with extra prose. Check the actual control and active/focus/selected
states in their container, including forced colors where applicable. A token
contrast check alone cannot show that the focus outline survived rendering.

Preserve deliberate branding and existing sufficient cues. Do not introduce a
new theme as a prerequisite for a local visual repair. Keyboard and assistive
interaction additionally use [Accessibility](accessibility-and-composites.md).

[Impeccable: robustness and accessibility](https://github.com/pbakaus/impeccable/blob/4bee58d89e4b3d3b4a1c44cfd2445dce03cf09e6/.agents/skills/impeccable/reference/harden.md)
provides supporting patterns, not a replacement for the product's requirements.
