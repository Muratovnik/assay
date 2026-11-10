"""Real local Chromium/SDK integrations. CI requires dependencies; no model calls."""
from __future__ import annotations

import asyncio
import importlib.metadata
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

from test_benchmark_router import SCRIPTS, request
from route_evidence.core import EvidenceError
from route_evidence.providers import SOURCES, captured_snapshot
from route_evidence.browser import capture_page

REQUIRED = os.environ.get("REQUIRE_ROUTING_INTEGRATIONS") == "1"


def missing_dependency(message):
    if REQUIRED:
        raise AssertionError(message)
    raise unittest.SkipTest(message)


class BrowserIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            missing_dependency("Install requirements-browser.txt and Chromium")
        cls.pw = sync_playwright().start()
        try:
            cls.browser = cls.pw.chromium.launch(headless=True,
                executable_path=os.environ.get("ROUTE_CHROMIUM_EXECUTABLE") or None)
        except Exception as exc:
            cls.pw.stop()
            missing_dependency("Cannot launch Chromium: " + type(exc).__name__)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.pw.stop()

    def setUp(self):
        self.page = self.browser.new_page()
        self.addCleanup(self.page.close)

    # Synthetic FrontierCode 2.0 layout: a chart block with the model filter, then
    # the leaderboard block whose own heading names the suite, its two view tabs
    # and one table. The effort sits in its own element after the model name.
    FRONTIER_HEAD = ('<tr><th>#</th><th>Model</th><th>Harness</th><th><button>Score<span aria-hidden="true">'
                     '▼</span></button></th><th>Pass rate</th><th>Flag rate</th><th>Cost / rollout</th>'
                     '<th>Output tokens</th></tr>')
    FRONTIER_BEST = ('<tr><td>1</td><td><span aria-hidden="true"></span>Example 5.2<span>xhigh</span></td>'
                     '<td>Example Harness</td><td><span><span aria-hidden="true"></span><span>49.1%</span></span></td>'
                     '<td>53.5%</td><td>1.5%</td><td>$17.73</td><td>156.0k</td></tr>'
                     '<tr><td>2</td><td>Other 1.7<span>na</span></td><td>Other Harness</td><td>16.2%</td>'
                     '<td>18.9%</td><td>0.8%</td><td>$3.52</td><td>89.3k</td></tr>')
    FRONTIER_ALL = FRONTIER_BEST + (
        '<tr><td>1</td><td>Example 5.2high</td><td>Example Harness</td><td>45.3%</td><td>49.4%</td>'
        '<td>2.0%</td><td>$8.40</td><td>76.0k</td></tr>'
        '<tr><td>1</td><td>Example 5.2</td><td>Example Harness</td><td>17.4%</td><td>19.4%</td>'
        '<td>0.0%</td><td>$0.44</td><td>62.6k</td></tr>')

    def frontier(self, *, delay=300, change=True, version="FrontierCode 2.0", models="1/2 models", tabs=True):
        controls = ('<div role="tablist"><button id="best" role="tab" aria-selected="true">Best reasoning mode</button>'
                    '<button id="every" role="tab" aria-selected="false">All reasoning levels</button></div>'
                    if tabs else "")
        update = ("document.getElementById('rows').innerHTML=" + json.dumps(self.FRONTIER_HEAD + self.FRONTIER_ALL)
                  if change else "void 0")
        self.page.set_content(f'''<h1>FrontierCode Leaderboard</h1><main>
        <div><h4>FrontierCode 2.0<span>chart</span></h4>
          <button aria-expanded="true"><span>Models</span><span>{models}<span aria-hidden="true">▲</span></span></button></div>
        <div id="board"><div><h4>{version}<span>Leaderboard</span></h4>{controls}</div>
          <table><tbody id="rows">{self.FRONTIER_HEAD}{self.FRONTIER_BEST}</tbody></table></div>
        <section><span>Changelog</span><a href="#">FrontierCode 2.0</a></section></main>
        <script>{{ const every = document.getElementById('every');
          if (every) every.onclick = () => {{
            document.getElementById('best').setAttribute('aria-selected', 'false');
            every.setAttribute('aria-selected', 'true');
            setTimeout(() => {{ {update}; }}, {delay}); }}; }}</script>''')

    def frontier_snapshot(self, timeout=3):
        return captured_snapshot(SOURCES["frontiercode"], capture_page(self.page, SOURCES["frontiercode"], timeout=timeout))

    def test_frontier_captures_all_reasoning_levels_for_every_published_model(self):
        self.frontier()
        result = self.frontier_snapshot()
        rows = {(r["model"], r["effort"]): r for r in result["rows"]}
        self.assertEqual(result["version"], "2.0")
        self.assertEqual(set(rows), {("Example 5.2", "xhigh"), ("Example 5.2", "high"),
                                     ("Example 5.2", None), ("Other 1.7", None)})
        top = rows[("Example 5.2", "xhigh")]
        self.assertEqual((top["harness"], top["subset"], top["score"]), ("Example Harness", "all", .491))
        self.assertEqual(top["published_rates"], {"pass_rate": .535, "flag_rate": .015})
        self.assertEqual((top["cost_usd"], top["output_tokens"]), (17.73, 156000))
        self.assertEqual(rows[("Other 1.7", None)]["harness"], "Other Harness")

    def test_frontier_unchanged_table_after_switch_is_not_relabelled(self):
        self.frontier(change=False)
        with self.assertRaises(EvidenceError):
            capture_page(self.page, SOURCES["frontiercode"], timeout=1)

    def test_frontier_old_version_in_the_board_heading_is_refused(self):
        # The changelog and the chart still say 2.0; only the board's own heading counts.
        self.frontier(version="FrontierCode 1.1")
        with self.assertRaises(EvidenceError):
            self.frontier_snapshot(timeout=1)

    def test_frontier_missing_view_control_is_refused(self):
        self.frontier(tabs=False)
        with self.assertRaisesRegex(EvidenceError, "dataset control not found"):
            capture_page(self.page, SOURCES["frontiercode"], timeout=.5)

    def test_frontier_model_count_must_be_published_and_complete(self):
        self.frontier(models="")
        with self.assertRaisesRegex(EvidenceError, "published model count not found"):
            capture_page(self.page, SOURCES["frontiercode"], timeout=1)
        self.frontier(models="1/3 models")
        with self.assertRaisesRegex(EvidenceError, "incomplete_models"):
            self.frontier_snapshot()

    def test_old_version_in_changelog_does_not_validate_current_table(self):
        self.page.set_content('''<h1>Terminal-Bench 5.0</h1><p>Terminal-Bench 4.0 retired</p>
        <table><tr><th>Model</th><th>Score</th></tr><tr><td>Example low</td><td>90%</td></tr></table>''')
        with self.assertRaises(EvidenceError):
            capture_page(self.page, SOURCES["terminal-bench"], timeout=1)

    def test_terminal_selected_benchmark_and_aggregate_units(self):
        self.page.set_content("""<h1>TERMINAL-BENCH <span>9 8 7 6 5 4 3 2 1 0 . 9 8 7 6 5 4 3 2 1 0</span></h1>
        <button role="combobox" aria-label="Benchmark">4.0</button>
        <table><tr><th>MODEL</th><th>AGENT</th><th>RESOLUTION RATE</th><th>TOKENS</th><th>COST</th></tr>
        <tr><td>Example (max)</td><td>Codex</td><td>58.2% ± 2.8%</td><td>1.5B</td><td>$3.3k</td></tr></table>""")
        result = captured_snapshot(SOURCES["terminal-bench"], capture_page(self.page, SOURCES["terminal-bench"], timeout=1))
        row = result["rows"][0]
        self.assertEqual((row["model"], row["effort"], row["harness"]), ("Example", "max", "Codex"))
        self.assertIsNone(row["cost_usd"])
        self.assertIsNone(row["reported_tokens"])
        self.assertEqual(row["aggregate_usage"], {"total_cost_usd": 3300, "total_tokens": 1500000000})
        self.assertAlmostEqual(row["score_low"], .554)
        self.assertAlmostEqual(row["score_high"], .61)
        self.page.get_by_role("combobox", name="Benchmark").evaluate("(e)=>e.textContent='5.0'")
        with self.assertRaises(EvidenceError):
            capture_page(self.page, SOURCES["terminal-bench"], timeout=1)

    def test_late_reasoning_control_is_selected_before_capturing(self):
        self.frontier()
        self.page.evaluate("""() => {
          const mode = document.getElementById('every');
          const list = mode.parentElement;
          mode.remove();
          setTimeout(() => list.append(mode), 200);
        }""")
        result = self.frontier_snapshot()
        self.assertEqual(len(result["rows"]), 4)
        self.assertEqual({r["effort"] for r in result["rows"]}, {"xhigh", "high", None})

    def test_board_binding_excludes_unrelated_visible_table(self):
        self.frontier()
        self.page.evaluate("""() => document.querySelector('main').insertAdjacentHTML('beforeend',
          '<table><tr><th>Model</th><th>Score</th></tr><tr><td>Unrelated low</td><td>1%</td></tr></table>')""")
        result = self.frontier_snapshot()
        self.assertEqual({r["model"] for r in result["rows"]}, {"Example 5.2", "Other 1.7"})

    def test_multiple_leaderboards_without_binding_are_rejected(self):
        self.page.set_content('''<h1>Terminal-Bench 4.0</h1>
        <table><tr><th>Model</th><th>Score</th></tr><tr><td>A low</td><td>90%</td></tr></table>
        <table><tr><th>Model</th><th>Score</th></tr><tr><td>B low</td><td>10%</td></tr></table>''')
        with self.assertRaises(EvidenceError):
            capture_page(self.page, SOURCES["terminal-bench"], timeout=.5)


