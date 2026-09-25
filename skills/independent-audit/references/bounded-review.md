# Bounded reviewer integration

Read this for already-authorized audit delegation and when a caller invokes the
method inside a bounded reviewer role, such as `evidence-reviewer`. The coverage
handoff applies to ordinary audit workers too; profile-specific verdicts and
packet rules apply only when that profile is selected. An ordinary repository
audit does not require a subagent. The skill grants no delegation.

## Carry coverage through delegation

The primary assigns questions and applicable criteria owners from its coverage
map, alongside the source boundary and original objective. A label such as
"frontend" or "code quality" alone does not establish which concerns were checked.
Keep unassigned concerns with the primary; delegate only within existing authority.
The reviewer performing a comparison must have the applicable criteria sections
available and read them or receive their exact relevant text with source/scope.
The primary's reading alone does not establish that the delegated check used them.

Carry the current outcome's relevant source and scope, the current assignment's
authority, material changes to acceptance, disputed decisions and unverified
premises with the packet. An implementer's summary is not a substitute for the
source of a consequential exception. Include enough original context to test that
basis within permitted reads; absent evidence stays an explicit limitation. Two
reviewers agreeing on the same unsupported premise do not independently validate it.

Each return identifies the assigned questions actually checked, decisive evidence,
partial or unverified questions, exclusions and any material newly observed gap.
Findings alone are not a coverage receipt. The primary reconciles returns against
the original questions, completes remaining authorized checks or reports their
limits. Findings in one concern do not establish review of other assigned
concerns; a clean concern also needs its scoped conclusion. Missing access remains
a gap, never N/A or implicit PASS.

For a material observed deviation or retained custom mechanism, the return must
connect the applicable criterion and any relied-on exception to its conclusion.
An accurate inventory with no such comparison is partial evidence. The primary
checks that connection before marking the concern covered; complete the missing
comparison locally, request a bounded follow-up within existing authority, or
retain the unresolved question in the final report. Preserve accepted deferrals
and remaining limits when summarizing; do not turn them into full adoption or
erase them behind an area's other passing checks.

## Preserve the packet boundary

The primary establishes the objective, owner criteria, review mode, exact
snapshot, permitted read-only oracle, and owned scope before delegation. The
reviewer independently tests the supplied claims; it does not repair the work,
invent missing packet inputs, switch modes, or expand access.

Within that boundary, compare the actual result with the original objective and
owner criteria, not only the supplied checklist or passing logs. Material
recipient, composition, distribution, and side-effect constraints belong in the
packet when they affect acceptance. Report a consequential missing decision or
out-of-scope surface to the primary; do not silently approve it or enlarge the
reviewer's authority to investigate it.

Frozen contracts constrain action, not the reporting of a contradiction. When
in scope, test whether the gate implements the supplied objective without
rejecting supported cases or admitting forbidden ones. Distinguish an
enforcement defect from a concern about an explicit owner policy; report the
latter to the primary without rewriting the contract or granting an exception.
Use the role's existing verdict rules according to demonstrated impact, not a
new automatic failure category for every questioned restriction.

When a load-bearing packet input is missing, follow `refused` if the selected
role declares that contract; otherwise report the missing input and its effect
on coverage. This differs from a valid packet whose mandatory acceptance evidence
cannot be established during review: that result is `inconclusive`.

Only run the declared oracle within the actual permissions. A profile requesting
read-only mode does not prove the effective session boundary; inherited runtime
overrides and client behavior must be checked. Never relax settings yourself.
If a necessary probe cannot run, report that gap without labeling it successful.

Frozen read roots also bound listings, searches and Git discovery. Identify a
snapshot by its manifest/digests; do not recover missing paths or history from
ancestors or neighboring tasks. Report a boundary violation separately from the
subject verdict. Preserve the caller's expected-effect and outcome vocabulary;
an audit can complete with a failing subject verdict. Deliver the full finding
set and decisive receipts in the final result or authorized durable artifact,
not only in interim peer messages.

## Preserve meaning across verdict vocabularies

For `evidence-reviewer` acceptance mode, use its external vocabulary:

| Audit conclusion | Profile verdict | Meaning |
| --- | --- | --- |
| PASS | ship | All mandatory claims established for the named stage. |
| PASS WITH NON-BLOCKING FINDINGS | ship | Same acceptance condition; retain findings and required owner/disposition evidence. |
| FAIL | fix-first or rethink | A demonstrated failure blocks acceptance. Choose fix-first for a bounded correction; rethink when the approach or contract is invalidated. Severity alone does not choose between them. |
| INCONCLUSIVE | inconclusive | No decisive failure, but mandatory evidence or an acceptance choice remains unresolved. |

The role's stricter acceptance/disposition requirements still apply; an
unsupported prerequisite cannot be hidden in non-blocking findings. A known
failure dominates unknowns. `ship` is a scoped recommendation, never permission
to publish. The caller must not advance acceptance on `inconclusive` or `refused`.

Keep claim statuses and evidence limits visible without requiring two competing
top-level verdicts. Offer a correction only when supported; a demonstrated
failure need not have a known cause or invented fix. Unknown defect existence
stays an open question with a discriminating check.

Decision and adversarial modes retain their own role vocabularies; do not map
them to release acceptance. In particular, absence of a found risk is not proof
that every product requirement passed.
