"""Optional CPU-only encoder in the existing cancellable process boundary."""
from __future__ import annotations

import json
import os
from pathlib import Path
import sys


def similarities(path, query, texts, *, seconds):
    from .core import EvidenceError, encoded
    from .history import _refuse_link_ancestors
    from .processes import ProcessScope
    if path is None or not Path(path).is_dir():
        raise EvidenceError("semantic encoder must be installed locally")
    _refuse_link_ancestors(Path(path))
    if len(texts) > 2048:
        raise EvidenceError("semantic slice exceeds CPU bound")
    scope = ProcessScope(seconds)
    try:
        result = json.loads(scope.run([sys.executable, "-B", str(Path(__file__).resolve())],
            encoded({"path": str(Path(path).resolve()), "query": query, "texts": texts})))
    finally:
        scope.cancel()
    if not isinstance(result, list) or len(result) != len(texts):
        raise EvidenceError("semantic encoder unavailable")
    return result


def main():
    os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", TOKENIZERS_PARALLELISM="false")
    try:
        data = json.loads(sys.stdin.buffer.read(9 * 1024 * 1024))
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer(data["path"], device="cpu", local_files_only=True, trust_remote_code=False)
        vectors = model.encode([data["query"], *data["texts"]], normalize_embeddings=True, show_progress_bar=False)
        print(json.dumps([float(v @ vectors[0]) for v in vectors[1:]], allow_nan=False))
    except Exception:
        # Never echo query, paths or library diagnostics into an advisor context.
        print("null")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
