"""Anonymous, bounded reads of the publisher's Terminal-Bench 4.0 board.

The public application identifier and read contract are published in Harbor:
https://github.com/harbor-framework/harbor/blob/9faf488373fbeea62ccca682dd2dbba5dab1d08c/src/harbor/auth/constants.py
https://github.com/harbor-framework/harbor/blob/9faf488373fbeea62ccca682dd2dbba5dab1d08c/src/harbor/hub/leaderboards.py
Metric units and the board identity come from the benchmark owner, not a mirror:
https://github.com/harbor-framework/terminal-bench/blob/3b5caaa4863d64dda7f0957bf4fc2d4f019202d4/leaderboard/leaderboard.yaml
"""
from __future__ import annotations

import time
import urllib.error
import urllib.request

from .cache import FetchError
from .core import MAX_BYTES, EvidenceError, digest, encoded, loads, number, text, validate_snapshot

ENDPOINT = "https://ofhuhcpkvzjlejydnvyd.supabase.co/functions/v1/leaderboard-read"
# Publisher-owned public application identifier, NOT a user secret or bearer.
PUBLISHABLE_KEY = "sb_publishable_Z-vuQbpvpG-PStjbh4yE0Q_e-d3MTIH"
BOARD_ID = "9f966760-00f1-424e-90f5-c964fb6f6091"
PACKAGE = "terminal-bench/terminal-bench"
BOARD_NAME = "4-0-0"
PAGE_SIZE = 100
MAX_PAGES = 100


class HubUnavailable(FetchError):
    """Unavailable or refusing endpoint; an explicitly enabled browser may substitute."""


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise FetchError("terminal_hub_redirect_refused")


def fetch_page(body: dict, timeout: float) -> bytes:
    """Read public data only; no credential discovery, cookies, or SDK execution."""
    from .providers import retry_delay
    request = urllib.request.Request(ENDPOINT, data=encoded(body), method="POST", headers={
        "Content-Type": "application/json", "Accept": "application/json",
        "User-Agent": "assay-benchmark-evidence/1", "apikey": PUBLISHABLE_KEY})
    try:
        with urllib.request.build_opener(NoRedirect()).open(request, timeout=timeout) as response:
            content = response.read(MAX_BYTES + 1)
            if len(content) > MAX_BYTES:
                raise FetchError("terminal_hub_response_too_large")
            return content
    except urllib.error.HTTPError as exc:
        # A refused anonymous read (401/403, e.g. a rotated application key)
        # leaves this API unavailable, like 404/410/5xx: an enabled browser may
        # read the same public page. Throttling and other client errors never do.
        error = HubUnavailable if exc.code in (401, 403, 404, 410) or exc.code >= 500 else FetchError
        raise error("terminal_hub_http_%d" % exc.code,
                    retry_delay(exc.headers.get("Retry-After"))) from exc
    except (urllib.error.URLError, OSError) as exc:
        raise HubUnavailable("terminal_hub_transport_failed: " + type(exc).__name__) from exc


def positive_int(value, field, *, allow_zero=False, maximum=10000):
    if type(value) is not int or not (0 if allow_zero else 1) <= value <= maximum:
        raise FetchError("terminal_hub_invalid_" + field)
    return value


def parse_page(payload: dict):
    """Require a paged, public, exact-version board; partial data is not success."""
    if not isinstance(payload, dict) or not isinstance(payload.get("leaderboard"), dict):
        raise FetchError("terminal_hub_missing_board")
    board = payload["leaderboard"]
    if (board.get("id") != BOARD_ID or board.get("name") != BOARD_NAME
            or board.get("title") != "Terminal-Bench 4.0" or board.get("visibility") != "public"
            or board.get("package") not in (None, PACKAGE)):
        raise FetchError("terminal_hub_board_identity_changed")
    rows = payload.get("rows", board.get("rows"))
    page = payload.get("pagination")
    if not isinstance(rows, list) or not isinstance(page, dict):
        raise FetchError("terminal_hub_missing_rows_or_pagination")
    total = positive_int(page.get("total"), "total", allow_zero=True)
    pages = positive_int(page.get("total_pages"), "total_pages", allow_zero=True, maximum=MAX_PAGES)
    if pages != (total + PAGE_SIZE - 1) // PAGE_SIZE:
        raise FetchError("terminal_hub_inconsistent_pagination")
    # A board timestamp is source metadata, not the evaluation date of a row.
    version = {key: value for key, value in board.items() if key != "rows"}
    return board, rows, total, pages, digest(version)


