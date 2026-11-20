"""What the route table cost and how its delegated work fared in review, from Claude Code transcripts.

Read-only: it reads subagent transcripts and their meta files under a Claude Code
projects directory, makes no network request and writes nothing. The transcript
layout is what Claude Code 2.1.31x was observed to write, not a documented API,
so every field is read defensively and a line that is not a JSON object is
skipped and counted.

A launch is one subagent transcript whose first timestamp falls in the window.
Its class is the first word of its meta `description`, read exactly as the launch
check reads it. A review is a launch of a review class, or any launch whose report
carries a review line; verdict counts are therefore counts of reviews, not of
pieces of work. Only verdict lines are parsed, by the word they open with in the
contract's vocabulary or independent-audit's: prose is never interpreted. A
review's subject is the launch its REVIEWED line names, or else the one launch that reported, as its own, a commit the review names; a commit
id is matched as a token, not read for meaning.
"""
from __future__ import annotations

import json
import math
import re
import statistics
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .core import EvidenceError, read_document
from .route_table import CLASS_NAME, LABEL

CONTRACT_VERDICTS = ("ship", "fix-first", "rethink", "inconclusive")
# independent-audit's FAIL blocks acceptance but leaves the choice between fix-first
# and rethink to the reviewer, so a review that names neither is a rejection of its own.
FAIL = "fail"
VERDICTS = (*CONTRACT_VERDICTS, FAIL)
REWORK = frozenset({"fix-first", "rethink", FAIL})
NO_VERDICT = "no_verdict_line"
UNRECOGNIZED = "unrecognized_verdict"
# The words a verdict line may open with, in the contract's vocabulary and in the
# audit's, as independent-audit's bounded review maps them to the contract.
VERDICT_WORDS = {"ship": "ship", "fix-first": "fix-first", "rethink": "rethink", "inconclusive": "inconclusive",
                 "pass": "ship", "pass with non-blocking findings": "ship", "fail": FAIL}
TOKEN_KINDS = ("input", "output", "cache_read", "cache_write_5m", "cache_write_1h")
PRICE_KEYS = frozenset({"input", "output", "cache_read", "cache_write_5m_multiplier", "cache_write_1h_multiplier"})
HANDBACK = "SubagentHandback"
ADVISOR_ITERATION = "advisor_message"

_EMPHASIS = r"[*_]*"


def _review_line(keyword: str) -> re.Pattern:
    # The keyword opens its own line; markdown emphasis may wrap the keyword, the
    # colon or the value, so `**VERDICT:** ship` and `VERDICT: **ship**` both parse.
    return re.compile(rf"^\s*{_EMPHASIS}\s*{keyword}\s*{_EMPHASIS}\s*:\s*{_EMPHASIS}\s*(.*?)\s*{_EMPHASIS}\s*$",
                      re.IGNORECASE)


VERDICT_LINE = _review_line("verdict")
# A Markdown heading, numbered or not, may carry the verdict line, or say only
# `Verdict` and leave the value to the line after it.
HEADING = re.compile(r"^\s*#{1,6}\s+(?:\d+[.)]\s*)?")
VERDICT_ALONE = re.compile(rf"^{_EMPHASIS}\s*verdict\s*{_EMPHASIS}\s*$", re.IGNORECASE)
# The value's opening word is the verdict when the value ends there or Markdown or
# punctuation closes the word; a word that runs on into the sentence is not read.
VERDICT_WORD = re.compile(r"(pass\s+with\s+non-blocking\s+findings|fix-first|rethink|inconclusive|ship|pass|fail)"
                          r"(?=[*_]*\s*$|[*_]*\s*[.,;:(—–]|[*_]+\s)", re.IGNORECASE)
