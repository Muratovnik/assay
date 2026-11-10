"""Point a Claude agent at the text behind a fetched summary, at what a search only found and at a contradicted full-read claim.

Three notes, none a block, all stated as facts:

- After a WebFetch, once per request and agent: the result is an answer a
  model wrote about the page, not the page's text.
- After a WebSearch, once per request and agent: the results are found, not
  read, and a request to include them is met by the ones the conclusion rests on.
- On Stop or SubagentStop, once: a line of the turn that says a file or URL was
  read in full, when the transcript shows the file the claim's own clause names
  read only in part, or short of the line range the claim states for it, or that
  URL opened only through WebFetch.

The claim check fires only on positive evidence. A file the transcript shows no
Read of, for example one printed with a shell command, leaves it silent, and so
does a URL that a shell command also names. It reads the transcript tail the
skill gate reads and stores nothing; the fetch and search notes each store one
hashed key per request and agent.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import time

from .skill_gate import HANDBACK, _lines, _prompt

TTL = 86_400
MAX_RECORDS = 128
MAX_CLAIMS = 3
MAX_LINE = 2_000
FETCH = "WebFetch"
SEARCH = "WebSearch"
SHELLS = frozenset({"Bash", "PowerShell"})
# A line claiming a whole source was read; the reference must sit on the same line.
CLAIM = re.compile(r"целиком|полностью|in full\b|in its entirety|entire(?:ly)?\b|end to end|cover to cover"
                   r"|from start to finish|whole (?:file|page|paper|article|document|text|source)", re.I)
NUMBERED = re.compile(r"^\s*(\d+)\t", re.M)
# The parts of a claim line that say which file it is about; see _clauses.
SENTENCE = re.compile(r"[;|]|[.!?](?=\s)")
ASIDE = re.compile(r"\([^()\n]*\)")
QUOTED = re.compile(r'"[^"\n]*"|«[^»\n]*»|“[^”\n]*”')
TOKEN = re.compile(r"[^\s`'\"*()\[\]<>,;|«»“”]+")
LINE_SUFFIX = re.compile(r"(?::\d[\d\-–—]*|#L\d[\w\-–—]*)?[.:]*$")
ATTACHED = re.compile(r"(?::|#L)(\d+)(?:[-–—]L?(\d+))?")
WORDED = re.compile(r"\b(?:lines?|строк[аи]?)\s+(\d+)(?:\s*[-–—]\s*(\d+))?|\((\d+)\s*[-–—]\s*(\d+)\)", re.I)

FETCH_NOTE = ("Assay source check: a WebFetch result is a model's answer to the fetch prompt about the page, "
              "not the page's text. Its quotes are short and paraphrased, and a blocked or challenge page can "
              "come back as a summary of that page. A conclusion that rests on the fetch summary is stated "
              "as resting on it. Retrieve the page's text with a shell download, and read it at the part the "
              "conclusion depends on, when that conclusion depends on exact wording, a number, a table or code "
              "the summary may have distorted or dropped, or when the page is long; a narrow fact the summary "
              "quotes from an authoritative page needs only the label. This note appears once per request.")
SEARCH_NOTE = ("Assay source check: search results are found, not read. A request to include search sources is met "
               "by the ones the conclusion rests on, each labelled with how it was read; the other results take at "
               "most one line with their count and kind, and an unopened result is named only if it could change "
               "the conclusion, with why it stayed unopened and what that leaves uncertain.")


def _key(*parts):
    return hashlib.sha256(json.dumps(["source-check", *parts]).encode()).hexdigest()


def _identity(event):
    session, agent = event.get("session_id"), event.get("agent_id")
    if not isinstance(session, str) or not session or len(session) > 200:
        return None
    if agent is not None and (not isinstance(agent, str) or not agent or len(agent) > 200):
        return None
    turn = event.get("prompt_id")
    # Without a prompt id the note appears once per agent, which still bounds it.
    return session, agent, turn if isinstance(turn, str) and len(turn) <= 200 else None


def _once(event, directory, kind, note, clock):
    """The note on the first result of its kind for this request and agent, else {}."""
    identity = _identity(event) if directory else None
    if identity is None:
        return {}
    from route_evidence.pipeline_store import PipelineStore
    key = _key(*identity)
    with PipelineStore(Path(directory) / "source-check", clock=clock).transaction() as tx:
        if tx.get(kind, key):
            return {}
        records = tx.values(kind)
        if len(records) >= MAX_RECORDS:
            tx.delete(kind, min(records, key=lambda item: item["at"])["id"])
        now = clock()
        tx.put(kind, key, {"id": key, "at": now}, now + TTL)
    return {"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": note}}


def fetched(event, directory, *, clock=time.time):
    """The fetch note for this request and agent on its first WebFetch result, else {}."""
    return _once(event, directory, "fetch-note", FETCH_NOTE, clock) if event.get("tool_name") == FETCH else {}


def searched(event, directory, *, clock=time.time):
    """The search note for this request and agent on its first WebSearch result, else {}."""
    return _once(event, directory, "search-note", SEARCH_NOTE, clock) if event.get("tool_name") == SEARCH else {}


def _range(data, result, text):
    """(first, last, total, ranged) lines one Read returned; total is None when the transcript omits it."""
    ranged = isinstance(data, dict) and (data.get("offset") is not None or data.get("limit") is not None)
    file = result.get("file") if isinstance(result, dict) else None
    if isinstance(file, dict) and all(isinstance(file.get(k), int) for k in ("startLine", "numLines", "totalLines")):
        return file["startLine"], file["startLine"] + file["numLines"] - 1, file["totalLines"], ranged
    numbers = [int(n) for n in NUMBERED.findall(text or "")]
    if not numbers:
        return None
    limit = data.get("limit") if isinstance(data, dict) else None
    # A ranged read that came back shorter than its limit reached the end.
    total = numbers[-1] if isinstance(limit, int) and len(numbers) < limit else None
    return numbers[0], numbers[-1], total, ranged


def _covered(reads):
    """Whether one file's reads demonstrably cover it from the first line to the last."""
    if any(not ranged and (total is None or last >= total) for _, last, total, ranged in reads):
        return True
    totals = [total for *_, total, _ in reads if total is not None]
    if not totals:
        return False
    reached = 0
    for first, last, *_ in sorted(reads):
        if first > reached + 1:
            return False
        reached = max(reached, last)
    return reached >= max(totals)


