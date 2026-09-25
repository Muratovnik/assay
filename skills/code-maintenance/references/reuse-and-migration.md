# Reuse and migration scope

Use when adding or materially changing reusable mechanics, adapting a dependency,
or carrying out a requested migration. Inspect the affected boundary and callers;
a small unrelated repair does not require an inventory of the whole repository.

## Establish who performs the behavior

Trace the actual implementation behind the public interface. Distinguish behavior
provided by the native platform, an installed library, and owned code. An import,
package entry or familiar wrapper name is insufficient: a dependency can be
present while local handlers still perform the standard mechanism.

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
Keep product choices and visual tokens in the facade; avoid competing state or
event machinery that recreates the underlying primitive's contract.

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

For a multi-stage plan, use available
[long-horizon planning](../../implementation-planning/references/long-horizon.md)
for readiness, dependencies and the next detailed stage. Supply the consumers,
compatibility constraints and retirement conditions established here; the planner
must not redefine them. If already in that planning workflow, return these criteria
to the same plan rather than re-entering the method or creating another inventory.
