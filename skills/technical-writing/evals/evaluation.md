# Evaluation of technical-writing

Evaluator-only material. `cases.json` contains task inputs, `rubric.json` the
criteria. Neither may be read while the skill performs a user's task. These
published cases were available during development and are not unseen evidence.

The historical C1 comparison used the supplied 2026-09-16 snapshot, whose
pilot identifies its baseline as `1e6fb49`. No model-run result was recorded
for that C1 comparison. The earlier pilot tested a different revision using read-only tools; do not
transfer its score to C1, or say that it exercised file edits, this script,
Chinese behavior, full client discovery or publication. Unit tests of the
preservation tool establish only their explicitly tested structural conditions.
The content-selection amendment below has its own baseline and bounded results;
it does not rewrite either historical record.

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

For the historical C1 protocol, first compare frozen C0 and C1 on the revised
known regressions. For a later amendment, identify its actual prior bytes. Keep model,
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

## Content-selection amendment — 2026-10-06

### Decision and source basis

The owner reported redundant explanations, obligatory-looking installation and
first-launch sections, decorative examples and release/work notes in Tolmach's
README. Review used [Tolmach at b915b0d](https://github.com/Muratovnik/Tolmach/tree/b915b0dde4086aec977018d1faff4338b6565855)
and [Assay at 08e8b7b](https://github.com/Muratovnik/assay/tree/08e8b7b989da36ad33acfa02c697f6527053f575).
Tolmach's coverage document also contained a current-support table and a stale
exclusion about the same supported integrations. Its current README had changelog
navigation, not a standalone `What changed` section; do not invent that finding.
No historical instruction-load trace establishes that Assay caused these outputs.

The confirmed method conflict was narrower: the general editorial guidance
already selected content by reader need, while the README module, adopted
profile and public template pushed a demonstration and first-result sequence.
The amendment makes those slots conditional, clarifies content placement and
updates, and separates authorized removal from the conservative preservation
check. It changes the existing owner rather than adding a humanizer or runtime.

Transfers from the source review:

- [Google's audience guidance](https://developers.google.com/tech-writing/one/audience):
  use the gap between this reader's established knowledge and the task, not the
  editor's inventory of facts. A known term can replace its repeated definition.
- [Diataxis](https://diataxis.fr/how-to-use-diataxis/): choose the document's
  function and needed content; do not instantiate empty document-type templates.
- [Anthropic's doc-coauthoring workflow](https://github.com/anthropics/skills/blob/main/skills/doc-coauthoring/SKILL.md):
  select, combine or remove material before polishing it, and inspect the result
  as its reader. Do not import mandatory question rounds or extra reader agents.
- [Google's notices guidance](https://developers.google.com/style/notices):
  put material prerequisites and warnings where they change an action. An
  author's unperformed check is not automatically a product warning.
- [Vale](https://docs.vale.sh/) and
  [Humanizer](https://github.com/blader/humanizer/blob/main/SKILL.md): narrow style
  diagnostics can help; a clean lint result or a punctuation blacklist does not
  establish useful content. No new linter, word ban or imitation of personality
  was adopted. Existing language and editorial references remain the owners of
  prose judgment.

These are adapted decision criteria, not copied implementations or measurements
of Assay. The runtime entry points do not link to this evaluator record.

### Added public regression groups

Eight task cases and two discovery inputs extend the existing schema. All 32
previous task records, 13 previous triggers, their criteria and shared dimensions
remain unchanged. In particular, TW04/TW14/TW16 and the narrow no-op/copyedit
controls retain their original expectations. New inputs are synthetic, public
working/regression material; none is an unseen final set.

| Group | Decision and legitimate control |
| --- | --- |
| TW19/TW20 | Same Cedar facts for a public README and release acceptance report; the latter needs the verification record. |
| TW21/TW22 | Catalog-managed Lark installation versus real Silt setup and first export. TW21 also distinguishes a familiar client-side term from an unfamiliar setting the task explicitly asks readers to choose. |
| TW23/TW24 | Rewrite can remove an irrelevant fenced authoring command; a narrow copyedit preserves it outside scope. Both preserve user commands, conditions and required notices. |
| TW25 | Successive Quarry updates reconcile old exclusions, workarounds and format-specific bounds. |
| TW26 | An ADR keeps accepted/proposed status, genuine history and operational consequences. |
| TT14/TT15 | Ordinary documentation request from code sources versus code-only work. Input classification alone does not prove discovery or a two-turn transition. |

A hard loss of a necessary condition, qualifier, status or notice cannot be offset
by brevity. No preferred sentence, punctuation quota, heading count or word count
is an oracle. The unfamiliar-setting requirement in TW21 was aligned with the
explicit brief during independent review so that a merely supplied fact does not
become mandatory publication content.

Three direct probes exercised the unchanged preservation checker with the new
TW23 source: identical input returned `0`; removal of the irrelevant author
block returned `1` for `fenced_code`; removal plus a damaged retained user flag
returned `1` for both `fenced_code` and `inline_code`. Those results distinguish
intentional removal from additional corruption without suppressing a failure.
They test scanner behavior, not a model's interpretation or semantic fidelity.

### Execution conditions and retained attempts

The diagnostic used the prior runtime bytes from `08e8b7b` and the amendment,
with fresh native collaborator tasks configured as `gpt-6.1-sol`, effort `high`,
no conversation inheritance, the same tools and the same delivery wrapper.
P1/P2/P4 explicitly named the frozen technical-writing method. P3 supplied the
complete 14-skill inventory and allowed task-based selection. There was no
installed-client or hook integration in this experiment.

The existing `tools/eval_assets.py prepare` produced input-only frozen packets.
Its snapshots include entry points, references and adapters, so complete working
method copies also supplied the matching assets and scripts, excluding `evals/`.
Packet and method hashes were checked after execution. Raw inputs, criteria,
outputs and consumer-check records were retained outside source, separately from
future inputs. The SHA-256 of each sorted runtime-file/hash map was:

| Method bytes | Digest |
| --- | --- |
| Prior technical-writing | `3172b7efccc88870f63e81646744ba5bb69d066c84691a7a781e5a1b0ce3929b` |
| Initial amendment | `3957f4be13c407e80f3f6edb67f4a361ef4adb723882574ba8c83872d329dbcf` |
| Revised amendment | `7d721822979f5df3514990379072b276b620601ee2168b062f34a842d9ff03ce` |

Four paired tasks were the diagnostic budget. P1/P2 share source facts and are
one group, not independent samples of a population. A separate author prepared
P4, and its criteria were not read by the primary until both outputs existed.
The revised runtime was frozen before P4 and was not tuned from that result.

Two additional executor attempts were retained: the initial P1 amendment still
published the work-record acceptance note, prompting a narrow clarification and
one changed-candidate run; the first prior P3 task left its code-only boundary
ambiguous and also updated docs. That attempt is not scored as unauthorized
behavior. The brief was made explicit for both conditions before comparing P3's
code phase and subsequent documentation request. There were ten initial executor
tasks in total, plus the two P3 continuation turns. Unexecuted prepared packets
are not results, and unchanged tasks were not rerun to select a preferred answer.
Two packet preparations rejected an output directory inside the protected source
boundary before any executor ran; output/source placement was corrected without
changing the preparer.

These were instruction-separated directories on a shared filesystem, not an
enforced sandbox. The root and case author had access to keys; executor prompts
excluded keys, sibling results and source history, but the tool surface did not
prevent outside reads. A separate source review inspected P1 and incidentally saw
P4 completion summaries, so it was not a blind outcome judge. No calibrated model
score, full native read trace, billed usage or quota measurement is available.

P4 has an additional harness limit: its supplied context requested a Markdown
answer without file edits, while the common wrapper requested a saved working-copy
artifact. Both conditions wrote the disposable runbook copy and retained the
other inputs. Compare their document meaning and command fidelity; do not use
this conflicting delivery setup to grade authorization or absence of effects.

### Observed artifacts and decision

Inspection compared the finished documents with the supplied facts and scope.
The table reports decisions within these tasks, not a pass percentage.

| Task | Prior and revised observations | Supported conclusion |
| --- | --- | --- |
| P1: Vern catalog README | Prior output included catalog installation, a first-launch sequence, the literal translation example, release-specific idols, the unperformed game check and a defensive provenance sentence. The revised output omitted those while retaining coverage, language/restart, translation exceptions, saved-value distinctions, setting scope and attribution. It still expanded the familiar client-side term into a redundant sentence. | Content selection improved on this regression, but the familiar-term criterion remains refuted. P1 is partial, not an accepted clean result. |
| P2: same facts, release acceptance report | Both kept the exact archive/date, actual package/dictionary checks, unperformed gameplay and remaining owner decision; neither claimed acceptance. Both retained some unnecessary product/provenance detail. | The verification-status control was preserved. No general concision or quality advantage is established on this task. |
| P3: Listfmt code, then documentation | In the clarified code-only phase both changed only the Python file. On the subsequent ordinary documentation request both updated README and format reference, removed stale JSON exclusions, retained default text/CSV limits and supplied the actual checkout/Python requirements. | The transition artifacts are correct in both conditions. A separate CLI observation confirmed order, duplicate names, Unicode and the unchanged text default; the code stayed unchanged during the docs phase. |
| P4: Glint runbook rewrite | Both retained the two symptom thresholds, region-specific pending validation, restart conditions, exact command syntax, five-minute checks, stopping/escalation and irreversible-deletion conditions. Both omitted editorial history. | No semantic regression found in this reserved operational control. Its authorization dimension is ungradable because of the wrapper conflict above. |

P3 executors reported choosing code-change and then technical-writing. The
artifacts corroborate task completion, not the actual load/read sequence.
Automatic discovery remains unverified without the intended installed-client
trace. No observed missed route justified changing a peer link, trigger or hook.

Independent source review accepted the guidance and revised public cases after
checking the unfamiliar-setting and protected-deletion controls. It also confirmed
the residual P1 redundancy: the README uses `клиентский мод` and then repeats
player-only/server-unneeded installation despite the stated audience knowledge.
The relevant instruction already exists; another paraphrase or routing change
is not supported by that observation. The new TW21 criterion keeps this failure
visible for later work rather than declaring it solved.

The amendment is structurally checkable and behaviorally exercised, with a
bounded improvement in selection and a remaining execution defect. It does not
establish flawless prose, full discovery, model portability, savings or a pass
on every public case. Further iteration needs a distinguishing execution trace
or acceptance intervention, not another synonymous rule or repeated unchanged
run. Preserve these results if that later work changes the evaluator or method.
