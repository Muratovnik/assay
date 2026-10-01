"""English model-facing hints selected from multilingual user input.

Matching a request language never localizes the instruction or the user reply.
No model calls, tool calls or permissions.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import tomllib

MAX_PROMPT = 16_384
MAX_CONTEXT = 900
DELEGATION_SKILL = "skill/route-subagents"
SKILL_NAME = re.compile(r"(?:\$|/assay:|assay:)?([a-z][a-z0-9-]{0,63})(?![\w-])")
EXPLAIN = re.compile(r"^(?:what|how|why|explain|что|как|почему|объясни|расскажи|не\b|do not\b|don't\b)", re.I)


def load_rules(root: Path, *, disabled_rules=(), disabled_skills=()):
    catalog = tomllib.loads((root / "catalog.toml").read_text(encoding="utf-8"))
    document = tomllib.loads((root / "hooks/activation-rules.toml").read_text(encoding="utf-8"))
    if set(document) != {"schema", "rules"} or document["schema"] != 1 or not isinstance(document["rules"], list):
        raise ValueError("invalid activation rule document")
    assets = {asset["id"]: asset for asset in catalog["assets"] if asset["kind"] == "skill"}
    rules, seen, content, represented = [], set(), [], set()
    for item in document["rules"]:
        if not isinstance(item, dict) or set(item) != {"id", "skill", "priority", "patterns"}:
            raise ValueError("invalid activation rule")
        if not isinstance(item["id"], str) or not isinstance(item["skill"], str) or item["id"] in seen:
            raise ValueError("invalid or duplicate activation rule")
        if not re.fullmatch(r"[a-z][a-z0-9-]{0,63}", item["id"]) or item["skill"] not in assets:
            raise ValueError("activation rule references unknown catalog skill")
        if type(item["priority"]) is not int or not 0 <= item["priority"] <= 1000:
            raise ValueError("invalid rule priority")
        if not isinstance(item["patterns"], list) or not 1 <= len(item["patterns"]) <= 8:
            raise ValueError("invalid rule patterns")
        for pattern in item["patterns"]:
            if not isinstance(pattern, str) or not pattern.startswith("^") or len(pattern) > 400:
                raise ValueError("rules must have bounded, anchored patterns")
            re.compile(pattern)
        seen.add(item["id"])
        represented.add(item["skill"])
        path = (root / assets[item["skill"]]["path"] / "SKILL.md").resolve()
        if not path.is_relative_to(root.resolve()):
            raise ValueError("skill escapes installed plugin")
        if not path.is_file() or item["id"] in disabled_rules or item["skill"] in disabled_skills:
            continue
        content.append((item["skill"], hashlib.sha256(path.read_bytes()).hexdigest()))
        rules.append(dict(item))
    if len(seen) > 32 or set(disabled_rules) - seen or set(disabled_skills) - set(assets):
        raise ValueError("unknown disabled rule/skill or too many rules")
    # Explicit names come from the existing catalogue, not a second inventory.
    # They have no heuristic triggers and can never win ordinary classification.
    for identifier, asset in assets.items():
        if identifier in represented or identifier in disabled_skills:
            continue
        path = (root / asset["path"] / "SKILL.md").resolve()
        if not path.is_relative_to(root.resolve()):
            raise ValueError("skill escapes installed plugin")
        if path.is_file():
            rules.append({"id": "explicit:" + identifier, "skill": identifier, "priority": 0, "patterns": []})
            content.append((identifier, hashlib.sha256(path.read_bytes()).hexdigest()))
    fingerprint = hashlib.sha256(json.dumps([rules, content], sort_keys=True).encode()).hexdigest()
    return sorted(rules, key=lambda item: (-item["priority"], item["id"])), fingerprint


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
                parts.append(child.content if name and name[1] in known_names else " ")
            elif child.type in {"softbreak", "hardbreak"}:
                parts.append(" ")
        # Only the first actual request paragraph; a pasted second document
        # cannot activate another workflow after an explanatory first paragraph.
        return " ".join("".join(parts).split()).strip()
    return ""


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


def delegation_hint(text, rules):
    """Recognize a request modifier, not a downstream workflow or permission."""
    # CommonMark has already removed code and block quotations. Mask prose
    # quotations as well; an unmatched quote is too ambiguous for this hint.
    quoted = r"\"[^\"]*\"|«[^»]*»|“[^”]*”|(?<!\w)'[^']*'(?!\w)"
    text = re.sub(quoted, " ", text)
    if re.search(r"[\"«»“”]|(?<!\w)'|'(?!\w)", text):
        return None
    negative = (
        r"\b(?:do not|don't|never|avoid|without|no)\s+"
        r"(?:(?:use|using|spawn|spawning|launch|launching)\s+)?"
        r"(?:(?:any|more|new)\s+)?(?:sub[- ]?)?agents?\b|"
        r"\b(?:не\s+(?:используй|запускай|подключай)|без)\s+(?:суб)?агент\w*\b"
    )
    if re.search(negative, text, re.I):
        return None
    # Only direct clauses in the first request paragraph are eligible. Do not
    # search arbitrary words in a pasted example or a subsequent document.
    clauses = re.split(r"[.;!?]\s+|\s+(?:and|и)\s+", text, flags=re.I)
    return next((rule for rule in rules if rule["skill"] == DELEGATION_SKILL
                 and any(not EXPLAIN.match(clause.strip())
                         and re.search(pattern, clause.strip(), re.I)
                         for clause in clauses for pattern in rule["patterns"])), None)


def select(prompt, rules):
    names = {rule["skill"].split("/", 1)[1] for rule in rules}
    text = request_text(prompt, names)
    if not text or EXPLAIN.match(text) or text.startswith(('"', "'", "«", "“")):
        return []
    # Explicit catalog choices retain priority. An ordinary "use subagents"
    # request is not an unknown skill name and must reach modifier selection.
    selected = explicit_selection(text, rules)
    if not selected:
        selected = next(([rule] for rule in rules if rule["skill"] != DELEGATION_SKILL
                         and any(re.search(pattern, text, re.I) for pattern in rule["patterns"])), [])
    # Keep the first applicable workflow; delegation complements it rather than
    # injecting implementation/review stages that are not ready yet.
    modifier = delegation_hint(text, rules)
    if modifier and modifier not in selected and len(selected) < 2:
        selected.append(modifier)
    return selected


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


def evaluate(event, rules):
    """Pure decision: no filesystem state, subprocesses, permissions or rewrites."""
    if event.get("hook_event_name") != "UserPromptSubmit":
        return {"rule_ids": [], "context": ""}
    selected = select(event.get("prompt"), rules)
    ids = [rule["id"] for rule in selected]
    return {"rule_ids": ids, "context": context(ids, rules)}
