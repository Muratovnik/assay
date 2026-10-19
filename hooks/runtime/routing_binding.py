"""The plugin's routing binding: which routing configuration the hooks check and where they keep observations.

`routing.json` in the plugin data directory holds `{"config", "cache_dir"}`,
both absolute. The launch check reads the configuration from it when
`ASSAY_ROUTING_CONFIG` is not set, and Claude host observations go to
`cache_dir`. Without a binding ordinary delegation is unchecked, so a binding
left under its earlier name is refused rather than ignored.
"""
from __future__ import annotations

from pathlib import Path

from route_evidence.core import EvidenceError, RetiredConfiguration, read_document
from route_evidence.pipeline_config import plain_path

NAME = "routing.json"
RETIRED_NAME = "routing-telemetry.json"
RETIRED_VARIABLE = "ASSAY_ROUTING_TELEMETRY_CONFIG"
RENAMED = (f"the routing binding {RETIRED_NAME} was renamed to {NAME}; rename the file in the plugin data "
           "directory, keeping its config and cache_dir, so the route table check applies again")
VARIABLE_REMOVED = (f"{RETIRED_VARIABLE} was removed; put the binding in {NAME} in the plugin data directory "
                    "or name the configuration with ASSAY_ROUTING_CONFIG")


def directory(environment):
    data = environment.get("PLUGIN_DATA") or environment.get("CLAUDE_PLUGIN_DATA")
    return Path(data) if data else None


def configuration(environment):
    """The binding, or None when the plugin has none; a retired form is refused, never ignored."""
    if environment.get(RETIRED_VARIABLE):
        raise RetiredConfiguration(VARIABLE_REMOVED)
    data = directory(environment)
    if data is None:
        return None
    path = data / NAME
    if not path.exists():
        if (data / RETIRED_NAME).exists():
            raise RetiredConfiguration(RENAMED)
        return None
    plain_path(path)
    raw = read_document(path)
    if not isinstance(raw, dict) or set(raw) != {"config", "cache_dir"}:
        raise EvidenceError("routing binding requires config and cache_dir")
    for value in raw.values():
        if not isinstance(value, str) or not Path(value).is_absolute():
            raise EvidenceError("routing binding paths must be absolute")
        plain_path(Path(value))
    return raw
