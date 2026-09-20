"""Opt-in local task evidence. Storage, retrieval and bounded advisor projection."""
from __future__ import annotations

import copy
import json
import math
import re
import time
from collections import Counter
from pathlib import Path

from .cache import atomic_write, source_lock
from .core import EvidenceError, digest, encoded, epoch, number
from .advice_contracts import _safe_name, validate_packets
from .history import _refuse_link_ancestors, _read_json
from .task_costs import estimates, compare, chain_totals, UNITS

MAX_INDEX_BYTES = 32 * 1024 * 1024
MAX_ROWS = 15000
MAX_SUMMARY = 6144


def validate_summary(value):
    if not isinstance(value, dict) or value.get("schema_version") != 1 or len(encoded(value)) > MAX_SUMMARY:
        raise EvidenceError("invalid task evidence projection")
    allowed = {"schema_version", "mode", "packets", "cost_units_are_not_interchangeable", "status",
               "reason", "corpus_fingerprint", "source", "retrieval_version", "settings_hash"}
    if set(value) - allowed or not isinstance(value.get("packets"), list) or len(value["packets"]) > 8:
        raise EvidenceError("invalid task evidence fields")
    def check(node, depth=0):
        if depth > 14:
            raise EvidenceError("task projection nesting limit")
        if isinstance(node, dict):
            if any(k in {"query", "task_query", "task_queries", "description", "prompt", "raw_output", "ground_truth", "encoder_path"} for k in node):
                raise EvidenceError("task text cannot enter advisor projection")
            for v in node.values():
                check(v, depth+1)
        elif isinstance(node, list):
            for v in node:
                check(v, depth+1)
        elif isinstance(node, str) and (len(node) > 512 or any(ord(c) < 32 for c in node)):
            raise EvidenceError("invalid projection string")
    check(value)
    return value


def attach_summary(snapshot, summary):
    from .advice_contracts import snapshot_identity, validate_routing_snapshot
    from .advice import semantic_projection
    output = copy.deepcopy(snapshot)
    output["evidence"]["task_similarity_evidence"] = validate_summary(summary)
    output["evidence_hash"] = digest(output["evidence"])
    output["snapshot_id"] = snapshot_identity({k:v for k,v in output.items() if k != "snapshot_id"})
    if len(encoded(semantic_projection(output))) > output["policy"]["max_snapshot_bytes"]:
        return snapshot
    return validate_routing_snapshot(output)


def settings(value=None):
    value = copy.deepcopy({} if value is None else value)
    defaults = {"enabled": False, "mode": "lexical", "min_similarity": .15,
                "neighbors": 32, "minimum_observations": 3, "deadline_seconds": 2,
                "retain_descriptions": False, "encoder_path": None, "encoder_revision": None}
    if not isinstance(value, dict) or set(value) - set(defaults):
        raise EvidenceError("invalid task evidence settings")
    cfg = {**defaults, **value}
    if type(cfg["enabled"]) is not bool or type(cfg["retain_descriptions"]) is not bool:
        raise EvidenceError("task evidence flags must be boolean")
    if cfg["mode"] not in {"lexical", "semantic"}:
        raise EvidenceError("invalid retrieval mode")
    for name, limit in (("neighbors", 32), ("minimum_observations", 100)):
        if type(cfg[name]) is not int or not 1 <= cfg[name] <= limit:
            raise EvidenceError("invalid retrieval bound")
    number(cfg["min_similarity"], "min_similarity", upper=1)
    if not 0 < number(cfg["deadline_seconds"], "deadline_seconds", upper=30):
        raise EvidenceError("invalid retrieval deadline")
    if cfg["encoder_path"] is not None and not isinstance(cfg["encoder_path"], str):
        raise EvidenceError("encoder_path must be a local path")
    if cfg["encoder_revision"] is not None:
        _safe_name(cfg["encoder_revision"], "encoder_revision")
    if cfg["mode"] == "semantic" and cfg["encoder_path"] and not cfg["encoder_revision"]:
        raise EvidenceError("semantic encoder requires a pinned revision")
    return cfg


