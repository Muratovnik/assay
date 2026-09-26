# Reuse and migration scope

Use for material decisions to add, retain or change reusable behavior or visual
states, adapt a dependency, or carry out a requested migration. Inspect the affected
boundary and callers; a small unrelated repair needs no whole-repository inventory.

## Preserve the applicable outcome

Before relying on a material exception or a reduced migration, check its source
and decision basis with the available
[contract-change criteria](../../implementation-planning/references/scope-and-readiness.md#check-material-changes-to-the-contract);
applying them starts no second plan. The unfinished remainder of the migration
follows the staged-adoption rules below.

## Establish who performs the behavior

Trace the actual implementation behind the public interface. Distinguish behavior
provided by the native platform, an installed library, and owned code. An import,
package entry or familiar wrapper name is insufficient: a dependency can be
present while local handlers still perform the standard mechanism. Dependency
presence, shared placement, delegation of a capability and reduced maintenance
burden are different claims; evidence for one does not establish all four.

Prefer a fitting existing capability before recreating its mechanics. Respect an
explicit request to reuse maintained solutions. Before retaining or adding material
duplication in the changed boundary, identify the concrete API gap, unsupported
consumer behavior or operating constraint and compare the maintenance burden.
Reuse still-applicable evidence; use the component-evidence procedure in
[evidence-research](../../evidence-research/references/component-evidence.md) when
version, compatibility or maintenance premises need verification. Do not claim
that no solution exists because the first candidate or configuration failed.

Preserve a useful facade for product semantics, styling, compatibility or a stable
consumer interface. Simple native controls can be the fitting reusable primitive.
Own code is justified when it serves a real gap at lower total lifecycle cost;
record a material exception briefly in the owning decision or task, including the
conditions that would invalidate its rationale. A historical workaround must be
rechecked when its relevant version or environment changes. Neither library
presence nor a preference for reuse authorizes an unrelated rewrite.

## Apply this to UI primitives

For complex controls, locate keyboard navigation, focus management, dismissal,
positioning, selection and disabled/loading behavior where applicable. Check which
parts native or library primitives already supply before adding local handlers.
Keep product choices in the facade and express visual tokens through the library's
supported theme or configuration where it has one; avoid competing state or event
machinery that recreates the underlying primitive's contract.

Include visual states, variants and theming when they affect the requested
ownership boundary. Check the installed version's props, slots, theme API and
CSS variables before reproducing standard loading, disabled, focus or hover
presentation. Distinguish library configuration, product composition, API adaptation,
a justified missing capability and duplicated standard behavior. Headless deliberately
leaves visual ownership locally; it is valid when that is the applicable choice.
A branded spinner or product-specific composition can also be justified. Neither
CSS volume nor the number of wrappers is a verdict or a migration percentage.

Apply constraints at their actual boundary. A prohibition on utility classes in
feature code need not prohibit a supported shared theme. Build dependencies,
configuration and runtime CSP are separate constraints; verify compatibility
without weakening security to make a preferred library fit.

Choose by the required interaction, not the component's name. A trigger opening a
searchable popup need not become an editable combobox. A styled native input need
not become a dependency wrapper. Conversely, a tabs component with its own arrow
and focus algorithm does not delegate that mechanism merely by importing a UI kit.

Validate the affected integration with the actual primitive, including meaningful
keyboard/focus, disabled, nested or asynchronous cases. A self-authored behavioral
stub can check facade forwarding but cannot prove the library's runtime guarantee.
Preserve applicable operating constraints such as CSP; qualify untested behavior.

## Keep staged adoption tied to the request

Separate the requested outcome from the current implementation step. A pilot can
reduce risk, but successful installation or a migrated subset does not complete a
broader authorized migration. Continue authorized remaining work unless an explicit
checkpoint or a real dependency prevents it; do not silently redefine the brief.

When splitting work or handing it off, record the switched consumers/mechanisms,
retained implementations and reasons, and the remaining acceptance conditions in
the existing task or decision. Give deferred work a concrete continuation condition
and responsible owner or explicitly unassigned status. Avoid a second inventory
document when the owning task suffices. At completion, reconcile code and consumers
with the original scope; report a partial result as partial. A requested pilot is
complete when its own acceptance contract is met, without forcing a whole-system
migration. Lack of authority for the remainder must stay explicit.

## Keep exceptions finite and test the final state

For a temporary exception, identify the affected object/capability, reason and
version-sensitive premise, responsible owner or explicitly unassigned status,
revisit trigger and exit condition in the owning task. Tie "on next change" to a
relevant consumer or family, not any edit to its file. Preventing new debt does
not retire old debt: give the remaining outcome a next authorized stage or a
concrete dependency. Preserve a genuinely permanent product-specific choice as
such rather than inventing a retirement obligation.

Where a gate protects staged adoption, verify it with the
[exclusion and end-state checks](effective-quality-checks.md#check-exclusions-and-the-reachable-end-state),
not a new generic migration runner. This method decides which exceptions are
approved: an authorized new requirement or upstream regression can justify a new
one, and an empty debt list is a valid terminal state. Retire temporary
scaffolding only after that state is tested, keeping applicable permanent
invariants.

For a multi-stage plan, use available
[long-horizon planning](../../implementation-planning/references/long-horizon.md)
for sequencing and readiness; the consumers, compatibility constraints and
retirement conditions established here stay authoritative.

## Preserve structural and public contracts

For changed ownership or placement, consume the
[architecture method](../../software-architecture/SKILL.md) and implement its
adopted decisions without copying its criteria into a second architecture document.
Trace old mechanism, canonical replacement, switched consumers and retirement or
justified compatibility. Separate file relocation from intentional behavior changes.

Record old and new entry points and affected consumers, including supported
external paths. Check public imports/exports, route registration, aliases,
generated artifacts, assets, style scoping, build output, package contents and
lint/type/test selection; a green command can select none of the relocated files.
Adding Node package `exports`, for example, can close formerly reachable entry
points: establish the supported surface rather than inferring compatibility from
updated local imports. Test the built artifact with a representative supported
consumer where relevant. A facade can remain for an external support obligation
without an in-repository importer; name its owner and supported lifetime. Retiring
a supported path needs evidence or explicit authorization to change that contract.

Keep required consumers working at each promised intermediate stage. Record what
is reversible and what requires a separate data/schema recovery step; restoring
source alone does not prove rollback of the system. Coverage uses
[effective checks](effective-quality-checks.md), and agreed violation debt follows
[finite exceptions](#keep-exceptions-finite-and-test-the-final-state). Do not
silently expand the task into a new release or live data migration.
