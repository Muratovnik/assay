"""English model-facing skill guidance for every request, in any input language.

The model judges which skills apply; no rule matches the user's words. Only an
explicit skill choice ("use code-change", `$code-change`) is recognized
deterministically. No model calls, tool calls or permissions.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import tomllib

MAX_PROMPT = 16_384
MAX_CONTEXT = 900
MAX_CHECK = 2_700
MAX_CUE = 80
DELEGATION_SKILL = "skill/route-subagents"
SKILL_CHECK = "skill-check"
SKILL_GATE = "skill-gate"
# Claude source checks: the note after a fetch and the stop check of full-read claims.
FETCH_NOTE = "fetch-note"
READ_CLAIMS = "read-claims"
# The Claude stop check of skill references a turn's own actions call for, one rule per row.
# This file is also loaded standalone, so it repeats branches.RULES; a test keeps the two equal.
BRANCH_RULES = ("coverage-claims", "branch-vue-structure", "branch-quality-checks", "branch-bounded-review",
                "branch-implementation-units", "branch-ui-acceptance", "branch-languages")
# The Claude note on a tool call that shows a skill the session has not loaded, one rule per row.
# Repeated from midturn.RULES for the same reason; a test keeps the two equal.
MIDTURN_RULES = ("midturn-evidence-research", "midturn-code-change", "midturn-test-writing", "midturn-ui-delivery",
                 "midturn-technical-writing", "midturn-skill-evaluation")
# Phrase rules retired in favor of the skill check. Old settings that disable
# them stay valid and do nothing, instead of breaking the hooks.
RETIRED_RULES = frozenset({"test-audit", "test-writing", "research", "reuse-lookup", "reuse-question",
                           "planning", "audit", "ui-delivery", "code-change", "delegation"})
OPAQUE_TEXT = " [data] "
SKILL_NAME = re.compile(r"(?:\$|/assay:|assay:)?([a-z][a-z0-9-]{0,63})(?![\w-])")
EXPLAIN = re.compile(r"^(?:what|how|why|explain|что|как|почему|объясни|расскажи|не\b|do not\b|don't\b)", re.I)
QUOTES = ('"', "'", "«", "“")


class RuleSet(list):
    """Explicitly selectable skills in check order, and whether the check runs."""

    def __init__(self, rules, skill_check, skill_gate=False, skills_root="", fetch_note=False, read_claims=False,
                 branch_rules=(), midturn_rules=()):
        super().__init__(rules)
        self.skill_check = skill_check
        # The Claude stop gate holds a reply to the skills its check line names.
        self.skill_gate = skill_check and skill_gate
        # Where a subagent without the skill tool reads each SKILL.md.
        self.skills_root = skills_root
        # Independent of the skill check: it reads sources, not skills.
        self.fetch_note = fetch_note
        self.read_claims = read_claims
        # Rows of the stop check that hold a turn to the references its own actions call for.
        self.branch_rules = frozenset(branch_rules)
        # Rows of the note on a tool call that shows a skill this session has not loaded. The note
        # points at the skill check, so it goes when the check does.
        self.midturn_rules = frozenset(midturn_rules) if skill_check else frozenset()


def load_rules(root: Path, *, disabled_rules=(), disabled_skills=()):
    catalog = tomllib.loads((root / "catalog.toml").read_text(encoding="utf-8"))
    document = tomllib.loads((root / "hooks/activation-rules.toml").read_text(encoding="utf-8"))
    if set(document) != {"schema", "skills"} or document["schema"] != 2 or not isinstance(document["skills"], list):
        raise ValueError("invalid skill map document")
    assets = {asset["id"]: asset for asset in catalog["assets"] if asset["kind"] == "skill"}
    known = {SKILL_CHECK, SKILL_GATE, FETCH_NOTE, READ_CLAIMS, *BRANCH_RULES, *MIDTURN_RULES}
    if set(disabled_rules) - RETIRED_RULES - known or set(disabled_skills) - set(assets):
        raise ValueError("unknown disabled rule/skill")
    rules, seen, content = [], [], []
    for item in document["skills"]:
        if not isinstance(item, dict) or set(item) != {"skill", "cue"} or item["skill"] not in assets:
            raise ValueError("skill map entry references unknown catalog skill")
        cue = item["cue"]
        if (not isinstance(cue, str) or not 0 < len(cue) <= MAX_CUE or not cue.isascii()
                or not cue.isprintable() or cue != cue.strip()):
            raise ValueError("skill map cue must be short printable ASCII")
        seen.append(item["skill"])
        path = (root / assets[item["skill"]]["path"] / "SKILL.md").resolve()
        if not path.is_relative_to(root.resolve()):
            raise ValueError("skill escapes installed plugin")
        if not path.is_file() or item["skill"] in disabled_skills:
            continue
        content.append((item["skill"], hashlib.sha256(path.read_bytes()).hexdigest()))
        rules.append({"id": "explicit:" + item["skill"], "skill": item["skill"], "priority": 0,
                      "patterns": [], "cue": cue})
    if sorted(seen) != sorted(set(seen)) or set(seen) != set(assets):
        raise ValueError("skill map must name every catalog skill exactly once")
    skills_root = str(root.resolve() / "skills")
    result = RuleSet(rules, SKILL_CHECK not in disabled_rules, SKILL_GATE not in disabled_rules, skills_root,
                     FETCH_NOTE not in disabled_rules, READ_CLAIMS not in disabled_rules,
                     [rule for rule in BRANCH_RULES if rule not in disabled_rules],
                     [rule for rule in MIDTURN_RULES if rule not in disabled_rules])
    # The installation path is the owner's; bound the text the catalog controls.
    if longest_check(rules) > MAX_CHECK:
        raise ValueError("skill check exceeds its context bound")
    fingerprint = hashlib.sha256(json.dumps([rules, content, result.skill_check], sort_keys=True).encode()).hexdigest()
    return result, fingerprint


def longest_check(rules):
    """Length of the longest skill check variant these rules produce."""
    full = RuleSet(rules, True)
    every = [rule["skill"].split("/", 1)[1] for rule in rules]
    # The loaded-skills hint comes only from the Claude gate's records.
    return max(len(skill_check(full, loaded=every)), len(skill_check(full, client="codex")),
               len(subagent_check(full, client="codex")))


def request_text(prompt, known_names):
    if not isinstance(prompt, str) or len(prompt) > MAX_PROMPT:
        return ""
    from markdown_it import MarkdownIt
    # CommonMark, not a second hand-written markdown parser. Blockquotes,
    # fenced/indented code, lists and headings are data rather than requests.
    tokens = MarkdownIt("commonmark").parse(prompt)
    for index, token in enumerate(tokens):
        if token.type != "inline" or token.level != 1 or not index or tokens[index - 1].type != "paragraph_open":
            continue
        parts = []
        for child in token.children or []:
            if child.type == "text":
                parts.append(child.content)
            elif child.type == "code_inline":
                name = SKILL_NAME.fullmatch(child.content)
                # Preserve a barrier: dropping data could manufacture a choice.
                parts.append(child.content if name and name[1] in known_names else OPAQUE_TEXT)
            elif child.type in {"html_inline", "image"}:
                parts.append(OPAQUE_TEXT)
            elif child.type in {"softbreak", "hardbreak"}:
                parts.append(" ")
        # Only the first actual request paragraph; a pasted second document
        # cannot select a skill after an explanatory first paragraph.
        return " ".join("".join(parts).split()).strip()
    return ""


def continuation_request(prompt):
    """Recognize only a whole, plain continuation request, never a task or consent.

    Additional paragraphs, quoted/code examples and scope modifiers must go
    through ordinary task selection; they must not inherit an old hint.
    """
    if not isinstance(prompt, str) or len(prompt) > MAX_PROMPT:
        return False
    try:
        from markdown_it import MarkdownIt
    except ImportError:
        # Without the parser nothing counts as a continuation; the stateful
        # path must not take the parser-free skill check down with it.
        return False
    tokens = MarkdownIt("commonmark").parse(prompt)
    if [token.type for token in tokens] != ["paragraph_open", "inline", "paragraph_close"]:
        return False
    children = tokens[1].children or []
    if not children or any(child.type != "text" for child in children):
        return False
    text = prompt.strip()
    return re.fullmatch(
        r"(?:(?:please|пожалуйста)[, ]+)?(?:continue|resume|go on|go ahead|продолжай|продолжи|продолжим)[.!]?",
        text, re.I) is not None


def explicit_selection(text, rules):
    explicit = re.match(
        r"^(?:use|apply|используй|примени)\s+(?:(?:the\s+)?skills?\s+|the\s+|навык[и]?\s+)?(.+)$",
        text, re.I)
    if not explicit and not text.startswith(("$", "/assay:")):
        return []
    selection = explicit[1] if explicit else text
    found = []
    # Stop at the first non-name: later quoted or negated methods are not choices.
    for segment in re.split(r"\s*(?:,|\band\b|\bи\b)\s*", selection, flags=re.I):
        match = SKILL_NAME.match(segment)
        rule = next((r for r in rules if match and r["skill"] == "skill/" + match[1]), None)
        if not rule:
            break
        if rule not in found:
            found.append(rule)
        if segment[match.end():].strip() or len(found) == 2:
            break
    return found


def select(prompt, rules):
    """The skills a request names explicitly; ordinary wording selects nothing."""
    names = {rule["skill"].split("/", 1)[1] for rule in rules}
    text = request_text(prompt, names)
    if not text or EXPLAIN.match(text) or text.startswith(QUOTES):
        return []
    return explicit_selection(text, rules)


def context(rule_ids, rules, *, restored=False):
    selected = [r for identifier in rule_ids for r in rules if r["id"] == identifier][:2]
    if not selected:
        return ""
    names = ", ".join(r["skill"].split("/", 1)[1] for r in selected)
    prefix = "Previous request suggested" if restored else "The request suggests"
    delegation = (
        " For already-authorized delegation, select useful outcomes and launch timing before substantial solo work; "
        "revisit ready dependencies and material verification, not just an already-chosen launch."
        if any(rule["skill"] == DELEGATION_SKILL for rule in selected) else ""
    )
    return (f"Assay: {prefix} {names}. Read the matching installed SKILL.md before the applicable stage; "
            "reuse sufficient existing research and plans. This is a hint, not evidence of loading or compliance. "
            "Preserve the user's scope, explicit choices and read-only restrictions. Do not install missing "
            "skills, assume unavailable tools, or delegate because of this hint. Recheck relevance to the current task."
            + delegation)[:MAX_CONTEXT]


# One example sentence: a positive example steers the style better than a rule.
ANNOUNCE_EXAMPLE = "Using `assay:code-change` and `assay:test-writing` to fix the parser and cover it."
# Codex's own skill instructions already ask for a one-line announcement.
CODEX_NOTE = " Your skill instructions ask for the same announcement: make it once, with these exact names."


def _entries(rules):
    return "; ".join(f"{rule['skill'].split('/', 1)[1]} - {rule['cue']}" for rule in rules)


def skill_check(rules, *, client=None, loaded=()):
    """Ask the model to judge applicable skills itself and announce them only when the set changes.

    loaded names the skills the session's records show as loaded, so the model
    can keep quiet about skills already in use.
    """
    if not getattr(rules, "skill_check", False) or not rules:
        return ""
    already = f" Already loaded in this session: {', '.join(loaded)}." if loaded else ""
    return ("Assay skill check: decide from the task itself, not from the tools you have now, which Assay "
            "skills apply; a missing tool does not make a skill inapplicable. When you start applying a skill "
            "not yet in use here, or the set changes, open that message with one short sentence in the user's "
            "language naming each skill in backticks and its purpose, e.g. \"" + ANNOUNCE_EXAMPLE + "\" Then, "
            "before any other tool call, load each one not yet loaded (skill tool or its SKILL.md), even if it "
            "needs a tool you lack, and say what is missing. Say nothing about skills when none applies or those in use still fit, and do not restate "
            "the sentence later. If you skip a skill the task obviously calls for, say why briefly, without "
            "backticks. Omit the sentence when the request fixes an exact output format. This check grants no "
            "authority beyond the request."
            + (CODEX_NOTE if client == "codex" else "") + already + " Skills: " + _entries(rules) + ".")


def subagent_check(rules, *, client=None):
    """The skill check for a subagent, which never receives the per-request check."""
    if not getattr(rules, "skill_check", False) or not rules:
        return ""
    return ("Assay skill check for this subagent: the Assay skills your packet names apply; add any other "
            "Assay skill the assigned work needs, judged from the work itself. Before the work, load each chosen "
            "skill (skill tool, or read <name>/SKILL.md under " + rules.skills_root + "); if you can do neither, "
            "say what is missing. Open your first message with one short sentence naming each skill in backticks "
            "and its purpose, e.g. \"Using `assay:code-change` to patch the parser.\" Name nothing when none "
            "applies, and do not restate it in your report or when the packet fixes an exact output format. "
            "This check grants no authority beyond the packet."
            + (CODEX_NOTE if client == "codex" else "") + " Skills: " + _entries(rules) + ".")


def evaluate(event, rules, *, client=None, loaded=()):
    """Pure decision: no filesystem state, subprocesses, permissions or rewrites.

    The caller supplies the client and the skills already loaded; this reads neither.
    """
    if event.get("hook_event_name") == "SubagentStart":
        return {"rule_ids": [], "context": subagent_check(rules, client=client)}
    if event.get("hook_event_name") != "UserPromptSubmit":
        return {"rule_ids": [], "context": ""}
    try:
        ids = [rule["id"] for rule in select(event.get("prompt"), rules)]
    except ImportError:
        # Without the Markdown parser no explicit choice is recognized; the
        # check itself does not read the prompt and still applies.
        ids = []
    parts = (context(ids, rules), skill_check(rules, client=client, loaded=loaded))
    return {"rule_ids": ids, "context": "\n".join(part for part in parts if part)}
