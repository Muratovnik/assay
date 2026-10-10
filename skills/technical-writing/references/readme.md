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

Determine how this reader obtains the product and uses it in its normal supported
environment. Verify relevant distribution and native integration sources before
choosing the route. A declared console entry point does not disprove another
invocation; a manifest alone does not establish registry publication. A working
source command or demonstration does not establish the acquisition and native-use
path. Lead with that supported path when this audience needs it; source-based use
can be primary when it is the actual intended route.

For every retained procedure, including developer instructions, use
[procedure conditions](document-design.md#establish-procedure-conditions) to establish
setup from sufficient authoritative sources, following checks delegated by the
inspected entry point when needed.
Place prerequisites, directories, files and access before the first action that
needs them, allowing earlier steps or usable prerequisite handoffs to supply them.
Do not inherit conditions known only to the editor's environment.

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

Identify what the product is and the job it helps the reader do. A collection
of instructions, a library and a hosted service have different ways to use them;
the project name alone may not establish which one the reader is looking at.
Add a constraint or mechanism
when it changes suitability or explains otherwise unclear behavior. Do not lead
with the repository inventory or an inflated claim. Give concrete uses instead
of several restatements of the tagline.
Use the audience's established terms and keep distinct uses separate. Apply the
[content review](document-design.md#review-the-finished-content) to the opening
and feature list together so a property is not restated as another capability.

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
First use means applying the acquired product to this reader's own task through
its supported interface, including native integration where applicable. Building,
testing or packaging the repository belongs here only when necessary for that use;
otherwise keep contributor setup with the contributor route. A demonstration can
teach that first use when it supplies the same route; a separate demo needs its own
role and cannot fill a missing normal-use path.

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

Review the full saved README within the opened scope, including retained opening
claims and connected procedures. Reconcile their [canonical owners and projections](document-design.md#update-the-semantic-unit).
Use an available permitted project renderer or check path, with the bounded fallback
and reporting limits in [delivery checks](../SKILL.md#deliver-and-check-the-artifact).
Verify from the actual repository path. The first dependent action should not be
separated from necessary setup by collapsible content or a wall of decorative
material. Link captions should say what the reader will find; an icon or badge must not be the only statement of a
critical limitation. Verify renamed heading anchors and inbound links within the
opened scope. Do not fabricate a full inbound-link audit.

Deliver one README file without a surrounding code fence or a method report.
For literal source in chat, use a fence longer than those inside. Put any needed
asset request, unresolved claim or narrow verification note in a separate handoff.
Keep factual correctness, house-style compliance and the owner's editorial
preference separate when reporting an audit; no combined score is necessary.