def query_text(value):
    if not isinstance(value, str) or len(value.encode("utf-8")) > 4096 or "\x00" in value:
        raise EvidenceError("task query must be at most 4096 UTF-8 bytes")
    return value


def validate_queries(value, packet_ids):
    if value is None:
        return {}
    if not isinstance(value, dict) or set(value) - set(packet_ids):
        raise EvidenceError("task queries require known packet IDs")
    return {k: query_text(v) for k, v in value.items()}


def packet_candidates(packet, candidates):
    eligible = packet.get("eligible")
    return [c for c in candidates if eligible is None or c["candidate_id"] in eligible]


def tokens(value):
    return Counter(re.findall(r"[^\W_]+", value.casefold(), flags=re.UNICODE))


def cosine(left, right):
    denom = math.sqrt(sum(x*x for x in left.values()) * sum(x*x for x in right.values()))
    return sum(v * right.get(k, 0) for k, v in left.items()) / denom if denom else 0.0


def public_coverage(rows):
    """Historical pool patterns remain useful without mapping old models to new ones."""
    from collections import defaultdict
    groups = defaultdict(list)
    for row in rows:
        groups[(row["comparison_basis"], row["metric"])].append(row)
    out = []
    for (basis, metric), group in sorted(groups.items()):
        tasks = defaultdict(list)
        for row in group:
            tasks[row["task_id"]].append(row)
        pool = {(r["model"], r["effort"]) for r in group}
        complete = [v for v in tasks.values() if len(v) == len(pool) and all(r["score"] is not None for r in v)]
        out.append({"comparison_basis": basis, "metric": metric, "tasks": len(tasks),
            "historical_routes": len(pool), "complete_pool_tasks": len(complete),
            "all_fail_tasks": sum(all(r["score"] == 0 for r in v) for v in complete),
            "all_pass_tasks": sum(all(r["score"] == 1 for r in v) for v in complete),
            "unknown_effort_observations": sum(r["effort"] is None for r in group),
            "applicability": "historical_pool_not_current_candidate_probability"})
    return out


def validate_corpus(document):
    if (not isinstance(document, dict) or set(document) != {"schema_version", "source", "records"}
            or document["schema_version"] != 1):
        raise EvidenceError("invalid task corpus schema")
    source = document["source"]
    if not isinstance(source, dict) or set(source) != {"id", "revision", "url", "license", "use"}:
        raise EvidenceError("task corpus requires provenance and usage basis")
    for key in ("id", "revision", "license"):
        _safe_name(source[key], "corpus source")
    if source["use"] != "local-only" or not isinstance(source["url"], str) or not source["url"].startswith("https://") or len(source["url"]) > 512:
        raise EvidenceError("corpus is local-only with an HTTPS provenance URL")
    records = document["records"]
    if not isinstance(records, list) or not 1 <= len(records) <= MAX_ROWS:
        raise EvidenceError("corpus requires 1..15000 tasks")
    seen = set()
    for row in records:
        if not isinstance(row, dict) or set(row) != {"task_id", "task_types", "features", "query", "observations"}:
            raise EvidenceError("invalid task record")
        ref = _safe_name(row["task_id"], "task_id")
        if ref in seen:
            raise EvidenceError("duplicate task identity")
        seen.add(ref)
        query_text(row["query"])
        validate_packets([{"packet_id": ref, "task_types": row["task_types"], "features": row["features"]}])
        if not isinstance(row["observations"], list) or not 1 <= len(row["observations"]) <= 100:
            raise EvidenceError("invalid task observations")
        pairs = set()
        for obs in row["observations"]:
            keys = {"model", "effort", "metric", "comparison_basis", "score", "cost_scope", "costs", "unit_basis", "complete"}
            if not isinstance(obs, dict) or set(obs) != keys:
                raise EvidenceError("invalid task observation")
            for key in ("model", "metric", "comparison_basis"):
                _safe_name(obs[key], key)
            if obs["effort"] is not None:
                _safe_name(obs["effort"], "effort")
            key = (obs["model"], obs["effort"], obs["comparison_basis"], obs["metric"])
            if key in pairs:
                raise EvidenceError("duplicate task/model observation")
            pairs.add(key)
            if obs["score"] is not None:
                number(obs["score"], "score", upper=1)
            if obs["cost_scope"] not in {"response", "chain"} or type(obs["complete"]) is not bool:
                raise EvidenceError("invalid task cost scope")
            if not isinstance(obs["costs"], dict) or set(obs["costs"]) - UNITS or not isinstance(obs["unit_basis"], dict) or set(obs["unit_basis"]) - UNITS:
                raise EvidenceError("invalid task costs")
            for unit, val in obs["costs"].items():
                if val is not None:
                    number(val, unit)
                    if unit in {"api_usd", "quota_units"} and unit not in obs["unit_basis"]:
                        raise EvidenceError("cost unit requires a basis")
            for label in obs["unit_basis"].values():
                _safe_name(label, "unit basis")
    if len(encoded(document)) > MAX_INDEX_BYTES:
        raise EvidenceError("task corpus exceeds byte limit")
    return copy.deepcopy(document)


