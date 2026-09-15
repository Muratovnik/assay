# Assay

**Evidence-grounded methods for coding agents.** Eight skills and two agent
profiles for Claude Code, Codex, Cursor and Gemini CLI, kept in one source and
installed into whichever native location your client reads.

An assay is a test of what something is actually made of. These methods share a
bias: say what was checked, say what it establishes, and say what it does not.

## Install

| Client | Command |
| --- | --- |
| Claude Code | `/plugin marketplace add Muratovnik/assay` then `/plugin install assay@assay` |
| Codex | `codex plugin marketplace add Muratovnik/assay`, then install from `/plugins` |
| Any of 75+ agents | `npx skills add Muratovnik/assay` |
| Gemini CLI | `gemini skills install https://github.com/Muratovnik/assay.git --consent` |
| Cursor | Customize → From GitHub Repository → `Muratovnik/assay` |

Restart or start a new session afterwards; clients read their skill roots at
startup. Full per-client detail, including uninstall and upgrade, is in
[the install guide](docs/install.md).

<details>
<summary>Symlink installer, and how to get the agent profiles</summary>

The plugin routes install skills. The two agent profiles, and a setup where your
edits to a checkout take effect immediately, come from the repository's own
installer:

```text
git clone https://github.com/Muratovnik/assay.git
cd assay
python -m pip install -r requirements-tools.txt
python tools/assay.py plan
python tools/assay.py install-links
```

`plan` is read-only and prints every target it would create and every rollback
target. `install-links` then links `~/.agents/skills/<name>` to this checkout and
renders the profile adapters. On Windows, creating a directory symlink needs that
permission (Developer Mode or an elevated token); the installer fails closed
rather than falling back to a shell.

</details>

## What's inside

Skills activate on their own when a task matches their description. Each links to
its own instructions.

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

Two agent profiles ship as capability boundaries rather than personas:
`evidence-reviewer` reviews a frozen packet with a read-only oracle and returns a
verdict, and `official-docs-researcher` answers one bounded question from primary
documentation. Neither pins a model.

Detail lives one level down. A `SKILL.md` stays short and routes to `references/`
only when a task needs that depth, so an unused method costs little context.

## Requirements

Python 3.11 or newer for the repository tools, and the pinned YAML parser in
`requirements-tools.txt` if you run the source gates. The skills themselves are
Markdown and need nothing installed.

`route-subagents` can optionally consult benchmark evidence when choosing a model,
through a local MCP server in `skills/route-subagents/scripts/`. It is opt-in, it
is registered by you, and the skill works without it.

## Trust and safety

**Skills instruct an agent, and some of them ship scripts that agent can run.**
Read what you install, from this repository or any other. The scripts here take
explicit paths and never install anything into your environment on their own, but
that is a claim you should verify rather than take.

Nothing here phones home. There is no telemetry, no account and no network call
except the optional benchmark server you would have to register yourself.

Report a vulnerability privately: see [SECURITY.md](SECURITY.md).

## How this is validated

`python tools/check.py --all` runs every gate on Linux and Windows for every
change: source structure, the unit suite, a compatibility fixture, the generated
inventory, the evaluation data, the rendered client manifests and the audit packet
suite. The publication audit runs alongside them.

No model is run in CI, and no skill here carries a score. What the `evals/`
directories do and do not establish is spelled out in
[what the evaluations establish](docs/evaluation.md).

## Contributing

Issues and pull requests are welcome; replies are best-effort. The authoring
contract, including what the validator does not check, is in
[AGENTS.md](AGENTS.md); the workflow is in [CONTRIBUTING.md](CONTRIBUTING.md).

[How assay is put together](docs/architecture.md) describes the inventory,
discovery topology and the guarded install lifecycle.

Русская версия: [README.ru.md](README.ru.md).

## License

MIT. See [LICENSE](LICENSE).
