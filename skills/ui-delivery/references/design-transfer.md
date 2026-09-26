# Design transfer

Use when an existing interface — a running application, a rendered page, a raster or
DOM capture, or an older design file — becomes an editable design artifact or design
system, or when structure inside an existing design file is replaced or migrated. It
adds only the transfer duties; the general rules keep their own owners.

## Fix the source and the allowed delta

Before the first capture or write, record what is reproduced and the allowed delta:
source revision/runtime, target file, data, state, theme, viewport, scale/DPR, crop,
the fonts used for comparison, and whether the result covers the viewport, the
document content or a scroll region. Use the available standard capture/edit path;
check pricing and limits for the current operation.

State those conditions with the result and reuse them for later comparisons: a
capture from another zoom, dataset or theme is no match however close it looks. A
redesign is legitimate when the brief allows it, and then it is declared. A source
defect is its own finding, resolved by decision, not quietly corrected inside a
claim of fidelity.

## Distinguish the observed UI from the target system

For system selection or redesign, inspect the code library and available design
resources before recreating a catalog. Treat official kits as candidates: compare
actual versions, license/access, editable properties, supported states, tokens and
code APIs. Similar names and publisher branding do not establish compatibility.
Record mapped, product-specific and unmapped parts in the existing work record;
unavailable resources limit the claim rather than requiring a paid dependency.

For a faithful transfer, preserve the authorized source and identify defects or
possible target-system changes separately. Do not silently redesign it to match a
kit. For an authorized target system, establish its basis and material allowed
differences before propagating components to consumers. Public availability does
not authorize installation, import, publication or a purchase. Resolve only choices
that materially change the deliverable, not a fresh approval for every instance.

Check an important state/property/token in the design and the actual code consumer
when claiming correspondence. Keep capture fidelity, mapping and observed consumer
effect distinct. Use existing tools or manual verification; no specific connector
or design-kit subscription is required. Consumer-facing support and observed-only
material are distinguished by [system organization](design-system-organization.md).

## Establish coverage before a broad transfer

When the requested result spans multiple screens, journeys or material states,
derive the expected transfer set from the brief and source behavior before using
the produced artifact as evidence of completeness. Reuse the supported journeys
and states already identified by [workspace](workspace-consistency.md) and
[acceptance](scenario-testing.md); do not invent a second product specification.

Keep the inventory proportional to the claim. Record the surfaces and material
states needed to support "complete" or "all required states", including loading,
empty, error, expanded/overlay or role/theme/size differences only where the
source actually supports them and they change the ordered result. A single
explicitly requested static state does not require an application-wide inventory
or a full Cartesian product of route × state × viewport × theme.

- Failure: nine default screens are transferred and called complete although the
  source contract also requires an error state, an open inspector and a direct
  entry state that were never considered.
- Valid control: the user orders one named screen in one state; unrelated routes
  and hidden states remain out of scope.
- Check: each expected source item ends as transferred and verified, intentionally
  omitted, unavailable/unverified, or explicitly out of scope. The candidate set
  itself cannot be the oracle for whether anything was missed.

## Capture the chosen state, then treat it as raw material

Reproduce the state from an existing story, fixture or scenario when one exists. Set
data, time/access and readiness for it, fonts and assets included, and do not wait
for idle in a way that erases the loading, transition or failure state under test. A
missing Storybook or browser on a native platform does not require installing one:
take the available path and name the gap. Capture mechanics stay with
[browser checks](browser-checks.md).

What comes back is material, not a result. Confirm transfer coverage, source
accuracy and the required structure/editability separately; none follows from the
others or from import. Inspect the usual losses: substituted fonts, flattened SVG
and masks, missing border and focus rings, displaced overlays, clipped content.
Never promise 1:1 from the fact of import; keep expected/captured, visually
compared, linked to the system and verified after replacement distinct in the
report. A flat or raster result is a legitimate deliverable when the ordered
artifact is a reference image, and an intentional popup over content is a state to
reproduce, not an overlap to remove. Structure depth and property chains belong to
[component system](component-system.md).

