"""Vendor guidance: deterministic section extraction from official documentation.

Quoted publisher material only. No summarizing model, no paid call, and no
rewriting: the caller reads the publisher's own words with their provenance.
Caveats are never dropped by shortening; a missing section is an explicit drift
error, because silently returning a guide without its exceptions is worse than
returning nothing.
"""
from __future__ import annotations

import re

from .core import EvidenceError, digest, identity, text, validate_guide_applicability

EXTRACTOR_VERSION = 2
MAX_EXCERPT = 1500
MAX_CAVEAT = 800
MAX_CAVEATS = 6
MAX_SECTIONS = 4

FENCE = re.compile(r"^\s*(```|~~~)")
HEADING = re.compile(r"^(#{1,4})\s+(\S.*?)\s*$")
CALLOUT = re.compile(r"<(Note|Warning|Tip|Info|Danger|Check)>(.*?)</\1>", re.S)
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
    lines, fenced, found = body.splitlines(), False, []
    for index, line in enumerate(lines):
        if FENCE.match(line):
            fenced = not fenced
            continue
        if fenced:
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
        return "\n".join(lines[start + 1:end]).strip()
    return None


def preamble(body):
    """Everything above the first section heading."""
    lines, found = outline(body)
    first = next((start for level, _, start in found if level >= 2), len(lines))
    return chr(10).join(lines[:first])


def callouts(value):
    """Publisher warnings and notes, kept whole and separate from the prose."""
    found = []
    for match in CALLOUT.finditer(value):
        inner = " ".join(match.group(2).split())
        if inner:
            found.append({"kind": match.group(1).lower(), "text": inner[:MAX_CAVEAT],
                          "truncated": len(inner) > MAX_CAVEAT})
    return found[:MAX_CAVEATS], CALLOUT.sub("", value)


def drop_code(value):
    kept, fenced, blocks = [], False, 0
    for line in value.splitlines():
        if FENCE.match(line):
            fenced = not fenced
            blocks += 1 if fenced else 0
            continue
        if not fenced:
            kept.append(line)
    return "\n".join(kept), blocks


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