REVIEWED_LINE = _review_line("reviewed")
FOLLOWS_LINE = _review_line("follows")
NAME_TOKEN = re.compile(r"[\s:]*([^\s,:;]+)")
# The name runs to the dash, set off by spaces, that opens the label's purpose.
NAME_BEFORE_DASH = re.compile(r"[\s:]*([^\s,:;—–-][^,:;—–]*?)\s+[—–-]\s")
# A Git commit id as reports write it: 7 to 40 lowercase hex digits standing alone. A
# hyphen or underscore beside it makes it part of a UUID, a branch or a file name.
COMMIT_ID = re.compile(r"(?<![0-9A-Za-z_-])[0-9a-f]{7,40}(?![0-9A-Za-z_-])")

UNITS = {
    "client": "Claude Code subagent transcripts only; their layout is observed, not a documented API",
    "launch": "one subagent transcript whose first timestamp is inside the window",
    "reviews": "verdict counts are reviews, not pieces of work: each report a launch handed back that carries "
               "a contract verdict, a REVIEWED or a FOLLOWS line, and at least one per launch of a review class",
    "verdicts": "ship accepts the work; fix-first, rethink and fail reject it, fail being an audit FAIL that "
                "named neither; inconclusive, no_verdict_line and unrecognized_verdict decide nothing. The audit's "
                "PASS and PASS WITH NON-BLOCKING FINDINGS count as ship, its INCONCLUSIVE as inconclusive",
    "tokens": "the child's own requests, deduplicated by message id; advisor calls and tokens are counted "
              "separately",
    "cache_write_5m": "includes cache writes the transcript did not split by lifetime",
    "minutes": "wall-clock time between the first and last transcript timestamps; a resumed launch includes "
               "the wait between its rounds",
}
COST_BASIS = ("API list-price equivalent computed from the supplied prices file; not subscription quota; "
              "tiered or long-context prices are not modelled")


@dataclass
class Launch:
    path: Path
    session: Path
    start: datetime
    end: datetime
    malformed: int = 0
    tool_calls: int = 0
    own: Counter = field(default_factory=Counter)
    advisor: Counter = field(default_factory=Counter)
    advisor_calls: int = 0
    by_model: dict = field(default_factory=lambda: defaultdict(Counter))
    # Each report the child handed back, oldest first: a resumed child hands back once a round.
    reports: list = field(default_factory=list)
    # Each request it answered, oldest first: the launch prompt, then the coordinator's messages.
    requests: list = field(default_factory=list)
    has_meta: bool = False
    model: str | None = None
    effort: str | None = None
    cls: str | None = None
    name: str | None = None


@dataclass(eq=False)  # two rounds with equal lines and time are still two reviews
class Review:
    """One report read as a review; a reused reviewer gives one per round."""
    launch: Launch
    at: datetime
    lines: dict
    subjects: list = field(default_factory=list)
    follows: "Review | None" = None
    # Commit ids named in this report and in the requests the launch had received by then.
    commits: set = field(default_factory=set)

    @property
    def name(self) -> str | None:
        return self.launch.name

    @property
    def verdict(self) -> str:
        return self.lines["verdict"]


def parse_time(value: str, option: str) -> datetime:
    """An ISO timestamp as aware UTC; a value without an offset is UTC."""
    try:
        moment = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except (AttributeError, ValueError):
        raise EvidenceError(f"{option} must be an ISO timestamp, such as 2026-11-04T16:00") from None
    return moment.replace(tzinfo=timezone.utc) if moment.tzinfo is None else moment.astimezone(timezone.utc)


def _timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        moment = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return moment.replace(tzinfo=timezone.utc) if moment.tzinfo is None else moment.astimezone(timezone.utc)


def _count(value: Any) -> int:
    return value if type(value) is int and value >= 0 else 0


