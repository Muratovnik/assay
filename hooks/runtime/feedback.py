"""Opt-in feedback candidates; observations are not diagnoses or evaluations."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import time
import uuid

from .activation import request_text
from .events import identity, event_key
from route_evidence.pipeline_store import PipelineStore

MODES = ("off", "metadata", "content")
CLIENT_EVENTS = {"claude": "UserPromptSubmit", "codex": "UserPromptSubmit",
                 "gemini": "BeforeAgent", "cursor": "beforeSubmitPrompt"}
KIND = "feedback-candidate-v1"
RETENTION = 90 * 24 * 3600
MAX_RECORDS = 512
MAX_EXCERPT = 4096
MAX_ANNOTATIONS = 4
CATEGORIES = ("reported_mismatch", "changed_requirement", "preference", "disagreement", "uncertain")
BASES = ("prior_requirement", "new_requirement", "unknown")
REVIEW_STATES = ("candidate", "confirmed", "dismissed", "duplicate")
TEXT_FIELDS = ("task", "observed", "expected", "hypothesis", "evidence")
# These are candidate signals, not a sentiment classifier or a verdict. The
# existing CommonMark selector keeps quoted documents/code out of this grammar.
SIGNALS = (
    ("omission", r"^(?:you (?:missed|omitted|forgot|ignored)\b|ты (?:упустил\w*|пропустил\w*|забыл\w*|проигнорировал\w*)\b)"),
    ("correction", r"^(?:(?:no|нет)[,.!:]?\s+)?(?:i (?:asked|said|meant)\b|я (?:просил\w*|говорил\w*|имел\w* в виду)\b)"),
    ("correction", r"^(?:that(?:'s| is) (?:wrong|incorrect|not what i)|this is (?:wrong|incorrect|not what i)|это (?:неправильно|неверно|не то)\b)"),
    ("omission", r"^(?:why (?:didn't|did not|haven't|have not) you\b|почему ты не\b)"),
    ("repeated_constraint", r"^(?:i already (?:told|asked)|я (?:уже|же) (?:говорил\w*|просил\w*)\b|ты опять\b|you (?:did it|are doing it) again\b)"),
    ("correction", r"^(?:not what i (?:asked|meant)|не (?:это|то) (?:я )?имел\w* в виду)\b"),
)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def bounded_id(value):
    return isinstance(value, str) and 0 < len(value) <= 512 and not any(ord(c) < 32 for c in value)


def source(event, client):
    """Normalize only documented identity fields, never open transcript paths."""
    if client not in CLIENT_EVENTS or not isinstance(event, dict):
        raise ValueError("unsupported feedback client or event")
    name = event.get("hook_event_name")
    if name != CLIENT_EVENTS[client] and not (client == "cursor" and name == "postToolUse"):
        return None
    if client in {"claude", "codex"}:
        scope = identity(event, client)
        session, delivery = event.get("session_id"), event_key(event, client)
    elif client == "gemini":
        session, delivery = event.get("session_id"), None
        cwd, transcript = event.get("cwd"), event.get("transcript_path")
        if not bounded_id(session) or not isinstance(cwd, str) or not 0 < len(cwd) <= 4096:
            return None
        if not isinstance(transcript, str) or not 0 < len(transcript) <= 4096:
            return None
        scope = digest([client, session, cwd, transcript])
    else:
        session, generation = event.get("conversation_id"), event.get("generation_id")
        roots = event.get("workspace_roots")
        if not bounded_id(session) or not bounded_id(generation):
            return None
        if not isinstance(roots, list) or not 1 <= len(roots) <= 32 or any(
                not isinstance(p, str) or not 0 < len(p) <= 4096 for p in roots):
            return None
        scope, delivery = digest([client, session, roots]), "generation:" + generation
    if not scope or not bounded_id(session) or (delivery is not None and not bounded_id(delivery)):
        return None
    return {"client": client, "event": name, "scope": scope,
            "session_id": session, "delivery_id": delivery,
            "evidence_level": "command_input_unattested"}


def signal(prompt):
    text = request_text(prompt, set())
    for kind, pattern in SIGNALS:
        if re.search(pattern, text, re.I):
            return kind
    return None


def store(directory, *, clock=time.time):
    directory = Path(directory)
    if not directory.is_absolute():
        raise ValueError("feedback state directory must be absolute")
    # A separate directory reuses the store implementation, not the routing
    # database's capacity or short-lived receipt lifetime.
    return PipelineStore(directory / "feedback", clock=clock)


def candidate_id(origin):
    if origin["delivery_id"] is not None:
        return digest([origin["scope"], origin["delivery_id"]])
    # Identical Claude/Gemini text can be a genuinely new correction. A text
    # hash or timestamp is not a native idempotency key.
    return uuid.uuid4().hex


def notice(record, directory, root):
    entry = json.dumps(str(root / "hooks/runtime/feedback_cli.py"))
    location = json.dumps(str(directory))
    schema = '{"category":"reported_mismatch|changed_requirement|preference|disagreement|uncertain","basis":"prior_requirement|new_requirement|unknown"}'
    detail = (" Optional text fields: task, observed, expected, hypothesis, evidence (each <=1500 characters)."
              if record["capture_mode"] == "content" else " Do not include free text in metadata mode.")
    return (f"Assay feedback candidate {record['id']} was recorded locally, not confirmed as an error. "
            "During this existing turn, compare the user's correction with the earlier request and actual work. "
            "Changed requirements, preferences and disagreement are not proof of failure; do not agree merely to please. "
            "If permitted shell access is available, annotate once using Python 3.11+ with -I -B and script "
            f"{entry}, arguments annotate {record['id']} --state-dir {location}, JSON on stdin: {schema}."
            + detail + " Keep the cause unknown unless supported; never confirm, dismiss, create evals or edit instructions automatically. "
            "No additional model call, retry loop or interruption of the user's task is required. "
            "Missing permission or an unavailable recorder leaves the candidate unannotated; do not bypass the sandbox.")


def handle(event, client, settings, *, root, clock=time.time):
    mode = settings.get("feedback_capture", "off")
    if mode not in MODES:
        raise ValueError("invalid feedback capture mode")
    if mode == "off":
        return {}
    origin = source(event, client)
    if origin is None:
        return {}
    directory = settings.get("state_dir")
    if not directory:
        raise ValueError("feedback capture needs a state directory")
    now = clock()
    key = candidate_id(origin)
    if client == "cursor" and origin["event"] == "postToolUse":
        with store(directory, clock=clock).transaction() as tx:
            record = tx.get(KIND, key)
            if not record or not record["pending_notice"] or now - record["created_at"] > 24 * 3600:
                return {}
            message = notice(record, directory, root)
            record["pending_notice"] = False
            tx.put(KIND, key, record, record["expires_at"])
        return {"additional_context": message}
    prompt = event.get("prompt")
    kind = signal(prompt)
    if not kind:
        return {}
    version = (root / "VERSION").read_text(encoding="utf-8").strip()
    if not bounded_id(version):
        raise ValueError("invalid installed revision")
    record = {"schema": 1, "id": key, "created_at": now, "expires_at": now + RETENTION,
              "status": "candidate", "source": origin, "signal": kind,
              "capture_mode": mode, "assay_version": version,
              "excerpt": prompt[:MAX_EXCERPT] if mode == "content" else None,
              "excerpt_truncated": len(prompt) > MAX_EXCERPT if mode == "content" else False,
              "annotations": [], "review": None, "pending_notice": client == "cursor"}
    message = notice(record, directory, root)
    with store(directory, clock=clock).transaction() as tx:
        if tx.get(KIND, key):
            return {}
        if len(tx.values(KIND)) >= MAX_RECORDS:
            raise ValueError("feedback store full; inspect and delete records explicitly")
        tx.put(KIND, key, record, record["expires_at"])
    if client == "cursor":
        # beforeSubmitPrompt has no documented additional_context output. The
        # next successful tool in this generation carries the advisory notice.
        return {}
    output = {"additionalContext": message}
    if client != "gemini":
        output["hookEventName"] = origin["event"]
    return {"hookSpecificOutput": output}


def read(directory, key=None, *, clock=time.time):
    with store(directory, clock=clock).transaction() as tx:
        if key is not None:
            record = tx.get(KIND, key)
            if record is None:
                raise ValueError("unknown or expired feedback candidate")
            return record
        return sorted(tx.values(KIND), key=lambda item: (item["created_at"], item["id"]))


def annotate(directory, key, data, *, clock=time.time):
    if not isinstance(data, dict) or set(data) - {"category", "basis", *TEXT_FIELDS}:
        raise ValueError("invalid annotation fields")
    if data.get("category") not in CATEGORIES or data.get("basis") not in BASES:
        raise ValueError("invalid annotation category or requirement basis")
    for field in TEXT_FIELDS:
        if field in data and (not isinstance(data[field], str) or len(data[field]) > 1500):
            raise ValueError("invalid annotation text")
    with store(directory, clock=clock).transaction() as tx:
        record = tx.get(KIND, key)
        if record is None:
            raise ValueError("unknown or expired feedback candidate")
        if record["capture_mode"] != "content" and set(data) & set(TEXT_FIELDS):
            raise ValueError("text annotations require content capture consent")
        if any(item["value"] == data for item in record["annotations"]):
            return record
        if len(record["annotations"]) >= MAX_ANNOTATIONS:
            raise ValueError("annotation history full")
        record["annotations"].append({"at": clock(), "provenance": "model_or_caller_interpretation", "value": data})
        tx.put(KIND, key, record, record["expires_at"])
        return record


def review(directory, key, status, reason, *, duplicate_of=None, clock=time.time):
    if status not in REVIEW_STATES or not isinstance(reason, str) or not 0 < len(reason.strip()) <= 1500:
        raise ValueError("explicit review needs a status and bounded reason")
    with store(directory, clock=clock).transaction() as tx:
        record = tx.get(KIND, key)
        if record is None:
            raise ValueError("unknown or expired feedback candidate")
        if status == "duplicate":
            if duplicate_of == key or not isinstance(duplicate_of, str) or not tx.get(KIND, duplicate_of):
                raise ValueError("duplicate must reference another retained candidate")
        elif duplicate_of is not None:
            raise ValueError("duplicate reference requires duplicate status")
        if record["capture_mode"] != "content":
            raise ValueError("textual review needs content capture consent; use delete for metadata records")
        record["status"] = status
        record["review"] = {"at": clock(), "reason": reason, "duplicate_of": duplicate_of,
                            "provenance": "explicit_local_review_unattested"}
        tx.put(KIND, key, record, record["expires_at"])
        return record


def delete(directory, key, *, clock=time.time):
    with store(directory, clock=clock).transaction() as tx:
        if tx.get(KIND, key) is None:
            raise ValueError("unknown or expired feedback candidate")
        tx.delete(KIND, key)
