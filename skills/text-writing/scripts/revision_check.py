"""Read-only revision diagnostics; observations, not a factuality or style score."""
from __future__ import annotations

import argparse
from bisect import bisect_right
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import re
import statistics
from typing import Any

MAX_BYTES = 2_000_000
NUMBER = r"[+\-−]?(?:\d{1,3}(?:[ \u00a0\u202f]\d{3})+|\d+)(?:[.,]\d+)?(?:[eE][+\-]?\d+)?"
BOUND_NUMBER = rf"(?<![\w.,]){NUMBER}(?!\w|[.,]\d)"
UNITS = (
    "KiB", "MiB", "GiB", "TiB", "KB", "MB", "GB", "TB", "kB", "B",
    "ms", "min", "kg", "mg", "mcg", "µg", "μg", "mL", "ml", "km", "cm", "mm",
    "Hz", "kHz", "MHz", "GHz", "s", "h", "g", "L", "m", "°C", "°F", "%",
    "USD", "EUR", "RUB", "руб", "мс", "сек", "мин", "кг", "мг", "мкг", "мл",
    "км", "см", "мм", "ГБ", "МБ", "КБ", "ч", "г", "л", "м", "₽", "$", "€", "£",
)
UNIT = "(?:" + "|".join(re.escape(unit) for unit in sorted(UNITS, key=len, reverse=True)) + ")"
PATTERNS = (
    ("url", re.compile(r"https?://[^\s<>\"'`]+")),
    ("date", re.compile(r"(?<!\w)(?:\d{4}-\d{2}-\d{2}|\d{2}[./]\d{2}[./]\d{4})(?!\w)")),
    ("version", re.compile(r"(?<!\w)(?:v\d+(?:\.\d+){1,3}|\d+(?:\.\d+){2,3})(?:-[\w.-]+)?(?!\w)")),
    ("quantity", re.compile(rf"(?<![\w.,])(?P<number>{NUMBER})\s*(?P<unit>{UNIT})(?!\w)")),
    ("currency", re.compile(rf"(?<!\w)(?P<unit>[$€£₽])\s*(?P<number>{NUMBER})(?!\w|[.,]\d)")),
    ("number", re.compile(BOUND_NUMBER)),
)
WORD = re.compile(r"[^\W\d_]+(?:[-'’][^\W\d_]+)*|\d+(?:[.,]\d+)?", re.UNICODE)
LIMITS = (
    "Exact token comparison cannot verify truth, entailment, negation, modality, "
    "attribution, deadlines or what a number counts. Equal inventories can hide changed meaning. "
    "Units, numeric date forms and HTTP(S) URLs are recognized conservatively; "
    "written-out numbers, names, relative links and arbitrary units are not covered. "
    "A source match is provenance, not proof that a claim is supported."
)


def numeric_key(value: str) -> str:
    return re.sub(r"[ \u00a0\u202f]", "", value).replace("−", "-")


def extract(text: str, label: str) -> list[dict[str, Any]]:
    """Keep offsets; consume URLs/dates before their embedded numeric tokens."""
    occupied = bytearray(len(text))
    newlines = [-1, *[match.start() for match in re.finditer("\n", text)]]
    records: list[dict[str, Any]] = []
    for kind, pattern in PATTERNS:
        for match in pattern.finditer(text):
            start, end = match.span()
            if any(occupied[start:end]):
                continue
            value = match.group()
            if kind == "url":
                value = value.rstrip(".,;:!?")
                while value.endswith(")") and value.count(")") > value.count("("):
                    value = value[:-1]
                end = start + len(value)
            if kind == "version":
                value = value.rstrip(".")
                end = start + len(value)
            occupied[start:end] = b"\1" * (end - start)
            if kind in ("quantity", "currency"):
                key = numeric_key(match.group("number")) + " " + match.group("unit")
                record_kind = "quantity"
            else:
                key = numeric_key(value) if kind == "number" else value
                record_kind = kind
            line = bisect_right(newlines, start - 1)
            records.append({
                "kind": record_kind, "key": key, "text": value,
                "source": label, "line": line, "column": start - newlines[line - 1],
            })
    return sorted(records, key=lambda item: (item["line"], item["column"]))


def inventory(records: list[dict[str, Any]]) -> dict[tuple[str, str], list[dict[str, Any]]]:
    result: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        result[(record["kind"], record["key"])].append(record)
    return result


