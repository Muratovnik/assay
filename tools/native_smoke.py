"""Inspect captured native events without treating model self-reports as evidence.

Claude Skill tool success is observable in stream-json. The supported Codex
JSON projection has command events, not a stable skill-activation receipt; it
is deliberately reported as unverified rather than guessed from shell text.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

if __package__:
    from .command_receipt import verify, digest
else:
    from command_receipt import verify, digest


def inspect_events(text: str, *, client: str, required: tuple[str, ...] = (),
                   forbidden: tuple[str, ...] = ()) -> dict[str, Any]:
    if client not in ("codex", "claude") or set(required) & set(forbidden):
        raise ValueError("invalid client or contradictory selection requirements")
    records = []
    for index, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        record = json.loads(line)
        if not isinstance(record, dict) or not isinstance(record.get("type"), str):
            raise ValueError(f"invalid native event at line {index}")
        records.append(record)
    if not records:
        raise ValueError("empty native trace")
    calls: dict[str, dict[str, Any]] = {}
    completed = False
    errors = []
    if client == "claude":
        for record in records:
            if record["type"] == "result":
                completed = record.get("is_error") is False
                if record.get("is_error"):
                    errors.append("native result is_error")
            message = record.get("message", {})
            if record["type"] not in ("assistant", "user") or not isinstance(message, dict):
                continue
            content = message.get("content", [])
            if not isinstance(content, list):
                continue
            for block in content:
                if not isinstance(block, dict):
                    continue
                if block.get("type") == "tool_use":
                    ident = block.get("id")
                    args = block.get("input", {})
                    if not isinstance(ident, str) or not isinstance(args, dict) or not isinstance(block.get("name"), str):
                        raise ValueError("malformed native tool invocation")
                    if block["name"] == "Skill" and not isinstance(args.get("skill"), str):
                        raise ValueError("malformed Skill invocation")
                    if ident in calls:
                        raise ValueError("duplicate Skill invocation ID")
                    calls[ident] = {"id": ident, "tool": block["name"], "input": args,
                                    "skill": args.get("skill") if block["name"] == "Skill" else None,
                                    "outcome": "attempted"}
                elif block.get("type") == "tool_result":
                    call = calls.get(block.get("tool_use_id"))
                    if call is not None:
                        if call["outcome"] != "attempted":
                            raise ValueError("duplicate Skill result")
                        call["outcome"] = "failed" if block.get("is_error", False) else "succeeded"
    else:
        completed = any(record["type"] == "turn.completed" for record in records)
        errors = [record["type"] for record in records if record["type"] in ("error", "turn.failed")]
    loaded = {call["skill"] for call in calls.values() if call["tool"] == "Skill" and call["outcome"] == "succeeded"}
    prohibited = sorted({call["skill"] for call in calls.values() if call["tool"] == "Skill"} & set(forbidden))
    missing = sorted(set(required) - loaded)
    if prohibited:
        status = "refuted"
    elif client == "codex" or not completed or errors or missing:
        status = "unverified"
    else:
        status = "observed-loader-contract"
    return {"client": client, "status": status, "terminal_observed": completed,
            "calls": list(calls.values()),
            "adverse_calls": [call for call in calls.values() if call["outcome"] != "succeeded"],
            "missing_loader_success": missing,
            "prohibited_attempts": prohibited, "native_errors": errors,
            "trace_sha256": digest(text.encode("utf-8")),
            "limits": ["Declared prompt, model, effort and client version belong in the run record.",
                       "Explicit loading is not automatic selection; source reads may bypass Skill.",
                       "A loader event is not evidence of following the method or effective permissions.",
                       "Codex automatic discovery remains unverified by this event adapter.",
                       "Negative results cover only captured Skill-loader events, not all filesystem reads."]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--client", choices=["claude", "codex"], required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--manifest-sha256", required=True)
    parser.add_argument("--require", action="append", default=[])
    parser.add_argument("--forbid", action="append", default=[])
    args = parser.parse_args()
    try:
        intent, run = verify(args.receipt, args.manifest_sha256)
        result = inspect_events((args.receipt / "stdout.bin").read_text(encoding="utf-8"),
                                client=args.client, required=tuple(args.require), forbidden=tuple(args.forbid))
        if (run["state"] != "completed" or run.get("changed_inputs")) and result["status"] != "refuted":
            result["status"] = "unverified"
        result["command"] = intent["argv"]
        result["source_inputs"] = intent["inputs_before"]
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return {"observed-loader-contract": 0, "refuted": 1, "unverified": 2}[result["status"]]
    except (OSError, ValueError, TypeError, KeyError) as error:
        print(f"native smoke: unverified: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
