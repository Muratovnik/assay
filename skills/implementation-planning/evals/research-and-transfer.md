# Planning method: research and transfer decisions

Authoring evidence, not runtime instructions or an evaluation answer key.
Reviewed for the implementation-planning addition on 2026-09-25. External methods
are design evidence; none of the sources below establishes that this Assay skill
improves outcomes. The procedures and synthetic cases are independently written;
no external runtime, evaluation dataset or implementation is bundled.

## Scope and ownership

The gap is a shared method for a grounded plan, its acceptance and its evolution
across stages. Code maintenance and UI delivery already share staged-migration
criteria; independent audit needs to assess a plan without implementing it.
These are concrete integrations in this change, not measured usage or behavioral
benefits. The new method owns sequence, readiness and continuity, not code
architecture, UI semantics, test design, research infrastructure or agent dispatch.

Reuse sufficient verified prior research. Current implementation scope checks
included the Assay authoring contract, catalog, existing three consumers,
reuse-and-migration reference, evaluation packet owner and projection/generation
checks. The baseline was main at `c642a41f9d9c88b252b775514a62fd8c242d7b09`.

## Source register and limits

| Source and examined location | Decision-relevant observation | Limit |
| --- | --- | --- |
| [Superpowers writing-plans](https://github.com/obra/superpowers/blob/8ca22dba9a94f28898bbce59f2537ff4d87c747d/skills/writing-plans/SKILL.md), task sizing, file structure and plan template | Outcome-sized reviewable tasks, concrete files and carried interface constraints; also prescriptive small steps and code examples | Instruction design, not a comparative outcome study |
| [Compound Engineering traceability design](https://github.com/EveryInc/compound-engineering-plugin/blob/4043703d32c5df9e35f22757dee22f3a72a99c66/docs/plans/2026-04-21-001-feat-ce-plan-traceability-loop-plan.md), overview and R1-R9 | Stable unit IDs and origin/acceptance links survive reordering; origin-only structures are conditional | Historical design document, not proof of current shipped behavior. The previously discussed current ce-plan paths returned 404 during this implementation; no current implementation claim is made |
| [Spec Kit analyze](https://github.com/github/spec-kit/blob/b60057692cd726ea56331ec47f9ebc3e8877d8f7/templates/commands/analyze.md), semantic models and detection passes | Compare requirements, tasks, coverage, ambiguity and consistency | Consistent documents do not establish implemented behavior |
| [OpenSpec editing changes](https://github.com/Fission-AI/OpenSpec/blob/65a7233f36ad022e99cc23115279768b8ca24fb6/docs/editing-changes.md), editing artifacts and resolving discrepancies | Plans/specification can evolve during implementation; determine whether specification or implementation must change | Flexibility does not authorize changing the brief to excuse code drift |
| [ExecPlans recipe](https://developers.openai.com/cookbook/articles/codex_exec_plans), plan expectations and template | Recoverable context, observations/decisions, behavioral validation and recovery | Archived recipe; used as historical method evidence, not current client/API policy |
| [GSD phase planning](https://github.com/open-gsd/gsd-core/blob/155c08facfed172a14fbd204ab75c841c706d1f9/docs/how-to/plan-a-phase.md), phase plans and tracer-first | Stage-level planning and early end-to-end integration slice | Revision from the development branch `next`; no stable-interface or comparative effectiveness claim |
| [Planning with Files](https://github.com/OthmanAdi/planning-with-files/blob/4d24d9a8a2baa55a15e7f8f9ec6da8d19793ee8c/skills/planning-with-files/SKILL.md), task-specific recovery and shared-plan ownership considered in prior research | Recover the chosen task, preserve evidence and avoid competing writers | Prior-research transfer, not independently rerun here; no import of fixed files, hooks or interaction counters |
| [Claude Code plan mode](https://code.claude.com/docs/en/common-workflows#plan-before-editing), plan before editing | A permission mode: read files and propose a plan, make no edits until approval | Mutable client documentation; limits effects and sets the flow, not plan-quality criteria |
| [Codex Plan Mode](https://github.com/openai/codex/blob/782826663df3e898d0c594a13f6f75cc2a498644/codex-rs/collaboration-mode-templates/templates/plan.md), mode rules, phases and finalization | Non-mutating exploration before questions, two kinds of unknowns, a decision-complete plan in a compact format | Client template for a plan implemented right away; no roadmap, replanning or interrupted continuation |
| [Assay skill-evaluation transfer method](../../skill-evaluation/references/research-and-transfer.md) and [evaluation method](../../skill-evaluation/SKILL.md) | Tie rules to decisions, valid controls and observable checks; distinguish packaging, discovery and outcomes | Local authoring method, not evidence of benefit |

Repository sources are pinned to the revision current when this record was
written; the recipe and client documentation are mutable pages. Recheck a source
before making a new version-specific claim. No popularity ranking, vendor
benchmark or process-compliance percentage is treated as proof of planning
quality. Long autonomous execution and multi-week planning are distinct: the
latter additionally needs real external owners, resources and date constraints.

## Rule decisions

| Decision / gap | Transfer and local procedure | Legitimate neighboring case | Observable case or check |
| --- | --- | --- | --- |
| Explicit plan versus automatic process overhead | Adapt proportional depth in `SKILL.md`; an explicit small plan is delivered, but an obvious authorized edit needs no separate ritual | A high-risk one-line change can need planning; a mechanical multi-file edit may not | `explicit-small-plan`, `obvious-edit`, `implementation-already-authorized` |
| Grounds for file/interface claims | Adapt Superpowers specificity in scope-and-readiness; distinguish observed files from proposals | Missing access allows a provisional bounded plan, not fabricated inspection | `bounded-form`, `missing-project` |
| Useful task boundaries and durable identity | Adapt Superpowers outcomes and historical Compound IDs in implementation-units; tie tasks to requirements and checks | A short plan needs no ID namespace; internal helper choices can remain local | `dependency-contract`, `dependency-cycle`; manual reorder review |
| False certainty about unknowns | Local synthesis in scope-and-readiness: inspect accessible facts, plan a bounded probe or name an external decision | The investigation can be ready while dependent implementation is not | `bounded-unknown`, `external-policy` |
| Code detail versus contract precision | Adapt interface detail; reject universal full-code and universal no-signature rules | A reproducer or exact schema can be necessary to remove consequential ambiguity | `dependency-contract`; manual interface review |
| Distant detail and integration risk | Adapt GSD phase/tracer mechanism in long-horizon; detail the next ready stage | A local repair needs no artificial end-to-end tracer; a true multi-week plan needs external constraints | `full-migration`, `calendar-uncertainty` |
| Pilot accidentally becomes project completion or expanded authority | Retain Assay migration semantics and use them in roadmap acceptance | A requested pilot is genuinely complete at its own acceptance boundary | `full-migration`, `pilot-only` |
| Coverage and acceptance | Adapt Spec Kit bidirectional coverage; separate behavior checks from business measures | Existing suitable tests can suffice; no mandatory new test count | `review-missing-acceptance`, `review-valid-control`, `business-measurement` |
| Stale plan after requirement change | Adapt OpenSpec mutable artifacts in review-and-replan; update affected units and invalidate affected evidence | Unapproved implementation drift is not a new requirement | `async-replan`, `unapproved-drift` |
| Safe continuation | Adapt ExecPlans and prior Planning with Files recovery ideas in continuation | A short atomic edit needs no durable state file; uncertain side effect needs inspection, not blind replay | `resume-effect`, `resume-wrong-plan` |
| Shared status ownership | Adapt single-owner reconciliation, not a new lock/database | Disjoint tasks may be worked in parallel under existing permissions | `shared-plan-owners` |
| Honest readiness | Separate implementation, verification and blocked evidence in all stages | Unavailable browser evidence need not invalidate already demonstrated unit behavior | `partial-verification` |
| Authority and read-only plan review | Retain existing audit authority; planning cannot grant implementation or delegates | Already authorized implementation needs no repeated ritual approval | `plan-audit`, `idea-discussion`, `implementation-already-authorized` |
| Client plan modes | Retain as the host workflow: a mode limits effects and sets the flow and output format; this method supplies plan criteria inside it and names no client | Under a decision-complete rule, complete the next ready stage; later roadmap stages keep outcomes and entry conditions | Not exercised; no corpus case |
| Rules owned by other skills | Link to the owner instead of restating: staged-adoption completion stays in code maintenance, review authority in independent audit | A consumer still names when to use this method and what stays with itself | Resolving consumer-link test; manual duplication review |
| Selective reading and evaluation isolation | Retain Assay conditional references and existing packet builder | Installing only one skill may leave optional criteria unavailable; no auto-install | Packet snapshot tests and resolving consumer-link tests |

## Rejected or deferred transfers

Reject mandatory 2-5 minute tasks, code-complete distant plans, a commit per small
step, fixed review counts, blanket bans on safe diagnostics, automatic subagents
and fixed three-file state. These are not necessary properties of a sound plan.
Keep exact public contracts and bounded probes when their decision requires them.

Defer a task database, new CLI, scheduler, model router, automated quality score and
large comparative campaigns. Existing task locations, native tools and the current
input-only packet utility have concrete consumers already. No new infrastructure
is justified by this prose capability.

## Mechanical integration and remaining uncertainty

The catalog entry and three consumer links establish an authored integration.
Independent compatibility expectations check the two native links; generated
inventory checks cover the three architecture languages and skill index.
Skill-specific packet and consumer-link checks live in
`tools/test_implementation_planning.py`, which the existing `tools/test_*.py`
suite discovers; refusal cases of the shared packet utility belong to
`test_validation.py`. No new gate is needed. Client manifests already select the
skills directory and do not need a version bump or a manual new skill list.

Semantic cases, code tests and a manual review are separate evidence. File moves
or smaller entry text do not establish context savings. All behavioral scenarios
remain authored until exercised in an authorized fresh client. See
[evaluation protocol](evaluation.md) for comparison, result retention and limits.
