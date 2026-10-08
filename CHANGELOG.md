# Changelog

Generated from the commit history under the
[Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) Angular
preset. Sections and entry format follow
[`conventional-changelog-angular`](https://github.com/conventional-changelog/conventional-changelog/tree/master/packages/conventional-changelog-angular);
every entry links to the commit that introduced it.

## [0.17.2](https://github.com/Muratovnik/assay/compare/v0.17.1...v0.17.2) (2026-10-08)

### Bug Fixes

* **writing:** select claims and detail for the document's purpose, check delivered review reports for unnecessary repetition, and preserve the narrower scope of copyedits and preserve-all requests ([4812353](https://github.com/Muratovnik/assay/commit/4812353dda751a4818eebff2b50a154262961b83))

## [0.17.1](https://github.com/Muratovnik/assay/compare/v0.17.0...v0.17.1) (2026-10-07)

Delegation uses task-specific recommendations by default. A binding caller
choice now requires a declared justification or an actual user-confirmation
reference, including partial choices and choices with an omitted origin.

### Bug Fixes

* **routing:** reject unexplained caller overrides before retrieval, preserve justified exceptions and their provenance, retain history privacy and diagnostic replay, and keep user choices and dispatch constraints binding ([6e676b1](https://github.com/Muratovnik/assay/commit/6e676b14bb67c5114f933fb23c1e8115f6eb39bf))

## [0.17.0](https://github.com/Muratovnik/assay/compare/v0.16.1...v0.17.0) (2026-10-07)

Native routing now asks whether each model and effort pair can meet the concrete
assignment, then compares measured costs among adequate candidates. New configs
use this policy; existing configs retain their declared policy until explicitly
migrated with `migrate-config --native-decisions`.

### Features

* **routing:** use named task-adequacy questions and packet-local evidence, select adequate routes by comparable benchmark or supported paired task costs, separate unknown adequacy and cost from fallback, and include task criteria and privacy scope in cache identity ([2da38a0](https://github.com/Muratovnik/assay/commit/2da38a0cc22d0f12743729f6a63838ed45a4e4fb))

### Bug Fixes

* **routing:** remove the shared 24 KiB native input ceiling while keeping a separate result limit and complete candidate inventory ([14c656e](https://github.com/Muratovnik/assay/commit/14c656e19140758572a97bc895a2993177ef743d))
* **routing:** preserve explicit-choice provenance and distinguish selected routes from recorded fallback ([0a481a9](https://github.com/Muratovnik/assay/commit/0a481a97ea4b07278346631fde241310451f1acf))
* **routing:** compare benchmark quality and expense without anchoring the recommendation to the caller baseline ([671c860](https://github.com/Muratovnik/assay/commit/671c8607526cda2dc461d31d54cd0e45434cf441))
* **routing:** preserve packet assessment bindings when cached advice is reused ([a8f2542](https://github.com/Muratovnik/assay/commit/a8f2542e5b33c20dd3461d0faf8fda11e55edf39))
* **routing:** put readable quality and expense evidence alongside the complete native snapshot ([a1e4d2d](https://github.com/Muratovnik/assay/commit/a1e4d2d3ba6470fd30e4408533b9b7eb092b3117))
* **routing:** deliver large private Claude inputs through native tools and validate foreground replies ([c795675](https://github.com/Muratovnik/assay/commit/c79567504ff2f482d64fc89ac2c889131796aca6))
* **routing:** accept an omitted empty uncertainty list for known assessments while requiring grounds for unknown judgments ([6a6eafe](https://github.com/Muratovnik/assay/commit/6a6eafe2d9fc30e113fd665909cae4fa058cc680))

Cost comparisons stay within matching cohorts and cost units. Task inference,
unmeasured alternatives and conflicting evidence remain explicit uncertainties;
benchmark USD does not establish subscription quota savings or the cost of a new
assignment. Structural checks do not establish the accuracy of every adequacy
judgment.

## [0.16.1](https://github.com/Muratovnik/assay/compare/v0.16.0...v0.16.1) (2026-10-06)

Technical documentation now selects material for its reader and publication
surface before arranging it, and the finished draft is reviewed for passages
that add nothing this reader needs. Three foundational research studies are
published in English and Russian.

### Bug Fixes

* **technical-writing:** select, condense, move or remove material for the reader, task, publication surface and authorized scope before choosing headings; make README demonstration, installation and first-use blocks conditional, so a catalog-managed install or automatic operation gets no ritual section; review the finished draft for re-explained familiar terms, claims repeated across prose, headings and table cells, process provenance and purposeless modifiers, while keeping necessary conditions, newcomer explanations, acceptance evidence and required notices; reconcile related current claims after a behavior change; keep the preservation checker's strict exit codes and report an authorized deletion instead of hiding it; add 13 public regression cases and two discovery inputs ([d5766ab](https://github.com/Muratovnik/assay/commit/d5766ab2670dc1fd98127cab8bd2764d6196be0f))

### Documentation

* **research:** publish the research-quality, software-engineering and LLM reasoning and behavior control studies in English and Russian, with paired indexes ([46740f2](https://github.com/Muratovnik/assay/commit/46740f2eb8d0db046eec2842f8b20a0354837ee6))

The technical-writing change was exercised on a small set of synthetic tasks
with one model configuration, and those tasks are now public. Automatic
discovery, other models and broader prose quality have not been established.

## [0.16.0](https://github.com/Muratovnik/assay/compare/v0.15.0...v0.16.0) (2026-10-06)

Code changes now establish the capability a guarantee needs and consider
existing implementations before writing their own, entered by concrete kinds of
behavior rather than a judgment of materiality. Corrections and acceptable
examples can be kept as explicit local records for later review, and the Claude
evidence reviewer promises only the boundary the client keeps.

### ⚠ BREAKING CHANGES

* **profiles:** the Claude `evidence-reviewer` is a bounded reader with `Read`, `Grep` and `Glob`; it no longer reruns the oracle or loads skills, so callers include snapshot-bound receipts for the named oracle and pass audit criteria by path, and a packet without receipts is refused; the Codex projection keeps the oracle ([18fd6c6](https://github.com/Muratovnik/assay/commit/18fd6c6b023a0c53656bb96cffbdc83db2442b3b))

### Features

* **code-change:** establish which capability provides an unchecked guarantee before choosing the implementation; enter the reuse reference before writing or keeping own code for behavior that commonly has an existing implementation, such as parsing, validation, retries, caching, dates, hashing, CLI arguments, HTTP clients, pathfinding or asset loading; name a semantic mismatch as the gap instead of skipping the check; report the decision in a `Reuse:` line and an unrequested missing capability in an optional proposal line ([18fd6c6](https://github.com/Muratovnik/assay/commit/18fd6c6b023a0c53656bb96cffbdc83db2442b3b))
* **implementation-planning:** list the conditions a project should supply, separating observable facts from owner decisions, and the costly decision categories that need the contract check, each with a nearby control ([18fd6c6](https://github.com/Muratovnik/assay/commit/18fd6c6b023a0c53656bb96cffbdc83db2442b3b))
* **evidence-research:** borrow code, behavior or assets from another project through one procedure for provenance, terms, compatibility and the permitted operation; mark sources recalled from memory as not opened, name independence axes, compare on a discriminating basis without a query quota and stop in four stated situations ([18fd6c6](https://github.com/Muratovnik/assay/commit/18fd6c6b023a0c53656bb96cffbdc83db2442b3b))
* **hooks:** record corrections and allowed examples with an explicit command, keep the storage mode separate from the optional correction-grammar trigger, review metadata records with codes and a basis reference instead of text, and print the record command in `doctor`; recognize Russian lookups for an existing implementation ([18fd6c6](https://github.com/Muratovnik/assay/commit/18fd6c6b023a0c53656bb96cffbdc83db2442b3b))

### Bug Fixes

* **route-subagents:** keep the session reminder to three sentences while preserving the subagent planning step for any wording of the request; add the routing checklist at session start only when routing is configured, and tell packet builders what a reviewer without the oracle needs ([18fd6c6](https://github.com/Muratovnik/assay/commit/18fd6c6b023a0c53656bb96cffbdc83db2442b3b))
* **tools:** check heading anchors in links between skill files ([18fd6c6](https://github.com/Muratovnik/assay/commit/18fd6c6b023a0c53656bb96cffbdc83db2442b3b))

### Documentation

* **how-to:** describe project conditions for agents, client settings that guard tests and check configuration, feedback records with their privacy limits, and what each install route lacks ([18fd6c6](https://github.com/Muratovnik/assay/commit/18fd6c6b023a0c53656bb96cffbdc83db2442b3b))

The added evaluation cases are public synthetic examples, and no model run was
performed for this release. Better decisions, task outcomes or lower cost have
not been established.

## [0.15.0](https://github.com/Muratovnik/assay/compare/v0.14.0...v0.15.0) (2026-10-04)

Task continuation now recovers the selected work, current constraints and
applicable verification. Repairs trace connected preparation stages to the
consumer outcome, and command receipts can compare named inputs with a retained
successful run.

### Features

* **workflow:** load relevant methods before decisions, preserve live hints for plain continuation requests, carry unresolved outcomes and applicable evidence between stages, compare exact command receipts with explicit acceptance limits, and evaluate delivered artifacts with five executable scenarios and valid controls ([26f00fd](https://github.com/Muratovnik/assay/commit/26f00fd414c9a16194cc8b554bb05f474c277b11))

### Bug Fixes

* **tests:** publish complete readiness markers separately for each acquisition worker and verify that cancellation stops every detected process, releases the source lock and preserves cache failure semantics ([26f00fd](https://github.com/Muratovnik/assay/commit/26f00fd414c9a16194cc8b554bb05f474c277b11))

Both collections delivered all five public synthetic exercises in a bounded
comparison. General improvements in task success and execution cost remain
unestablished.

## [0.14.0](https://github.com/Muratovnik/assay/compare/v0.13.0...v0.14.0) (2026-10-04)

Code changes now choose evidence of correctness before deciding to add tests.
Existing coverage can be reused when sufficient, while explicit testing requests,
required project checks and real consumer boundaries retain their protection.

### Features

* **code-change:** choose verification before adding tests, distinguish diagnostic checks from regression protection, refresh results when relevant inputs change, and reconcile completion with the original consumer outcome; planning links to this decision and test-writing retains independent expectations ([8531707](https://github.com/Muratovnik/assay/commit/853170764f9515aaa288679290a7fbc183de8e0d))

The additional evaluation cases are public synthetic examples. Improved task
outcomes and lower execution cost have not been established by a paired comparison.

## [0.13.0](https://github.com/Muratovnik/assay/compare/v0.12.1...v0.13.0) (2026-10-04)

UI delivery now researches suitable references before custom implementation,
starting with the existing design system and the concrete gap. Runtime changes
connect generated-code compilation, actual build inputs and identity lifetime to
evidence from the reached execution stage. Codex SessionEnd hooks use the client's
three-second timeout limit.

### Features

* **ui:** research visual direction, component patterns or product behavior before a material custom implementation; use Refero Styles and The Component Gallery as optional reference catalogs, record the mechanism, fit, limits and adoption decision, and reuse sufficient existing evidence for local repairs ([795482b](https://github.com/Muratovnik/assay/commit/795482b9fd0698f04e41d2a40afe03c5ca829d6a))

### Bug Fixes

* **skills:** validate final generated code with the operation's compiler and references, account for actual runtime inputs and scoped drift, test identity guarantees over the consumer's required lifetime, and distinguish enabled functions, reached stages and helper success from completed operations; add 12 decision scenarios without claiming measured task effectiveness ([8200322](https://github.com/Muratovnik/assay/commit/820032212f18e86d8cbcba1c508b100611c6cfcd))
* **hooks:** set Codex SessionEnd to three seconds so loading the plugin no longer requires the client to clamp its timeout; preserve other hook limits ([cfdccc1](https://github.com/Muratovnik/assay/commit/cfdccc1541b967c52b02bb324599961c7f548732))

### Documentation

* **ui-delivery:** refresh Figwright 0.6.0 guidance for end-to-end connection checks, process-scoped file claims, actual resize results and variant property ownership; pin source references and retain older-adapter recovery paths conditionally ([427e345](https://github.com/Muratovnik/assay/commit/427e345a5c9a0d1cec6290e70be20884f5eff2c5))

## [0.12.1](https://github.com/Muratovnik/assay/compare/v0.12.0...v0.12.1) (2026-10-02)

Planning and delegation now connect risky dependencies to evidence from their
real consumers. Resource recovery distinguishes partial acquisition, cancellation
and an uncertain result after a lost reply. Routing receipts report invalid input
instead of silently dropping it.

### Bug Fixes

* **workflows:** verify material prerequisites before dependent work, test real producer output at its consumer and check the supported delivery path; preserve resource ownership through failures, distinguish a product defect from a wrong oracle or broken fixture, and retain current evidence in handoffs; add 13 public regression and control scenarios for evaluating these decisions ([f39fc01](https://github.com/Muratovnik/assay/commit/f39fc0170a4a34b0e90151c66a0bc876b4fe2bed))
* **hooks:** honour an explicit English or Russian plan-only modifier in the first request paragraph, including restored session hints, while preserving explicit skill choices and ignoring quoted examples ([f39fc01](https://github.com/Muratovnik/assay/commit/f39fc0170a4a34b0e90151c66a0bc876b4fe2bed))
* **route-subagents:** expose typed receipt input and output schemas, reject unknown fields and malformed or excessive evidence references with actionable errors, preserve supported legacy aliases and nullable observations, and keep CLI help usable without the optional MCP SDK ([f39fc01](https://github.com/Muratovnik/assay/commit/f39fc0170a4a34b0e90151c66a0bc876b4fe2bed))

## [0.12.0](https://github.com/Muratovnik/assay/compare/v0.11.0...v0.12.0) (2026-10-01)

Subagent routing now starts by identifying useful, bounded work before substantial
solo work begins. Delegation hints preserve the requested primary workflow when
the optional routing skill is unavailable or disabled.

### Features

* **route-subagents:** plan useful delegation around a concrete outcome, its consumer, launch timing and full cost; defer a packet only with a specific trigger, and check and use its return before integrating it; session reminders introduce this planning step early, with bounded English and Russian hints for direct delegation requests ([96096c1](https://github.com/Muratovnik/assay/commit/96096c16e35d93788352e9f6db869058c0b47d89))

### Bug Fixes

* **hooks:** preserve implementation, review or research as the primary workflow when the delegation hint is disabled, missing or explicitly negated; recognise file paths, dotted identifiers and URLs inside delegation arguments without crossing sentence boundaries, and invalidate saved intent when the delegation grammar changes ([96096c1](https://github.com/Muratovnik/assay/commit/96096c16e35d93788352e9f6db869058c0b47d89))

## [0.11.0](https://github.com/Muratovnik/assay/compare/v0.10.0...v0.11.0) (2026-09-30)

Assay now gives bounded skill hints for the current prompt and client, and
preserves required routing decisions when optional hints are unavailable.
UI delivery and comment cleanup retain the evidence needed to verify a change.
Existing evidence-only routing configurations keep their behavior.

### ⚠ BREAKING CHANGES

* **route-subagents:** private advisor launches in Claude required mode now need `CLAUDE_CODE_DISABLE_BACKGROUND_TASKS=1` in the environment that starts Claude; without it the guard refuses the launch, because background completion notifications can expose the private advisor result; this native switch disables all background tasks for that Claude session, including worker and Bash tasks; Assay does not change client settings automatically ([9ef9a84](https://github.com/Muratovnik/assay/commit/9ef9a84f0036b571724cb7560dcaf8e683c64c15))

### Features

* **hooks:** add client-specific manifests, prompt hints, bounded optional session state, diagnostics and read-only routing preflight; reintroduce skill reminders after resume and compaction, omit quoted examples and code from prompt matching, and keep basic reminders and required routing guards available without the optional parser ([9ef9a84](https://github.com/Muratovnik/assay/commit/9ef9a84f0036b571724cb7560dcaf8e683c64c15))
* **skills:** preserve UI evidence through implementation and handoff, and keep unresolved feedback and essential evidence when cleaning up comments ([2394b5a](https://github.com/Muratovnik/assay/commit/2394b5a05afaf33f07920929a374d2dd29faa237))

### Bug Fixes

* **route-subagents:** replace private Claude advisor returns with schema-valid neutral results, preflight every selectable advisor route against its generated definition, and refuse protected launches on unsupported required-mode adapters ([9ef9a84](https://github.com/Muratovnik/assay/commit/9ef9a84f0036b571724cb7560dcaf8e683c64c15))

## [0.10.0](https://github.com/Muratovnik/assay/compare/v0.9.0...v0.10.0) (2026-09-29)

Required routing now passes the routed model in the Agent call and generates
definitions only for effort, which the call cannot carry. A rolling alias is
resolved by the host rather than guessed, a configured baseline answers when the
advisor cannot, and every route is checked before the first launch.
Evidence-only configurations keep their behavior.

### ⚠ BREAKING CHANGES

* **route-subagents:** required mode needs a `baseline`, and without one launches outside `unrouted_agents` are refused; agent types in `unrouted_agents` no longer inherit the parent's model but launch with the baseline model unless the configuration gives them a model or `"inherit"`, and a different model from the caller must be routed; generated definitions no longer stop a worker whose observed effort differs from its route, the mismatch blocks continuation once it stops; run `tools/assay.py claude-routes` again after upgrading, then `claude-routes --prune` to remove the definitions of 0.9.0 ([e4521bb](https://github.com/Muratovnik/assay/commit/e4521bb985eb615c4308d8f3ec247b5c4a21204b))

### Features

* **route-subagents:** route a profile listed in `pipeline.profiles` with the model alias in the Agent call and one generated definition per profile and effort, keeping model-pinned variants for full model IDs, which the call does not accept; record what the host resolves each alias to, so a changed resolution becomes an inventory event that suspends the alias's confirmed evidence names until `inventory-confirm` runs again; select the baseline as a fallback when the advisor abstains, gives invalid advice, ends without a result or is disabled; report which cached benchmark sources name each inventory model with up to five candidate spellings, and confirm one with `inventory-confirm --evidence-name`; check every selectable route, the baseline per profile and the model of each exempt type in `doctor` and `routing_status`; keep the launch reminder silent on Claude launches in required mode, and delete the generation lock with `claude-routes --remove` ([e4521bb](https://github.com/Muratovnik/assay/commit/e4521bb985eb615c4308d8f3ec247b5c4a21204b))

## [0.9.0](https://github.com/Muratovnik/assay/compare/v0.8.0...v0.9.0) (2026-09-29)

Skill evaluation adds evaluation design and bounded iterative improvement, and
route-subagents adds an opt-in required routing mode for Claude Code. Every
existing routing configuration keeps its behavior unless it selects that mode.

### Features

* **route-subagents:** add an opt-in required routing mode for Claude Code in which a separately launched advisor fetches its private input and submits its own answer, workers run through immutable model/effort definitions generated by `tools/assay.py claude-routes`, and the plugin hook admits only registered launches; user choices, owner-listed native agents and existing agent definitions stay usable, the inventory is renewed without a reconnect, and `claude-routes --remove` uninstalls the definitions; without `pipeline.mode: "required"` the hooks return no decision and the evidence-only workflow is unchanged ([54edf80](https://github.com/Muratovnik/assay/commit/54edf80f13a7bd5bfdd76aeae43c05a344cec079))
* **skill-evaluation:** design an evaluation with a covered task population, calibrated evaluators, blinded and order-varied comparisons and separate working, selection and final evidence, and improve a skill in bounded steps against a fixed baseline, objective, budget and stopping rule; optional case metadata is validated and the repository accepts only public metadata ([f00e1e9](https://github.com/Muratovnik/assay/commit/f00e1e93fc8f7a23f89c6d7b9d99e569ec44fb2d))

## [0.8.0](https://github.com/Muratovnik/assay/compare/v0.7.0...v0.8.0) (2026-09-26)

Two new methods: product flow mapping, which reconstructs an existing product's
journeys from evidence for a redesign or test handoff, and research-driven change,
which carries an evidence-backed change through planning, implementation, review
and delivery. Three skills are renamed to match their scope, and the source checks
now parse metadata and links with maintained parsers and check every skill as a
standalone copy.

### ⚠ BREAKING CHANGES

* `code-maintenance` is now `code-change`, `operations-ui-delivery` is now `ui-delivery` and `skill-design` is now `skill-evaluation`, together with their catalog IDs, native link targets and adapters; no old-name aliases are shipped, so remove existing links with the previous revision before installing this one ([7716739](https://github.com/Muratovnik/assay/commit/7716739440ffa2eed65012a2ceb5069a7467a034))

### Features

* **product-flow-mapping:** reconstruct an existing product's journeys and trace its screens, states and controls to evidence, keeping observed, adopted and proposed behavior apart, with a bidirectional inventory and paired description and screenshot frames for a designer; UI acceptance and design transfer route journey reconstruction to it, and test writing consumes the same scenarios ([630e59c](https://github.com/Muratovnik/assay/commit/630e59ca2164a468df851a52318150d33827a947))
* **research-driven-change:** carry a change from need through evidence, decision, plan unit, implementation, verification and the requested delivery, entering at existing research, a plan, a changed artifact or review feedback without restarting sufficient prior work; research, planning, code change, skill evaluation and audit link back to it and keep their own authority ([5b76f5c](https://github.com/Muratovnik/assay/commit/5b76f5c5f12f5ad0116af940308fb83a5862e87b))

### Bug Fixes

* parse skill frontmatter and adapter YAML with one local safe loader and check name, description, compatibility, allowed-tools and metadata against the Agent Skills specification; parse links with markdown-it-py, including reference links and HTML resources, and check the full collection and every single skill in copied layouts with declared optional peers; `uninstall-links` no longer depends on unrelated publication checks but still refuses linked sources, foreign targets and modified adapters ([7716739](https://github.com/Muratovnik/assay/commit/7716739440ffa2eed65012a2ceb5069a7467a034))

## [0.7.0](https://github.com/Muratovnik/assay/compare/v0.6.0...v0.7.0) (2026-09-26)

Two new methods: implementation planning for a bounded change or a staged
roadmap, and software architecture for boundaries, contracts and code placement.
Skills now link to the method that owns a rule instead of restating it, so each
criterion has one owner.

### Features

* **implementation-planning:** plan a bounded change or a staged roadmap from the actual project, with outcome-sized units, real dependencies, observable acceptance and the readiness of the next stage, then replan affected work and continue safely after an interruption; code maintenance, UI delivery and independent audit link to it, and independent audit also reviews plans ([74a203c](https://github.com/Muratovnik/assay/commit/74a203c6f33f29c48fd5b58b1fe022ffed0a5dd5))
* **software-architecture:** reconstruct a system's current architecture, design boundaries, place and share code, assess a proposal or an implementation and apply an adopted FSD profile; code maintenance, implementation planning and independent audit link to it for boundary, contract and placement decisions ([07eecca](https://github.com/Muratovnik/assay/commit/07eecca30e936e3540aa34c0057ddc6b917418b4))

### Bug Fixes

* **skills:** give each contract and reuse criterion one owner: planning keeps contract-change authority and recovery from recurring complaints, effective quality checks keep exception and end-state probes, reuse and migration keep delegation, exception approval and the terminal-state policy; a facade now expresses visual tokens through the library's theme where one exists ([06d9236](https://github.com/Muratovnik/assay/commit/06d92362e771277b62f1e0a9f03979ec0babd06a))

## [0.6.0](https://github.com/Muratovnik/assay/compare/v0.5.0...v0.6.0) (2026-09-23)

Subagent routing now scopes vendor guidance to the exact models a host has and
brings benchmark evidence up to date when that inventory changes. The UI skill
gains a procedure for organizing a design-system library for its consumers and
a clearer account of what a complete transfer requires.

### Features

* **operations-ui-delivery:** organize a design-system library for its consumers, cover broad transfer completeness and capture readiness, add Figma library mechanics through the Figwright adapter, and resume interrupted multi-step work from the current artifact ([f005a6c](https://github.com/Muratovnik/assay/commit/f005a6cd2f036b8b5f8d0de8cdd60b9206fe10ac))
* **route-subagents:** scope GPT-6 and Opus 5.5 guidance to the models and surfaces it documents, match reviewed CursorBench model names, give a newly confirmed inventory one bounded early benchmark check with per-model matching diagnostics, and read Terminal-Bench 4.0 from the publisher's public JSON API before the opt-in browser route ([519cf94](https://github.com/Muratovnik/assay/commit/519cf94698ccc9bc6af625df8cfb18713e4f8d9f))

### Bug Fixes

* **route-subagents:** check a new inventory only against sources the host can fetch, so a browser-only source with the browser disabled keeps its fresh snapshot instead of recording a failure and backing off ([066cf4f](https://github.com/Muratovnik/assay/commit/066cf4f6a96f7802c91eb0bdd9dd5a4199391a30))
* **route-subagents:** report fresh data during a backoff as cached, and evict the oldest inventory checks first when the history is full ([f56e4a4](https://github.com/Muratovnik/assay/commit/f56e4a41ac776c8d31daf5e47f2374fa864eb290))
* **route-subagents:** let an enabled browser read Terminal-Bench when the API refuses an anonymous read; rate limits and other client errors still never substitute for it ([f5de75b](https://github.com/Muratovnik/assay/commit/f5de75b637ee05b36896c2d94125132ed94bd0bc))

Guidance scope and model-name matching are registry contracts checked against
fixtures, not live retrievals or model evaluations; confirm the Terminal-Bench
API with the online smoke in the installed environment before relying on it. The
new UI decision cases are specifications, and no behavioral run is claimed.
Reconnect the MCP server after updating its code.

## [0.5.0](https://github.com/Muratovnik/assay/compare/v0.4.0...v0.5.0) (2026-09-21)

The operational UI skill now covers the whole life of a UI artifact: designing a
new screen, implementing a reference in code, transferring an existing interface
into an editable design, editing a component library, and reviewing any of them.

### Features

* **operations-ui-delivery:** cover every layout mode from one entrypoint and add conditional procedures for the component system, design transfer and the Figwright adapter ([856bbc1](https://github.com/Muratovnik/assay/commit/856bbc1a8af3b22f5843b60575edc74c5f766ee6))

Each mode names what establishes quality and which check distinguishes it. The
new procedures own what the existing ones did not: shared bases, transitive
reuse and property effects that must be observable; the duties that only a
transfer carries, from fixing the source to migrating without breaking
relations; and the adapter rules for reading documentation before choosing a
method, checking every result and recovering from a partial write. Existing
owners gained the source of truth for each decision, theme and token resolution
through the composition, geometry depth, asset provenance and capture readiness.

These are instructions, not a runner: nothing here installs a tool or measures
behavior. The library-organization commands are named from the adapter source
at a pinned revision ([baa643f](https://github.com/Muratovnik/assay/commit/baa643f56e550788d44080035c3cd58f2e8985cf)),
so a client should still be asked which tools it exposes.

## [0.4.0](https://github.com/Muratovnik/assay/compare/v0.3.0...v0.4.0) (2026-09-20)

### Features

* **routing:** ship plugin reminders for applicable skills at session start and after context compaction, and reinforce required routing before subagent launches ([e248ab8](https://github.com/Muratovnik/assay/commit/e248ab842fa200b93107b13ec4855bd7f2f0e716))

Reminders are included in the full Codex and Claude Code plugin. They require
Python 3.11+ available as `python`; Codex also requires native hook trust.
Skills-only installations do not connect plugin hooks. These bounded reminders
make no model or network calls and do not enforce or authorize delegation.

## [0.3.0](https://github.com/Muratovnik/assay/compare/v0.2.0...v0.3.0) (2026-09-20)

Subagent routing gains optional advice, historical task evidence and estimates of
the cost of a complete work chain. Recommendations remain advisory: the caller
chooses and launches workers using its current model inventory.

### Features

* **routing:** request bounded advice through a caller-selected native economy model or the optional Jev adapter, with policy checks and local decision history; external advice requires separate consent ([b8bd160](https://github.com/Muratovnik/assay/commit/b8bd160a87480a2b452b3c66ba02948efe977cca))
* **routing:** retrieve similar measured tasks and estimate complete-chain costs, including retries, verification and coordination; API prices, tokens and subscription quota remain separate, and missing measurements stay unknown ([04e58f9](https://github.com/Muratovnik/assay/commit/04e58f9929a59ab29e7b618f2475d5fb58b29a9c))
* **routing:** automatically prepare a missing public task corpus when task evidence is enabled, or prefetch it with `task-setup`; pinned source checksums, cache reuse, offline mode and download status cover the first-use workflow ([9926ea1](https://github.com/Muratovnik/assay/commit/9926ea16bf27e0ea443748fd12a4766bd60a4d85))

### Bug Fixes

* **routing:** retain historical results and costs when the source models are absent from the current inventory, without transferring their scores to newer models or letting empty candidate estimates crowd out evidence ([54c3fba](https://github.com/Muratovnik/assay/commit/54c3fba539a3545ae1e56216ad6bc994c20f16e4))

Task evidence is opt-in through `task_evidence.enabled` in a v2 routing
configuration. The initial corpus covers 528 LiveCodeBench tasks and 13 historical
models; it is coding-task context, not measured subscription savings or coverage
of every workflow. Reconnect the MCP server after updating its code or configuration.

## [0.2.0](https://github.com/Muratovnik/assay/compare/v0.1.0...v0.2.0) (2026-09-19)

Two writing methods join the library, and the documentation set now exists in
English, Russian and Simplified Chinese: the README, the install guide, the
architecture and evaluation notes, the upgrade how-to, the discovery
explanation, the contributing guide and the security policy.

### Features

* **technical-writing:** a method for product documentation — README, how-to, tutorial, reference, explanation, runbook, ADR/RFC and release notes — written from its sources rather than from memory ([bd05e0f](https://github.com/Muratovnik/assay/commit/bd05e0fd4e5a83f50ae4f0f1c78c063d802213d7))
* **technical-writing:** a read-only preservation check that compares the protected regions of an edited document and reports what it could not classify instead of passing it ([a7cc3aa](https://github.com/Muratovnik/assay/commit/a7cc3aae6e19a1a1b34784ed4e35165081eba028))
* **technical-writing:** a README module with a selectable house style and two skeletons, public product and internal document ([95d39b6](https://github.com/Muratovnik/assay/commit/95d39b68cbfeb82b3e2b266bc8af8867850be787))
* **technical-writing:** the bundled README profile adopted as a project standard, scoped to the owner's public repositories and stated as such ([25293df](https://github.com/Muratovnik/assay/commit/25293dfbddb038c72b2f2844b8e029ea9f43cd5a))
* **text-writing:** an editorial method for ordinary prose — messages, letters, articles, portfolio and product copy — with separate profiles for Russian, English and Simplified Chinese ([f73fc02](https://github.com/Muratovnik/assay/commit/f73fc0221ac584b57e53e304b0ac4d536e4444c0))
* **text-skills:** a composition method shared by both writing skills ([59d0bbc](https://github.com/Muratovnik/assay/commit/59d0bbc46d7c4c68c08da208228ba1512166cf38))
* **text-skills:** the C1 method revision, with byte-exact fixtures admitted to the preservation suite ([e0d078e](https://github.com/Muratovnik/assay/commit/e0d078ec6042744d7a0fc4802f06ed139caa12ce))
* **tools:** the generated catalog block is now verified in every document that carries it, so a translated architecture page cannot drift from the catalog ([c101950](https://github.com/Muratovnik/assay/commit/c10195056563f806581eed611e91e3e8a72fcde2))

### Bug Fixes

* **technical-writing:** an unread link and an empty document are no longer reported as preserved ([d9430fc](https://github.com/Muratovnik/assay/commit/d9430fca5966c28899adf13fae41478ffe5f8bd6))
* **technical-writing:** the preservation check emits UTF-8, and a refuted region now outranks a merely unverified one in the exit code ([17adb58](https://github.com/Muratovnik/assay/commit/17adb5817e96bf12f4c8ac3f038a2a62ce2e61d7))
* **text-writing:** the protocol, the author profile and the Chinese control are exact ([1e6fb49](https://github.com/Muratovnik/assay/commit/1e6fb49d9ddc9e3577bbac7b93718e5c9642960f))
* **ci:** the exposure probe looks inside the ignored directories instead of naming them, which a fresh clone does not have ([15b0851](https://github.com/Muratovnik/assay/commit/15b085134caa0926dfcdbf846b7b55e9f33fe04d))
* **tests:** a reaped process entry is treated as a finished process ([8b93609](https://github.com/Muratovnik/assay/commit/8b936096c96ddda6419e6d97318f7c3a62f5d6a5))

## [0.1.0](https://github.com/Muratovnik/assay/releases/tag/v0.1.0) (2026-09-15)

First public release. The library existed privately before this, and those
revisions are not listed: their numbering and evidence belonged to a workspace
this repository no longer describes.

### Features

* eight skills with their references and evaluation data: `code-maintenance`, `test-writing`, `test-audit`, `independent-audit`, `evidence-research`, `operations-ui-delivery`, `route-subagents` and `skill-design` ([11c4c93](https://github.com/Muratovnik/assay/commit/11c4c930005b754217db9f23c0bbfe0d4f22f695))
* **profiles:** two agent profiles as capability boundaries rather than personas, `evidence-reviewer` and `official-docs-researcher`, neither pinning a model ([11c4c93](https://github.com/Muratovnik/assay/commit/11c4c930005b754217db9f23c0bbfe0d4f22f695))
* **install:** a guarded link lifecycle where `plan` reports every target and rollback target without writing, `install-links` preflights the whole vector before the first write, and `uninstall-links` removes only exact links or adapter bytes ([11c4c93](https://github.com/Muratovnik/assay/commit/11c4c930005b754217db9f23c0bbfe0d4f22f695))
* **render:** client manifests, profile adapters and the skills index generated from `catalog.toml` and `VERSION`, verified byte-for-byte by the source check ([11c4c93](https://github.com/Muratovnik/assay/commit/11c4c930005b754217db9f23c0bbfe0d4f22f695))
* **route-subagents:** optional benchmark-evidence routing for model and effort selection, as a local MCP server the user registers themselves ([11c4c93](https://github.com/Muratovnik/assay/commit/11c4c930005b754217db9f23c0bbfe0d4f22f695))
* **tools:** evidence utilities for repeatable checks: frozen input-only evaluation packets, command receipts, native loader inspection and scoped quality-tool probes, each executing only after an explicit `--execute` ([11c4c93](https://github.com/Muratovnik/assay/commit/11c4c930005b754217db9f23c0bbfe0d4f22f695))
* **ci:** seven source gates on Linux and Windows, a publication audit and an owner-side pre-push guard ([11c4c93](https://github.com/Muratovnik/assay/commit/11c4c930005b754217db9f23c0bbfe0d4f22f695))
