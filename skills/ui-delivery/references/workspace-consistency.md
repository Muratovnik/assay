# Workspace consistency

Use for repeated flows, shared shells, headers, panels or space/scroll allocation.
Scope the affected family; a distinct task need not adopt identical layout.

## Follow consumers and entry paths

Map changed components, styles and state owners to actual screens and compare
equivalent work: identity, actions, selection, disclosure, save/cancel and recovery.
A shared table does not unify its surrounding create/edit forms. Include affected
direct entry, reload and return paths; navigation from a new page can conceal
missing initialization. Repair the shared cause or bypassed primitive when found;
read-only details and bulk editors can legitimately differ.

For a broad replacement, preserve supported saved views, navigation, deep links
and input before retiring entry points. Prove a representative path before wider
migration when useful, then cover its consumers. Preserve outcomes, not obsolete
widgets. Compare same-role controls in actual themes/containers: matching tokens
do not prove matching computed colors, padding or text bounds. Use a fitting
shared variant; a numeric label may not fit an icon-sized trigger. Reuse agreed
selector behavior without adding search to every short fixed choice.

## Derive states and size owners from the source

List required functional states from the brief, scenarios and the source's
behavior or code: selection, disclosure, loading, error, empty and recovery,
separately from hover/focus/disabled. Do not read the expectation off the
variants that already exist; an expanded/collapsed navigation that the product
supports is required even when no variant was drawn. Pick width, theme and
content axes from the product and give a local edit a local matrix; a full
Cartesian product is not required.

Decide who owns each size and behavior: content-driven, stretching, fixed or a
structurally different variant. Check short and long text, item counts and an
intermediate size between reference frames. Two copies drawn at two capture
widths do not prove adaptation; when only the size differs, a resize contract
usually suffices, and a genuinely different composition may earn a variant.
FIXED sizing, a scroll region and an absolute overlay are valid when they match
the role. Where an accessibility standard applies, also check that enlarged text
and user spacing keep content and actions reachable; that is a robustness check,
not a mandate for looser spacing everywhere. For the shared base and its
consumers use [Component system](component-system.md); this file does not
define a second component model.

## Compare semantic columns across tables

When related screens show the same objects or fields, map columns by meaning
rather than position. Agree useful minimum/preferred widths and which columns
receive spare space, accounting for selection, drag handles, row actions and
additional numeric/detail columns. Reuse a fitting shared sizing policy or
explicit variant; equal percentages in tables with different columns do not
establish consistency.

Compare the same representative short/long values at comparable usable table
widths, with relevant panel and navigation states. Inspect the boundary between
identity and category/value columns, wrapping/truncation, scanning and action
reachability. Matching CSS, total table width or absence of overflow can all pass
while one screen needlessly compresses an identity column and another wastes its
space. Relate measurements to the intended composition, not arbitrary pixel parity.

Different tasks, extra columns and constrained panels can legitimately change
final widths. Preserve those differences while keeping common fields recognizable
and usable; do not freeze every table to one width or reorder data to match a
visual grid. Use [Visual judgment](visual-judgment.md) for composed acceptance.

## Preserve collection context deliberately

For changed search, filters, tabs, sort, page or detail navigation, identify the
state owner and intended lifetime: local view, return navigation, reload or shared
URL. Place controls with the population they affect; a list filter should not
appear to filter unrelated tabs or the whole application. Use existing routing
and preference mechanisms, not serialization of every UI state.

Check a later page -> narrower filter -> item -> return, plus Back/Forward and
direct entry where supported. Reconcile an invalid page index rather than showing
a false empty result. Restore the agreed query/position and destination after
supported sign-in; a direct link cannot depend on history that never existed.
For changed selection lifetime use [Selection](selection.md).

Local transient disclosures and sensitive draft values need not enter the URL.
Selection reset on page change can be an explicit product contract; do not replace
it with hidden persistence. Reusing the browser's normal links/history may suffice.

## Check the supported environment

Choose input methods independently of viewport width: a desktop can have touch
and a tablet a keyboard. Exercise the relevant non-hover route rather than treating
a narrow screenshot as touch coverage. Respect supported locales and direction;
check long names and formatted numbers/dates against the same underlying meaning,
including the product's time-zone contract where relevant. Translation should
not change identity, quantity or ordering semantics.