def _text(content):
    if isinstance(content, str):
        return content
    return "\n".join(part.get("text", "") for part in content or [] if isinstance(part, dict))


def ledger(path, *, subagent=False, needed=False):
    """(claims, reads, fetched, shell) from a transcript's tail, or None when it cannot be read.

    Claims: lines of this turn's messages that say something was read in full.
    Reads map a file path to the line ranges its Reads returned, and fetched
    holds WebFetch URLs, both since the latest compaction; shell holds the
    shell commands of the same span. Without a claim in the turn, and unless
    needed says the final message holds one, the scan stops at the turn's start.
    """
    if not isinstance(path, str) or not path or len(path) > 4_096:
        return None
    claims, reads, fetched_urls, shell, results, in_turn = [], {}, set(), [], {}, True
    try:
        for raw in _lines(path):
            try:
                entry = json.loads(raw) if raw.strip() else None
            except ValueError:
                continue
            if not isinstance(entry, dict) or (entry.get("isSidechain") and not subagent):
                continue
            kind = entry.get("type")
            if kind == "system" and entry.get("subtype") == "compact_boundary":
                break
            message = entry.get("message")
            content = message.get("content") if isinstance(message, dict) else None
            if kind == "user":
                if in_turn and _prompt(entry, content):
                    in_turn = False
                    if not claims and not needed:
                        break  # Nothing to check: earlier reads would go unused.
                for block in content if isinstance(content, list) else []:
                    if isinstance(block, dict) and block.get("type") == "tool_result":
                        results[block.get("tool_use_id")] = (entry.get("toolUseResult"), _text(block.get("content")))
                continue
            if kind != "assistant" or not isinstance(content, list):
                continue
            for block in content:
                if not isinstance(block, dict):
                    continue
                data = block.get("input")
                if block.get("type") == "text" and in_turn:
                    claims += [line for line in block.get("text", "").splitlines() if CLAIM.search(line[:MAX_LINE])]
                elif block.get("type") != "tool_use" or not isinstance(data, dict):
                    continue
                elif block.get("name") == HANDBACK and in_turn and isinstance(data.get("message"), str):
                    claims += [line for line in data["message"].splitlines() if CLAIM.search(line[:MAX_LINE])]
                elif block.get("name") == "Read" and isinstance(data.get("file_path"), str):
                    span = _range(data, *results.get(block.get("id"), (None, None)))
                    if span:
                        reads.setdefault(data["file_path"], []).append(span)
                elif block.get("name") == FETCH and isinstance(data.get("url"), str):
                    fetched_urls.add(data["url"])
                elif block.get("name") in SHELLS and isinstance(data.get("command"), str):
                    shell.append(data["command"])
    except (OSError, ValueError):
        return None
    return claims, reads, fetched_urls, shell


