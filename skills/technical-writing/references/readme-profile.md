# README profile: project-standard

This is an editable proposed preset, not a universal standard or evidence of
prior owner approval. It is scoped to README documents. Other technical pages
use their task-specific structure. `profiles/*.json` in assay are agent capability
profiles; do not use that directory for editorial preferences.

## Selection and scope

An explicit task-specific style overrides this preset; an adopted project style
is retained unless the task asks to replace it. A new README with no style can use
this preset as a draft. Approval and later changes belong to the owner, outside
the finished README. Do not auto-save preferences from model-generated drafts.

Once selected, apply the rules below. A missing required fact or asset is a
reported gap, not a licence to fabricate it. An applicable verified element must
not be omitted merely because the model has a different aesthetic preference.

## Public product

| Element | Contract | Absent evidence or material |
| --- | --- | --- |
| Hero | Product name and a concrete one-sentence purpose; GitHub draft uses a centered header. Place a supplied usable logo above it. | Without a logo, use a text hero. Never invent branding. For other renderers use a plain heading unless centered HTML is verified there. |
| Badges | One consistent `flat-square` row for applicable licence, CI workflow and release/package targets established by project sources. Each badge links to its underlying resource. | Omit a badge whose target is unknown or inapplicable; record a required missing target in the author handoff. Do not label a build passing from workflow existence. |
| Useful capabilities | Concrete supported things the reader can do, in `What you can do`. A tiny utility may express these in its opening rather than repeat them. | Do not fill the section with generic adjectives. |
| Demonstration | Show an existing appropriate image/live demo when supplied; otherwise use the first-use example as the demonstration. | No empty Screenshot section or invented screenshot. |
| First result | `Install` then `Quick start`, or `Access` then a hosted first-use path. Necessary conditions and expected result are included. | An unpublished product can use a supported checkout route, clearly described. |
| Navigation | `Documentation` links to relevant existing pages. A short page with no deeper docs can omit this block. | Do not add dead links or create a documentation site for the template. |
| Limits and provenance | State material limits where they affect use. End with a licence link when its terms are known. Include a contributing link when available and relevant. | Never assume MIT, invent support promises or remove existing legal/attribution notices. |

Order for applicable blocks: hero → badges → useful capabilities → available
visual/live demonstration → first-result path → navigation → further limits →
contributing pointer → licence. A risk or limit needed earlier moves before the
relevant action; this is an explicit exception, not style drift. A primary visual
may follow the hero if the owner selects that treatment. No universal line count
or fixed number of features is part of this preset.

Default heading pairs: `What you can do` / `Возможности`; `Install` / `Установка`;
`Access` / `Доступ`; `Quick start` / `Первый запуск`; `Documentation` / `Документация`;
`Limits` / `Ограничения`; `Contributing` / `Участие в разработке`; `License` / `Лицензия`.
Use the document's language. An adopted project glossary or explicit heading
scheme wins. Do not rename existing anchors during local copyediting.

## Internal or maintainer README

Use a plain heading, purpose, applicable setup/first task, working rules or
architecture needed by the team, then links. A public badge row, star-history,
hero art and contributor-avatar wall are not inherited. Existing licence,
security and attribution notices remain. A team can explicitly adopt visual
modules without changing the document's purpose.

## Owner-selectable extensions

Star-history, contributor avatars, social links, a Mermaid diagram, a tree and
an explicit table of contents are off in the draft preset. They are supported
choices, not prohibited or inherently bad elements. If the owner requires one,
record its source and applicable condition; follow it on subsequent pages in that
scope. Include a tree or diagram from actual structure, not a generic example.
A missing source stays missing even for a required extension.

Change only the owner's chosen values; do not turn a preference on one README
into a global rule. Stylistic consistency is a service the skill can provide even
when a fully specified no-skill prompt produces equally good prose.
