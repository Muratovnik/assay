"""Application/CLI/process lifecycle tests. No public network or model requests."""
from __future__ import annotations

import asyncio
import json
import io
from contextlib import redirect_stdout
import os
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from test_benchmark_router import SCRIPTS, any_source, data, guide_data, request, row
from route_evidence.cache import Cache, FetchError, source_lock
from route_evidence.core import EvidenceError, timestamp
from route_evidence.processes import ProcessScope
from route_evidence.providers import SOURCES
from route_evidence.service import RoutingService, ingest, load_config
import benchmark_router


class ServiceTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.now = 1800000000.0
        self.cache = Cache(self.root / "cache", clock=lambda: self.now)
        self.service = RoutingService(self.cache, client="codex", offline=True, clock=lambda: self.now)

    async def context(self, *task_types, **kwargs):
        return await self.service.get_routing_context(list(task_types) or ["terminal"], **kwargs)

    async def test_inventory_once_per_connection(self):
        result = await self.context("implementation")
        self.assertEqual(result["status"], "needs_inventory")
        result = await self.context("implementation", available=request()["available"])
        self.assertEqual(result["data_status"], "offline")
        self.assertEqual(result["task_types"], ["implementation"])
        result = await self.context("implementation")
        self.assertTrue(result["tasks"][0]["missing_primary"])
        self.assertEqual(self.service.status()["inventory"]["models"], 2)

    async def test_context_needs_no_declared_policy(self):
        service = RoutingService(self.cache, offline=True, clock=lambda: self.now)
        result = await service.get_routing_context(["terminal"], available=request()["available"])
        self.assertEqual(result["declared_constraints"], {})
        self.assertNotIn("quality_loss_pp", service.preferences)

    async def test_one_off_constraint_does_not_persist_to_the_next_call(self):
        await self.context("terminal", available=request()["available"], constraints={"quality_loss_pp": 2})
        self.assertNotIn("quality_loss_pp", self.service.preferences)
        self.assertEqual((await self.context("terminal"))["declared_constraints"], {})

    async def test_unknown_constraint_is_refused(self):
        with self.assertRaises(EvidenceError):
            await self.context("terminal", available=request()["available"], constraints={"objective": "cost_usd"})

    async def test_invalid_inventory_cannot_poison_session(self):
        await self.context("terminal", available=request()["available"])
        with self.assertRaises(EvidenceError):
            await self.context("terminal", available=[{"model": "bad", "efforts": []}])
        self.assertEqual((await self.context("terminal"))["data_status"], "offline")
        self.assertEqual(self.service.status()["inventory"]["models"], 2)

    async def test_expired_inventory_requires_reconfirmation(self):
        await self.context("terminal", available=request()["available"])
        self.now += 86400
        self.assertEqual((await self.context("terminal"))["status"], "needs_inventory")

    async def test_connections_do_not_share_inventory_or_limits(self):
        await self.context("terminal", available=request()["available"])
        other = RoutingService(self.cache, client="claude", preferences={"quality_loss_pp": 1}, offline=True)
        result = await other.get_routing_context(["terminal"])
        self.assertEqual(result["status"], "needs_inventory")
        self.assertEqual(other.preferences["quality_loss_pp"], 1)

    async def test_offline_and_fresh_cache_never_start_workers(self):
        with patch.object(ProcessScope, "fetch", side_effect=AssertionError("network requested")):
            await self.service.refresh(["deepswe"])
            self.cache.get(SOURCES["deepswe"], lambda *args: (data(), {}))
            self.service.offline = False
            values = await self.service.refresh(["deepswe"])
        self.assertEqual(values[0]["refresh"], "cached")

    async def test_refresh_has_one_deadline_for_all_sources(self):
        self.service.offline, self.service.timeout = False, .3
        def slow(scope, source, validators, *, browser):
            scope.run([sys.executable, "-c", "import time; time.sleep(30)"])
        start = time.monotonic()
        with patch.object(ProcessScope, "fetch", slow):
            values = await self.service.refresh(list(SOURCES))
        self.assertLess(time.monotonic() - start, 4)
        self.assertEqual(len(values), len(SOURCES))
        self.assertTrue(all(v["stale"] for v in values))
        for sid in SOURCES:
            with source_lock(self.cache.root / (sid + ".lock")) as acquired:
                self.assertTrue(acquired)

    async def test_cancellation_drains_workers_and_releases_source_locks(self):
        self.service.offline = False
        entered = threading.Event()
        scopes = []
        def slow(scope, source, validators, *, browser):
            scopes.append(scope)
            entered.set()
            scope.run([sys.executable, "-c", "import time; time.sleep(30)"])
        with patch.object(ProcessScope, "fetch", slow):
            task = asyncio.create_task(self.service.refresh(["deepswe"]))
            while not entered.is_set():
                await asyncio.sleep(.01)
            task.cancel()
            with self.assertRaises(asyncio.CancelledError):
                await asyncio.wait_for(task, 4)
        self.assertTrue(scopes[0].cancelled.is_set())
        self.assertFalse(scopes[0]._processes)
        with source_lock(self.cache.root / "deepswe.lock") as acquired:
            self.assertTrue(acquired)
        self.assertEqual(self.cache.read(SOURCES["deepswe"]).get("failures", 0), 0)

    async def test_quality_only_evidence_remains_useful_through_agent_interface(self):
        atlas_data = data("swe-atlas-qna", [row(cost=None)])
        self.cache.get(SOURCES["swe-atlas-qna"], lambda *args: (atlas_data, {}))
        result = await self.context("investigation", available=request()["available"])
        comparison = result["tasks"][0]["primary_comparisons"][0]
        self.assertEqual(comparison["candidates"][0]["expense_evidence"], "none")
        self.assertIn("unknown_primary_expense", result["tasks"][0]["evidence_gaps"])
        self.assertNotIn("recommended", result)

    def test_configuration_is_strict_and_dated(self):
        config = self.root / "config.json"
        for value in ({"schema_version": 1, "unexpected": True},
                      {"schema_version": 1, "preferences": {"price_guess": 2}},
                      {"schema_version": 1, "preferences": {"objective": "cost_usd"}},
                      {"schema_version": 1, "inventory": {"available": request()["available"]}}):
            config.write_text(json.dumps(value), encoding="utf-8")
            with self.assertRaises(EvidenceError):
                load_config(config)
        valid = {"schema_version": 1, "client": "codex", "preferences": {"quality_loss_pp": 3},
                 "inventory": {"available": request()["available"], "observed_at": timestamp(self.now)}}
        config.write_text(json.dumps(valid), encoding="utf-8")
        self.assertEqual(load_config(config), valid)

    def test_identical_import_preserves_data_change_date(self):
        before = ingest(self.cache, data(), timestamp(self.now))
        self.now += 60
        after = ingest(self.cache, data(), timestamp(self.now))
        self.assertEqual(before["data_changed_at"], after["data_changed_at"])
        self.assertNotEqual(before["last_success_at"], after["last_success_at"])

    def test_corrupt_source_identity_is_not_trusted(self):
        ingest(self.cache, data(), timestamp(self.now))
        path = self.cache.root / "deepswe.json"
        value = json.loads(path.read_text())
        value["snapshot"]["version"] = "unrelated"
        from route_evidence.core import digest
        value["data_hash"] = digest(value["snapshot"])
        path.write_text(json.dumps(value))
        self.assertIsNone(self.cache.read(SOURCES["deepswe"])["snapshot"])


