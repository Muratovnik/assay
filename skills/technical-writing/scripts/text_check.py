"""Read-only structural preservation check for an edited Markdown document.

Compares a `before` and an `after` file and reports whether the regions an edit
must not touch are still identical. It reads two files and nothing else: it
writes no file, runs no command found in the text, calls no model and opens no
network connection. Structural preservation is not semantic equivalence.
"""
from __future__ import annotations

import argparse
import bisect
import json
import re
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence

FENCE = re.compile(r'^(?P<indent>[ \t]*)(?P<fence>`{3,}|~{3,})(?P<info>.*)$')
CODE_RUN = re.compile(r'`+')
LINK = re.compile(
    r'!?\[(?:[^\]\\]|\\.)*\]\([ \t]*(<[^<>\n]*>|[^\s()]*)'
    r'(?:[ \t]+(?:"[^"\n]*"|\'[^\'\n]*\'|\([^()\n]*\)))?[ \t]*\)')
DEFINITION = re.compile(r'^[ \t]{0,3}\[(?:[^\]\\]|\\.)+\]:[ \t]*(\S+)', re.MULTILINE)
AUTOLINK = re.compile(r'<(?:[A-Za-z][A-Za-z0-9+.\-]*:[^<>\s]*|[^<>\s@]+@[^<>\s]+)>')
LEFTOVER_LINK = re.compile(r'\](?:\(|:[ \t])')
INLINE_TAG = re.compile(r'<[/!?A-Za-z][^<>\n]*>')
ALERT = re.compile(r'^\[!.+?\]')
DIRECTIVE = re.compile(r'^(?::::|\{[{%])')
STATUS_ORDER = ('fail', 'unverified', 'warning', 'pass', 'not-applicable')
PROTECTED = {
    'copyedit': ('frontmatter', 'fenced_code', 'inline_code', 'link_destination',
                 'table_row', 'blockquote'),
    'rewrite': ('frontmatter', 'fenced_code', 'inline_code', 'link_destination'),
}


class InvalidInput(Exception):
    """The input could not be inspected at all; never reported as a result."""


@dataclass
class Region:
    """One extracted slice of source with the line it starts on."""

    text: str
    line: int


@dataclass
class Document:
    """Everything the comparison needs from one file."""

    endings: str
    frontmatter: list[Region] = field(default_factory=list)
    fenced_code: list[Region] = field(default_factory=list)
    inline_code: list[Region] = field(default_factory=list)
    link_destination: list[Region] = field(default_factory=list)
    table_row: list[Region] = field(default_factory=list)
    blockquote: list[Region] = field(default_factory=list)
    unverified: list[Region] = field(default_factory=list)
    unread_link: list[Region] = field(default_factory=list)

    def regions(self, kind: str) -> list[Region]:
        return getattr(self, kind)

    def unclassified(self) -> list[Region]:
        """Every construct this scanner declined to judge, in source order."""
        return sorted(self.unverified + self.unread_link, key=lambda region: region.line)

    def inspected(self, kinds: Sequence[str]) -> int:
        return sum(len(self.regions(kind)) for kind in kinds)


def read_document(path: Path) -> tuple[str, str]:
    """Return decoded text and the file's line-ending style, or refuse the input."""
    try:
        raw = path.read_bytes()
    except OSError as error:
        raise InvalidInput(f'{path.name}: cannot be read ({error.strerror or error})') from error
    try:
        text = raw.decode('utf-8')
    except UnicodeDecodeError as error:
        raise InvalidInput(f'{path.name}: not valid UTF-8 at byte {error.start}') from error
    text = text.lstrip('﻿')
    if not text.strip():
        raise InvalidInput(f'{path.name}: empty, so there was nothing to inspect')
    crlf = raw.count(b'\r\n')
    lone_cr = raw.count(b'\r') - crlf
    lf = raw.count(b'\n') - crlf
    found = [name for name, count in (('crlf', crlf), ('lf', lf), ('cr', lone_cr)) if count]
    endings = found[0] if len(found) == 1 else ('mixed' if found else 'none')
    return text.replace('\r\n', '\n').replace('\r', '\n'), endings


