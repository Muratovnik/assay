"""Optional public-page capture with observable dataset identity.

This module never upgrades a generic click or an old version in a changelog
into proof that a table belongs to a selected dataset. Ambiguity is an error.
"""
from __future__ import annotations

import json
import os
import re
import time

from .cache import FetchError
from .providers import heading_identity, table_header


def active(control) -> bool:
    return (control.get_attribute("aria-selected") == "true"
            or control.get_attribute("aria-pressed") == "true"
            or control.get_attribute("aria-current") in ("true", "page")
            or control.get_attribute("data-state") == "active")


def control_for(page, label, timeout=15):
    count = r"(?:\s*(?:\(\d+\s+tasks?\)|\d+))?" if label in ("Main", "Extended") else ""
    pattern = re.compile(r"^" + re.escape(label) + count + r"$", re.I)
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        for role in ("tab", "button"):
            control = page.get_by_role(role, name=pattern).filter(visible=True)
            count = control.count()
            if count == 1:
                return control
            if count > 1:
                raise FetchError("browser_layout_unsupported: ambiguous dataset control")
        page.wait_for_timeout(50)
    raise FetchError("browser_layout_unsupported: dataset control not found: " + label)


def scope_for(page, control=None):
    panel_id = control.get_attribute("aria-controls") if control is not None else None
    if panel_id:
        panel = page.locator("[id=" + json.dumps(panel_id) + "]")
        if panel.count() != 1 or not panel.is_visible():
            raise FetchError("browser_dataset_not_ready")
        return panel
    main = page.locator("main:visible")
    return main if main.count() == 1 else page.locator("body")


def table_rows(scope):
    if scope.locator('[aria-busy="true"]:visible').count():
        raise FetchError("browser_dataset_not_ready")
    tables = scope.locator("table:visible").evaluate_all(r"""tables => tables.map(t => {
        const trs = Array.from(t.querySelectorAll('tr'));
        const cells = trs.map(tr => Array.from(tr.querySelectorAll('th,td')));
        const text = c => Array.from(c.childNodes).map(n =>
            n.nodeType === Node.TEXT_NODE ? n.textContent :
            n.nodeType === Node.ELEMENT_NODE && n.getAttribute('aria-hidden') !== 'true'
                ? n.innerText || '' : '').join(' ').trim();
        const rows = cells.map(row => row.map(text));
        const model = rows[0]?.findIndex(h => h.toLowerCase() === 'model');
        if (model >= 0 && cells.length > 1 &&
            cells.slice(1).every(row => /^Harness: \S/.test(row[model]?.title || ''))) {
            rows[0].push('Harness');
            rows.slice(1).forEach((row, i) => row.push(cells[i+1][model].title.slice(9).trim()));
        }
        return rows;
    })""")
    suitable = []
    for table in tables:
        if len(table) < 2:
            continue
        header = {table_header(v) for v in table[0]}
        if "model" in header and header & {"score", "resolution rate", "mergeability", "merge rate"}:
            # Loading rows and spinners cannot count as a completed table.
            if any(len(row) != len(table[0]) for row in table[1:]):
                continue
            if not all(any(re.fullmatch(r"\d+(?:\.\d+)?\s*%(?:\s*±.*)?", cell) for cell in row)
                       for row in table[1:]):
                continue
            if table not in suitable:
                suitable.append(table)
    if len(suitable) != 1:
        raise FetchError("browser_layout_unsupported: expected one identifiable leaderboard table")
    return suitable[0]


def ready_table(page, *, control=None, previous=None, changed=False, timeout=15):
    deadline = time.monotonic() + timeout
    last, stable_at = None, None
    while time.monotonic() < deadline:
        try:
            if control is not None and not active(control):
                raise FetchError("browser_dataset_not_ready")
            current = table_rows(scope_for(page, control))
            if changed and previous is not None and current == previous:
                raise FetchError("browser_dataset_transition_unverified")
            if current != last:
                last, stable_at = current, time.monotonic()
            elif stable_at is not None and time.monotonic() - stable_at >= .3:
                return current
        except FetchError:
            last, stable_at = None, None
        page.wait_for_timeout(50)
    raise FetchError("browser_dataset_transition_unverified")


def observed_identity(page, source, version_control=None):
    headings = page.locator("h1:visible").all_text_contents()
    headings = list(dict.fromkeys(" ".join(h.split()) for h in headings))
    if len(headings) != 1:
        raise FetchError("browser_layout_unsupported: ambiguous active heading")
    selected = None
    if version_control is not None and active(version_control):
        selected = " ".join(version_control.inner_text().split())
    if source["id"] == "terminal-bench":
        benchmark = page.get_by_role("combobox", name="Benchmark", exact=True).filter(visible=True)
        if benchmark.count() == 1:
            # Animated h1 digits all appear in innerText. The named selector
            # supplies the active dataset; only the heading's own text names it.
            own_text = page.locator("h1:visible").evaluate(
                "e => [...e.childNodes].filter(n=>n.nodeType===Node.TEXT_NODE).map(n=>n.textContent).join('')")
            if own_text.strip().casefold() == "terminal-bench":
                headings = ["TERMINAL-BENCH"]
                selected = source["benchmark"] + " " + benchmark.inner_text().strip()
    heading_identity(source, headings[0], selected_version=selected)
    return {"heading": headings[0], "selected_version": selected}


