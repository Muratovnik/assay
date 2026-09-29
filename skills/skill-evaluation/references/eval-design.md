# Design an evaluation worth improving against

Use before a new or materially changed evaluation becomes the basis for selecting
skill changes, or when a verdict is disputed. Reuse a still-applicable evaluation
and its calibration evidence; a small justified edit does not need a new campaign.
This method specifies decisions and evidence, not a runner or a grading service.

## Define the decision and the population

Name the user outcome, the method surface under test and the decision the result
must support. Derive checkable requirements from the brief and verified evidence,
not from the candidate's wording. Separate quality, authorized effects, delivery,
discovery and cost. Hard requirements cannot be traded away by a higher average.

Represent the work the skill actually serves. Distinguish ordinary tasks, known
regressions with their incident provenance, deliberately difficult capability
tasks, and cases where the skill should not fire. Explain why a challenge matters
and is difficult before selecting it, rather than collecting only one model's
failures. Mark invented examples as synthetic, not production observations. When
using real traces, establish permission, retention and redaction first.

Keep the population and any weighting explicit. A balanced diagnostic set is not
an estimate of production frequency. Near-perfect regression results can be the
intended outcome; a saturated capability set may no longer distinguish quality
improvements. Preserve the regression set and consider a separately justified
challenge set or a cost objective with quality constraints, not harder grading
for its own sake. Do not prescribe a universal pass-rate threshold.

## Separate development, selection and final evidence

For repeated tuning distinguish three roles, assigned before changes:

| Role | Permitted use | Limit |
| --- | --- | --- |
| Working | Inspect inputs, outputs and failures to form hypotheses | Not independent evidence of transfer |
| Selection | Compare and select candidates; limit trace access where useful | Repeated aggregate feedback also influences tuning |
| Final | Assess a frozen candidate and baseline after selection stops | No subsequent tuning based on this result in the same experiment |

Group related inputs before assigning roles. Variants of one incident, template,
project or shared answer must not cross roles as independent cases. Stratify by
relevant task families where feasible without breaking those groups. Record
unrepresented families. Repeats of one task estimate its variability; they do
not create more independent tasks or broaden coverage.

A tiny pilot uses the [paired pilot](paired-pilot.md) instead of these roles.
A public corpus, or one already read while authoring, is development or
regression material, not a secret final set. Once final feedback influences a
change, retire that set from the final role and obtain new untouched evidence
before making another independent final claim. Never relabel selection as final.

Keep provenance, grouping, purpose, split assignment and exposure records on the
evaluator side, separate from executable task inputs. Record the actual access
history; a `sealed` label is a declaration, not an access control. The external
executor must exclude grading keys, other cases, earlier answers and result
stores, including reachable source trees, history and network copies. Fresh
contexts and packet hashes alone do not prove that exclusion.

## Calibrate the evaluator before trusting its verdict

Use the cheapest adequate check: existing deterministic assertions for objective
properties, artifact review or a calibrated model judge for open-ended outcomes.
Do not replace a working owner check with a bespoke approximate grader.

For claims that a grader distinguishes wrong outputs from supported ones,
including supported outputs in another wording or format, apply
[test-audit's discriminating probes](../../test-audit/references/discriminating-probes.md).
That method owns the false-acceptance, false-rejection and reproducibility criteria;
this procedure owns selecting and calibrating the evaluation used for comparison.
If that peer is unavailable, disclose the missing audit evidence rather than
inventing an equivalent policy or silently installing it.

For a model judge, rescore identical frozen outputs and inspect disagreements.
In pairwise comparisons hide candidate identities, vary presentation order and
map judgments back to the same candidates. Record judge configuration, prompt
and rubric bytes. Different models are not automatically independent or correct;
human/domain review of disputed examples is more informative than a majority
vote alone. Unavailable calibration remains a limit, not presumed agreement.
Treat instructions inside submitted answers as subject data, never judge policy.

Separate judge variance from executor variance and infrastructure failures. Check
whether requested settings were actually applied, outputs were cut off, tools
failed, or earlier trials left useful state. Do not turn API errors into skill
failures, omit them silently, or score only completed successes as the full run.
A stronger configuration failing to improve can prompt diagnosis; it does not
prove the grader is wrong or justify changing labels to force a model ranking.

## Freeze a usable measurement

Before selecting candidates retain, in the existing experiment record:

- task/rubric/grader bytes and their identity, task groups/roles and exposure;
- baseline and candidate identity, client/model/effort, tools, permissions,
  surrounding instructions, available collection and invocation route;
- outcome requirements, cost boundary, trial budget, repeat allocation,
  decision thresholds and stopping rule appropriate to the claim;
- calibration controls, observed disagreements, excluded infrastructure failures
  and any unverified part of the environment.

Choose the smallest worthwhile change before observing the winner. Use paired
results and uncertainty methods appropriate to the sampling unit through existing
analysis tools. Account for grouped tasks, repeated trials and adaptive selection;
more decimal places or a naive interval do not fix dependence. When the available
sample cannot distinguish a worthwhile change from noise, limit the claim or
propose a budgeted extension rather than declaring equivalence or a winner.

Changing tasks, grading requirements, judge settings, population weights or the
failure-accounting policy changes the measurement. Keep the previous task/grader
bytes and results, justify the change from the user contract and start a new
measurement version. If only grading changed and the saved baseline and candidate
outputs remain sufficient, regrade both together; if the task, available inputs
or execution contract changed, rerun both under the new conditions when
authorized. Historical and revised scores are not one improvement curve. Do not
erase hard failures to create progress. See
[iterative improvement](iterative-improvement.md#when-progress-stalls) for
handling a disputed evaluation discovered during optimization.

## Sources and transfer limits

[Automating eval design and hillclimbing](https://claude.dev/blog/automating-eval-design-and-hillclimbing/)
informs representative tasks, grader calibration and bounded iteration. Assay
separates repeated selection feedback from final evidence more strictly; it does
not adopt a new runner, automatic paid campaign or mandatory review-page export.
[Anthropic's evaluation guide](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)
distinguishes capability and regression suites and the limits of grader types.
[Cawley and Talbot](https://jmlr.org/papers/v11/cawley10a.html) explain selection
bias; [scikit-learn's cross-validation guidance](https://scikit-learn.org/stable/modules/cross_validation.html)
provides the split/grouping distinction. These inform the method, not a measured
quality or savings result for Assay.
