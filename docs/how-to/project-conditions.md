# State project conditions for agents

Use this when agents keep guessing conditions your project already knows: its
stage, which contracts outsiders depend on, which dependencies are acceptable.
Assay's methods look for these conditions before decisions that depend on them
([the list](../../skills/implementation-planning/references/scope-and-readiness.md#conditions-the-project-should-supply)).
What an agent can observe in the repository it extracts itself; what only you can
decide is better written down once than re-asked or silently assumed.

Assay does not install this fragment and stores no project values. A project
without it keeps working: agents extract observable facts and name their
assumptions about the rest.

## Add a fragment to the project's instructions

Put a short section in the instruction file your clients already read: Claude
Code loads `CLAUDE.md` at the start of every session and can also read
`AGENTS.md`; Codex combines `AGENTS.md` files from the repository root down to
the working directory, within a size limit (32 KiB by default). Both treat the
text as context, not as enforced configuration. Write only decisions; leave out
facts the repository already shows, such as test locations or installed versions.

```markdown
## Project conditions (checked 2026-10-06, revision abc1234)

- Stage: prototype; storage formats may change without migration until v1.
- Criticality: internal tool; a failed run can be repeated, no customer data.
- Critical areas: `migrations/` and `auth/` need an owner question before changes.
- Dependencies: MIT/Apache-2.0/BSD only; no new runtime services.
- Public contracts: the CLI flags and the `export` JSON schema are used by other teams.
- Expected extensions: new import formats; no plugin system planned.
```

A Russian-language project can write the same section in Russian; the methods
match meaning, not wording:

```markdown
## Условия проекта (проверено 2026-10-06, ревизия abc1234)

- Стадия: прототип; форматы сохранения можно менять без миграции до v1.
- Зависимости: только MIT/Apache-2.0/BSD; новых сервисов не добавлять.
- Публичные контракты: флаги CLI и JSON-схема `export` используются другими командами.
```

Domain facts belong here too, for example which engine classes already provide a
behavior or under which terms a project's assets may be reused. Assay keeps such
examples out of its general methods.

## Keep it current

Date or revision each section. An outdated condition is worse than a missing one:
an agent that finds a stale value should name it stale rather than apply it, and
you should update or remove it when the stage or policy changes. Keep the values
in one owning file; other documents link to it instead of copying it.

## What this does not do

The fragment does not grant authority, approve risky changes or enforce anything.
Approvals, permissions and protected paths stay with the client configuration and
the project's own review process; [project guards](project-guards.md) covers the
client-side options for tests and check configuration. Writing a condition down
does not prove that an agent applied
it: check the result and the report, which should cite the condition or name the
assumption it made instead.

Sources checked on 2026-10-06: Claude Code,
[How Claude remembers your project](https://code.claude.com/docs/en/memory);
Codex, [Custom instructions with AGENTS.md](https://developers.openai.com/codex/guides/agents-md).
