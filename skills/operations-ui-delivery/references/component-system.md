# Component system

Use when designing, changing or judging a repeatable UI system — shared bases,
families, nested compositions, editable properties and their code mapping — in
a design tool, in code or both. Settle what each part is and who owns it before
adding one more. A shared base may be a native control, a code component, a
master with instances or a unique composition; content may arrive as a
property, slot or child. Code and editor catalogs need not match, and "variant"
means a supported difference of state or structure, not an editor construct.

## Split families by role, not by surface difference

Separate a family when role, stable structure, behavior, states or required
editing genuinely differ; derive it from the contract consumers depend on. A
different label, icon or width does not justify a second base. Parts that look
alike may share styling and keep different interaction contracts: a trigger
opening a command menu and a control holding a value are not one thing.

- Failure: a value picker inherits menu behavior because it reuses that look.
- Valid control: separate public components are right when assembled from one
  base or differing in a material contract; no component carries every axis.
- Check: for each member, name its role and the contract that differs.

## Map the system before adding to it

When a pattern repeats, record the minimal map `base → compositions →
properties/states → consumers`, then choose deliberately between a fitting
existing resource, a composition of existing resources and a justified new
solution. A routine map is a short working note; a label fix does not require
an inventory of the product.

Not every layer deserves to be a component, and a wrapper added for its own
sake is a hop without a contract: a native control can be the correct base, a
unique composition can stay unique, and a missing component with an expected
name is not a defect. Create a shared base where it buys repeated change,
consistency or behavior at acceptable complexity. For the affected role, name
the base in use, where it is composed and which consumers a change reaches,
instead of adding another base beside those that already fit.

A technically reusable entity is not automatically part of the consumer-facing
library surface. It may be an internal building block, a public primitive, a
higher-level composition or example material depending on the contract consumers
are expected to use. This file decides that reuse contract; how the whole catalog
exposes, groups and distinguishes those roles belongs to
[design-system organization](design-system-organization.md).

## Follow reuse transitively to real consumers

A shared base helps only where consumers pass through it. Trace the affected
chain inward, into what the composition nests, and outward, to the places that
render it: a reusable row whose controls are redrawn inside does not update
those controls anywhere they appear, and a master's existence, or an import in
code, does not prove use. A consumer may opt out for a stated reason, but then
stops counting as evidence that the base works. Change the base once and
observe a real consumer, not the base alone. Code-side refactoring belongs to
[reuse and migration](../../code-maintenance/references/reuse-and-migration.md).

## Keep shell, content and demo example distinct

Distinguish the container providing placement, surface and shared actions, the
content performing the task, and the example illustrating either. A repeatable
panel must host its intended content and keep its shared actions and sizes;
baking one demo form into every shell variant makes it unusable for the next
consumer. An anatomy view documents structure, not the ordered composition.

- Valid control: a single standalone screen owes nobody a universal slot
  system, and a finished product screen is a legitimate composition.
- Check: place different intended content in the shell and confirm its shared
  actions, sizes and surfaces survive.

Sizing and adaptation of screens, panels and containers belong to
[workspace](workspace-consistency.md); geometry, bounds, overlap and visual
library readability to [visual judgment](visual-judgment.md); consumer-facing
catalog structure, public/internal separation and findability to
[design-system organization](design-system-organization.md); popup geometry and
modality to [interaction](interaction-and-layout.md); the duties of a transfer
to [design transfer](design-transfer.md).

## State the contract a reusable composition offers

Settle the minimum a consumer needs: purpose, parameters, which content is
required and which optional with its constraints, the visible parts, the states
and the styling goals. The parent owns the composition; a nested part owns its
own independent states when that matches its role, so parent variants need not
be multiplied for every combination of child states. A simple element needs no
schema. Field composition belongs to [forms and input](forms-and-input.md),
membership and mixed selection to [selection](selection.md).

