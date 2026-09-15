# Code quality verification

Use for implementation, refactoring or code quality selected within the audit's
scope, including the current code of a broad repository audit without a new diff
or an explicit implementation claim. This is a verification procedure.
The corresponding implementation, testing, UI and
research skills own the principles; this file neither restates a new standard
nor authorizes repairs. Read only the applicable criteria sections below and
preserve the audit's read-only scope even when a linked method describes writing.

## Identify criteria and inspect evidence

Select concerns from actual structure and applicable owner contracts before
hunting for findings. For substantial owned mechanics, read the reuse criteria
and inspect representative implementations and consumers; component names,
dependency presence and green tests alone cannot establish who performs the
behavior. Keep checked concerns and remaining gaps in the audit's coverage map.
For a material departure found during those checks, complete the comparison:
which requirement applies to this unit and stage, what the source actually does,
and whether the evidence establishes compliance, a valid exception, a violation
or an unresolved question. Use the main claim statuses with that explanation.
Do not infer conformity from a description of the implementation or infer a
violation from the absence of a retrospective design note alone.

| Concern | Criteria owner | Verification |
| --- | --- | --- |
| Behavior versus adopted standards | [Working contract](../../code-maintenance/SKILL.md#establish-the-working-contract), conditional [TS/Vue profile](../../code-maintenance/references/typescript-vue-conventions.md) | Establish which convention was accepted, when and for which files. Compare functional results and convention compliance separately; a newly proposed preference is not a prior violation. |
| Responsibility and interface | [Responsibilities](../../code-maintenance/SKILL.md#responsibilities-and-interfaces) | Trace representative operations, callers and imports across resulting units. Identify the actual decision/lifecycle hidden by an extraction and knowledge still required by callers. Challenge both needless indirection and blanket bans on small adapters. |
| Reused mechanics behind a facade | [Reuse criteria](../../code-maintenance/references/reuse-and-migration.md#establish-who-performs-the-behavior), conditional [UI primitives](../../code-maintenance/references/reuse-and-migration.md#apply-this-to-ui-primitives) | Trace native/library calls and local handlers to the behavior claimed as reused. For retained owned mechanics, complete the [reuse comparison](solution-choices-and-reuse.md#resolve-retained-mechanics) against the explicit request and evidenced exception; seek valid native controls and useful adapters as counterexamples. Distinguish real integration evidence from a behavioral stub. |
| Partial adoption and completion | [Staged adoption](../../code-maintenance/references/reuse-and-migration.md#keep-staged-adoption-tied-to-the-request) | Compare the original authorized scope, switched consumers, retained implementations and remaining acceptance conditions. Do not certify a broad migration from a completed pilot; equally, do not fail a requested pilot for excluding unrelated consumers. |
| State and effects | [State ownership](../../code-maintenance/SKILL.md#state-and-effects), conditional [Vue structure](../../code-maintenance/references/vue-structure.md) | Trace initialization, writes, derived values, reset/disposal and affected consumers. Look for synchronization or lifetime failures and distinguish deliberate shared state, drafts and local mutation. |
| Resulting structure | [Final structure](../../code-maintenance/SKILL.md#inspect-the-final-structure) | Read the full affected units and important callers, including relevant dirty changes. Check whether the claimed simplification changed responsibility or only moved text; test the proposed split against a cohesive large unit. |
| Effective enforcement | [Quality checks](../../code-maintenance/references/effective-quality-checks.md) | Follow actual invocation, resolved config, rule severity and covered files; inspect relocated tests/configs. Use authorized bad/valid controls for load-bearing doubts and report unexecuted portions separately. |
| Fixtures, selectors and suite structure | [Test boundaries](../../test-writing/references/boundary-choices.md), [suite maintenance](../../test-writing/references/suite-maintenance.md) | Trace fixture identity/lifetime and assertions to consumer contracts; check preservation of collected cases and required static checks after a split. Use [test-audit](../../test-audit/SKILL.md) for substantive regression-protection review. |
| Package or platform premises | [Component evidence](../../evidence-research/references/component-evidence.md) | Verify installed/recommended versions, source dates and actual API constraints; distinguish an old stable package from a demonstrated maintenance risk and inspect bounded search evidence behind absence claims. |
| Claimed UI acceptance | [Scenario acceptance](../../operations-ui-delivery/references/scenario-testing.md) | Connect viewport/data/entry conditions to supported journeys and actual observations. Determine whether the check can pass while the stated interaction problem remains. |

Use implementation principles as evaluative criteria, not proof of an adopted
project style. An architectural concern needs a concrete in-scope burden or
failure scenario; a different plausible design alone is an optional suggestion.
An evidenced violation of an explicit applicable convention or reuse requirement
can refute that requirement without an invented functional bug. Establish its
scope, actual deviation and any accepted exception; keep that conclusion separate
from a proposal to migrate and its costs. Apply the finding filter after checking
the selected concern, not as a reason to skip standards verification.
If a criteria owner is unavailable, use supplied owner contracts and name the
missing method; do not invent a replacement policy or claim verified compliance.

## Report the scoped conclusion

For each material claim connect the criteria location, actual code/configuration,
discriminating evidence and status using the main audit method. Separate standards
violations, behavior defects, structural burden and missing verification. Respect
the requested scope when attributing accumulated debt. This review does not
require a rewrite, a finding quota, exhaustive metric collection or a new report.
