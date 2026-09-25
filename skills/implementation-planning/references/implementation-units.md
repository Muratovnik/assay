# Implementation units

Use for multi-unit decomposition, shared interfaces and substantive acceptance.
The unit is an outcome that can be meaningfully accepted or rejected, not a file,
a tool invocation, a fixed time slice or an obligatory commit.

## Describe enough to execute

For each unit give its result, requirement or necessary prerequisite, dependencies,
affected parts, approach and constraints, and the observation that establishes
completion. Group setup and tests with the outcome they enable unless they have
an independently useful deliverable. Split coupled changes only when intermediate
compatibility and meaningful acceptance exist. Otherwise keep one coherent unit.

Use durable identifiers when units are referenced over time. Reordering preserves
IDs; replacing or splitting a unit records the relationship rather than silently
reusing its ID for another result. Ephemeral short chat plans need no numbering
scheme beyond what the reader needs.

Name dependencies by the result or contract required, not just a task number.
Distinguish blocking, enabling and optional work. Identify cycles and resolve the
shared contract, use an intentional joint unit or introduce a justified compatible
transition; do not present an impossible topological order. Work with disjoint
files is not necessarily independent. Shared mutable resources, contracts and
integration checks can require coordination even when parallel work is authorized.
Planning concurrency is not authorization to create workers.

## Contracts versus implementation

Fix externally consumed formats, compatibility, responsibility and sequencing
constraints when other units depend on them. Include exact interfaces when
necessary to avoid incompatible independently implemented parts. Preserve shared
constraints in a linked common section that every relevant unit can actually read.

Leave internal algorithms and helper names to implementation when they do not
change the contract. A reproducing test or small protocol example is useful when
it removes material ambiguity. Do not prewrite all future code or forbid concrete
code universally. Paths and commands must be grounded or explicitly proposed.
No mandatory two-minute steps, TDD sequence or per-unit Git operation follows.

## Bidirectional coverage and acceptance

Trace every material requirement to a unit and a discriminating observation.
Trace each unit back to an agreed requirement or necessary enabling result.
Account for integration and applicable failure, compatibility, accessibility,
recovery, migration and operational constraints, not just the happy path. Do not
turn this into a feature checklist irrelevant to the project.

Specify what a check must observe; 'add tests' or 'run the suite' alone is not
acceptance. Reuse suitable existing checks. New tests are needed for a meaningful
gap, not to manufacture changed test files. State an unavailable check and the
proof still needed. Keep planned commands distinct from actual executed evidence.

Separate implementation acceptance from a later product hypothesis. A working
onboarding flow can be verified before a retention effect can be measured. Give
that later observation a metric/population, owner and review condition when known;
do not claim business impact from a unit test or invent a measurement date.

## Example: prevent repeated profile submission

Outcome: another supported submission action while this form's request is pending
does not send a second request; after failure inputs remain and retry is available.
Inspect the real handler and pending-state owner first. Change the handler guard,
presentation and relevant checks as one coherent result. Acceptance exercises
repeat click and keyboard submission during pending work, failure then retry, and
ordinary success. The scope is this client's form, not deduplication across tabs
or clients. Discovering that broader requirement triggers a contract decision,
not an unannounced server rewrite. Disabling a button alone does not establish
all supported submission paths.
