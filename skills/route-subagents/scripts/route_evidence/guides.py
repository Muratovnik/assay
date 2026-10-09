"""Vendor guidance: deterministic section extraction from official documentation.

Quoted publisher material only. No summarizing model, no paid call, and no
rewriting: the caller reads the publisher's own words with their provenance.
Caveats are never dropped by shortening; a missing section is an explicit drift
error, because silently returning a guide without its exceptions is worse than
returning nothing.
"""
from __future__ import annotations

import re
from bisect import bisect_right

from .core import EvidenceError, digest, identity, text, validate_guide_applicability

EXTRACTOR_VERSION = 4
MAX_EXCERPT = 1500
MAX_CAVEAT = 800
MAX_CAVEATS = 6
MAX_SECTIONS = 4

FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")
QUOTE = re.compile(r"^ {0,3}> ?")
LIST_ITEM = re.compile(r"^( *)(?:[-+*]|\d{1,9}[.)]) +(.*)$")
HEADING = re.compile(r"^(#{1,4})\s+(\S.*?)\s*$")
CALLOUT_TAG = re.compile(r"<(/?)(Note|Warning|Tip|Info|Danger|Check)>")
QUOTED_MARKER = re.compile(r"`+|<!--")
FRONTMATTER = re.compile(r"\A---\r?\n(.*?)\r?\n---\r?\n", re.S)


def guide(gid, publisher, clients, url, sections, *, page_url=None,
          models=(), surfaces=("api",), conditions=(), reviewed_on=None):
    applicability = validate_guide_applicability({
        "models": list(models), "surfaces": list(surfaces),
        "conditions": list(conditions), "reviewed_on": reviewed_on})
    return {"id": gid, "kind": "guide", "adapter": "guide", "publisher": publisher,
            "clients": tuple(clients), "url": url, "page_url": page_url or url.removesuffix(".md"),
            "sections": tuple(sections), "extractor_version": EXTRACTOR_VERSION,
            "applicability": applicability}


# Canonical addresses: the documentation domains redirect across hosts, and the
# fetcher refuses cross-host redirects, so the final address is registered here.
GUIDES = {g["id"]: g for g in (
    guide("openai-reasoning", "OpenAI", ("codex",),
          "https://developers.openai.com/api/docs/guides/reasoning.md",
          ("Reasoning effort", "Controlling costs")),
    guide("claude-thinking", "Anthropic", ("claude",),
          "https://platform.claude.com/docs/en/build-with-claude/thinking.md",
          ("Thinking and effort", "Configuring thinking")),
    guide("claude-model-choice", "Anthropic", ("claude",),
          "https://platform.claude.com/docs/en/about-claude/models/choosing-a-model.md",
          ("Establish key criteria", "Model selection matrix")),
    guide("openai-gpt-6", "OpenAI", ("codex",),
          "https://developers.openai.com/api/docs/guides/latest-model.md",
          ("Limitations", "Update API and model parameters"),
          models=("gpt-6-astra", "gpt-6-sol", "gpt-6-luna"),
          conditions=("API migration guidance; native client controls need separate verification.",
                      "Model-specific exceptions inside the selected sections still apply."),
          reviewed_on="2026-09-22"),
    guide("openai-gpt-6-astra-skills", "OpenAI", ("codex",),
          "https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra.md",
          ("Better skills", "Up-to-date AGENTS.md"), models=("gpt-6-astra",),
          surfaces=("codex",),
          conditions=("Astra-specific observations do not establish behavior on Sol or Luna.",
                      "Instruction changes need a task-specific comparison, not blanket removal of checks."),
          reviewed_on="2026-09-22"),
    guide("claude-opus-5-5", "Anthropic", ("claude",),
          "https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5-5.md",
          ("Calibrate effort", "Unattended agentic runs"), models=("claude-opus-5-5",),
          conditions=("API and harness guidance; verify controls exposed by the active native client.",
                      "A turn ending is not a delivery receipt; continuation remains bounded by task authority.",
                      "Vendor effort guidance is not a measured saving on this workload or subscription."),
          reviewed_on="2026-09-22"),
)}


def matching_models(applicability, available):
    """Resolve only declared identities; null scope/inventory stays unknown."""
    if applicability is None or available is None:
        return None
    wanted = set(map(identity, applicability["models"]))
    return sorted(item["model"] for item in available
                  if not wanted or wanted.intersection(
                      identity(name) for name in [item["model"], *item.get("evidence_names", [])]))


def guide_ids(client=None, available=None):
    """Select registered scope using only caller-confirmed model identities.

    None means a catalog/status query. A supplied inventory filters scoped
    guides; unknown aliases never imply a family, version or provider binding.
    An empty model selector means no extra model restriction, not universal
    support for every API capability mentioned in the document.
    """
    return sorted(g["id"] for g in GUIDES.values()
                  if (client is None or client in g["clients"])
                  and (available is None or not g["applicability"]["models"]
                       or matching_models(g["applicability"], available)))


