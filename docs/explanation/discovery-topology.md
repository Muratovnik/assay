# Why one catalogued source reaches several clients

Assay keeps one canonical copy of each skill and each agent profile and gets it
to several agent clients that each read a different directory and, for
profiles, a different file format. This page explains the reasoning behind
that arrangement — why a skill is linked once and reached twice, why profiles
are rendered instead of linked, why there is no `~/.codex/skills` projection,
and what each choice costs. For the commands that produce this layout, see
[the install guide](../install.md); for the layout itself, see
[the architecture note](../architecture.md).

## The problem

`catalog.toml` is the single inventory: it records each asset's ownership,
activation and exact per-client destinations, and nothing else — no model, no
effort level, no runtime state and no machine path. `VERSION` is the only
revision label. Everything a client reads is meant to be produced from those
two files, never edited by hand, because a hand-edited manifest is otherwise
indistinguishable from a correct one until it drifts.

Two kinds of client asset need to reach several clients from that one source:
skills, which every supported client can read as a directory, and agent
profiles, which need a different file format per client. The two are handled
differently, and the difference follows from that distinction.

## Skills: linked once, reached twice

A skill is installed once and reached twice:

```text
~/.agents/skills/<name>   -> <checkout>/skills/<name>
~/.claude/skills/<name>   -> ~/.agents/skills/<name>
```

The first link is the native entry: it points straight at the checkout's
skill directory. The second does not point at a second copy of the skill; it
points at that same native entry. Claude reaches the skill through the shared
native root rather than through its own independent projection.

The repository records this arrangement without recording the reasoning
behind it, so what follows is what it does, not why it was chosen. Every
supported client reads a skill as a plain directory, so one link serves all of
them, and there is no second copy that could go stale. The cost is a
dependency: if the native entry under `~/.agents/skills` is missing or wrong,
Claude's link resolves to nothing, even though nothing about Claude's own
directory looks broken.

## Why there is no `~/.codex/skills` projection

Codex does not need a link into `~/.codex/skills`, because that is not
where it looks. Codex reads `.agents/skills` in the project, walking up to the
repository root, and `~/.agents/skills` for the user account. Its own
`.system` directory is the client's territory and is never managed here. A
projection into `~/.codex/skills` would be extra state pointed at a path
Codex does not read for this purpose — nothing to gain, and one more link the
lifecycle would have to track and verify on every plan, install and uninstall.

## Profiles: rendered, not linked

Agent profiles cannot be linked, because Codex and Claude do not read the
same file format for them:

```text
~/.codex/agents/<profile>.toml   rendered from profiles/<profile>.json
~/.claude/agents/<profile>.md    rendered from profiles/<profile>.json
```

Both destinations are generated from the same JSON source, one file per
client, produced by `tools/assay.py render`. The source check verifies the
rendered bytes match what rendering the current source would produce, so a
hand-edited adapter fails that check instead of silently drifting from the
source it claims to represent — rendering is what makes that check meaningful
at all. The cost of rendering instead of linking is that two on-disk files now
have to stay in step with one source instead of one link doing that
automatically; the source check is what carries that cost instead of leaving
it to be noticed later.

## Profiles as capability boundaries

A profile is a capability boundary, not a role with a model attached: it
carries no model, no effort level, no machine path and no runtime state. Both
rendered adapters ask the client to constrain itself accordingly — the Codex
adapter asks for a read-only sandbox, and the Claude adapter uses plan mode
with a capability-derived tool list.

Only the `evidence-reviewer` profile receives `Bash`, and only because its
declared oracle has to be executable for the review to mean anything; its
instructions still forbid mutating commands, so the added capability is
scoped to running a check, not to changing anything. `official-docs-researcher`
gets no execution capability at all, consistent with a read-only research
role.

That distinction has a limit worth stating plainly: an adapter's requested
sandbox is configuration, not a guarantee. Whether a given session actually
enforced a read-only sandbox is a property of that run, and has to be
verified rather than assumed from the file that requested it. The same is
true one level up — a skill activating automatically is not permission to
delegate to another agent or to mutate anything; that boundary belongs to the
skill's own instructions and the profile's declared capabilities, not to the
fact of being installed.

## What this explanation does not claim

None of the gates described in the architecture note prove that a client
actually discovered an installed skill, or that a requested sandbox was
actually honoured by a session — only a captured run in a fresh client can
speak to either of those. Everything above is read from the repository: it
describes the source and the rendering contract, not an installation anyone
observed working.

## Boundaries

This page explains the discovery topology; it is not the install or upgrade
procedure. For the commands that create, verify or remove these links and
adapters, see [the install guide](../install.md). It does not cover the
guarded lifecycle's preflight and rollback behaviour, or the delegation policy
that `route-subagents` owns — both belong to [the architecture
note](../architecture.md).
