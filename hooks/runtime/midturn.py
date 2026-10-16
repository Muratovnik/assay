"""Name a skill that a tool call shows the work needs and the Claude session has not loaded.

The skill check runs once per request, so a skill that the work calls for only
after the first tool call is easy to miss: a shell download of documentation
without `evidence-research`, an edit of a test file without `test-writing`.
Each row of ROWS pairs a skill with a sign that one tool call shows by itself.
On PreToolUse, when a row matches and neither the records nor the transcript
tail show the skill loaded, the agent gets one short note stating the fact and
the decision the skill governs in that call. The default form is that note. The
`deny` form refuses the first matching call with the same text; the retry
passes because the key is kept. It runs no model.

At most one note per skill, request and agent, kept as one hashed key like the
fetch note's. A write made through a shell command is not seen, and a skill
read through a shell command is not seen as loaded: the Skill tool and a
`Read` of its SKILL.md are what count, as in the skill gate.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
import time

from .skill_gate import _key as gate_key, _save as save_load, loaded as recorded, transcript

TTL = 86_400
MAX_RECORDS = 128
FORMS = ("note", "deny")
WRITES = frozenset({"Edit", "Write", "MultiEdit", "NotebookEdit"})
SHELLS = frozenset({"Bash", "PowerShell"})
WEB = frozenset({"WebFetch", "WebSearch"})
MAX_PATH = 4_096
MAX_COMMAND = 65_536


@dataclass(frozen=True)
class Row:
    rule: str  # The ID that disabled_rules turns off.
    skill: str
    action: str  # What the call does, completed by its evidence.
    decision: str  # What the skill governs in a call that shows the sign.


ROWS = (
    Row("midturn-evidence-research", "evidence-research", "fetches an external source",
        "which source is read, how much of it and what the conclusion may rest on"),
    Row("midturn-code-change", "code-change", "edits source code",
        "which responsibility and callers the change touches and what check shows it works"),
    Row("midturn-test-writing", "test-writing", "edits a test file",
        "what behavior the test pins and whether it fails without the fix"),
    Row("midturn-ui-delivery", "ui-delivery", "edits an interface file",
        "the states and actions the screen needs and how the result is judged"),
    Row("midturn-technical-writing", "technical-writing", "edits documentation",
        "who reads the document and what that reader needs to do with it"),
    Row("midturn-skill-evaluation", "skill-evaluation", "edits a skill file",
        "what evidence shows the change helps and not only that it reads well"),
)
RULES = tuple(row.rule for row in ROWS)

SEPARATOR = re.compile(r"[\\/]")
SOURCE = re.compile(r"\.(?:py|pyi|js|mjs|cjs|ts|mts|cts|go|rs|java|kt|cs|c|h|cc|cpp|hpp|rb|php|swift|sh|bash|ps1|psm1"
                    r"|lua|gd|sql)$", re.I)
INTERFACE = re.compile(r"\.(?:vue|svelte|[jt]sx|css|scss|sass|less|html?)$", re.I)
# Python, Go and JavaScript conventions: a test directory, test_*, *_test, *.test.*, *.spec.*.
TEST = re.compile(r"(?:^|[\\/])(?:tests?|__tests__|spec)[\\/]|(?:^|[\\/])(?:test_[^\\/]*|conftest\.py|[^\\/]*_tests?\.[^\\/.]+"
                  r"|[^\\/]*\.(?:test|spec)\.[^\\/.]+)$", re.I)
# Output of a tool or a package manager, not a file anyone maintains.
GENERATED = re.compile(r"(?:^|[\\/])(?:node_modules|dist|build|vendor|__pycache__|\.git|\.cache|\.venv|venv|\.next|coverage)[\\/]"
                       r"|\.min\.(?:js|css)$|\.d\.ts$|_pb2(?:_grpc)?\.py$|\.generated\.\w+$|\.g\.cs$", re.I)
# A scratch directory is no one's code, but a task worktree below tmp/worktrees holds a real checkout.
WORKTREE = re.compile(r"(?:^|[\\/])tmp[\\/]worktrees[\\/][^\\/]+(?=[\\/])", re.I)
SCRATCH = re.compile(r"(?:^|[\\/])(?:tmp|temp|scratchpad|\.private|\.tmp)[\\/]", re.I)
DOCUMENT = re.compile(r"\.(?:md|mdx|markdown|rst)$", re.I)
README = re.compile(r"(?:^|[\\/])README(?:\.[\w-]+)*\.(?:md|mdx|markdown|rst|txt)$", re.I)
DOCS = re.compile(r"(?:^|[\\/])docs[\\/]", re.I)
# Plans and research are working records, not documentation for a reader.
WORKING = re.compile(r"(?:^|[\\/])docs[\\/](?:[\w.-]+[\\/])*(?:plans?|research)[\\/]|[\\/]plans?[\\/][^\\/]+\.md$", re.I)
# Agent instructions, memory notes and generated change logs are other work.
NOT_DOCUMENTATION = re.compile(r"(?:^|[\\/])(?:CLAUDE|AGENTS|GEMINI|MEMORY|CHANGELOG|SKILL)\.md$|[\\/]memory[\\/][^\\/]+$", re.I)
SKILL_FILE = re.compile(r"(?:^|[\\/])SKILL\.md$|[\\/]skills?[\\/][a-z][a-z0-9-]*[\\/](?:references|evals)[\\/]|"
                        r"(?:^|[\\/])activation-rules\.toml$", re.I)
# A shell command that fetches: the verb must open a command, so a commit message that
# mentions curl does not count.
FETCH = re.compile(r"(?:^|[;&|(`\n]|\$\()\s*(?:(?:\w+=\S+\s+)|(?:\$[\w:.]+\s*=\s*))*(?:curl|wget|iwr|irm|invoke-webrequest|invoke-restmethod)"
                   r"(?:\.exe)?\b", re.I)
URL = re.compile(r"https?://(\[[0-9a-f:]+\]|[^\s/:<>()\"'`\[\]]+)", re.I)
LOCAL = re.compile(r"^(?:localhost|127\.\d+\.\d+\.\d+|0\.0\.0\.0|\[?::1\]?|[^.]*\.localhost|[^.]*\.test|"
                   r"host\.docker\.internal|example\.(?:com|org|net))$", re.I)
# A reachability probe throws the body away or asks for the headers only.
PROBE = re.compile(r"(?:^|\s)(?:-o|--output|-OutFile)\s+(?:/dev/null|nul|\$null)\b|\s>\s*(?:/dev/null|nul|\$null)\b"
                   r"|(?:^|\s)(?:-I|--head)\b|-X\s+HEAD\b|-Method\s+Head\b", re.I)


def classify(path):
    """The row a written file calls for, or None."""
    if not isinstance(path, str) or not path or len(path) > MAX_PATH or GENERATED.search(path):
        return None
    if SCRATCH.search(WORKTREE.sub("", path)):
        return None
    if SKILL_FILE.search(path):
        return "midturn-skill-evaluation"
    if NOT_DOCUMENTATION.search(path):
        return None
    if README.search(path) or (DOCUMENT.search(path) and DOCS.search(path) and not WORKING.search(path)):
        return "midturn-technical-writing"
    if INTERFACE.search(path):
        return None if TEST.search(path) else "midturn-ui-delivery"
    if SOURCE.search(path):
        return "midturn-test-writing" if TEST.search(path) else "midturn-code-change"
    return None


def external(command):
    """The host the first fetching command of a shell command line reaches, or None.

    The host is the first URL after the verb. A local address, a reachability probe and a
    fetch with no URL give None.
    """
    if not isinstance(command, str):
        return None
    command = command[:MAX_COMMAND]
    starts = [match.end() for match in FETCH.finditer(command)]
    for index, start in enumerate(starts):
        end = starts[index + 1] if index + 1 < len(starts) else len(command)
        part = command[start:end]
        found = URL.search(part)
        if found and not LOCAL.match(found[1]) and not PROBE.search(part):
            return found[1].lower()
    return None


def signs(tool, data):
    """(rule, evidence) pairs that one tool call shows; evidence is a file name or a host, never a full URL."""
    if not isinstance(data, dict):
        return []
    if tool in WRITES:
        path = data.get("notebook_path" if tool == "NotebookEdit" else "file_path")
        rule = classify(path)
        return [(rule, SEPARATOR.split(path)[-1])] if rule else []
    if tool in WEB:
        found = URL.match(data["url"]) if isinstance(data.get("url"), str) else None
        return [("midturn-evidence-research", found[1].lower() if found else "web search")]
    if tool in SHELLS:
        host = external(data.get("command"))
        return [("midturn-evidence-research", host)] if host else []
    return []


def text(row, evidence):
    """The note: facts about this call and the skill, ending with what the skill check expects."""
    return (f"Assay skill note: this call {row.action} ({evidence[:80]}). The assay:{row.skill} skill governs "
            f"{row.decision}; this session has not loaded it. The skill check expects it loaded (skill tool or "
            "its SKILL.md) and named in one short sentence.")


def _identity(event):
    session, agent = event.get("session_id"), event.get("agent_id")
    if not isinstance(session, str) or not session or len(session) > 200:
        return None
    if agent is not None and (not isinstance(agent, str) or not agent or len(agent) > 200):
        return None
    turn = event.get("prompt_id")
    # Without a prompt id the note appears once per agent, which still bounds it.
    return session, agent, turn if isinstance(turn, str) and len(turn) <= 200 else None


def _key(*parts):
    return hashlib.sha256(json.dumps(["skill-note", *parts]).encode()).hexdigest()


def _path(event):
    """The transcript of the calling agent: the subagent's own file, or the session's."""
    if event.get("agent_id") is None:
        return event.get("transcript_path")
    own = event.get("agent_transcript_path")
    if isinstance(own, str) and own:
        return own
    base, session = event.get("transcript_path"), event.get("session_id")
    if isinstance(base, str) and base and isinstance(session, str):
        return str(Path(base).parent / session / "subagents" / f"agent-{event['agent_id']}.jsonl")
    return None


def _shown_loaded(event, skill, names, directory, clock):
    """Whether this agent has loaded the skill: the gate's records, else the transcript tail.

    Records miss a compaction's re-attached skills and the loads of a continued, resumed or
    forked session. What the transcript shows is added to the records, so the next call
    does not read it again.
    """
    if skill in recorded(event, "claude", names, directory, clock=clock):
        return True
    scan = transcript(_path(event), names, subagent=event.get("agent_id") is not None)
    if not scan or not scan[1]:
        return False
    key = gate_key(event)
    if key is not None:
        try:
            from route_evidence.pipeline_store import PipelineStore
            with PipelineStore(Path(directory) / "skill-gate", clock=clock).transaction() as tx:
                current = (tx.get("loads", key) or {"skills": []})["skills"]
                save_load(tx, key, [*current, *[found for found in sorted(scan[1]) if found not in current]], clock)
        except Exception:
            pass  # The records are a cache of the transcript, never a condition.
    return skill in scan[1]


def checked(event, rules, names, directory, *, form="note", clock=time.time):
    """The note, or under the deny form the refusal, for the first sign this call shows; else {}.

    Rules are the enabled row IDs and names the enabled skills. A skill is named at most once
    per request and agent: the key is stored whichever form answers, so a refused call passes
    on its retry.
    """
    if event.get("hook_event_name") != "PreToolUse" or not directory or not isinstance(event.get("tool_name"), str):
        return {}
    identity = _identity(event)
    if identity is None:
        return {}
    hits = [(row, evidence) for rule, evidence in signs(event["tool_name"], event.get("tool_input"))
            for row in ROWS if row.rule == rule and rule in rules and row.skill in names]
    if not hits:
        return {}
    from route_evidence.pipeline_store import PipelineStore
    for row, evidence in hits:
        key = _key(*identity, row.skill)
        with PipelineStore(Path(directory) / "skill-note", clock=clock).transaction() as tx:
            if tx.get("note", key):
                continue
        if _shown_loaded(event, row.skill, names, directory, clock):
            continue
        with PipelineStore(Path(directory) / "skill-note", clock=clock).transaction() as tx:
            # A parallel call of the same request may have been named while the transcript was read.
            if tx.get("note", key):
                continue
            records = tx.values("note")
            if len(records) >= MAX_RECORDS:
                tx.delete("note", min(records, key=lambda item: item["at"])["id"])
            now = clock()
            tx.put("note", key, {"id": key, "at": now}, now + TTL)
        message = text(row, evidence)
        if form == "deny":
            return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                    "permissionDecisionReason": "Assay: " + message + " This call was not run; the same call passes "
                    "when repeated."}}
        return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "additionalContext": message}}
    return {}
