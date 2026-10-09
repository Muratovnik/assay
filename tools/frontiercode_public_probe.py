"""One public FrontierCode acquisition; print a bounded receipt, never a cache dump."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
from pathlib import Path
import subprocess
import sys
import tempfile

TOTAL_SECONDS = 90
OPERATION_SECONDS = 15
RECEIPT_BYTES = 64 * 1024


def worker():
    from route_evidence import browser
    from route_evidence.core import MAX_BYTES, EvidenceError, digest, encoded
    from route_evidence.providers import Fetcher, SOURCES

    capture = browser.capture
    proof = {}

    def observed_capture(source, *, timeout):
        # Observe the real capture without replacing navigation, selectors or parsing.
        result = capture(source, timeout=timeout)
        payload = encoded(result)
        if len(payload) > MAX_BYTES:
            raise EvidenceError("probe_capture_response_too_large")
        parts = []
        for part in result["parts"]:
            table = part["tables"][0]
            headers = table[0]
            if len(headers) > 64 or any(len(label) > 240 for label in headers):
                raise EvidenceError("probe_capture_header_budget_exceeded")
            parts.append({"subset": part["subset"], "observed_subset": part["observed_subset"],
                          "headers": headers, "captured_data_rows": len(table) - 1})
        proof.update(capture_sha256=digest(result), capture_encoding="canonical JSON from core.encoded",
                     capture_bytes=len(payload), identity=result["identity"], parts=parts)
        return result

    browser.capture = observed_capture
    try:
        snapshot, validators = Fetcher(browser=True, timeout=OPERATION_SECONDS)(SOURCES["frontiercode"], {})
        reply = {"snapshot": snapshot, "validators": validators, "capture": proof}
        if len(encoded(reply)) > MAX_BYTES:
            raise EvidenceError("probe_worker_response_too_large")
    except EvidenceError as exc:
        reply = {"error": str(exc)[:300], "capture": proof}
    except Exception:
        reply = {"error": "probe_worker_internal_error", "capture": proof}
    finally:
        browser.capture = capture
    sys.stdout.buffer.write(encoded(reply))
    return 0


def run(repo):
    from route_evidence.cache import Cache, FetchError
    from route_evidence.core import MAX_BYTES, EvidenceError, digest, encoded, loads
    from route_evidence.processes import ProcessScope
    from route_evidence.providers import SOURCES

    source = SOURCES["frontiercode"]
    calls = {"online": 0, "offline": 0}
    receipt = {
        "schema_version": 1, "probe": "frontiercode_public_production_acquisition", "status": "failed",
        "source": {"id": source["id"], "url": source["url"], "benchmark": source["benchmark"],
                   "version": source["version"], "adapter": source["adapter"],
                   "adapter_revision": source["revision"], "definition_sha256": digest(source)},
        "method": "Actual Fetcher/browser capture, fresh task Cache, separate Cache instance offline reread",
        "bounds": {"acquisition_wall_seconds": TOTAL_SECONDS, "browser_operation_seconds": OPERATION_SECONDS,
                   "capture_payload_bytes": MAX_BYTES, "worker_response_bytes": MAX_BYTES,
                   "normalized_rows": 10000, "receipt_bytes": RECEIPT_BYTES,
                   "browser_network_transfer_byte_cap": None},
        "interpretation": "Rendered capture and normalized measurement hashes; no native task execution or subscription-cost measurement.",
    }
    try:
        def git(ref):
            return subprocess.check_output(["git", "-C", str(repo), "rev-parse", ref],
                                           text=True, stderr=subprocess.DEVNULL).strip()
        receipt["code"] = {"head": git("HEAD"), "tree": git("HEAD^{tree}"),
                           "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                           "provider_blob": git("HEAD:skills/route-subagents/scripts/route_evidence/providers.py"),
                           "browser_blob": git("HEAD:skills/route-subagents/scripts/route_evidence/browser.py")}
        with tempfile.TemporaryDirectory(prefix="assay-frontiercode-probe-") as temporary:
            cache_root = Path(temporary) / "cache"
            cache = Cache(cache_root)
            if cache.read(source) != {}:
                raise EvidenceError("probe_cache_was_not_empty")
            scope = ProcessScope(TOTAL_SECONDS)

            def fetch(actual_source, validators):
                calls["online"] += 1
                if actual_source != source or validators:
                    raise FetchError("probe_unexpected_source_or_validator")
                reply = loads(scope.run([sys.executable, "-B", str(Path(__file__).resolve()),
                                         "--repo", str(repo), "--worker"]).decode("utf-8"))
                if "error" in reply:
                    receipt["capture"] = reply.get("capture", {})
                    raise FetchError(reply["error"])
                if set(reply) != {"snapshot", "validators", "capture"}:
                    raise FetchError("probe_invalid_worker_reply")
                receipt["capture"] = reply["capture"]
                return reply["snapshot"], reply["validators"]

            try:
                online = cache.get(source, fetch, force=True)
            finally:
                scope.cancel()
            receipt["online"] = {key: online.get(key) for key in
                                 ("availability", "refresh", "last_attempt_at", "last_success_at", "error")}
            if online["refresh"] != "updated" or online["availability"] != "fresh" or online["snapshot"] is None:
                raise EvidenceError("probe_online_acquisition_failed")

            def forbidden_fetch(*args):
                calls["offline"] += 1
                raise AssertionError("offline reread attempted acquisition")

            offline = Cache(cache_root).get(source, forbidden_fetch, offline=True)
            snapshot = online["snapshot"]
            equal = encoded(snapshot) == encoded(offline["snapshot"])
            state = Cache(cache_root).read(source)
            receipt["cache"] = {"initial_empty": True, "offline_refresh": offline["refresh"],
                                "offline_snapshot_equal": equal,
                                "persisted_data_hash_equal": state.get("data_hash") == digest(snapshot),
                                "fetch_calls": calls}
            if not equal or calls != {"online": 1, "offline": 0} or not receipt["cache"]["persisted_data_hash_equal"]:
                raise EvidenceError("probe_offline_equality_failed")
            rows = snapshot["rows"]
            subsets = dict(sorted(Counter(row["subset"] for row in rows).items()))
            if set(subsets) != {"main", "extended"}:
                raise EvidenceError("probe_expected_both_subsets")
            receipt["normalized"] = {
                "snapshot_sha256": digest(snapshot), "snapshot_bytes": len(encoded(snapshot)),
                "rows": len(rows), "rows_by_subset": subsets,
                "metrics": sorted({row["metric"] for row in rows}),
                "intervals": {"rows_with_published_bounds": sum(row.get("score_low") is not None and row.get("score_high") is not None for row in rows),
                              "rows_without_bounds": sum(row.get("score_low") is None for row in rows),
                              "scale": "0..1", "confidence_level_inferred": False},
                "expenses": {"rows_with_value": {field: sum(row.get(field) is not None for row in rows)
                                                  for field in ("cost_usd", "output_tokens", "reported_tokens", "steps")},
                             "normalized_cost_basis_counts": dict(sorted(Counter(row.get("cost_basis") or "unknown" for row in rows).items())),
                             "rows_with_aggregate_usage": sum(bool(row.get("aggregate_usage")) for row in rows),
                             "complete_task_chain_cost_measured": False,
                             "subscription_quota_measured": False},
            }
            receipt["status"] = "passed"
    except EvidenceError as exc:
        receipt["error"] = str(exc)[:300]
    except Exception:
        receipt["error"] = "probe_internal_error"
    payload = encoded(receipt)
    if len(payload) > RECEIPT_BYTES:
        payload = encoded({"schema_version": 1, "probe": "frontiercode_public_production_acquisition",
                           "status": "failed", "error": "probe_receipt_budget_exceeded"})
        receipt["status"] = "failed"
    print("FRONTIERCODE_PROBE_RECEIPT=" + payload.decode("utf-8"), flush=True)
    return 0 if receipt["status"] == "passed" else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    repo = args.repo.resolve()
    sys.path.insert(0, str(repo / "skills" / "route-subagents" / "scripts"))
    return worker() if args.worker else run(repo)


if __name__ == "__main__":
    raise SystemExit(main())
