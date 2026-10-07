"""Versioned opt-in advisor settings; no transport imports or implicit migration."""
from __future__ import annotations

import copy
from pathlib import Path

from .core import EvidenceError, encoded, number


def _object(value, keys, name):
    if not isinstance(value, dict) or set(value) - set(keys):
        raise EvidenceError("unknown or invalid " + name + " configuration")
    return copy.deepcopy(value)


def settings(config=None):
    from .advice import default_policy

    config = config or {}
    advisor = _object(config.get("advisor", {}), {
        "enabled", "backend", "native", "jev", "max_packets",
        "max_candidates_per_packet", "max_snapshot_bytes", "max_pending", "pending_seconds",
    }, "advisor")
    advisor.setdefault("enabled", config.get("schema_version") in (2, 3))
    advisor.setdefault("backend", "native-economy")
    if type(advisor["enabled"]) is not bool or advisor["backend"] not in ("native-economy", "jev"):
        raise EvidenceError("invalid advisor enabled/backend")
    native = _object(advisor.get("native", {}), {"selection", "require_explicit_resolved_route"}, "native")
    native.setdefault("selection", "economy")
    native.setdefault("require_explicit_resolved_route", True)
    if native != {"selection": "economy", "require_explicit_resolved_route": True}:
        raise EvidenceError("native economy requires an explicitly resolved advisor route")
    advisor["native"] = native
    jev = _object(advisor.get("jev", {}), {
        "enabled", "model", "api_key_env", "external_data_consent", "timeout_seconds",
        "endpoint", "cooldown_seconds", "privacy_profile",
    }, "jev")
    for key, value in {"enabled": False, "model": "jev-1.13.0", "api_key_env": "TYPESAFE_API_KEY",
                       "external_data_consent": False, "timeout_seconds": 5}.items():
        jev.setdefault(key, value)
    for key in ("enabled", "external_data_consent"):
        if type(jev[key]) is not bool:
            raise EvidenceError("invalid Jev consent/enabled flag")
    if not isinstance(jev["model"], str) or not jev["model"].startswith("jev-") or "latest" in jev["model"]:
        raise EvidenceError("Jev requires a pinned model version")
    if jev["api_key_env"] != "TYPESAFE_API_KEY":
        raise EvidenceError("Jev credentials use TYPESAFE_API_KEY")
    for key in ("timeout_seconds", "cooldown_seconds"):
        if key in jev and not 0 < number(jev[key], key, upper=3600) <= (5 if key == "timeout_seconds" else 3600):
            raise EvidenceError("invalid Jev time limit")
    advisor["jev"] = jev
    if jev.get("endpoint", "https://api.typesafe.ai") != "https://api.typesafe.ai":
        raise EvidenceError("Jev requires the official endpoint")
    if jev.get("privacy_profile", "external-structured") != "external-structured":
        raise EvidenceError("unsupported external privacy profile")
    # The adapter validates its version and timeout contract without loading
    # the optional SDK or reading a credential.
    from .advisors.jev import JevAdapter
    JevAdapter(jev)
    for key, value, limit in (("max_pending", 16, 16), ("pending_seconds", 600, 600)):
        advisor.setdefault(key, value)
        if type(advisor[key]) is not int or not 1 <= advisor[key] <= limit:
            raise EvidenceError("invalid " + key)
    policy = copy.deepcopy(config.get("policy", {}))
    if not isinstance(policy, dict):
        raise EvidenceError("policy must be an object")
    for key in ("max_packets", "max_candidates_per_packet", "max_snapshot_bytes"):
        if key in advisor:
            if key in policy and policy[key] != advisor[key]:
                raise EvidenceError("conflicting advisor/policy bound")
            policy[key] = advisor[key]
    policy = default_policy(policy)
    telemetry = _object(config.get("telemetry", {}), {"mode", "retention_days"}, "telemetry")
    telemetry.setdefault("mode", "metadata")
    telemetry.setdefault("retention_days", 30)
    if telemetry["mode"] not in ("off", "metadata", "full"):
        raise EvidenceError("unknown telemetry mode")
    if type(telemetry["retention_days"]) is not int or not 1 <= telemetry["retention_days"] <= 365:
        raise EvidenceError("retention_days must be between 1 and 365")
    result = {"advisor": advisor, "policy": policy, "telemetry": telemetry}
    if "task_evidence" in config:
        from .task_evidence import settings as task_settings
        result["task_evidence"] = task_settings(config["task_evidence"])
    return result


def migrate_config(source: Path, destination: Path, *, enable_advisor=False, mode="evidence-only",
                   native_input_unlimited=False):
    """Create a v3 configuration exclusively; never install or rewrite the source.

    The default keeps the existing workflow. Required routing is an explicit mode.
    """
    from .service import load_config
    from .pipeline_config import settings as pipeline_settings

    config = load_config(source)
    if config.get("schema_version") not in (1, 2) and not (native_input_unlimited and config.get("schema_version") == 3):
        raise EvidenceError("migration requires a v1 or v2 source")
    legacy = config["schema_version"]
    config["schema_version"] = 3
    if legacy == 1:
        config["advisor"] = {"enabled": enable_advisor or mode == "required"}
    if native_input_unlimited:
        policy = config.setdefault("policy", {})
        policy.update(schema_version=2, policy_version="routing-policy-v2", max_snapshot_bytes=None)
        config.setdefault("advisor", {}).pop("max_snapshot_bytes", None)
    config.update(settings(config))
    config["pipeline"] = pipeline_settings(config if legacy == 3 else {"pipeline": {"mode": mode}})
    with destination.open("xb") as stream:
        stream.write(encoded(config))
    return {"status": "migrated", "schema_version": 3, "advisor_enabled": config["advisor"]["enabled"],
            "pipeline_mode": config["pipeline"]["mode"], "setup_required": config["pipeline"]["mode"] == "required",
            "native_input_unlimited": native_input_unlimited,
            "registration_changed": False, "launch_arguments_changed": False}
