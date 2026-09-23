"""Public-source adapters. Parse measurements; never execute downloaded code."""
from __future__ import annotations

import email.utils
import math
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser

from .cache import FetchError
from .model_names import model_identity
from .core import MAX_BYTES, EvidenceError, effort, identity, loads, number, validate_snapshot

# Endpoints, not a model ranking. A new model needs no code change. New benchmark
# revisions are explicit because changed task sets must not be silently pooled.
SOURCES = {
    "deepswe": {"id": "deepswe", "benchmark": "DeepSWE", "version": "1.1",
                "url": "https://deepswe.datacurve.ai/artifacts/v1.1/leaderboard-live.json",
                "page": "https://deepswe.datacurve.ai/", "adapter": "deepswe", "revision": 3},
    "cursorbench": {"id": "cursorbench", "benchmark": "CursorBench", "version": "4.0",
                    "url": "https://prod.cursor.com/evals", "adapter": "table", "revision": 5},
    "frontiercode": {"id": "frontiercode", "benchmark": "FrontierCode", "version": "1.1",
                     "url": "https://cognition.com/frontiercode", "adapter": "browser", "revision": 4},
    "terminal-bench": {"id": "terminal-bench", "benchmark": "Terminal-Bench", "version": "4.0",
                       "url": "https://www.tbench.ai/", "adapter": "browser", "revision": 5,
                       "preferred_data": "harbor-public-api"},
}
for key, name in (("qna", "Codebase QnA"), ("tw", "Test Writing"), ("refactoring", "Refactoring")):
    sid = "swe-atlas-" + key
    SOURCES[sid] = {"id": sid, "benchmark": "SWE Atlas " + name, "version": "unversioned",
                    "url": "https://labs.scale.com/leaderboard/sweatlas-" + key,
                    "adapter": "atlas", "revision": 3}


def snapshot(source: dict, rows: list, updated=None, warnings=None) -> dict:
    return validate_snapshot({"schema_version": 1, "source_id": source["id"],
                              "source_url": source["url"], "benchmark": source["benchmark"],
                              "version": source["version"], "source_updated_at": updated,
                              "warnings": warnings or [], "rows": rows})


def base_row(model, reasoning, harness, subset="all", metric="resolve_rate"):
    return {"model": model, "effort": reasoning, "harness": harness,
            "subset": subset, "metric": metric, "protocol": "publisher-default",
            "score_low": None, "score_high": None, "evaluated_at": None}


def deepswe(source: dict, body: str) -> dict:
    data = loads(body)
    if not isinstance(data, dict) or not isinstance(data.get("rows"), list):
        raise EvidenceError("DeepSWE: expected rows array")
    rows = []
    for item in data["rows"]:
        if not isinstance(item, dict):
            raise EvidenceError("DeepSWE: malformed row")
        row = base_row(item.get("model"), item.get("reasoning_effort"), item.get("harness"),
                       metric="pass_at_1")
        # pass_at_4 is not an alternative spelling of pass_at_1.
        row.update(score=item.get("pass_at_1"), score_low=item.get("ci_lo"),
                   score_high=item.get("ci_hi"), cost_usd=item.get("mean_cost_usd"),
                   output_tokens=item.get("mean_output_tokens"),
                   duration_seconds=item.get("mean_duration_seconds"), steps=item.get("mean_agent_steps"),
                   cost_basis=item.get("cost_basis") or "publisher API pricing; date not specified",
                   sample_count=item.get("n_attempted"), task_count=item.get("n_tasks_attempted"),
                   configuration=item.get("config"), ci_method=item.get("ci_method"),
                   token_details={k: v for k, v in item.items() if k.startswith("mean_")
                                  and ("tokens" in k or k == "mean_compute_units")},
                   protocol="scored-attempts; provider/verifier/network errors excluded")
        rows.append(row)
    return snapshot(source, rows, data.get("generated_at"),
                    ["Costs use the artifact's published tariff, not subscription quota.",
                     "Harness version and per-row evaluation date are not supplied."])


