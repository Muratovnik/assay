# README presentation details

Use only when the selected profile includes the corresponding material. These
are authoring checks, not an installer, badge crawler or publication pipeline.

## Evidence-backed badges

Use the actual repository, workflow filename/branch and package identifier from
the sources. A workflow file supports a status-badge target; it does not prove
that its last run passed. A version declaration alone does not prove a published
release or package. Keep licence identification separate from assumptions about
individual files. Never invent coverage, downloads or security-audit claims.

Prefer dynamic badges linked to their real targets when those targets are known.
Keep the chosen badge style uniform. Do not guess values for a static success
badge. External requests need the task's authorization; no request means no
claim that remote assets were fetched successfully. A timeout or blocked request
is a verification limit, not proof that the target is broken.

## Hero and images

Use supplied, permission-appropriate assets. Do not generate a new logo or edit
screenshots just to satisfy a template. Provide useful alternative text; do not
make the product name, setup requirement or critical warning available only as
pixels. Place a short caption or context near a demonstration when needed.

For a GitHub-centered header, keep blank lines around Markdown inside HTML:

````markdown
<div align="center">

# Project name

A concrete description of its job.

</div>
````

This is a syntax example, not a project tagline. Use the actual approved title
and description. For distribution sites or docs builders, verify their rendering
rather than assuming the same HTML and media support. Fall back to a plain
heading/image if the target requires it, and retain the rest of the selected
style. Resolve image paths against the document or publishing base actually used.

## Tables, diagrams and navigation

A table works for comparable fields; prose works for a short explanation. A
Mermaid diagram needs a real architecture or flow and a renderer that supports
it. Give the reader a textual route through the same decision when the diagram
is essential. Never fabricate components to make a diagram look complete.

Use the owner's selected table-of-contents policy. When heading text changes,
check affected anchors with the target renderer or existing project tooling.
Keep code samples and heading roles aligned; preserved bytes under the wrong
heading are still a documentation defect.

Community modules are explicit style choices. Contributor avatars, star-history
and social links need verified repository/account targets and permission-appropriate
assets. Private identifiers must not be sent to an external badge or chart
service without authorization. Repo growth is not a quality claim.

## Finished artifact

Inspect the intended output, not just the model's report. A `.md` file contains
its document directly, with no outer code fence and no "here is the README"
wrapper. If returning literal Markdown in chat, an outer fence must be longer
than all matching fences inside. Do not alter internal code to solve wrapping.

The existing preservation script cannot fully classify HTML. Do not suppress its
`unverified` result to claim coverage, and do not ban a requested header merely
to obtain a green result. Use an authorized render/source comparison for the
uncovered region and state that scope. Markdown structure, remote availability
and correctness of commands remain different checks.