def usage_tokens(usage: dict) -> Counter:
    """Token kinds of one request. Writes without a lifetime split count as 5-minute writes."""
    split = usage.get("cache_creation")
    if isinstance(split, dict) and ("ephemeral_5m_input_tokens" in split or "ephemeral_1h_input_tokens" in split):
        write_5m = _count(split.get("ephemeral_5m_input_tokens"))
        write_1h = _count(split.get("ephemeral_1h_input_tokens"))
    else:
        write_5m, write_1h = _count(usage.get("cache_creation_input_tokens")), 0
    return Counter({"input": _count(usage.get("input_tokens")), "output": _count(usage.get("output_tokens")),
                    "cache_read": _count(usage.get("cache_read_input_tokens")),
                    "cache_write_5m": write_5m, "cache_write_1h": write_1h})


def _text(content: Any) -> str:
    if not isinstance(content, list):
        return ""
    return "\n".join(block["text"] for block in content
                     if isinstance(block, dict) and block.get("type") == "text" and isinstance(block.get("text"), str))


def _request(entry: dict, content: Any) -> str:
    """The text of a request the child answered: its launch prompt or a message the
    coordinator sent it; a reminder, a compaction summary or a tool result is none."""
    origin = entry.get("origin")
    if entry.get("isCompactSummary") is True or (
            entry.get("isMeta") is True and not (isinstance(origin, dict) and origin.get("kind") == "coordinator")):
        return ""
    if isinstance(content, str):
        return content
    if any(isinstance(block, dict) and block.get("type") == "tool_result" for block in content or ()):
        return ""
    return _text(content)


def commits(text: str) -> set[str]:
    """Commit ids in a text, each in its longest spelling there. A run of digits alone is a
    number and a run of letters alone a word, so an id needs both."""
    found = sorted({token for token in COMMIT_ID.findall(text)
                    if not token.isdigit() and any(c.isdigit() for c in token)}, key=len, reverse=True)
    kept: list[str] = []
    for token in found:
        if not any(longer.startswith(token) for longer in kept):
            kept.append(token)
    return set(kept)


def same_commit(a: str, b: str) -> bool:
    """Two spellings of one commit: the shorter abbreviates the longer."""
    return a.startswith(b) or b.startswith(a)


def read_transcript(path: Path, since: datetime, until: datetime | None) -> Launch | None:
    """The launch a transcript records, or None when it did not start inside the window."""
    launch = None
    messages: dict[str, tuple[Any, dict]] = {}
    texts: dict[str, list[str]] = {}
    order: list[str] = []
    tools: set[str] = set()
    handbacks: dict[Any, list] = {}
    refused: set[str] = set()
    malformed = 0
    with path.open(encoding="utf-8", errors="replace") as stream:
        for line in stream:
            if not line.strip():
                continue
            try:
                entry = json.loads(line)
            except ValueError:
                entry = None
            if not isinstance(entry, dict):
                malformed += 1
                continue
            moment = _timestamp(entry.get("timestamp"))
            if launch is None:
                if moment is None:
                    continue
                if moment < since or (until is not None and moment >= until):
                    return None
                launch = Launch(path=path, session=path.parent.parent, start=moment, end=moment)
            elif moment is not None:
                launch.end = max(launch.end, moment)
            message = entry.get("message")
            if not isinstance(message, dict):
                continue
            content = message.get("content")
            if entry.get("type") == "user":
                # A tool result marked as an error means the call did not go through.
                refused.update(block["tool_use_id"] for block in (content if isinstance(content, list) else ())
                               if isinstance(block, dict) and block.get("type") == "tool_result"
                               and block.get("is_error") is True and isinstance(block.get("tool_use_id"), str))
                if request := _request(entry, content):
                    launch.requests.append((moment or launch.end, request))
            if entry.get("type") != "assistant":
                continue
            for block in content if isinstance(content, list) else ():
                if not isinstance(block, dict) or block.get("type") != "tool_use":
                    continue
                if isinstance(block.get("id"), str):
                    tools.add(block["id"])
                supplied = block.get("input")
                if block.get("name") == HANDBACK and isinstance(supplied, dict) and isinstance(supplied.get("message"), str):
                    # A call repeated on a later line of its message is the same hand-back.
                    key = block["id"] if isinstance(block.get("id"), str) else len(handbacks)
                    handbacks.setdefault(key, [moment or launch.end, ""])[1] = supplied["message"]
            ident = message.get("id")
            if not isinstance(ident, str):
                continue
            # One message is written on several lines; the last line's usage stands.
            if isinstance(message.get("usage"), dict):
                messages[ident] = (message.get("model"), message["usage"])
            text = _text(content)
            if text.strip():
                if ident not in texts:
                    order.append(ident)
                texts.setdefault(ident, []).append(text)
    if launch is None:
        return None
    launch.malformed = malformed
    launch.tool_calls = len(tools)
    for model, usage in messages.values():
        iterations = usage.get("iterations")
        requests = ([item for item in iterations if isinstance(item, dict)]
                    if isinstance(iterations, list) and iterations else [usage])
        for request in requests:
            tokens = usage_tokens(request)
            name = request.get("model") if isinstance(request.get("model"), str) else model
            role = "advisor" if request is not usage and request.get("type") == ADVISOR_ITERATION else "own"
            if role == "advisor":
                launch.advisor_calls += 1
                launch.advisor.update(tokens)
            else:
                launch.own.update(tokens)
            launch.by_model[(role, name if isinstance(name, str) else None)].update(tokens)
    # A hand-back the client refused, for example one a hook held for a recheck, did not
    # reach the caller; it stands only when the child sent no other.
    sent = [key for key in handbacks if key not in refused] or list(handbacks)[-1:]
    launch.reports = sorted(((at, report) for at, report in (handbacks[key] for key in sent)),
                            key=lambda item: item[0])
    if not launch.reports and order:
        launch.reports = [(launch.end, "\n".join(texts[order[-1]]))]
    return launch


