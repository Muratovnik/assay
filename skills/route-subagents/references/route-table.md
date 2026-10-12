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

## Configuration

The table lives in the client's routing configuration (schema 4), next to
`client` and `pipeline`. Model names are client facts, so they appear only there:

```json
{
  "schema_version": 4,
  "client": "claude",
  "routes": {
    "basis": "FrontierCode 1.1 and CursorBench 4.0, read 2026-10-12; API cost per task, not quota",
    "classes": {
      "gather": {"model": "<model>", "effort": "<effort>", "when": "search and read code or sources, summarize findings"},
      "code":   {"model": "<model>", "effort": "<effort>", "when": "ordinary implementation, fixes and tests"},
      "hard":   {"model": "<model>", "effort": "<effort>", "when": "ambiguous multi-step work and design"}
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
under `routes`, or `{"status": "not_configured"}`.

## Using the table

1. Decide whether to delegate at all. When the work is one dependent chain that
   fits in the primary's context, delegating adds a plan, a handoff and a merge;
   the same work done locally is often cheaper.
2. Read the classes from `routing_status`, or from the refusal that lists them.
3. Choose the class whose `when` fits the packet. Choose by the work, not by
   caution: a stronger class "to be safe" is the inheritance this table removes.
   If no class fits, keep the work local or ask the owner to add one.
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

With a table configured in evidence-only mode, the Assay `PreToolUse` hook checks
every native spawn of a supported client. It refuses a spawn that declares no
class, declares an unknown class, or names a model or effort different from the
class's pair, and a spawn whose settings the client would replace by inheritance
or by an override. The refusal lists the classes with their pairs.

Exemptions are the client's continuation mechanisms and the owner's
`pipeline.unrouted_agents` types. `pipeline.explicit_routes: "off"` turns the
check off. Without a table, a Claude spawn must still name both settings and a
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

Refresh the sources first with `refresh` when the cache is stale; which sources
add new models within days is visible in their `source_updated_at`.

## Frozen alternatives

The [routing advisor](routing-advisor.md), [required routing](required-routing.md)
and [local task evidence](task-evidence.md) remain available to an owner who
enables them, and their contracts are unchanged. They are frozen: not the
default path, not extended, and not used when a table is configured unless the
owner turns them on.
