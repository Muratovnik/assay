"""Real local Chromium/SDK integrations. CI requires dependencies; no model calls."""
from __future__ import annotations

import asyncio
import importlib.metadata
import json
import os
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

    def fixture(self, *, delay=500, mutate=True, version="FrontierCode 1.1"):
        value = "document.getElementById('score').textContent='10%'" if mutate else "void 0"
        self.page.set_content(f'''<h1>FrontierCode Leaderboard</h1><main>
        <button aria-pressed="true">{version}</button>
        <button role="tab" aria-selected="true">All reasoning levels</button>
        <button id="main" role="tab" aria-selected="true" aria-controls="results">Main</button>
        <button id="extended" role="tab" aria-selected="false" aria-controls="results">Extended</button>
        <div id="results"><table><tr><th>Model</th><th>Score</th><th>Cost</th></tr>
        <tr><td>Example low</td><td id="score">90%</td><td>$1</td></tr></table></div></main>
        <script>document.getElementById('extended').onclick=()=>{{
          document.getElementById('main').setAttribute('aria-selected','false');
          document.getElementById('extended').setAttribute('aria-selected','true');
          setTimeout(()=>{{{value}}},{delay}); }};</script>''')

    def test_delayed_tab_data_is_not_read_as_previous_subset(self):
        self.fixture()
        capture = capture_page(self.page, SOURCES["frontiercode"], timeout=3)
        result = captured_snapshot(SOURCES["frontiercode"], capture)
        self.assertEqual({r["subset"]: r["score"] for r in result["rows"]}, {"main": .9, "extended": .1})

    def test_active_tab_without_data_change_fails_closed(self):
        self.fixture(mutate=False)
        with self.assertRaises(EvidenceError):
            capture_page(self.page, SOURCES["frontiercode"], timeout=.7)

    def test_old_version_in_changelog_does_not_validate_current_table(self):
        self.page.set_content('''<h1>Terminal-Bench 5.0</h1><p>Terminal-Bench 4.0 retired</p>
        <table><tr><th>Model</th><th>Score</th></tr><tr><td>Example low</td><td>90%</td></tr></table>''')
        with self.assertRaises(EvidenceError):
            capture_page(self.page, SOURCES["terminal-bench"], timeout=1)

    def test_missing_selected_version_is_not_guessed(self):
        self.fixture(version="FrontierCode 1.0")
        with self.assertRaises(EvidenceError):
            capture_page(self.page, SOURCES["frontiercode"], timeout=1)

    def test_live_frontier_controls_preserve_effort_harness_and_rollout_expense(self):
        self.fixture()
        self.page.evaluate("""() => {
          document.getElementById('main').innerHTML='Main<span>100</span>';
          document.getElementById('extended').innerHTML='Extended<span>150</span>';
          document.querySelector('table').innerHTML=
            '<tr><th>Model</th><th>Score<span>▼</span></th><th>Cost / rollout<span>▼</span></th><th>Output tokens<span>▼</span></th></tr>'+
            '<tr><td title="Harness: codex">Example<span>max</span></td><td id="score">90%</td><td>$4.59</td><td>30.1k</td></tr>';
        }""")
        result = captured_snapshot(SOURCES["frontiercode"], capture_page(self.page, SOURCES["frontiercode"], timeout=3))
        row = result["rows"][0]
        self.assertEqual((row["model"], row["effort"], row["harness"]), ("Example", "max", "codex"))
        self.assertEqual((row["cost_usd"], row["output_tokens"]), (4.59, 30100))
        self.assertIn("rollout", row["cost_basis"])

    def test_terminal_selected_benchmark_and_aggregate_units(self):
        self.page.set_content("""<h1>TERMINAL-BENCH <span>9 8 7 6 5 4 3 2 1 0 . 9 8 7 6 5 4 3 2 1 0</span></h1>
        <button role="combobox" aria-label="Benchmark">4.0</button>
        <table><tr><th>MODEL</th><th>AGENT</th><th>RESOLUTION RATE</th><th>TOKENS</th><th>COST</th></tr>
        <tr><td>Example (max)</td><td>Codex</td><td>58.2% ± 2.8%</td><td>1.5B</td><td>$3.3k</td></tr></table>""")
        result = captured_snapshot(SOURCES["terminal-bench"], capture_page(self.page, SOURCES["terminal-bench"], timeout=1))
        row = result["rows"][0]
        self.assertEqual((row["model"], row["effort"], row["harness"]), ("Example", "max", "Codex"))
        self.assertEqual((row["cost_usd"], row["reported_tokens"]), (3300, 1500000000))
        self.assertNotIn("per task", row["cost_basis"])
        self.page.get_by_role("combobox", name="Benchmark").evaluate("(e)=>e.textContent='5.0'")
        with self.assertRaises(EvidenceError):
            capture_page(self.page, SOURCES["terminal-bench"], timeout=1)

    def test_late_reasoning_control_is_selected_before_capturing(self):
        self.fixture()
        self.page.evaluate("""() => {
          const mode = [...document.querySelectorAll('button')].find(e=>e.textContent==='All reasoning levels');
          mode.remove();
          setTimeout(() => {
            mode.setAttribute('aria-selected','false');
            mode.onclick = () => {
              mode.setAttribute('aria-selected','true');
              setTimeout(()=>document.querySelector('table').insertAdjacentHTML('beforeend',
                '<tr><td>Example high</td><td>91%</td><td>$2</td></tr>'), 300);
            };
            document.querySelector('main').append(mode);
          }, 200);
        }""")
        result = captured_snapshot(SOURCES["frontiercode"], capture_page(self.page, SOURCES["frontiercode"], timeout=3))
        self.assertEqual(len(result["rows"]), 4)
        self.assertEqual({r["effort"] for r in result["rows"]}, {"low", "high"})

    def test_aria_panel_excludes_unrelated_visible_table(self):
        self.fixture()
        self.page.evaluate("""() => document.body.insertAdjacentHTML('beforeend',
          '<table><tr><th>Model</th><th>Score</th></tr><tr><td>Other low</td><td>1%</td></tr></table>')""")
        result = captured_snapshot(SOURCES["frontiercode"], capture_page(self.page, SOURCES["frontiercode"], timeout=3))
        self.assertEqual(len(result["rows"]), 2)
        self.assertTrue(all(r["model"] == "Example" for r in result["rows"]))

    def test_multiple_leaderboards_without_binding_are_rejected(self):
        self.page.set_content('''<h1>Terminal-Bench 4.0</h1>
        <table><tr><th>Model</th><th>Score</th></tr><tr><td>A low</td><td>90%</td></tr></table>
        <table><tr><th>Model</th><th>Score</th></tr><tr><td>B low</td><td>10%</td></tr></table>''')
        with self.assertRaises(EvidenceError):
            capture_page(self.page, SOURCES["terminal-bench"], timeout=.5)


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
    code = "import os,sys,time; from pathlib import Path; Path(sys.argv[1]).write_text(str(os.getpid())); time.sleep(20)"
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
                    until = time.monotonic() + 10
                    while not (root / "worker.pid").exists() and time.monotonic() < until:
                        await asyncio.sleep(.02)
                    self.assertTrue((root / "worker.pid").exists())
                    pid = int((root / "worker.pid").read_text())
                    call.cancel()
                    with self.assertRaises(asyncio.CancelledError):
                        await call
                    until = time.monotonic() + 3
                    while is_running(pid) and time.monotonic() < until:
                        await asyncio.sleep(.02)
                    self.assertFalse(is_running(pid))
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
                        self.assertFalse(envelope.get("failures", 0))

    async def test_stdio_tools_session_inventory_and_validation(self):
        from mcp import Client, StdioServerParameters
        with tempfile.TemporaryDirectory() as tmp:
            config = Path(tmp) / "routing.json"
            config.write_text(json.dumps({"schema_version": 1, "client": "codex", "preferences": {}}), encoding="utf-8")
            params = StdioServerParameters(command=sys.executable, args=["-B", str(SCRIPTS / "benchmark_mcp.py"),
                "--cache-dir", str(Path(tmp) / "cache"), "--offline", "--config", str(config)])
            async with asyncio.timeout(30):
                async with Client(params) as client:
                    tools = await client.list_tools()
                    self.assertEqual({t.name for t in tools.tools}, {"get_routing_context", "routing_status",
                        "prepare_routing", "complete_routing", "record_routing_outcome"})
                    status = await client.call_tool("routing_status", {})
                    self.assertFalse(status.is_error)
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
                    diagnostic = await client.call_tool("prepare_routing", {"packets": [
                        {"packet_id": "local-check", "task_types": ["implementation"], "features": {}}]})
                    self.assertFalse(diagnostic.is_error)
                    self.assertEqual(diagnostic.structured_content["usage"], "diagnostic_only")
                    self.assertNotIn("handoff", diagnostic.structured_content)
                    unknown = await client.call_tool("complete_routing", {"decision_id": "absent", "advisor_result": {}})
                    self.assertEqual(unknown.structured_content["status"], "expired")
                    receipt = await client.call_tool("record_routing_outcome", {"decision_id": "absent", "execution": {}})
                    self.assertFalse(receipt.structured_content["recorded"])

    async def test_native_advisor_protocol_roundtrip_without_inference(self):
        from mcp import Client, StdioServerParameters
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bootstrap = root / "advisor_server.py"
            bootstrap.write_text('''import sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
from route_evidence.cache import Cache
from route_evidence.routing import build_context
from route_evidence.service import RoutingService
from benchmark_mcp import build_server
service = RoutingService(Cache(Path(sys.argv[2]) / "cache"), client="codex",
    advisor_config={"schema_version": 2, "telemetry": {"mode": "metadata"}})
async def context(request):
    return {**build_context(request, []), "sources": [], "data_status": "unavailable", "usage": "routing"}
service.context = context
build_server(service).run(transport="stdio")
''', encoding="utf-8")
            params = StdioServerParameters(command=sys.executable,
                args=["-B", str(bootstrap), str(SCRIPTS), str(root)])
            async with asyncio.timeout(30):
                async with Client(params) as client:
                    prepared = await client.call_tool("prepare_routing", {
                        "packets": [{"packet_id": "local-check", "task_types": ["implementation"], "features": {}}],
                        "available": request()["available"],
                        "advisor_route": {"model": "economy-b", "effort": "max", "selection_basis": {
                            "source": "caller", "reason_code": "bounded_ranking"}}})
                    self.assertFalse(prepared.is_error)
                    value = prepared.structured_content
                    self.assertEqual(value["status"], "awaiting_native_advice")
                    # A deterministic fixture fulfills the wire contract. No
                    # native model is started and no model quality is measured.
                    answer = value["handoff"]["result_contract"]
                    arguments = {"decision_id": value["decision_id"], "advisor_result": answer}
                    completed = await client.call_tool("complete_routing", arguments)
                    self.assertFalse(completed.is_error)
                    self.assertEqual(completed.structured_content["status"], "decided")
                    self.assertNotEqual(completed.structured_content.get("telemetry_status"), "write_failed")
                    repeated = await client.call_tool("complete_routing", arguments)
                    self.assertEqual(completed.structured_content, repeated.structured_content)
                    recorded = await client.call_tool("record_routing_outcome", {
                        "decision_id": value["decision_id"], "execution": {"status": "unknown"}})
                    self.assertFalse(recorded.is_error)
                    self.assertEqual(recorded.structured_content["execution"]["observed"], {})


if __name__ == "__main__":
    unittest.main()
