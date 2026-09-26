# How assay is put together

**English** · [Русский](ru/architecture.md) · [简体中文](zh-CN/architecture.md)

Each skill is a directory under `skills/`, each agent profile a JSON file under
`profiles/`, and `catalog.toml` is the complete inventory. Nothing is duplicated
per client: the installer links or renders the one source into whichever native
location a client reads.

## Inventory

<!-- assay:catalog:start -->

<!-- Generated from catalog.toml by tools/catalog_docs.py; do not edit this block. -->
| Asset | Activation | Codex target | Claude target |
| --- | --- | --- | --- |
| `skill/route-subagents` | automatic | `~/.agents/skills/route-subagents` | `~/.claude/skills/route-subagents` |
| `skill/ui-delivery` | automatic | `~/.agents/skills/ui-delivery` | `~/.claude/skills/ui-delivery` |
| `skill/independent-audit` | automatic | `~/.agents/skills/independent-audit` | `~/.claude/skills/independent-audit` |
| `skill/skill-evaluation` | automatic | `~/.agents/skills/skill-evaluation` | `~/.claude/skills/skill-evaluation` |
| `skill/evidence-research` | automatic | `~/.agents/skills/evidence-research` | `~/.claude/skills/evidence-research` |
| `skill/test-writing` | automatic | `~/.agents/skills/test-writing` | `~/.claude/skills/test-writing` |
| `skill/test-audit` | automatic | `~/.agents/skills/test-audit` | `~/.claude/skills/test-audit` |
| `skill/software-architecture` | automatic | `~/.agents/skills/software-architecture` | `~/.claude/skills/software-architecture` |
| `skill/code-change` | automatic | `~/.agents/skills/code-change` | `~/.claude/skills/code-change` |
| `skill/implementation-planning` | automatic | `~/.agents/skills/implementation-planning` | `~/.claude/skills/implementation-planning` |
| `skill/technical-writing` | automatic | `~/.agents/skills/technical-writing` | `~/.claude/skills/technical-writing` |
| `skill/text-writing` | automatic | `~/.agents/skills/text-writing` | `~/.claude/skills/text-writing` |
| `profile/evidence-reviewer` | explicit | `~/.codex/agents/evidence-reviewer.toml` | `~/.claude/agents/evidence-reviewer.md` |
| `profile/official-docs-researcher` | explicit | `~/.codex/agents/official-docs-researcher.toml` | `~/.claude/agents/official-docs-researcher.md` |

<!-- assay:catalog:end -->

`catalog.toml` carries ownership, activation and exact destinations. It carries no
model, effort, runtime state, package manifest or machine path. `VERSION` labels
the source contract; the installer and the client manifests read it rather than
repeating it.

## Discovery topology

A skill is installed once and reached twice. The native skill root holds the link
to the catalogued source, and Claude links through that same native entry rather
than to a second copy:

```text
~/.agents/skills/<name> -> <checkout>/skills/<name>
~/.claude/skills/<name> -> ~/.agents/skills/<name>
```

There is no `~/.codex/skills` projection. Codex reads `.agents/skills` in the
project and `~/.agents/skills` for the user, and its `.system` directory belongs
to the client. Agent profiles need different file formats per client, so they are
rendered rather than linked; their destinations are in the inventory above.

This section says what the layout is.
[Why one source reaches several clients](explanation/discovery-topology.md)
says why it is arranged that way — `~/.agents/skills` is the root several
clients already read, not one client's private directory — and what each choice
costs.

An automatic skill activating is not permission to delegate or to mutate anything.
Delegation is one level deep: the primary agent spawns every worker, and a worker
never creates another agent. `route-subagents` owns that policy once, and the
other skills do not restate it.

Profiles are capability boundaries, not roles with a model attached. The Codex
adapter asks for a read-only sandbox and the Claude adapter uses plan mode with a
capability-derived tool list. Only the evidence reviewer receives `Bash`, because
its declared oracle has to be executable, and its instructions still forbid
mutating commands. An adapter's requested sandbox is configuration: verify the
effective session policy rather than assuming a parent process left it intact.

## Routing advice

The routing advisor is a bundled part of `route-subagents`, served by its
existing benchmark MCP/CLI application. It reuses acquisition and cohort evidence,
builds a bounded immutable snapshot, asks the selected adapter for a ranking,
then applies deterministic policy. Native economy resolves a current economical
client model; Jev is an optional, explicitly consented hosted backend. Profiles
and the catalog carry neither a permanent economy model nor runtime settings.

Assay owns contracts, policy, local metadata and diagnostic replay. The client
owns authorization, spawning, cancellation and actual quota accounting. Prepared
state and an exact decision cache are bounded in memory; optional JSON telemetry
has its own cache namespace and retention. No new daemon, spawn hook, learned
router or mandatory model evaluation campaign is introduced. The
[advisor reference](../skills/route-subagents/references/routing-advisor.md)
defines failure, configuration migration and rollback behavior.

## Guarded lifecycle

`python tools/assay.py plan` is read-only. For every catalogued target it reports
the expected link destination or adapter hash, the current state and the exact
rollback target. `install-links` preflights the whole plan and accepts only a
missing target or an exact existing projection; a real directory, a foreign link,
a modified adapter or a reparse-point parent stops the entire run before the first
write.

Creation is idempotent. If a write fails, only entries created by that invocation
are removed, and only after their identity is rechecked. `uninstall-links`
preflights the same way and removes only exact links or adapter bytes: a missing
target is harmless, and drift is preserved and reported rather than overwritten.

Windows uses the native directory-symlink API and fails closed when the process
lacks that permission. There is no shell fallback in which a path could be
reinterpreted as syntax.

The lifecycle has no archive, package hash, install-state database, mutation lock
or journal. Its authority is the current catalog and source revision, which is why
an adapter installed by an older revision must be removed with that revision
before a newer one installs its own.

## Upgrade and rollback

An upgrade uses two revisions: run `uninstall-links` from the revision that created
the current adapters, then `install-links` from the new one. Before a live install
or removal, capture the affected source bytes and the observed target vector
outside the managed roots, including any existing drift, and keep that snapshot
until both clients have been exercised.

Rollback restores the exact recorded targets from that snapshot. It never mixes an
old source with a new registration, and it preserves unrelated drift instead of
flattening it to make a preflight pass. A state file living beside the installation
is not a backup of it.

[Upgrading a linked install](how-to/upgrade-linked-install.md) is that sequence
as a procedure, with the snapshot step first and the restore step last.

## Gates

```text
python -B tools/check.py --all
```

That one command runs every gate and reports each rather than stopping at the
first failure: the source check, the `tools/` unit suite, the compatibility
fixture, the generated catalog document, the evaluation data, the rendered
client files, the audit-packet suite and the preservation fixtures. `make check`
is the same command, and it creates the scratch directory the audit-packet suite
needs. To run one gate alone, the list lives in `tools/check.py`.

These prove source structure, plan determinism, guarded install and uninstall
semantics, and adapter capabilities. They cannot prove that a client discovered a
skill or that a sandbox was effective; that needs a run in a fresh client, and the
evaluation notes say what such a run does and does not establish.
