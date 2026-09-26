"""Read-only fingerprints of explicitly named UI sources; no discovery or installation."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path, PurePosixPath
from typing import Sequence


def inspect_sources(root: Path, sources: Sequence[str]) -> list[dict[str, str]]:
    """Validate role=relative/path inputs and report identities, never file contents.

    This verifies paths/bytes, not that a source is authoritative or semantically current.
    The caller chooses existing sources; no required DESIGN.md or new index is created.
    """
    root = root.resolve(strict=True)
    if not root.is_dir() or not sources:
        raise ValueError('an existing project directory and at least one source are required')
    result = []
    seen = set()
    for source in sources:
        role, separator, relative = source.partition('=')
        if not separator or not re.fullmatch(r'[a-z][a-z0-9-]*', role):
            raise ValueError('source must be role=relative/path with a lowercase role')
        parts = relative.split('/')
        if not relative or '\\' in relative or ':' in relative or any(p in {'', '.', '..'} for p in parts):
            raise ValueError(f'{role}: expected a normalized project-relative file')
        path = PurePosixPath(relative)
        if path.is_absolute() or any(p in {'.git', 'node_modules'} or p.startswith('.env') for p in parts):
            raise ValueError(f'{role}: unsupported source path')
        if (role, relative) in seen:
            raise ValueError(f'{role}: duplicate source')
        seen.add((role, relative))
        target = root
        for part in parts:
            target = target / part
            if target.is_symlink():
                raise ValueError(f'{role}: symlink sources are not followed')
        if not target.is_file():
            raise ValueError(f'{role}: source does not exist or is not a regular file: {relative}')
        # Resolve again to guard ordinary path mistakes; not a race-proof sandbox.
        if not target.resolve(strict=True).is_relative_to(root):
            raise ValueError(f'{role}: source escapes project root')
        with target.open('rb') as stream:
            digest = hashlib.file_digest(stream, 'sha256').hexdigest()
        result.append({'role': role, 'path': relative, 'sha256': digest})
    return result


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--source', action='append', required=True, help='existing role=relative/path; repeat as needed')
    args = parser.parse_args(argv)
    try:
        records = inspect_sources(args.root, args.source)
    except (OSError, ValueError) as error:
        parser.exit(2, f'ui-context: {error}\n')
    print(json.dumps({'sources': records}, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