def anchor(heading):
    return "-".join(re.findall(r"[a-z0-9]+", heading.lower()))


def outline(body):
    """Headings with their line spans, ignoring anything inside a code fence."""
    lines, found = body.splitlines(), []
    code, _ = code_lines(lines)
    for index, line in enumerate(lines):
        if code[index]:
            continue
        match = HEADING.match(line)
        if match:
            found.append((len(match.group(1)), match.group(2), index))
    return lines, found


def section_text(body, heading):
    """The named section, including its subsections, or None when absent."""
    lines, found = outline(body)
    for position, (level, title, start) in enumerate(found):
        if title != heading:
            continue
        end = len(lines)
        for other_level, _, other_start in found[position + 1:]:
            if other_level <= level:
                end = other_start
                break
        return "\n".join(lines[start + 1:end]).strip("\r\n")
    return None


def preamble(body):
    """Everything above the first section heading."""
    lines, found = outline(body)
    first = next((start for level, _, start in found if level >= 2), len(lines))
    return chr(10).join(lines[:first])


def callouts(value):
    """Publisher warnings and notes, kept whole and separate from the prose."""
    lines = value.splitlines(keepends=True)
    code, _ = code_lines([line.rstrip("\r\n") for line in lines])
    starts, position = [], 0
    for line in lines:
        starts.append(position)
        position += len(line)
    quoted, comments = quoted_spans(value, lines, starts, code)
    quoted_starts = [start for start, _ in quoted]
    found, spans, stack = [], list(comments), []
    for match in CALLOUT_TAG.finditer(value):
        quoted_index = bisect_right(quoted_starts, match.start()) - 1
        if (code[bisect_right(starts, match.start()) - 1] or escaped(value, match.start())
                or (quoted_index >= 0 and match.start() < quoted[quoted_index][1])):
            continue
        closing, kind = match.groups()
        if not closing:
            if not stack:
                opening = match
            stack.append(kind)
        elif stack:
            if stack.pop() != kind:
                raise EvidenceError("guide_callout_nesting_changed")
            if stack:
                continue
            # Keep the raw inner span, including code and its whitespace. A
            # fenced closing-tag example must not end this actual callout.
            inner = value[opening.end():match.start()].strip()
            if inner:
                if len(inner) > MAX_CAVEAT:
                    raise EvidenceError("guide_caveat_size_limit_exceeded")
                found.append({"kind": kind.lower(), "text": inner, "truncated": False})
            spans.append((opening.start(), match.end()))
    if stack:
        raise EvidenceError("guide_callout_unclosed")
    if len(found) > MAX_CAVEATS:
        raise EvidenceError("guide_caveat_count_limit_exceeded")
    kept, previous = [], 0
    for start, end in sorted(spans):
        if start > previous:
            kept.append(value[previous:start])
        previous = max(previous, end)
    return found, "".join(kept) + value[previous:]


def escaped(value, position):
    before = position
    while before and value[before - 1] == "\\":
        before -= 1
    return (position - before) % 2 == 1


def quoted_spans(value, lines, starts, code):
    """Source offsets keep literal tags distinct without rewriting real caveats."""
    markers = [match for match in QUOTED_MARKER.finditer(value)
               if not code[bisect_right(starts, match.start()) - 1]]
    next_tick, latest = {}, {}
    for match in reversed(markers):
        if match[0][0] == "`":
            next_tick[match.start()] = latest.get(len(match[0]))
            latest[len(match[0])] = match
    # Inline spans cannot cross a paragraph, heading or fenced/indented block.
    boundaries = [start for line, start, blocked in zip(lines, starts, code)
                  if blocked or not line.strip() or HEADING.match(line)]
    spans, comments, position = [], [], 0
    for match in markers:
        if match.start() < position or escaped(value, match.start()):
            continue
        if match[0] == "<!--":
            end = value.find("-->", match.end())
            if end < 0:
                raise EvidenceError("guide_comment_unclosed")
            position = end + 3
            comments.append((match.start(), position))
        else:
            closing = next_tick[match.start()]
            boundary = bisect_right(boundaries, match.start())
            if closing is None or (boundary < len(boundaries) and boundaries[boundary] < closing.start()):
                continue
            position = closing.end()
        spans.append((match.start(), position))
    return spans, comments


def quote_content(line, maximum=None):
    depth = 0
    while maximum is None or depth < maximum:
        quote = QUOTE.match(line)
        if not quote:
            break
        line = line[quote.end():]
        depth += 1
    return line, depth


