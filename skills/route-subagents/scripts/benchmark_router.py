#!/usr/bin/env python3
"""Benchmark evidence CLI. MCP and this CLI share the same application service."""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

from route_evidence.cache import Cache
from route_evidence.core import MAX_BYTES, EvidenceError, loads, read_document
from route_evidence.routing import TASK_TYPES, brief
from route_evidence.service import REGISTRY, RoutingService, default_cache, ingest, load_config


def add_options(parser):
    parser.add_argument("--cache-dir", type=Path, default=default_cache())
    parser.add_argument("--config", type=Path, help="local preferences and optional dated inventory")
    parser.add_argument("--client", help="native host label, not an automatic inventory detector")
    parser.add_argument("--ttl-hours", type=float, default=24)
    parser.add_argument("--timeout-seconds", type=float, default=30, help="total refresh deadline, not per-source")
    parser.add_argument("--offline", action="store_true",
                        help="diagnostic cache replay only; disables refresh, never use for live routing")
    browsers = parser.add_mutually_exclusive_group()
    browsers.add_argument("--browser", action="store_true", help="enable optional rendered-table integrations")
    browsers.add_argument("--no-browser", action="store_true", help="explicitly keep browser integrations off")
    parser.add_argument("--force", action="store_true", help="bypass freshness, never Retry-After")


def make_service(args):
    config = load_config(args.config)
    if args.client and config.get("client") and args.client != config["client"]:
        raise EvidenceError("client override conflicts with the configured client; use a separate client config")
    return RoutingService(Cache(args.cache_dir, ttl=args.ttl_hours * 3600),
                          client=args.client or config.get("client", "unconfigured"),
                          preferences=config.get("preferences"), inventory=config.get("inventory"),
                          timeout=args.timeout_seconds, browser=args.browser, offline=args.offline, force=args.force,
                          advisor_config=config)


