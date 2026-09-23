# Figwright operations

Use before the first substantive operation through the Figwright adapter for
Figma — reading a file for implementation, building or editing a design,
authoring components, variants, properties or styles, organizing a library, or
visual acceptance through that tool. It complements the vendor `figma-build`
and `figma-codegen` skills instead of repeating them: they own how a value is
grounded and which binding path a token takes. With a different adapter, that
adapter's documentation applies and none of the command names here carry over.

## Confirm the connection and the target file

Confirm the plugin is connected (`ping`) and look at the command set this
session actually exposes before planning a write. With more than one file open,
claim the target through the documented mechanism when the current schema
offers it — `list_files` names the connected files and `use_file` claims one,
by session identity when two open files share a name. Unclaimed calls follow
whichever file the user last touched, so a task can read one file, write to
another and still report success.

Re-confirm identity and a known page/node anchor after a reconnect, a restart
or resume, and after any change in the set of open files. A file name is not a
unique identifier. If identity cannot be confirmed, keep that as a stated gap
and resolve it before any write whose target is ambiguous; never accept an
untitled document or whichever tab is in front as the target. Continuing from a
read that names its own page/node anchor is legitimate when no claim mechanism
is exposed — what is not legitimate is guessing.

## Read the vendor documentation for the operation you chose

Read it before choosing the method, not after a call fails:

- any write — `figma-build/SKILL.md` and `write-rules.md`;
- assembling a screen or section — `assemble-screens.md`;
- masters, variant sets, component properties, variables and styles —
  `author-design-system.md`;
- Figma library boundaries, published/local resources, slots, cross-file moves or
  design-system organization — [Figwright design-system mechanics](figwright-design-system.md);
- implementing a design in code — `figma-codegen/SKILL.md` with the applicable
  grounding, mapping and asset references.

For the chosen operation read its schema: the allowed node types, the required
order and the side effects. Rereading an unchanged section before every call is
unnecessary — read once per kind of operation, then work.

## Resolve a gap from the schema and the primary source

Missing or stale documentation is resolved from the current tool schema and the
primary source, not by tuning parameters across the whole file until something
looks right; probe on one characteristic node instead. A capability the tool
offers is not an obligation to apply it to every composition.

Upstream `main` does not prove a command exists in this client. Where the
documentation and the exposed tools diverge, take the confirmed available path
and say which one you took. Never call an invented command, an invented motion
or exposure API, or another backend's tool.

## Check every result before the next dependent call

Check the transport result, the MCP `isError` flag and the operation's own
documented confirmation for every call. A JavaScript wrapper that returns
successfully does not prove the nested tools inside it succeeded.

On a failure, stop the dependent actions, reread the affected state and account
for a partial write: earlier successful writes are not undone by a later error
and must not be blindly repeated. Reporting success unconditionally after a
loop is forbidden. Independent work that did succeed is not thrown away — name
what stands and what does not.

## Verify the effect, not the acknowledgement

After the last write of a step, verify the identifiers and property keys, the
link to the receiver, and the visible effect including nested compositions. A
summary `ok`, an API listing and a default that happens to match the drawn text
are not evidence of an effect.

For a multi-node write, compare the expected set of affected identifiers with
the actual one. Nonexistent or unsuitable nodes can be skipped while the call
still reports `ok`, and an equal count does not prove an equal set. A
best-effort write allowed by its own contract may legitimately leave gaps —
those gaps stay in the reported result instead of turning into a pass.

## Match the intent to a method