class CLITests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.prefix = [sys.executable, "-B", str(SCRIPTS / "benchmark_router.py"), "--cache-dir", self.tmp.name]

    def cli(self, *args, input=None):
        return subprocess.run([*self.prefix, *args], input=input, capture_output=True, text=True, timeout=10)

    def test_request_from_stdin(self):
        p = self.cli("--offline", "context", "--request", "-", input=json.dumps(request()))
        self.assertEqual(p.returncode, 0, p.stderr)
        payload = json.loads(p.stdout)
        self.assertEqual(payload["data_status"], "offline")
        self.assertEqual(payload["task_types"], ["implementation"])

    def test_bad_stdin_is_structured_error(self):
        p = self.cli("--offline", "context", "--request", "-", input="{bad")
        self.assertEqual(p.returncode, 2)
        self.assertEqual(json.loads(p.stdout)["status"], "error")

    def test_smoke_refuses_offline_or_cached_mode_before_refresh(self):
        with redirect_stdout(io.StringIO()), patch.object(RoutingService, "refresh", side_effect=AssertionError("must not refresh")):
            self.assertEqual(benchmark_router.main(["--cache-dir", self.tmp.name, "smoke"]), 2)

    def test_config_and_client_cannot_disagree(self):
        config = Path(self.tmp.name) / "config.json"
        config.write_text(json.dumps({"schema_version": 1, "client": "codex"}))
        p = self.cli("--config", str(config), "--client", "claude", "status")
        self.assertEqual(p.returncode, 2)
        self.assertIn("conflicts", json.loads(p.stdout)["error"])

    def test_invalid_deadline_or_ttl_returns_error(self):
        for flag, value in (("--ttl-hours", "nan"), ("--timeout-seconds", "inf"), ("--timeout-seconds", "0")):
            p = self.cli(flag, value, "status")
            self.assertEqual(p.returncode, 2)
            self.assertEqual(json.loads(p.stdout)["status"], "error")


