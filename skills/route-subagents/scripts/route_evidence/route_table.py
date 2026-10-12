"""The owner's task-class route table and the launch check that enforces it.

A table names a few task classes and the model and effort each class launches
with. The primary agent picks the class; the pair follows from the table, so a
child neither inherits the session's settings nor carries an ad hoc choice.

The class is read from a short plain field of the native spawn call: the first
word of a Claude Agent `description`, the start of a Codex `task_name`. The
execution prompt is not used, because a client may store it encrypted.
"""
from __future__ import annotations

import copy
import re
import tomllib
from pathlib import Path
from typing import Any

from .core import EvidenceError
from .pipeline_config import EFFORT_ORDER

CLASS_NAME = re.compile(r"[a-z][a-z0-9-]{0,31}\Z")
# A label starts with the class and then a separator; a bare class is valid too.
LABEL = re.compile(r"\s*([a-z][a-z0-9-]{0,31})(?:[\s:_]|\Z)")
PLACEHOLDER_EFFORTS = frozenset({"default", "auto", "inherit", "unspecified"})
MAX_CLASSES = 16
MAX_TEXT = 300
MAX_BASIS = 2000

# Native spawn calls this check reads. A client absent here has no launch check.
SPAWN = {
    "claude": {"tools": frozenset({"Agent", "Task"}), "model": "model", "effort": "effort",
               "label": "description"},
    "codex": {"tools": frozenset({"spawn_agent"}), "model": "model", "effort": "reasoning_effort",
              "label": "task_name"},
}


def _text(value: Any, limit: int, code: str) -> str:
    if (not isinstance(value, str) or not value.strip() or len(value) > limit
            or any(ord(c) < 32 and c not in "\n\t" for c in value)):
        raise EvidenceError(code)
    return value


def _effort(client: str, value: Any) -> str:
    if not isinstance(value, str) or value in PLACEHOLDER_EFFORTS:
        raise EvidenceError("invalid_route_table_effort")
    if client == "claude":
        if value not in EFFORT_ORDER:
            raise EvidenceError("invalid_route_table_effort")
    elif not re.fullmatch(r"[a-z][a-z0-9-]{0,31}", value):
        raise EvidenceError("invalid_route_table_effort")
    return value


def settings(config: dict | None) -> dict | None:
    """The normalized table, or None when the owner configured none."""
    raw = (config or {}).get("routes")
    if raw is None:
        return None
    if not isinstance(raw, dict) or set(raw) - {"classes", "basis"} or "classes" not in raw:
        raise EvidenceError("invalid_route_table")
    client = (config or {}).get("client")
    if client not in SPAWN:
        raise EvidenceError("route_table_unsupported_client")
    classes = raw["classes"]
    if not isinstance(classes, dict) or not 1 <= len(classes) <= MAX_CLASSES:
        raise EvidenceError("invalid_route_table_classes")
    table = {}
    for name, entry in classes.items():
        if not isinstance(name, str) or not CLASS_NAME.fullmatch(name):
            raise EvidenceError("invalid_route_table_class_name")
        if not isinstance(entry, dict) or set(entry) != {"model", "effort", "when"}:
            raise EvidenceError("invalid_route_table_class")
        model = entry["model"]
        if (not isinstance(model, str) or not model or model != model.strip() or len(model) > 200
                or any(ord(c) < 32 for c in model) or model == "inherit"):
            raise EvidenceError("invalid_route_table_model")
        table[name] = {"model": model, "effort": _effort(client, entry["effort"]),
                       "when": _text(entry["when"], MAX_TEXT, "invalid_route_table_when")}
    basis = raw.get("basis")
    if basis is not None:
        _text(basis, MAX_BASIS, "invalid_route_table_basis")
    return {"classes": table, "basis": copy.deepcopy(basis)}


def declared_class(label: Any) -> str | None:
    match = LABEL.match(label) if isinstance(label, str) else None
    return match[1] if match else None


def listing(table: dict) -> str:
    return "; ".join(f"{name} = {entry['model']}/{entry['effort']} ({entry['when']})"
                     for name, entry in table["classes"].items())


def _codex_definition(kind: str, cwd: Any, home: Path) -> dict:
    """Model settings a Codex custom agent file pins; the file wins over the call."""
    if not isinstance(kind, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}", kind):
        return {}
    roots = [home / ".codex" / "agents"]
    if isinstance(cwd, str) and cwd:
        roots.insert(0, Path(cwd) / ".codex" / "agents")
    for root in roots:
        path = root / (kind + ".toml")
        if path.is_file():
            try:
                data = tomllib.loads(path.read_text(encoding="utf-8"))
            except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError):
                return {"unreadable": str(path.name)}
            return {key: data[key] for key in ("model", "model_reasoning_effort") if isinstance(data.get(key), str)}
    return {}


