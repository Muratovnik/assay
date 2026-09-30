# Installing assay

Which route you take depends on your client, and on whether you want the agent
profiles as well as the skills. All of them install the same source.

**English** · [Русский](ru/install.md) · [简体中文](zh-CN/install.md)

## What is verified and what is not

Earlier installation observations do not verify this revision's discovery,
hooks or behavior. The matrix below states shipped surfaces from manifests and
installer code. Claim a successful native run only with a receipt identifying
client/version, package revision, route and observed event. Metadata eligibility,
loader invocation, followed criteria and outcome quality are different claims.

## Installation surfaces

| Route | Skills | Profiles | Reminders | Requirements and evidence boundary |
| --- | --- | --- | --- | --- |
| Claude Code plugin | Collection | Both Claude adapters | Packaged hooks | Client plus Python 3.11+ as `python`; manifest/handler checks are not a current native-run receipt |
| Codex plugin | Collection | Not installed into native agents directory | Packaged hooks, subject to client trust | Client plus Python 3.11+ as `python`; no discovery guarantee from packaging |
| Third-party skills CLI, including Cursor selection | Selected directories | No | No | Node/npx and compatible client; inspect the reported destination and selected files |
| Gemini skills installation | Skills | No Assay profile installation | No Assay plugin reminders | Gemini CLI; check its reported skill root and discovery |
| `install-links` | Linked collection | Selected Codex/Claude adapters | No | Python 3.11+, `requirements-tools.txt`, symlink support; exact filesystem checks are not behavior evidence |

The collection preserves relative peer links. A singleton supplies its bounded
core, not every specialist criterion in the collection. `metadata.assay-optional-skills`
records optional collaborators for Assay checks; no client is expected to install
dependencies from this field. The source gate copies the collection and each
singleton into temporary layouts to check Markdown resource boundaries; it does
not simulate a third-party installer. See [composition](explanation/skill-composition.md).

## Automatic skill reminders

The full plugin ships separate generated manifests for Claude Code
([`hooks/hooks.json`](../hooks/hooks.json)) and Codex
([`hooks/codex.json`](../hooks/codex.json)). `UserPromptSubmit` supplies bounded,
English/Russian, catalogue-backed suggestions. Session and delegation reminders
remain available. These hints do not authorize edits/delegation or prove compliance.

Python 3.11+ must be available as `python`. Prompt classification additionally uses
`hooks/requirements.txt` in that interpreter's isolated environment; no dependency
is installed automatically. Hooks make no model/network calls. The strict Claude
routing guard does not depend on the prompt parser and takes precedence over hints.

Enable the full plugin and review its native hook/trust diagnostics after updates.
Skills CLI and `install-links` do not register hooks or edit personal AGENTS.md.
The optional required-routing protocol remains Claude-specific; selecting it on
Codex blocks protected operations rather than silently dropping the requirement.

See [hook configuration, doctor, client limits and offline replay](how-to/hooks.md).
The guide separates installed/configured/observed evidence, explains optional state,
rollback and overlapping hooks, and documents the custom-effort constraints.

## Claude Code

```text
claude plugin marketplace add Muratovnik/assay
claude plugin install assay@assay
```

The slash equivalents are `/plugin marketplace add Muratovnik/assay` and
`/plugin install assay@assay`. Add `--scope project` to install for one
repository instead of your user account, and pin a release by adding a tag to the
marketplace: `Muratovnik/assay@v0.2.0`.

Start a new session afterwards. Skills appear under their own names, and the two
agent profiles arrive with the plugin.

## Codex

```text
codex plugin marketplace add Muratovnik/assay
```

Then open `/plugins` in the CLI and install assay from that marketplace. Restart
Codex afterwards.

Codex reads skills from `.agents/skills` in the project, walking up to the
repository root, and from `$HOME/.agents/skills` for your user account. Its agent
definitions live in `~/.codex/agents/*.toml`, which the plugin route does not
write: for the profiles, use the symlink installer below.

## Any agent, through the skills CLI

```text
npx skills add Muratovnik/assay
```

Add `-a claude-code` or `-a codex` to target a client and `-g` for global scope.
Use `--skill '*'` to select the full collection. `--skill <name>` selects a
bounded standalone method; it does not recursively install linked peers.
Check the destination shown by the installed CLI version against your client's
current skill roots. If discovery misses, use a supported project installation
or the explicit native link layout below; do not create guessed aliases.

