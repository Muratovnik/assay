"""Point a Claude agent at a loaded skill's reference whose reading condition its own turn visibly met.

Each row of BRANCHES pairs a reference with the condition its SKILL.md names
for reading it and a sign of that condition in the turn's own actions or words:
an edited .vue file for code-change's Vue structure, a plan file written for
implementation-planning's units, a line saying that nothing qualifies for
evidence-research's coverage reference. On Stop or SubagentStop, when a sign
appears in this turn, the session or subagent loaded the skill since the latest
compaction and the reference was not read in that span, the turn continues
once with one note naming every such reference. It is never a block, runs no
model and stores nothing. A condition the transcript cannot show, such as
whether a comparison is consequential, has no row; a write made through a shell
command is not seen. It reads the transcript tail the skill gate reads.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
import re

from .skill_gate import HANDBACK, NAME, _lines, _load, _prompt


@dataclass(frozen=True)
class Branch:
    rule: str  # The ID that disabled_rules turns off.
    skill: str
    references: tuple
    condition: str  # The reading condition, as SKILL.md names it.
    sign: str  # What this turn did, completed by its evidence.


COVERAGE = "coverage-claims"
BRANCHES = (
    Branch(COVERAGE, "evidence-research", ("search-and-coverage.md",),
           "a landscape or a claim of completeness", "says something is absent or that none qualifies"),
    Branch("branch-vue-structure", "code-change", ("vue-structure.md",),
           "Vue components, reactive state or composables", "edited"),
    Branch("branch-quality-checks", "code-change", ("effective-quality-checks.md",),
           "quality-tool changes, relocated files or claims that checks enforce a rule",
           "changed check configuration or moved files"),
    Branch("branch-bounded-review", "independent-audit", ("bounded-review.md",),
           "authorized audit delegation", "launched a review agent"),
    Branch("branch-implementation-units", "implementation-planning", ("implementation-units.md",),
           "multi-unit decomposition, shared interfaces or meaningful acceptance", "wrote a plan"),
    Branch("branch-ui-acceptance", "ui-delivery", ("scenario-testing.md", "visual-judgment.md"),
           "acceptance evidence after the last write and judging the composed result", "edited interface files"),
    Branch("branch-languages", "technical-writing", ("languages.md",),
           "prose in Russian, English or Chinese", "wrote documentation in Russian or Chinese"),
)
RULES = tuple(row.rule for row in BRANCHES)

SHELLS = frozenset({"Bash", "PowerShell"})
WRITES = frozenset({"Edit", "Write", "MultiEdit", "NotebookEdit"})
AGENTS = frozenset({"Agent", "Task"})
MAX_ITEMS = 2
MAX_LINE = 2_000
MAX_QUOTE = 160
MAX_TEXT = 65_536
# Enough Cyrillic or Chinese characters to be prose rather than a quoted word.
MIN_PROSE = 40
# A line saying that no solution exists or that none qualifies, in English or Russian. A
# claim about the landscape names what is absent; "no test selected", "committed nowhere"
# and "none of them ran" are facts about the work, so a common negation needs that noun.
SOLUTION = re.compile(
    r"\b(?:skills?|tools?|solutions?|librar(?:y|ies)|packages?|plugins?|mods?|extensions?|alternatives?"
    r"|implementations?|projects?|products?|frameworks?|services?|options?|candidates?|utilit(?:y|ies)|apps?)\b"
    r"|навык|инструмент|решени|библиотек|пакет|плагин|\bмод(?:а|ы|ов)?\b|расширени|аналог|альтернатив|реализаци"
    r"|проект|продукт|фреймворк|сервис|вариант|кандидат|утилит|приложени", re.I)
ABSENCE = re.compile(
    r"\bnothing (?:like (?:this|that|it)|similar|comparable)\b|\bnot aware of any\b"
    r"|\bтакого нет\b|\bничего (?:подобного|похожего)|\bнет (?:ни )?(?:готов|существующ|подобн)"
    r"|\bготов\w* (?:[\w-]+ ){0,2}нет\b", re.I)
NEGATION = re.compile(
    r"\bno (?:existing|ready-made|off-the-shelf|such)\b|\bnone of (?:them|these|those|the)\b"
    r"|\b(?:does|do)(?:n't| not) (?:yet )?exist\b|\bnowhere\b|\bthere (?:is|are) no\b"
    r"|\bни од(?:ин|на|но|ного|ной)\b|\bнигде\b|\bне существу", re.I)
# Linter, formatter, type-checker, test-runner, hook and CI configuration.
QUALITY = re.compile(
    r"(?:^|[\\/])(?:\.?ruff\.toml|mypy\.ini|\.flake8|pytest\.ini|tox\.ini|\.pylintrc|\.pre-commit-config\.ya?ml"
    r"|\.eslintrc[^\\/]*|eslint\.config\.[cm]?[jt]s|\.prettierrc[^\\/]*|prettier\.config\.[cm]?js|biome\.jsonc?"
    r"|\.stylelintrc[^\\/]*|stylelint\.config\.[cm]?js|\.golangci\.ya?ml|lefthook\.ya?ml|\.markdownlint[^\\/]*"
    r"|check\.py)$|[\\/]\.github[\\/]workflows[\\/][^\\/]+\.ya?ml$|[\\/]\.husky[\\/]", re.I)
# A shared Python manifest counts only when the written text holds a tool section.
MANIFEST = re.compile(r"(?:^|[\\/])(?:pyproject\.toml|setup\.cfg)$", re.I)
TOOL_SECTION = re.compile(r"^\s*\[(?:tool\.|tool:pytest\b|flake8\b|mypy\b|pycodestyle\b)", re.M)
MOVE = re.compile(r"\bgit\s+mv\b")
VUE = re.compile(r"\.vue$", re.I)
INTERFACE = re.compile(r"\.(?:vue|svelte|[jt]sx|css|scss|sass|less|html?)$", re.I)
# A test of an interface is checked by running it, not by judging a rendered screen.
TEST = re.compile(r"\.(?:test|spec)\.\w+$|[\\/]__tests__[\\/]", re.I)
# A file under a plans directory, or one named for a plan: not explanation.md.
PLAN = re.compile(r"[\\/]plans?[\\/][^\\/]+\.md$|(?:^|[\\/._-])plan(?:s|ning)?(?:[._-][^\\/]*)?\.md$", re.I)
DOCUMENT = re.compile(r"\.(?:md|mdx|markdown|rst)$", re.I)
# Agent memory notes are not documentation for a reader.
NOTES = re.compile(r"[\\/]memory[\\/][^\\/]+$|(?:^|[\\/])MEMORY\.md$", re.I)
PROSE = re.compile(r"[Ѐ-ӿ一-鿿]")
REVIEW = re.compile(r"\b(?:review|reviewer|audit|auditor)\b|ревью|аудит", re.I)
# A worker that fixes or implements review findings is not the review.
REPAIR = re.compile(r"\bfix|\bimplement|^code\b|исправ|реализ", re.I)
REVIEWER = re.compile(r"review|audit", re.I)
REFERENCE_PATH = re.compile(r"[\\/]([a-z][a-z0-9-]{0,63})[\\/]references[\\/]([\w.-]+\.md)$")
SEPARATOR = re.compile(r"[\\/]")


def _claims(line):
    line = line[:MAX_LINE]
    return bool(ABSENCE.search(line) or (NEGATION.search(line) and SOLUTION.search(line)))


def _absent(text):
    return [line for line in text.splitlines() if _claims(line)] if isinstance(text, str) else []


def _written(tool, data):
    """The text a write tool adds, bounded."""
    if tool == "MultiEdit":
        edits = data.get("edits") if isinstance(data.get("edits"), list) else []
        text = "\n".join(edit["new_string"] for edit in edits
                         if isinstance(edit, dict) and isinstance(edit.get("new_string"), str))
    else:
        text = data.get({"Write": "content", "Edit": "new_string", "NotebookEdit": "new_source"}.get(tool, ""))
    return text[:MAX_TEXT] if isinstance(text, str) else ""


def signs(tool, data):
    """(rule, evidence) pairs that one tool call shows."""
    if not isinstance(data, dict):
        return []
    if tool in WRITES:
        path = data.get("notebook_path" if tool == "NotebookEdit" else "file_path")
        if not isinstance(path, str) or not path or len(path) > 4_096:
            return []
        name, text = SEPARATOR.split(path)[-1], _written(tool, data)
        found = []
        if VUE.search(path):
            found.append(("branch-vue-structure", name))
        if QUALITY.search(path) or (MANIFEST.search(path) and TOOL_SECTION.search(text)):
            found.append(("branch-quality-checks", name))
        if INTERFACE.search(path) and not TEST.search(path):
            found.append(("branch-ui-acceptance", name))
        # Editing an existing plan, such as ticking a step, does not decompose work.
        if tool == "Write" and PLAN.search(path):
            found.append(("branch-implementation-units", name))
        if DOCUMENT.search(path) and not NOTES.search(path) and len(PROSE.findall(text)) >= MIN_PROSE:
            found.append(("branch-languages", name))
        return found
    if tool in SHELLS and isinstance(data.get("command"), str) and MOVE.search(data["command"][:MAX_TEXT]):
        return [("branch-quality-checks", "git mv")]
    if tool in AGENTS:
        description, agent = (value if isinstance(value, str) else ""
                              for value in (data.get("description"), data.get("subagent_type")))
        description = " ".join(description.split())[:200]
        if REVIEWER.search(agent[:200]) or (REVIEW.search(description) and not REPAIR.search(description)):
            return [("branch-bounded-review", description[:80] or agent[:80])]
    return []


def ledger(path, rows, *, subagent=False, needed=False):
    """(evidence, loaded, read) from a transcript's tail, or None when it cannot be read.

    Evidence maps each row's rule to what this turn showed for it: lines of
    its messages saying something is absent, or the files and launches its
    tool calls name. Loaded holds the rows' skills loaded since the latest
    compaction, read the (skill, reference) pairs read in that span by Read or
    a shell command naming both. Without evidence in the turn, and unless
    needed says the final message holds some, the scan stops at the turn's start.
    """
    if not isinstance(path, str) or not path or len(path) > 4_096:
        return None
    skills = {row.skill for row in rows}
    wanted = {(row.skill, reference) for row in rows for reference in row.references}
    rules = {row.rule for row in rows}
    evidence, loaded, read, in_turn = {}, set(), set(), True

    def note(rule, items):
        if rule in rules and items:
            evidence.setdefault(rule, []).extend(items)

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
            attachment = entry.get("attachment")
            if kind == "attachment" and isinstance(attachment, dict) and attachment.get("type") == "invoked_skills":
                # Compaction re-attaches the skills it keeps; their references are not re-read.
                for skill in attachment.get("skills") or []:
                    name = (NAME.fullmatch(skill["name"]) if isinstance(skill, dict)
                            and isinstance(skill.get("name"), str) else None)
                    if name and name[1] in skills:
                        loaded.add(name[1])
                continue
            message = entry.get("message")
            content = message.get("content") if isinstance(message, dict) else None
            if kind == "user" and in_turn and _prompt(entry, content):
                in_turn = False
                if not evidence and not needed:
                    break  # Nothing to check: earlier loads and reads would go unused.
            if kind != "assistant" or not isinstance(content, list):
                continue
            for block in content:
                if not isinstance(block, dict):
                    continue
                data = block.get("input")
                if block.get("type") == "text" and in_turn:
                    note(COVERAGE, _absent(block.get("text")))
                if block.get("type") != "tool_use" or not isinstance(data, dict):
                    continue
                tool = block.get("name")
                if tool == HANDBACK and in_turn:
                    note(COVERAGE, _absent(data.get("message")))
                skill = _load(tool, data, skills)
                if skill:
                    loaded.add(skill)
                elif tool == "Read" and isinstance(data.get("file_path"), str):
                    match = REFERENCE_PATH.search(data["file_path"])
                    if match and (match[1], match[2]) in wanted:
                        read.add((match[1], match[2]))
                elif tool in SHELLS and isinstance(data.get("command"), str):
                    command = data["command"][:MAX_TEXT]
                    read.update(pair for pair in wanted if pair[0] in command and pair[1] in command)
                if in_turn:
                    for rule, item in signs(tool, data):
                        note(rule, [item])
    except (OSError, ValueError):
        return None
    return evidence, loaded, read


def _quote(line):
    line = " ".join(line.split())
    return "“" + (line if len(line) <= MAX_QUOTE else line[:MAX_QUOTE - 1] + "…") + "”"


def stopped(event, rules=RULES, skills=None):
    """Continuation feedback on Stop or SubagentStop naming each reference this turn's signs call for, else {}.

    Rules are the enabled rows; skills, when given, are the enabled skill names.
    """
    name = event.get("hook_event_name")
    if name not in {"Stop", "SubagentStop"} or event.get("stop_hook_active"):
        return {}
    if name == "SubagentStop" and not event.get("agent_id"):
        return {}
    rows = [row for row in BRANCHES if row.rule in rules and (skills is None or row.skill in skills)]
    if not rows:
        return {}
    last = event.get("last_assistant_message")
    final = _absent(last[:MAX_TEXT]) if isinstance(last, str) and any(row.rule == COVERAGE for row in rows) else []
    path = event.get("agent_transcript_path") if name == "SubagentStop" else event.get("transcript_path")
    scan = ledger(path, rows, subagent=name == "SubagentStop", needed=bool(final))
    if not scan:
        return {}
    evidence, loaded, read = scan
    if final:
        evidence[COVERAGE] = [*final, *evidence.get(COVERAGE, [])]
    lines = []
    for row in rows:
        items = list(dict.fromkeys(evidence.get(row.rule, [])))
        unread = [reference for reference in row.references if (row.skill, reference) not in read]
        if not items or row.skill not in loaded or not unread:
            continue
        shown = "; ".join(_quote(item) if row.rule == COVERAGE else item for item in items[:MAX_ITEMS])
        line = (f"- {row.skill}: {' and '.join('references/' + reference for reference in unread)}, which the "
                f"skill names for {row.condition}; this turn {row.sign} ({shown}).")
        if row.rule == COVERAGE:
            line += (" Evidence absent from the examined scope is not proof that it does not exist; a claim "
                     "already limited to what was examined and naming that scope needs one line saying so.")
        lines.append(line)
    if not lines:
        return {}
    who = "this subagent" if name == "SubagentStop" else "this session"
    # Stated as facts, as the skill gate's feedback is.
    return {"hookSpecificOutput": {"hookEventName": name, "additionalContext": "\n".join([
        f"Assay branch check: {who} loaded each skill below, this turn met the condition it names for a "
        "reference, and that reference was not read in this context:", *lines,
        "The answer already given stands: after reading, one short line is enough when nothing changes; "
        "otherwise only the corrections that would change the user's code, conclusions or decisions, without "
        "repeating the answer."])}}
