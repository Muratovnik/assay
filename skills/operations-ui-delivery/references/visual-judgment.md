# Visual judgment

Use for a requested visual critique, distinctive design or cleanup of a generic
interface, and for judging the composed result of any created, implemented or
transferred UI artifact: a screen, a mockup, a component library or its code.
Evaluate the actual audience, task, brand and rendered composition; match the
depth of the check to the ordered artifact. Structural links and property
effects belong to [Component system](component-system.md); sizing behavior of
screens and containers to [Workspace](workspace-consistency.md).
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

## Establish which source governs each decision

When several sources exist, assign authority by question: the product's behavior
contract answers what a control does, the current library or API answers what
exists to build with, normative tokens answer intended values, the observed
render answers what the build actually does and a visual reference answers how
it should look. Check which theme or token source the build or instance really
uses. Name a discrepancy with documentation and resolve it by the standing
product decision; the runtime is not automatically right, and a convenient
value must not be chosen silently. In a transfer compare essential properties
with the source; in a new design compare with the brief and the agreed system.
A local task needs only its affected sources; do not require a new
design-system document or a rewritten owner instruction.

## Check tokens, fonts and theme through the composition

Choose a token by semantic role and source, not by a matching color value.
Verify the actual font family, weight and line-height at the consumer; a
foundations showcase and a bound size do not prove the right font on the screen.
Theme must pass through nested instances, surfaces, text, borders and overlays:
check mode/theme overrides and resolved values where the chain can break. Account
for ancestor paint in the final surroundings: fill, opacity, radius, clipping,
gaps and seams. A neutral wrapper must not add a surface by accident; a
transparent wrapper and a deliberate local fill are both valid when they match
the role. Do not mandate one variables collection, theme variants, styles,
native slots, guides, annotations or code mapping; pick the mechanism that
delivers the needed change with maintainable handoff.

- Failure: a dark parent contains a nested instance left on the light theme; a
  white rectangular wrapper shows at the corners of a rounded control.
- Check: read resolved values and overrides on the nested elements, and inspect
  the composed render in each affected theme, not the theme name.

## Inspect geometry at the affected depth

This file owns the depth rule; other procedures link here. After an edit,
check the bounds of the content, its parent, the component set or section and
the affected neighbors. Checking only the top-level children misses variants
overlapping inside a set or a background bleeding through correct children.
State the actual traversal depth of any geometric claim and do not declare the
whole file sound from one sample.

Distinguish an intended runtime overlay (popup, modal, stacked surface) from an
accidental overlap of independent examples on a canvas. Check clipping,
reachability of the last element, focus rings, padding/gap, wrapping and voids.
Do not cure a wrong height owner with successive manual resizes; fix the owner
of the size. A library is itself a composition to judge: meaningful grouping,
stable order and readable axes let a user find the current element and compare
variants. Zero intersections do not prove legibility. Do not impose one page
skeleton, fixed grid or mandatory showcase set on every project.

## Keep asset provenance

Keep the origin and a fitting lifecycle for every asset used. A temporary tool
link can serve a preview, but a delivered result obtains its resource through
the accepted asset pipeline or a stable dynamic source. Verify the intended
variant, size/aspect ratio and how the asset is fetched after the session ends.
Do not replace an exact asset with an approximate glyph because of a similar
name; a one-off preview and a standard CDN or API are both legitimate.

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