class OptionalSDKTests(unittest.TestCase):
    def test_cli_help_and_missing_sdk_diagnostic_without_site_packages(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = Path(tmp) / "routing.json"
            config.write_text(json.dumps({"schema_version": 5, "client": "codex", "preferences": {}}), encoding="utf-8")
            for arguments, code in ((["--help"], 0),
                                    (["--offline", "--cache-dir", str(Path(tmp) / "cache"),
                                      "--config", str(config)], 2)):
                with self.subTest(arguments=arguments):
                    result = subprocess.run([sys.executable, "-S", "-B", str(SCRIPTS / "benchmark_mcp.py"),
                                             *arguments], capture_output=True, text=True, timeout=10)
                    self.assertEqual(result.returncode, code, result.stderr)
                    self.assertNotIn("Traceback", result.stderr)
                    if code == 2:
                        self.assertIn("MCP SDK unavailable", result.stderr)


class MCPIntegrationTests(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        try:
            version = importlib.metadata.version("mcp")
        except importlib.metadata.PackageNotFoundError:
            missing_dependency("Install requirements-mcp.txt to test real stdio MCP")
        if version != "2.2.0":
            missing_dependency("MCP integration requires the pinned SDK 2.2.0")

    async def test_stdio_cancellation_stops_owned_fetch_and_releases_lock(self):
        from mcp import Client, StdioServerParameters
        from route_evidence.cache import source_lock
        from test_benchmark_adoption import is_running
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            # Only acquisition is replaced. Real SDK transport, service,
            # ProcessScope and OS locks remain in the cancellation path.
            bootstrap = root / "server.py"
            bootstrap.write_text("""
import sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
from route_evidence.processes import ProcessScope
from route_evidence.service import RoutingService
from route_evidence.cache import Cache
from benchmark_mcp import build_server
root = Path(sys.argv[2])
def slow(self, source, validators, *, browser):
    code = ("import os,sys,time; from pathlib import Path; "
            "marker=Path(sys.argv[1]).with_name('worker.'+str(os.getpid())+'.pid'); "
            "ready=marker.with_suffix('.ready'); ready.write_text(str(os.getpid()), encoding='ascii'); "
            "ready.replace(marker); time.sleep(20)")
    self.run([sys.executable, "-B", "-S", "-c", code, str(root / "worker.pid")])
ProcessScope.fetch = slow
service = RoutingService(Cache(root / "cache"), timeout=25)
build_server(service).run(transport="stdio")
""", encoding="utf-8")
            params = StdioServerParameters(command=sys.executable,
                args=["-B", str(bootstrap), str(SCRIPTS), str(root)])
            async with asyncio.timeout(30):
                async with Client(params) as client:
                    await client.list_tools()
                    call = asyncio.create_task(client.call_tool("get_routing_context", {
                        "task_types": ["terminal"], "available": request()["available"]}))
                    def worker_pids():
                        return [int(path.read_text(encoding="ascii")) for path in root.glob("worker.*.pid")]
                    until = time.monotonic() + 10
                    while not worker_pids() and time.monotonic() < until:
                        await asyncio.sleep(.02)
                    self.assertTrue(worker_pids())
                    call.cancel()
                    with self.assertRaises(asyncio.CancelledError):
                        await call
                    until = time.monotonic() + 3
                    while any(is_running(pid) for pid in worker_pids()) and time.monotonic() < until:
                        await asyncio.sleep(.02)
                    self.assertFalse(any(is_running(pid) for pid in worker_pids()))
                    acquired = False
                    while time.monotonic() < until:
                        with source_lock(root / "cache" / "terminal-bench.lock") as acquired:
                            if acquired:
                                break
                        await asyncio.sleep(.02)
                    self.assertTrue(acquired, "cancelled request did not release its source lock within 3s")
                    status = await client.call_tool("routing_status", {})
                    self.assertFalse(status.is_error)
                    for path in (root / "cache").glob("*.json"):
                        envelope = json.loads(path.read_text())
                        self.assertIsNone(envelope.get("snapshot"))
                        self.assertFalse(envelope.get("failures", 0), envelope)

    async def test_stdio_tools_session_inventory_and_validation(self):
        from mcp import Client, StdioServerParameters
        with tempfile.TemporaryDirectory() as tmp:
            config = Path(tmp) / "routing.json"
            config.write_text(json.dumps({"schema_version": 5, "client": "codex", "preferences": {}}), encoding="utf-8")
            params = StdioServerParameters(command=sys.executable, args=["-B", str(SCRIPTS / "benchmark_mcp.py"),
                "--cache-dir", str(Path(tmp) / "cache"), "--offline", "--config", str(config)])
            async with asyncio.timeout(30):
                async with Client(params) as client:
                    tools = await client.list_tools()
                    self.assertEqual({t.name for t in tools.tools}, {"get_routing_context", "routing_status"})
                    status = await client.call_tool("routing_status", {})
                    self.assertFalse(status.is_error)
                    self.assertEqual(status.structured_content["pipeline"]["mode"], "evidence-only")
                    self.assertFalse(status.structured_content["inventory"]["configured"])
                    self.assertEqual(status.structured_content["refresh_mode"], "offline")
                    initial = await client.call_tool("get_routing_context", {"task_types": ["implementation"]})
                    self.assertEqual(initial.structured_content["status"], "needs_inventory")
                    self.assertEqual(initial.structured_content["data_status"], "not_checked")
                    supplied = await client.call_tool("get_routing_context",
                                                      {"task_types": ["implementation"], "available": request()["available"]})
                    self.assertEqual(supplied.structured_content["task_types"], ["implementation"])
                    self.assertEqual(supplied.structured_content["tasks"][0]["primary_comparisons"], [])
                    self.assertEqual(supplied.structured_content["declared_constraints"], {})
                    self.assertEqual(supplied.structured_content["data_status"], "offline")
                    self.assertEqual(supplied.structured_content["usage"], "diagnostic_only")
                    self.assertIn("disabled", supplied.structured_content["data_message"])
                    self.assertTrue(all(s["availability"] == "missing" for s in supplied.structured_content["sources"]))
                    reused = await client.call_tool("get_routing_context", {"task_types": ["implementation"]})
                    self.assertEqual(reused.structured_content["data_status"], "offline")
                    invalid = await client.call_tool("get_routing_context", {"task_types": ["implementation"], "available": []})
                    self.assertTrue(invalid.is_error)
                    after = await client.call_tool("routing_status", {})
                    self.assertEqual(after.structured_content["inventory"]["models"], 2)


if __name__ == "__main__":
    unittest.main()