def code_lines(lines):
    """Mask code in the configured Markdown excerpts, retaining container bounds."""
    code, opening, blocks = [], None, 0
    list_indents, quote_depth, indented, paragraph = [], 0, False, False
    for raw in lines:
        line = raw.expandtabs(4)
        if opening is not None:
            marker, depth, base = opening
            body, observed_depth = quote_content(line, depth)
            indentation = len(body) - len(body.lstrip(" "))
            if observed_depth == depth and (not body.strip() or indentation >= base):
                code.append(True)
                fence = FENCE.match(body[base:])
                if (fence and fence[1][0] == marker[0] and len(fence[1]) >= len(marker)
                        and not fence[2].strip()):
                    opening = None
                continue
            # A fenced block cannot continue outside its quote/list container.
            opening, list_indents, paragraph = None, [], False
        body, depth = quote_content(line)
        if depth != quote_depth:
            list_indents, indented, paragraph = [], False, False
        quote_depth = depth
        indentation = len(body) - len(body.lstrip(" "))
        item = LIST_ITEM.match(body)
        container = next((level for level in reversed(list_indents) if level <= indentation), 0)
        if indentation - container >= 4:
            item = None
        if item:
            while list_indents and len(item[1]) < list_indents[-1]:
                list_indents.pop()
            base = item.start(2)
            list_indents.append(base)
            body = body[base:]
        else:
            if body.strip():
                while list_indents and indentation < list_indents[-1]:
                    list_indents.pop()
            base = list_indents[-1] if list_indents else 0
            body = body[base:]
        fence = FENCE.match(body)
        if fence and (fence[1][0] != "`" or "`" not in fence[2]):
            opening = (fence[1], depth, base)
            blocks += 1
            indented, paragraph = False, False
            code.append(True)
        elif (body.startswith("    ") and (indented or not paragraph)) or (indented and not body.strip()):
            blocks += not indented
            indented, paragraph = True, False
            code.append(True)
        else:
            indented = False
            paragraph = bool(body.strip()) and HEADING.match(body) is None
            code.append(False)
    return code, blocks


def drop_code(value):
    lines = value.splitlines()
    code, blocks = code_lines(lines)
    return "\n".join(line for line, omitted in zip(lines, code) if not omitted), blocks


def condense(value):
    return re.sub(r"\n{3,}", "\n\n", value).strip()


def trim(value):
    """Shorten prose only, on a paragraph boundary, and say that it happened."""
    if len(value) <= MAX_EXCERPT:
        return value, False
    cut = value.rfind("\n\n", 0, MAX_EXCERPT)
    return value[:cut if cut > MAX_EXCERPT // 2 else MAX_EXCERPT].rstrip(), True


def front_matter(body):
    match = FRONTMATTER.match(body)
    fields = {}
    if not match:
        return fields, body
    for line in match.group(1).splitlines():
        key, _, value = line.partition(":")
        if _ and key.strip() in ("title", "url"):
            fields[key.strip()] = value.strip().strip('"').strip("'")
    return fields, body[match.end():]


def guide_snapshot(source: dict, body: str) -> dict:
    if source["extractor_version"] != EXTRACTOR_VERSION:
        raise EvidenceError("guide extractor version mismatch")
    fields, content = front_matter(body)
    title = fields.get("title")
    if not title:
        _, found = outline(content)
        title = next((heading for level, heading, _ in found if level == 1), None)
    if not title:
        raise EvidenceError("guide_document_title_missing: " + source["id"])
    canonical = fields.get("url") or source["page_url"]
    if not canonical.startswith("https://"):
        raise EvidenceError("guide canonical url must use HTTPS")
    # Page-level warnings sit above the first section (deprecations, model
    # applicability). Selecting sections must not silently drop them.
    document_caveats, _ = callouts(preamble(content))
    sections = []
    for heading in source["sections"][:MAX_SECTIONS]:
        raw = section_text(content, heading)
        if raw is None:
            # Layout drift must fail loudly: a quietly missing section would
            # remove the publisher's exceptions without anyone noticing.
            raise EvidenceError("guide_section_missing: %s/%s" % (source["id"], heading))
        caveats, prose = callouts(raw)
        prose, blocks = drop_code(prose)
        excerpt, truncated = trim(condense(prose))
        sections.append({"section": heading, "anchor": anchor(heading),
                         "url": canonical + "#" + anchor(heading), "excerpt": excerpt,
                         "characters": len(excerpt), "truncated": truncated,
                         "code_blocks_omitted": blocks, "caveats": caveats})
    return {"schema_version": 1, "guide_id": source["id"], "publisher": source["publisher"],
            "source_url": source["url"], "document_title": text(title, "guide title"),
            "canonical_url": canonical, "extractor_version": EXTRACTOR_VERSION,
            "content_hash": digest(body), "applies_to": list(source["clients"]),
            "applicability": validate_guide_applicability(source["applicability"]),
            "document_caveats": document_caveats, "retrieved_sections": sections}
