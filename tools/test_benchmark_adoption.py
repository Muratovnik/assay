"""Acceptance regressions from PR4's recorded live and Windows failures."""
from __future__ import annotations

import ctypes
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch

from test_benchmark_router import SCRIPTS, request
from route_evidence.core import EvidenceError
from route_evidence.processes import ProcessScope
from route_evidence.providers import SOURCES, table_snapshot

FIXTURE = Path(__file__).parent / "fixtures" / "cursorbench-responsive.html"


class CursorAcquisitionTests(unittest.TestCase):
    def test_responsive_publisher_headers_preserve_expense(self):
        snapshot = table_snapshot(SOURCES["cursorbench"], FIXTURE.read_text(encoding="utf-8"))
        observed = snapshot["rows"][0]
        self.assertEqual((observed["cost_usd"], observed["reported_tokens"], observed["steps"]),
                         (17.28, 117236, 128))
        self.assertIsNone(observed["total_tokens"])
        self.assertIsNone(observed["output_tokens"])

    def test_missing_expected_column_is_schema_failure(self):
        body = FIXTURE.read_text(encoding="utf-8")
        for label in ("Cost", "Tokens", "Steps"):
            with self.subTest(label=label), self.assertRaisesRegex(EvidenceError, "columns"):
                table_snapshot(SOURCES["cursorbench"], body.replace(label, "Changed"))

    def test_published_unknown_expense_remains_null(self):
        body = FIXTURE.read_text(encoding="utf-8").replace("$17.28", "—")
        observed = table_snapshot(SOURCES["cursorbench"], body)["rows"][0]
        self.assertIsNone(observed["cost_usd"])
        self.assertEqual(observed["steps"], 128)


class CLIRequestTests(unittest.TestCase):
    def test_external_request_cannot_supply_an_internal_result(self):
        with tempfile.TemporaryDirectory() as temp:
            prefix = [sys.executable, "-B", str(SCRIPTS / "benchmark_router.py"),
                      "--cache-dir", temp, "--offline", "context", "--request"]
            for value in ({"schema_version": 2, "tasks": [], "inventory": []},
                          {**request(), "data_status": "ready"}, None, 17, "status", []):
                for source in ("stdin", "file"):
                    with self.subTest(value=value, source=source):
                        text = json.dumps(value)
                        path = Path(temp) / "request.json"
                        path.write_text(text, encoding="utf-8")
                        result = subprocess.run([*prefix, "-" if source == "stdin" else str(path)],
                                                input=text if source == "stdin" else None,
                                                capture_output=True, text=True, timeout=10)
                        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                        self.assertEqual(json.loads(result.stdout)["status"], "error")
                        self.assertNotIn("Traceback", result.stderr)
            valid = subprocess.run([*prefix, "-"], input=json.dumps(request()),
                                   capture_output=True, text=True, timeout=10)
            self.assertEqual(valid.returncode, 0, valid.stderr)
            self.assertEqual(json.loads(valid.stdout)["data_status"], "offline")


def is_running(pid):
    if os.name != "nt":
        stat = Path(f"/proc/{pid}/stat")
        try:
            return stat.read_text().split()[2] != "Z"
        except FileNotFoundError:
            # Reaped between the lookup and the read: the entry can vanish
            # mid-call, so its absence is an answer rather than an error.
            pass
        try:
            os.kill(pid, 0)
            return True
        except ProcessLookupError:
            return False
    from ctypes import wintypes
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    handle = kernel.OpenProcess(0x1000, False, pid)
    if not handle:
        if ctypes.get_last_error() == 87:
            return False
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        status = wintypes.DWORD()
        if not kernel.GetExitCodeProcess(handle, ctypes.byref(status)):
            raise ctypes.WinError(ctypes.get_last_error())
        return status.value == 259
    finally:
        kernel.CloseHandle(handle)


