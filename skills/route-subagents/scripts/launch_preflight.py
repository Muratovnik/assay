"""Local fallback argument check; no advisor, network, telemetry or launch permit."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys

from route_evidence.client_capabilities import claude_overrides, contract, codex_route_check
from route_evidence.core import MAX_BYTES, EvidenceError, loads, read_document, text
from route_evidence.routing import validate_request

CODEX_ARGUMENTS = {"reasoning_effort", "model_reasoning_effort", "fork_turns", "agent_type"}
CLAUDE_ARGUMENTS = {"model", "effort", "subagent_type"}


class RouteRefuted(EvidenceError):
    """The declared arguments resolve to a route other than the selected one."""


def _first(layers):
    return next(((source, value) for source, value in layers if value is not None), (None, None))


def _codex_context(launch, properties):
    fork = launch.get("fork_turns", "all")
    if "fork_turns" in launch and "fork_turns" not in properties:
        raise EvidenceError("codex_context_field_not_exposed")
    if fork in ("none", "all"):
        return fork
    count = int(fork) if isinstance(fork, str) and fork.isdigit() else fork
    if type(count) is int and count > 0:
        return "recent"
    raise EvidenceError("codex_context_control_not_supported_by_this_preflight")


def _bound_definition(definition, launch, field, code):
    # A definition applies only when the call selects it by name, and a selected
    # type may pin settings the caller has to declare.
    if definition or field in launch:
        if not isinstance(definition.get("name"), str) or definition["name"] != launch.get(field):
            raise EvidenceError(code)


def check(document, *, environment=None):
    allowed = {"client", "mode", "failure", "packet_id", "available", "selected", "basis",
               "launch", "tool_schema", "spawn_fields", "definition", "defaults", "parent",
               "host", "inheritance_reason"}
    if not isinstance(document, dict) or set(document) - allowed:
        raise EvidenceError("invalid_fallback_preflight_fields")
    client = document.get("client")
    if client not in {"codex", "claude"} or document.get("mode") not in {"required", "evidence-only"}:
        raise EvidenceError("fallback_requires_client_and_mode")
    if document["mode"] == "required":
        raise EvidenceError("required_routing_needs_registered_launch_not_local_fallback")
    if document.get("failure") not in {"approval_rejected", "service_unavailable"}:
        raise EvidenceError("invalid_failure_for_local_fallback")
    packet = text(document.get("packet_id"), "packet_id")
    basis = document.get("basis")
    if not isinstance(basis, dict) or set(basis) != {"source", "reason"} or basis["source"] not in {"user", "task"}:
        raise EvidenceError("fallback_requires_deliberate_selection_basis")
    text(basis["reason"], "selection_reason")
    selected = document.get("selected")
    if not isinstance(selected, dict) or set(selected) != {"model", "effort"}:
        raise EvidenceError("fallback_requires_selected_model_and_effort")
    if any(not isinstance(value, str) or value in {"inherit", "auto"} for value in selected.values()):
        raise EvidenceError("fallback_requires_literal_selected_settings")
    validate_request({"client": client, "task_types": ["investigation"], "available": document.get("available")})
    if not any(selected == {"model": row["model"], "effort": level}
               for row in document["available"] for level in row["efforts"]):
        raise EvidenceError("fallback_selection_not_in_current_inventory")
    launch = document.get("launch")
    if not isinstance(launch, dict):
        raise EvidenceError("fallback_requires_launch_arguments")
    # This input intentionally excludes execution prompts and private task text.
    if set(launch) - {"model", "effort"} - CODEX_ARGUMENTS - CLAUDE_ARGUMENTS:
        raise EvidenceError("preflight_accepts_routing_arguments_only")
    schema = document.get("tool_schema")
    fields = document.get("spawn_fields")
    definition, parent, defaults = document.get("definition", {}), document.get("parent", {}), document.get("defaults", {})
    for value in (definition, parent, defaults):
        if not isinstance(value, dict):
            raise EvidenceError("invalid_fallback_configuration")
    if (not isinstance(schema, dict) or not isinstance(schema.get("properties"), dict)
            or not isinstance(fields, dict) or set(fields) != {"model", "effort"}
            or any(value is not None and (not isinstance(value, str) or not value) for value in fields.values())):
        raise EvidenceError("fallback_requires_current_tool_schema_and_field_binding")
    properties = schema["properties"]
    if client == "codex":
        bound = {field for field in fields.values() if field is not None}
        if set(launch) - bound - {"fork_turns", "agent_type"}:
            raise EvidenceError("codex_launch_argument_not_bound")
        context = _codex_context(launch, properties)
        _bound_definition(definition, launch, "agent_type", "codex_definition_type_mismatch")
        if context == "all" and bound & set(launch):
            raise EvidenceError("full_history_cannot_express_route_overrides")
        result = codex_route_check(selected, launch, definition=definition, defaults=defaults,
                                   parent=parent, tool_schema=schema, spawn_fields=fields)
        inherited = context == "all" or any(
            (field is None or field not in launch) and config_field not in definition and config_field not in defaults
            for part, config_field in (("model", "model"), ("effort", "model_reasoning_effort"))
            for field in [fields[part]])
    else:
        if launch.get("subagent_type") == "fork":
            raise EvidenceError("claude_fork_requires_parent_route_not_local_fallback")
        if set(launch) & CODEX_ARGUMENTS:
            raise EvidenceError("codex_arguments_are_not_claude_controls")
        if fields["model"] != "model" or fields["effort"] not in {None, "effort"}:
            raise EvidenceError("invalid_claude_spawn_field_binding")
        if "effort" in launch and not contract(client, document.get("host"))["per_call_effort"]:
            raise EvidenceError("claude_per_call_effort_not_supported")
        if "effort" in launch and fields["effort"] is None:
            raise EvidenceError("claude_effort_field_not_bound")
        from route_evidence.claude_agents import CLAUDE_MODEL_ALIASES
        if "model" in launch and launch["model"] not in CLAUDE_MODEL_ALIASES:
            raise EvidenceError("claude_call_model_requires_native_alias")
        for field in (value for value in fields.values() if value is not None):
            spec = properties.get(field)
            choices = spec.get("enum") if isinstance(spec, dict) else None
            if (not isinstance(spec, dict) or (choices is not None and not isinstance(choices, list))
                    or (field in launch and choices is not None and launch[field] not in choices)):
                raise EvidenceError("claude_route_field_not_exposed")
        _bound_definition(definition, launch, "subagent_type", "claude_definition_type_mismatch")
        # Documented precedence: model is call, definition (inherit means the
        # parent's), CLAUDE_CODE_SUBAGENT_MODEL, then parent; the effort
        # environment variable outranks call and definition.
        env = os.environ if environment is None else environment
        env_model = env.get("CLAUDE_CODE_SUBAGENT_MODEL") or None
        env_effort = env.get("CLAUDE_CODE_EFFORT_LEVEL") or None
        if definition.get("model") == "inherit":
            model = _first([("call", launch.get("model")), ("parent", parent.get("model"))])
        else:
            model = _first([("call", launch.get("model")), ("definition", definition.get("model")),
                            ("environment", None if env_model == "inherit" else env_model),
                            ("parent", parent.get("model"))])
        effort = _first([("environment", None if env_effort == "auto" else env_effort), ("call", launch.get("effort")),
                         ("definition", definition.get("effort")), ("parent", parent.get("effort"))])
        sources = {"model": model, "effort": effort}
        result = {**claude_overrides(selected, env, document.get("host")),
                  "configured": {part: value for part, (_, value) in sources.items()}}
        for part, (_, value) in sources.items():
            if value is None:
                result["unverified"].append(part + "_unresolved")
            elif value != selected[part]:
                result["conflicts"].append(part + "_configuration_override")
        inherited = any(source == "parent" for source, _ in sources.values())
    # A refuted route outranks evidence that is merely missing.
    if result["conflicts"]:
        raise RouteRefuted("fallback_route_conflicting:" + ",".join(sorted(set(result["conflicts"]))))
    if inherited:
        text(document.get("inheritance_reason"), "inheritance_reason")
    if result["unverified"]:
        raise EvidenceError("fallback_route_unresolved:" + ",".join(sorted(set(result["unverified"]))))
    return {"status": "arguments_checked", "packet_id": packet, "configured": result["configured"],
            "selection_source": basis["source"], "failure": document["failure"],
            "launch_verified": False, "observed_model": None, "observed_effort": None,
            "authorization_granted": False}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", required=True, help="routing-only JSON file, or - for stdin")
    args = parser.parse_args(argv)
    try:
        document = (loads(sys.stdin.buffer.read(MAX_BYTES + 1).decode("utf-8"))
                    if args.request == "-" else read_document(Path(args.request)))
        result = check(document)
    except RouteRefuted as exc:
        print(json.dumps({"status": "blocked", "outcome": "refuted", "error": str(exc),
                          "authorization_granted": False}))
        return 1
    except (EvidenceError, OSError, UnicodeError, TypeError, ValueError, KeyError, AttributeError,
            RecursionError) as exc:
        # Malformed or incomplete input fails closed and is never a result.
        print(json.dumps({"status": "blocked", "outcome": "unverified", "error": str(exc),
                          "authorization_granted": False}))
        return 2
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