def request_document(path):
    return loads(sys.stdin.buffer.read(MAX_BYTES + 1).decode("utf-8")) if str(path) == "-" else read_document(Path(path))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    add_options(parser)
    parser.add_argument("--details", action="store_true")
    subs = parser.add_subparsers(dest="command", required=True)
    cp = subs.add_parser("context")
    request = cp.add_mutually_exclusive_group(required=True)
    request.add_argument("--request", help="JSON file, or - for stdin")
    request.add_argument("--task-type", action="append", choices=sorted(TASK_TYPES),
                         help="repeatable; uses configured inventory and optional limits")
    for name in ("refresh", "status", "smoke"):
        sp = subs.add_parser(name)
        sp.add_argument("--source", action="append", choices=sorted(REGISTRY),
                        help="benchmark sources and vendor guides share one refresh cycle")
    ip = subs.add_parser("ingest")
    ip.add_argument("--file", type=Path, required=True)
    ip.add_argument("--observed-at", required=True)
    dp = subs.add_parser("doctor")
    dp.add_argument("--check-browser", action="store_true", help="actually launch Chromium on about:blank")
    for name in ("prepare", "complete", "record"):
        ap = subs.add_parser(name)
        ap.add_argument("--request", required=True, help="JSON object file, or - for stdin")
    hp = subs.add_parser("history-import")
    hp.add_argument("--file", type=Path, action="append", required=True,
                    help="explicit Codex/Claude JSONL path; repeat for multiple logs (read-only)")
    rp = subs.add_parser("replay")
    rp.add_argument("--record", type=Path, required=True, help="retained advisor record; never invokes a model")
    rp.add_argument("--policy", type=Path, help="optional pure-policy overrides")
    mp = subs.add_parser("migrate-config")
    mp.add_argument("--source", type=Path, required=True)
    mp.add_argument("--output", type=Path, required=True, help="new file only; never replaces the source")
    mp.add_argument("--enable-advisor", action="store_true")
    tp = subs.add_parser("task-import", help="import an explicit local corpus; no network")
    tp.add_argument("--file", type=Path, required=True)
    tp.add_argument("--manifest", type=Path, help="LLMRouterBench slice manifest; otherwise normalized corpus JSON")
    subs.add_parser("task-setup", help="download and index pinned public evidence; no model calls")
    tp = subs.add_parser("task-context", help="local task evidence only; never calls a model")
    tp.add_argument("--request", required=True)
    subs.add_parser("task-purge-descriptions", help="remove only opted-in descriptions from local receipts")
    tp = subs.add_parser("task-evaluate", help="held-out lookup on existing answers; no model calls")
    tp.add_argument("--file", type=Path, required=True)
    tp.add_argument("--unit", choices=["api_usd", "quota_units", "input_tokens", "output_tokens", "duration_seconds"], default="api_usd")
    tp.add_argument("--overhead", type=float)
    tp = subs.add_parser("task-forecast", help="chronological cost diagnostics from retained receipts; no model calls")
    tp.add_argument("--request", required=True, help="JSON with packets")
    tp.add_argument("--unit", choices=["api_usd", "quota_units", "input_tokens", "output_tokens", "duration_seconds"], default="api_usd")
    args = parser.parse_args(argv)
    try:
        if args.command == "smoke" and (args.offline or not args.force):
            raise EvidenceError("smoke requires --force and online mode")
        if args.command == "migrate-config":
            from route_evidence.advisor_config import migrate_config
            result = migrate_config(args.source, args.output, enable_advisor=args.enable_advisor)
            print(json.dumps(result, indent=2))
            return 0
        service = make_service(args)
        if args.command in {"prepare", "context", "task-context"}:
            service.advisor_workflow.task_evidence.provisioner.wait = True
        code = 0
        if args.command == "task-setup":
            from route_evidence.task_bootstrap import setup
            result = setup(service.advisor_workflow.task_evidence, offline=args.offline)
            code = 0 if result["status"] == "ready" else 2
        elif args.command == "task-forecast":
            import time
            from route_evidence.advice_contracts import validate_packets
            from route_evidence.task_evaluation import forecast
            document = request_document(args.request)
            if not isinstance(document, dict) or set(document) != {"packets"}:
                raise EvidenceError("forecast requires packets")
            packets = validate_packets(document["packets"])
            evidence = service.advisor_workflow.task_evidence
            deadline = time.monotonic() + evidence.config["deadline_seconds"]
            result = {"status": "diagnostic_only", "packets": [
                {"packet_id": p["packet_id"], **forecast(evidence.local_rows(p, deadline), args.unit)} for p in packets]}
        elif args.command == "task-evaluate":
            from route_evidence.task_evaluation import evaluate
            result = evaluate(read_document(args.file), args.unit, args.overhead)
        elif args.command == "task-purge-descriptions":
            result = service.advisor_workflow.task_evidence.purge_descriptions()
        elif args.command == "task-import":
            from route_evidence.task_import import llmrouterbench
            document = (llmrouterbench(args.file, read_document(args.manifest)) if args.manifest else
                        read_document(args.file))
            result = service.advisor_workflow.task_evidence.install(document)
        elif args.command == "task-context":
            from route_evidence.advice_contracts import validate_packets, candidate_id
            document = request_document(args.request)
            if not isinstance(document, dict) or "packets" not in document or set(document) - {"packets", "available", "task_queries", "cost_objectives"}:
                raise EvidenceError("invalid task context request")
            packets = validate_packets(document["packets"])
            prepared = service.prepare(list(dict.fromkeys(t for p in packets for t in p["task_types"])), available=document.get("available"))
            if "status" in prepared:
                result = prepared
            else:
                from route_evidence.core import effort
                candidates = [{"candidate_id": candidate_id(a["model"], effort(e)), "model": a["model"], "effort": effort(e)}
                              for a in prepared["available"] for e in a["efforts"]]
                result = asyncio.run(service.advisor_workflow.task_evidence.async_summarize(packets, candidates, document.get("task_queries"), document.get("cost_objectives")))
        elif args.command == "ingest":
            value = ingest(service.cache, read_document(args.file), args.observed_at)
            result = {"sources": [value]}
        elif args.command in ("prepare", "complete", "record"):
            document = request_document(args.request)
            allowed = {
                "prepare": {"packets", "available", "constraints", "advisor_route", "task_queries", "cost_objectives"},
                "complete": {"decision_id", "advisor_result", "envelope"},
                "record": {"decision_id", "execution"},
            }[args.command]
            if not isinstance(document, dict) or set(document) - allowed:
                raise EvidenceError("invalid advisor operation fields")
            required = {"prepare": {"packets"}, "complete": {"decision_id", "advisor_result"},
                        "record": {"decision_id", "execution"}}[args.command]
            if required - set(document):
                raise EvidenceError("missing advisor operation fields")
            if args.command == "prepare":
                result = asyncio.run(service.prepare_routing(**document, portable=True))
            elif args.command == "complete":
                result = service.complete_routing(**document)
            else:
                result = service.record_routing_outcome(**document)
        elif args.command in ("history-import", "replay"):
            from route_evidence.history import import_history, replay
            result = (import_history(args.file) if args.command == "history-import" else
                      replay(read_document(args.record), policy=read_document(args.policy) if args.policy else None))
        elif args.command == "context":
            if args.offline:
                print("DIAGNOSTIC ONLY: --offline disables source refresh. "
                      "Do not use this replay for live routing; inspect data_status/data_message.", file=sys.stderr)
            if args.request:
                # External JSON is always a request, never an internal result.
                document = request_document(args.request)
                if isinstance(document, dict) and ("task_query" in document or "features" in document):
                    query, features = document.pop("task_query", None), document.pop("features", None)
                    if "task_types" not in document or set(document) - {"task_types", "client", "available", "constraints"}:
                        raise EvidenceError("invalid task context fields")
                    if document.get("client", service.client) != service.client:
                        raise EvidenceError("task context client conflicts with configured client")
                    result = asyncio.run(service.get_routing_context(document["task_types"], available=document.get("available"),
                        constraints=document.get("constraints"), details=True, task_query=query, features=features))
                else:
                    result = asyncio.run(service.context(document))
            else:
                result = asyncio.run(service.get_routing_context(args.task_type, details=True))
        elif args.command in ("status", "doctor"):
            result = service.status(getattr(args, "source", None))
            if args.command == "doctor" and args.check_browser:
                from route_evidence.processes import ProcessScope
                from route_evidence.core import encoded
                scope = ProcessScope(args.timeout_seconds)
                try:
                    worker = Path(__file__).parent / "route_evidence" / "worker.py"
                    reply = loads(scope.run([sys.executable, "-B", str(worker)], encoded({"diagnose_browser": True})).decode("utf-8"))
                    result["browser_check"] = reply
                    result["installation"].update(browser_launch_checked=True, browser_launch_ready=not bool(reply.get("error")))
                    code = 2 if reply.get("error") else 0
                finally:
                    scope.cancel()
        else:
            result = {"sources": asyncio.run(service.refresh(args.source))}
            if args.command == "smoke":
                # A live smoke must fetch, not validate synthetic cache entries.
                # Caller uses --force; refuse misleading offline smoke success.
                code = 0 if all(s.get("snapshot") and s.get("refresh") in ("updated", "validated_not_modified")
                                for s in result["sources"]) else 2
        if not args.details and not args.command.startswith("task-"):
            # Raw rows are dropped; candidates, gaps and limits stay complete.
            result = brief(result)
        print(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False))
        return code
    except (EvidenceError, OSError, UnicodeError) as exc:
        print(json.dumps({"status": "error", "error": str(exc)}, ensure_ascii=False))
        return 2
    except KeyboardInterrupt:
        return 130
    finally:
        if "service" in locals() and service._advisor_workflow is not None:
            service.advisor_workflow.task_evidence.provisioner.close()


if __name__ == "__main__":
    raise SystemExit(main())