## Classify a region before replacing it

Classify each region before writing: already linked, a compatible swap, a
composition from shared bases, justifiably unique, or no fitting resource. A
justified unique region is an outcome, not a blocked one, and a matching name is not
compatibility. Before migrating the rest, verify supported text, icon, state, size,
content and the overrides consumers rely on, using one representative and one risky
case: long content, a non-default state, another theme, focus. A probe on the
default label is no authority for fifty replacements. Identical instances need no
repeated probe, and a justified local base is a valid resource.

## Migrate without breaking the relations

Preserve the relations the region depends on: parent, index and order, grid row,
column and span, min/max sizing, bounds, padding, gap and clipping, and reactions or
prototype links. A fixed size, scroll region or absolute overlay is worth keeping
when it matches the role. Obtain real identifiers after each structural change and
verify the new state in its container before deleting your old node. Leave no
visible duplicate, never delete a master with unverified consumers, and after a
reparent, combine or rename re-read properties, links and geometry at the affected
levels. Adapter operations and error semantics belong to [Figwright](figwright.md);
a transferred reaction's behavior to [motion](motion-and-transitions.md).

- Failure: a write series fails midway and is replayed from the start, leaving two
  copies of the region and one consumer bound to the discarded base.
- Decision: stop dependent steps, read the partial result, restore the violated
  invariants, then continue. Completed work is kept; an allowed best-effort series
  keeps its named skips in the result.
- Check: parent, order, span, size, clipping and links at the affected levels, plus
  one real consumer of anything replaced.

## Separate organizing from replacing

Moving and reordering inside an existing library keeps the base's identity, its
references and its consumers' overrides. Clone or recreate produces a different
entity, and consumers keep pointing at the original until a separately justified
migration moves them. A requested fork or replacement is legitimate when declared as
one with a planned consumer migration; after either, verify identity, keys, consumer
links and overrides.

## Compare a real reference with a real candidate

Compare a real reference with a real candidate in the same state and the conditions
fixed above. Distinguish manual comparison, raster diff and tree inspection: they
detect different classes of difference, and none substitutes for another. Never
report a diff that was not run, and import no match percentage or threshold:
rendering and font rasterization differ between environments.

Judge a difference by what it means for the task: a thin focus ring, a wrong icon or
a shifted type step is material even when a large matching background dominates the
frame. Resolved tokens, fonts, nested theme, ancestor paint at the needed depth and
library readability are judged in [visual judgment](visual-judgment.md). Two widths
record two sizes, not the space between them: breakpoint frames stay a legitimate
convention, and sizing belongs to [workspace consistency](workspace-consistency.md).

- Failure: a structural pass finds no detached instance and the screen is called
  faithful, while the transferred page is a third taller than its source.
- Check: name the comparison performed, its state and scope, then list the
  differences with a decision for each: accepted, defect or deferred. Evidence
  levels are governed by [acceptance](scenario-testing.md).

## Method references

- [Classify sections before applying a system](https://github.com/edenspiekermann/Skills/blob/a49e859329aa99e81e8725bc66767d16e8fc9539/skills/apply-design-system/SKILL.md)
- [Separate capture from reconciliation](https://github.com/alima-max/prototype-to-figma-skill/blob/6e2e1befaa6f6df34a046956127b1d4f54bcb158/SKILL.md)
- [Reference, actual capture, comparison, report](https://github.com/voidmatcha/frontend-niche-skills/blob/18b71b698fa6fa7c861d2bfe1272728a90cf95ed/skills/design-to-code-fidelity/SKILL.md)
- [A capture is not a connected component system](https://github.com/figma/mcp-server-guide/blob/ecefd5b5dfd0ca7a1b8f142e0d59bc7f8a2efde6/skills/figma-generate-design/SKILL.md)
- [Figma: turn coded screens into editable design layers](https://help.figma.com/hc/en-us/articles/40826832449303-Turn-coded-screens-into-editable-design-layers)

These inform method, not thresholds, scripts, package installation or copying of
licensed text.