def fact_changes(before: str, after: str, sources: list[str]) -> dict[str, Any]:
    old = inventory(extract(before, "before"))
    new = inventory(extract(after, "after"))
    evidence = inventory([item for n, source in enumerate(sources, 1)
                          for item in extract(source, f"source[{n}]")])
    changes, supported = [], []
    for key in sorted(new.keys() - old.keys()):
        item = {"direction": "added", "kind": key[0], "value": key[1], "locations": new[key]}
        if key in evidence:
            supported.append(dict(item, source_matches=evidence[key]))
        else:
            changes.append(item)
    for key in sorted(old.keys() - new.keys()):
        changes.append({"direction": "removed", "kind": key[0], "value": key[1], "locations": old[key]})
    return {
        "status": "review" if changes else "observed" if old or new else "unverified",
        "coverage": {"before_occurrences": sum(map(len, old.values())),
                     "after_occurrences": sum(map(len, new.values())),
                     "source_occurrences": sum(map(len, evidence.values()))},
        "changes": changes, "source_backed_additions": supported,
        "limits": LIMITS,
    }


def prose(text: str) -> tuple[str, int, int]:
    """A small explicit Markdown subset, not a replacement for text_check.py."""
    lines = text.splitlines()
    if lines and lines[0].strip() == "---":
        closing = next((n for n in range(1, len(lines)) if lines[n].strip() in ("---", "...")), None)
        if closing is None:
            raise ValueError("unclosed frontmatter")
        lines = lines[closing + 1:]
    kept: list[str] = []
    fence = ""
    headings = items = 0
    for line in lines:
        marker = re.match(r"^ {0,3}(`{3,}|~{3,})(.*)$", line)
        if fence:
            if marker and marker[1][0] == fence[0] and len(marker[1]) >= len(fence) and not marker[2].strip():
                fence = ""
                kept.append("")
            continue
        if marker:
            fence = marker[1]
            kept.append("")
            continue
        if re.match(r"^(?: {4}|\t)\S", line) or re.search(r"</?[A-Za-z][^>]*>", line) or "|" in line:
            raise ValueError("style subset excludes indented code, HTML and tables")
        if re.match(r"^ {0,3}#{1,6}\s+", line):
            headings += 1
            kept.append("")
            continue
        if re.match(r"^\s*(?:[-+*]|\d+[.)])\s+", line):
            items += 1
            line = re.sub(r"^\s*(?:[-+*]|\d+[.)])\s+", "", line)
        line = re.sub(r"(`+)(.*?)\1", "", line)
        line = re.sub(r"https?://\S+", "", line)
        kept.append(line)
    if fence:
        raise ValueError("unclosed code fence")
    return "\n".join(kept), headings, items


def style_metrics(text: str, language: str, minimum: int) -> dict[str, Any]:
    if language not in ("en", "ru"):
        return {"status": "unverified", "reason": "word segmentation supports only explicit en or ru"}
    try:
        body, headings, items = prose(text)
    except ValueError as error:
        return {"status": "unverified", "reason": str(error)}
    words = WORD.findall(body)
    if len(words) < minimum:
        return {"status": "unverified", "reason": "below requested minimum prose-word coverage",
                "word_count": len(words), "minimum_words": minimum}
    lengths = [len(WORD.findall(part)) for part in re.split(r"[.!?]+(?:\s+|$)", body)]
    lengths = [length for length in lengths if length]
    paragraphs = [part for part in re.split(r"\n\s*\n", body) if WORD.search(part)]
    mean = statistics.mean(lengths)
    return {"status": "observed", "metrics": {
        "words": len(words), "sentence_segments": len(lengths), "paragraphs": len(paragraphs),
        "headings": headings, "list_items": items,
        "mean_sentence_words": round(mean, 3),
        "sentence_length_cv": round(statistics.pstdev(lengths) / mean, 3) if len(lengths) >= 2 else None,
        "segments_at_most_five_words": sum(length <= 5 for length in lengths),
    }}