def _handle(url):
    """The most specific part of a URL a sentence or a command would repeat."""
    bare = re.sub(r"^https?://(www\.)?", "", url).rstrip("/")
    tail = bare.rsplit("/", 1)[-1]
    return tail if len(tail) >= 6 and "/" in bare else bare


def _span(reads):
    parts = sorted({f"{first}-{last}" for first, last, *_ in reads})
    totals = {total for *_, total, _ in reads if total is not None}
    return "lines " + ", ".join(parts[:4]) + (f" of {max(totals)}" if totals else "")


def _blank(pattern, text):
    """The text with each match of the pattern replaced by spaces, so positions stay where they were."""
    return pattern.sub(lambda match: " " * len(match[0]), text)


def _clauses(line):
    """(texts whose files a claim word names, in order of preference, the clause) for each claim on a line.

    A line splits into sentences at `;`, `|` and a sentence end, and a sentence
    into clauses at its commas, except that a colon after the claim word keeps
    the rest of the sentence, a list, with the claim. A file named inside a
    parenthesis belongs to it alone; a claim inside one names the parenthesis's
    files, or the clause's when it names none. A claim word inside quotation
    marks quotes something and claims nothing. Every text has the clause's length.
    """
    for sentence in SENTENCE.split(line):
        outer, bounds, start = _blank(ASIDE, sentence), [], 0
        for comma in [match.start() for match in re.finditer(",", outer)] + [len(outer)]:
            if comma < start:
                continue
            claim = _claim(outer[start:comma])
            if claim and ":" in outer[start + claim.end():comma]:
                comma = len(outer)
            bounds.append((start, comma))
            start = comma + 1
        for first, last in bounds:
            part, whole = outer[first:last], sentence[first:last]
            if _claim(part):
                yield [part], whole
            for aside in ASIDE.finditer(whole):
                if _claim(aside[0]):
                    yield [" " * aside.start() + aside[0] + " " * (len(whole) - aside.end()), part], whole


def _claim(text):
    return CLAIM.search(_blank(QUOTED, text))


def _named(text, paths):
    """(start, end of the name, matched read paths) of each file reference in a text.

    A path, or its tail from a directory on, names the read files it ends;
    only without one does a bare file name of four or more characters name every
    read file of that name. A `:12-40` or `#L12` after the name is left outside it.
    """
    found = []
    for match in TOKEN.finditer(text):
        cut = LINE_SUFFIX.search(match[0]).start()
        token = match[0][:cut].removeprefix("./")
        strong = [path for path, plain in paths.items()
                  if "/" in token and (plain == token or plain.endswith("/" + token.lstrip("/")))]
        weak = [path for path, plain in paths.items() if len(token) >= 4 and plain.rsplit("/", 1)[-1] == token]
        if strong or weak:
            found.append((match.start(), match.start() + cut, strong or weak))
    return found


