# README profile: project-standard

Adopted on 2026-09-19 by this repository's owner for their public projects,
after reviewing two finished READMEs drafted with it. It is scoped to README
documents. Other technical pages use their task-specific structure.
`profiles/*.json` in assay are agent capability profiles; do not use that
directory for editorial preferences.

Adoption covers the owner's public repositories. It is not a universal
standard, and it says nothing about another owner's projects or about an
internal document that has not chosen it.

## Selection and scope

An explicit task-specific style overrides this preset; an adopted project style
is retained unless the task asks to replace it. Within the adopted scope this
preset is the project style for a README with none of its own. Elsewhere it is
a draft to work from. Later changes belong to the owner, outside the finished
README. Do not auto-save preferences from model-generated drafts.

Once selected, apply the rules below to content that serves this audience and
publication surface. Visual treatment and block order do not require every slot
to be filled; use the README module's content conditions first.
A missing required fact or asset is a
reported gap, not a licence to fabricate it. An applicable verified element must
not be omitted merely because the model has a different aesthetic preference.

## Public product

| Element | Contract | Absent evidence or material |
| --- | --- | --- |
| Hero | Product name and a concrete one-sentence purpose; GitHub draft uses a centered header. Place a supplied usable logo above it. | Without a logo, use a text hero. Never invent branding. For other renderers use a plain heading unless centered HTML is verified there. |
| Badges | One consistent `flat-square` row for applicable licence, CI workflow and release/package targets established by project sources. Each badge links to its underlying resource. | Omit a badge whose target is unknown or inapplicable; record a required missing target in the author handoff. Do not label a build passing from workflow existence. |
| Useful capabilities | Concrete supported things the reader can do, in `What you can do`. A tiny utility may express these in its opening rather than repeat them. | Do not fill the section with generic adjectives. |
| Demonstration | Use an appropriate image, live demo or example when it explains a non-obvious behavior or choice. An agreed visual requirement still applies to a suitable supplied asset. | No empty Screenshot section or invented screenshot. If no example helps, omit the block. |
| Installation or access | Use `Install` or `Access` when the reader needs setup, prerequisites or a route beyond what the publication surface already supplies. | An unpublished product can use a supported checkout route. A catalog-managed install needs no duplicate instructions; a repository may need a download link. |
| First use | Use `Quick start` for necessary actions after installation or access, with starting conditions and expected result. | Omit the block for automatic operation requiring no action or setup. Preserve product-specific conditions where they affect use. |
| Navigation | `Documentation` links to relevant existing pages. A short page with no deeper docs can omit this block. | Do not add dead links or create a documentation site for the template. |
| Limits and provenance | State material limits where they affect use. End with a licence link when its terms are known. Include a contributing link when available and relevant. | Never assume MIT, invent support promises or remove existing legal/attribution notices. |

Order for applicable blocks: hero → badges → useful capabilities → available
visual/live demonstration → first-result path → navigation → further limits →
contributing pointer → licence. A risk or limit needed earlier moves before the
relevant action; this is an explicit exception, not style drift. A primary visual
may follow the hero if the owner selects that treatment. No universal line count
or fixed number of features is part of this preset.

Names for applicable headings, not a required set: `What you can do` / `Возможности`; `Install` / `Установка`;
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