class TaskEvidence:
    def __init__(self, cache_root, config=None, *, history=None, clock=time.time):
        self.cache_root = Path(cache_root)
        self.root = Path(cache_root) / "task-evidence"
        self.config = settings(config)
        self.history, self.clock = history, clock

    def purge_descriptions(self):
        """Explicit opt-out cleanup; only removes the optional field from owned receipts."""
        if self.history is None or not self.history.root.exists():
            return {"status": "purged", "records": 0}
        _refuse_link_ancestors(self.history.root)
        _refuse_link_ancestors(self.history.root / ".write.lock")
        count = 0
        with source_lock(self.history.root / ".write.lock") as acquired:
            if not acquired:
                raise EvidenceError("history is busy")
            for path in self.history.root.glob("outcome-*.json"):
                record = _read_json(path)
                self.history._validate_record(record, record.get("decision_id"), "outcome")
                if "task_description" in record.get("execution", {}):
                    del record["execution"]["task_description"]
                    atomic_write(path, record)
                    count += 1
        return {"status": "purged", "records": count}

    async def async_summarize(self, packets, candidates, queries=None, objectives=None):
        """The whole local read/parse/encoder operation has one cancellable deadline."""
        import asyncio
        import sys
        from .processes import ProcessScope
        validate_queries(queries, [p["packet_id"] for p in packets])
        if not self.config["enabled"] or all(p.get("explicit") or len(packet_candidates(p, candidates)) <= 1 for p in packets):
            return self.summarize(packets, candidates, queries, objectives)
        scope = ProcessScope(self.config["deadline_seconds"])
        payload = {"root": str(self.cache_root.resolve()), "config": self.config, "now": self.clock(),
                   "history_mode": self.history.mode if self.history else "off",
                   "packets": packets, "candidates": candidates, "queries": queries, "objectives": objectives}
        try:
            raw = await asyncio.to_thread(scope.run, [sys.executable, "-B", str(Path(__file__).with_name("task_worker.py"))], encoded(payload))
            return validate_summary(json.loads(raw))
        except (EvidenceError, ValueError, OSError):
            return {"schema_version": 1, "status": "unavailable", "reason": "invalid_missing_or_over_budget",
                    "mode": self.config["mode"], "packets": [], "cost_units_are_not_interchangeable": True}
        finally:
            scope.cancel()

    def install(self, document):
        corpus = validate_corpus(document)
        _refuse_link_ancestors(self.root)
        self.root.mkdir(parents=True, exist_ok=True)
        path = self.root / "corpus.json"
        _refuse_link_ancestors(path)
        _refuse_link_ancestors(self.root / "corpus.lock")
        with source_lock(self.root / "corpus.lock") as acquired:
            if not acquired:
                raise EvidenceError("task corpus is busy")
            fingerprint = digest(corpus)
            payload = {"schema_version": 1, "fingerprint": fingerprint, "corpus": corpus}
            atomic_write(path, payload)
        return {"status": "installed", "fingerprint": fingerprint, "tasks": len(corpus["records"]), "source": corpus["source"]}

    def load(self):
        path = self.root / "corpus.json"
        _refuse_link_ancestors(path)
        if not path.exists():
            return None
        if path.stat().st_size > MAX_INDEX_BYTES + 1024:
            raise EvidenceError("task index exceeds byte limit")
        document = json.loads(path.read_text(encoding="utf-8"))
        if set(document) != {"schema_version", "fingerprint", "corpus"} or document["schema_version"] != 1:
            raise EvidenceError("invalid task index")
        corpus = validate_corpus(document["corpus"])
        if document["fingerprint"] != digest(corpus):
            raise EvidenceError("task index checksum mismatch")
        return document

    def local_rows(self, packet, deadline, query=""):
        if self.history is None or self.history.mode == "off" or not self.history.root.exists():
            return []
        _refuse_link_ancestors(self.history.root)
        records, seen = [], set()
        for i, path in enumerate(sorted(self.history.root.glob("outcome-*.json"))):
            if i >= 2048 or time.monotonic() >= deadline:
                raise EvidenceError("local history budget exceeded")
            record = _read_json(path)
            if epoch(record["expires_at"]) <= self.clock():
                continue
            execution = record.get("execution", {})
            cost = execution.get("cost_observation")
            if not cost or execution.get("status") == "launched":
                continue
            # The immutable decision describes what was known before execution.
            decision = self.history._path(record["decision_id"], "decision")
            if not decision.exists():
                continue
            prior = _read_json(decision)
            if epoch(prior["expires_at"]) <= self.clock():
                continue
            meta = next((p for p in prior["snapshot"]["packets"] if p["packet_id"] == record["packet_id"]), {})
            if meta.get("task_types") != packet["task_types"] or meta.get("features") != packet["features"]:
                continue
            if query and self.config["retain_descriptions"] and execution.get("task_description"):
                description = execution["task_description"]
                if self.config["mode"] == "semantic":
                    from .task_encoder import similarities
                    similarity = similarities(self.config["encoder_path"], query, [description], seconds=max(.01, deadline-time.monotonic()))[0]
                else:
                    similarity = cosine(tokens(query), tokens(description))
                if similarity < self.config["min_similarity"]:
                    continue
            key = (record["decision_id"], record["packet_id"])
            if key in seen:
                # Multiple chain receipts for one packet are not independent evidence.
                raise EvidenceError("ambiguous duplicate chain receipt")
            seen.add(key)
            totals = chain_totals(cost)
            status = execution["outcome"]["status"]
            score = 1 if status == "accepted" else 0 if status in {"rejected", "failed"} else None
            records.append({"task_id": cost.get("comparison_task", digest(key)), **cost["initial_route"], "metric": "accepted",
                "observed_at": record["created_at"], "chain_id": digest(key),
                "comparison_basis": digest([prior["snapshot"]["client"], totals["comparison_basis"]]),
                "cost_scope": "chain", "costs": totals["totals"], "components": totals["components"],
                "complete": totals["complete"], "unit_basis": totals["unit_basis"], "score": score})
        return records

    def summarize(self, packets, candidates, queries=None, objectives=None):
        queries = validate_queries(queries, [p["packet_id"] for p in packets])
        objectives = objectives or {}
        if not isinstance(objectives, dict) or set(objectives) - {p["packet_id"] for p in packets}:
            raise EvidenceError("objectives require known packet IDs")
        for obj in objectives.values():
            if not isinstance(obj, dict) or set(obj) != {"unit", "unit_basis", "overhead"} or obj["unit"] not in {"api_usd", "quota_units"}:
                raise EvidenceError("objective requires unit, unit_basis and incremental overhead")
            _safe_name(obj["unit_basis"], "unit_basis")
            if obj["overhead"] is not None:
                number(obj["overhead"], "overhead")
        base = {"schema_version": 1, "mode": self.config["mode"], "packets": [],
                "cost_units_are_not_interchangeable": True, "retrieval_version": 1,
                "settings_hash": digest(self.config)}
        if not self.config["enabled"]:
            return {**base, "status": "disabled"}
        deadline = time.monotonic() + self.config["deadline_seconds"]
        try:
            if all(p.get("explicit") or len(packet_candidates(p, candidates)) <= 1 for p in packets):
                return {**base, "status": "available", "packets": [
                    {"packet_id": p["packet_id"], "status": "skipped_fixed_route"} for p in packets]}
            document = self.load()
            for packet in packets:
                if time.monotonic() >= deadline:
                    raise EvidenceError("task evidence deadline exceeded")
                eligible = packet_candidates(packet, candidates)
                if packet.get("explicit") or len(eligible) <= 1:
                    base["packets"].append({"packet_id": packet["packet_id"], "status": "skipped_fixed_route"})
                    continue
                local = self.local_rows(packet, deadline, queries.get(packet["packet_id"], ""))
                neighbors = []
                query = queries.get(packet["packet_id"], "")
                query_terms = tokens(query)
                records = (document or {}).get("corpus", {}).get("records", [])
                compatible = [r for r in records if set(r["task_types"]) & set(packet["task_types"]) and
                    all(k not in packet["features"] or packet["features"][k] == v for k, v in r["features"].items())]
                if self.config["mode"] == "semantic" and query and compatible:
                    from .task_encoder import similarities
                    scores = similarities(self.config["encoder_path"], query, [r["query"] for r in compatible],
                                          seconds=max(.01, deadline-time.monotonic()))
                else:
                    scores = [cosine(query_terms, tokens(r["query"])) for r in compatible]
                for row, similarity in zip(compatible, scores):
                    if time.monotonic() >= deadline:
                        raise EvidenceError("task evidence deadline exceeded")
                    if query and similarity > 0 and similarity >= self.config["min_similarity"]:
                        neighbors.append((similarity, row))
                neighbors.sort(key=lambda p: (-p[0], p[1]["task_id"]))
                neighbors = neighbors[:self.config["neighbors"]]
                public = [{"task_id": r["task_id"], **o} for _, r in neighbors for o in r["observations"]]
                minimum = self.config["minimum_observations"]
                baseline = packet.get("baseline")
                baseline_id = next((c["candidate_id"] for c in eligible if baseline and
                    (c["model"], c["effort"]) == (baseline["model"], baseline["effort"])), None)
                obj = objectives.get(packet["packet_id"], {"unit": None, "overhead": None})
                # Local and public estimates are never pooled into one score.
                entry = {"packet_id": packet["packet_id"], "status": "available" if local or public else "no_match",
                    "neighbors": len(neighbors), "examples": [digest(r["task_id"])[:16] for _, r in neighbors[:3]],
                    "public_coverage": public_coverage(public),
                    "public": estimates(public, eligible, minimum=minimum),
                    "local": estimates(local, eligible, minimum=minimum),
                    "comparison": compare(local, eligible, baseline_id, obj["unit"], obj["overhead"],
                                          minimum=minimum, unit_basis=obj.get("unit_basis")),
                    "limitations": ["similarity_is_not_success_probability", "historical_models_not_mapped",
                                     "local_exact_features_only", "quality_not_proven", "unmeasured_conditions_unknown"]}
                base["packets"].append(entry)
            base.update(status="available", corpus_fingerprint=(document or {}).get("fingerprint"),
                        source=(document or {}).get("corpus", {}).get("source"))
        except (EvidenceError, OSError, ValueError, KeyError, TypeError):
            return {**base, "packets": [], "status": "unavailable", "reason": "invalid_missing_or_over_budget"}
        if len(encoded(base)) > MAX_SUMMARY:
            return {"schema_version": 1, "status": "insufficient_coverage", "reason": "summary_budget_exceeded",
                    "mode": self.config["mode"], "packets": [], "cost_units_are_not_interchangeable": True}
        return base