class ProcessOwnershipTests(unittest.TestCase):
    @unittest.skipUnless(os.name == "nt", "Windows job assignment contract")
    def test_failed_assignment_never_starts_target(self):
        with tempfile.TemporaryDirectory() as temp:
            marker = Path(temp) / "started"
            code = "import sys; from pathlib import Path; Path(sys.argv[1]).touch()"
            with patch("route_evidence.windows_job.Job.assign", side_effect=OSError("assignment denied")):
                with self.assertRaisesRegex(OSError, "assignment denied"):
                    ProcessScope(3).run([sys.executable, "-c", code, str(marker)])
            self.assertFalse(marker.exists())

    @unittest.skipUnless(os.name == "nt", "Windows kill-on-close contract")
    def test_success_closes_job_and_reaps_detached_output_descendant(self):
        code = ("import subprocess,sys; "
                "p=subprocess.Popen([sys.executable,'-B','-S','-c','import time; time.sleep(8)'], "
                "stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); "
                "print(p.pid)")
        pid = int(ProcessScope(3).run([sys.executable, "-B", "-S", "-c", code]))
        until = time.monotonic() + 2
        while is_running(pid) and time.monotonic() < until:
            time.sleep(.01)
        self.assertFalse(is_running(pid))

    def test_deadline_owns_descendant_after_direct_parent_exit(self):
        with tempfile.TemporaryDirectory() as temp:
            pidfile = Path(temp) / "descendant.pid"
            code = ("import subprocess,sys; from pathlib import Path; "
                    "p=subprocess.Popen([sys.executable,'-B','-S','-c','import time; time.sleep(8)']); "
                    "Path(sys.argv[1]).write_text(str(p.pid))")
            started = time.monotonic()
            with self.assertRaisesRegex(EvidenceError, "deadline"):
                ProcessScope(.7).run([sys.executable, "-B", "-S", "-c", code, str(pidfile)])
            elapsed = time.monotonic() - started
            self.assertTrue(pidfile.exists(), "worker did not reach readiness")
            self.assertLess(elapsed, 3)
            self.assertFalse(is_running(int(pidfile.read_text())), "owned descendant still running")

    def test_cancel_after_parent_exit_preserves_unrelated_process(self):
        with tempfile.TemporaryDirectory() as temp:
            pidfile = Path(temp) / "descendant.pid"
            code = ("import subprocess,sys; from pathlib import Path; "
                    "p=subprocess.Popen([sys.executable,'-B','-S','-c','import time; time.sleep(8)']); "
                    "Path(sys.argv[1]).write_text(str(p.pid))")
            unrelated = subprocess.Popen([sys.executable, "-B", "-S", "-c", "import time; time.sleep(20)"],
                                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            scope = ProcessScope(15)
            try:
                with ThreadPoolExecutor(max_workers=1) as pool:
                    future = pool.submit(scope.run, [sys.executable, "-B", "-S", "-c", code, str(pidfile)])
                    until = time.monotonic() + 5
                    while not pidfile.exists() and time.monotonic() < until:
                        time.sleep(.01)
                    self.assertTrue(pidfile.exists())
                    time.sleep(.15)  # Allow the short-lived direct child to exit.
                    started = time.monotonic()
                    scope.cancel()
                    with self.assertRaises(EvidenceError):
                        future.result(timeout=3)
                    self.assertLess(time.monotonic() - started, 3)
                    self.assertFalse(is_running(int(pidfile.read_text())))
                self.assertIsNone(unrelated.poll())
            finally:
                scope.cancel()
                unrelated.terminate()
                unrelated.wait(timeout=3)

    def test_process_protocol_preserves_binary_stdin_and_stdout(self):
        payload = b"\x00\r\n\x1a\xffpayload"
        code = "import sys; sys.stdout.buffer.write(sys.stdin.buffer.read())"
        scope = ProcessScope(5)
        try:
            self.assertEqual(scope.run([sys.executable, "-B", "-c", code], payload), payload)
        finally:
            scope.cancel()
