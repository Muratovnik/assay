"""Reviewed publisher spellings, not fuzzy model/version inference."""
from __future__ import annotations

from .core import digest, effort, identity

# Cursor's own model pages identify these exact releases. The benchmark omits
# "Claude"; this does not license stripping arbitrary providers or date suffixes.
# Extend this source-local table only with a checked publisher correspondence.
CURSOR_ALIASES = {
    "opus-5-5": ("claude-opus-5-5", "https://cursor.com/docs/models/claude-opus-5-5"),
    "opus-5": ("claude-opus-5", "https://cursor.com/docs/models/claude-opus-5"),
    "fable-5-1": ("claude-fable-5-1", "https://cursor.com/docs/models/claude-fable-5-1"),
    "fable-5": ("claude-fable-5", "https://cursor.com/docs/models/claude-fable-5"),
    "sonnet-5": ("claude-sonnet-5", "https://cursor.com/docs/models/claude-sonnet-5"),
}


def model_identity(source_id, label):
    """Return the original spelling plus a reversible, source-scoped annotation."""
    pair = CURSOR_ALIASES.get(identity(label)) if source_id == "cursorbench" else None
    return {"source_model": label, "canonical_model": pair[0] if pair else label,
            "basis": "publisher_alias" if pair else "lexical",
            "rule": "cursorbench:" + identity(label) if pair else None,
            "reference": pair[1] if pair else None}


def resolve_model(source_id, label, inventory):
    """Match only exact/lexical or reviewed names; conflicting bindings abstain."""
    annotation = model_identity(source_id, label)
    keys = {identity(label), identity(annotation["canonical_model"])}
    matches = {inventory[key]["model"]: inventory[key] for key in keys if key in inventory}
    if len(matches) > 1:
        return None, annotation, "ambiguous_model_identity"
    if not matches:
        return None, annotation, "unmatched_model_name"
    return next(iter(matches.values())), annotation, None


def inventory_keys(available):
    """Per-route discovery fingerprints: order/removal alone does not add a key."""
    return sorted({digest({"names": sorted({identity(item["model"]),
                                            *(identity(n) for n in item.get("evidence_names", []))}),
                           "efforts": sorted(effort(e) for e in item["efforts"])})
                   for item in available})


def matching_diagnostics(source_id, rows, available, *, state="loaded", harness=None):
    """Explain name/effort gaps without treating unmatched names as unpublished models."""
    inventory = {identity(name): item for item in available
                 for name in [item["model"], *item.get("evidence_names", [])]}
    by_model = {item["model"]: {"model": item["model"], "status": state,
                               "matched_names": [], "observed_efforts": [],
                               "usable_rows": 0} for item in available}
    unmatched, ambiguous = set(), set()
    if state == "loaded":
        for row in rows:
            candidate, annotation, error = resolve_model(source_id, row["model"], inventory)
            if error:
                (ambiguous if error == "ambiguous_model_identity" else unmatched).add(row["model"])
                continue
            target = by_model[candidate["model"]]
            # Every relevant match is retained; only unrelated unmatched examples
            # are bounded below. A name match never equates different efforts.
            if annotation not in target["matched_names"]:
                target["matched_names"].append(annotation)
            if row["effort"] not in target["observed_efforts"]:
                target["observed_efforts"].append(row["effort"])
            if (row["effort"] is not None and row["effort"] in list(map(effort, candidate["efforts"]))
                    and (not harness or identity(harness) == identity(row["harness"]))):
                target["usable_rows"] += 1
        for item in available:
            target = by_model[item["model"]]
            if not target["matched_names"]:
                target["status"] = "no_matching_model_name"
            elif target["usable_rows"]:
                target["status"] = "matched"
            elif not set(target["observed_efforts"]) & set(map(effort, item["efforts"])):
                target["status"] = "no_matching_effort"
            else:
                target["status"] = "harness_filtered"
            target["observed_efforts"].sort(key=lambda value: "" if value is None else value)
            target["matched_names"].sort(key=lambda value: value["source_model"])
    names = sorted(unmatched)
    return {"models": [by_model[key] for key in sorted(by_model)],
            "unmatched_name_count": len(names), "unmatched_name_examples": names[:12],
            "unmatched_names_truncated": len(names) > 12,
            "ambiguous_names": sorted(ambiguous),
            "note": "Name gaps describe this snapshot and inventory, not absence of published measurements."}
