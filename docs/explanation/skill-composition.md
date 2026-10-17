# Skill composition and standalone boundaries

A skill owns criteria for a particular decision. Loading a linked method is not
a call to a workflow engine, delegation, an implementation assignment or a new
source of permissions. A link graph is not an execution graph.

## What a single-skill install contains

Skill-local resources are required. Sibling methods are optional collaborators
listed in the string-valued frontmatter metadata key `assay-optional-skills`.
This is an Assay validation convention inside the standard metadata map, not an
Agent Skills dependency field, client resolver or install command. The rule for
declaring a peer belongs to the [authoring contract](../../AGENTS.md#writing-a-skill).

A singleton retains the core task, authority and evidence boundary written in its
own instructions; it does not include the criteria its peers own. For the full
set of criteria, install the collection in one skill root.

## What the source checks establish

`tools/asset_formats.py` delegates YAML syntax to PyYAML and applies a local safe
loader. `tools/skill_resources.py` delegates CommonMark parsing to markdown-it-py.
Code fences are examples, not links; reference links and HTML href/src resources
are inspected. The checker copies the collection and each singleton to ordinary
temporary layouts, checks declared peer boundaries, requires local resources and
rejects broken peer targets when that peer is present. A link to a section must
match a heading anchor in the target, so a renamed heading fails rather than
leaving a dangling reference. Empty selections fail. Every file under a skill's
`references/` or `examples/` must be linked from that skill's `SKILL.md` itself,
and one over 100 lines opens with a `## Contents` list that links each of its
other second-level headings.

These checks do not run an installer, resolve all dynamic script/import paths,
validate URL contents, prove a client discovered the skill or establish useful
agent behavior. A reviewed optional declaration is not behavioral evidence.

## Links between skills

Anthropic's skill authoring guidance keeps references one level deep from
`SKILL.md`, because an agent may only preview a file it reached through another
reference. Assay follows that inside a skill: `SKILL.md` links every reference
the skill ships. Between skills it departs from the guidance on purpose. A
criterion has one owner, and another skill's reference links to that owner
instead of restating it, so the rule changes in one place. From the reader's
`SKILL.md` such a criterion is a second hop away and may be read only in part.
The contents list at the top of each long reference keeps its scope visible in
a partial read. Copying shared criteria into every skill would remove the hop,
but each rule would then have several copies to keep in step.

## Sources and transfer limits

- [Agent Skills specification](https://agentskills.io/specification): YAML frontmatter, string-valued metadata and skill-relative resources. It does not define automatic peer installation.
- [Claude skill authoring best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices): references one level deep from `SKILL.md`, a contents list in reference files over 100 lines, and frontmatter limits. Assay keeps the cross-skill exception above.
- [Vercel Skills CLI](https://github.com/vercel-labs/skills): selected-skill installation is distinct from the full collection. Assay's copied-layout checks do not certify a particular CLI version.
- [markdown-it-py token API](https://markdown-it-py.readthedocs.io/en/latest/using.html): reuse a maintained CommonMark parser rather than grow a regex parser or renderer.

These are mechanism comparisons and design rationale, not comparative results for
Assay.
