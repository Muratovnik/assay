# Figwright design-system and library mechanics

Use with [Figwright operations](figwright.md) when the task changes or judges
Figma-specific design-system structure: local versus published components,
cross-file libraries, component properties including slots, library organization,
or movement of published resources. The tool-neutral decisions still belong to
[component system](component-system.md), [design-system organization](design-system-organization.md)
and [visual judgment](visual-judgment.md). This file owns how those decisions map
onto Figma and the current Figwright adapter.

## Separate the Figma platform capability from the adapter capability

Check the current Figwright tool list and schema before planning a write. Figma can
support a component or library mechanism that the connected adapter can only read,
or cannot expose at all. Preserve the intended contract when write support is
missing; do not silently replace it with detach, extra variants or copied layers.

A platform feature documented by Figma is evidence that the design can use that
feature, not evidence that this Figwright session can author it. Conversely, a
Figwright command is not a reason to apply the mechanism when the component or
library contract does not call for it.

## Choose local components or a published library by actual reuse scope

A main component can stay local when its consumers are in the same Figma file.
Use a published library when components, styles or variables need to be reused
across files and receive published updates there. Publishing is a distribution
boundary, not a reward for complexity or a requirement for every repeated product
pattern.

Figma often benefits from separating a reusable library from files where product
design is iterated, because the library can remain a clear source of truth. This is
not a mandatory two-file topology: Figma explicitly allows one library file or
multiple libraries, including libraries that use assets from another library.
Follow the product's existing ownership and consumer boundaries instead of creating
another file only because a component is large.

- Valid control: a product-specific shell used by many screens in one file can
  remain a local component.
- Check: name the consumers that require the resource. If cross-file consumers need
  coordinated updates, confirm the resource is published and those consumers remain
  subscribed; otherwise local linkage can be sufficient.

## Use the right Figma component property

Choose the mechanism from the editing contract rather than from convenience:

- use a variant axis for a finite supported difference such as state, size or type;
- use TEXT or BOOLEAN properties for exposed scalar content/visibility;
- use INSTANCE_SWAP when one nested component instance is replaced by another
  supported component;
- use a SLOT when an instance needs freely variable, repeating or freeform child
  content while remaining linked to the main component.

Slots can carry default content and preferred instances, and Figma documents them
as a way to reduce variant/hidden-layer workarounds and detached instances. A slot
does not mean every container should become freely extensible: the parent still
owns the stable shell and the slot owns only the content region intended to vary.

A stable application shell with reusable navigation and a genuinely variable
content region is a possible slot use case by this contract, not a universal
AppShell recipe. Keep a fixed child or ordinary nested instance when the content
contract is fixed.

## Preserve slots when Figwright cannot author them

At the pinned Figwright implementation used by this skill, `get_component_api`
can report `SLOT` properties, but `set_instance_properties` documents SLOT as
not settable and the component-property authoring handler only creates
BOOLEAN/TEXT/INSTANCE_SWAP properties. Treat this as a capability boundary.

When an existing component already uses a slot:

1. read and preserve the SLOT contract;
2. do not convert it to variant explosion, hidden layers, an instance-swap-only
   API or a detached composition just because the adapter cannot write the slot;
3. use a supported Figma/vendor path only when it is available and authorized;
4. otherwise report the slot mutation as unsupported by the current adapter and
   leave the existing linked structure intact.

Recheck the live tool schema when Figwright changes. This limitation is versioned,
not a permanent statement about Figma or future Figwright releases.

## Organize the Figma library through its real retrieval surfaces

Figma's Assets organization mirrors `file → page → frame`, while component names
and physical grouping also influence related components shown during instance swap.
Use Pages, frames/sections and naming to implement the semantic organization chosen
by [design-system organization](design-system-organization.md), while preserving
existing conventions that already make the catalog understandable.

Do not impose one fixed page skeleton such as `Foundations / Components / Patterns`.
The tool-neutral requirement is findability; Figma pages, frames, sections and
slash-separated names are implementation mechanisms. Keep related families
retrievable and distinguish public resources from internal/documentation material
using the conventions already accepted by the library.

## Move published components without breaking subscribed instances

Moving an ordinary local node and moving a published component across library files
are different operations.

Within one file, Figwright `reorder_nodes` and `reparent_nodes` can preserve the
same node identity as described in [Figwright operations](figwright.md).
`clone_node` creates a new identity and is only a deliberate fork/replacement.

For a published component moved between Figma library files, use Figma's documented
**Move published components** workflow when the task requires existing subscribed
instances to follow the move. Publishing the pasted component **as a copy** creates
a new main component and breaks that continuing linkage. If the current Figwright
adapter does not expose the complete cross-file move/publish workflow, do not
simulate it with clone/reparent and claim that subscriptions were preserved.

- Failure: a published Button is cloned into a new library file, the old main is
  removed and the move is reported complete although subscribed product files still
  point to the old library identity.
- Check: after an authorized published move, verify the destination library state
  and a subscribed instance/update path, not only the existence of a lookalike main
  component in the destination file.

## Build reusable Figma dependencies before dependents

Follow [component system](component-system.md) for the dependency decision. In
Figma, resolve existing local/subscribed library dependencies first, then author or
instance them before building a parent that depends on them. Do not use temporary
copied children merely to let the parent be built earlier.

After creation, read the parent and confirm nested reusable children point to the
intended main components. Figma's official library-generation workflow also builds
components in dependency order, but its atom/molecule naming is an example taxonomy,
not a requirement for this skill.

## References

- [Figma: library fundamentals](https://help.figma.com/hc/en-us/articles/39723547036055-Components-collection-Library-fundamentals)
- [Figma: guide to libraries](https://help.figma.com/hc/en-us/articles/360041051154-Guide-to-libraries-in-Figma)
- [Figma: publish a library](https://help.figma.com/hc/en-us/articles/360025508373-Publish-a-library)
- [Figma: edit main components and linked instances](https://help.figma.com/hc/en-us/articles/360038665934-Edit-main-components)
- [Figma: name and organize components](https://help.figma.com/hc/en-us/articles/360038663994-Name-and-organize-components)
- [Figma: slots](https://help.figma.com/hc/en-us/articles/38231200344599-Use-slots-to-build-flexible-components-in-Figma)
- [Figma: move published components](https://help.figma.com/hc/en-us/articles/4404848314647-Move-published-components)
- [Figma MCP: dependency-ordered component creation](https://github.com/figma/mcp-server-guide/blob/main/skills/figma-generate-library/references/component-creation.md#1-component-architecture)
- [Figma MCP: slot patterns](https://github.com/figma/mcp-server-guide/blob/main/skills/figma-use/references/component-patterns.md#slots-createslot-and-slot-properties)
- [Figwright: component API exposes SLOT](https://github.com/awdr74100/figwright/blob/670b69040f0933728de9a31bb9d8ce920bf3ce44/packages/mcp/src/tools/get-component-api.ts)
- [Figwright: SLOT is not settable through set_instance_properties](https://github.com/awdr74100/figwright/blob/670b69040f0933728de9a31bb9d8ce920bf3ce44/packages/mcp/src/tools/set-instance-properties.ts)
- [Figwright: SLOT authoring is out of scope in the current property handler](https://github.com/awdr74100/figwright/blob/670b69040f0933728de9a31bb9d8ce920bf3ce44/packages/plugin/src/handlers/component-property.ts)

These references describe Figma and the pinned Figwright revision. Always prefer the
capabilities and documentation of the live adapter session when they differ.