def is_delimiter_row(line: str) -> bool:
    """A GFM table delimiter: at least two dash cells, nothing else."""
    if '|' not in line or '-' not in line:
        return False
    cells = [cell.strip() for cell in line.strip().strip('|').split('|')]
    return len(cells) >= 2 and all(re.fullmatch(r':?-+:?', cell) for cell in cells)


def _mask(text: str, spans: Sequence[tuple[int, int]]) -> str:
    """Blank out spans so a later scan cannot match inside them, keeping offsets."""
    characters = list(text)
    for start, end in spans:
        for index in range(start, end):
            if characters[index] != '\n':
                characters[index] = ' '
    return ''.join(characters)


def scan(text: str, endings: str, mode: str) -> Document:
    """Classify the source into protected regions and constructs it cannot judge.

    A kind the mode does not protect stays ordinary prose, so a command inside a
    table cell is still compared even where the table itself may be restructured.
    """
    lines = text.split('\n')
    starts = [0]
    for line in lines[:-1]:
        starts.append(starts[-1] + len(line) + 1)
    document = Document(endings=endings)
    blocked: list[tuple[int, int]] = []

    def slice_of(first: int, last: int) -> str:
        end = starts[last] + len(lines[last])
        return text[starts[first]:end]

    def take(target: list[Region], first: int, last: int, per_line: bool = False) -> None:
        if per_line:
            target.extend(Region(lines[n], n + 1) for n in range(first, last + 1))
        else:
            target.append(Region(slice_of(first, last), first + 1))
        blocked.append((starts[first], starts[last] + len(lines[last])))

    index = 0
    if lines and lines[0].rstrip() == '---':
        for end in range(1, len(lines)):
            if lines[end].rstrip() in {'---', '...'}:
                take(document.frontmatter, 0, end)
                index = end + 1
                break
    while index < len(lines):
        line = lines[index]
        stripped = line.strip()
        opener = FENCE.match(line)
        if opener and not (opener.group('fence')[0] == '`' and '`' in opener.group('info')):
            marker = opener.group('fence')
            closing = re.compile(r'^[ \t]*' + re.escape(marker[0]) + '{%d,}[ \t]*$' % len(marker))
            for end in range(index + 1, len(lines)):
                if closing.match(lines[end]):
                    take(document.fenced_code, index, end)
                    index = end + 1
                    break
            else:
                take(document.unverified, index, len(lines) - 1)
                index = len(lines)
            continue
        if '|' in line and index + 1 < len(lines) and is_delimiter_row(lines[index + 1]):
            end = index + 1
            while end + 1 < len(lines) and '|' in lines[end + 1] and lines[end + 1].strip():
                end += 1
            if 'table_row' in PROTECTED[mode]:
                take(document.table_row, index, end, per_line=True)
            index = end + 1
            continue
        if re.match(r'^[ \t]{0,3}>', line):
            end = index
            while end + 1 < len(lines) and re.match(r'^[ \t]{0,3}>', lines[end + 1]):
                end += 1
            body = re.sub(r'^[ \t]{0,3}>[ \t]?', '', line)
            if ALERT.match(body.strip()):
                quoted = [re.sub(r'^[ \t]{0,3}>[ \t]?', '', lines[n]) for n in range(index, end + 1)]
                if any(FENCE.match(one) for one in quoted):
                    take(document.unverified, index, end)
            elif 'blockquote' in PROTECTED[mode]:
                take(document.blockquote, index, end)
            index = end + 1
            continue
        at_block_start = index == 0 or not lines[index - 1].strip()
        if at_block_start and stripped and not AUTOLINK.match(stripped) and (
                DIRECTIVE.match(stripped) or re.match(r'^<[/!?A-Za-z]', stripped)):
            end = index
            while end + 1 < len(lines) and lines[end + 1].strip():
                end += 1
            take(document.unverified, index, end)
            index = end + 1
            continue
        index += 1

    def line_at(offset: int) -> int:
        return bisect.bisect_right(starts, offset)

    prose = _mask(text, blocked)
    position = 0
    spans: list[tuple[int, int]] = []
    while (run := CODE_RUN.search(prose, position)) is not None:
        closer = re.compile(r'(?<!`)`{%d}(?!`)' % len(run.group())).search(prose, run.end())
        if closer is None:
            position = run.end()
            continue
        document.inline_code.append(Region(text[run.start():closer.end()], line_at(run.start())))
        spans.append((run.start(), closer.end()))
        position = closer.end()
    prose = _mask(prose, spans)
    spans = []
    for match in LINK.finditer(prose):
        document.link_destination.append(Region(match.group(1), line_at(match.start(1))))
        spans.append(match.span())
    for match in DEFINITION.finditer(prose):
        document.link_destination.append(Region(match.group(1), line_at(match.start(1))))
        spans.append(match.span())
    for match in AUTOLINK.finditer(prose):
        document.link_destination.append(Region(match.group(), line_at(match.start())))
        spans.append(match.span())
    remaining = _mask(prose, spans)
    for match in INLINE_TAG.finditer(remaining):
        document.unverified.append(Region(match.group(), line_at(match.start())))
    for match in LEFTOVER_LINK.finditer(remaining):
        # A destination form this scanner does not parse, such as balanced
        # parentheses inside it. Unread is not the same as absent.
        line = line_at(match.start())
        fragment = text[match.start():match.start() + 40].split('\n')[0]
        document.unread_link.append(Region(fragment, line))
    document.link_destination.sort(key=lambda region: region.line)
    document.unverified.sort(key=lambda region: region.line)
    return document