def measured_row(item):
    if not isinstance(item, dict):
        raise FetchError("terminal_hub_invalid_row")
    if item.get("status") == "hide":
        return None
    if item.get("status") != "display":
        raise FetchError("terminal_hub_unknown_row_status")
    meta, metrics = item.get("metadata"), item.get("metrics")
    if not isinstance(meta, dict) or not isinstance(metrics, dict):
        raise FetchError("terminal_hub_missing_row_fields")
    model_display, agent_display = meta.get("model_display"), meta.get("agent_display")
    if not isinstance(model_display, dict) or not isinstance(agent_display, dict):
        raise FetchError("terminal_hub_missing_display_identity")
    score = number(metrics.get("accuracy"), "accuracy", upper=100) / 100
    width = number(metrics.get("accuracy_ci95_half_width"), "accuracy_ci95_half_width", upper=100) / 100
    reasoning = meta.get("reasoning_effort")
    if reasoning in (None, "", "unknown", "unspecified", "N/A", "—"):
        reasoning = None
    aggregates = {}
    for key in ("total_cost_usd", "total_tokens", "output_tokens", "cached_input_tokens", "uncached_input_tokens"):
        if metrics.get(key) is not None:
            aggregates[key] = number(metrics[key], key)
    return {"model": text(model_display.get("label"), "model display"),
            "effort": reasoning, "harness": text(agent_display.get("label"), "agent display"),
            "subset": "all", "metric": "accuracy", "score": score,
            "score_low": max(0, score - width), "score_high": min(1, score + width),
            "protocol": "publisher-hub-curated; harness version and evaluation budget unspecified",
            "evaluated_at": None, "publisher_row_id": text(item.get("id"), "publisher row id"),
            "published_date": meta.get("date"),
            "sample_count": number(metrics.get("n_trials"), "n_trials"),
            "aggregate_usage": aggregates}


def fetch_snapshot(source, *, timeout, reader=None, clock=time.monotonic):
    """Complete all pages within one deadline/byte budget; do not execute remote code."""
    if source.get("id") != "terminal-bench" or source.get("version") != "4.0":
        raise FetchError("terminal_hub_source_identity_changed")
    number(timeout, "source timeout", upper=300)
    if timeout <= 0:
        raise FetchError("terminal_hub_deadline_exceeded")
    reader = reader or fetch_page
    deadline, byte_count, all_rows, ids = clock() + timeout, 0, [], set()
    expected = None
    for page_number in range(1, MAX_PAGES + 1):
        remaining = deadline - clock()
        if remaining <= 0:
            raise FetchError("terminal_hub_deadline_exceeded")
        body = {"leaderboard_id": BOARD_ID, "page": page_number, "page_size": PAGE_SIZE}
        raw = reader(body, remaining)
        if not isinstance(raw, bytes):
            raise FetchError("terminal_hub_invalid_transport_bytes")
        byte_count += len(raw)
        if byte_count > MAX_BYTES:
            raise FetchError("terminal_hub_response_too_large")
        try:
            payload = loads(raw.decode("utf-8"))
        except UnicodeError as exc:
            raise FetchError("terminal_hub_invalid_utf8") from exc
        board, rows, total, pages, revision = parse_page(payload)
        if expected is None:
            expected = (total, pages, revision)
        elif expected != (total, pages, revision):
            raise FetchError("terminal_hub_changed_during_pagination")
        pagination = payload["pagination"]
        if pagination.get("page", page_number) != page_number or pagination.get("page_size", PAGE_SIZE) != PAGE_SIZE:
            raise FetchError("terminal_hub_wrong_page")
        if len(rows) != min(PAGE_SIZE, total - (page_number - 1) * PAGE_SIZE):
            raise FetchError("terminal_hub_incomplete_page")
        for item in rows:
            if not isinstance(item, dict):
                raise FetchError("terminal_hub_invalid_row")
            row_id = text(item.get("id"), "publisher row id")
            if row_id in ids:
                raise FetchError("terminal_hub_duplicate_row_id")
            ids.add(row_id)
            measured = measured_row(item)
            if measured is not None:
                all_rows.append(measured)
        if page_number >= pages:
            if len(ids) != total:
                raise FetchError("terminal_hub_incomplete_board")
            if clock() > deadline:
                raise FetchError("terminal_hub_deadline_exceeded")
            return validate_snapshot({"schema_version": 1, "source_id": source["id"],
                "source_url": source["url"], "benchmark": source["benchmark"], "version": source["version"],
                "source_updated_at": board.get("updated_at"), "rows": all_rows,
                "acquisition": {"kind": "publisher_json_api", "url": ENDPOINT, "board_id": BOARD_ID,
                                "pages": page_number, "reported_rows": total, "anonymous": True},
                "warnings": ["API schema is grounded in publisher source; live endpoint availability is checked on each acquisition.",
                             "Aggregate run cost/tokens are retained in aggregate_usage, not compared as per-task expenses.",
                             "Release dates and board update times are not per-row evaluation dates.",
                             "Pagination consistency checks do not establish a transactional snapshot."]})
    raise FetchError("terminal_hub_page_limit")