- Check: take a consumer case that did not shape the contract and see whether
  the needed content and states are reachable and which region it may replace.

## Editability means an observable effect

A property is editable only when the chain holds: declaration → value passed →
bound receiver → resulting effect. A stored property value proves nothing about
the text, visibility, state, theme or nested content a consumer sees; a schema
and a description are not the proof either.

- Failure: an API returns the new label while the intended nested text is
  untouched, and the change is reported as done.
- Decision: in authorized work use a distinguishable reversible probe — a
  non-default text, a changed state or content, or a value on the shared base.
  Check the expected propagation and the neighboring invariants it could break,
  then revert; a default equal to the drawn text is a weak binding check. After
  merging or structural replacement, exercise a fresh and an existing consumer.
- Valid control: cover materially different binding and nesting paths — one
  single-line field does not demonstrate a multiline or select API, or another
  theme, when their wiring differs — while identical instances need no repeated
  probe. In read-only work use existing distinguishable values; where none
  exist, leave the effect unverified instead of probing without write authority.

Detaching, a literal value or a local override is allowed for a concrete
reason, but cannot at the same time be presented as full linkage to the shared
system; say which parts stayed connected.

## Choose the edit boundary of a nested element

Decide how a consumer reaches a nested element: a public property of the parent,
the nested instance's own API, or a supported exposure mechanism; do not promise
a property the consumer cannot reach. Deliberate encapsulation is a legitimate
answer, and no specific native exposure feature is required of every environment
or adapter; where the mechanism is missing, name the boundary rather than imply
it. Check from the consumer's position that the advertised value takes effect.

## Map design roles onto the real code API

When implementing a reference in code, establish the correspondence
`design role/node → code component or composition → props/state/tokens/assets`.
Use an existing design-to-code mapping, such as a maintained Code Connect
definition, when it is available and current; otherwise rely on the real API
and the project's own documentation. Verify actual use and value passing, not
the presence of a name in a map. A missing mapping file is not a blocker by
itself, and the code catalog may name things differently while serving the role.

- Failure: a generated copy or lost content hides an incompatibility, or an
  unmapped region is silently redrawn instead of reported.
- Check: render the implemented composition with realistic content, confirm the
  mapped props, states and assets take effect, and list what stayed unmapped.

## Primary references

- [WAI-ARIA APG: menu button](https://www.w3.org/WAI/ARIA/apg/patterns/menu-button/)
- [WAI-ARIA APG: combobox](https://www.w3.org/WAI/ARIA/apg/patterns/combobox/)
- [WAI-ARIA APG: listbox](https://www.w3.org/WAI/ARIA/apg/patterns/listbox/)
- [Figma: design system structure](https://help.figma.com/hc/en-us/articles/38978644498199-AI-workflows-collection-Best-practices-to-help-Figma-AI-understand-your-design-system)
- [Figma: slots for flexible content](https://help.figma.com/hc/en-us/articles/38231200344599-Use-slots-to-build-flexible-components-in-Figma)
- [Edenspiekermann: replacement classification](https://github.com/edenspiekermann/Skills/blob/a49e859329aa99e81e8725bc66767d16e8fc9539/skills/apply-design-system/SKILL.md)
- [Figma: component properties and their bound layers](https://github.com/figma/mcp-server-guide/blob/ecefd5b5dfd0ca7a1b8f142e0d59bc7f8a2efde6/skills/figma-generate-library/references/component-creation.md#6-component-properties)
- [Figma: Code Connect](https://github.com/figma/mcp-server-guide/blob/ecefd5b5dfd0ca7a1b8f142e0d59bc7f8a2efde6/skills/figma-code-connect/SKILL.md)
- [Figma: design to code](https://github.com/figma/mcp-server-guide/blob/ecefd5b5dfd0ca7a1b8f142e0d59bc7f8a2efde6/skills/figma-design-to-code/SKILL.md)

They inform method, not fixed values, tooling or permission to install anything.
