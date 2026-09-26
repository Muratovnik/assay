# assay

Reusable methods for coding agents: skills and agent profiles for Claude Code,
Codex, Cursor and Gemini CLI. An assay is a test of what something is actually
made of — these methods say what was checked, what it establishes, and what it
does not.

**English** · [Русский](README.ru.md) · [简体中文](README.zh-CN.md)

[![checks](https://img.shields.io/github/actions/workflow/status/Muratovnik/assay/check.yml?branch=main&label=checks&style=flat-square)](https://github.com/Muratovnik/assay/actions/workflows/check.yml)
[![release](https://img.shields.io/github/v/release/Muratovnik/assay?style=flat-square)](https://github.com/Muratovnik/assay/releases)
[![license](https://img.shields.io/github/license/Muratovnik/assay?style=flat-square)](LICENSE)

## What you can do

Skills are eligible for discovery when a task matches their descriptions.
Selection depends on the client, installation and task; metadata alone is not
proof of activation. Each row links to the method itself.

| Skill | Use it when | Skip it when |
| --- | --- | --- |
| [code-change](skills/code-change/SKILL.md) | A change affects code structure, shared logic or tooling | The edit is prose, or the task is a read-only audit |
| [implementation-planning](skills/implementation-planning/SKILL.md) | Work needs a plan, from one change to a staged roadmap, or a plan needs revising | You are still discussing an idea, only researching, or the edit is obvious |
| [software-architecture](skills/software-architecture/SKILL.md) | A system's boundaries, contracts or file placement need choosing or assessing | The edit is local and routine, or you need an audit verdict rather than criteria |
| [test-writing](skills/test-writing/SKILL.md) | Tests need writing or repairing against a contract | You only need to run an existing suite, or explain testing |
| [test-audit](skills/test-audit/SKILL.md) | Someone claims a suite protects against regressions | You are writing the tests, or merely executing them |
| [independent-audit](skills/independent-audit/SKILL.md) | A plan, change, architecture, release or migration needs checking against its brief | You want the change made; this method does not fix things |
| [evidence-research](skills/evidence-research/SKILL.md) | A consequential claim needs sources located and reconciled | The answer is one lookup away |
| [ui-delivery](skills/ui-delivery/SKILL.md) | A product interface needs designing, repairing, transferring or critiquing | The work is backend only |
| [route-subagents](skills/route-subagents/SKILL.md) | Delegation is already authorised and needs bounding | Nobody authorised delegation; parallelism is not permission |
| [skill-evaluation](skills/skill-evaluation/SKILL.md) | A skill misfires, or a proposed method needs evaluating | You are editing metadata or authoring routine content |
| [technical-writing](skills/technical-writing/SKILL.md) | Product documentation needs writing, reshaping, translating or reviewing from its sources | The text is an ordinary message or article, or the change is code |
| [text-writing](skills/text-writing/SKILL.md) | Ordinary prose needs writing or reshaping for one particular reader | The text is product documentation, agent instructions or a commit record |

Two agent profiles ship as capability boundaries rather than personas.
`evidence-reviewer` reviews a frozen packet through a read-only oracle and
returns a verdict; `official-docs-researcher` answers one bounded question from
primary documentation. Neither pins a model.

> [!NOTE]
> A skill instructs an agent, and some skills here ship scripts that agent can
> run. Read what you install, from this repository or any other.

## Install

The instructions are Markdown. The **Claude Code and Codex plugin reminders**
require Python 3.11+ available as `python` and use only its standard library.
The symlink installer and repository checks also need `requirements-tools.txt`.
Optional skill scripts declare their own dependencies; loading prose does not
install them.

| Client | Command |
| --- | --- |
| Claude Code | `/plugin marketplace add Muratovnik/assay` then `/plugin install assay@assay` |
| Any supported agent | `npx skills add Muratovnik/assay` |
| Codex | `codex plugin marketplace add Muratovnik/assay`, then install from `/plugins` |
| Cursor | `npx skills add Muratovnik/assay -a cursor` |
| Gemini CLI | `gemini skills install https://github.com/Muratovnik/assay.git --consent` |

The third-party skills CLI installs selected skills, not plugin hooks or agent
profiles. Prefer the full collection (`--skill '*'`) for composed work. A single
skill has a bounded core and declares optional peers; missing criteria are not
silently supplied. Check the destination reported by your CLI version. See the
[installation and evidence matrix](docs/install.md#installation-surfaces) and
[name migration](docs/how-to/migrate-skill-names.md).

## Quick start

Start a new session after installing: clients read their skill roots at
startup. The skills then appear under their own names — `test-writing`,
`independent-audit` and the rest.

Give the agent a task that matches one of them:

```text
Review tests/test_billing.py and tell me whether it actually protects
against regressions, or only runs.
```

`test-audit` is the intended method: it looks for wrong expectations, missed
defects and brittle checks rather than just confirming that the suite runs.
Check that it was loaded; name it explicitly when discovery misses. Loading
does not prove that its criteria were followed.

<details>
<summary><b>Symlink installer</b> — the agent profiles, and edits that take effect immediately</summary>

The Claude Code plugin already includes both profiles. The symlink installer
also supplies Codex profiles and makes checkout edits available without
reinstalling. Do not install duplicate Claude entries alongside the plugin:

```text
git clone https://github.com/Muratovnik/assay.git
cd assay
python -m pip install -r requirements-tools.txt
python tools/assay.py plan
python tools/assay.py install-links
```

`plan` writes nothing. It prints every target it would create and the exact
rollback target for each. `install-links` then links `~/.agents/skills/<name>`
to this checkout and renders the profile adapters, preflighting the whole plan
first: a real directory, a foreign link or a modified adapter stops the run
before anything is written.

On Windows, creating a directory symlink needs that permission, normally
Developer Mode or an elevated terminal. The installer fails closed rather than
falling back to a shell.

</details>

## Documentation

- [Installing assay](docs/install.md) — per-client detail, uninstalling and upgrading.
- [Upgrading a linked install](docs/how-to/upgrade-linked-install.md) — moving a symlink install to a newer revision, and the way back if it goes wrong.
- [How assay is put together](docs/architecture.md) — the inventory, the discovery topology and the guarded install lifecycle.
- [Why one source reaches several clients](docs/explanation/discovery-topology.md) — why a skill is linked and a profile rendered, and what each choice costs.
- [What the evaluations establish](docs/evaluation.md) — what each skill's `evals/` directory proves and does not prove.
- [Skills index](skills/README.md) — the generated list of skills with activation and a one-line purpose.

## Limits

- Nothing here phones home: no telemetry, no account and no network call,
  except the optional `route-subagents` benchmark server, which you register
  yourself.
- The scripts take explicit paths and do not install anything into your
  environment on their own — worth verifying rather than taking on faith.
- These methods read repositories, documentation and, in the research method,
  web pages. That content is data, not instruction, and the methods say so —
  but no instruction is a guarantee. Review what an agent proposes after it
  has read something you do not control.
- No model runs in continuous integration and no skill carries a score; see
  [what the evaluations establish](docs/evaluation.md) for the exact scope.
- Report a vulnerability privately through [SECURITY.md](SECURITY.md) rather
  than a public issue.

## Contributing

Issues and pull requests are welcome; replies are best-effort. The authoring
contract, including an explicit list of what the gates do not check, is in
[AGENTS.md](AGENTS.md); the workflow is in [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT. See [LICENSE](LICENSE).