class ProcessTests(unittest.TestCase):
    def test_deadline_terminates_process(self):
        scope = ProcessScope(.2)
        start = time.monotonic()
        with self.assertRaisesRegex(FetchError, "deadline"):
            scope.run([sys.executable, "-c", "import time; time.sleep(30)"])
        self.assertLess(time.monotonic() - start, 4)
        self.assertFalse(scope._processes)

    def test_cancelled_scope_never_starts_new_process(self):
        scope = ProcessScope(3)
        scope.cancel()
        with patch("subprocess.Popen", side_effect=AssertionError("must not spawn")):
            with self.assertRaisesRegex(FetchError, "cancelled"):
                scope.run([sys.executable, "-c", "pass"])

    @unittest.skipIf(os.name == "nt" or not Path("/proc").exists(), "Linux process inspection")
    def test_descendants_inherit_and_die_with_owned_process_group(self):
        from concurrent.futures import ThreadPoolExecutor
        with tempfile.TemporaryDirectory() as tmp:
            pidfile = Path(tmp) / "pid"
            code = "import subprocess,sys,time; from pathlib import Path; p=subprocess.Popen([sys.executable,'-S','-c','import time; time.sleep(30)']); Path(sys.argv[1]).write_text(str(p.pid)); time.sleep(30)"
            scope = ProcessScope(20)
            with ThreadPoolExecutor(max_workers=1) as pool:
                future = pool.submit(scope.run, [sys.executable, "-S", "-c", code, str(pidfile)])
                until = time.monotonic() + 10
                try:
                    while not pidfile.exists() and time.monotonic() < until and not future.done():
                        time.sleep(.02)
                    self.assertTrue(pidfile.exists(), "child did not reach readiness")
                    pid = int(pidfile.read_text())
                finally:
                    scope.cancel()
                with self.assertRaises(FetchError):
                    future.result(timeout=4)
            # A reaped entry and a zombie both mean the group was killed. The
            # read can lose that race after the entry was seen, and Linux
            # answers that with ESRCH rather than with a missing file.
            try:
                state = Path(f"/proc/{pid}/stat").read_text().split()[2]
            except (FileNotFoundError, ProcessLookupError):
                state = None
            if state is not None:
                self.assertEqual(state, "Z", "descendant still executing after cancellation")

    @unittest.skipIf(os.name == "nt" or not Path("/proc").exists(), "Linux process inspection")
    def test_timeout_kills_group_after_worker_parent_exited(self):
        with tempfile.TemporaryDirectory() as tmp:
            pidfile = Path(tmp) / "pid"
            code = "import subprocess,sys; from pathlib import Path; p=subprocess.Popen([sys.executable,'-S','-c','import time; time.sleep(30)']); Path(sys.argv[1]).write_text(str(p.pid))"
            start = time.monotonic()
            with self.assertRaisesRegex(FetchError, "deadline"):
                ProcessScope(2).run([sys.executable, "-S", "-c", code, str(pidfile)])
            self.assertLess(time.monotonic() - start, 6)
            pid = int(pidfile.read_text())
            # The descendant sleeps far longer than this test runs, so it cannot
            # have exited on its own: a zombie and a reaped entry both mean the
            # group was killed. Reading can lose the race, and that is the same
            # answer rather than a failure: the open reports it as ENOENT and
            # the read, once the open has succeeded, as ESRCH.
            try:
                state = Path(f"/proc/{pid}/stat").read_text().split()[2]
            except (FileNotFoundError, ProcessLookupError):
                state = None
            if state is not None:
                self.assertEqual(state, "Z")


if __name__ == "__main__":
    unittest.main()
