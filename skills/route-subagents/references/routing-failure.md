# Routing rejected or unavailable

Read this before launching after a failed recommendation request. Delegation
authorization and permission for the failed data operation remain separate.

## Establish what failed

A request rejected before execution produced no advisor recommendation. Report
the actual failure and distinguish approval rejection, unavailable service,
invalid input/advice and valid advisor abstention. Invalid input or advice needs
correction through the existing workflow; it does not authorize fallback. A valid
abstention keeps that workflow's eligible baseline rules.

Respect an approval rejection. Do not repeat the rejected operation through CLI,
another endpoint, provider or changed telemetry settings. Where useful, verify
the actual registration and local/remote data boundary without resubmitting the
private payload. Explain the rejected action and stated reason; ask for the
missing permission only if that action remains necessary. An enabled telemetry
setting is not evidence of consent or a reason to select a more expensive model.

## Choose the next authorized action

In required mode, only the registered decision/launch contract can recover the
failure. Do not replace it with this procedure, a direct native call or local work
when the user required delegation.

In evidence-only mode, continue unaffected local work. Launch an exception only
after deliberately selecting both settings for each packet from the complete
current inventory, preserving hard constraints and actual human choices. State
the task-specific sufficiency, verification and relevant cost/uncertainty basis
before dispatch. A service failure, parent setting, profile name or generic
"strongest model" statement supplies no such basis. Do not silently choose the
cheapest pair either. A maximum effort may be appropriate when the work or the
human's explicit choice justifies it.

If no supported, justified pair is known, do not launch that packet. Continue
permitted local work or report the exact selection/capability blocker. Do not
change the primary's settings or client-wide defaults to route one child.

## Check the native arguments locally

Use `scripts/launch_preflight.py --request <routing-only.json>` (relative to this
skill) with the declared client and actual mode. The command reads JSON and
prints a result; it does not contact the routing service, acquire benchmarks,
retain descriptions, create telemetry, grant permission or launch a model. It is
an argument check, not a replacement recommendation or a host receipt. Use it
only if the local read itself is permitted. Keep the input task-owned and ignored,
or pass JSON through stdin with `--request -`; omit prompts, repository contents,
paths to private artifacts and the denied payload. A short selection reason is
enough here; keep detailed evidence in the existing task record.

Supply `client`, `mode: "evidence-only"`, `failure: "approval_rejected"` or
`"service_unavailable"`, `packet_id`, `available`, a complete `selected` pair,
`basis: {"source": "task"|"user", "reason": "..."}`, routing-only `launch`
arguments, the current `tool_schema` and semantic `spawn_fields` binding. `user`
means the human actually specified this pair; it is not a configuration label.
The check validates presence and argument consistency, not whether a prose reason
is true, whether the inventory is complete or whether task adequacy was proved.

For example, a fictional Codex host exposes a suitable `worker-model` and the
task's bounded review justifies `medium`. This is illustrative, not a default:

```json
{
  "client": "codex", "mode": "evidence-only", "failure": "approval_rejected",
  "packet_id": "review",
  "available": [{"model": "worker-model", "efforts": ["low", "medium", "high"]}],
  "selected": {"model": "worker-model", "effort": "medium"},
  "basis": {"source": "task", "reason": "Bounded review with frozen acceptance receipts and direct verification."},
  "launch": {"model": "worker-model", "reasoning_effort": "medium", "fork_turns": "none"},
  "tool_schema": {"properties": {"model": {}, "reasoning_effort": {"enum": ["low", "medium", "high"]}, "fork_turns": {}}},
  "spawn_fields": {"model": "model", "effort": "reasoning_effort"}
}
```

For Codex use its actual exposed field names; a launch argument the binding does
not name is rejected. `fork_turns` must be exposed when passed: `"none"` or a
positive recent-turn count accepts explicit fields, while an omitted value or
`"all"` inherits and cannot express overrides. An `agent_type` needs a
`definition` whose `name` matches it, with the model or `model_reasoning_effort`
that role pins, because a custom agent overrides the call. Supply `defaults`
config metadata when it applies. Deliberate inheritance needs `parent` config
metadata (`model`, `model_reasoning_effort`), matching selected settings and a
concrete `inheritance_reason`. A self-contained packet with explicit supported
fields is normally simpler.

For Claude use `launch.model` with a supported native alias. On CLI 2.1.292+
with the field exposed, bind effort to `effort`, supply `host` with current
`surface` and `version`, and pass `launch.effort`. On older/other schemas bind
effort to `null` and supply the selected definition's checked `name`, `model`
when pinned and `effort` in `definition`. A `subagent_type` always needs that
`definition`, its name matching; a definition the call does not select is
rejected. `subagent_type: "fork"` inherits the parent and is not a fallback
route. Definition and parent metadata must come from the actual selected source,
not an invented assertion. The check resolves the documented precedence: model
from the call, the definition (`inherit` means the parent's),
`CLAUDE_CODE_SUBAGENT_MODEL`, then the parent; effort from
`CLAUDE_CODE_EFFORT_LEVEL`, the call, the definition, then the parent. It reads
those variables from its own process, so run it from the session's shell; it
rejects conflicts and leaves `auto` or a forced model without a value
unresolved. Deliberate session inheritance also needs matching `parent` metadata
and `inheritance_reason`. Discovery, permissions and effective runtime still
need native evidence. Follow [Claude mechanics](claude-code-routing.md) for that
client; a Codex field is not a Claude control.

Exit 0 with `status: "arguments_checked"` means the declared route can be
expressed by those arguments. Exit 1 with `outcome: "refuted"` means the
arguments or declared configuration resolve to a different model or effort.
Exit 2 with `outcome: "unverified"` means invalid, incomplete or unsupported
input, or a setting that stays unresolved. Both blocked outcomes mean no launch,
and neither success nor failure grants authorization. Launch with the checked routing arguments unchanged
and the bounded packet only after the selection and permissions are established.
Record the failure and manual selection in the existing task record, marking
advisor recommendation and runtime observations absent. If telemetry recording
was the rejected operation, do not send the record there without its own
permission. Resume normal recommendation workflow when the failure is resolved.

Evidence-only hooks deliver this procedure as a reminder before each native
launch, and at session start only where routing is configured. They do not
force a native caller to run the preflight. Codex has no verified strict routing adapter;
Claude required mode retains its existing host gate. Do not claim that a passed
argument check prevents a caller from launching outside this procedure.
