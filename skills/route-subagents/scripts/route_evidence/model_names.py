"""Reviewed publisher spellings, not fuzzy model/version inference."""
from __future__ import annotations

from collections import Counter

from .core import digest, effort, identity

# Cursor's own model pages identify these exact releases. The benchmark omits
# "Claude"; this does not license stripping arbitrary providers or date suffixes.
# The table is frozen: a new model's spelling is the owner's confirmed
# `evidence_names`, which the spelling report below helps to find.
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


MAX_SPELLING_CANDIDATES = 5


def _tokens(value):
    key = identity(value)
    return key.split("-") if key else []


def _candidate_rank(model, label):
    """Sort key for a label an owner may confirm, or None without a shared word.

    Fewer foreign words, then an equal version sequence, rank first. This orders
    advice for a person; it is not a match and never binds a row.
    """
    mine, theirs = _tokens(model), _tokens(label)
    my_words = {t for t in mine if not t.isdigit()}
    their_words = {t for t in theirs if not t.isdigit()}
    if not my_words & their_words:
        return None
    shared = sum((Counter(mine) & Counter(theirs)).values())
    same_version = [t for t in mine if t.isdigit()] == [t for t in theirs if t.isdigit()]
    return (len(their_words - my_words), not same_version, -len(my_words & their_words),
            -shared, len(theirs) - shared, label)


def spelling_report(snapshots, available, *, limit=MAX_SPELLING_CANDIDATES):
    """Which cached sources name each inventory model, and spellings to review.

    `snapshots` lists (source_id, rows). Candidates are unbound labels of the
    sources that name none of a model's rows. The owner confirms one as
    `evidence_names` or ignores it; this report changes no matching.
    """
    inventory = {identity(name): item for item in available
                 for name in [item["model"], *item.get("evidence_names", [])]}
    models = {item["model"]: {"named_in": [], "unnamed_in": [], "candidates": {}} for item in available}
    for source_id, rows in snapshots:
        named, unbound = set(), set()
        for label in {row["model"] for row in rows}:
            candidate, _, error = resolve_model(source_id, label, inventory)
            if candidate:
                named.add(candidate["model"])
            elif error == "unmatched_model_name":
                unbound.add(label)
        for model, entry in models.items():
            if model in named:
                entry["named_in"].append(source_id)
                continue
            entry["unnamed_in"].append(source_id)
            for label in unbound:
                rank = _candidate_rank(model, label)
                if rank is not None:
                    entry["candidates"].setdefault(label, (rank, []))[1].append(source_id)
    report = []
    for model in sorted(models):
        entry = models[model]
        ranked = sorted(entry["candidates"].items(), key=lambda item: item[1][0])[:limit]
        report.append({"model": model, "named_in": entry["named_in"], "unnamed_in": entry["unnamed_in"],
                       "candidates": [{"label": label, "sources": sources} for label, (_, sources) in ranked]})
    return {"status": "checked" if snapshots else "no_cached_rows",
            "sources": [source_id for source_id, _ in snapshots], "models": report,
            "note": ("Candidates are spellings to confirm with inventory-confirm --evidence-name; "
                     "they never bind rows. A source that does not name a model may not measure it.")}