def capture_page(page, source, *, timeout=15):
    """Separated from navigation so delayed DOM transitions can be regression-tested."""
    if source["adapter"] == "atlas":
        proof = observed_identity(page, source)
        page.get_by_text("Performance Comparison", exact=True).wait_for(timeout=timeout * 1000)
        return {"identity": proof, "html": page.content()}
    version_control = modes = None
    prior_version_table = None
    version_changed = False
    if source["id"] == "frontiercode":
        version_control = control_for(page, source["benchmark"] + " " + source["version"], timeout)
        if not active(version_control):
            try:
                prior_version_table = table_rows(scope_for(page))
            except FetchError:
                pass
            version_control.click(timeout=timeout * 1000)
            version_changed = True
        # The selected version must be observable, not merely present in a nav.
        end = time.monotonic() + timeout
        while not active(version_control) and time.monotonic() < end:
            page.wait_for_timeout(50)
        modes = control_for(page, "All reasoning levels", timeout)
        if not active(modes):
            prior_version_table = ready_table(page, timeout=timeout)
            modes.click(timeout=timeout * 1000)
            end = time.monotonic() + timeout
            while not active(modes) and time.monotonic() < end:
                page.wait_for_timeout(50)
            if not active(modes):
                raise FetchError("browser_dataset_not_ready")
            version_changed = True
    proof = observed_identity(page, source, version_control)
    parts = []
    for subset in (("Main", "Extended") if source["id"] == "frontiercode" else ("all",)):
        control = None if subset == "all" else control_for(page, subset, timeout)
        changed, previous = version_changed, prior_version_table
        if control is not None and not active(control):
            try:
                previous = table_rows(scope_for(page))
            except FetchError:
                previous = None
            control.click(timeout=timeout * 1000)
            changed = True
        rows = ready_table(page, control=control, previous=previous, changed=changed, timeout=timeout)
        final_proof = observed_identity(page, source, version_control)
        if final_proof != proof and source["id"] != "terminal-bench":
            raise FetchError("browser_dataset_identity_changed")
        # Terminal's static heading becomes animated during hydration. Both
        # observations were independently checked against this exact revision.
        if source["id"] == "terminal-bench":
            proof = final_proof
        if control is not None and not active(control):
            raise FetchError("browser_dataset_identity_changed")
        if modes is not None and not active(modes):
            raise FetchError("browser_reasoning_view_changed")
        parts.append({"subset": subset.lower(), "observed_subset": subset.lower(),
                      "identity": final_proof, "tables": [rows]})
        version_changed, prior_version_table = False, None
    return {"identity": proof, "parts": parts}


def capture(source, *, timeout=15):
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise FetchError("browser_package_missing: install requirements-browser.txt in the tool environment") from exc
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(headless=True, timeout=timeout * 1000,
                                        executable_path=os.environ.get("ROUTE_CHROMIUM_EXECUTABLE") or None)
        except Exception as exc:
            if "Executable doesn't exist" in str(exc):
                raise FetchError("browser_binary_missing: run python -m playwright install chromium") from exc
            raise FetchError("browser_launch_failed: run doctor --check-browser") from exc
        try:
            context = browser.new_context(accept_downloads=False, service_workers="block")
            page = context.new_page()
            page.set_default_timeout(timeout * 1000)
            response = page.goto(source["url"], wait_until="domcontentloaded", timeout=timeout * 1000)
            if response is None or response.status >= 400:
                raise FetchError("browser_http_error")
            from urllib.parse import urlsplit
            if urlsplit(page.url).netloc != urlsplit(source["url"]).netloc:
                raise FetchError("browser_cross_origin_redirect")
            return capture_page(page, source, timeout=timeout)
        except FetchError:
            raise
        except Exception as exc:
            raise FetchError("browser_navigation_or_layout_timeout") from exc
        finally:
            browser.close()


def check_installation():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise FetchError("browser_package_missing") from exc
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(headless=True, timeout=10000,
                                        executable_path=os.environ.get("ROUTE_CHROMIUM_EXECUTABLE") or None)
        except Exception as exc:
            code = "browser_binary_missing" if "Executable doesn't exist" in str(exc) else "browser_launch_failed"
            raise FetchError(code) from exc
        try:
            page = browser.new_page()
            page.set_content("<h1>Local browser check</h1>")
            return {"browser_launch_checked": True, "status": "ready"}
        finally:
            browser.close()
