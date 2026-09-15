# Contributing

Thanks for looking. This is a set of methods one person maintains and published
because they might be useful to your agent too. Issues and pull requests are
welcome; replies are best-effort, not same-day.

## Before you write

**Open an issue first for a new skill.** The bar is a capability with more than
one proven consumer, and it is cheaper to hear that a proposed method is already
covered by an existing one than to find out in review. Consolidating two skills
into one is a normal outcome here.

**Small fixes need no ceremony.** A wrong instruction, a broken link, a
description that fires on the wrong task: send the pull request.

## Setting up

```text
git clone https://github.com/Muratovnik/assay.git
cd assay
python -m pip install -r requirements-tools.txt
```

Use an isolated environment. Nothing in this repository installs into a global
one, and nothing should start.

## The gates

Run them before sending a change. They take seconds.

```text
python -B tools/check.py --all
```

That runs every gate, reports each one, and keeps going rather than stopping at
the first failure. `make check` is the same command, and it creates the scratch
directory the audit-packet suite needs, so there is nothing to set up first.

To run one gate on its own, the list lives in `tools/check.py`. Continuous
integration runs `check --all` on Linux and Windows, plus the publication audit.

What the gates do **not** check is written down in [AGENTS.md](AGENTS.md); read
that before trusting a green run.

## Adding a skill

1. Create `skills/<name>/SKILL.md` with `name` (matching the directory),
   `description` and `license: MIT` in the frontmatter.
2. Write the description as a pair: when to use the method, and when to skip it.
   The second half is what keeps it from firing on unrelated work.
3. Keep `SKILL.md` short. Conditional depth goes in `references/`, loaded only
   when a task needs it.
4. Add `agents/openai.yaml` with the Codex interface strings, in English.
5. Add `evals/` with cases and a separate rubric. Inputs and grading criteria stay
   apart, and neither is read while the skill is doing a user's task.
6. Register the asset in `catalog.toml`, then run
   `python -B tools/catalog_docs.py --write` and `python -B tools/assay.py render`
   to refresh the generated inventory, the client manifests and the skills index.
   The gate compares those bytes, so a forgotten render fails the build.

Scripts, if the skill needs them, live inside the skill directory with their own
requirements file. They take explicit paths, never hardcode one from your machine,
and distinguish success, a refuted condition and missing evidence in their exit
codes.

## Commits

Conventional Commits, with the closed type set `build`, `chore`, `ci`, `docs`,
`feat`, `fix`, `perf`, `refactor`, `revert`, `style`, `test`. A scope is optional
and lowercase; `!` marks a breaking change.

Say what changed and why it was worth changing. A commit message that only
restates the diff costs a reader the same time it saved you.

`CHANGELOG.md` follows the Angular preset of Conventional Commits: `feat` and
`fix` subjects become its entries, an optional scope becomes the bold prefix, and
a `BREAKING CHANGE` footer becomes its own section. Your subject is the entry, so
write it for someone reading the release rather than the diff.

**Do not credit an AI tool as an author, co-author, reviewer or generator** in a
commit, pull request, release note or tracked file. Use your own identity.

## Reporting a problem

A good report for a skill says what you asked, which skill activated or failed
to, and what it produced. Include the client and its version: activation
behaviour differs between them, and a method that misfires in one may be correct
in another.

For anything security-related, use [SECURITY.md](SECURITY.md) instead of a public
issue.
