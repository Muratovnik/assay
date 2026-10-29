# Route table

The route table is the owner's short list of task classes, each with the model
and effort a child of that class launches with. The primary agent decides what
to delegate and which class the work belongs to; the pair follows from the
table. A child therefore neither inherits the session's settings nor carries a
pair chosen ad hoc for one launch.

The table replaces per-launch model ranking as the default because published
benchmarks cannot separate pairs closer than several score points, and a
per-packet adequacy judgment over them did not discriminate in practice. A few
classes with deliberate pairs carry the resolution the data has. The table is
reviewed when a model is released, not recomputed for every launch.

## Contents

- [Configuration](#configuration)
- [Bind the configuration to the hooks](#bind-the-configuration-to-the-hooks)
- [Upgrade from 0.28](#upgrade-from-028)
- [Upgrade from 0.29](#upgrade-from-029)
- [Using the table](#using-the-table)
- [Enforcement](#enforcement)
- [Building and reviewing the table](#building-and-reviewing-the-table)

## Configuration

The table lives in the client's routing configuration (schema 5), next to
`client` and `pipeline`. Model names are client facts, so they appear only there:

```json
{
  "schema_version": 5,
  "client": "claude",
  "routes": {
    "basis": "FrontierCode 1.1 and CursorBench 4.0, read 2026-10-12; API cost per task, not quota",
    "classes": {
      "find":   {"model": "<model>", "effort": "<effort>", "when": "find and read code or sources, summarize findings"},
      "build":  {"model": "<model>", "effort": "<effort>", "when": "ordinary implementation, fixes and tests"},
      "design": {"model": "<model>", "effort": "<effort>", "when": "ambiguous multi-step work and design"}
    }
  }
}
```

- 1–16 classes. A class name is lowercase letters, digits and hyphens, starting
  with a letter; no underscore, because a Codex task name continues with one.
- `model` is a value the client's spawn call accepts; `inherit` is refused.
- `effort` is a level the client documents. A placeholder such as `default`,
  `auto`, `inherit` or `unspecified` is refused.
- `when` tells the primary which work the class covers. `basis` records the
  evidence and date behind the pairs.

An invalid table is a configuration error. `routing_status` returns the table
under `routes`, or `{"status": "not_configured"}`. It rereads the configuration
file on every call, as the hook does on every launch, so an edited table shows
without restarting the MCP server. If an edit leaves the file invalid,
`routing_status` keeps showing the last valid table and reports the error under
`configuration.error`.

A schema 5 configuration accepts only these top-level keys: `schema_version`,
`client`, `preferences`, `inventory`, `pipeline` and `routes`. `pipeline` accepts
`mode` (only `evidence-only`), `explicit_routes` (`require`, the default, or
`off`), `unrouted_agents`, `host`, `inventory_file` and `inventory_ttl_hours`.
`unrouted_agents` is a list of agent-type names (default `[]`): letters, digits and
`_.:-`, no `assay-` prefix, no duplicates, at most 64. The object form that
mapped a type to a model is refused. Any other key is an error. A configuration that carries a section or key of the
removed routing advisor, required mode or execution telemetry, or an older
`schema_version`, is refused with one message that lists the keys to remove and
the version to set; there is no migration command.

## Bind the configuration to the hooks

The Assay hooks find the configuration in one of two ways:

- `ASSAY_ROUTING_CONFIG` holds the absolute path of the configuration file and is
  used when set.
- Otherwise the binding file `routing.json` in the plugin's data directory
  (`PLUGIN_DATA` or `CLAUDE_PLUGIN_DATA`) names it:

```json
{"config": "/absolute/path/to/routing.json", "cache_dir": "/absolute/path/to/benchmark-evidence"}
```

Both values are absolute paths without links, and no other key is allowed.
`config` is the configuration file. `cache_dir` is where Claude host observations
are written (see [observed alias resolutions](claude-code-routing.md#observed-alias-resolutions));
`routing_status` reads them from the benchmark cache of the MCP server, so use the
same directory as that server's `--cache-dir`. Observations are written only when
the binding exists; `ASSAY_ROUTING_CONFIG` alone records none.

With neither a binding nor `ASSAY_ROUTING_CONFIG`, no launch is checked. To see
which of them the hooks found, run `python -I -B hooks/runtime/cli.py doctor
--client claude`: it reports `routing_binding_found` and `routing_config_found`.

## Upgrade from 0.28

0.28 and earlier shipped a routing advisor, a required routing mode, execution
history and telemetry, and feedback capture. They no longer exist, and their
settings are refused by name, not ignored, so an old setup stops launches until
it is changed:

1. In the plugin's data directory rename `routing-telemetry.json` to
   `routing.json`; its `config` and `cache_dir` stay as they are. While the old
   name is the only one present, route-table launches are refused with a message
   naming the rename. `ASSAY_ROUTING_TELEMETRY_CONFIG` is refused when set: use
   the binding file or `ASSAY_ROUTING_CONFIG`.
2. In the routing configuration set `schema_version` to 5 and delete the sections
   `advisor`, `policy`, `telemetry` and `task_evidence`, and the `pipeline` keys
   `state_dir`, `agents_dir`, `mcp_server`, `advisor_route`, `profiles`,
   `variants`, `baseline`, `approved_choices`, `profile_capabilities` and
   `agent_templates`. `pipeline.mode` accepts only `evidence-only`.
3. In the hook configuration (`ASSAY_HOOK_CONFIG`) delete `record_events`,
   `feedback_capture` and `feedback_trigger`; a hook configuration that still names
   one is refused with a message listing it (`docs/how-to/hooks.md` in the Assay
   repository).
4. The MCP tools `prepare_routing`, `get_advisor_input`, `complete_routing`,
   `get_routing_decision`, `authorize_routing_launch` and `record_routing_outcome`,
   the `claude-routes` command and the history and telemetry commands of
   `benchmark_router.py` are gone. History and telemetry files an earlier release
   wrote are no longer read.
5. Delete the agent definitions that `claude-routes` generated: the files
   `assay-<profile>-<effort>-<hash>.md`, the `.assay-routing-v2.json` ownership
   manifest and the `.assay-routing-v2.lock` file in the directory that
   `pipeline.agents_dir` named. Nothing removes them now. Their frontmatter calls
   `routing_hook.py`, which no longer does anything for them, so a leftover file is
   harmless but no longer routes.

## Upgrade from 0.29

`pipeline.unrouted_agents` takes only a list of agent types. The launch check
never used the model an object form attached to a type, so that form was
removed in schema 5 and a configuration that still has it, `{}` included, refuses
launches with a message naming the change. Replace the object with the list of
its keys: `{}` becomes `[]` and `{"Explore": "inherit"}` becomes `["Explore"]`.

## Using the table

1. Decide whether to delegate at all. When the work is one dependent chain that
   fits in the primary's context, delegating adds a plan, a handoff and a merge;
   the same work done locally is often cheaper.
2. Read the classes from `routing_status`, or from the refusal that lists them.
3. Choose the class whose `when` fits the packet. Choose by the work, not by
   caution and not by a pair chosen beforehand: a stronger class "to be safe" is
   the inheritance this table removes. When two classes fit, take the less
   demanding one; a stronger class needs a reason in the work itself, such as
   real ambiguity or design. If no class fits, keep the work local or ask the
   owner to add one. State in one line, with the launch, why the work fits the
   class.
4. Launch with that class's model and effort in the spawn call itself, and
   declare the class at the start of the call's short label field. The field
   and the inheritance rules are client mechanics:
   [Claude Code](claude-code-routing.md#route-table-launches),
   [Codex](codex-routing.md#route-table-launches).
5. A model or effort the user explicitly chose for a child wins over the table.
   Launch it through an owner-exempt agent type, or tell the user the hook will
   refuse it until the owner exempts the type or adds a class.

When a child's result needed rework at a stronger pair, record that with the
outcome; repeated rework in one class is the signal to review its pair.

## Enforcement

With a table configured, the Assay `PreToolUse` hook checks
every native spawn of a supported client. It refuses a spawn that declares no
class, declares an unknown class, or names a model or effort different from the
class's pair, and a spawn whose settings the client would replace by inheritance
or by an override. The refusal lists the classes with their pairs and the rule
for choosing one. An admitted launch gets a short note naming its class and
asking for the one-line reason; nothing checks that the reason is written.

If a configured routing file or the routing binding cannot be read or validated,
the hook refuses recognized launches; a configuration written for an older
schema or a binding left under its old name is refused with a message that says
what to change. With no binding or routing configuration,
ordinary delegation remains available. This refusal requires the host to invoke
the trusted hook: a disabled, skipped or broken handler is not a verified guard.

Exemptions are the client's continuation mechanisms and the owner's
`pipeline.unrouted_agents` types. `pipeline.explicit_routes: "off"` turns the
check off. A spawn the check skips for either reason gets a short pointer to the
table instead of the generic launch reminder. Without a table, a Claude spawn must still name both settings and a
Codex spawn is not checked.

Clients differ in what they allow:

| Level | Client capability | Table role |
| --- | --- | --- |
| Enforced | The spawn call carries model and effort, and a pre-tool hook sees it | The hook refuses deviations (Claude Code, Codex) |
| Advisory | The spawn call carries both, but no hook sees it | The primary follows the table; nothing verifies the launch |
| Configured | Only an agent definition can set the model | Write one definition per class from the table and spawn by its name |

## Building and reviewing the table

The owner approves the table. To propose pairs from cached measurements, run
`route-candidates`; it reads only the local benchmark cache:

```text
python skills/route-subagents/scripts/benchmark_router.py --cache-dir CACHE route-candidates --source frontiercode --subset main --harness claude-code
```

Each row shows a measured pair's score and published cost, whether it is on the
cost/score frontier, whether it is within `--band` (default 0.07) of the best
score, and the proposal: the cheapest pair inside that band. The band states the
resolution a table without intervals can support; it is not a measured margin.
Map each class to the benchmark that resembles its work, and keep a class
provisional when no benchmark measures it. Published costs are API prices, not
subscription quota.

`--harness` matches by lexical identity, so `claude-code` also selects a board
that prints "Claude Code". A board that publishes only run totals, such as
Terminal-Bench, is priced per attempt: run total divided by its sample count,
and only when every priced row ran the same number of attempts; otherwise the
result is `no_measured_pairs` with `reason: run_totals_differ_in_sample_count`.
A zero run total is not a cost. `cost_basis` names which cost the rows carry,
and published per-task costs are never mixed with derived ones. This derivation
serves the owner's review here only; routing context keeps run totals out of
per-task expense comparisons.

Refresh the sources first with `refresh` when the cache is stale; which sources
add new models within days is visible in their `source_updated_at`.
