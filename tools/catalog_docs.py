"""Render/check only the marked catalog block in the active architecture document."""
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


def check(root: Path) -> bool:
    path = root / DOCUMENT
    text = path.read_text(encoding="utf-8")
    return text == updated(text, aa.load_catalog(root))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=aa.ROOT)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--write", action="store_true")
    args = parser.parse_args()
    try:
        path = args.root / DOCUMENT
        if path.is_symlink():
            raise ValueError("refusing a linked architecture document")
        text = path.read_text(encoding="utf-8")
        candidate = updated(text, aa.load_catalog(args.root))
        if args.write:
            if text != candidate:
                path.write_text(candidate, encoding="utf-8", newline="\n")
            print("catalog document: synchronized")
            return 0
        if text != candidate:
            print("catalog document: stale; run python tools/catalog_docs.py --write", file=sys.stderr)
            return 1
        print("catalog document: PASS")
        return 0
    except (OSError, ValueError) as error:
        print(f"catalog document: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
