# Compare Assay skills on real tasks

**Scope:** a reproducible study protocol for the existing evaluation assets, not an automated benchmark command. Start with [the evidence review](../research/skill-effectiveness.md) for what is and is not currently measured. This guide is for an evaluation coordinator with an authorized client, disposable task environments and access to genuine execution traces. It does **not** authorize model calls, paid usage, delegation, external writes or installation.

## 1. Specify the decision before running anything

Write down which claim you are testing:

- **Whole collection:** Does a naturally installed Assay collection improve end-to-end outcomes relative to the same client without Assay?
- **Named skill:** Does one method improve the specified work, with its conditional peer methods held fixed?
- **Candidate revision:** Does a particular change beat the **actual frozen previous bytes**, not a recollection of them?
- **Discovery:** Does the native client select and read the right method at the right step?
- **Cost parity:** Can a method reduce accepted-delivery expense without losing any required outcome?

These are **different experiments**. Do not combine their results into one pass/fail score. State the model/client versions, time, task population, measurable outcome, smallest worthwhile difference, hard disqualifiers, cost boundary and maximum attempt budget **before** seeing the compared outcomes.

For a low-cost diagnostic pilot, follow [paired-pilot](../../skills/skill-evaluation/references/paired-pilot.md): select three or four representative tasks, each under both conditions, including a known failure, a valid neighboring control and a task so simple that extra process should not be needed. **This is a diagnostic, not a statistical effect estimate.** Do not turn its run count into a confidence interval implying generality.

If optimizing more than one candidate or accepting a new evaluator, follow [eval-design](../../skills/skill-evaluation/references/eval-design.md) and [iterative-improvement](../../skills/skill-evaluation/references/iterative-improvement.md) before tuning. They already own evaluator calibration, grouping, trial budgets and evidence splits; this guide adds no second evaluation service.

## 2. Freeze task conditions and separate evidence

For each case, preserve:

1. The original user's request, external constraints, target repository commit or document bytes, and actual accepted-result criteria **independent of any candidate output**.
2. Its task family/project/incident group and why that group belongs to the target population. Mark synthetic cases synthetic. Pair a known-invalid case with a nearby legitimate action or implementation that must remain valid.
3. An input-only packet and an evaluator-only bundle with grading expectations, private source keys, previous runs and corrections. All evaluator bundles must remain **outside the executor's effective read roots and accessible tools**.
4. Exact Assay and comparator revisions, loaded skill/reference bytes or hashes, active root instructions, optional peers, client, model snapshot and effort, inference settings, available tools, network access, filesystem permissions and invocation route.
5. Maximum calls or elapsed work per attempt, the permitted side effects, rollback/disposal policy and what counts as a setup failure versus a skill failure.
6. The evaluation policy for partial completion, refused actions, guessed evidence, unauthorized mutations and remaining user corrections.

Do not put both the rubric and a task packet into the executor's accessible working tree. A fresh chat or package digest **does not itself prevent reading other files, installed skills, connected apps or prior test answers**. Where full isolation cannot be established, mark the run **instruction-bounded, not blind**, and do not use it for a leakage-sensitive claim.

The public cases in Assay's skill evals directories are suitable for regression diagnosis and working development. They are **not** independent final evidence after their answers or expected behaviors have been consulted. Group by shared original incident/template/project and keep related cases in one role. New final evaluation groups must be genuinely reserved and kept outside the source repository and executor access; merely setting the word "sealed" in public metadata does not make them hidden.

## 3. Build matched conditions

| Condition | Skill availability | Question answered | Restriction |
| --- | --- | --- | --- |
| A — baseline | Named skill absent; for whole-collection comparison all Assay skills absent | What the unchanged agent can deliver | Retain **the same necessary project brief, contracts, runtime and tools**; removing required repository facts is an unfair comparator |
| B — natural | Actual deployed collection and automatic routing | Does the intervention work as users encounter it? | Observe load/read events; a self-report is insufficient. Keep order of conditions counterbalanced |
| C — forced diagnostic | Coordinator explicitly supplies the exact named skill and its genuinely applicable references | Does guidance help *if it is definitely supplied*? | **Never substitute for B** as evidence of automatic discovery |
| D — ablation, optional | Full collection except a named skill; other peers held fixed | What is its conditional contribution in the complete system? | Different from a standalone skill effect; interactions prevent additive rankings |