def child_name(description: str, has_class: bool) -> str | None:
    """The child's name: the words after the class, or from the start without one,
    up to the dash that opens the purpose; without that dash, the first word."""
    rest = description
    if has_class:
        match = LABEL.match(description)
        rest = description[match.end():] if match else description
    token = NAME_BEFORE_DASH.match(rest) or NAME_TOKEN.match(rest)
    if not token:
        return None
    name = token[1].strip("`*_.,;:-–— ")
    return name if any(c.isalnum() for c in name) else None


def _classify(description: str, classes: list[str] | None) -> str | None:
    match = LABEL.match(description) if description else None
    name = match[1] if match else None
    if classes is not None and name not in classes:
        return None
    return name


def read_meta(launch: Launch, classes: list[str] | None) -> None:
    path = launch.path.with_name(launch.path.stem + ".meta.json")
    meta: Any = None
    try:
        meta = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError):
        meta = None
    if not isinstance(meta, dict):
        return
    launch.has_meta = True
    description = meta.get("description") if isinstance(meta.get("description"), str) else ""
    launch.model = meta.get("model") if isinstance(meta.get("model"), str) else None
    launch.effort = meta.get("effort") if isinstance(meta.get("effort"), str) else None
    launch.cls = _classify(description, classes)
    launch.name = child_name(description, launch.cls is not None)


def _verdict_word(value: str) -> str | None:
    """The verdict a value opens with, or None when it opens with any other word."""
    match = VERDICT_WORD.match(value.strip().lstrip("*_ "))
    return VERDICT_WORDS[" ".join(match[1].lower().split())] if match else None


def _verdict_line(line: str) -> str | None:
    """A verdict line's value, the line set as a heading or not; None for any other line."""
    heading = HEADING.match(line)
    match = VERDICT_LINE.match(line[heading.end():] if heading else line)
    return match[1].strip() if match else None


