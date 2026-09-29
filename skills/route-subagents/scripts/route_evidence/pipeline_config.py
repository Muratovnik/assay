"""Client-side routing contract. Runtime choices never enter neutral profiles."""
from __future__ import annotations

import copy
import os
import re
import time
from pathlib import Path
from typing import Any

from .core import EvidenceError, epoch, is_reparse, read_document

PROTOCOL = 3
ROOT_TOOLS = frozenset({"prepare_routing", "get_routing_decision", "authorize_routing_launch", "record_routing_outcome"})
ADVISOR_TOOLS = frozenset({"get_advisor_input", "complete_routing"})
ROUTING_TOOLS = ROOT_TOOLS | ADVISOR_TOOLS
EFFORT_ORDER = ("low", "medium", "high", "xhigh", "max")
CLAUDE_EFFORTS = frozenset(EFFORT_ORDER)
MODES = frozenset({"evidence-only", "required"})
NAME = re.compile(r"[a-z][a-z0-9-]{0,63}\Z")
AGENT_TYPE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}\Z")
DEFAULT_INVENTORY_TTL_HOURS = 24
MAX_INVENTORY_TTL_HOURS = 720


def pair(value: Any) -> dict[str, str]:
    if not isinstance(value, dict) or set(value) != {"model", "effort"}:
        raise EvidenceError("pipeline_route_requires_model_and_effort")
    if (not isinstance(value["model"], str) or not value["model"].strip()
            or value["model"] != value["model"].strip() or len(value["model"]) > 200
            or any(ord(c) < 32 for c in value["model"])
            or value["model"] == "inherit" or not isinstance(value["effort"], str)
            or value["effort"] not in CLAUDE_EFFORTS):
        raise EvidenceError("invalid_claude_route")
    return dict(value)


def _absolute(value: Any, code: str) -> str | None:
    if value is not None and (not isinstance(value, str) or not value or not Path(value).is_absolute()):
        raise EvidenceError(code)
    return value


def _unrouted(value: Any) -> dict:
    """Owner-exempt native agent types and the model each one launches with.

    A list names types that use the baseline model. An object maps a type to
    "baseline", "inherit" (the parent's model, as an explicit choice) or
    {"model": ID}. Generated routed definitions are never exempt.
    """
    if isinstance(value, list):
        if any(not isinstance(name, str) for name in value) or len(set(value)) != len(value):
            raise EvidenceError("invalid_pipeline_unrouted_agents")
        value = {name: "baseline" for name in value}
    if not isinstance(value, dict) or len(value) > 64:
        raise EvidenceError("invalid_pipeline_unrouted_agents")
    result = {}
    for name, spec in value.items():
        if not isinstance(name, str) or not AGENT_TYPE.fullmatch(name) or name.startswith("assay-"):
            raise EvidenceError("invalid_pipeline_unrouted_agents")
        if isinstance(spec, dict):
            if set(spec) != {"model"}:
                raise EvidenceError("invalid_pipeline_unrouted_agent_model")
            model = spec["model"]
            if (not isinstance(model, str) or not model or model != model.strip() or len(model) > 200
                    or any(ord(c) < 32 for c in model) or model == "inherit"):
                raise EvidenceError("invalid_pipeline_unrouted_agent_model")
            spec = {"model": model}
        elif spec not in ("baseline", "inherit"):
            raise EvidenceError("invalid_pipeline_unrouted_agent_model")
        result[name] = spec
    return result


