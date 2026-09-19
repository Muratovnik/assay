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

A skill activates on its own when a task matches its description. Each row
links to the instructions the agent will actually read.

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

Two more skills are in the repository — `technical-writing` (write, reshape,
translate or review product documentation from its sources) and `text-writing`
(write or reshape ordinary prose for a particular reader, or review an existing
text). Both arrived after `v0.1.0` and are **not** part of that release, so an
install pinned to the tag does not carry them.

Two agent profiles ship as capability boundaries rather than personas.
`evidence-reviewer` reviews a frozen packet through a read-only oracle and
returns a verdict; `official-docs-researcher` answers one bounded question from
primary documentation. Neither pins a model.

> [!NOTE]
> A skill instructs an agent, and some skills here ship scripts that agent can
> run. Read what you install, from this repository or any other.

## Install

The skills themselves are Markdown; a client just needs to load them. Python
3.11 or newer, plus the pinned dependency in `requirements-tools.txt`, is only
needed for the symlink installer and this repository's own tools below.

| Client | Command | Verified |
| --- | --- | --- |
| Claude Code | `/plugin marketplace add Muratovnik/assay` then `/plugin install assay@assay` | yes |
| Any supported agent | `npx skills add Muratovnik/assay` | yes |
| Codex | `codex plugin marketplace add Muratovnik/assay`, then install from `/plugins` | documented |
| Cursor | `npx skills add Muratovnik/assay -a cursor` | documented |
| Gemini CLI | `gemini skills install https://github.com/Muratovnik/assay.git --consent` | documented |

**Verified** means the route was exercised against this published repository
and the installed files compared byte for byte. **Documented** means it
follows the client's own documentation and has not been run here.

For Codex, the CLI's global install writes to `~/.codex/skills/`, which
current Codex documentation does not list as a skill root; install into the
project instead, or use the symlink installer below. Per-client detail,
uninstall and upgrade are in [the install guide](docs/install.md).

## Quick start

Start a new session after installing: clients read their skill roots at
startup. The skills then appear under their own names — `test-writing`,
`independent-audit` and the rest.

Give the agent a task that matches one of them:

```text
Review tests/test_billing.py and tell me whether it actually protects
against regressions, or only runs.
```

`test-audit` activates on its own, with nothing to invoke by name: it looks
for wrong expectations, missed defects and brittle checks rather than
confirming that the suite runs. There is nothing else to install.

<details>
<summary><b>Symlink installer</b> — the agent profiles, and edits that take effect immediately</summary>

The plugin routes install skills. The two agent profiles, and a setup where
your edits to a checkout are live without reinstalling, come from the
repository's own installer:

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
