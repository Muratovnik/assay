# Skill composition and standalone boundaries

A skill owns criteria for a particular decision. Loading a linked method is not
a call to a workflow engine, delegation, an implementation assignment or a new
source of permissions. A link graph is not an execution graph.

## A small interface between methods

Describe a consequential handoff through its condition, inputs, returned result,
retained owner and unavailable-method behavior. These belong in the owning plan
or existing task context; they do not require a new registry or task database.

| Caller and condition | Input | Useful return | What stays with the caller |
| --- | --- | --- | --- |
| `code-change` needs a material boundary decision | Inspected consumers, constraints and intended behavior | `software-architecture` criteria and justified boundary choice | Implementation scope, caller updates and verification |
| `implementation-planning` needs an unresolved comparison | Decision, constraints and existing evidence | `evidence-research` comparison with uncertainty and sources | One plan and its readiness decision |
| `independent-audit` checks an architectural claim | Frozen subject, brief and claimed boundary | Applicable architecture criteria and evidence | Read-only authority, coverage and verdict |
| `ui-delivery` needs a staged rollout | Target users, source/target fidelity and deliverable | Ready implementation units and return conditions | Requested UI result, not a replacement artifact |
| `test-writing` changes a check | Independently justified behavior and relevant consumers | Applicable tool-scope criteria | Expectations, positive/negative controls and test design |
| `skill-evaluation` reviews a method revision | Actual input/candidate identity and failure | Discriminating comparison and limits | Evaluation integrity; no automatic implementation permission |

For example, fixing a known local defect can preserve an established boundary
without redesigning the application. Reading architecture criteria during audit
does not authorize moving files. Continuing an accepted plan does not restart its
research unless a material premise has changed. A requested implementation and PR
must still finish the authorized delivery; a plan is not a substitute for it.

## What a single-skill install promises

Skill-local resources are required. Sibling methods are optional collaborators
listed in the string-valued frontmatter metadata key `assay-optional-skills`.
This is an Assay validation convention inside the standard metadata map, not an
Agent Skills dependency field, client resolver or install command.

A singleton retains the core task, authority and evidence boundary written in its
own instructions. It does not promise all specialist criteria available in the
full collection. When an unavailable peer matters, continue supported core work
and name the missing criterion or unresolved conclusion. Never invent its rules,
automatically install it or label the incomplete composed workflow complete.
For the full set of available criteria, install the collection in one skill root.

A reference is optional because its absence has a defined bounded result, not
because declaring it optional makes a validator green. New indispensable detail
must live in the shipped skill or require a clearly documented larger delivery.
Keep one canonical owner for shared detail; retain necessary safety and outcome
constraints at each independently distributed entry point.

## What the source checks establish

`tools/asset_formats.py` delegates YAML syntax to PyYAML and applies a local safe
loader. `tools/skill_resources.py` delegates CommonMark parsing to markdown-it-py.
Code fences are examples, not links; reference links and HTML href/src resources
are inspected. The checker copies the collection and each singleton to ordinary
temporary layouts, checks declared peer boundaries, requires local resources and
rejects broken peer targets when that peer is present. Empty selections fail.

These checks do not run an installer, resolve all dynamic script/import paths,
validate URL contents, prove a client discovered the skill or establish useful
agent behavior. A reviewed optional declaration is not behavioral evidence.

## Naming and reuse

`code-change` covers new implementation, repairs and refactoring;
`ui-delivery` covers product UI beyond operations screens;
`skill-evaluation` diagnoses and compares skill behavior rather than ordinary
authoring. The other names retain their existing scope. `independent-audit` is
not a guarantee of independence: reviewing one's own implementation remains
self-review and must be reported as such. See [migration](../how-to/migrate-skill-names.md).

Reuse is supported by repeated decisions across materially different consumers,
not a count of incoming links. A one-consumer method may be experimental without
claiming proven generality. Do not shorten instructions or add a framework on
word count alone; inspect which criteria are actually loaded and useful.

## Sources and transfer limits

- [Agent Skills specification](https://agentskills.io/specification): YAML frontmatter, string-valued metadata and skill-relative resources. It does not define automatic peer installation.
- [Vercel Skills CLI](https://github.com/vercel-labs/skills): selected-skill installation is distinct from the full collection. Assay's copied-layout checks do not certify a particular CLI version.
- [markdown-it-py token API](https://markdown-it-py.readthedocs.io/en/latest/using.html): reuse a maintained CommonMark parser rather than grow a regex parser or renderer.
- [Superpowers writing-plans](https://github.com/obra/superpowers/blob/main/skills/writing-plans/SKILL.md): explicit inputs, outputs and execution handoff are useful; a fixed ceremony for every edit is not adopted.
- [OpenSpec](https://github.com/Fission-AI/OpenSpec): visible artifacts and transitions inform continuation, not a mandatory new document set.

These are mechanism comparisons and design rationale, not comparative results for
Assay. Existing lifecycle proposals remain separate; this change adds no second
orchestrator, model runner or task store.