For a previous-vs-candidate method comparison, substitute frozen old and candidate bytes for A/B while retaining the exact same evaluable task, client, peers, tool permissions and grading method. A forced read may help diagnose why natural routing missed; report its role separately. If a skill changes model, available tools, number of attempts or research source access as part of the treatment, describe the **combined intervention** and do not attribute all the difference to instruction wording.

Use case-level random/counterbalanced order across pairs to limit time and learning effects. Prefer fresh genuinely isolated contexts and disposable project copies. Treat repeated samples of one task as within-group variability, **not independent new tasks**. Keep failed attempts and setup failures in the record; do not rerun unchanged inputs until a favorable result appears.

## 4. Prepare the existing corpus without exposing its grading key

Assay already has packet tools; do not build another runner for the sake of this procedure. In an authorized local checkout with existing isolated Python dependencies, from the repository root:

    python tools/eval_assets.py check

    python tools/eval_assets.py prepare --cases skills/evidence-research/evals/cases.json --case E01 --output-parent /path/to/coordinator-evidence

The second command is **an illustrative example** using the documented case-ID pattern; confirm the actual selected ID and output directory in your checkout before executing. Its returned manifest digest belongs in the coordinator's inaccessible results store, not in the executor input.

For eligible audit fixtures use the specific [independent-audit packet procedure](../../skills/independent-audit/evals/protocol.md); for a generic method use [skill evaluation](../../skills/skill-evaluation/evals/evaluation.md). Where required, include frozen, applicable optional peers **equally in both arms**. Do not fetch current peer files into a comparison supposedly pinned to an old revision.

Use the actual returned packet path and recorded pre-run manifest hash with:

    python skills/independent-audit/evals/verify_packet.py /path/to/packet --manifest-sha256 RECORDED_DIGEST

The verifier checks declared bytes and unexpected files/links, **not actual isolation or semantic validity**. Pre/post digest agreement does not rule out transient writes elsewhere. The existing [native smoke tool](../../tools/native_smoke.py) may qualify client loader traces; at the examined revision its Codex mapping is insufficient to establish automatic skill activation. Do not equate "tool invoked", "skill read", "criterion applied" and "artifact accepted".

Execution belongs in the configured native client, using its already authorized sandbox or disposable working copy. The fixture preparer **does not launch the model**.

## 5. Choose observations that can reject a convincing but wrong result

Grade five separate dimensions, against an acceptance contract established **before** candidate inspection:

| Dimension | Adequate primary observation | Inadequate substitute |
| --- | --- | --- |
| **Consumer outcome** | Running the changed command, interacting with the rendered UI, checking source fidelity or evaluating an actual decision against given facts | Plausible prose, a summary of intended implementation, file counts |
| **Correct criterion** | The selected option changes for the relevant condition; appropriate alternatives and trade-offs affect the decision | A table with the right column headings or repeated skill terminology |
| **Authorized effects** | Actual changed files/state, preserved permissions and failure paths; ideally trace and state before/after | A green happy-path test or a statement that no other state changed |
| **Discovery and process** | Qualified native load/read events and observed tool results, with decision timing | Presence of the SKILL.md file or self-reported use |
| **Delivery and cost** | Requested artifact and end-to-end accepted outcome; observed agent, reviewer, rerun and correction usage | One successful tool call or tokens for only the final response |

Include positive, should-not-fire, boundary/exception, unfamiliar, conflicting, adversarial and long-running cases **when relevant to that skill**. Do not require every category for a simple edit. Consider a known-invalid and nearby valid control for each material restriction. For a test-writing result, mutate a disposable example to introduce the claimed defect and check the oracle would reject it; make sure the valid equivalent implementation still passes. For audit or research conclusions, inspect their evidence sources and qualifiers, including tables and version labels. For an agent workflow, examine actual final artifacts, not only an answer about how to do the work.

Any **confirmed unauthorized effect, fabricated decisive evidence or violated hard requirement** is a hard failure. It must not be offset by more words, lower tokens, more other passed checks or a higher soft judge rating. For open qualitative outcomes, calibrate a blinded judge against **known invalid and legitimate variants**, repeat grading identical artifacts and report disagreements. Grading keys from a candidate's own prose are not independent expectations.

## 6. Measure differences and uncertainty honestly

For an identical case set of N independent task groups with binary accepted outcomes, the descriptive paired difference in percentage points is:

    100 × mean_i(accepted_with_skill_i − accepted_without_skill_i)