def _fragment(value: str, limit: int = 60) -> str:
    collapsed = ' '.join(value.split())
    return collapsed if len(collapsed) <= limit else collapsed[:limit - 1] + '…'


def _difference(before: Region, after: Region) -> tuple[int, str]:
    """Point at the first line that differs inside a region, not at its first line."""
    old = before.text.split('\n')
    new = after.text.split('\n')
    for offset in range(max(len(old), len(new))):
        was = old[offset] if offset < len(old) else ''
        now = new[offset] if offset < len(new) else ''
        if was != now:
            return before.line + offset, f'{_fragment(was)} -> {_fragment(now)}'
    return before.line, f'{_fragment(before.text)} -> {_fragment(after.text)}'


def compare(kind: str, before: list[Region], after: list[Region], ordered: bool) -> dict:
    """Report one protected kind as pass, fail or not-applicable."""
    if not before and not after:
        return {'kind': kind, 'status': 'not-applicable',
                'detail': 'no region of this kind in either document', 'line': None}
    if ordered:
        for position, region in enumerate(before):
            if position >= len(after):
                return {'kind': kind, 'status': 'fail', 'line': region.line,
                        'detail': f'removed: {_fragment(region.text)}'}
            if after[position].text != region.text:
                line, detail = _difference(region, after[position])
                return {'kind': kind, 'status': 'fail', 'line': line, 'detail': detail}
        if len(after) > len(before):
            extra = after[len(before)]
            return {'kind': kind, 'status': 'fail', 'line': extra.line,
                    'detail': f'added: {_fragment(extra.text)}'}
    else:
        lost = Counter(region.text for region in before) - Counter(region.text for region in after)
        if lost:
            missing = next(iter(lost))
            line = next(region.line for region in before if region.text == missing)
            return {'kind': kind, 'status': 'fail', 'line': line,
                    'detail': f'no longer present after the rewrite: {_fragment(missing)}'}
        gained = Counter(region.text for region in after) - Counter(region.text for region in before)
        if gained:
            added = next(iter(gained))
            line = next(region.line for region in after if region.text == added)
            return {'kind': kind, 'status': 'fail', 'line': line,
                    'detail': f'added by the rewrite: {_fragment(added)}'}
    count = max(len(before), len(after))
    order = 'in order' if ordered else 'as a multiset, order ignored'
    return {'kind': kind, 'status': 'pass', 'line': None,
            'detail': f'{count} region(s) identical {order}'}


