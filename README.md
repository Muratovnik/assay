# assay

Reusable methods for coding agents: skills and agent profiles for Claude Code,
Codex, Cursor and Gemini CLI.

**English** · [Русский](README.ru.md) · [简体中文](README.zh-CN.md)

[![checks](https://img.shields.io/github/actions/workflow/status/Muratovnik/assay/check.yml?branch=main&label=checks)](https://github.com/Muratovnik/assay/actions/workflows/check.yml)
[![release](https://img.shields.io/github/v/release/Muratovnik/assay)](https://github.com/Muratovnik/assay/releases)
[![license](https://img.shields.io/github/license/Muratovnik/assay)](LICENSE)

```text
/plugin marketplace add Muratovnik/assay
/plugin install assay@assay
```

An assay is a test of what something is actually made of. These methods share a
bias: say what was checked, say what it establishes, and say what it does not.

> [!NOTE]
> A skill instructs an agent, and some skills here ship scripts that agent can
> run. Read what you install, from this repository or any other.

## Install

| Client | Command | Verified |
| --- | --- | --- |
| Claude Code | `/plugin marketplace add Muratovnik/assay` then `/plugin install assay@assay` | yes |
| Any supported agent | `npx skills add Muratovnik/assay` | yes |
| Codex | `codex plugin marketplace add Muratovnik/assay`, then install from `/plugins` | documented |
| Cursor | `npx skills add Muratovnik/assay -a cursor` | documented |
| Gemini CLI | `gemini skills install https://github.com/Muratovnik/assay.git --consent` | documented |

**Verified** means the route was exercised against this published repository and
the installed files compared byte for byte. **Documented** means it follows the
client's own documentation and has not been run here. Start a new session
afterwards: clients read their skill roots at startup.

The skills CLI covers Claude Code, Codex, Cursor, OpenCode "and 75 more" by its
own count. For Codex its global install writes to `~/.codex/skills/`, which
current Codex documentation does not list as a skill root; install into the
project instead, or use the installer below.

Per-client detail, uninstall and upgrade are in [the install guide](docs/install.md).

<details>
<summary><b>Symlink installer</b> — the agent profiles, and edits that take effect immediately</summary>

The plugin routes install skills. The two agent profiles, and a setup where your
edits to a checkout are live without reinstalling, come from the repository's own
installer:

```text
git clone https://github.com/Muratovnik/assay.git
cd assay
python -m pip install -r requirements-tools.txt
python tools/assay.py plan
python tools/assay.py install-links
```

`plan` writes nothing. It prints every target it would create and the exact
rollback target for each. `install-links` then links `~/.agents/skills/<name>` to
this checkout and renders the profile adapters, preflighting the whole plan first:
a real directory, a foreign link or a modified adapter stops the run before
anything is written.

On Windows, creating a directory symlink needs that permission, normally
Developer Mode or an elevated terminal. The installer fails closed rather than
falling back to a shell.

</details>

## What's inside

A skill activates on its own when a task matches its description. Each row links
to the instructions the agent will actually read.

| Skill | Use it when | Skip it when |
| --- | --- | --- |
| [code-maintenance](skills/code-maintenance/SKILL.md) | A change affects code structure, shared logic or tooling | The edit is prose, or the task is a read-only audit |
| [test-writing](skills/test-writing/SKILL.md) | Tests need writing or repairing against a contract | You only need to run an existing suite, or explain testing |
| [test-audit](skills/test-audit/SKILL.md) | Someone claims a suite protects against regressions | You are writing the tests, or merely executing them |
| [independent-audit](skills/independent-audit/SKILL.md) | A change, release or migration needs checking against its brief | You want the change made; this method does not fix things |
| [evidence-research](skills/evidence-research/SKILL.md) | A consequential claim needs sources located and reconciled | The answer is one lookup away |
| [operations-ui-delivery](skills/operations-ui-delivery/SKILL.md) | Operational UI needs designing, repairing or critiquing | The work is backend only |
| [route-subagents](skills/route-subagents/SKILL.md) | Delegation is already authorised and needs bounding | Nobody authorised delegation; parallelism is not permission |
| [skill-design](skills/skill-design/SKILL.md) | A skill misfires, or a proposed method needs evaluating | You are editing metadata or authoring routine content |

Two agent profiles ship as capability boundaries rather than personas.
`evidence-reviewer` reviews a frozen packet through a read-only oracle and
returns a verdict; `official-docs-researcher` answers one bounded question from
primary documentation. Neither pins a model.

Detail lives one level down. A `SKILL.md` stays short and routes to `references/`
only when a task needs that depth, so an unused method costs little context.

## Requirements

The skills are Markdown and need nothing installed. Python 3.11 or newer and the
pinned YAML parser in `requirements-tools.txt` are for the repository's own tools
and gates.

`route-subagents` can optionally consult benchmark evidence when choosing a model,
through a local MCP server in `skills/route-subagents/scripts/`. It is opt-in, you
register it yourself, and the skill works without it.

## Trust and safety

The scripts here take explicit paths and never install anything into your
environment on their own, but that is a claim worth verifying rather than taking.

Nothing phones home. There is no telemetry, no account and no network call except
the optional benchmark server you would have to register yourself.

These methods read repositories, documentation and, in the research method, web
pages. That content is data, not instruction, and the methods say so — but no
instruction is a guarantee. Review what an agent proposes after it has read
something you do not control. Report a vulnerability privately through
[SECURITY.md](SECURITY.md).

## How this is validated

`python tools/check.py --all` runs every gate: source structure, the unit suite, a
compatibility fixture, the generated inventory, the evaluation data, the rendered
client manifests and the audit packet suite. Continuous integration runs the same
command on Linux and Windows, plus the publication audit and the Claude plugin
manifest validator.

No model runs in continuous integration and no skill here carries a score. What
the `evals/` directories do and do not establish is spelled out in
[what the evaluations establish](docs/evaluation.md).

## Contributing

Issues and pull requests are welcome; replies are best-effort. The authoring
contract, including an explicit list of what the gates do not check, is in
[AGENTS.md](AGENTS.md); the workflow is in [CONTRIBUTING.md](CONTRIBUTING.md).

[How assay is put together](docs/architecture.md) describes the inventory, the
discovery topology and the guarded install lifecycle.

## License

MIT. See [LICENSE](LICENSE).