An improvement is a **paired comparison**, not the proportion of polished final answers. Report both arm rates, the four paired outcome counts (**both pass, both fail, skill-only pass, baseline-only pass**), total N, the full raw outcome table and any missing runs. Preserve group identity: multiple trials or paraphrases of a case are **clustered within the original group**, not independent observations. If the evaluation is a purposively balanced set, label its effect **on that set**, never as an estimate for typical Assay traffic.

For sufficiently varied independent groups, use a paired uncertainty method appropriate to the outcome and design (for example, a **cluster-level bootstrap** resampling task/project groups together). Report the interval method, number of groups, repeats and zero/failure accounting. A small pilot may be too imprecise for an inferential interval; say so rather than manufacturing decimal confidence.

Handle saturation explicitly: if both arms pass every tested task, this only rules out failures *seen in those conditions*. It does not establish equivalence, especially for harder tasks and newly added constraints. Define a **practically meaningful quality difference or non-inferiority margin before measuring** when the intended claim is "same quality at lower cost"; lack of a statistically significant difference is **not** a non-inferiority result. Do not collapse incomparable document, coding and UI rubrics into one arbitrary average.

Cost should include preparation when treatment-specific, assistant/subagent steps, model calls, tool calls, reviewer work, integration, retries and remaining user corrections through **accepted delivery**. Record tokens, elapsed time, billed API cost if actually known, and subscription quota as **separate quantities**; no transformation of tokens or benchmark prices into invented subscription usage. Report cost per accepted result alongside failure/censoring counts, not only mean cost per attempt. Where a component cannot be measured, mark **unknown** rather than zero.

Before changing method text after observing results, freeze and archive working evidence and reserve an untouched final group. If the evaluator, oracle, cases, population weights or failure policy changes, version the measurement and regrade **both** saved conditions together if possible. If execution input or treatment changed, run both again only under a separately authorized budget. Never combine successive measurements with changed criteria as a smooth improvement curve.

## 7. Record a study that another reviewer can challenge

Use the coordinator's existing evidence record; no compulsory new platform, database or tracked results store. The minimal comparison entry for each pair needs:

| Field | Meaning |
| --- | --- |
| identity | Study ID, date, main commit and skill/revision content hashes, client and model snapshot |
| population | Task/incident group, provenance, selection/exclusion reason, role: working / selection / final; actual exposure |
| treatment | Baseline A/B/C/D, natural vs forced route, available peer methods, surrounding instructions, permissions and tools |
| execution | Attempt ID/order/seed where available, raw trace and artifact pointers, effective isolation and loader-observation status |
| outcome | Independent criteria, hard-failure status, accepted/partial/refuted/unverified observations and grader version |
| cost | Per-attempt usage, retries, full-chain cost boundary, missing or noncomparable measurements |
| integrity | Raw task input hashes, packet digest, before/after state, judge blindness and any contamination |
| decision | Outcome supported by the observed population, contradictions, remaining uncertainties and stop reason |

Publish a **summary and appropriately sanitized reproducibility materials** when authorized. Do not publish private traces, token keys, leaked answers from genuinely reserved final tests, user data or unredacted connector content. Failed attempts and false activations should be represented in aggregate even if their raw data cannot be shared.

A useful final report answers: (a) whether the skill was naturally discovered, (b) whether its relevant instructions were actually used, (c) whether the **real task** improved against a comparable baseline, (d) whether legitimate work and hard boundaries were preserved, and (e) at what total observed cost. If one of these could not be measured, the answer is **unverified** on that dimension.

## 8. Promote a change only for an actual supported cause

Choose among **retain**, **narrow**, **remove**, **reposition**, **repair evaluator**, **change discovery**, **repair implementation/tooling** and **defer for more evidence**. These are not ordered toward "more skill text":

- If a rule is correct and the model never read it, investigate routing or conditional load timing before adding prose.
- If it read the rule and ignored it, compare execution/feedback paths and the actual consumer; a new paraphrase is not automatically a fix.
- If grading accepts the original defect, fix the oracle, preserve old and new measurement versions and regrade both arms. That repair is **not a measured gain** from a new skill.
- If a rule blocks valid nearby work, check the owner's actual contract and narrow the rule, keeping the protected failure case.
- If both arms succeed on easy tasks, retain the method or investigate cost with an explicit quality floor; do not invent an effect to justify a rewrite.
- If a material gain survives relevant controls and an independent final comparison, report its **task population, revision, model, uncertainty and cost**, not a universal percentage.

Repository source checks and hosted CI can establish that the eventual change is packaged and integrates. They cannot replace the above behavioral comparisons. Publishing a proposed PR is distinct from a behavioral qualification or a merge.
