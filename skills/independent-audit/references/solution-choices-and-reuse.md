# Solution choices and reuse

Use for material build, adapt, adopt, or retain decisions within the named audit.
The objective is justified complexity and useful outcomes, not a dependency quota
or a presumption that custom work is wrong.

## Establish the actual problem and alternatives

Existing material owned mechanics can trigger this review in a broad repository
audit; no new dependency, migration claim or explicit user reminder is required.
For implementation reuse checks, read the applicable
[reuse criteria](../../code-maintenance/references/reuse-and-migration.md).
Verify actual behavior and standard visual-state ownership behind wrappers, not
only dependency presence or shared placement. For repeated UI families, apply the
[component-system criteria](../../operations-ui-delivery/references/component-system.md)
to representative bases, configurations, compositions and real consumers. A narrow
review traces its affected chain rather than inventorying the whole product. For a
partial adoption, compare the delivered subset and recorded remainder with the
original request using that method's staged-adoption criteria. Retain read-only
authority; its implementation instructions are criteria, not a repair assignment.

Start from the required consumer outcome, supported environments, owner choices,
and operating constraints. Separate those from limitations introduced by the
candidate itself. Recheck a historical workaround's premises before accepting it
as a current requirement.

Inspect capabilities already owned by the project, its dependencies, standard
library, and platform before proposing another mechanism. Where material, compare
maintained external components/services and a small owned implementation. Retain,
simplify, or remove an unnecessary mechanism are also possible outcomes. Reuse
prior research when its requirements and relevant external facts still hold;
do not require a fixed candidate count or exhaustive market coverage.

Verify consequential compatibility and maintenance claims against current primary
documentation/source and relevant versions, not names, popularity, or marketing.
Use a bounded isolated probe only within the audit's authority. Without access,
report the specific unverified comparison; do not invent a replacement's fitness
or make unrelated acceptance claims inconclusive.

## Test the decision basis separately from conformance

For an exception or material change of result, apply the available
[contract-change criteria](../../implementation-planning/references/scope-and-readiness.md#check-material-changes-to-the-contract)
in read-only mode. An unresolved basis is an open question, not a finding, and
the current task still bounds repair authority.

Keep decision basis, fitness for the current outcome, implementation conformance
and audit coverage separate. Matching an ADR may establish conformance while
leaving its authority or fitness unresolved. No new verdict taxonomy or mandatory
report table is needed.

## Resolve retained mechanics

For each material owned mechanism encountered in the selected scope, turn the
ownership observation into a decision against the linked reuse criteria:

- Establish the applicable owner request and current stage, then inspect the
  decision or exception being relied on. Compare its scope, authority and current
  premises with this mechanism and its consumers. An implementation report cannot
  silently narrow the user's request; an explicitly accepted pilot must retain
  its own acceptance boundary.
- Compare the required behavior with the existing native/library capability and
  the concrete gap or tradeoff claimed for keeping it locally. Small size, working
  keyboard behavior and the absence of a reason for a wholesale rewrite do not
  settle that comparison. Reuse verified prior evidence when still applicable.
- State the scoped result and its basis: compliant delegation, justified owned
  behavior, accepted temporary deferral, demonstrated contract violation, or an
  unresolved comparison with the missing evidence and next discriminating check.
  These explanations use the main audit's claim statuses, not a new verdict scale.

A valid scoped deferral can satisfy the current stage without proving completed
adoption or justifying indefinite retention. Check any promised continuation
against the staged-adoption criteria; do not invent a deadline or migration
obligation absent from the contract. A missing note alone does not prove a defect.
If competing instructions or unavailable evidence prevent deciding applicability,
keep that question explicit instead of accepting the implementation's description.

Separate conformance from repair economics: a confirmed violation can be reported
before a replacement is selected, and a conforming exception needs no replacement
recommendation. Do not use either "custom" or "no rewrite needed" as the result of
the check. Group equivalent mechanisms when they share the same evidenced basis;
no exhaustive component catalog or mandatory new decision document is required.

## Learn from products without importing their scope

For material product or workflow choices, examine how comparable products serve
the relevant audience, task, failure/recovery paths, and integration conventions.
Explain which observed approach could help this consumer and why. An established
pattern can improve an owned implementation without importing a library or service.

An analogue is evidence and inspiration, not the acceptance contract. Its feature
set, audience, business model, or operating environment may differ. Trace a missing
scenario to the brief or a concrete supported user need before calling it a defect;
otherwise offer it as optional discovery. Do not require feature parity, copy a
whole architecture, or treat access to source as permission to incorporate it.

## Compare the whole cost of ownership

Evaluate only decision-relevant tradeoffs: requirement coverage, integration and
configuration, transitive dependencies, deployment/privacy constraints, security,
license compatibility, maintainership, updates/API stability, and exit or rollback
costs. Consider the ongoing testing and support burden of custom code as well as
that of an external dependency. A mature component is not automatically suitable;
a small implementation is not automatically cheap or safe.

For an existing candidate, distinguish whether the original choice was reasonable
from whether replacing it now is worthwhile. Compare migration, compatibility,
data conversion, and regression risks with a bounded correction or deferred change.
Do not let sunk effort excuse a confirmed failure, or recommend a prerelease rewrite
solely because a popular alternative exists. Borrowing an approach, configuring an
existing capability, or a thin owned adapter may be enough.

## Calibrate the conclusion

A substantive finding names the chosen mechanism, a violated requirement or
demonstrated unnecessary burden, the affected consumer, and applicable evidence.
When recommending an alternative, establish its relevant fit and tradeoffs; if
that is unresolved, propose a discriminating check instead of a promised fix.
Absence of retrospective rationale alone does not establish poor design. An
explicitly required decision deliverable follows the main delivery rules.

Custom code, an unused library, or an unadopted competitor feature is not itself a
release blocker. Apply the main verdict rules to demonstrated impact at the named
stage. Keep optional improvements and consequential owner choices separate from
defects. Do not install dependencies, rewrite the implementation, amend owner
policy, or expand a bounded review to settle an out-of-scope comparison.

When component assessment needs external guidance, use the current
[OpenSSF evaluation guide](https://best.openssf.org/Concise-Guide-for-Evaluating-Open-Source-Software)
and [component-user guidance](https://best.openssf.org/Simplifying-Software-Component-Updates#component-users)
as selective lenses, not mandatory certifications or mechanical acceptance scores.