def review_lines(text: str) -> dict:
    """The verdict contract's lines in a report; nothing else in it is read."""
    verdicts, contract, reviewed, follows = [], set(), [], []
    lines = text.splitlines()
    for number, line in enumerate(lines):
        if (value := _verdict_line(line)) is not None:
            verdicts.append(_verdict_word(value))
            if value.lower() in CONTRACT_VERDICTS:
                contract.add(value.lower())
        elif (heading := HEADING.match(line)) and VERDICT_ALONE.match(line[heading.end():]):
            following = next((later for later in lines[number + 1:] if later.strip()), "")
            if _verdict_line(following) is None and (word := _verdict_word(following)) is not None:
                verdicts.append(word)
        elif match := REVIEWED_LINE.match(line):
            for name in match[1].split(","):
                name = name.strip().strip("`*_ ")
                if name and name not in reviewed:
                    reviewed.append(name)
        elif match := FOLLOWS_LINE.match(line):
            name = match[1].strip().strip("`*_ ")
            if name:
                follows.append(name)
    # A line that opens with another word is prose beside the verdict and decides
    # nothing; two lines that read different verdicts leave the review unread. FAIL
    # beside the fix-first or rethink that says which rejection it is reads as that one.
    read = {word for word in verdicts if word is not None}
    named = read - {FAIL}
    if FAIL in read and len(named) == 1 and named <= REWORK:
        read = named
    if not verdicts:
        verdict = NO_VERDICT
    elif len(read) == 1:
        verdict = read.pop()
    else:
        verdict = UNRECOGNIZED
    return {"verdict": verdict, "reviewed": reviewed, "follows": follows[-1] if follows else None,
            # Only the contract's own line, with exactly one of its four words, marks a
            # review: a `Verdict:` line in other words also closes reports that judge no work.
            "marks_review": bool(len(contract) == 1 or reviewed or follows)}


def _named(candidates: list[Launch], name: str, review: Review) -> Launch | None:
    """The latest launch of this name that started no later than the review, else the latest one."""
    found = [launch for launch in candidates
             if launch is not review.launch and launch.name and launch.name.casefold() == name.casefold()]
    if not found:
        return None
    earlier = [launch for launch in found if launch.start <= review.at]
    return max(earlier or found, key=lambda launch: launch.start)


def _followed(reviews: list[Review], name: str, review: Review) -> Review | None:
    """The latest earlier review by this name; a reused reviewer follows its own earlier round."""
    position = reviews.index(review)
    for earlier in reversed(reviews[:position]):
        if earlier.name and earlier.name.casefold() == name.casefold():
            return earlier
    return None


def _reviews_of(launch: Launch, is_review_class: bool) -> list[Review]:
    """The launch's reports that are reviews, oldest first."""
    parsed = [Review(launch, at, review_lines(report), commits=commits("\n".join([report, *_asked(launch, at)])))
              for at, report in launch.reports]
    found = [review for review in parsed
             if review.lines["marks_review"] or (is_review_class and review.verdict != NO_VERDICT)]
    if is_review_class and not found:
        # A review-class launch is one review even when no report of it carries a line.
        found = parsed[-1:] or [Review(launch, launch.end, review_lines(""),
                                       commits=commits("\n".join(_asked(launch, launch.end))))]
    return found


def _asked(launch: Launch, at: datetime) -> list[str]:
    """The requests the launch had received by this moment."""
    return [text for moment, text in launch.requests if moment <= at]


def _own_commits(launch: Launch) -> list[tuple[datetime, set[str]]]:
    """Per report, the commits it names that no earlier request to the launch named: the
    work it reports as its own, not the base or the target it was given."""
    found = []
    for at, report in launch.reports:
        given = commits("\n".join(_asked(launch, at)))
        found.append((at, {commit for commit in commits(report) if not any(same_commit(commit, g) for g in given)}))
    return found


def _reporters(reported: list, commit: str, review: Review) -> list[Launch]:
    """Launches that reported this commit as their own no later than the review."""
    found = []
    for launch, at, own in reported:
        if launch is not review.launch and at <= review.at and all(launch is not other for other in found) \
                and any(same_commit(commit, mine) for mine in own):
            found.append(launch)
    return found


