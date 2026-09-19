"""Render/check the marked catalog block in every document that carries it.

A document opts in by containing the marker pair, so a translated architecture
page is held to the same inventory as the English one instead of drifting into
a copy nobody regenerates.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

if __package__:
    from . import assay as aa
else:
    import assay as aa

DOCUMENT = Path("docs/architecture.md")
BEGIN = "<!-- assay:catalog:start -->"
END = "<!-- assay:catalog:end -->"


def render(catalog: aa.Catalog) -> str:
    lines = [BEGIN, "", "<!-- Generated from catalog.toml by tools/catalog_docs.py; do not edit this block. -->",
             "| Asset | Activation | Codex target | Claude target |",
             "| --- | --- | --- | --- |"]
    for asset in catalog.assets:
        targets = {item.client: f"~/{aa.ROOT_LAYOUT[item.root].as_posix()}/{item.path}"
                   for item in asset.projections}
        lines.append(f"| `{asset.id}` | {asset.activation} | `{targets['codex']}` | `{targets['claude']}` |")
    return "\n".join([*lines, "", END])


def updated(text: str, catalog: aa.Catalog) -> str:
    if text.count(BEGIN) != 1 or text.count(END) != 1:
        raise ValueError("architecture document requires exactly one catalog marker pair")
    start, end = text.index(BEGIN), text.index(END)
    if end < start:
        raise ValueError("catalog markers are reversed")
    return text[:start] + render(catalog) + text[end + len(END):]


def documents(root: Path) -> list[Path]:
    """Every Markdown document under docs/ that carries the marker pair.

    The English page is required: a run that found nothing to check must not
    report success just because a path moved.
    """
    found = []
    for path in sorted((root / "docs").rglob("*.md")):
        if BEGIN not in path.read_text(encoding="utf-8"):
            continue
        if path.is_symlink():
            raise ValueError(f"refusing a linked catalog document: {path.name}")
        found.append(path)
    if (root / DOCUMENT) not in found:
        raise ValueError(f"{DOCUMENT.as_posix()} carries no catalog marker pair")
    return found


def check(root: Path) -> bool:
    catalog = aa.load_catalog(root)
    for path in documents(root):
        text = path.read_text(encoding="utf-8")
        if text != updated(text, catalog):
            return False
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=aa.ROOT)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--write", action="store_true")
    args = parser.parse_args()
    try:
        catalog = aa.load_catalog(args.root)
        stale: list[str] = []
        for path in documents(args.root):
            text = path.read_text(encoding="utf-8")
            candidate = updated(text, catalog)
            if text == candidate:
                continue
            if args.write:
                path.write_text(candidate, encoding="utf-8", newline="\n")
            else:
                stale.append(path.relative_to(args.root).as_posix())
        if args.write:
            print("catalog document: synchronized")
            return 0
        if stale:
            print(f"catalog document: stale ({', '.join(stale)}); "
                  "run python tools/catalog_docs.py --write", file=sys.stderr)
            return 1
        print("catalog document: PASS")
        return 0
    except (OSError, ValueError) as error:
        print(f"catalog document: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
