# Research foundations

**English** · [Русский](../ru/research/README.md)

These studies examine the quality of research, software engineering, and the control of language-model behavior. They informed work on Assay, but can also be read and used independently of its skills.

## Read the studies

| Study | Questions it addresses | Full texts |
| --- | --- | --- |
| Research quality | What makes an investigation well-founded; how to evaluate evidence, alternatives, uncertainty, synthesis, and reporting | [English](foundations/research-quality.md) · [Русский](../ru/research/foundations/research-quality.md) |
| Software engineering | How system properties, engineering decisions, maintenance costs, tests, dependencies, and organizational conditions relate | [English](foundations/software-engineering.md) · [Русский](../ru/research/foundations/software-engineering.md) |
| LLM reasoning and behavior control | How instructions, examples, context, tools, feedback, training, and external enforcement affect observable behavior; how to test their limits | [English](foundations/llm-reasoning-control.md) · [Русский](../ru/research/foundations/llm-reasoning-control.md) |

Each language has a complete document, including the tables, examples, qualifications, unresolved claims, and bibliography. The Russian documents preserve the supplied source text apart from the added language navigation and status notice. The English documents are translations of that same text, not abbreviated adaptations.

## Evidence status and use

The supplied editions incorporate reviews dated October 5, 2026. The research-quality and LLM-control documents also describe targeted source checks during preparation on October 6, 2026. The software-engineering document explicitly says that its consolidation did not include a new external verification. Consult each study's own source-status and limitation sections: opening an abstract, checking a passage, recalling a work from memory, and reproducing an experiment are different levels of evidence.

Publication and translation here do not constitute a new literature review, independent replication, or validation of the studies as complete models. The documents distinguish empirical findings, methodological reasoning, practitioners' experience, recommendations, and unsupported claims. Preserve those distinctions when quoting, translating, or applying them. The LLM study's conclusions are bounded by the model generations, tasks, configurations, and evidence dates it discusses; a publication date does not establish applicability to every current model.

These are research documents, not normative Assay policy, runtime instructions, grading keys, or mandatory skill dependencies. The active task and applicable authoring and skill contracts determine what an agent must do. The research can inform a proposed revision, but does not silently override those contracts. Ordinary use of a skill does not require reading this corpus.

## Connections to Assay methods

The following map identifies related decision owners in the examined Assay revision, `08e8b7b989da36ad33acfa02c697f6527053f575`. It is navigation, not a claim that each skill derives entirely from one study, implements every conclusion, or has been behaviorally validated by that study.

| Foundation | Related method owners | Examples of relevant decisions |
| --- | --- | --- |
| Research quality | [Evidence research](../../skills/evidence-research/SKILL.md), [independent audit](../../skills/independent-audit/SKILL.md), [skill evaluation](../../skills/skill-evaluation/SKILL.md) | Match evidence to a claim; preserve uncertainty and source independence; distinguish a checked outcome from a completion label |
| Software engineering | [Code change](../../skills/code-change/SKILL.md), [software architecture](../../skills/software-architecture/SKILL.md), [implementation planning](../../skills/implementation-planning/SKILL.md), [test writing](../../skills/test-writing/SKILL.md), [test audit](../../skills/test-audit/SKILL.md), [independent audit](../../skills/independent-audit/SKILL.md) | Compare reuse and maintenance costs; justify boundaries; choose meaningful checks rather than treating a green signal as the entire goal |
| LLM reasoning and behavior control | [Skill evaluation](../../skills/skill-evaluation/SKILL.md), [subagent routing](../../skills/route-subagents/SKILL.md), [authoring contract](../../AGENTS.md), [hook boundaries](../how-to/hooks.md) | Distinguish discovery, loading, execution, observation, and enforcement; bound transfer from literature to a local method |

Publication preserves the studies without importing their entire contents as instructions. Representative themes already have owners: evidence-to-claim fidelity in evidence research, boundary and reuse decisions in software architecture, and research transfer and behavioral evidence in skill evaluation. This placement check is not an exhaustive finding-by-finding transfer audit and does not establish that no method gaps remain.

For a later method change, connect the particular source passage and its limitations to the decision it should improve, inspect existing coverage, and use the [research-transfer procedure](../../skills/skill-evaluation/references/research-and-transfer.md). Retaining existing guidance, adapting a finding, rejecting a transfer, or leaving a question open are all possible outcomes. The presence of a study does not require adding a rule.

## Maintaining the language pair

Keep the corresponding English and Russian sections synchronized when changing substantive content. Preserve section numbering, tables, examples, names, identifiers, link targets, numeric values and units, negations, applicability conditions, and verification status. Dates and decimal typography may follow the language without changing their meaning. Update translated internal anchors when headings change.

Do not silently repair a disputed source claim in only one language. A substantive correction needs its grounds and affected conclusion recorded in the study; a translation correction should restore the source meaning. Keep the studies' evidence dates distinct from later editorial or translation dates. Structural checks can detect missing sections, citations, or values, but do not prove semantic equivalence or source accuracy.

## Other research records

[Product-flow mapping](product-flow-mapping.md) records a narrower transfer into a method. [Text skills C1](text-skills-c1.md) records historical candidate corrections and their evaluation limits. These records serve a different purpose from the full foundational studies and remain separate.