def settings(config: dict | None = None) -> dict:
    """Normalized pipeline settings. Absent configuration is the 0.8.0 workflow.

    Required routing is opt-in: only an explicit `pipeline.mode: "required"`
    enables the host guard. No configuration, a v1/v2 file or a v3 file without
    a mode keeps the evidence-only workflow, including the root-mediated advisor.
    """
    config = config or {}
    raw = config.get("pipeline", {})
    keys = {"mode", "state_dir", "agents_dir", "mcp_server", "advisor_route", "profiles", "variants", "baseline",
            "approved_choices", "profile_capabilities", "unrouted_agents", "agent_templates",
            "inventory_file", "inventory_ttl_hours", "host"}
    if not isinstance(raw, dict) or set(raw) - keys:
        raise EvidenceError("unknown_pipeline_configuration")
    value = {"mode": "evidence-only", "state_dir": None, "agents_dir": None,
             "mcp_server": "assay-benchmark-routing", "advisor_route": None, "profiles": [],
             "variants": [], "baseline": None, "approved_choices": {}, "profile_capabilities": {},
             "unrouted_agents": {}, "agent_templates": {}, "inventory_file": None,
             "inventory_ttl_hours": DEFAULT_INVENTORY_TTL_HOURS, "host": None, **copy.deepcopy(raw)}
    from .client_capabilities import host_settings
    value["host"] = host_settings(value["host"])
    if not isinstance(value["mode"], str) or value["mode"] not in MODES:
        raise EvidenceError("invalid_pipeline_mode")
    if not isinstance(value["mcp_server"], str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", value["mcp_server"]):
        raise EvidenceError("invalid_pipeline_mcp_server")
    for key in ("state_dir", "agents_dir", "inventory_file"):
        _absolute(value[key], "pipeline_paths_must_be_absolute")
    ttl = value["inventory_ttl_hours"]
    if type(ttl) not in (int, float) or not 1 <= ttl <= MAX_INVENTORY_TTL_HOURS:
        raise EvidenceError("invalid_pipeline_inventory_ttl")
    if value["baseline"] is not None:
        value["baseline"] = pair(value["baseline"])
    route = value["advisor_route"]
    if route is not None:
        from .advisors.native import _validate_basis
        if not isinstance(route, dict) or set(route) != {"model", "effort", "selection_basis"}:
            raise EvidenceError("invalid_pipeline_advisor_route")
        pair({k: route[k] for k in ("model", "effort")})
        _validate_basis(route["selection_basis"])
    profiles = value["profiles"]
    # Profiles routed with the model in the Agent call and effort in a
    # generated definition; `variants` pin a model the call cannot express.
    if (not isinstance(profiles, list) or len(profiles) > 32 or len(set(map(str, profiles))) != len(profiles)
            or any(not isinstance(p, str) or not NAME.fullmatch(p) for p in profiles)):
        raise EvidenceError("invalid_pipeline_profiles")
    variants = value["variants"]
    if not isinstance(variants, list) or len(variants) > 100:
        raise EvidenceError("invalid_pipeline_variants")
    seen = set()
    for variant in variants:
        if not isinstance(variant, dict) or set(variant) != {"profile", "model", "effort"}:
            raise EvidenceError("invalid_pipeline_variant")
        if not isinstance(variant["profile"], str) or not NAME.fullmatch(variant["profile"]):
            raise EvidenceError("invalid_pipeline_profile")
        pair({k: variant[k] for k in ("model", "effort")})
        key = tuple(variant[k] for k in ("profile", "model", "effort"))
        if key in seen:
            raise EvidenceError("duplicate_pipeline_variant")
        seen.add(key)
    choices = value["approved_choices"]
    if not isinstance(choices, dict) or len(choices) > 100:
        raise EvidenceError("invalid_pipeline_approved_choices")
    for key, choice in choices.items():
        if not isinstance(key, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}", key):
            raise EvidenceError("invalid_pipeline_choice_id")
        pair(choice)
    capabilities = value["profile_capabilities"]
    if not isinstance(capabilities, dict) or len(capabilities) > 100:
        raise EvidenceError("invalid_pipeline_profile_capabilities")
    for profile, names in capabilities.items():
        if (not isinstance(profile, str) or not NAME.fullmatch(profile)
                or not isinstance(names, dict) or len(names) > 32):
            raise EvidenceError("invalid_pipeline_profile_capabilities")
        for name, supported in names.items():
            if (not isinstance(name, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:+/-]{0,127}", name)
                    or (supported is not None and type(supported) is not bool)):
                raise EvidenceError("invalid_pipeline_profile_capability")
    value["unrouted_agents"] = _unrouted(value["unrouted_agents"])
    templates = value["agent_templates"]
    if not isinstance(templates, dict) or len(templates) > 32:
        raise EvidenceError("invalid_pipeline_agent_templates")
    for profile, path in templates.items():
        if not isinstance(profile, str) or not NAME.fullmatch(profile):
            raise EvidenceError("invalid_pipeline_agent_template_profile")
        if path is None:
            raise EvidenceError("pipeline_paths_must_be_absolute")
        _absolute(path, "pipeline_paths_must_be_absolute")
    return value


def configured_inventory(config: dict) -> dict | None:
    """The owner's dated host inventory: a separate file when configured.

    A separate file lets the owner confirm a current inventory without changing
    the policy configuration that hooks and sessions are bound to.
    """
    path = settings(config)["inventory_file"]
    if path is None:
        inventory = config.get("inventory")
        return copy.deepcopy(inventory) if inventory is not None else None
    if config.get("inventory") is not None:
        raise EvidenceError("inventory_configured_twice")
    location = plain_path(Path(path))
    try:
        inventory = read_document(location)
    except FileNotFoundError as exc:
        raise EvidenceError("configured_inventory_file_missing") from exc
    if not isinstance(inventory, dict) or set(inventory) != {"available", "observed_at"}:
        raise EvidenceError("inventory requires available and actual observed_at")
    from .routing import validate_request
    validate_request({"client": config.get("client", "unconfigured"), "task_types": ["implementation"],
                      "available": inventory["available"]})
    epoch(inventory["observed_at"])
    return inventory


def confirm_inventory(config: dict, available: list | None = None, *, evidence_names=(), clock=time.time) -> dict:
    """The owner's statement that the host offers these models and efforts now.

    Only the separate inventory file changes, so running sessions keep their
    configuration binding. Without `available` the recorded list is kept.
    `evidence_names` pairs add the owner's confirmed source spellings of a
    listed model; confirmation is the only way a spelling binds benchmark rows.
    """
    path = settings(config)["inventory_file"]
    if path is None:
        raise EvidenceError("inventory_file_not_configured")
    location = plain_path(Path(path))
    if available is None:
        current = configured_inventory(config)
        available = current["available"]
    available = copy.deepcopy(available)
    for model, label in evidence_names:
        entry = next((item for item in available if isinstance(item, dict) and item.get("model") == model), None)
        if entry is None:
            raise EvidenceError("evidence_name_model_not_in_inventory")
        names = entry.setdefault("evidence_names", [])
        if isinstance(names, list) and label not in names:
            names.append(label)
    from .routing import validate_request
    validate_request({"client": config.get("client", "unconfigured"), "task_types": ["implementation"],
                      "available": available})
    location.parent.mkdir(parents=True, exist_ok=True)
    from .cache import atomic_write
    from .core import timestamp
    inventory = {"available": copy.deepcopy(available), "observed_at": timestamp(clock())}
    atomic_write(location, inventory)
    return {"status": "confirmed", "observed_at": inventory["observed_at"],
            "models": len(inventory["available"]), "configuration_changed": False,
            "expires_after_hours": settings(config)["inventory_ttl_hours"]}


def inventory_ttl_seconds(config: dict | None) -> float:
    return float(settings(config)["inventory_ttl_hours"]) * 3600


def plain_path(path: Path) -> Path:
    """Reject linked/reparse ancestors, including a missing path's existing parent."""
    if not path.is_absolute():
        raise EvidenceError("pipeline_path_not_absolute")
    for entry in (path, *path.parents):
        if is_reparse(entry):
            raise EvidenceError("pipeline_linked_path")
    return path


def runtime_overrides(expected: dict, environment: dict | None = None, *, host=None) -> dict:
    """Inspect the environment under a declared client contract; never mutate it."""
    from .client_capabilities import claude_overrides
    return claude_overrides(expected, os.environ if environment is None else environment, host)