def _pair_by_commit(review: Review, reported: list) -> tuple[set[str], bool, list[dict]]:
    """Add the subjects the review's commits name: the commits on its REVIEWED line, or,
    with none there and no name resolved, those in its report and the requests it had
    received. Returns the commits some launch reported, whether one paired, and each
    commit two or more launches reported, which pairs with none of them."""
    line_commits = commits("\n".join(review.lines["reviewed"]))
    if not line_commits and review.subjects:
        return set(), False, []
    settled, paired, unclear = set(), False, []
    for commit in sorted(line_commits or review.commits):
        owners = _reporters(reported, commit, review)
        if len(owners) > 1:
            unclear.append({"review": review.name, "commit": commit,
                            "launches": sorted(launch.name or "?" for launch in owners)})
        elif owners:
            paired = True
            if all(owners[0] is not other for other in review.subjects):
                review.subjects.append(owners[0])
        if owners:
            settled.add(commit)
    return settled, paired, unclear


def _session_names(session: Path, classes: list[str] | None) -> set[str]:
    """Child names of every launch in a session, read from meta files only."""
    names = set()
    for path in session.glob("subagents/agent-*.meta.json"):
        try:
            meta = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, ValueError):
            continue
        description = meta.get("description") if isinstance(meta, dict) else None
        if isinstance(description, str):
            name = child_name(description, _classify(description, classes) is not None)
            if name:
                names.add(name.casefold())
    return names


def read_prices(path: Path) -> dict:
    """Owner-supplied list prices: model-id fragment -> $ per MTok and cache-write multipliers."""
    document = read_document(path)
    if not isinstance(document, dict) or not document:
        raise EvidenceError("invalid_prices_file: expected an object of model-id fragments")
    prices = {}
    for key, entry in document.items():
        if not isinstance(key, str) or not key.strip():
            raise EvidenceError("invalid_prices_file: empty model-id fragment")
        if not isinstance(entry, dict) or set(entry) != PRICE_KEYS:
            raise EvidenceError(f"invalid_prices_file: {key} needs exactly {', '.join(sorted(PRICE_KEYS))}")
        if any(type(value) not in (int, float) or not math.isfinite(value) or value < 0 for value in entry.values()):
            raise EvidenceError(f"invalid_prices_file: {key} needs non-negative numbers")
        prices[key.strip().lower()] = entry
    return prices


def _price(prices: dict, model: str | None) -> dict | None:
    if not model:
        return None
    matches = [key for key in prices if key in model.lower()]
    return prices[max(matches, key=len)] if matches else None


def _cost(tokens: Counter, price: dict) -> float:
    return (tokens["input"] * price["input"] + tokens["output"] * price["output"]
            + tokens["cache_read"] * price["cache_read"]
            + tokens["cache_write_5m"] * price["input"] * price["cache_write_5m_multiplier"]
            + tokens["cache_write_1h"] * price["input"] * price["cache_write_1h_multiplier"]) / 1e6


def _median(values: list) -> float | int | None:
    if not values:
        return None
    middle = statistics.median(values)
    return int(middle) if float(middle).is_integer() else round(middle, 1)


def _tokens(counter: Counter) -> dict:
    return {kind: counter[kind] for kind in TOKEN_KINDS}


def _verdict_table() -> dict:
    return {key: 0 for key in (*VERDICTS, NO_VERDICT, UNRECOGNIZED)}


def _chains(reviews: list[Review]) -> list[list[Review]]:
    """Each path of reviews linked by FOLLOWS, oldest first; a lone review is no chain."""
    followed = {id(review.follows) for review in reviews if review.follows is not None}
    chains = []
    for review in reviews:
        if id(review) in followed or review.follows is None:
            continue
        chain, seen, current = [], set(), review
        while current is not None and id(current) not in seen:
            seen.add(id(current))
            chain.append(current)
            current = current.follows
        chains.append(list(reversed(chain)))
    return chains