def check_launch(client: str, tool_name: Any, supplied: Any, table: dict, *, unrouted=(),
                 environment: dict | None = None, cwd: Any = None, home: Path | None = None) -> str | None:
    """The refusal for a spawn that does not follow the table, or None to let it run."""
    spec = SPAWN.get(client)
    if spec is None or tool_name not in spec["tools"] or not isinstance(supplied, dict):
        return None
    environment = environment or {}
    home = Path.home() if home is None else home
    if client == "claude":
        kind = supplied.get("subagent_type") or "general-purpose"
        if kind == "fork" or supplied.get("resume") or kind in unrouted:
            return None
    else:
        kind = supplied.get("agent_type") or "default"
        if kind in unrouted:
            return None
    field = spec["label"]
    name = declared_class(supplied.get(field))
    if name is None or name not in table["classes"]:
        return (f"routing needs a task class at the start of this call's `{field}` (for example "
                f"`{next(iter(table['classes']))}: ...`), then that class's model and effort. Classes: "
                + listing(table))
    entry = table["classes"][name]
    expected = {spec["model"]: entry["model"], spec["effort"]: entry["effort"]}
    wrong = [f"{key}={supplied.get(key)!r} (class {name} uses {value!r})"
             for key, value in expected.items() if supplied.get(key) != value]
    if wrong:
        return ("this launch does not match its declared class: " + "; ".join(wrong)
                + ". Use the class's pair, or declare the class that fits the task. Classes: " + listing(table))
    if client == "codex":
        fork = supplied.get("fork_turns")
        if fork is None or fork == "all":
            return ("a Codex spawn with omitted or \"all\" fork_turns inherits the parent's model and "
                    "effort and ignores the requested ones; pass fork_turns=\"none\" with a self-contained "
                    "message, or a bounded recent-turn count")
        pinned = _codex_definition(kind, cwd, home)
        if "unreadable" in pinned:
            return f"the custom agent file for `{kind}` could not be read, so its model settings are unknown"
        conflicts = [f"{key}={value!r}" for key, value in pinned.items()
                     if value != entry["model" if key == "model" else "effort"]]
        if conflicts:
            return (f"the custom agent file for `{kind}` pins " + ", ".join(conflicts)
                    + ", which overrides this call; use an agent type without pinned settings for class " + name)
    else:
        override = environment.get("CLAUDE_CODE_EFFORT_LEVEL")
        if override and override != entry["effort"]:
            return (f"CLAUDE_CODE_EFFORT_LEVEL={override!r} overrides this call's effort; class {name} "
                    f"needs {entry['effort']!r}. Unset the variable for routed launches")
    return None


def candidates(rows: list, *, band: float, subset: str | None = None, harness: str | None = None,
               match: str | None = None) -> dict:
    """Measured pairs of one benchmark subset for the owner to review, cheapest first.

    Pairs whose score is within `band` of the best measured score are treated as
    indistinguishable from it; the cheapest of them is the proposal. Published
    tables without intervals cannot resolve a smaller difference, so `band` is
    the owner's statement of that resolution, not a measured quantity.
    """
    if type(band) not in (int, float) or not 0 <= band < 1:
        raise EvidenceError("route_candidates_band_must_be_a_fraction")
    usable = [row for row in rows if isinstance(row, dict)
              and type(row.get("score")) in (int, float) and type(row.get("cost_usd")) in (int, float)
              and (subset is None or row.get("subset") == subset)
              and (harness is None or row.get("harness") == harness)
              and (match is None or match.lower() in str(row.get("model", "")).lower())]
    if not usable:
        return {"status": "no_measured_pairs", "rows": []}
    best = max(row["score"] for row in usable)
    inside = [row for row in usable if row["score"] >= best - band]
    cheapest = min(inside, key=lambda row: (row["cost_usd"], -row["score"]))
    result = []
    for row in sorted(usable, key=lambda row: (row["cost_usd"], -row["score"])):
        dominated = any(other is not row and other["cost_usd"] <= row["cost_usd"] and other["score"] >= row["score"]
                        and (other["cost_usd"] < row["cost_usd"] or other["score"] > row["score"])
                        for other in usable)
        result.append({"model": row.get("model"), "effort": row.get("effort"), "harness": row.get("harness"),
                       "subset": row.get("subset"), "score": row["score"], "cost_usd": row["cost_usd"],
                       "frontier": not dominated, "within_band": row in inside, "proposal": row is cheapest})
    return {"status": "ok", "best_score": best, "band": band, "cost_basis": "published API cost, not quota",
            "rows": result}
