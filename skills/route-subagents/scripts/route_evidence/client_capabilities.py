"""Documented client contracts, not attestations of a running installation.

Keep launch mechanics here, not in neutral skills or model rankings. Unknown
versions/surfaces and unobserved runtime values must remain unknown.
"""
from __future__ import annotations

import re

from .core import EvidenceError

CHECKED_AT = "2026-09-29"
SOURCES = {
    "claude_agents": "https://code.claude.com/docs/en/sub-agents",
    "claude_effort": "https://code.claude.com/docs/en/model-config",
    "claude_hooks": "https://code.claude.com/docs/en/hooks",
    "codex_agents": "https://developers.openai.com/codex/subagents",
    "codex_hooks": "https://developers.openai.com/codex/hooks",
}


def version_tuple(value):
    """Only documented stable x.y.z releases are orderable here, not SemVer."""
    if not isinstance(value, str) or not re.fullmatch(r"[0-9]{1,5}\.[0-9]{1,5}\.[0-9]{1,5}", value):
        return None
    return tuple(map(int, value.split(".")))


def host_settings(raw=None):
    value = {"version": None, "surface": "unknown", "provider": "unknown", "agent_scope": "unknown"}
    if raw is None:
        return value
    if not isinstance(raw, dict) or set(raw) - set(value):
        raise EvidenceError("invalid_client_host_contract")
    value.update(raw)
    if value["version"] is not None and (not isinstance(value["version"], str) or len(value["version"]) > 80):
        raise EvidenceError("invalid_client_version")
    if value["surface"] not in {"cli", "desktop", "ide", "sdk", "unknown"}:
        raise EvidenceError("invalid_client_surface")
    if value["agent_scope"] not in {"user", "project", "plugin", "additional", "cli", "unknown"}:
        raise EvidenceError("invalid_agent_scope")
    provider = value["provider"]
    if not isinstance(provider, str) or not re.fullmatch(r"[a-z][a-z0-9_-]{0,63}", provider):
        raise EvidenceError("invalid_client_provider")
    return value


def contract(client, host=None):
    host = host_settings(host)
    known_surface = host["surface"] == "cli"
    version = version_tuple(host["version"])
    report = {"client": client, "declared_host": host, "checked_at": CHECKED_AT,
              "evidence": "official_documentation", "installed_version_verified": False,
              "surface_verified": False, "version_known": version is not None,
              "configured_is_not_observed": True,
              "observed_model": None, "observed_effort": None,
              "sources": [url for key, url in SOURCES.items() if key.startswith(client + "_")]}
    if client == "claude":
        from .claude_agents import CLAUDE_MODEL_ALIASES
        report.update(per_call_model=sorted(CLAUDE_MODEL_ALIASES), per_call_effort=False, effort_transport="agent_definition",
                      model_transport="call_alias_or_pinned_definition",
                      model_precedence=("call_definition_environment_parent" if known_surface and version and version >= (2, 1, 251)
                                        else "environment_call_definition_parent" if known_surface and version else "unknown"),
                      input_rewrite_requires_allow=False,
                      plugin_ignored_fields=["hooks", "mcpServers", "permissionMode"],
                      strict_adapter="claude" if host["surface"] in {"cli", "unknown"} else None,
                      definition_registry_loaded="unverified", effective_permissions="unverified",
                      observation="event_specific")
    elif client == "codex":
        report.update(per_call_effort=None, effort_transport="inspect_exposed_tool_schema",
                      model_precedence="custom_agent_over_spawn_over_defaults_over_parent",
                      input_rewrite_requires_allow=True, strict_adapter=None,
                      unsupported=["permission_neutral_receipt_injection", "private_native_advisor_return"],
                      uncovered_tools=["hosted WebSearch", "write_stdin continuations", "specialized opt-out paths"])
    else:
        report.update(per_call_effort=None, strict_adapter=None, effort_transport="unknown")
    return report


