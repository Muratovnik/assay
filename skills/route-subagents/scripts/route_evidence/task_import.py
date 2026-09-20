"""Read an explicit LLMRouterBench release slice without extracting archives."""
from __future__ import annotations

import json
import tarfile
from pathlib import Path, PurePosixPath

from .core import EvidenceError, digest
from .history import _refuse_link_ancestors
from .task_evidence import validate_corpus, MAX_INDEX_BYTES


def llmrouterbench(path, manifest):
    if not isinstance(manifest, dict) or set(manifest) != {"source", "datasets"}:
        raise EvidenceError("import manifest requires source and datasets")
    datasets = manifest["datasets"]
    if not isinstance(datasets, dict) or not datasets:
        raise EvidenceError("select datasets explicitly")
    for spec in datasets.values():
        if not isinstance(spec, dict) or set(spec) - {"task_types", "metric", "harness", "efforts", "priced_models"} or {"task_types", "metric", "harness", "efforts"} - set(spec):
            raise EvidenceError("dataset manifest requires metric, harness and effort identities")
        if not isinstance(spec["efforts"], dict) or not isinstance(spec.get("priced_models", []), list):
            raise EvidenceError("invalid effort or pricing declarations")
    path = Path(path)
    _refuse_link_ancestors(path)
    records, consumed = {}, 0

    def ingest(name, read):
        nonlocal consumed
        parts = PurePosixPath(name).parts
        if ".." in parts or PurePosixPath(name).is_absolute() or "\\" in name or ":" in name:
            raise EvidenceError("unsafe corpus member")
        dataset = next((p for p in parts if p in datasets), None)
        if dataset is None or not name.endswith(".json") or len(parts) < 3:
            return
        raw = read(MAX_INDEX_BYTES + 1)
        consumed += len(raw)
        if len(raw) > MAX_INDEX_BYTES or consumed > 256 * 1024 * 1024:
            raise EvidenceError("import slice too large; select a smaller corpus")
        doc = json.loads(raw)
        model, spec = parts[-2], datasets[dataset]
        if not isinstance(doc, dict) or not isinstance(doc.get("records"), list):
            raise EvidenceError("invalid LLMRouterBench result file")
        for row in doc["records"]:
            if not isinstance(row, dict) or "index" not in row:
                raise EvidenceError("result requires stable task index")
            task_id = dataset + ":" + str(row["index"])
            query = row.get("origin_query") or row.get("prompt")
            if not isinstance(query, str):
                raise EvidenceError("result has no task text")
            # Long benchmark prompts are rejected, never silently shortened.
            item = records.setdefault(task_id, {"task_id": task_id, "task_types": spec["task_types"],
                "features": {}, "query": query, "observations": []})
            if item["query"] != query:
                raise EvidenceError("task identity conflicts across model files")
            costs = {k: row.get(k) for k in ("prompt_tokens", "completion_tokens") if k in row}
            costs = { {"prompt_tokens": "input_tokens", "completion_tokens": "output_tokens"}[k]: v for k,v in costs.items()}
            if "cost" in row:
                # Some releases use 0 for unpriced local inference. No implied free model.
                costs["api_usd"] = row["cost"] if model in spec.get("priced_models", []) else None
            obs = {"model": model, "effort": spec["efforts"].get(model), "metric": spec["metric"],
                "comparison_basis": digest([manifest["source"], dataset, spec["harness"]]),
                "score": row.get("score"), "cost_scope": "response",
                "costs": costs, "unit_basis": {"api_usd": manifest["source"]["revision"]}, "complete": True}
            existing = [o for o in item["observations"] if o["model"] == model]
            if existing and existing[0] != obs:
                raise EvidenceError("conflicting repeated model result")
            if not existing:
                item["observations"].append(obs)

    if path.is_dir():
        for file in sorted(path.rglob("*.json")):
            _refuse_link_ancestors(file)
            with file.open("rb") as stream:
                ingest(file.relative_to(path).as_posix(), stream.read)
    else:
        with tarfile.open(path, mode="r|*") as archive:
            for member in archive:
                if member.issym() or member.islnk() or not (member.isfile() or member.isdir()):
                    raise EvidenceError("corpus archive links/special files are unsupported")
                if member.isfile():
                    if member.size > MAX_INDEX_BYTES and any(p in datasets for p in PurePosixPath(member.name).parts):
                        raise EvidenceError("corpus member too large")
                    with archive.extractfile(member) as stream:
                        ingest(member.name, stream.read)
    return validate_corpus({"schema_version": 1, "source": manifest["source"],
                           "records": sorted(records.values(), key=lambda r: r["task_id"])})