def preserve(before_path: Path, after_path: Path, mode: str) -> dict:
    """Run every check for one mode and return the report with its exit code."""
    before_text, before_endings = read_document(before_path)
    after_text, after_endings = read_document(after_path)
    before = scan(before_text, before_endings, mode)
    after = scan(after_text, after_endings, mode)
    kinds = PROTECTED[mode]
    checks = [compare(kind, before.regions(kind), after.regions(kind), mode == 'copyedit')
              for kind in kinds]
    for kind in PROTECTED['copyedit']:
        if kind not in kinds:
            checks.append({'kind': kind, 'status': 'not-applicable', 'line': None,
                           'detail': 'not protected in rewrite mode'})
    unread = before.unread_link + after.unread_link
    if unread:
        for check in checks:
            if check['kind'] == 'link_destination' and check['status'] == 'not-applicable':
                check['detail'] = (f'{len(unread)} link marker(s) were found but no destination '
                                   f'could be read; see unverified_construct')
                check['line'] = unread[0].line
    unverified = before.unclassified() + after.unclassified()
    if unverified:
        checks.append({'kind': 'unverified_construct', 'status': 'unverified',
                       'line': unverified[0].line,
                       'detail': f'{len(unverified)} construct(s) this scanner cannot classify, '
                                 f'first: {_fragment(unverified[0].text, 40)}'})
    else:
        checks.append({'kind': 'unverified_construct', 'status': 'not-applicable', 'line': None,
                       'detail': 'every block was classified'})
    if before.inspected(kinds) == 0 and after.inspected(kinds) == 0:
        checks.append({'kind': 'coverage', 'status': 'unverified', 'line': None,
                       'detail': 'no protected region exists in either document, '
                                 'so nothing was inspected'})
    same_endings = before.endings == after.endings
    checks.append({'kind': 'line_endings', 'status': 'pass' if same_endings else 'warning',
                   'line': None,
                   'detail': f'both files use {before.endings}' if same_endings else
                             f'{before.endings} before, {after.endings} after; protected content '
                             f'was compared after normalising to lf'})
    statuses = {check['status'] for check in checks}
    exit_code = 0
    if 'unverified' in statuses:
        exit_code = 2
    if 'fail' in statuses:
        # A refuted region is a known result and outranks evidence that is merely
        # missing; the unverified checks stay in the report either way.
        exit_code = 1
    checks.sort(key=lambda check: (STATUS_ORDER.index(check['status']), check['kind']))
    return {'mode': mode, 'checks': checks, 'exit_code': exit_code}


def render(report: dict) -> str:
    lines = [f"preserve: {report['mode']}"]
    for check in report['checks']:
        place = f" (line {check['line']})" if check['line'] else ''
        lines.append(f"  {check['kind']:<22}{check['status']:<16}{check['detail']}{place}")
    lines.append(f"exit {report['exit_code']}")
    return '\n'.join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        # A document may quote any script; the report must not depend on the
        # console code page, which on Windows cannot encode CJK punctuation.
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8', errors='backslashreplace')
    parser = argparse.ArgumentParser(prog='text_check.py', description=__doc__)
    subcommands = parser.add_subparsers(dest='command', required=True)
    check = subcommands.add_parser('preserve', help='compare protected regions of two documents')
    check.add_argument('--before', type=Path, required=True, help='the document before the edit')
    check.add_argument('--after', type=Path, required=True, help='the document after the edit')
    check.add_argument('--mode', choices=sorted(PROTECTED), required=True)
    check.add_argument('--json', action='store_true', help='machine-readable report on stdout')
    check.add_argument('--allow-unverified', action='store_true',
                       help='report unclassifiable constructs without making the run exit 2; '
                            'a document with no protected region at all still exits 2')
    args = parser.parse_args(argv)
    try:
        report = preserve(args.before, args.after, args.mode)
    except InvalidInput as error:
        parser.exit(2, f'text-check: {error}\n')
    uninspected = any(check['kind'] == 'coverage' and check['status'] == 'unverified'
                      for check in report['checks'])
    if args.allow_unverified and report['exit_code'] == 2 and not uninspected:
        # The flag forgives a construct the scanner could not classify. It never
        # forgives a document in which nothing was inspected at all.
        report['exit_code'] = 0
    print(json.dumps(report, ensure_ascii=False, indent=2) if args.json else render(report))
    return report['exit_code']


if __name__ == '__main__':
    raise SystemExit(main())
