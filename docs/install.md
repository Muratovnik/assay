# Installing assay

Which route you take depends on your client, and on whether you want the agent
profiles as well as the skills. All of them install the same source.

**English** · [Русский](ru/install.md) · [简体中文](zh-CN/install.md)

## What is verified and what is not

The Claude Code route and the skills CLI route were exercised against the
published repository, and the installed files were compared byte for byte. The
Codex, Cursor and Gemini CLI routes follow those clients' own documentation and
have not been run here. The distinction is kept on purpose: a library that asks
others to separate verified from documented owes the same of itself.

## Claude Code

```text
claude plugin marketplace add Muratovnik/assay
claude plugin install assay@assay
```

The slash equivalents are `/plugin marketplace add Muratovnik/assay` and
`/plugin install assay@assay`. Add `--scope project` to install for one
repository instead of your user account, and pin a release by adding a tag to the
marketplace: `Muratovnik/assay@v0.1.0`.

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

Add `-a claude-code` or `-a codex` to target one client, `-g` for a global rather
than project install, and `--skill <name>` to take one method rather than the
whole library.

One caveat worth knowing: for Codex the CLI's global install writes to
`~/.codex/skills/`, which current Codex documentation does not list as a skill
root. If Codex does not see the skills afterwards, install into the project
instead, or use the symlink installer.

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

## Uninstalling

```text
python tools/assay.py uninstall-links
```

It removes only entries whose link target or rendered bytes still exactly match
the current plan. Anything you changed by hand is left alone and reported, so an
uninstall cannot quietly discard your edit.

For the plugin routes, use your client's own uninstall: `claude plugin uninstall
assay@assay`, or the client's plugin manager.

## Upgrading

Pull the new revision and re-run the installer. If the profile adapters changed
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