def _wanted(text):
    """The line range stated right after a file name, as (first, last), or None for the whole file."""
    match = ATTACHED.match(text)
    if match:
        return int(match[1]), int(match[2] or match[1])
    match = WORDED.search(text)
    if not match:
        return None
    first = int(match[1] or match[3])
    return first, int(match[2] or match[4] or first)


def _covers(reads, wanted):
    """Whether one file's reads cover the stated range, or the whole file when none is stated."""
    if wanted is None:
        return _covered(reads)
    if any(not ranged and (total is None or last >= total) for _, last, total, ranged in reads):
        return True
    reached = wanted[0] - 1
    for first, last, *_ in sorted(reads):
        if first > reached + 1:
            break
        reached = max(reached, last)
    return reached >= wanted[1]


def _claimed(line, reads):
    """(name, reads) of each file a claim on this line names and the transcript shows read short of what it names."""
    paths = {path: path.replace("\\", "/") for path in reads}
    found = []
    for texts, whole in _clauses(line.replace("\\", "/")):
        references = next((named for named in (_named(text, paths) for text in texts) if named), [])
        starts = sorted(start for start, _, _ in _named(whole, paths))
        for start, stop, candidates in references:
            # A range belongs to the reference it follows, up to the next reference of the clause.
            end = next((other for other in starts if other > start), len(whole))
            wanted = _wanted(whole[stop:end])
            if not any(_covers(reads[path], wanted) for path in candidates):
                found += [(re.split(r"[\\/]", path)[-1], reads[path]) for path in candidates]
    return found


def contradicted(claims, reads, fetched_urls, shell):
    """Each claimed source the transcript shows read only in part or only through WebFetch.

    A claim names the files its own clause names (see _clauses). A bare file name
    stands for every read file of that name, and a path or its tail for the
    files it ends; the claim holds when one of them was read in full, or read
    over the line range the claim states right after the name.
    """
    found = []
    for line in claims:
        for name, spans in _claimed(line[:MAX_LINE], reads):
            found.append(f"{name}: only {_span(spans)} were read")
        for url in fetched_urls:
            handle = _handle(url)
            if (url in line or handle in line) and not any(handle in command for command in shell):
                found.append(f"{url}: opened only through WebFetch, whose result is a model's summary")
    return list(dict.fromkeys(found))[:MAX_CLAIMS]


def stopped(event):
    """Continuation feedback on Stop or SubagentStop when a full-read claim is contradicted, else {}."""
    name = event.get("hook_event_name")
    if name not in {"Stop", "SubagentStop"} or event.get("stop_hook_active"):
        return {}
    if name == "SubagentStop" and not event.get("agent_id"):
        return {}
    last = event.get("last_assistant_message")
    final = ([line for line in last[:65_536].splitlines() if CLAIM.search(line[:MAX_LINE])]
             if isinstance(last, str) else [])
    path = event.get("agent_transcript_path") if name == "SubagentStop" else event.get("transcript_path")
    scan = ledger(path, subagent=name == "SubagentStop", needed=bool(final))
    if not scan:
        return {}
    claims, reads, fetched_urls, shell = scan
    claims += final
    reasons = contradicted(claims, reads, fetched_urls, shell)
    if not reasons:
        return {}
    return {"hookSpecificOutput": {"hookEventName": name, "additionalContext": (
        "Assay source check: this turn says a source was read in full, and the transcript shows otherwise: "
        + "; ".join(reasons) + ". The answer already given stands: one short line is enough to say what was "
        "actually read when nothing changes, otherwise only the corrections that would change the user's "
        "conclusions, without repeating the answer.")}}