def style_changes(before: str, after: str, language: str, minimum: int, terms: list[str]) -> dict[str, Any]:
    old, new = (style_metrics(text, language, minimum) for text in (before, after))
    result: dict[str, Any] = {"status": "unverified", "language": language,
                             "calibration": "none; no quality or authorship inference",
                             "before": old, "after": new,
                             "limits": "Sentence splitting is approximate (abbreviations and lists can distort it). "
                                       "Coverage minimum is an operational guard, not a research-derived quality threshold."}
    if old["status"] != "observed" or new["status"] != "observed":
        return result
    delta = {key: round(new["metrics"][key] - value, 3)
             for key, value in old["metrics"].items()
             if value is not None and new["metrics"][key] is not None}
    questions = []
    if delta["sentence_segments"] > 0 and delta["mean_sentence_words"] < 0:
        questions.append("Was fragmentation requested, and are the connections still clear?")
    if delta["headings"] < 0 or delta["list_items"] < 0:
        questions.append("Was the removed structure useful for navigation or the reader's next action?")
    term_counts = []
    for term in terms:
        pattern = re.compile(r"(?<!\w)" + re.escape(term) + r"(?!\w)")
        counts = [len(pattern.findall(text)) for text in (before, after)]
        term_counts.append({"term": term, "before": counts[0], "after": counts[1]})
        if counts[0] and not counts[1]:
            questions.append(f"Was removing the supplied term {term!r} intended? Repetition alone is not a defect.")
    result.update(status="observed", delta=delta, term_counts=term_counts,
                  review_questions=questions, interpretation="Directional observations, not overediting verdicts.")
    return result


def analyze(before: str, after: str, *, sources: list[str] | None = None,
            style: bool = False, language: str = "unknown", minimum: int = 100,
            terms: list[str] | None = None) -> dict[str, Any]:
    sources, terms = sources or [], terms or []
    if terms and not style:
        raise ValueError("term observations require --style")
    if minimum < 1 or any(not term.strip() for term in terms):
        raise ValueError("minimum must be positive and terms must be nonempty")
    if any(not text.strip() or "\x00" in text for text in (before, after, *sources)):
        raise ValueError("inputs must contain nonempty text without NUL bytes")
    facts = fact_changes(before, after, sources)
    stylistic = style_changes(before, after, language, minimum, terms) if style else {"status": "not-requested"}
    status = facts["status"]
    if style:
        status = "unverified" if stylistic["status"] == "unverified" else "review" if facts["changes"] else "observed"
    return {"schema_version": 1, "status": status, "facts": facts, "style": stylistic,
            "claims": {"factuality": "unverified", "meaning_preservation": "unverified",
                       "writing_quality": "unverified"},
            "input_text_sha256": {label: hashlib.sha256(text.encode("utf-8")).hexdigest()
                             for label, text in [("before", before), ("after", after),
                                                 *[(f"source[{n}]", text) for n, text in enumerate(sources, 1)]]}}


def exit_code(report: dict[str, Any], strict: bool) -> int:
    if report["status"] == "unverified":
        return 2
    return int(strict and bool(report["facts"]["changes"]))


def read_text(path: Path) -> str:
    with path.open("rb") as stream:
        data = stream.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise ValueError(f"input exceeds {MAX_BYTES} bytes: {path}")
    return data.decode("utf-8-sig")


def render(report: dict[str, Any]) -> str:
    lines = [f"revision diagnostics: {report['status']}"]
    if "error" in report:
        return "\n".join([*lines, report["error"]])
    facts = report["facts"]
    lines.append(f"facts: {facts['status']}; coverage: {json.dumps(facts['coverage'])}")
    for item in facts["changes"]:
        location = item["locations"][0]
        lines.append(f"  {item['direction']} {item['kind']} {json.dumps(item['value'], ensure_ascii=False)} "
                     f"at {location['source']}:{location['line']}:{location['column']}")
    for item in facts["source_backed_additions"]:
        lines.append("  source-backed addition (check entailment): " + json.dumps(item, ensure_ascii=False))
    lines.append("style: " + json.dumps(report["style"], ensure_ascii=False))
    lines.append(facts["limits"])
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("before", type=Path)
    parser.add_argument("after", type=Path)
    parser.add_argument("--source", type=Path, action="append", default=[])
    parser.add_argument("--style", action="store_true")
    parser.add_argument("--language", default="unknown")
    parser.add_argument("--min-style-words", type=int, default=100)
    parser.add_argument("--term", action="append", default=[])
    parser.add_argument("--strict", action="store_true", help="exit 1 on unreviewed token changes; not a truth judgment")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        report = analyze(read_text(args.before), read_text(args.after),
                         sources=[read_text(path) for path in args.source], style=args.style,
                         language=args.language, minimum=args.min_style_words, terms=args.term)
        code = exit_code(report, args.strict)
    except (OSError, UnicodeError, ValueError) as error:
        report, code = {"schema_version": 1, "status": "unverified", "error": str(error)}, 2
    print(json.dumps(report, ensure_ascii=False, indent=2) if args.json else render(report))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
