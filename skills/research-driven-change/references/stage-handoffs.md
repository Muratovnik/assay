# Stage handoffs

Use for entry into a multi-stage request, acceptance of an upstream result or a
return to earlier work. This procedure owns transition readiness and the attained
endpoint. The [planning method](../../implementation-planning/SKILL.md) owns units,
sequencing and the plan; do not create a parallel plan or a new status schema.

## Choose the next justified step

Identify the requested endpoint and which dependencies of it are unresolved.
Research, planning, execution and review can each be the entry point. A known
narrow correction inside a larger cycle needs only the affected work. An existing
plan is evidence to reconcile, not an instruction to repeat its completed stages.

For each next action distinguish:

- **Ready:** the inputs needed to make this decision are sufficient and current.
- **Authorized:** the current request permits this action on this subject.
- **Available:** the actual tools and effective permissions can perform it.

A ready plan does not authorize implementation. An authorized pull request may
be blocked by publication capability. Tool availability does not grant permission.
Check consequential capability early enough to avoid silently promising an
unavailable endpoint; an untried relevant tool is not proof of unavailability.

| Transition | Sufficient input | Result to carry forward |
| --- | --- | --- |
| Research to choice | The relevant options, local constraints, source conditions and material unknowns | A supported choice, retained alternative or bounded unresolved decision |
| Choice to plan | Expected outcome, transfer rationale and applicable acceptance | Ready units and their dependencies, with unresolved work named |
| Plan to implementation | The next unit is grounded in the current subject and its effects are authorized | Actual changed artifact, intentional deviations, checks and unfinished scope |
| Implementation to review | Exact subject/revision, original acceptance, actual changes and available checks | Findings with evidence, exclusions and verification limits; not repair authority |
| Checked work to publication | The state is suitable for the requested kind of proposal and publication is authorized | Confirmed remote identity and revision, with pending checks or delivery gaps |
| Feedback to renewed work | A supported finding or changed premise, the affected decision and current subject | A bounded correction or replan, relevant renewed evidence, or a reasoned non-change |

These are semantic handoffs, not obligatory stages in this order. A review-only
request remains with the audit method. Review may occur before or after a pull
request; a requested draft may legitimately precede full verification. Label its
limits rather than claiming completion or withholding an authorized draft until
unrelated stages finish. Publication never implies merge or release.

Use [evidence to change](evidence-to-change.md) when accepting a research choice and
[review and delivery](review-and-delivery.md) when a finding or remote effect is
involved. A file, checkbox or method invocation alone cannot establish its output.

## Return from a selected method

The method supplies the applicable criteria, actual result, supporting location or
check and unresolved limitation. The owner of this work reconciles them with the
requested outcome and chooses the next authorized action. Referencing another
method does not create a second assignment, duplicate source record or permission
to spawn workers. Do not repeatedly reload an unchanged method already available.

For a blocked dependency, name the missing evidence, decision or capability and
what observation could resolve it. Continue independent ready work when useful.
Do not weaken acceptance, silently defer an in-scope item or convert an unchanged
retry into progress. A justified no-change research conclusion may complete a
choice request; it is not a receipt for a separately requested implementation.

## Keep one sufficient account

Use the user's chosen record and its existing labels. When a durable record is
needed, planning's
[continuation procedure](../../implementation-planning/references/continuation.md)
owns what to preserve and how to resume. This method connects its stage results;
it does not copy that procedure into another ledger. At a transition retain the
critical qualification in addition to its source link so the next method need
not reconstruct the old conversation.

For example, a compact entry in an existing plan can say:

> Goal: keep a dataset adapter compatible without changing its public IDs.
> D1: adapt the existing alias mechanism; research note R2 records its input
> assumptions and why blind case-folding is unsuitable. U3 implements D1.
> U3 changed the adapter in revision X; its exact-match fixture passed on X,
> while the provider integration was unavailable. Review F1 identifies an
> untested collision, not an approved change to the public-ID contract.
> Next: reproduce F1 and, if confirmed, repair U3 and its affected checks.
> Endpoint still owed: the requested PR. No publication has occurred.

This is an example, not an executed receipt, required filename or prescribed
notation. A skill-behavior change can use the same account with a behavior case
and its valid control instead of a provider fixture. Neither requires a database.