Do not add mobile, RTL or language support absent from the brief. For existing
contrast themes, state cues and focus use
[Visual judgment](visual-judgment.md#preserve-meaning-across-display-modes).

## Adapt to the space that actually changes

For web components whose arrangement depends on their allocated space, prefer
container size queries over viewport breakpoints when a conditional layout is
needed and the supported runtime permits it. A form or table beside a drawer
can become narrow while the browser window stays wide. Keep layout and conditions
separate: Grid/Flex define arrangement; container/media queries determine when
styles change, including Grid/Flex styles. They are complementary tools, not
interchangeable alternatives. Establish whether the task needs a conditional
style change at all; automatic sizing/wrapping can already satisfy a simple
layout without an additional condition.

Choose the ancestor that owns the available space as the query container, using
`container-type: inline-size` when only the inline dimension matters. A size query
styles descendants, not the queried container itself. Check containment's effect
on sizing and the intended ancestor in nested layouts; name the container when
needed to avoid querying an unrelated nearer one. Do not add containment to every
wrapper, assume content-driven height survives full size containment, or introduce
JavaScript measurement when supported CSS suffices. Verify target support and
provide a fitting fallback when required by the existing browser contract.

Keep media queries for actual viewport-level composition or environmental
conditions such as `hover`, `pointer` and `prefers-reduced-motion`. Neither
container width nor viewport width establishes those capabilities/preferences.
Do not replace valid media conditions indiscriminately, or remove Grid/Flex when
adding queries. Choose the condition independently of the layout mechanism.

Check a fixed viewport while opening/closing the neighboring drawer, resizing
an existing split pane or otherwise varying the component's allocated width.
Exercise relevant narrow/wide layouts and boundary transitions while mounted,
with real content, retained input/focus and reachable actions. Test viewport
changes separately when they affect the shell. Window-resize screenshots or the
presence of `@container` alone cannot establish container-responsive behavior.

## Give regions useful space and scroll

Determine which document, shell, navigation, table and panel should scroll. Let
children use available composition space; viewport-minus-constant heights can
ignore wrapping headers, filters and errors. Inspect descendants creating scroll
extent, including offscreen accessible labels, rather than deleting labels or
hiding all overflow. Long documents, overflowing navigation and wide data tables
can legitimately scroll.

Check empty and realistically dense content, long/localized values and zoom.
Scroll each relevant region and observe which others move or clip. Assess useful
height and width together: redundant headers/status/toolbars may crowd work, while
unrelated containing blocks leave blank space above panels or below tables.
Align useful areas of one workspace without forcing equal outer heights. Keep
necessary identity/warnings and valid short independent forms.

Choose window sizes from the operating environment; compact desktop does not
require a new mobile product. Inspect relationships between row identity, values
and actions at wide and compact sizes. Zero overflow does not prove scanability
or reachability. Do not force a density ratio, fixed width or full-height panel.

When empty side space coexists with cramped fields, judge the whole composition,
not just table width. Trace width limits, alignment and gutters to the shared
workspace owner and check equivalent pages. Centering, reserved space and fluid
width are alternatives, not universal rules; intentional whitespace can aid focus.

## Separate wayfinding, identity and actions

Give breadcrumbs, title, status and actions distinct jobs. A compact path above
the title is one useful option. Allocate absent/loading/long path states so late
content does not accidentally shift the title or actions. Recompose or reserve
space rather than hide identity or use illegible text. Contract long paths with
an operable disclosure for hidden ancestors; preserve current context across
sidebar, title and navigation.

Check the header with the work area, long labels and collapsed/expanded navigation.
Flat pages without breadcrumbs, intentional reflow and product-specific current
page links remain valid. Follow the product/accessibility contract; public systems
disagree on current-page links. No universal crumb placement or layer count applies.

## Support the task with panels

Compare open/closed composition. Inline comparison or an overlay can fit different
space/task needs; do not invent adaptive modes or universal breakpoints. When
adaptation exists, resize inline → overlay → inline while editing. Check retained
draft/selection, focus, backdrop, scroll and parent completion; cold-start tests
of both modes miss remount losses and stale focus traps. For modality changes,
read [Interaction](interaction-and-layout.md#treat-overlays-as-one-composed-interaction);
for animated adaptation, read [Motion](motion-and-transitions.md).

When a side block moves into document flow, recompose its labels, values, help
and actions for that available space; stacking the old sidebar box may preserve
its awkward gaps and detached controls. Compare both mounted modes with realistic
content and inspect reading order, grouping and the relation of help to its field.
Check useful action alignment and hit areas, not only container bounds or retained
state. Different internal layouts can legitimately serve the two modes.

Choose the spatial anchors that should survive opening a supporting panel: for
example the workspace boundary, title or leading content edge. Switching from a
centered capped body to an uncapped split layout can move the entire workspace
even when both endpoints fit. Allocate panel space at the common container when
appropriate; do not animate an avoidable displacement merely to smooth it. Compare
anchor positions before, during and after open/close across affected pages and
navigation widths. Also verify useful remaining column/field width. Preserve
intentional reflow or a deliberate mode change rather than freezing every pixel.

A supporting nonmodal panel must leave the parent's Create/Save reachable by
pointer and keyboard. Reflow or use a shared action location, preserving object
scope; panel-local Add/Apply is not necessarily parent Save. Exercise completion
while the panel remains open on affected create/edit/library paths. DOM presence,
z-index changes or helper dismissal cannot prove this. An intentional modal
confirmation/prerequisite may suspend parent work; preserve its return path.

## Method references

- [Impeccable: classify drift](https://github.com/pbakaus/impeccable/blob/8dac6ae7e020c43ab10ce9b41939f6fd42627b96/.agents/skills/impeccable/reference/polish.md)
- [gstack: find consuming pages](https://github.com/garrytan/gstack/blob/0d1bd5616c0ef096bb7ccee336f63c60ee408618/qa/sections/qa-patterns.md)
- [Pajamas: panels](https://design.gitlab.com/components/drawer/)
- [Navigation patterns](https://github.com/jpoindexter/ux-flow-skills/blob/fc7f4a4b913dc5b1a2029af16fb8ec363331c821/skills/flow-navigation/SKILL.md)
- [Pajamas: breadcrumbs](https://design.gitlab.com/components/breadcrumb/)
- [Cloudscape: collection filter persistence](https://cloudscape.design/patterns/general/filter-patterns/filter-persistence-in-collection-views/)
- [Impeccable: adapt to actual input and environment](https://github.com/pbakaus/impeccable/blob/4bee58d89e4b3d3b4a1c44cfd2445dce03cf09e6/.agents/skills/impeccable/reference/adapt.md)
- [MDN: container size queries and containment](https://developer.mozilla.org/en-US/docs/Web/CSS/Guides/Containment/Container_queries)
- [MDN: media query conditions](https://developer.mozilla.org/en-US/docs/Web/CSS/Guides/Media_queries/Using)

Use their methods, not their fixed design values, tooling or gates.
