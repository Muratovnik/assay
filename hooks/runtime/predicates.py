"""Decide from one tool call alone whether a hook check can apply to it; regular expressions only.

The Claude hook runs before every tool call, and most calls are ones no check
answers or records. These predicates let the hook entry tell those calls apart
before it loads the rules, the routing modules and the stores. The checks that
own them (the mid-turn note, the rerun note, the skill gate) import them from
here, so the entry and the checks cannot disagree about which calls they read.
"""
from __future__ import annotations

import re

from .scratch import is_scratch

# The profiles that may only read and report; any plugin prefix before the last ":" is ignored.
READING_ROLES = frozenset({"evidence-reviewer", "official-docs-researcher"})

WRITES = frozenset({"Edit", "Write", "MultiEdit", "NotebookEdit"})
SHELLS = frozenset({"Bash", "PowerShell"})
WEB = frozenset({"WebFetch", "WebSearch"})
QUESTION = "AskUserQuestion"
MAX_PATH = 4_096
MAX_COMMAND = 65_536

# A Read of this file loads the skill it names, as the Skill tool does.
LOADED_SKILL = re.compile(r"[\\/]skills[\\/]([a-z][a-z0-9-]{0,63})[\\/]SKILL\.md$")

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
DOCUMENT = re.compile(r"\.(?:md|mdx|markdown|rst)$", re.I)
README = re.compile(r"(?:^|[\\/])README(?:\.[\w-]+)*\.(?:md|mdx|markdown|rst|txt)$", re.I)
DOCS = re.compile(r"(?:^|[\\/])docs[\\/]", re.I)
# Plans and research are working records, not documentation for a reader.
WORKING = re.compile(r"(?:^|[\\/])docs[\\/](?:[\w.-]+[\\/])*(?:plans?|research)[\\/]|[\\/]plans?[\\/][^\\/]+\.md$", re.I)
# Agent instructions, memory notes and generated change logs are other work.
NOT_DOCUMENTATION = re.compile(r"(?:^|[\\/])(?:CLAUDE|AGENTS|GEMINI|MEMORY|CHANGELOG|SKILL)\.md$|[\\/]memory[\\/][^\\/]+$", re.I)
# A written skill file: its SKILL.md, a reference or eval, or the activation rules. Not the load pattern above.
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
# An option that leaves things as they are, by its label. Whole words: "поставить" contains "оставить".
NO_ACTION = re.compile(r"\b(?:оставить|ничего|не (?:делать|менять|трогать|удалять|выпускать|проводить|ставить"
                       r"|поставлять|включать)|отлож\w*|позже|пока (?:ничего|не\w*)|сначала обсудить|(?:подо)?ждать"
                       r"|do nothing|keep\w*|leave|defer\w*|later|skip)\b|^(?:нет|no)\b", re.I)


def reading_profile(role):
    """The reading profile a native agent type names, or None."""
    if not isinstance(role, str):
        return None
    name = role.split(":")[-1]
    return name if name in READING_ROLES else None


def classify(path):
    """The mid-turn row a written file calls for, or None."""
    if not isinstance(path, str) or not path or len(path) > MAX_PATH or GENERATED.search(path):
        return None
    if is_scratch(path):
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


def _can_leave_as_is(question):
    if not isinstance(question, dict):
        return False
    if question.get("multiSelect") is True:
        return True
    options = question.get("options")
    return isinstance(options, list) and any(
        isinstance(option, dict) and isinstance(option.get("label"), str) and NO_ACTION.search(option["label"].strip())
        for option in options)


def offers_no_action(questions):
    """Whether every question to the owner can leave things as they are.

    A multi-select question can, with its boxes left unticked; a single-choice one needs an
    option whose label says so. Anything malformed cannot.
    """
    return isinstance(questions, list) and bool(questions) and all(_can_leave_as_is(question) for question in questions)


