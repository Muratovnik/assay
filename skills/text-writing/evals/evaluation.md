# Evaluation of text-writing

Evaluator-only material. `cases.json` contains task inputs, `rubric.json` the
criteria. Neither may be read while the skill performs a user's task. These
published cases were available during development and are not unseen evidence.

This revision is candidate C1 against the supplied 2026-09-16 snapshot, whose
pilot identifies its baseline as `1e6fb49`. C1 has no model-run result yet.
The earlier pilot tested a different revision using read-only tools; do not
transfer its score to C1, or say that it exercised file edits, this script,
Chinese behavior, full client discovery or publication. Unit tests of the
preservation tool establish only their explicitly tested structural conditions.

## Prepare the input

Use assay's existing frozen-packet preparer, one case at a time. Give the
executor only the prompt, context, named input files and the selected frozen
method. No rubric, prior answer, case kind, pair label or other case belongs in
its packet. Do not give it the whole handoff archive. The environment notes that
matter to the task must be in the case context, not in this evaluator file.

Keep all experiment conditions on the same input bytes. Bind a run to corpus,
method, model/settings and trial identifiers and preserve its receipts. A changed
input requires a new answer from both conditions. A changed rubric applied to
old answers is a separate adjudication result, never a rewritten historic score.

## Grade decisions, not one preferred sentence

Accept multiple correct phrasings within the requested authority. No-op is
correct when a text needs no change; it must not become a ban on an explicitly
requested rewrite, a genuine disambiguation or an evidence-backed correction.
Keep preservation, truth, task scope and optional preferences separate. One
preference should not be charged twice under equivalent no-op criteria.

For each criterion record its stable ordinal ID, a verdict, a short supporting
answer quote or artifact location, and the reason tied to the task sources.
Use `ungradable` for a broken or ambiguous task pending adjudication, not for a
model's wrong answer. Do not count omitted/ungradable criteria as passed.
A correctly limited `unverified` conclusion by the subject can earn `pass` when
the input evidence really is insufficient.

Mark actual effects from receipts or before/after artifacts, not from a model's
claim to have refrained. Tool-enforced lack of write access is not a measured
benefit of the skill. A read attempt is not proof of successful reading. A
missing terminal event or inaccessible input is an execution validity issue;
retain the attempt and any cost.

## Compared conditions and repeats

First compare frozen C0 and C1 on the revised known regressions. Keep model,
effort, instructions outside the method, permissions and tools comparable. Add
the ordinary-prompt baseline when assessing the value of a method at all.
Predeclare attempt counts and record all trials; never rerun until green and
report only the best one. Randomize answer labels and keep the key outside the
grader's input, noting that an answer can still reveal its method.

Use a separately authored and access-restricted fresh set to assess transfer.
The `N-` cases added with C1 are diagnostic regressions, not that fresh set.
Source validity, actual agent behavior and reader preference are different
results. A critical semantic failure prevents case acceptance even when prose
is preferred. Measure tokens, time and cost only from actual records.

Russian/English were the earlier pilot's scope. Simplified Chinese runtime and
cases remain in the package without new behavioral qualification. Use a grader
competent in each language or label those results unverified. No paid campaign,
new runner, delegation or global installation is authorized by this document.

## Local checks

Validate these data with the full repository's `tools/eval_assets.py check`.
The handoff's structural tests are not a replacement for that gate. Technical
preservation tests also have the explicit command:

```text
python -B -m unittest discover -s skills/technical-writing/evals -p "test_*.py"
```

Inspect tests before execution. This runs only the bundled check against known
fixtures; it does not run a model or arbitrary shell examples. Include this
suite in the real repository's gate if that gate does not already discover it.

## Selection and preservation alignment — 2026-10-08

The UI prompt previously required every supported fact, while drafting needs
selection for a reader's purpose. The corrected prompt and two preservation
passages protect the meaning of retained or explicitly required material and
keep copyedit and preserve-all scope intact.

The [shared relevance study](../../technical-writing/evals/relevance-study.md)
records a paired Russian volunteer-email task with the UI prompt explicitly
loaded, plus the existing `TW-EN-01-D` preservation control. Both the baseline
and correction select appropriate recipient-facing facts; the baseline was
already clean, so this pair establishes no comparative behavioral gain. The
corrected preservation control retains every required fact. These are explicit
invocation checks, not natural-discovery measurements.

`relevance-cases.json` publishes the ordinary email as TXTREL01, with a separate
rubric and public working metadata. Earlier cases and criteria are unchanged.
The [shared evidence record](../../technical-writing/evals/relevance-evidence.json)
contains the three outputs as runs 10-12, with source, method and packet hashes.

## Reader purpose and cross-method handoffs — 2026-10-08

The [shared durability study](../../technical-writing/evals/durability-study.md)
qualifies product-copy and language examples by the reader's actual task and
clarifies the writing owner inside larger work. It includes a Chinese public
card and helper reply where an actual seat-versus-book question requires the
contrast. That bounded execution is reported separately from earlier Chinese
coverage and does not establish general language qualification. Ordinary-prose
cases and their exposure records accompany this study's technical cases.

A later final failure in that study prompted a complete-text contribution check
for ordinary prose and correction of a portfolio example's unnecessary caveat.
The language profiles also retain useful explanatory endings without requiring
a next action. The study preserves the failed output, subsequent method identities
and a Chinese control that distinguishes a useful recap from a nearby duplicate.
