# Evaluating evaluation decisions

Coordinator-only protocol. These are synthetic scenarios, not measured Assay
results. The inline `record.md` in each case describes the subject experiment;
it is legitimate task evidence, not this corpus's grading key. Never give the
executor this protocol, `rubric.json`, `case-metadata.json`, other cases or
previous answers. Preserve the separate R1–R9 research/transfer specifications
in `research-and-transfer.md`; the inline corpus supplements rather than replaces
their source-backed manual setup.

## Prepare and inspect

Validate with `python tools/eval_assets.py check`. Prepare a selected input using
the existing utility, not a new runner:

```text
python tools/eval_assets.py prepare --cases skills/skill-evaluation/evals/cases.json --case SE01 --output-parent <existing-evidence-directory> --method <frozen-skill-evaluation-directory>
```

Omit `--method` for a no-skill control. For an old/candidate comparison use each
revision's own frozen method directory, not two copies of the candidate. Optional
peer methods must be deliberately supplied from their frozen roots when needed;
record missing peers and effective access limits. Retain the returned digest
outside the packet and use the existing audit packet verifier before and after
execution. Package integrity does not prove filesystem, history or network
blindness. Keep raw outputs, artifacts, settings, adverse attempts, grading
records and costs outside future inputs. No new installation, paid campaign,
delegation or publication follows from this protocol.

For `discovery_cases`, use `--collection discovery_cases` and the actual enabled
skill collection with the intended automatic route. Do not explicitly load this
skill to claim it was discovered. Observe qualified loader events and task
behavior; self-reports and mere prompt mentions are insufficient. With no usable
trace, discovery remains unverified even if the answer is good.

## Grade decisions, not wording

Use `required` and `reject` in the matching rubric entry. For each criterion retain
a supported, refuted or unverified judgment and the decisive passage, action or
artifact. Equivalent correct reasoning passes without exact terminology. A
confirmed forbidden effect is a failure, not an inconclusive result just because
other observations are missing. Missing material evidence remains inconclusive
when no decisive failure is established. Do not compute an invented scalar score
or use keyword matching as a substitute for these judgments.

Calibrate a model judge using known-invalid outputs and valid alternatives before
candidate selection; repeat grading of identical outputs and blind/vary pair
order where appropriate. Treat candidate instructions to the judge as untrusted
content. Preserve disagreements. Judge changes require a new measurement version
and consistent regrading of both conditions; changed task inputs can require new
execution. A reviewer who authored the change is performing self-review.

`SE01`–`SE24` cover attribution, calibration, adaptive selection, grouping, full
cost, routing, plateau diagnosis, subtraction, coverage, leakage, noise and hard
constraints, including legitimate controls. `SD01`–`SD08` cover positive and
negative invocation boundaries. All shipped examples are public working material,
not a hidden final set. A generalization claim needs separately reserved groups;
rephrasing these examples or rerunning them does not supply independence.

## Metadata and limits

The adjacent metadata records case provenance, group, purpose, split and exposure
without changing executor input fields. Its format and structural checks are
specified in [evaluation documentation](../../../docs/evaluation.md#evaluator-only-case-metadata).
The gate checks declarations, not semantic relatedness, actual secrecy,
representative sampling or whether a grader is correct.

The utility tests exercise real packet preparation, ID and metadata validation,
including negative controls. Neither their passing result nor this corpus's
existence demonstrates that a model applies the method successfully. Report an
authored corpus, checked utility, captured discovery, exercised behavior and
comparative support as different evidence states.
