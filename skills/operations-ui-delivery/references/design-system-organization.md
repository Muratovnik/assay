# Design-system organization

Use when organizing or judging a reusable design system or component library as
a catalog for its consumers: how people find the right resource, distinguish its
role and lifecycle, compare a family and avoid internal or example-only material.
The contracts inside one reusable component belong to
[component system](component-system.md); geometry and visual legibility belong to
[visual judgment](visual-judgment.md); editor-specific moves and naming mechanics
belong to the adapter in use.

## Organize for retrieval, not creation history

Treat the library consumer as a user with a concrete retrieval task. Group and
name resources by stable role and product meaning so a consumer can predict where
to look and distinguish nearby alternatives. Creation order, internal node type or
who authored an item are weak organizing principles when they do not help that
task. A library may use pages, folders, sections, prefixes, search metadata or
another mechanism; no one hierarchy is required.

- Failure: reusable resources, experiments and examples form one flat pile in the
  order they were created, so a consumer must inspect many unrelated items before
  finding the intended control.
- Valid control: five clearly named independent resources can remain in one small
  flat catalog when their roles are obvious; extra hierarchy would add no useful
  distinction.
- Check: start from a consumer need such as "choose the supported control for this
  role" and verify that its name, grouping and nearby context lead to the intended
  resource without knowledge of the file's authoring history.

Information scent depends on labels and surrounding context, while mature
component catalogs such as Storybook expose hierarchy specifically for
categorization, search and filtering. Use that principle without copying another
system's category names.

## Separate the consumer surface from support material

Distinguish resources intended for ordinary reuse from internal building blocks,
documentation/anatomy examples, experiments and lifecycle states such as
deprecated or not-yet-supported material when those categories exist. This is a
semantic boundary, not a required folder layout or prefix convention.

A technical component can remain internal when consumers should use a higher-level
composition instead. Conversely, a public primitive can be the right direct
resource when its contract is intentionally exposed. Existing product conventions
and documented release states take precedence over a newly invented taxonomy.

- Failure: an internal helper and a supported public component are presented as
  equivalent choices, so new consumers bind to the implementation detail.
- Valid control: a small system intentionally exposes its primitives directly and
  has no separate internal tier; do not invent one.
- Check: from the consumer position identify the recommended reusable resource,
  any lifecycle warning that changes whether it should be adopted, and which nearby
  items are examples or implementation support rather than substitutes.

When documenting an existing interface alongside a target system, distinguish
observed-only material, recommended reusable resources and retained exceptions
where those statuses affect adoption. A captured control or an older official-kit
component must not become the supported target merely by appearing in the catalog.
Preserve source/version and unmapped limitations where material, using
[design transfer](design-transfer.md) for correspondence. Do not impose a new tier
on a small system that has no such distinction or silently replace its resources.

## Keep related families and states comparable

A consumer should be able to discover the supported members, states and meaningful
alternatives of a family without searching the whole artifact. Keep a stable
relationship among related resources and expose the distinctions that change
role, state or structure. This does not require one component set, one page, a
fixed grid or a complete Cartesian matrix.

Use [component system](component-system.md) to decide whether two items belong to
one family at all. Organization follows that contract; it must not merge controls
that only look alike or split a family merely to make the catalog symmetrical.

- Failure: default, destructive and loading members of one supported family are
  separated among unrelated examples, while similarly styled but behaviorally
  different controls are adjacent and appear interchangeable.
- Check: locate one family from its role, enumerate the supported differences that
  matter to a consumer, and confirm that an unrelated lookalike is not presented
  as another state of it.

## Make composition levels legible without imposing a taxonomy

Foundations, reusable components, composed patterns and examples often serve
different jobs in mature systems. Atlassian and Primer separate foundations from
reusable components or patterns, while Carbon documents patterns as reusable
combinations that solve user goals. Use these distinctions when they exist in the
product, but do not require those exact levels or names.

The useful invariant is that a consumer can tell whether an item is a source of
shared design decisions, a directly reusable control, a higher-level recurring
composition or explanatory material. A local system that deliberately combines
levels remains valid when the roles are still unambiguous.

## Preserve identity while reorganizing

Organization does not by itself authorize recreation. Moving, grouping, renaming
or documenting an existing resource should preserve its identity, consumers and
overrides when the environment supports that operation. If the requested change
actually replaces, forks or deprecates a resource, use
[component system](component-system.md) for the contract and
[design transfer](design-transfer.md) for structural migration duties.

Dependency order, canonical shared bases and whether a nested entity should be
shared at all belong to [component system](component-system.md). Organization must
preserve those decisions rather than recreate resources merely to place or group
them.

## Judge architecture separately from canvas polish

A tidy canvas can still expose the wrong resources, and a semantically clear
library can still be visually hard to scan. Use this procedure for information
architecture, public/internal boundaries, family discoverability and lifecycle;
use [visual judgment](visual-judgment.md) for spacing, overlap, density, readable
axes and the composed presentation.

A library is not qualified merely because nothing overlaps. Equally, do not fail a
plain but usable catalog for lacking decorative showcases, a fixed page skeleton or
another system's documentation style.

## Method references

- [Storybook: naming components and hierarchy](https://storybook.js.org/docs/writing-stories/naming-components-and-hierarchy)
- [Storybook: documenting components](https://storybook.js.org/docs/writing-docs)
- [Atlassian: parts of the design system](https://atlassian.design/get-started/about-atlassian-design-system)
- [Atlassian: composition and reusable components](https://atlassian.design/get-started/develop/composition)
- [Atlassian: release and deprecation phases](https://atlassian.design/release-phases)
- [Primer: design patterns from foundations and use cases](https://primer.style/product/contribute/design/)
- [Carbon: patterns as reusable combinations](https://carbondesignsystem.com/patterns/overview/)
- [NN/g: information scent and contextual cues](https://www.nngroup.com/articles/information-scent/)
- [Figma: design-system structure for AI workflows](https://help.figma.com/hc/en-us/articles/38978644498199-AI-workflows-collection-Best-practices-to-help-Figma-AI-understand-your-design-system)

These sources support retrieval, role separation and system organization; they do
not make another product's taxonomy, editor structure, naming scheme or release
process mandatory here.