# Commands of one line run in order; a pipe or a redirection ends the part that names the run.
SEGMENT = re.compile(r"\r?\n|;|&&|\|\|")
TAIL = re.compile(r"\s(?:\||[0-9*]?>{1,2}|<).*$", re.S)
SCRIPT = re.compile(r"\.(?:ps1|psm1|py|sh|bash|js|mjs|cjs|ts|mts|rb|lua)$", re.I)
# Code given inline or on standard input is a new program each time, not a rerun.
INLINE = frozenset({"-", "-c", "-e", "-command", "-encodedcommand", "--eval", "--command"})
PREFIX = re.compile(r"^(?:&|\.|env|\w+=\S*|\$env:\w+=\S*)$", re.I)
INTERPRETERS = frozenset({"pwsh", "powershell", "python", "python3", "py", "node", "bash", "sh", "zsh", "ruby",
                          "deno", "tsx", "ts-node", "lua", "perl"})
# Environment managers that run the rest of the line: `uv run pytest`, `poetry run python x.py`.
WRAPPERS = frozenset({"uv", "uvx", "poetry", "pipenv", "pdm", "hatch", "rye"})
VALUED = frozenset({"--with", "--python", "-p", "--project", "--directory", "--env-file", "--extra", "--group"})
RUNNERS = frozenset({"pytest", "vitest", "jest", "mocha", "ava", "tap", "nox", "tox"})
# A package manager or build tool runs tests only through these subcommands.
SUBCOMMANDS = {"npm": {"test", "t", "run"}, "pnpm": {"test", "t", "run"}, "yarn": {"test", "run"},
               "bun": {"test", "run"}, "dotnet": {"test"}, "go": {"test"}, "cargo": {"test", "nextest"},
               "make": {"test", "check"}, "gradle": {"test", "check"}, "gradlew": {"test", "check"},
               "mvn": {"test", "verify"}, "npx": RUNNERS | {"playwright"}}
TESTING = re.compile(r"test|check|e2e", re.I)
MODULES = frozenset({"pytest", "unittest"})


def _tokens(part):
    tokens = [token.strip("'\"") for token in TAIL.sub("", " " + part).split()]
    while tokens and PREFIX.match(tokens[0]):
        tokens.pop(0)
    return [token for token in tokens if token]


def _program(token):
    name = re.split(r"[\\/]", token)[-1].lower()
    return name[:-4] if name.endswith((".exe", ".cmd", ".bat")) else name


def _short(token):
    parts = [part for part in re.split(r"[\\/]+", token) if part and part != "."]
    return "/".join(parts[-2:]).lower()


def _script(tokens, index):
    """A script by its last two path parts with its arguments, a path argument shortened the same way."""
    return " ".join(_short(token) for token in tokens[index:])


def _run(tokens):
    """The signature of one command's tokens, or None."""
    program = _program(tokens[0])
    if SCRIPT.search(tokens[0]):
        return _script(tokens, 0)
    if program in WRAPPERS:
        rest = tokens[2:] if program != "uvx" and len(tokens) > 1 and tokens[1].lower() == "run" else tokens[1:]
        while rest and rest[0].startswith("-"):
            rest = rest[2:] if rest[0].lower() in VALUED else rest[1:]
        return _run(rest) if rest else None
    if program in RUNNERS:
        return " ".join([program, *tokens[1:]]).lower()
    if program in SUBCOMMANDS:
        command = tokens[1].lower() if len(tokens) > 1 else ""
        if command not in SUBCOMMANDS[program] or (command == "run" and not TESTING.match(tokens[2] if len(tokens) > 2 else "")):
            return None
        return " ".join([program, *tokens[1:]]).lower()
    if program not in INTERPRETERS:
        return None
    for index, token in enumerate(tokens[1:], 1):
        lowered = token.lower()
        if lowered in INLINE:
            return None
        if lowered == "-m":
            module = tokens[index + 1].lower() if index + 1 < len(tokens) else ""
            return " ".join([module, *tokens[index + 2:]]).lower() if module in MODULES else None
        if SCRIPT.search(token):
            return _script(tokens, index)
    return None


def signature(command):
    """What the first run in a shell command line runs: a script's last two path parts or a test command; else None.

    Text after a heredoc marker is the heredoc's body, not commands.
    """
    if not isinstance(command, str):
        return None
    for part in SEGMENT.split(command[:MAX_COMMAND].split("<<", 1)[0]):
        tokens = _tokens(part)
        found = _run(tokens) if tokens else None
        if found:
            return found
    return None
