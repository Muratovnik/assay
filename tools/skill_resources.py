"""Validate Markdown references in source and copied skill selections.

CommonMark parsing belongs to markdown-it-py. This module owns only Assay's
resource-boundary policy, not an installer, dependency resolver or renderer.
"""
from __future__ import annotations

import os
import shutil
import stat
import tempfile
from html.parser import HTMLParser
from pathlib import Path, PurePosixPath
from urllib.parse import unquote, urlsplit

if __package__:
    from .asset_formats import ContractError, FRONTMATTER, frontmatter
else:
    from asset_formats import ContractError, FRONTMATTER, frontmatter

OPTIONAL_SKILLS = "assay-optional-skills"


class _HTMLReferences(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.targets: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        wanted = {"a": "href", "img": "src"}.get(tag)
        if wanted:
            self.targets.extend(
                value for key, value in attrs if key == wanted and value is not None
            )


def markdown_targets(text: str) -> list[str]:
    """Extract real links, excluding examples inside code spans and fences."""
    try:
        from markdown_it import MarkdownIt
    except ImportError as error:
        raise ContractError(
            "Markdown validation requires markdown-it-py; install "
            "requirements-tools.txt in your tooling environment"
        ) from error
    match = FRONTMATTER.match(text)
    if match:
        text = text[match.end():]
    result: list[str] = []
    pending = list(MarkdownIt("commonmark").parse(text))
    while pending:
        token = pending.pop()
        attribute = {"link_open": "href", "image": "src"}.get(token.type)
        if attribute:
            target = token.attrGet(attribute)
            if target is not None:
                result.append(target)
        elif token.type in {"html_inline", "html_block"}:
            parser = _HTMLReferences()
            parser.feed(token.content)
            parser.close()
            result.extend(parser.targets)
        pending.extend(token.children or [])
    return result


def local_target(target: str) -> str | None:
    parsed = urlsplit(target)
    if parsed.scheme in {"http", "https", "mailto"} or (
        parsed.netloc and not parsed.scheme
    ):
        return None
    if parsed.scheme:
        raise ValueError(f"unsupported resource scheme {parsed.scheme!r}")
    raw = unquote(parsed.path)
    if "\\" in raw or "\x00" in raw or PurePosixPath(raw).is_absolute():
        raise ValueError("resource paths must be relative POSIX paths without NUL")
    return raw or None


def markdown_problems(path: Path, root: Path) -> list[str]:
    problems: list[str] = []
    label = path.relative_to(root).as_posix()
    try:
        targets = markdown_targets(path.read_text(encoding="utf-8", errors="strict"))
    except (OSError, UnicodeError, ContractError) as error:
        return [f"{label}: {error}"]
    for target in targets:
        try:
            raw = local_target(target)
            if raw is not None:
                (path.parent / raw).resolve(strict=True).relative_to(root.resolve(strict=True))
        except (OSError, ValueError):
            problems.append(f"{label}: broken or out-of-root link {target!r}")
    return problems


def _plain_tree(path: Path) -> None:
    """Refuse links, reparse points and special files before reading/copying."""
    def inspect(item: Path) -> None:
        info = item.lstat()
        if stat.S_ISLNK(info.st_mode) or (
            getattr(info, "st_file_attributes", 0)
            & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
        ):
            raise ContractError(f"linked resource is unsupported: {item.name}")
        if not (stat.S_ISREG(info.st_mode) or stat.S_ISDIR(info.st_mode)):
            raise ContractError(f"non-regular resource is unsupported: {item.name}")

    inspect(path)
    for current, directories, files in os.walk(path, followlinks=False):
        for name in directories + files:
            inspect(Path(current) / name)


def selection_problems(skills_root: Path, known: set[str]) -> list[str]:
    """Check a copied layout; absence is allowed only for declared peers.

    This checks Markdown targets, not script imports, dynamic paths, fallback
    quality, client discovery or agent behavior.
    """
    problems: list[str] = []
    try:
        _plain_tree(skills_root)
        boundary = skills_root.resolve(strict=True)
        skills = sorted(path for path in skills_root.iterdir() if path.is_dir())
        if not skills or any(skill.name not in known for skill in skills):
            raise ContractError("selection must contain known skills")
    except (OSError, ContractError) as error:
        return [str(error)]
    for skill in skills:
        try:
            metadata = frontmatter(skill / "SKILL.md").get("metadata", {})
            if not isinstance(metadata, dict):
                raise ContractError("metadata must be an object")
            declared = metadata.get(OPTIONAL_SKILLS, "")
            if not isinstance(declared, str):
                raise ContractError(f"{OPTIONAL_SKILLS} must be a string")
            optional = declared.split()
            if len(optional) != len(set(optional)) or set(optional) - (known - {skill.name}):
                raise ContractError(f"{OPTIONAL_SKILLS} contains duplicate, unknown or self dependencies")
            used: set[str] = set()
            for path in sorted(skill.rglob("*.md")):
                if "evals" in path.relative_to(skill).parts:
                    continue
                for target in markdown_targets(path.read_text(encoding="utf-8", errors="strict")):
                    try:
                        raw = local_target(target)
                        if raw is None:
                            continue
                        resolved = (path.parent / raw).resolve(strict=False)
                        relative = resolved.relative_to(boundary)
                        peer = relative.parts[0] if relative.parts else ""
                        if peer != skill.name:
                            if peer not in optional:
                                raise ValueError("undeclared cross-skill resource")
                            used.add(peer)
                            if not (skills_root / peer).exists():
                                continue
                        if not resolved.exists():
                            raise ValueError("missing required resource")
                    except (OSError, ValueError) as error:
                        problems.append(
                            f"{path.relative_to(skills_root)}: unavailable packaged resource {target!r}: {error}"
                        )
            if set(optional) - used:
                problems.append(f"{skill.name}: unused optional declarations: {', '.join(sorted(set(optional) - used))}")
        except (ContractError, OSError, UnicodeError) as error:
            problems.append(f"{skill.name}: {error}")
    return problems


def distribution_problems(sources: list[Path]) -> list[str]:
    """Check the collection and every singleton copy without installing it."""
    known = {source.name for source in sources}
    if not sources or len(known) != len(sources):
        return ["distribution: expected distinct, non-empty skill sources"]
    try:
        for source in sources:
            _plain_tree(source)
        problems: list[str] = []
        for selected in [sources] + [[source] for source in sources]:
            with tempfile.TemporaryDirectory(prefix="assay-skill-copy-") as directory:
                copied = Path(directory) / "skills"
                copied.mkdir()
                for source in selected:
                    shutil.copytree(source, copied / source.name, symlinks=True)
                label = "collection" if len(selected) > 1 else selected[0].name
                problems.extend(
                    f"distribution ({label}): {problem}"
                    for problem in selection_problems(copied, known)
                )
        return sorted(set(problems))
    except (OSError, ValueError, ContractError) as error:
        return [f"distribution: {error}"]
