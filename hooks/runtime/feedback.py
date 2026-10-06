"""Opt-in feedback records; observations are not diagnoses or evaluations."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import time
import uuid

from .activation import load_rules, request_text
from .events import identity, event_key
from route_evidence.pipeline_store import PipelineStore

MODES = ("off", "metadata", "content")
# Storage mode and trigger are separate decisions. Explicit records are always
# available while storage is on; the correction grammar runs only when chosen.
TRIGGERS = ("explicit", "hook")
CLIENT_EVENTS = {"claude": "UserPromptSubmit", "codex": "UserPromptSubmit",
                 "gemini": "BeforeAgent", "cursor": "beforeSubmitPrompt"}
KIND = "feedback-candidate-v1"
SCHEMA = 2
RETENTION = 90 * 24 * 3600
MAX_RECORDS = 512
MAX_EXCERPT = 4096
MAX_ANNOTATIONS = 4
MAX_REVIEWS = 8
MAX_REFS = 8
MAX_METHODS = 16
RECORD_KINDS = ("correction", "allowed_behavior")
CATEGORIES = ("reported_mismatch", "changed_requirement", "preference", "disagreement", "uncertain")
BASES = ("prior_requirement", "new_requirement", "unknown")
# A cause-layer code is a reviewer's or annotator's hypothesis, never a finding.
LAYERS = ("absent", "not_loaded", "loaded_not_applied", "check_missed", "unknown")
REVIEW_STATES = ("candidate", "confirmed", "dismissed", "duplicate")
# Codes let a metadata record be reviewed without a free-text channel.
REVIEW_CODES = {
    "candidate": ("reopened", "new_evidence"),
    "dismissed": ("not_a_correction", "new_requirement", "preference", "insufficient_evidence",
                  "out_of_scope", "other"),
    "duplicate": ("same_incident",),
    "confirmed": (),
}
TEXT_FIELDS = ("task", "observed", "expected", "hypothesis", "evidence")
# Identifiers only: tracker items, commits, receipts, session IDs or relative
# anchors. No spaces, so a reference cannot carry a sentence.
REFERENCE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:#/@+-]{0,159}")
# A drive-qualified or home-rooted path stays a user path when its root is
# stripped. Shape cannot prove that a relative name or a token is not private.
USER_PATH = re.compile(r"[A-Za-z]:|(?:(?:mnt|cygdrive)/)?(?:[a-z]/)?(?:Users|home)/")
CRITERION_CODE = re.compile(r"[A-Za-z][A-Za-z0-9.-]{0,31}")
METHOD_PATH = re.compile(r"skills/[a-z][a-z0-9-]{0,63}/(?:SKILL\.md|references/[a-z0-9][a-z0-9-]{0,95}\.md)")
REVISION = re.compile(r"[0-9a-f]{7,64}")
# These are candidate signals, not a sentiment classifier or a verdict. The
# existing CommonMark selector keeps quoted documents/code out of this grammar.
SIGNALS = (
    ("omission", r"^(?:you (?:missed|omitted|forgot|ignored)\b|ты (?:упустил\w*|пропустил\w*|забыл\w*|проигнорировал\w*)\b)"),
    ("correction", r"^(?:i (?:asked|said|meant)\b|я (?:просил\w*|говорил\w*|имел\w* в виду)\b)"),
    ("correction", r"^(?:that(?:'s| is) (?:wrong|incorrect|not what i)|this is (?:wrong|incorrect|not what i)|это (?:неправильно|неверно|не то)\b)"),
    ("omission", r"^(?:why (?:didn't|did not|haven't|have not) you\b|почему ты не\b)"),
    ("repeated_constraint", r"^(?:i already (?:told|asked)|я (?:уже|же) (?:говорил\w*|просил\w*)\b|ты опять\b|you (?:did it|are doing it) again\b)"),
    ("correction", r"^(?:not what i (?:asked|meant)|не (?:это|то) (?:я )?имел\w* в виду)\b"),
)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def bounded_id(value):
    return isinstance(value, str) and 0 < len(value) <= 512 and not any(ord(c) < 32 for c in value)


def reference(value):
    """Accept a bounded identifier, never a user path or prose."""
    if not isinstance(value, str) or not REFERENCE.fullmatch(value) or USER_PATH.match(value):
        raise ValueError("references must be bounded identifiers without spaces or user paths")
    return value


def references(values):
    if not isinstance(values, list) or len(values) > MAX_REFS:
        raise ValueError("invalid reference list")
    return [reference(value) for value in values]


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
    text = re.sub(r"^(?:no|нет)[,.!:]?\s+", "", text, flags=re.I)
    if re.match(r"^you missed nothing\b", text, re.I):
        return None
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


def installed_version(root):
    version = (root / "VERSION").read_text(encoding="utf-8").strip()
    if not bounded_id(version):
        raise ValueError("invalid installed revision")
    return version


def rules_fingerprint(root, settings):
    """Fingerprint of hint rules and SKILL.md bytes; it does not cover references."""
    try:
        return load_rules(root, disabled_rules=settings.get("disabled_rules", ()),
                          disabled_skills=settings.get("disabled_skills", ()))[1]
    except Exception:
        return "unknown"


def method_identity(root, paths, revision):
    """Digest the reported method files as present in this recorder's root.

    The bytes an agent actually read may come from another installed copy, so
    the basis is named rather than presented as proof of the method used.
    """
    digests = {}
    for path in paths:
        target = root / path
        try:
            digests[path] = hashlib.sha256(target.read_bytes()).hexdigest() if target.is_file() else "unavailable"
        except OSError:
            digests[path] = "unavailable"
    return {"revision": revision or "unknown",
            "revision_basis": "caller_supplied" if revision else "unknown",
            "digests": digests or "unknown",
            "digest_basis": "recorder_root_bytes" if digests else "unknown"}


def context(root, settings, *, methods=None, revision=None):
    return {"assay_version": installed_version(root),
            "rules_fingerprint": rules_fingerprint(root, settings),
            "methods_reported": ({"paths": methods, "provenance": "self_reported"}
                                 if methods else "unknown"),
            "method_identity": method_identity(root, methods or [], revision)}


def notice(record, directory, root):
    entry = json.dumps(str(root / "hooks/runtime/feedback_cli.py"))
    location = json.dumps(str(directory))
    detail = (" Optional text fields: task, observed, expected, hypothesis, evidence (each <=1500 characters)."
              if record["capture_mode"] == "content" else " Do not include free text in metadata mode.")
    return (f"Assay feedback candidate {record['id']} was recorded locally, not confirmed as an error. "
            "During this existing turn, compare the user's correction with the earlier request and actual work. "
            "Changed requirements, preferences and disagreement are not proof of failure; do not agree merely to please. "
            "If permitted shell access is available, annotate once using Python 3.11+ with -I -B and script "
            f"{entry}, arguments annotate {record['id']} --state-dir {location}, JSON on stdin. "
            'A valid uncertain annotation is {"category":"uncertain","basis":"unknown"}. '
            "Choose category from reported_mismatch, changed_requirement, preference, disagreement, uncertain; "
            "choose basis from prior_requirement, new_requirement, unknown. A reported mismatch is an allegation, not proof. "
            "An optional layer code (absent, not_loaded, loaded_not_applied, check_missed, unknown) is a hypothesis; "
            "use unknown without a trace. "
            "Use unknown when the earlier requirement cannot be located; do not reconstruct it from the complaint."
            + detail + " Keep the cause unknown unless supported; never confirm, dismiss, create evals or edit instructions automatically. "
            "No additional model call, retry loop or interruption of the user's task is required. "
            "Missing permission or an unavailable recorder leaves the candidate unannotated; do not bypass the sandbox.")


def handle(event, client, settings, *, root, clock=time.time):
    mode = settings.get("feedback_capture", "metadata")
    trigger = settings.get("feedback_trigger", "explicit")
    if mode not in MODES or trigger not in TRIGGERS:
        raise ValueError("invalid feedback capture mode or trigger")
    if mode == "off" or trigger != "hook":
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
    record = {"schema": SCHEMA, "id": key, "kind": "correction", "created_at": now,
              "expires_at": now + RETENTION, "status": "candidate", "source": origin, "signal": kind,
              "capture_mode": mode, "assay_version": installed_version(root),
              "context": context(root, settings), "criterion": None, "related": None, "trace_refs": [],
              "excerpt": prompt[:MAX_EXCERPT] if mode == "content" else None,
              "excerpt_truncated": len(prompt) > MAX_EXCERPT if mode == "content" else False,
              "annotations": [], "review": None, "reviews": [], "pending_notice": client == "cursor"}
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


def criterion(value):
    if value is None:
        return None
    if not isinstance(value, dict) or set(value) - {"code", "ref"} or not value:
        raise ValueError("criterion takes a short code and/or an owning-record reference")
    if "code" in value and (not isinstance(value["code"], str) or not CRITERION_CODE.fullmatch(value["code"])):
        raise ValueError("invalid criterion code")
    if "ref" in value:
        reference(value["ref"])
    return dict(value)


def record(directory, data, settings, *, root, clock=time.time):
    """Store a case by explicit decision of the user or agent, without a hook event.

    Deciding to record a case does not grant content consent: free text is kept
    only when the owner-controlled storage mode is already `content`.
    """
    mode = settings.get("feedback_capture", "metadata")
    if mode not in MODES:
        raise ValueError("invalid feedback capture mode")
    if mode == "off":
        raise ValueError("feedback storage is off")
    allowed = {"kind", "client", "session_id", "criterion", "related", "trace_refs",
               "methods_reported", "revision", "excerpt"}
    if not isinstance(data, dict) or set(data) - allowed:
        raise ValueError("invalid record fields")
    kind = data.get("kind")
    if kind not in RECORD_KINDS:
        raise ValueError("record kind must be correction or allowed_behavior")
    client = data.get("client", "unknown")
    if client not in (*CLIENT_EVENTS, "unknown"):
        raise ValueError("unknown client")
    session = data.get("session_id")
    if session is not None:
        # A hook reads the session ID from the native event; a caller-supplied
        # one takes the identifier shape so it cannot carry a sentence.
        reference(session)
    rule = criterion(data.get("criterion"))
    if kind == "allowed_behavior" and not rule:
        # An allowed example is defined by the criterion it satisfies, never by
        # the absence of a complaint.
        raise ValueError("allowed_behavior needs the criterion it satisfies")
    methods = data.get("methods_reported", [])
    if not isinstance(methods, list) or len(methods) > MAX_METHODS or any(
            not isinstance(path, str) or not METHOD_PATH.fullmatch(path) for path in methods):
        raise ValueError("methods_reported takes catalogue-relative SKILL.md or reference paths")
    revision = data.get("revision")
    if revision is not None and (not isinstance(revision, str) or not REVISION.fullmatch(revision)):
        raise ValueError("revision must be a commit or digest")
    excerpt = data.get("excerpt")
    if excerpt is not None and (mode != "content" or not isinstance(excerpt, str) or not excerpt.strip()):
        raise ValueError("an excerpt requires content capture consent")
    traces = references(data.get("trace_refs", []))
    now = clock()
    key = uuid.uuid4().hex
    entry = {"schema": SCHEMA, "id": key, "kind": kind, "created_at": now, "expires_at": now + RETENTION,
             "status": "candidate",
             "source": {"client": client, "event": "explicit_record", "scope": None, "session_id": session,
                        "delivery_id": None, "evidence_level": "caller_report_unattested"},
             "signal": "explicit", "capture_mode": mode, "assay_version": installed_version(root),
             "context": context(root, settings, methods=list(methods), revision=revision),
             "criterion": rule, "related": data.get("related"), "trace_refs": traces,
             "excerpt": excerpt[:MAX_EXCERPT] if excerpt else None,
             "excerpt_truncated": bool(excerpt) and len(excerpt) > MAX_EXCERPT,
             "annotations": [], "review": None, "reviews": [], "pending_notice": False}
    with store(directory, clock=clock).transaction() as tx:
        related = entry["related"]
        if related is not None and (not isinstance(related, str) or not tx.get(KIND, related)):
            raise ValueError("related must reference a retained record")
        if len(tx.values(KIND)) >= MAX_RECORDS:
            raise ValueError("feedback store full; inspect and delete records explicitly")
        tx.put(KIND, key, entry, entry["expires_at"])
    return entry


def view(record):
    """Read an older record without inventing evidence it never stored."""
    result = dict(record)
    result.setdefault("kind", "correction")  # v1 stored only correction-grammar candidates
    result.setdefault("context", {"assay_version": record.get("assay_version", "unknown"),
                                  "rules_fingerprint": "unknown", "methods_reported": "unknown",
                                  "method_identity": "unknown"})
    result.setdefault("criterion", None)
    result.setdefault("related", None)
    result.setdefault("trace_refs", [])
    # History starts with the last review that actually survived, not a reconstruction.
    result.setdefault("reviews", [record["review"]] if record.get("review") else [])
    return result


def read(directory, key=None, *, clock=time.time):
    with store(directory, clock=clock).transaction() as tx:
        if key is not None:
            record = tx.get(KIND, key)
            if record is None:
                raise ValueError("unknown or expired feedback candidate")
            return view(record)
        return sorted((view(item) for item in tx.values(KIND)), key=lambda item: (item["created_at"], item["id"]))


def annotate(directory, key, data, *, clock=time.time):
    if not isinstance(data, dict) or set(data) - {"category", "basis", "layer", "trace_refs", *TEXT_FIELDS}:
        raise ValueError("invalid annotation fields")
    if "layer" in data and data["layer"] not in LAYERS:
        raise ValueError("invalid cause-layer code")
    if "trace_refs" in data:
        references(data["trace_refs"])
    for field in TEXT_FIELDS:
        if field in data and (not isinstance(data[field], str) or len(data[field]) > 1500):
            raise ValueError("invalid annotation text")
    with store(directory, clock=clock).transaction() as tx:
        stored = tx.get(KIND, key)
        if stored is None:
            raise ValueError("unknown or expired feedback candidate")
        record = view(stored)
        if record["kind"] == "correction":
            if data.get("category") not in CATEGORIES or data.get("basis") not in BASES:
                raise ValueError("invalid annotation category or requirement basis")
        elif {"category", "basis", "layer"} & set(data):
            raise ValueError("an allowed example takes no correction category or cause layer")
        if record["capture_mode"] != "content" and set(data) & set(TEXT_FIELDS):
            raise ValueError("text annotations require content capture consent")
        if any(item["value"] == data for item in record["annotations"]):
            return record
        if len(record["annotations"]) >= MAX_ANNOTATIONS:
            raise ValueError("annotation history full")
        record["annotations"].append({"at": clock(), "provenance": "model_or_caller_interpretation", "value": data})
        record["schema"] = SCHEMA
        tx.put(KIND, key, record, record["expires_at"])
        return record


def review(directory, key, status, reason=None, *, reason_code=None, basis_ref=None, layer=None,
           duplicate_of=None, clock=time.time):
    if status not in REVIEW_STATES:
        raise ValueError("explicit review needs a known status")
    if reason is not None and (not isinstance(reason, str) or not 0 < len(reason.strip()) <= 1500):
        raise ValueError("review reason must be bounded text")
    if reason_code is not None and reason_code not in REVIEW_CODES[status]:
        raise ValueError("review code does not apply to this status")
    if layer is not None and layer not in LAYERS:
        raise ValueError("invalid cause-layer code")
    if basis_ref is not None:
        reference(basis_ref)
    if status == "confirmed" and basis_ref is None:
        raise ValueError("confirmation needs a reference to its basis")
    with store(directory, clock=clock).transaction() as tx:
        stored = tx.get(KIND, key)
        if stored is None:
            raise ValueError("unknown or expired feedback candidate")
        record = view(stored)
        if status == "duplicate":
            if duplicate_of == key or not isinstance(duplicate_of, str) or not tx.get(KIND, duplicate_of):
                raise ValueError("duplicate must reference another retained candidate")
        elif duplicate_of is not None:
            raise ValueError("duplicate reference requires duplicate status")
        if record["capture_mode"] != "content" and reason is not None:
            raise ValueError("free-text review needs content capture consent; use a review code")
        if status != "confirmed" and reason is None and reason_code is None:
            raise ValueError("review needs a reason code" + (" or reason" if record["capture_mode"] == "content" else ""))
        if len(record["reviews"]) >= MAX_REVIEWS:
            raise ValueError("review history full; export or delete the record explicitly")
        entry = {"at": clock(), "status": status, "reason": reason, "reason_code": reason_code,
                 "basis_ref": basis_ref, "layer": layer, "duplicate_of": duplicate_of,
                 "provenance": "explicit_local_review_unattested"}
        record["status"] = status
        record["review"] = entry
        record["reviews"].append(entry)
        record["schema"] = SCHEMA
        tx.put(KIND, key, record, record["expires_at"])
        return record


def delete(directory, key, *, clock=time.time):
    with store(directory, clock=clock).transaction() as tx:
        if tx.get(KIND, key) is None:
            raise ValueError("unknown or expired feedback candidate")
        tx.delete(KIND, key)
