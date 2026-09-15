"""Wire contracts. Unknown measurements remain unknown, never zero."""
from __future__ import annotations

import copy
import hashlib
import json
import math
import re
from datetime import datetime, timezone
from typing import Any

MAX_BYTES = 8 * 1024 * 1024
METRICS = ("cost_usd", "output_tokens", "total_tokens", "reported_tokens", "duration_seconds", "steps")


class EvidenceError(ValueError):
    """Invalid or unavailable evidence, not an invitation to guess a model."""


def loads(text: str) -> Any:
    def pairs(items):
        out = {}
        for key, value in items:
            if key in out:
                raise EvidenceError(f"duplicate JSON key: {key}")
            out[key] = value
        return out

    def constant(value):
        raise EvidenceError(f"non-finite JSON number: {value}")

    if len(text.encode("utf-8")) > MAX_BYTES:
        raise EvidenceError("document exceeds size limit")
    try:
        return json.loads(text, object_pairs_hook=pairs, parse_constant=constant)
    except (ValueError, RecursionError) as exc:
        raise EvidenceError(f"invalid JSON: {exc}") from exc


def encoded(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True,
                       allow_nan=False, separators=(",", ":")) + "\n").encode()


def digest(value: Any) -> str:
    return hashlib.sha256(encoded(value)).hexdigest()


def timestamp(now: float) -> str:
    return datetime.fromtimestamp(now, timezone.utc).isoformat().replace("+00:00", "Z")


def epoch(value: str) -> float:
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            raise ValueError("timezone required")
        return dt.timestamp()
    except (ValueError, TypeError, AttributeError) as exc:
        raise EvidenceError("expected an ISO 8601 timestamp with timezone") from exc


def text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > 500:
        raise EvidenceError(f"{field}: expected a nonempty string of at most 500 characters")
    if any(ord(ch) < 32 for ch in value):
        raise EvidenceError(f"{field}: control characters are not allowed")
    return value.strip()


def number(value: Any, field: str, *, upper: float | None = None) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise EvidenceError(f"{field}: expected a number")
    try:
        value = float(value)
    except (ValueError, OverflowError) as exc:
        raise EvidenceError(f"{field}: number outside allowed range") from exc
    if not math.isfinite(value) or value < 0 or (upper is not None and value > upper):
        raise EvidenceError(f"{field}: number outside allowed range")
    return value


def identity(value: str) -> str:
    """Only lexical normalization; never infer versions, aliases or capabilities."""
    return "-".join(re.findall(r"[a-z]+|[0-9]+", value.lower()))


def effort(value: str | None) -> str | None:
    if value is None:
        return None
    value = text(value, "effort").lower().replace("extra high", "xhigh")
    return value  # Do not equate max, xhigh, high, adaptive, or unspecified.


def validate_snapshot(data: Any) -> dict:
    if not isinstance(data, dict) or data.get("schema_version") != 1:
        raise EvidenceError("snapshot: expected schema_version=1")
    data = copy.deepcopy(data)
    warnings = data.get("warnings", [])
    if not isinstance(warnings, list) or any(not isinstance(w, str) for w in warnings):
        raise EvidenceError("warnings must be a list of strings")
    for key in ("source_id", "source_url", "benchmark", "version"):
        text(data.get(key), key)
    if not data["source_url"].startswith("https://"):
        raise EvidenceError("source_url must use HTTPS")
    generated = data.get("source_updated_at")
    if generated is not None:
        epoch(generated)
    rows = data.get("rows")
    if not isinstance(rows, list) or not rows or len(rows) > 10000:
        raise EvidenceError("snapshot must contain 1..10000 measured rows")
    seen = set()
    for row in rows:
        if not isinstance(row, dict):
            raise EvidenceError("row must be an object")
        for key in ("model", "harness", "subset", "metric", "protocol"):
            text(row.get(key), key)
        row["effort"] = effort(row.get("effort"))
        row["score"] = number(row.get("score"), "score", upper=1)
        for key in METRICS:
            value = row.get(key)
            if value is not None:
                row[key] = number(value, key)
            else:
                row[key] = None
        lo, hi = row.get("score_low"), row.get("score_high")
        if (lo is None) != (hi is None):
            raise EvidenceError("both confidence bounds or neither are required")
        if lo is not None:
            lo = number(lo, "score_low", upper=1)
            hi = number(hi, "score_high", upper=1)
            if not lo <= row["score"] <= hi:
                raise EvidenceError("confidence interval does not contain score")
        if row.get("cost_usd") is not None:
            text(row.get("cost_basis"), "cost_basis")
        if row.get("evaluated_at") is not None:
            epoch(row["evaluated_at"])
        key = (row["model"], row["effort"], row["harness"], row["subset"],
               row["metric"], row["protocol"])
        if key in seen:
            raise EvidenceError("duplicate configuration in the same cohort")
        seen.add(key)
    return data


def validate_guide(data: Any) -> dict:
    """Quoted vendor sections. Shortening may never drop a caveat or a source."""
    if not isinstance(data, dict) or data.get("schema_version") != 1:
        raise EvidenceError("guide: expected schema_version=1")
    data = copy.deepcopy(data)
    for key in ("guide_id", "publisher", "source_url", "document_title", "canonical_url", "content_hash"):
        text(data.get(key), key)
    for key in ("source_url", "canonical_url"):
        if not data[key].startswith("https://"):
            raise EvidenceError(key + " must use HTTPS")
    if type(data.get("extractor_version")) is not int or data["extractor_version"] < 1:
        raise EvidenceError("guide requires an integer extractor_version")
    clients = data.get("applies_to")
    if not isinstance(clients, list) or not clients or any(not isinstance(c, str) for c in clients):
        raise EvidenceError("guide must declare the clients it applies to")
    caveats = data.get("document_caveats")
    if not isinstance(caveats, list) or len(caveats) > 8:
        raise EvidenceError("guide document caveats must be a bounded list")
    sections = data.get("retrieved_sections")
    if not isinstance(sections, list) or not 1 <= len(sections) <= 4:
        raise EvidenceError("guide must carry 1..4 extracted sections")
    for section in sections:
        if not isinstance(section, dict):
            raise EvidenceError("guide section must be an object")
        for key in ("section", "anchor", "url"):
            text(section.get(key), key)
        if not isinstance(section.get("excerpt"), str):
            raise EvidenceError("guide excerpt must be a string")
        if len(section["excerpt"]) > 4000:
            raise EvidenceError("guide excerpt exceeds the size limit")
        for key in ("truncated",):
            if not isinstance(section.get(key), bool):
                raise EvidenceError("guide section requires an explicit " + key)
        caveats = section.get("caveats")
        if not isinstance(caveats, list) or len(caveats) > 8:
            raise EvidenceError("guide caveats must be a bounded list")
        for caveat in caveats:
            if not isinstance(caveat, dict) or not isinstance(caveat.get("text"), str):
                raise EvidenceError("guide caveat must carry its text")
            text(caveat.get("kind"), "caveat kind")
    return data


def read_document(path):
    """Bound reads before JSON decoding (also used for stdin and configuration)."""
    with path.open("rb") as stream:
        return loads(stream.read(MAX_BYTES + 1).decode("utf-8"))
