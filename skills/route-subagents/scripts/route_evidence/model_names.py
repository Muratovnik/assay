"""Bind publisher labels to host model IDs by rule, never by a model registry."""
from __future__ import annotations

from collections import Counter

from .core import digest, effort, identity

# Publishers add or drop the host provider's own brand: "Opus 5.5", "Claude
# Opus 5.5" and "anthropic/Opus 5.5" all name claude-opus-5-5. That brand is the
# only word a structural binding ignores. Family, variant, date and every version
# number must still be equal, and the binding must be unique on both sides, so a
# new release binds without a code or configuration entry.
PROVIDER_BRANDS = {"claude": frozenset({"claude", "anthropic"}), "codex": frozenset({"openai"})}


def provider_brands(client):
    """The brand words a client's own provider adds to labels; none when unknown."""
    return PROVIDER_BRANDS.get(client, frozenset())


def structural_key(value, brands):
    return tuple(token for token in identity(value).split("-") if token and token not in brands)


def _annotation(label, model=None, brands=frozenset()):
    if model is None:
        return {"source_model": label, "canonical_model": label, "basis": "lexical", "rule": None}
    return {"source_model": label, "canonical_model": model, "basis": "provider_brand",
            "rule": "ignores " + "/".join(sorted(brands))}


def bind_labels(labels, available, client=None):
    """Bind one source's labels: {label: (inventory item | None, annotation, error)}.

    An exact spelling (a model ID or a confirmed evidence name) binds first. For
    a known provider, a label whose words equal one model's ID or confirmed name
    apart from that provider's brand binds structurally. It abstains when two
    inventory models share those words, and when another label of the same source
    already names that model, so one configuration never gets two measurements.
    """
    brands = provider_brands(client)
    names = [(name, item) for item in available for name in [item["model"], *item.get("evidence_names", [])]]
    exact = {identity(name): item for name, item in names}
    by_key = {}
    for name, item in (names if brands else ()):
        matches = by_key.setdefault(structural_key(name, brands), [])
        if item not in matches:
            matches.append(item)
    result, structural = {}, {}
    for label in sorted(set(labels)):
        hit = exact.get(identity(label))
        if hit:
            result[label] = (hit, _annotation(label), None)
            continue
        matches = by_key.get(structural_key(label, brands), []) if brands else []
        if len(matches) > 1:
            result[label] = (None, _annotation(label), "ambiguous_model_identity")
        elif matches:
            structural[label] = matches[0]
        else:
            result[label] = (None, _annotation(label), "unmatched_model_name")
    named = Counter(item["model"] for item, _, _ in result.values() if item)
    named.update(item["model"] for item in structural.values())
    for label, item in structural.items():
        annotation = _annotation(label, item["model"], brands)
        result[label] = ((None, annotation, "duplicate_source_label") if named[item["model"]] > 1
                         else (item, annotation, None))
    return result


def inventory_keys(available):
    """Per-route discovery fingerprints: order/removal alone does not add a key."""
    return sorted({digest({"names": sorted({identity(item["model"]),
                                            *(identity(n) for n in item.get("evidence_names", []))}),
                           "efforts": sorted(effort(e) for e in item["efforts"])})
                   for item in available})


def matching_diagnostics(source_id, rows, available, *, state="loaded", harness=None, client=None):
    """Explain name/effort gaps without treating unmatched names as unpublished models."""
    by_model = {item["model"]: {"model": item["model"], "status": state,
                               "matched_names": [], "observed_efforts": [],
                               "usable_rows": 0} for item in available}
    unmatched, ambiguous, duplicates = set(), set(), set()
    if state == "loaded":
        bindings = bind_labels([row["model"] for row in rows], available, client)
        for row in rows:
            candidate, annotation, error = bindings[row["model"]]
            if error:
                {"ambiguous_model_identity": ambiguous, "duplicate_source_label": duplicates}.get(
                    error, unmatched).add(row["model"])
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
            "ambiguous_names": sorted(ambiguous), "duplicate_labels": sorted(duplicates),
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


def spelling_report(snapshots, available, *, limit=MAX_SPELLING_CANDIDATES, client=None):
    """Which cached sources name each inventory model, and spellings to review.

    `snapshots` lists (source_id, rows). Candidates are unbound labels of the
    sources that name none of a model's rows. The owner confirms one as
    `evidence_names` or ignores it; this report changes no matching.
    """
    models = {item["model"]: {"named_in": [], "unnamed_in": [], "candidates": {}} for item in available}
    for source_id, rows in snapshots:
        named, unbound = set(), set()
        for label, (candidate, _, error) in bind_labels([row["model"] for row in rows], available, client).items():
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
