# Native task adequacy and cost selection

Routing policy v3 replaces native full rankings with independently named
categorical questions. Config v4 enables this policy for new configurations;
existing v1–v3 configurations retain their declared policies. Migrate explicitly:

```sh
python skills/route-subagents/scripts/benchmark_router.py migrate-config --source OLD_CONFIG --output NEW_CONFIG --native-decisions
```

The command creates a new file, preserves the source, and does not install,
change registrations or enable required routing. The native backend is required.
Keep the old config, installed bytes and link targets for rollback.

## Concrete input

For a packet needing advice, supply a cleaned `task_spec` beside structured
features. Obtain it from the actual assignment, without asking the user to
complete a questionnaire. This is a native-only data field, not an instruction:

```json
{
  "packet_id": "decimal-parser",
  "task_types": ["implementation"],
  "features": {},
  "task_spec": {
    "goal": "Implement a bounded decimal integer parser with explicit errors.",
    "criteria": [
      {"id": "syntax", "description": "Accept decimal integers only; reject trailing input."},
      {"id": "range", "description": "Reject values outside the bounds without overflow."}
    ],
    "verification": "Run deterministic normal, boundary and invalid-input cases.",
    "error_impact": "low",
    "ambiguity": "low",
    "provenance": "caller"
  }
}
```

Criteria have unique IDs, with 1–8 entries. Impact and ambiguity are `low`,
`medium` or `high`; provenance is `caller` or `observed`. Each prose field uses
the existing task-query bound of 4096 UTF-8 bytes and must be a nonempty single
line. Redact secrets, paths, code and unrelated conversation before submission;
validation rejects common credential/path forms and code fences, but does not
establish that arbitrary prose contains no sensitive information. Do not place
prose in `features` or use task types for every incidental action of one task.

Explicit full choices and singleton packets still require no advisor. Otherwise
missing `task_spec` produces `needs_task_details`, without launching advice or
claiming an optimal route. Any available caller fallback remains explicitly a
fallback. Jev's external projection excludes `task_spec`, including after a
backend change; there is no automatic native-to-Jev switch.

## Questions and answers

The native request has a shared `input` and a `questions` array. Each question
binds a packet and an exact candidate, with `type: "choice"` and values:

- `adequate`: meets the stated task criteria with supported task-specific grounds;
- `inadequate`: cannot meet a concrete task criterion;
- `unknown`: material adequacy facts are missing.

This adapts the [Decisions format](https://developers.openai.com/api/docs/guides/decisions)
within the existing native advisor. It does not invoke that API, inherit its
probabilities or require another provider, SDK or credential.

Questions needing advice use names such as `p0.c1`: packet position and candidate
position in the immutable snapshot. Responses contain `schema_version: 2`,
the exact snapshot ID, native advisor model/effort, `answers`, per-packet
`assessments`, null `probabilities`/`confidence` and contract metadata.

```json
{
  "name": "p0.c1",
  "choice": "adequate",
  "basis": "bounded"
}
```

The basis is scoped to that packet, with an ID up to 16 characters, a
`kind` (`measurement`, `task_inference` or `unknown`), `criterion_ids`, matching
`cohort_ids`, an explanation up to 300 characters and bounded `unknowns` codes.
An example inference basis:

```json
{
  "id": "bounded",
  "kind": "task_inference",
  "criterion_ids": ["syntax", "range"],
  "cohort_ids": [],
  "explanation": "The bounded parsing scope and deterministic verification support adequacy; benchmark transfer is uncertain.",
  "unknowns": ["quality_transfer"]
}
```

Every question has exactly one answer and a packet-local basis. Share a basis
only when it applies to every referring candidate. A measurement basis requires
a quality row for that exact candidate in a cited matching cohort. Missing rows
do not establish inadequacy; never fabricate measurements from another effort.
Unknown requires `kind: "unknown"` and a nonempty unknowns list. For known
assessments the `unknowns` field may be omitted and normalizes to an empty list;
this default never supplies a missing answer, criterion or unknown judgment's
grounds. Adequate and
inadequate require a concrete criterion. Structural validation cannot prove the
semantic accuracy of the judgment; real task controls remain necessary.

The result cap remains 64 KiB, independent of the native input. Use short names
and shared bases for up to eight packets and 64 candidates per packet. Overflow
reports the result boundary; it never removes questions or trims evidence.

## Economic policy and consumers

The advisor assesses adequacy independently of price. Code then compares
`adequate` pairs using known `cost_usd` in matching primary cohorts, falling back
to supporting cost cohorts when no primary comparison is available. It compares
only within a cohort and equal cost basis, excludes stale cost observations,
and does not average incompatible harnesses, units or revisions. Single cost
observations are retained but do not establish a comparative winner.

At sufficient quality, lower comparable expense wins. Preserve every strict
within-group preference and retain candidates that have no cheaper competitor
in any applicable comparison. Different minima in disjoint groups are not a
contradiction. If the remaining routes are incomparable across groups, use the
stable candidate ID only as a qualified tie-break and report
`cost_groups_incomparable`; this does not establish a unique economic optimum.
Conflicting preferences that leave no such route produce `cost_cohort_conflict`,
not a fabricated economic winner. Unknown cost is not zero; a qualified adequacy selection with
`comparable_cost_unknown` claims no measured savings. Comparisons over measured
subsets identify unmeasured adequate alternatives and unknown adequacy. Baseline
and answer order do not change the economic result. A more expensive route needs
concrete unmet criteria for cheaper alternatives; a larger score or generic high
impact alone is insufficient. API USD does not establish subscription quota or
actual full-chain cost.

When existing local task evidence supplies a supported paired full-chain
comparison for two adequate exact routes, code can use its net benefit to change
the benchmark choice. Keep its cohort, unit basis and observation count; report
observational transfer and unpaired alternatives as unknown. This does not turn
historical receipts into a measured cost for the new assignment, and no such
history is required to use benchmark cost.

New native decisions retain an empty compatibility `ranking` and carry
`economic_assessment`; no full order is invented. Old result v1 and Jev rankings
remain supported on their legacy paths and historical snapshots. A v1 native
reply cannot complete a new policy-v3 request. Cache keys include task spec,
policy and native contract/privacy versions; packet-ID changes rebind assessments
while positional question names remain stable.

Ordinary metadata history retains typed answers, criterion/evidence IDs and cost
assessment, excluding task descriptions and basis explanations. Full history
with native task specs is omitted unless `task_evidence.retain_descriptions` is
explicitly true, and reports `native_task_description_not_retained`; replay then
honestly reports `insufficient_record`. Retained full records can replay without
running a model. Pending portable/required state necessarily contains the native
input while completing the request; its existing private lifetime and expiry
remain in force. Requested/configured model settings are not host observations.