| Intent | Method and the distinguishing check |
| --- | --- |
| Inventory, or read for implementation | `get_design_context` at sufficient detail; expand the truncated or deduped part you will build from and follow a `sectionPlan` section by section. A field missing from a compact answer is not a missing property. Check component/token/icon maps by role: the render shows the look, the tree shows links and values. |
| Assemble from the system | `create_instance` the matching component or swap an existing one; read the contract with `get_component_api` and pass the exact current keys. Verify the overrides and one real consumer — a matching resource name does not prove compatibility. |
| Adaptive sizing | Parent layout → append the child → `set_layout_props` for HUG/FILL and min/max per the contract. `resize_nodes` can force sizing to FIXED: use it when a fixed size is the intent, and check the resulting behavior rather than the number. Screen, panel and container sizing stays in [workspace consistency](workspace-consistency.md). |
| Variants and properties | Name members `Prop=Value` before `combine_as_variants`, then read the derived axes back. A non-variant property is declare → bind to the correct sublayer → read → change on an instance → check the render; `bind_component_property` attaches TEXT to `characters`, BOOLEAN to `visible` and INSTANCE_SWAP to `mainComponent` per the current API. Which part should own a property is a [component system](component-system.md) question. |
| Themes and shared finishes | Distinguish a color binding on the paint (`bind_variable_to_paint`), a scalar binding on the node (`bind_variable_to_node`) and a composite `apply_style_to_node`. When replacing a paints or effects array, carry the needed `boundVariables` through or the style stops tracking its token. Check nested mode/Theme overrides and the composed result; the judgment itself is [visual judgment](visual-judgment.md). |
| Structural replacement | Preserve parent, order, grid row/column/span, sizing and the required links; verify the new node in its container before deleting the source. After a combine, rename or reparent, reread identifiers and property keys, suffixes included. Source fidelity and the allowed delta belong to [design transfer](design-transfer.md). |
| Organizing an existing library | Read [Figwright design-system mechanics](figwright-design-system.md) when publication boundaries, slots or cross-file libraries matter. For order within the same parent use `reorder_nodes` (nodeIds, index); for a move into another container use `reparent_nodes` (nodeIds, newParentId, optional index). Both re-insert the same node, so component identity, keys and main-component links survive, while coordinates become relative to the new parent — read positions back. Both skip missing or detached nodes and return `{ ok, affected }`: compare `affected` with the requested set. `clone_node` duplicates the subtree as a new sibling with a new id; use it only for an ordered fork or replacement, never as a hidden substitute for moving. These three names come from the Figwright source at the pinned revision below, not from the vendor skills; recheck the exposed tool list before relying on them. Verify identifiers, keys, overrides, parent/order and geometry afterwards. |
| A dependent series of reversible writes | Consider the documented `batch` when the operations, identifiers and dependencies are expressible in its contract, and check each result as well as the total. Keep destructive or non-batchable actions as separate verifiable stages. A single operation needs no batch. |
| Visual acceptance | Export the composition after the last write — `get_screenshot` on the node you changed — and confirm the result is non-empty and current; an `empty: true` export rendered nothing. An image of an asset does not replace a screenshot of its placement. The required evidence level is [acceptance](scenario-testing.md). |

For authored animation the vendor `motion` reference owns the Figwright command
path; what should move, and whether it should move at all, stays in
[motion](motion-and-transitions.md).

## Classify a failure before retrying

Distinguish a wrong method, a violated order, an API limitation and an unknown
cause — the repair differs, and retrying the same call answers none of them. A
limited compatible fallback is acceptable only while it keeps the same required
contract; a new variant axis or a detach is not a fix merely because the
command returned success.

A documented rollback is a mechanism, not proof of restoration. When an undo
fails or leaves residue, reread the affected nodes and their surroundings
rather than restarting the chain on the assumption that everything was
reverted. Finish a destructive stage only after the required links and
consumers have been verified. For an API that reaches inside a nested instance,
use a read/write mechanism confirmed in this client: platform support for
exposed instances does not prove the adapter supports it.

## Recovery when a binding owner cannot be resolved

If the current version cannot resolve the owner of a property binding inside a
variant set and the call comes back with a `get_componentPropertyDefinitions`
error, check two things before changing the design: the hierarchy you passed,
and how the adapter resolves the owner. `bind_component_property.nodeId` stays
the target sublayer, never the component set, and the property must exist on
the containing component — so a hierarchy mistake and an adapter defect look
alike from outside.

With the defect confirmed for the version in use, one workable path is: author
the component standalone → declare and bind the property → verify the effect →
clone or combine into the set → read the fresh keys, which change on combine →
re-verify the old and new instances and the render. That is a route around one
confirmed defect, not a general ban on binding inside variant sets and not
permission to take a library apart. Record the version and the observed
behavior alongside the result, and do not pin a version, a quota or a
workaround forever — recheck it when the adapter changes.

## Primary references

- [Figwright figma-build](https://github.com/awdr74100/figwright/blob/670b69040f0933728de9a31bb9d8ce920bf3ce44/skills/figma-build/SKILL.md)
- [Component property binding handler](https://github.com/awdr74100/figwright/blob/670b69040f0933728de9a31bb9d8ce920bf3ce44/packages/plugin/src/handlers/bind-component-property.ts#L59)
- [Component property owner resolution](https://github.com/awdr74100/figwright/blob/670b69040f0933728de9a31bb9d8ce920bf3ce44/packages/plugin/src/handlers/component-property.ts#L44)
- [Figma: generate design](https://github.com/figma/mcp-server-guide/blob/ecefd5b5dfd0ca7a1b8f142e0d59bc7f8a2efde6/skills/figma-generate-design/SKILL.md)
- [Figma: component creation](https://github.com/figma/mcp-server-guide/blob/ecefd5b5dfd0ca7a1b8f142e0d59bc7f8a2efde6/skills/figma-generate-library/references/component-creation.md)
- [Figma plugin API types](https://github.com/figma/mcp-server-guide/blob/ecefd5b5dfd0ca7a1b8f142e0d59bc7f8a2efde6/skills/figma-use/references/plugin-api-standalone.d.ts)
- [Figwright tool specs: reparent, reorder and clone](https://github.com/awdr74100/figwright/blob/670b69040f0933728de9a31bb9d8ce920bf3ce44/packages/mcp/src/tools/reparent-nodes.ts)

Historical URLs help clarify a mechanism; they do not replace the documentation
of the version actually in use.
