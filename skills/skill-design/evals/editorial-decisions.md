# Editorial diagnostic decisions

Coordinator record; not executor material. Recorded 2026-09-25 against Assay
`c642a41f9d9c88b252b775514a62fd8c242d7b09`. This candidate is additive to the existing
writing methods, not a measured replacement. Its exact bytes are the enclosing
Git commit; input-only cases and grading stay separate.

## Prior work and transfer boundary

[Quirón README](https://github.com/ilien-dev/quiron/blob/main/README.md), inspected
2026-09-25, documents before/after measurements, source-token checks, excessive
style correction, and a reported series in which style-band compliance did not
prevent 12/12 AI classifications by model judges. This is the author's result,
not a replication, a human reader study or evidence that any local threshold works.
Its language/corpus scope does not establish a Russian writing-quality baseline.

The transfer is at the level of ideas: bounded diagnostics, retained negative
results and an explicit evidence/decision record. No Quirón code, skill prose,
word lists, baseline data or evaluation samples are incorporated. Assay's code,
synthetic fixtures and guidance in this change are independently implemented.

## ED-01 — Expose factual-token changes

Decision: **retain as advisory diagnostic; behavioral benefit untested**.
Hypothesis: visible additions/removals reduce overlooked changes during editing.
Protect whole typed tokens, units and source provenance; never promote token
matches to factuality or semantic-preservation claims. Supplemental notes do not
make every note mandatory in the final text.

Implementation evidence: deterministic tests for `100` versus `10`, unit changes,
source-backed additions, notes not imported wholesale, line/column reporting,
input hashes and read-only CLI behavior. Controls include harmless numeric spacing
and removed repetition. Modality changes with equal tokens are an explicit blind
spot, not a successful meaning test. See the revision-check unit suite and the
writing [comparison protocol](../../text-writing/evals/revision-protocol.md).

Revisit after a captured prior/candidate comparison measuring missed changes and
false alarms on independently selected tasks. Passing unit tests is not that result.

## ED-02 — Notice possible overediting without normalizing the author

Decision: **retain as opt-in observation; behavioral benefit untested**.
Compare the original and requested result, not a universal normal range. Fewer
headings or shorter sentences are not intrinsically good or bad. Supplied terms
are context, not a repetition blacklist. A requested summary is a valid control.

Implementation evidence: deterministic tests cover fragmentation questions,
removed structure, unchanged text, literal terms and nonblocking style observations.
Russian and English have word-segmentation tests, not calibrated quality bands.
Other languages, short samples and unsupported markup remain unverified. The
100-word default is an operational coverage guard, not an empirical optimal size.

Revisit after ordinary writing and technical-document tasks establish whether the
questions catch real damage without provoking unnecessary restoration.

## ED-03 — Target human bands or require two clean runs

Decision: **reject as a default acceptance rule**.
The external style-only result is counterevidence to treating numeric compliance
as authorship or quality proof. A repeated deterministic check adds no independent
sample. Clean author prose, useful repeated terms, technical navigation and
requested structural rewrites are controls an overbroad rule could harm.

No local result establishes that chasing bands or rerunning unchanged checks
improves writing. Retain one check after a relevant edit when execution is authorized;
keep task/meaning judgments separate from metric observations. This does not rule
out a future well-scoped, language/genre-specific experiment.
