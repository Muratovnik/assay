"""Private worker protocol. Runs only registered public-source adapters."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from route_evidence.core import MAX_BYTES, EvidenceError, encoded, loads
from route_evidence.guides import GUIDES
from route_evidence.providers import Fetcher, SOURCES

REGISTRY = {**SOURCES, **GUIDES}


def main():
    try:
        command = loads(sys.stdin.buffer.read(MAX_BYTES + 1).decode("utf-8"))
        if command == {"diagnose_browser": True}:
            from route_evidence.browser import check_installation
            sys.stdout.buffer.write(encoded(check_installation()))
            return 0
        if not isinstance(command, dict) or set(command) != {"source_id", "validators", "browser", "timeout"}:
            raise EvidenceError("invalid_worker_request")
        sid = command["source_id"]
        if not isinstance(sid, str) or sid not in REGISTRY:
            raise EvidenceError("unknown_source")
        if not isinstance(command["validators"], dict) or type(command["browser"]) is not bool:
            raise EvidenceError("invalid_worker_request")
        snapshot, validators = Fetcher(browser=command["browser"], timeout=command["timeout"])(
            REGISTRY[sid], command["validators"])
        reply = encoded({"snapshot": snapshot, "validators": validators})
        if len(reply) > MAX_BYTES:
            raise EvidenceError("source_worker_response_too_large")
    except (EvidenceError, OSError, UnicodeError) as exc:
        reply = encoded({"error": str(exc)[:300], "retry_after": getattr(exc, "retry_after", 0)})
    except Exception:
        # Do not leak fetched HTML, local paths, headers or traceback to the host.
        reply = encoded({"error": "source_worker_internal_error", "retry_after": 0})
    sys.stdout.buffer.write(reply)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