def claude_overrides(expected, environment, host=None):
    """Resolve known precedence; never turn auto/inherit into literal models."""
    host = host_settings(host)
    version = version_tuple(host["version"]) if host["surface"] == "cli" else None
    problems, unknown = [], []
    effort = environment.get("CLAUDE_CODE_EFFORT_LEVEL")
    if effort == "auto":
        # A model default cannot be equated with the requested level without an
        # observation. Refuse a strict claim rather than inventing a default.
        unknown.append("effort_default_unresolved")
    elif effort and effort != expected["effort"]:
        problems.append("effort_environment_override")
    model = environment.get("CLAUDE_CODE_SUBAGENT_MODEL")
    force = environment.get("CLAUDE_CODE_SUBAGENT_MODEL_FORCE", "").lower() in {"1", "true", "yes"}
    if model == "inherit" and version and version >= (2, 1, 196):
        model = None
    modern = version is not None and version >= (2, 1, 251)
    if force and not model:
        unknown.append("forced_model_unresolved")
    elif model and model != expected["model"] and (force or not modern):
        problems.append("model_environment_override")
    return {"conflicts": problems, "unverified": unknown,
            "observed_model": None, "observed_effort": None}


def codex_route_check(expected, supplied, *, definition=None, defaults=None, parent=None,
                      tool_schema=None, spawn_fields=None):
    """Read-only preflight, never a dispatch permit or automatic config discovery.

    Config keys and native tool argument names are different contracts. Bind the
    latter explicitly from a reviewed exposed tool schema; None means unexposed.
    Without a binding, supplied arguments cannot prove the selected model/effort.
    """
    for value in (expected, supplied, definition, defaults, parent, tool_schema, spawn_fields):
        if value is not None and not isinstance(value, dict):
            raise EvidenceError("invalid_route_preflight_input")
    if not isinstance(expected, dict) or set(expected) != {"model", "effort"} or not isinstance(supplied, dict):
        raise EvidenceError("invalid_route_preflight_contract")
    if any(not isinstance(v, str) or not v or len(v) > 200 for v in expected.values()):
        raise EvidenceError("invalid_route_preflight_contract")
    definition, defaults, parent = definition or {}, defaults or {}, parent or {}
    properties = (tool_schema or {}).get("properties", {})
    if not isinstance(properties, dict):
        raise EvidenceError("invalid_spawn_schema")
    if spawn_fields is not None and (set(spawn_fields) != {"model", "effort"} or any(
            v is not None and (not isinstance(v, str) or not v or len(v) > 128)
            for v in spawn_fields.values())):
        raise EvidenceError("invalid_spawn_field_binding")
    fields = {"model": "model", "effort": "model_reasoning_effort"}
    bindings = spawn_fields or {}
    conflicts, unknown, resolved = [], [], {}
    explicit = {}
    for part in fields:
        field = bindings.get(part)
        if spawn_fields is None:
            unknown.append("spawn_field_binding_unverified:" + part)
        if field is not None:
            if field not in properties:
                conflicts.append("spawn_field_not_exposed:" + field)
            elif field in supplied:
                spec = properties[field]
                if not isinstance(spec, dict):
                    raise EvidenceError("invalid_spawn_schema")
                if "enum" in spec and (not isinstance(spec["enum"], list) or supplied[field] not in spec["enum"]):
                    conflicts.append("spawn_value_not_exposed:" + field)
            if field in supplied:
                explicit[part] = supplied[field]
    for part, config_field in fields.items():
        value = explicit.get(part, defaults.get(config_field, parent.get(config_field)))
        if spawn_fields is None and supplied:
            value = None  # Do not guess semantic names from API/config keys.
        if part == "effort" and part not in explicit and config_field not in defaults and (
                "model" in explicit or "model" in defaults):
            value = None  # A selected model's default is not the parent's.
        value = definition.get(config_field, value)
        resolved[part] = value
        if value is None:
            unknown.append(part + "_unresolved")
        elif value != expected[part]:
            conflicts.append(part + "_configuration_override")
    return {"configured": resolved, "conflicts": conflicts, "unverified": unknown,
            "spawn_fields": spawn_fields, "schema_validation": "selected_routing_fields_only",
            "launch_verified": False, "observed_model": None, "observed_effort": None}
