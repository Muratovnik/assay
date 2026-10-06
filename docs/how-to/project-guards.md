# Guard tests and check configuration in a project

Use this when a project wants changes to its tests and quality-check configuration
to need a person's approval, instead of relying on an agent's report that it left
them alone. Assay's methods already say not to weaken a check to get a green
result; this page is about the client configuration that can make such a change
visible or impossible. Assay does not install it and does not change client
settings: the project owner chooses and maintains it.

Client facts below were checked against primary documentation on 2026-10-06.
Clients change; recheck them after a client release, as for
[hooks](hooks.md).

## Decide what to protect

Protect the objects that decide whether work passes, not a proxy such as a green
build. A typical list, to adapt rather than copy:

- test directories and fixtures, for example `tests/**` or `**/__snapshots__/**`;
- check configuration: linter, type-checker and test-runner settings, coverage
  thresholds, `pyproject.toml` or `package.json` sections that configure them;
- CI workflows that run the gates, for example `.github/workflows/**`.

Protect them against any edit, not because an agent is expected to cheat: an
approved change is a normal event, and the prompt makes it a decision.

## Claude Code

Add `ask` rules to the project's `.claude/settings.json`. In that file a path
starting with `/` resolves against the session's primary working directory, so
start sessions from the project root; the patterns use gitignore syntax:

```json
{
  "permissions": {
    "ask": [
      "Edit(/tests/**)",
      "Edit(/.github/workflows/**)",
      "Edit(/pyproject.toml)"
    ]
  }
}
```

Rules are evaluated deny, then ask, then allow, so a broader `allow` cannot skip a
matching `ask`. Every permission mode, including `bypassPermissions` and auto
mode, still prompts for an explicit ask rule. An installed client mod that
handles tool checks can approve such a call, so check which mods are installed
where you rely on the prompt.

An `Edit` ask rule covers Claude's file tools. The documentation extends `Edit`
**deny** rules, not ask rules, to file commands Claude recognizes in Bash, such as
`sed` or `tee`, and to shell redirection targets; a shell edit of a path that has
only an ask rule is not documented to prompt. No rule covers a subprocess that
writes files itself, such as a script run by a test command; that needs the
client's sandbox. Use `deny` where an edit must never happen, and the reviewable
diff below where a shell edit must at least be visible.

A project `PreToolUse` hook is the alternative when the decision needs logic: it
receives `tool_input.file_path` for file edits and can return the
`permissionDecision` `ask`, `deny`, `allow` or `defer`. A hook decision does not
override a matching deny or ask rule.

## Codex

Codex does not offer the same path-scoped prompt today:

- A project `PreToolUse` hook (in `.codex/hooks.json`, run only after you trust its
  definition) can block a call with `permissionDecision: "deny"`, but `ask` is
  parsed and not supported: the hook is treated as failed and the call proceeds.
- File edits arrive through `apply_patch`, whose `tool_input.command` carries the
  patch text. The documentation does not specify a separate file-path field or
  the patch structure, so a hook that parses paths out of that text depends on an
  undocumented format.
- `PermissionRequest` runs only when Codex is already about to ask for approval,
  such as a sandbox escalation; it is not a per-path edit check.

Until a documented path-scoped control exists, keep the protection reviewable:
ask for a line such as `git diff --stat -- tests/ .github/workflows/` in the final
report and read that diff before accepting the work. The same line covers shell
edits in Claude Code that an ask rule does not reach.

## What this does not do

These settings do not verify which permissions a session actually had, prove
that an agent did not change files through another process, or judge whether an
approved change was right. After configuring, try a harmless edit to a protected
path in the client you use and confirm that it asks; until then the protection is
configured, not observed. False prompts on paths that are not checks mean the
list is too broad.

## Sources

- Claude Code: [Configure permissions](https://code.claude.com/docs/en/permissions),
  [Choose a permission mode](https://code.claude.com/docs/en/permission-modes),
  [Hooks reference](https://code.claude.com/docs/en/hooks).
- Codex: [Hooks](https://developers.openai.com/codex/hooks).
