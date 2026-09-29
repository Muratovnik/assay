"""Client-side routing contract. Runtime choices never enter neutral profiles."""
from __future__ import annotations

import copy
import os
import re
from pathlib import Path
from typing import Any

from .core import EvidenceError

PROTOCOL = 2
ROOT_TOOLS = frozenset({"prepare_routing", "get_routing_decision", "authorize_routing_launch", "record_routing_outcome"})
ADVISOR_TOOLS = frozenset({"get_advisor_input", "complete_routing"})
ROUTING_TOOLS = ROOT_TOOLS | ADVISOR_TOOLS
CLAUDE_EFFORTS = frozenset({"low", "medium", "high", "xhigh", "max"})
NAME = re.compile(r"[a-z][a-z0-9-]{0,63}\Z")


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


def settings(config: dict | None = None) -> dict:
    config = config or {}
    raw = config.get("pipeline", {})
    keys = {"mode", "state_dir", "agents_dir", "mcp_server", "advisor_route", "variants", "baseline", "approved_choices", "profile_capabilities"}
    if not isinstance(raw, dict) or set(raw) - keys:
        raise EvidenceError("unknown_pipeline_configuration")
    value = {"mode": "required", "state_dir": None, "agents_dir": None,
             "mcp_server": "assay-benchmark-routing", "advisor_route": None,
             "variants": [], "baseline": None, "approved_choices": {}, "profile_capabilities": {}, **copy.deepcopy(raw)}
    if not isinstance(value["mode"], str) or value["mode"] not in {"required", "evidence-only"}:
        raise EvidenceError("invalid_pipeline_mode")
    if not isinstance(value["mcp_server"], str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", value["mcp_server"]):
        raise EvidenceError("invalid_pipeline_mcp_server")
    for key in ("state_dir", "agents_dir"):
        path = value[key]
        if path is not None and (not isinstance(path, str) or not path or not Path(path).is_absolute()):
            raise EvidenceError("pipeline_paths_must_be_absolute")
    if value["baseline"] is not None:
        value["baseline"] = pair(value["baseline"])
    route = value["advisor_route"]
    if route is not None:
        from .advisors.native import _validate_basis
        if not isinstance(route, dict) or set(route) != {"model", "effort", "selection_basis"}:
            raise EvidenceError("invalid_pipeline_advisor_route")
        pair({k: route[k] for k in ("model", "effort")})
        _validate_basis(route["selection_basis"])
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
    return value


def plain_path(path: Path) -> Path:
    """Reject linked/reparse ancestors, including a missing path's existing parent."""
    if not path.is_absolute():
        raise EvidenceError("pipeline_path_not_absolute")
    for entry in (path, *path.parents):
        if entry.is_symlink() or getattr(entry, "is_junction", lambda: False)():
            raise EvidenceError("pipeline_linked_path")
    return path


def runtime_overrides(expected: dict, environment: dict | None = None) -> dict:
    """Inspect, never change, the host process environment. Unknown stays unknown."""
    env = os.environ if environment is None else environment
    problems = []
    effort = env.get("CLAUDE_CODE_EFFORT_LEVEL")
    if effort and effort != expected["effort"]:
        problems.append("effort_environment_override")
    # Older clients applied SUBAGENT_MODEL more broadly. Conservatively refuse
    # a conflicting value instead of guessing which precedence the host uses.
    model = env.get("CLAUDE_CODE_SUBAGENT_MODEL")
    force = env.get("CLAUDE_CODE_SUBAGENT_MODEL_FORCE", "").lower() in {"1", "true", "yes"}
    if (model and model != expected["model"]) or (force and not model):
        problems.append("model_environment_override")
    return {"conflicts": problems, "observed_model": None, "observed_effort": None}
