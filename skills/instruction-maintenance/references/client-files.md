# Client instruction files

Use when an edit touches files that different agents read, nested or imported
instruction files, or several repositories. These are client facts with a
source date; recheck the client's current documentation when a decision depends
on one, because discovery rules change between releases.

## What each client reads

Checked against the vendors' documentation on 2026-10-17.

**Codex** ([AGENTS.md guide](https://developers.openai.com/codex/guides/agents-md)):
a global `AGENTS.override.md` or `AGENTS.md` in the Codex home directory, then,
from the project root (typically the Git root) down to the working directory, at
most one file per directory: `AGENTS.override.md`, else `AGENTS.md`, else a
configured fallback name. Files are concatenated root first, so a nearer file
appears later. The project files share a size limit (`project_doc_max_bytes`,
32 KiB by default); the global file is loaded apart and does not count toward
it. A project file past the limit is cut or skipped, and Codex warns that it
was. A separate warning comes when the whole text, global file included,
exceeds the setting; on its own it does not mean that anything was cut. The
guide leaves the count open; checked on 2026-11-25 against the
[Codex source](https://github.com/openai/codex/blob/main/codex-rs/core/src/agents_md.rs)
and the warnings of Codex CLI 0.171.0.

**Claude Code** ([memory](https://code.claude.com/docs/en/memory)): `CLAUDE.md`,
`.claude/CLAUDE.md` and `CLAUDE.local.md` in the working directory and every
directory above it, plus user-level and managed files and `.claude/rules/`.
Subdirectory files load when the agent works with a file there. `@path` imports
expand at launch, relative to the importing file, up to four hops; an import
inside a code span is literal text. Recent versions read `AGENTS.md` directly,
but by default only when no `CLAUDE.md` or `CLAUDE.local.md` exists in the
working directory or above it; a `CLAUDE.md` that imports `AGENTS.md` works in
every version.

**Skills** ([Agent Skills specification](https://agentskills.io/specification)):
a `SKILL.md` frontmatter `description` is what an agent sees before choosing the
skill; the body loads when the skill is used, and referenced files only when the
body routes to them. A rule placed only in a reference is invisible until that
route is taken.

## Consequences for an edit

- **Single source.** When one file imports another, edit the imported file. A
  rule added beside the import is read by one client and not the others.
- **A new file can hide another.** Adding a `CLAUDE.local.md` or `CLAUDE.md`
  where a repository relies on `AGENTS.md` can stop one client reading
  `AGENTS.md` under its default setting. Check before creating a file.
- **Independent repositories inherit nothing reliably.** One client stops at the
  project root; another reads every ancestor directory. A parent rule that
  should bind a nested independent repository has to be stated there or pointed
  to from there; physical nesting is not a contract.
- **Order is not priority.** Concatenated files do not override each other by
  rule; a nearer file only appears later. Contradictions between levels stay
  contradictions until one is removed or explicitly scoped.
- **Size limits truncate.** Measure the size of the files a limit counts when a
  file grows near it, and read the client's warnings about what it cut.

To confirm what loaded, use the client's own listing of loaded instruction files
in a fresh session. A file's presence on disk is not evidence that it was read.
