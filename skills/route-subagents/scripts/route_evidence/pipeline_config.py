"""Client-side routing contract. Runtime choices never enter neutral profiles."""
from __future__ import annotations

import copy
import re
import time
from pathlib import Path
from typing import Any

from .core import EvidenceError, RetiredConfiguration, epoch, is_reparse, read_document

EFFORT_ORDER = ("low", "medium", "high", "xhigh", "max")
# The launch check is the only mode left; the key stays so a configuration says
# which contract it was written for.
MODES = frozenset({"evidence-only"})
EXPLICIT_ROUTES = frozenset({"require", "off"})
KEYS = frozenset({"mode", "explicit_routes", "unrouted_agents", "host", "inventory_file", "inventory_ttl_hours"})
# Keys of the removed required mode. A configuration that still names one is
# refused with the list instead of the generic unknown-key error.
REMOVED_KEYS = ("state_dir", "agents_dir", "mcp_server", "advisor_route", "profiles", "variants", "baseline",
                "approved_choices", "profile_capabilities", "agent_templates")
UNROUTED_OBJECT_REMOVED = (
    "pipeline.unrouted_agents takes only a list of agent types since schema 5; the object form that mapped a type "
    "to a model was removed because the launch check never used the model. Replace it with the list of its agent "
    "types, for example {} with [] and {\"Explore\": \"inherit\"} with [\"Explore\"]")
AGENT_TYPE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}\Z")
DEFAULT_INVENTORY_TTL_HOURS = 24
MAX_INVENTORY_TTL_HOURS = 720


def _absolute(value: Any, code: str) -> str | None:
    if value is not None and (not isinstance(value, str) or not value or not Path(value).is_absolute()):
        raise EvidenceError(code)
    return value


def _unrouted(value: Any) -> list[str]:
    """Owner-exempt native agent types: a list of type names, nothing else.

    The launch check only asks whether a type is listed. The object form that
    mapped a type to a model served the removed advisor and was never read
    afterwards, so it is refused as a retired configuration, `{}` included.
    """
    if isinstance(value, dict):
        raise RetiredConfiguration(UNROUTED_OBJECT_REMOVED)
    if not isinstance(value, list) or len(value) > 64 or len(set(map(str, value))) != len(value):
        raise EvidenceError("invalid_pipeline_unrouted_agents")
    for name in value:
        if not isinstance(name, str) or not AGENT_TYPE.fullmatch(name) or name.startswith("assay-"):
            raise EvidenceError("invalid_pipeline_unrouted_agents")
    return list(value)


def removed_keys(raw: Any) -> list[str]:
    """Dotted names of required-mode settings a `pipeline` block still carries."""
    if not isinstance(raw, dict):
        return []
    found = ["pipeline." + key for key in REMOVED_KEYS if key in raw]
    if raw.get("mode") == "required":
        found.insert(0, "pipeline.mode=required")
    return found


def settings(config: dict | None = None) -> dict:
    """Normalized launch-check settings; an absent block is the default check."""
    config = config or {}
    raw = config.get("pipeline", {})
    if not isinstance(raw, dict) or set(raw) - KEYS:
        raise EvidenceError("unknown_pipeline_configuration")
    value = {"mode": "evidence-only", "unrouted_agents": [], "inventory_file": None,
             "inventory_ttl_hours": DEFAULT_INVENTORY_TTL_HOURS, "host": None,
             "explicit_routes": "require", **copy.deepcopy(raw)}
    from .client_capabilities import host_settings
    value["host"] = host_settings(value["host"])
    if not isinstance(value["mode"], str) or value["mode"] not in MODES:
        raise EvidenceError("invalid_pipeline_mode")
    # A Claude launch without a model and an effort is refused unless the owner
    # turns that off.
    if not isinstance(value["explicit_routes"], str) or value["explicit_routes"] not in EXPLICIT_ROUTES:
        raise EvidenceError("invalid_pipeline_explicit_routes")
    _absolute(value["inventory_file"], "pipeline_paths_must_be_absolute")
    ttl = value["inventory_ttl_hours"]
    if type(ttl) not in (int, float) or not 1 <= ttl <= MAX_INVENTORY_TTL_HOURS:
        raise EvidenceError("invalid_pipeline_inventory_ttl")
    value["unrouted_agents"] = _unrouted(value["unrouted_agents"])
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
