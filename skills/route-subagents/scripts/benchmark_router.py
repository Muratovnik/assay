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
        code = 0
        if args.command == "ingest":
            value = ingest(service.cache, read_document(args.file), args.observed_at)
            result = {"sources": [value]}
        elif args.command in ("prepare", "complete", "record"):
            document = request_document(args.request)
            allowed = {
                "prepare": {"packets", "available", "constraints", "advisor_route"},
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
                result = asyncio.run(service.context(request_document(args.request)))
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
        if not args.details:
            # Raw rows are dropped; candidates, gaps and limits stay complete.
            result = brief(result)
        print(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False))
        return code
    except (EvidenceError, OSError, UnicodeError) as exc:
        print(json.dumps({"status": "error", "error": str(exc)}, ensure_ascii=False))
        return 2
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