def report(projects_dir: Path, since: datetime, until: datetime | None, *, classes: list[str] | None = None,
           review_classes: list[str] = (), prices: dict | None = None) -> dict:
    """The route report for launches started in [since, until)."""
    if until is not None and until <= since:
        raise EvidenceError("--until must be later than --since")
    for name in review_classes:
        if not CLASS_NAME.fullmatch(name) or (classes is not None and name not in classes):
            raise EvidenceError(f"--review-class {name!r} is not a class of the route table")
    header = {"client": "claude-code", "projects_dir": str(projects_dir),
              "window": {"since": since.isoformat(), "until": until.isoformat() if until else None},
              "class_source": "route_table" if classes is not None else "class_name_grammar",
              "review_classes": sorted(set(review_classes)), "units": UNITS}
    if not projects_dir.is_dir():
        return {"status": "no_transcripts", "reason": "projects_dir_not_found", **header}
    floor = since.timestamp()
    launches = []
    for path in sorted(projects_dir.glob("*/*/subagents/agent-*.jsonl")):
        try:
            # A file last written before the window cannot hold a launch that started in it.
            if path.stat().st_mtime < floor:
                continue
            launch = read_transcript(path, since, until)
        except OSError:
            continue
        if launch is not None:
            read_meta(launch, classes)
            launches.append(launch)
    if not launches:
        return {"status": "no_transcripts", "reason": "no_launch_started_in_window", **header}

    by_session = defaultdict(list)
    for launch in launches:
        by_session[launch.session].append(launch)
    review_set = set(review_classes)
    reviews = [review for launch in launches for review in _reviews_of(launch, launch.cls in review_set)]
    reviews.sort(key=lambda review: review.at)
    session_reviews = defaultdict(list)
    for review in reviews:
        session_reviews[review.launch.session].append(review)

    # A launch that judged work is not its author, so only the other launches report commits.
    reviewers = {id(review.launch) for review in reviews}
    reported = defaultdict(list)
    for launch in launches:
        if id(launch) not in reviewers:
            reported[launch.session].extend((launch, at, own) for at, own in _own_commits(launch) if own)

    known_names: dict[Path, set[str]] = {}
    unresolved, outside, unresolved_follows, ambiguous, ambiguous_reviews, by_commit = [], 0, 0, [], set(), 0
    for review in reviews:
        session = review.launch.session
        unmatched = []
        for name in review.lines["reviewed"]:
            subject = _named(by_session[session], name, review)
            if subject is not None:
                if all(subject is not other for other in review.subjects):
                    review.subjects.append(subject)
                continue
            if session not in known_names:
                known_names[session] = _session_names(session, classes)
            if name.casefold() in known_names[session]:
                outside += 1
            else:
                unmatched.append(name)
        settled, paired, unclear = _pair_by_commit(review, reported[session])
        by_commit += paired
        ambiguous.extend(unclear)
        if unclear:
            ambiguous_reviews.add(id(review))
        unresolved.extend({"review": review.name, "name": name} for name in unmatched
                          if not any(same_commit(commit, known) for commit in commits(name) for known in settled))
        if review.lines["follows"]:
            review.follows = _followed(session_reviews[session], review.lines["follows"], review)
            unresolved_follows += review.follows is None

    def key(launch):
        return (launch.cls, launch.model, launch.effort)

    groups = defaultdict(list)
    for launch in launches:
        groups[key(launch)].append(launch)
    reviewed = {id(subject) for review in reviews for subject in review.subjects}
    verdicts = defaultdict(lambda: {"first": _verdict_table(), "follow_up": _verdict_table()})
    for review in reviews:
        split = "follow_up" if review.lines["follows"] else "first"
        for group in {key(subject) for subject in review.subjects}:
            verdicts[group][split][review.verdict] += 1
    chains = _chains(reviews)
    chains_by_group = defaultdict(list)
    for chain in chains:
        sequence = [review.verdict for review in chain]
        subjects = sorted({subject.name or "?" for review in chain for subject in review.subjects})
        entry = {"length": len(chain), "verdicts": sequence, "reviews": [review.name or "?" for review in chain],
                 "reviewed": subjects, "repeated_rework": sum(v in REWORK for v in sequence) >= 2}
        for group in {key(subject) for review in chain for subject in review.subjects}:
            chains_by_group[group].append(entry)

    order = {name: index for index, name in enumerate(classes or [])}

    def rank(item):
        (cls, model, effort), members = item
        return (cls is None, order.get(cls, len(order)), -len(members) if classes is None else 0,
                cls or "", model or "", effort or "")

    rows = []
    for group, members in sorted(groups.items(), key=rank):
        own, advisor = Counter(), Counter()
        for launch in members:
            own.update(launch.own)
            advisor.update(launch.advisor)
        count_reviewed = sum(id(launch) in reviewed for launch in members)
        row = {"class": group[0], "model": group[1], "effort": group[2], "launches": len(members),
               "tool_calls": {"median": _median([launch.tool_calls for launch in members]),
                              "total": sum(launch.tool_calls for launch in members)},
               "minutes": {"median": _median([round((launch.end - launch.start).total_seconds() / 60, 1)
                                              for launch in members])},
               "tokens": _tokens(own),
               "advisor": {"calls": sum(launch.advisor_calls for launch in members), "tokens": _tokens(advisor)},
               "reviewed_launches": count_reviewed,
               "share_reviewed": round(count_reviewed / len(members), 3),
               "reviews_of_this_work": verdicts.get(group, {"first": _verdict_table(),
                                                           "follow_up": _verdict_table()}),
               "chains": chains_by_group.get(group, []),
               "repeated_rework": [sorted({*entry["reviews"], *entry["reviewed"]})
                                   for entry in chains_by_group.get(group, []) if entry["repeated_rework"]]}
        if prices is not None:
            row["cost"] = _group_cost(members, prices)
        rows.append(row)

    totals = {"launches": len(launches), "unclassed_launches": sum(launch.cls is None for launch in launches),
              "launches_without_meta": sum(not launch.has_meta for launch in launches),
              "malformed_lines_skipped": sum(launch.malformed for launch in launches),
              "advisor_calls": sum(launch.advisor_calls for launch in launches),
              "reviews": len(reviews),
              "reviews_without_verdict_line": sum(r.verdict == NO_VERDICT for r in reviews),
              "reviews_with_unrecognized_verdict": sum(r.verdict == UNRECOGNIZED for r in reviews),
              "reviews_without_resolved_subject": sum(not r.subjects for r in reviews),
              "reviews_resolved_by_commit": by_commit,
              "reviews_with_ambiguous_commits": len(ambiguous_reviews),
              "ambiguous_reviewed_commits": ambiguous,
              "reviews_with_unresolved_names": len({entry["review"] for entry in unresolved}),
              "unresolved_reviewed_names": unresolved,
              "reviewed_names_outside_window": outside,
              "follow_ups_with_unresolved_follows": unresolved_follows,
              "chains": len(chains),
              "chains_with_repeated_rework": sum(sum(r.verdict in REWORK for r in chain) >= 2
                                                 for chain in chains)}
    result = {"status": "ok", **header, "totals": totals, "classes": rows}
    if prices is not None:
        result["cost_basis"] = COST_BASIS
    return result


def _group_cost(members: list[Launch], prices: dict) -> dict:
    spent = {"own": 0.0, "advisor": 0.0}
    unpriced = set()
    for launch in members:
        for (role, model), tokens in launch.by_model.items():
            if not any(tokens.values()):
                continue
            price = _price(prices, model)
            if price is None:
                unpriced.add(model or "unknown")
            else:
                spent[role] += _cost(tokens, price)
    return {"own_usd": round(spent["own"], 6), "advisor_usd": round(spent["advisor"], 6),
            "unpriced_models": sorted(unpriced)}
