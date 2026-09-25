# Authoring contract

This repository is the single source for the skills and agent profiles it
publishes. An agent working here follows this contract; a human contributor will
find the same rules readable.

## What belongs here

A skill earns its place by having more than one proven consumer and one concrete
capability. A second hypothetical consumer is not evidence. Single-project
workflows stay with the project that needs them.

Store canonical content once. `catalog.toml` is the complete inventory and the
projection contract; `VERSION` is the only revision label. Client manifests and
profile adapters are generated from those two, never edited by hand.

## Writing a skill

- One directory per skill under `skills/<name>/`, where `<name>` matches the
  frontmatter `name` exactly: lowercase, hyphenated, no more than 64 characters.
- `SKILL.md` frontmatter carries `name`, `description` and `license`. The
  description says when to use the method **and when to skip it**, because that
  second half is what stops it firing on the wrong task.
- Keep `SKILL.md` short and route conditional depth into `references/`. An
  unused method should cost little context.
- Link to a rule another skill owns instead of restating it. The linking skill
  says when to use that method and what stays with itself; the owner keeps the
  rule, so it changes in one place.
- Keep client-specific facts — model aliases, tool names, permission metadata —
  in adapters or routed client references, never in neutral prose.
- Evaluation data lives in `evals/` and is never read while performing a user's
  task. A method that reads its own grading key stops being measured.
- Scripts belong inside the skill that uses them. Declare their dependencies in
  a requirements file beside them, never install into a user's environment, and
  never hardcode a path from the machine you wrote them on.
- Exit codes are part of a script's contract: success is 0, a refuted condition
  is non-zero, and missing or invalid evidence is distinct from both. A checker
  that inspected nothing must fail rather than pass.

## Profiles and adapters

Profiles are capability boundaries, not personas. They carry no model, no effort
level, no machine path and no runtime state. Codex skills project only to the
native `~/.agents/skills` root; Claude links through that same native entry.
Never manage Codex's `.system` directory.

The link lifecycle may create or remove only exact catalogued targets. It refuses
real directories, foreign links, modified adapters and reparse-point ancestors.
It does not package anything or keep install state.

## Gates

Set up tooling in an isolated Python 3.11+ environment with
`python -m pip install -r requirements-tools.txt`. Never auto-install into a
user's global environment.

```text
python -B tools/check.py --all
python .github/relkit.pyz audit
```

`check --all` runs every gate and reports each one rather than stopping at the
first failure. It creates its own scratch directory for the audit-packet suite.
`make check` is the same command. To run a single gate, the list is in
`tools/check.py`.

Generated client manifests, profile adapters and the skills index are produced by
`python -B tools/assay.py render` and verified byte-for-byte by the source check,
so a hand-edited manifest fails rather than drifting quietly.

Keep the marked inventory in `docs/architecture.md` synchronised with
`python tools/catalog_docs.py --write`, and never generate the compatibility
expectations from the catalog they are meant to check.

**What these gates do not check.** They do not run a model, so they say nothing
about whether a skill produces better work. They do not prove that a client
discovered a skill or that a requested sandbox was effective; only a captured run
in a fresh client speaks to that. They do not read your prose for accuracy: a
confident sentence about a mechanism passes every check here and can still be
wrong. Behavioural and discovery claims need actual client evidence.

## Commits and releases

After each coherent green boundary, commit locally. Stage exact task-owned paths
in one uninterrupted stage, inspect, commit sequence, and never leave a staged
handoff. Preserve any pre-existing staged work.

Commit subjects use the Conventional Commit types `build`, `chore`, `ci`, `docs`,
`feat`, `fix`, `perf`, `refactor`, `revert`, `style` and `test`, with an optional
lowercase scope and `!` for a breaking change. `CHANGELOG.md` is generated from
those subjects under the Angular preset, so a vague subject becomes a vague
changelog entry that nobody can fix later without rewriting history. Do not credit an AI tool as an
author, co-author, reviewer or generator anywhere in a commit, pull request,
release note or tracked file.

Never push unless explicitly asked. Before a live install or an upgrade, capture
the existing target bytes and link destinations outside the managed roots: an
upgrade removes with the old revision and installs with the new one, and rollback
restores that external snapshot.
