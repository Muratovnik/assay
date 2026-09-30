"""Bounded plugin records in the existing transactional rendezvous store.

No prompts, transcripts, tool arguments, task database or second store engine.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import time

from .activation import context
from .events import event_key, identity

TTL = 24 * 3600
MAX_OWN_RECORDS = 128
KINDS = ("hook-context", "hook-seen", "hook-event")


def _put(tx, kind, key, payload, now):
    records = tx.values(kind)
    if len(records) >= MAX_OWN_RECORDS and not tx.get(kind, key):
        oldest = min(records, key=lambda item: item["at"])
        tx.delete(kind, oldest["id"])
    tx.put(kind, key, {**payload, "id": key, "at": now}, now + TTL)


def apply(event, client, decision, rules, fingerprint, directory, *, record=False, outcome=None, clock=time.time):
    from route_evidence.pipeline_store import PipelineStore
    key = identity(event, client)
    if key is None:
        return decision
    now, name = clock(), event["hook_event_name"]
    delivery = event_key(event, client)
    # Native delivery identity is independent of inference and rule revisions.
    # Check it before changing context, including for prompts with no hint.
    seen = hashlib.sha256(json.dumps([key, delivery]).encode()).hexdigest() if delivery else None
    if outcome is not None:
        decision = {"rule_ids": [], "context": ""}
    with PipelineStore(Path(directory), clock=clock).transaction() as tx:
        duplicate = bool(seen and tx.get("hook-seen", seen))
        if duplicate:
            decision = {"rule_ids": [], "context": ""}
        elif name == "SessionEnd":
            # Deduplication expires independently; no broad delete by parent
            # session, which would destroy a different agent's current context.
            tx.delete("hook-context", key)
        elif name == "UserPromptSubmit" and outcome is None:
            _put(tx, "hook-context", key, {"rules": decision["rule_ids"], "fingerprint": fingerprint}, now)
        elif name == "PostCompact":
            # Codex accepts common output only, not additionalContext here.
            previous = tx.get("hook-context", key)
            if previous and previous["fingerprint"] == fingerprint:
                _put(tx, "hook-context", key, {**previous, "pending_restore": True}, now)
            decision = {"rule_ids": [], "context": ""}
        elif name == "PreToolUse" and outcome is None:
            previous = tx.get("hook-context", key)
            if previous and previous["fingerprint"] == fingerprint and previous.get("pending_restore"):
                names = ", ".join(r["skill"].split("/", 1)[1] for r in rules if r["id"] in previous["rules"])
                if names:
                    decision = {"rule_ids": previous["rules"], "context": decision["context"] +
                        f" Previous request suggested {names}; recheck relevance after compaction."}
                _put(tx, "hook-context", key, {**previous, "pending_restore": False}, now)
        elif name == "SessionStart" and outcome is None and event.get("source") in {"resume", "compact"}:
            previous = tx.get("hook-context", key)
            if previous and previous["fingerprint"] == fingerprint:
                restored = context(previous["rules"], rules, restored=True)
                decision = {"rule_ids": previous["rules"], "context":
                            "\n".join(part for part in (decision["context"], restored) if part)}
                # SessionStart(compact) can deliver the hint before the next
                # tool. Do not replay it again through the PostCompact fallback.
                if previous.get("pending_restore"):
                    _put(tx, "hook-context", key, {**previous, "pending_restore": False}, now)
        elif name == "SessionStart" and event.get("source") in {"startup", "clear", "fork"}:
            tx.delete("hook-context", key)
        # A guard response takes precedence over context. Do not consume an
        # undelivered hint (or its deduplication key) when a guard owns the reply.
        if seen and not duplicate and outcome is None and (name == "UserPromptSubmit" or decision["context"]):
            _put(tx, "hook-seen", seen, {}, now)
        if record:
            # This records receipt of command input, not authenticated client
            # execution and certainly not compliance with a skill.
            eid = hashlib.sha256(json.dumps([key, delivery, name, now]).encode()).hexdigest()
            _put(tx, "hook-event", eid, {"client": client, "event": name,
                 "rule_ids": decision["rule_ids"], "decision": outcome or ("duplicate" if duplicate else "hint" if decision["context"] else "silent"),
                 "evidence": "command_input_unattested"}, now)
    return decision
