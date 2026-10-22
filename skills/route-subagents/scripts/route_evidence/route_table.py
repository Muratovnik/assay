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

from .core import EvidenceError, identity
from .pipeline_config import EFFORT_ORDER

CLASS_NAME = re.compile(r"[a-z][a-z0-9-]{0,31}\Z")
# A label starts with the class and then a separator; a bare class is valid too.
LABEL = re.compile(r"\s*([a-z][a-z0-9-]{0,31})(?:[\s:_]|\Z)")
PLACEHOLDER_EFFORTS = frozenset({"default", "auto", "inherit", "unspecified"})
MAX_CLASSES = 16
MAX_TEXT = 300
MAX_BASIS = 2000
# Said with every class refusal and admission, because a primary that reads only
# the hook reply, such as a session still holding an older skill, still needs
# the selection rule and the record the skill asks for.
CHOOSING = ("Choose the class whose description fits the work, not the class whose pair you already chose; "
            "when two classes fit, take the less demanding one, since a stronger class needs a reason in the "
            "work itself, such as real ambiguity or design.")
REASON = "State in one line, with the launch, why the work fits its class."
# For a spawn the table does not check while a table is configured: a
# continuation, an owner-exempt agent type or a switched-off check.
OUTSIDE = ("Assay routing: this launch is outside the owner's route table check and keeps the settings it "
           "names or inherits. For a new child, take a class from routing_status and pass its model and effort "
           "in the call. " + CHOOSING)

# Native spawn calls this check reads. A client absent here has no launch check.
SPAWN = {
    "claude": {"tools": frozenset({"Agent", "Task"}), "model": "model", "effort": "effort",
               "label": "description"},
    "codex": {"tools": frozenset({"spawn_agent", "collaborationspawn_agent"}), "model": "model", "effort": "reasoning_effort",
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


def _checked_kind(client: str, tool_name: Any, supplied: Any, unrouted) -> str | None:
    """The agent type of a spawn the table governs; None for other tools and exempt launches."""
    spec = SPAWN.get(client)
    if spec is None or tool_name not in spec["tools"] or not isinstance(supplied, dict):
        return None
    if client == "claude":
        kind = supplied.get("subagent_type") or "general-purpose"
        if kind == "fork" or supplied.get("resume"):
            return None
    else:
        kind = supplied.get("agent_type") or "default"
    return None if kind in unrouted else kind


def check_launch(client: str, tool_name: Any, supplied: Any, table: dict, *, unrouted=(),
                 environment: dict | None = None, cwd: Any = None, home: Path | None = None) -> str | None:
    """The refusal for a spawn that does not follow the table, or None to let it run."""
    if tool_name in SPAWN.get(client, {}).get("tools", ()) and not isinstance(supplied, dict):
        return "routing launch input must be an object before its class and settings can be checked"
    kind = _checked_kind(client, tool_name, supplied, unrouted)
    if kind is None:
        return None
    spec = SPAWN[client]
    environment = environment or {}
    home = Path.home() if home is None else home
    field = spec["label"]
    name = declared_class(supplied.get(field))
    if name is None or name not in table["classes"]:
        example = next(iter(table["classes"])) + ("_..." if client == "codex" else ": ...")
        return (f"routing needs a task class at the start of this call's `{field}` (for example "
                f"`{example}`), then that class's model and effort. {CHOOSING} Classes: "
                + listing(table))
    entry = table["classes"][name]
    expected = {spec["model"]: entry["model"], spec["effort"]: entry["effort"]}
    wrong = [f"{key}={supplied.get(key)!r} (class {name} uses {value!r})"
             for key, value in expected.items() if supplied.get(key) != value]
    if wrong:
        return ("this launch does not match its declared class: " + "; ".join(wrong)
                + f". Use the class's pair, or declare the class that fits the task. {CHOOSING} Classes: "
                + listing(table))
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


def admission(client: str, tool_name: Any, supplied: Any, table: dict, *, unrouted=()) -> str | None:
    """Context for a launch the table admitted: the record to keep and the rule to apply next time.

    A reminder, not a check: nothing verifies that the reason is written.
    """
    if _checked_kind(client, tool_name, supplied, unrouted) is None:
        return None
    name = declared_class(supplied.get(SPAWN[client]["label"]))
    entry = table["classes"].get(name) if name else None
    if entry is None:
        return None
    return (f"Assay: launch admitted as class `{name}` ({entry['model']}/{entry['effort']}). {REASON} "
            f"{CHOOSING}")


PUBLISHED_COST = "published API cost, not quota"
DERIVED_COST = "published run total / sample count: cost per attempt, derived; API cost, not quota"


def _cost_per_attempt(row: dict) -> float | None:
    """A published run total over its attempts, or None unless both are positive."""
    total = (row.get("aggregate_usage") or {}).get("total_cost_usd")
    count = row.get("sample_count")
    if type(total) in (int, float) and type(count) in (int, float) and total > 0 and count > 0:
        return total / count
    return None


def _priced(rows: list) -> tuple[list, str | None, str | None]:
    """Rows carrying the cost they are compared on, that cost's basis, and a refusal.

    A published per-task cost wins, and the two units are never mixed. Without
    one, a run total becomes a cost per attempt only when every priced row ran
    the same number of attempts: a different count means a different protocol,
    whose attempts need not cost alike. A zero total is not a measurement.
    """
    if any(type(row.get("cost_usd")) in (int, float) for row in rows):
        return [row for row in rows if type(row.get("cost_usd")) in (int, float)], PUBLISHED_COST, None
    derived = [(row, _cost_per_attempt(row)) for row in rows]
    derived = [{**row, "cost_usd": cost} for row, cost in derived if cost is not None]
    if len({row["sample_count"] for row in derived}) > 1:
        return [], None, "run_totals_differ_in_sample_count"
    return derived, DERIVED_COST, None


def candidates(rows: list, *, band: float, subset: str | None = None, harness: str | None = None,
               match: str | None = None) -> dict:
    """Measured pairs of one benchmark subset for the owner to review, cheapest first.

    Pairs whose score is within `band` of the best measured score are treated as
    indistinguishable from it; the cheapest of them is the proposal. Published
    tables without intervals cannot resolve a smaller difference, so `band` is
    the owner's statement of that resolution, not a measured quantity.

    A harness matches by lexical identity, so `claude-code` selects a board's
    "Claude Code". A board that publishes only run totals is priced per attempt
    (see `_priced`); `cost_basis` says which cost the rows carry.
    """
    if type(band) not in (int, float) or not 0 <= band < 1:
        raise EvidenceError("route_candidates_band_must_be_a_fraction")
    selected = [row for row in rows if isinstance(row, dict)
                and type(row.get("score")) in (int, float)
                and (subset is None or row.get("subset") == subset)
                and (harness is None or identity(str(row.get("harness") or "")) == identity(harness))
                and (match is None or match.lower() in str(row.get("model", "")).lower())]
    usable, cost_basis, refusal = _priced(selected)
    if not usable:
        return {"status": "no_measured_pairs", "rows": [], **({"reason": refusal} if refusal else {})}
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
    return {"status": "ok", "best_score": best, "band": band, "cost_basis": cost_basis, "rows": result}
