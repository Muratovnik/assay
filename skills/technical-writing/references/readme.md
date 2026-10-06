# README module

Use for creating a README, a full rewrite, or applying an agreed README style.
For a local correction, consult only the affected part and keep the existing
layout. This module is an entry within `technical-writing`; it creates no new
agent, slash command, catalog entry or mandatory delegation.

## Establish what the reader is getting

Identify audience, product, version scope and render target from the task and
project sources. A public package, a hosted app, an internal tool and a folder's
maintainer notes need different first steps. A monorepo is a layout, not an
installation method. Read relevant manifests, entry points/help, existing docs,
release evidence, licence, workflows and available visual assets. Do not scan the
whole repository when the needed facts are already bounded.

Choose an available user route, not the route easiest to infer from a manifest.
A declared console entry point does not disprove another invocation. A manifest
alone does not establish registry publication. State the actual prerequisites,
working directory, files or access before the first action. Do not make a reader
inherit conditions known only to the editor's environment.

## Select a presentation contract

Read [the README profile](readme-profile.md) for a new README or a full layout
change. Use an explicitly supplied house style first. Otherwise retain an
established project standard. For a new page without one, the bundled profile
applies within the scope its own adoption note states, and is a working draft
outside it. Draft with it rather than blocking on cosmetic questions; a project
outside that scope needs its own approval before the preset becomes its
standard. Keep the approval note out of the README.

After a profile is chosen, its applicable requirements are requirements: do not
remove an agreed hero, badge row or section order just because minimalism is
preferred by the model. Decide content eligibility using
[document design](document-design.md#select-content-before-arranging-it) and the
conditions below; a visual style does not require an unnecessary section.
Equally, formatting never authorizes a false claim, a
fabricated asset or an unsafe instruction. Report conflicts or missing required
material to the author rather than silently changing the standard.

Choose one skeleton:

- [Public product](../assets/readme-public.template.md) for a public tool,
  package, application or reusable library.
- [Internal or maintainer document](../assets/readme-internal.template.md) for
  team setup, an internal tool or a repository/folder intended for maintainers.

The templates contain authoring slots, not finished prose. Populate applicable
parts, remove instructions and unused slots, and translate headings consistently.
No unfilled template marker belongs in the delivered page. Explicitly explained
user parameters such as a token variable remain legitimate.

## Compose the page

Start with the job the product helps the reader do and a distinguishing supported
constraint or mechanism. Do not lead with the repository inventory or an inflated
claim. Give concrete uses instead of several restatements of the tagline.
When an established term already conveys a property to this audience, do not
repeat its definition as another capability; explain only an unfamiliar meaning
or a consequential exception.

Add a demonstration when it explains a non-obvious behavior, comparison or
choice. Use a relevant existing screenshot, working demo link or supported
example. A missing screenshot does not require a text example; an obvious
before/after pair may add nothing to the purpose already stated. If one example
also teaches first use, keep it once. Never invent an asset or execution receipt.

Include installation or access instructions when this audience needs information
beyond the route the publication surface already supplies: prerequisites, a
choice of package or environment, permissions, or an unusual step. A catalog
page whose manager handles installation may need only product-specific conditions;
a repository page may still need the actual download or access link. Confirm what
the reader can already see rather than assuming every catalog handles setup.

Include first-use steps when an action after installation is needed to obtain a
result. Automatic operation with no setup needs no ritual `Quick start` section.
When a procedure is needed, provide its starting state, ordered actions and
observable result, with explained placeholders and real platform differences.
Label illustrative output as an example. A documented supported command needs
no repetitive personal disclaimer, but do not assert a test that did not happen.

Keep product information, reference detail and contributor tasks distinct. Link
actual existing documents instead of manufacturing a docs tree. Important limits
belong before the decision or action they affect, even if the standard footer
also collects less urgent limits. Planned work can be omitted from current
Features or clearly separated; never present it as available.
Keep release deltas and author verification notes in their appropriate record
unless they change the reader's decision here. Use existing changelog navigation
when useful; do not add a rolling `What changed` summary by default. After a
behavior change, reconcile the related current claims instead of layering a new
exception onto stale prose.

## Presentation and completion

Use [presentation details](readme-presentation.md) when adding badges, images,
HTML, diagrams, a table of contents or community modules. For a text-only README
with no such elements, the profile and selected skeleton are enough.

Verify the document from its actual repository path and on its intended renderer
when permitted. The first command should not be separated from necessary setup
by collapsible content or a wall of decorative material. Link captions should say
what the reader will find; an icon or badge must not be the only statement of a
critical limitation. Verify renamed heading anchors and inbound links within the
opened scope. Do not fabricate a full inbound-link audit.

Deliver one README file without a surrounding code fence or a method report.
For literal source in chat, use a fence longer than those inside. Put any needed
asset request, unresolved claim or narrow verification note in a separate handoff.
Keep factual correctness, house-style compliance and the owner's editorial
preference separate when reporting an audit; no combined score is necessary.
