#!/usr/bin/env python3
"""Record, capture or inspect local feedback cases without calling a model."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "hooks"))
sys.path.insert(0, str(ROOT / "skills/route-subagents/scripts"))
from runtime import feedback
from route_evidence.core import loads

MAX_INPUT = 1024 * 1024


class FeedbackParser(argparse.ArgumentParser):
    def error(self, message):
        # Native clients can interpret argparse's normal exit 2 as a request
        # to block. Also avoid echoing user-supplied command argument values.
        raise ValueError("invalid feedback command arguments")


def input_object(path=None):
    if path:
        with path.open("rb") as stream:
            raw = stream.read(MAX_INPUT + 1)
    else:
        raw = sys.stdin.buffer.read(MAX_INPUT + 1)
    if len(raw) > MAX_INPUT:
        raise ValueError("oversized feedback input")
    data = loads(raw.decode("utf-8"))
    if not isinstance(data, dict):
        raise ValueError("feedback input must be an object")
    return data


def main(argv=None):
    arguments = list(sys.argv[1:] if argv is None else argv)
    parser = FeedbackParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    event = commands.add_parser("event", help="native event on stdin; input failures never block a task")
    event.add_argument("--client", choices=tuple(feedback.CLIENT_EVENTS), required=True)
    event.add_argument("--config", type=Path, help="absolute owner-controlled ASSAY_HOOK_CONFIG override")
    explicit = commands.add_parser("record", help="explicit case from the user or agent; JSON object on stdin or --input")
    explicit.add_argument("--state-dir", type=Path, help="absolute parent data directory; default from configuration")
    explicit.add_argument("--config", type=Path, help="absolute owner-controlled ASSAY_HOOK_CONFIG override")
    explicit.add_argument("--input", type=Path, help="JSON object file; default stdin")
    for name in ("list", "show", "annotate", "review", "delete", "export"):
        command = commands.add_parser(name)
        command.add_argument("--state-dir", type=Path, required=True, help="absolute parent data directory, not its feedback child")
        if name not in {"list", "export"}:
            command.add_argument("id")
        if name == "annotate":
            command.add_argument("--input", type=Path, help="JSON object file; default stdin")
        if name == "review":
            command.add_argument("--status", choices=feedback.REVIEW_STATES, required=True)
            command.add_argument("--reason", help="free text; content mode only")
            command.add_argument("--reason-code", choices=sorted({code for codes in feedback.REVIEW_CODES.values() for code in codes}))
            command.add_argument("--basis-ref", help="identifier of the evidence a confirmation rests on")
            command.add_argument("--layer", choices=feedback.LAYERS, help="reviewer's cause-layer hypothesis")
            command.add_argument("--duplicate-of")
    try:
        args = parser.parse_args(arguments)
        if args.command == "event":
            # Import lazily: inspection/annotation does not load client guards,
            # settings or a model, and an event never edits native settings.
            from runtime.cli import options
            environment = dict(os.environ)
            if args.config:
                environment["ASSAY_HOOK_CONFIG"] = str(args.config)
            result = feedback.handle(input_object(), args.client, options(environment), root=ROOT)
        elif args.command == "record":
            from runtime.cli import options
            environment = dict(os.environ)
            if args.config:
                environment["ASSAY_HOOK_CONFIG"] = str(args.config)
            settings = options(environment)
            directory = args.state_dir or settings["state_dir"]
            if not directory:
                raise ValueError("record needs --state-dir or a configured state directory")
            entry = feedback.record(directory, input_object(args.input), settings, root=ROOT)
            result = {"id": entry["id"], "kind": entry["kind"], "status": entry["status"],
                      "capture_mode": entry["capture_mode"]}
        elif args.command in {"list", "export"}:
            records = feedback.read(args.state_dir)
            if args.command == "export":
                for record in records:
                    # ASCII JSON is valid UTF-8 and round-trips non-ASCII text
                    # even under a Windows console's legacy output encoding.
                    print(json.dumps(record))
                return 0
            result = [{key: record[key] for key in ("id", "kind", "created_at", "status", "signal", "capture_mode")}
                      | {"client": record["source"]["client"], "annotations": len(record["annotations"])}
                      for record in records]
        elif args.command == "show":
            result = feedback.read(args.state_dir, args.id)
        elif args.command == "annotate":
            record = feedback.annotate(args.state_dir, args.id, input_object(args.input))
            result = {"id": record["id"], "status": record["status"], "annotations": len(record["annotations"])}
        elif args.command == "review":
            record = feedback.review(args.state_dir, args.id, args.status, args.reason,
                                     reason_code=args.reason_code, basis_ref=args.basis_ref,
                                     layer=args.layer, duplicate_of=args.duplicate_of)
            result = {"id": record["id"], "status": record["status"], "reviews": len(record["reviews"])}
        else:
            feedback.delete(args.state_dir, args.id)
            result = {"id": args.id, "deleted": True}
        print(json.dumps(result))
        return 0
    except Exception:
        # Do not echo payloads, paths, credentials or user/model summaries. The
        # optional recorder never emits a blocking code or permission decision.
        print("Assay: feedback operation unavailable; check configuration, input, store capacity and permissions. No success claimed.", file=sys.stderr)
        if arguments[:1] == ["event"]:
            print("{}")
            return 0
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
