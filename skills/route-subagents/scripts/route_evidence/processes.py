"""Bound network and browser work with a cancellable process group per source.

Threads only supervise local subprocesses. DNS, HTTP and Chromium execute in
those groups; cancelling a tool cannot leave an uninterruptible network thread.
"""
from __future__ import annotations

import os
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path

from .cache import FetchError
from .core import MAX_BYTES, EvidenceError, encoded, loads, number


class CancelledFetch(FetchError):
    """Caller cancellation, not a failure of the benchmark publisher."""


def stop_tree(process: subprocess.Popen, job=None) -> None:
    # On POSIX, a reaped parent can still have living group members holding
    # capture pipes open. Do not skip its owned group merely because it exited.
    try:
        if job is not None:
            job.terminate()
        elif os.name == "nt":
            if process.poll() is None:
                process.kill()  # Assignment failed; the gated target never ran.
        else:
            os.killpg(process.pid, signal.SIGKILL)
    except (ProcessLookupError, OSError, subprocess.TimeoutExpired):
        pass
    if process.poll() is None:
        process.kill()
    process.wait(timeout=3)


class ProcessScope:
    def __init__(self, seconds: float):
        number(seconds, "timeout_seconds", upper=300)
        if seconds <= 0:
            raise EvidenceError("timeout_seconds must be positive")
        self.deadline = time.monotonic() + seconds
        self.cancelled = threading.Event()
        self._lock = threading.Lock()
        self._processes: dict[subprocess.Popen, object] = {}

    def remaining(self) -> float:
        return max(0, self.deadline - time.monotonic())

    def cancel(self) -> None:
        self.cancelled.set()
        with self._lock:
            # Creation and registration are one critical section. A cancellation
            # cannot slip between Popen and registration and lose a worker.
            for process, job in tuple(self._processes.items()):
                stop_tree(process, job)

    def run(self, argv: list[str], payload: bytes = b"") -> bytes:
        with self._lock:
            if self.cancelled.is_set():
                raise CancelledFetch("refresh_cancelled")
            if self.remaining() <= 0:
                raise FetchError("refresh_deadline_exceeded")
            job = None
            options = {"start_new_session": True}
            if os.name == "nt":
                from .windows_job import Job
                job = Job()
                gate = Path(__file__).with_name("windows_gate.py")
                argv = [sys.executable, "-B", "-S", str(gate), *argv]
                payload = b"\x01" + payload
                options = {"creationflags": subprocess.CREATE_NO_WINDOW}
            process = None
            try:
                process = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                           stderr=subprocess.DEVNULL, **options)
                if job is not None:
                    job.assign(process.pid)
                self._processes[process] = job
            except BaseException:
                if process is not None:
                    stop_tree(process, job)
                    for stream in (process.stdin, process.stdout):
                        if stream:
                            stream.close()
                if job is not None:
                    job.close()
                raise
        try:
            stdout, _ = process.communicate(payload, timeout=max(.01, self.remaining()))
            if self.cancelled.is_set():
                raise CancelledFetch("refresh_cancelled")
            if process.returncode:
                raise FetchError("source_worker_failed")
            if len(stdout) > MAX_BYTES:
                raise FetchError("source_worker_response_too_large")
            return stdout
        except subprocess.TimeoutExpired as exc:
            stop_tree(process, job)
            try:
                process.communicate(timeout=1)
            except subprocess.TimeoutExpired:
                pass  # Never hang forever draining pipes held by an orphan.
            raise FetchError("refresh_deadline_exceeded") from exc
        except BaseException:
            stop_tree(process, job)
            raise
        finally:
            with self._lock:
                self._processes.pop(process, None)
                if job is not None:
                    job.close()
            for stream in (process.stdin, process.stdout):
                if stream:
                    stream.close()

    def fetch(self, source: dict, validators: dict, *, browser: bool):
        import sys
        worker = Path(__file__).with_name("worker.py")
        payload = encoded({"source_id": source["id"], "validators": validators,
                           "browser": browser, "timeout": min(15, self.remaining())})
        reply = loads(self.run([sys.executable, "-B", str(worker)], payload).decode("utf-8"))
        if not isinstance(reply, dict):
            raise FetchError("source_worker_invalid_response")
        if "error" in reply:
            code = reply["error"]
            if not isinstance(code, str) or len(code) > 300:
                code = "source_worker_invalid_error"
            retry_after = number(reply.get("retry_after", 0), "retry_after", upper=86400)
            raise FetchError(code, retry_after)
        if set(reply) != {"snapshot", "validators"} or not isinstance(reply["validators"], dict):
            raise FetchError("source_worker_invalid_response")
        return reply["snapshot"], reply["validators"]