## Gemini CLI

```text
gemini skills install https://github.com/Muratovnik/assay.git --consent
```

Gemini reads `~/.agents/skills` and `.agents/skills` as aliases of its own skill
roots, so the symlink installer works there too.

## Cursor

```text
npx skills add Muratovnik/assay -a cursor
```

Cursor keeps personal skills in `~/.cursor/skills/`, and the skills CLI knows that
path. Cursor's own repository import lives in the Dashboard under team
marketplaces and is meant for a team administrator rather than a single install.

## The symlink installer

Use this when you want the agent profiles, or when you are editing a checkout and
want your changes live immediately.

```text
git clone https://github.com/Muratovnik/assay.git
cd assay
python -m pip install -r requirements-tools.txt
python tools/assay.py plan
python tools/assay.py install-links
```

`plan` writes nothing. It prints, for every target, what it would create and what
the exact rollback target would be; `--json` gives the same as structured output,
and `--home` points the whole plan at an isolated directory for a dry run.

`install-links` then creates:

```text
~/.agents/skills/<name>   -> <checkout>/skills/<name>
~/.claude/skills/<name>   -> ~/.agents/skills/<name>
~/.codex/agents/<profile>.toml    rendered from profiles/<profile>.json
~/.claude/agents/<profile>.md     rendered from profiles/<profile>.json
```

It preflights the whole plan first. A real directory, a foreign link, a modified
adapter or a reparse-point parent stops the run before anything is written.

**On Windows** creating a directory symlink requires that permission, normally
Developer Mode or an elevated terminal. The installer fails closed if it is
missing; it will not fall back to a shell command.

With the Claude Code plugin installed, the plugin already supplies the skills and
both profiles, so the Claude entries would show every skill twice. Add
`--client codex` to `plan`, `install-links` and `uninstall-links` to handle only
the Codex entries, or `--client claude` for only the Claude ones. A Claude skill
link resolves through the Codex one, so installing Claude alone needs the Codex
links in place, and removing Codex alone is refused while Claude links remain. To
drop the Claude entries from an existing install, run
`python tools/assay.py uninstall-links --client claude`.

## Optional routing advisor

`route-subagents` can use `native-economy` through the active client's available
models, or the separately enabled hosted Jev adapter. Both extend the existing
benchmark MCP server; installing skill links does not register or enable them.
Config v1 remains evidence-only and a v2 file keeps its advisor settings. The
explicit migration writes a new schema-3 file, evidence-only by default, and keeps
the original for rollback. Native-only operation needs no Jev SDK or key.
Required routing is a separate opt-in for Claude Code, described in the
[required routing contract](../skills/route-subagents/references/required-routing.md).

See the [routing advisor setup and workflow](../skills/route-subagents/references/routing-advisor.md)
for configuration, optional pinned SDK installation, external-data consent,
bounded handoff, metadata retention and offline replay. Reconnect the client
after changing its server configuration. Static tests do not establish native
model behavior, actual provider access or quota savings.

## Uninstalling

```text
python tools/assay.py uninstall-links
```

It removes only entries whose link target or rendered bytes still exactly match
the current plan. Anything you changed by hand is left alone and reported, so an
uninstall cannot quietly discard your edit. Unrelated Markdown-format or
render-drift errors do not block removal; the catalog, exact target ownership,
profile identity and safe-parent checks still apply.

For the plugin routes, use your client's own uninstall: `claude plugin uninstall
assay@assay`, or the client's plugin manager.

## Upgrading

Pull the new revision and re-run the installer, keeping the same `--client`
selection on every step. If the profile adapters changed
between revisions, the upgrade is two steps in order:

```text
# from the revision that created the current adapters
python tools/assay.py uninstall-links
# then, from the new revision
python tools/assay.py install-links
```

This matters because uninstall only removes bytes it recognises. Running it from
the new revision after the adapters changed leaves the old ones in place, and you
would have to remove them by hand.

Before either step, keep a copy of the existing adapter bytes and link
destinations somewhere outside the managed roots. That external snapshot is the
rollback path; a state file beside the installation is not one.

[Upgrading a linked install](how-to/upgrade-linked-install.md) walks through the
same upgrade step by step, including what to save first and how to undo it.