class Page(HTMLParser):
    """Small HTML reader for visible text and tables; excludes executable data."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts, self.tables = [], []
        self.skip = 0
        self.table = self.row = self.cell = None
        self.headings, self.heading = [], None

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "noscript", "svg"):
            self.skip += 1
        if self.skip:
            return
        if tag in ("p", "div", "h1", "h2", "h3", "li", "tr", "br"):
            self.parts.append("\n")
        if tag == "h1":
            self.heading = []
        if tag == "table":
            self.table = []
        elif tag == "tr" and self.table is not None:
            self.row = []
        elif tag in ("th", "td") and self.row is not None:
            self.cell = []

    def handle_endtag(self, tag):
        if tag in ("script", "style", "noscript", "svg"):
            self.skip = max(0, self.skip - 1)
            return
        if self.skip:
            return
        if tag == "h1" and self.heading is not None:
            self.headings.append(" ".join("".join(self.heading).split()))
            self.heading = None
        if tag in ("th", "td") and self.cell is not None:
            self.row.append(" ".join("".join(self.cell).split()))
            self.cell = None
        elif tag == "tr" and self.row is not None:
            self.table.append(self.row)
            self.row = None
        elif tag == "table" and self.table is not None:
            self.tables.append(self.table)
            self.table = None
        self.parts.append(" " if tag in ("span", "td", "th") else "\n")

    def handle_data(self, data):
        if not self.skip:
            self.parts.append(data)
            if self.heading is not None:
                self.heading.append(data)
            if self.cell is not None:
                self.cell.append(data)

    @property
    def visible(self):
        return "\n".join(" ".join(line.split()) for line in "".join(self.parts).splitlines() if line.strip())


def parse_page(body: str) -> Page:
    page = Page()
    page.feed(body)
    return page


def quantity(value: str, *, percent=False):
    value = value.strip().replace(",", "").replace("$", "")
    if value in ("", "—", "-", "N/A", "n/a"):
        return None
    if percent:
        found = re.fullmatch(r"(\d+(?:\.\d+)?)\s*%(?:\s*[±].*)?", value)
        if not found:
            raise EvidenceError("score must have an explicit percentage unit")
        return float(found[1]) / 100
    found = re.fullmatch(r"(\d+(?:\.\d+)?)\s*([kKmMbB]?)", value)
    if not found:
        raise EvidenceError("unrecognized numeric cell")
    return float(found[1]) * {"": 1, "k": 1000, "m": 1000000, "b": 1000000000}[found[2].lower()]


def table_header(label):
    return " ".join(label.lower().replace("▼", "").replace("▲", "").split())


EFFORT_SUFFIX = re.compile(r"(?:\s+|\[|\()(extra high|xhigh|max|high|medium|low|minimal|none)\s*[\])]?\*?$", re.I)


def split_model(label: str):
    label = label.strip()
    match = EFFORT_SUFFIX.search(label)
    return (label[:match.start()].strip(), effort(match[1])) if match else (label, None)


def parse_tables(source: dict, tables: list, *, subset="all") -> list:
    aliases = {"model": "model", "agent": "harness", "harness": "harness",
               "effort": "effort", "reasoning effort": "effort", "score": "score",
               "resolution rate": "score", "mergeability": "score", "merge rate": "score",
               "cost": "cost_usd", "avg cost": "cost_usd", "avg cost / task": "cost_usd",
               "cost per task": "cost_usd", "tokens": "reported_tokens", "steps": "steps"}
    if source["id"] == "frontiercode":
        aliases.update({"cost / rollout": "cost_usd", "output tokens": "output_tokens"})
    if not isinstance(tables, list):
        raise EvidenceError("tables must be an array")
    rows = []
    seen = set()
    for table in tables:
        if not isinstance(table, list) or any(not isinstance(cells, list) or any(not isinstance(c, str) for c in cells) for cells in table):
            raise EvidenceError("malformed table cells")
        if not table:
            continue
        header = {}
        for i, label in enumerate(table[0]):
            label = table_header(label)
            if source["id"] == "cursorbench":
                # HTTP includes both responsive labels; rendered DOM includes
                # one. Recognize the publisher's per-task labels in either form.
                match = re.fullmatch(r"(cost|tokens|steps)\s*(?:\1\s*)?/\s*task", label)
                if match:
                    label = match[1]
            field = aliases.get(label)
            if field is not None:
                if field in header:
                    raise EvidenceError("ambiguous duplicate leaderboard columns")
                header[field] = i
        if "model" not in header or "score" not in header:
            continue
        if source["id"] == "cursorbench" and not {"cost_usd", "reported_tokens", "steps"} <= header.keys():
            raise EvidenceError("CursorBench: expected cost, tokens and steps columns; source layout changed")
        for cells in table[1:]:
            if len(cells) != len(table[0]):
                raise EvidenceError("leaderboard table row width changed")
            label = cells[header["model"]]
            if not label.strip():
                continue
            model, reasoning = split_model(label)
            if "effort" in header:
                reasoning = effort(cells[header["effort"]])
            default_harness = "Cursor" if source["id"] == "cursorbench" else "publisher-harness-unspecified"
            harness = cells[header["harness"]] if "harness" in header else default_harness
            row = base_row(model, reasoning, harness, subset, metric={"frontiercode": "mergeability", "cursorbench": "task_score"}.get(source["id"], "resolve_rate"))
            if source["id"] == "cursorbench":
                # Keep the publisher label; the annotation is source-scoped and
                # routing rechecks it against the current reviewed alias table.
                row["model_identity"] = model_identity("cursorbench", model)
            row["score"] = quantity(cells[header["score"]], percent=True)
            for key in ("cost_usd", "reported_tokens", "output_tokens", "steps"):
                row[key] = quantity(cells[header[key]]) if key in header else None
            row["cost_basis"] = "published API cost per task; not subscription quota"
            if source["id"] == "frontiercode":
                row["cost_basis"] = "published API cost per rollout; not subscription quota"
            elif source["id"] == "terminal-bench":
                row["cost_basis"] = "published aggregate run cost; normalization and budget unspecified; not subscription quota"
            row["protocol"] = "publisher-table; harness version and evaluation budget not supplied"
            # Responsive copies of the same table are common. Reject conflicting duplicates.
            key = (model, reasoning, harness, subset)
            if key in seen:
                previous = next(r for r in rows if (r["model"], r["effort"], r["harness"], r["subset"]) == key)
                if previous != row:
                    raise EvidenceError("conflicting duplicate leaderboard row")
                continue
            rows.append(row)
            seen.add(key)
    if not rows:
        raise EvidenceError("no supported leaderboard table; page may require a browser or adapter update")
    return rows


def table_snapshot(source, body):
    page = parse_page(body)
    heading_identity(source, page.headings[0] if page.headings else "")
    return snapshot(source, parse_tables(source, page.tables), warnings=[
        "Point estimates only; small differences may be noise.",
        "Tokens column semantics are unspecified; stored as reported_tokens, not output or total tokens.",
        "Source does not supply per-row evaluation dates or a machine-readable revision timestamp."])


def atlas(source, body):
    page = parse_page(body)
    if "Performance Comparison" not in page.visible:
        raise EvidenceError("SWE Atlas leaderboard section not found")
    section = page.visible.split("Performance Comparison", 1)[1].split("Legend", 1)[0]
    pattern = re.compile(r"(?:^|\n)\d+\s*\n(.+?)\s*\n(?:NEW\s*\n)?(\d+(?:\.\d+)?)\s*±\s*(\d+(?:\.\d+)?)", re.S)
    rows = []
    for match in pattern.finditer(section):
        label = " ".join(match[1].split())
        score, ci = float(match[2]) / 100, float(match[3]) / 100
        scaffold = re.search(r"\((Claude Code|Codex|Mini-SWE-Agent)\)", label, re.I)
        harness = scaffold[1] if scaffold else "publisher-harness-unspecified"
        if scaffold:
            label = label.replace(scaffold[0], "")
        model, reasoning = split_model(label)
        row = base_row(model, reasoning, harness, metric="strict_task_resolve_rate")
        row.update(score=score, score_low=max(0, score - ci), score_high=min(1, score + ci),
                   protocol="publisher-table; per-row step budget and harness version unverified")
        rows.append(row)
    return snapshot(source, rows, warnings=[
        "Quality-only evidence: the leaderboard does not publish comparable per-task costs.",
        "Unversioned leaderboard; comparisons are confined to this snapshot and harness.",
        "Missing effort remains unknown and is never mapped to a client's default."])


class SameHostRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        old, new = urllib.parse.urlsplit(req.full_url), urllib.parse.urlsplit(newurl)
        if new.scheme != "https" or new.netloc != old.netloc:
            raise FetchError("cross-origin redirect refused; update the source definition")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def retry_delay(value):
    if not value:
        return 0
    try:
        delay = float(value)
        return min(86400, max(0, delay)) if math.isfinite(delay) else 0
    except ValueError:
        try:
            return min(86400, max(0, email.utils.parsedate_to_datetime(value).timestamp() - time.time()))
        except (ValueError, TypeError, OverflowError):
            return 0


def needs_browser(source):
    """Whether only the optional browser adapter can acquire this source."""
    return source["adapter"] == "browser" and source.get("preferred_data") is None


class Fetcher:
    def __init__(self, *, browser=False, timeout=15):
        number(timeout, "source timeout", upper=300)
        if timeout <= 0:
            raise EvidenceError("source timeout must be positive")
        self.browser, self.timeout = browser, timeout

    def __call__(self, source, validators):
        if source.get("preferred_data") == "harbor-public-api":
            from .terminal_hub import ENDPOINT, HubUnavailable, fetch_snapshot
            started = time.monotonic()
            try:
                return fetch_snapshot(source, timeout=self.timeout), {}
            except HubUnavailable as exc:
                # No fallback on malformed/version-mismatched JSON, other client
                # errors or Retry-After. Browser access remains opt-in.
                if not self.browser or exc.retry_after:
                    raise
                remaining = self.timeout - (time.monotonic() - started)
                if remaining <= 0:
                    raise FetchError("terminal_hub_deadline_exceeded") from exc
                result = Fetcher(browser=True, timeout=remaining).browser_snapshot(source)
                result["warnings"].append("Preferred public API unavailable: " + str(exc))
                result["acquisition"] = {"kind": "browser_fallback", "url": source["url"],
                                         "preferred_url": ENDPOINT, "preferred_error": str(exc)}
                return result, {}
        if source["adapter"] == "browser":
            if not self.browser:
                raise FetchError("browser_disabled: this source needs the optional browser adapter")
            return self.browser_snapshot(source), {}
        headers = {"Accept": "application/json,text/html,text/markdown",
                   "User-Agent": "assay-benchmark-evidence/1"}
        for field, header in (("etag", "If-None-Match"), ("last_modified", "If-Modified-Since")):
            value = validators.get(field)
            if isinstance(value, str) and not any(c in value for c in "\r\n"):
                headers[header] = value
        request = urllib.request.Request(source["url"], headers=headers)
        try:
            with urllib.request.build_opener(SameHostRedirect()).open(request, timeout=self.timeout) as response:
                body = response.read(MAX_BYTES + 1)
                if len(body) > MAX_BYTES:
                    raise FetchError("source response exceeds size limit")
                body = body.decode("utf-8")
                result = {"etag": response.headers.get("ETag"),
                          "last_modified": response.headers.get("Last-Modified")}
        except urllib.error.HTTPError as exc:
            if exc.code == 304:
                return None, validators
            raise FetchError(f"source returned HTTP {exc.code}", retry_delay(exc.headers.get("Retry-After"))) from exc
        except (urllib.error.URLError, OSError, UnicodeError) as exc:
            raise FetchError("source transport failed: " + type(exc).__name__) from exc
        if source["adapter"] == "guide":
            from .guides import guide_snapshot
            return guide_snapshot(source, body), result
        parser = {"deepswe": deepswe, "table": table_snapshot, "atlas": atlas}[source["adapter"]]
        try:
            if source["adapter"] == "atlas":
                page = parse_page(body)
                heading_identity(source, page.headings[0] if page.headings else "")
            return parser(source, body), result
        except EvidenceError:
            if not self.browser or source["adapter"] == "deepswe":
                raise
            return self.browser_snapshot(source), {}

    def browser_snapshot(self, source):
        from .browser import capture
        return captured_snapshot(source, capture(source, timeout=self.timeout))


def heading_identity(source, heading, *, selected_version=None):
    heading = " ".join(heading.split())
    if source["version"] == "unversioned":
        if identity(heading) != identity(source["benchmark"]):
            raise FetchError("benchmark_identity_changed")
        return
    expected = source["benchmark"] + " " + source["version"]
    if heading.casefold() in (expected.casefold(), (expected + " Leaderboard").casefold()):
        return
    if (source["id"] == "frontiercode" and heading.casefold() == "frontiercode leaderboard"
            and selected_version == expected):
        return
    if (source["id"] == "terminal-bench" and heading.casefold() == "terminal-bench"
            and selected_version == expected):
        return
    raise FetchError("benchmark_revision_absent_or_changed")


def captured_snapshot(source, capture):
    if not isinstance(capture, dict) or not isinstance(capture.get("identity"), dict):
        raise FetchError("browser_capture_missing_identity")
    proof = capture["identity"]
    if not isinstance(proof.get("heading"), str):
        raise FetchError("browser_capture_missing_heading")
    heading_identity(source, proof["heading"], selected_version=proof.get("selected_version"))
    if source["adapter"] == "atlas":
        if not isinstance(capture.get("html"), str):
            raise FetchError("browser_capture_missing_html")
        return atlas(source, capture["html"])
    parts = capture.get("parts")
    expected = {"main", "extended"} if source["id"] == "frontiercode" else {"all"}
    if not isinstance(parts, list) or len(parts) != len(expected):
        raise FetchError("browser_capture_missing_subsets")
    if any(not isinstance(p, dict) for p in parts):
        raise FetchError("browser_capture_invalid_parts")
    if {p.get("subset") for p in parts} != expected:
        raise FetchError("browser_capture_invalid_subsets")
    rows = []
    for part in parts:
        if part.get("identity") != proof or part.get("observed_subset") != part["subset"]:
            raise FetchError("browser_capture_dataset_identity_mismatch")
        tables = part.get("tables")
        if not isinstance(tables, list) or len(tables) != 1:
            raise FetchError("browser_capture_ambiguous_table")
        rows.extend(parse_tables(source, tables, subset=part["subset"]))
    return snapshot(source, rows, warnings=[
        "Rendered-table integration; no stable publisher API or guaranteed selector compatibility.",
        "No per-row evaluation dates; API costs are not subscription-quota measurements."])
