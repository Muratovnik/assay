"""Tests for the read-only preservation check in the technical-writing skill."""
import hashlib
import json
import runpy
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / 'skills/technical-writing/scripts/text_check.py'
# Execute the script without importlib's bytecode cache beside canonical skill source.
MODULE = runpy.run_path(str(SCRIPT))

BASE = """---
title: Sync guide
version: 2.4
---

# Preview a sync

Run `widgetctl sync --dry-run` to list the files. See the [report](logs/sync.md).

```bash
widgetctl sync --dry-run --timeout 30
```

| Parameter | Default | Note |
| --- | --- | --- |
| `--timeout` | 30 | Aborts the run after the given seconds. |

> A quotation from the operator handbook.
"""

RUSSIAN_BEFORE = """# Предпросмотр

Осуществляется выполнение операции по просмотру файлов, что позволяет в
кратчайшие сроки приступить к работе. Запустите `widgetctl sync --dry-run`.

```bash
widgetctl sync --dry-run
```
"""

RUSSIAN_AFTER = """# Предпросмотр

Команда показывает, какие файлы уйдут на сервер, — и ничего не загружает.
Запустите `widgetctl sync --dry-run`.

```bash
widgetctl sync --dry-run
```
"""

NESTED = """# Steps

1. Prepare the catalogue.

   ```bash
   widgetctl catalogue init --path ./cat
   ```

2. Run the sync.
"""

CHINESE = """# 如何预览同步结果

运行 `widgetctl sync --dry-run` 可以查看将要上传的文件，不会写入服务器。

```bash
widgetctl sync --dry-run --timeout 30
```

该命令是幂等的，网络中断后重复执行是安全的。
"""


class PreservationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def run_check(self, before, after, mode='copyedit', *extra):
        """Write the pair as bytes and run the command exactly as a caller would."""
        paths = []
        for name, content in [('before.md', before), ('after.md', after)]:
            path = self.root / name
            path.write_bytes(content if isinstance(content, bytes) else content.encode('utf-8'))
            paths.append(path)
        done = subprocess.run(
            [sys.executable, '-B', str(SCRIPT), 'preserve', '--before', str(paths[0]),
             '--after', str(paths[1]), '--mode', mode, '--json', *extra],
            capture_output=True, text=True, encoding='utf-8')
        report = json.loads(done.stdout) if done.stdout.strip() else None
        return done, report

    def status(self, report, kind):
        return next(check['status'] for check in report['checks'] if check['kind'] == kind)

    def test_loading_test_module_leaves_skill_source_unchanged(self):
        test_copy = self.root / 'tools/test_text_check.py'
        script_copy = self.root / 'skills/technical-writing/scripts/text_check.py'
        for target, source in [(test_copy, Path(__file__)), (script_copy, SCRIPT)]:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(source.read_bytes())
        before = {p.relative_to(self.root): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in self.root.rglob('*') if p.is_file()}
        loaded = subprocess.run([sys.executable, '-c',
            'import runpy, sys; sys.dont_write_bytecode = False; sys.pycache_prefix = None; runpy.run_path(sys.argv[1])',
            str(test_copy)], capture_output=True, text=True)
        self.assertEqual(loaded.returncode, 0, loaded.stderr)
        after = {p.relative_to(self.root): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in self.root.rglob('*') if p.is_file()}
        self.assertEqual(before, after, 'Collecting these tests must not write into skill source')

    def test_changed_command_inside_a_fence_is_refuted(self):
        done, report = self.run_check(BASE, BASE.replace('--timeout 30', '--timeout 60'))
        self.assertEqual(done.returncode, 1, done.stderr)
        self.assertEqual(report['exit_code'], 1)
        self.assertEqual(self.status(report, 'fenced_code'), 'fail')
        self.assertEqual(self.status(report, 'inline_code'), 'pass')

    def test_changed_inline_span_link_and_frontmatter_are_refuted(self):
        for kind, before, after in [
            ('inline_code', '`widgetctl sync --dry-run` to', '`widgetctl sync --dryrun` to'),
            ('link_destination', '(logs/sync.md)', '(logs/report.md)'),
            ('frontmatter', 'version: 2.4', 'version: 2.5'),
            ('table_row', '| `--timeout` | 30 |', '| `--timeout` | 60 |'),
            ('blockquote', 'A quotation from', 'A quote from'),
        ]:
            with self.subTest(kind=kind):
                done, report = self.run_check(BASE, BASE.replace(before, after))
                self.assertEqual(done.returncode, 1)
                self.assertEqual(self.status(report, kind), 'fail')

    def test_prose_only_russian_edit_with_dashes_passes(self):
        done, report = self.run_check(RUSSIAN_BEFORE, RUSSIAN_AFTER)
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(self.status(report, 'fenced_code'), 'pass')
        self.assertEqual(self.status(report, 'line_endings'), 'pass')

    def test_crlf_before_and_lf_after_passes_with_a_line_ending_warning(self):
        crlf = RUSSIAN_BEFORE.encode('utf-8').replace(b'\n', b'\r\n')
        done, report = self.run_check(crlf, RUSSIAN_AFTER)
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(self.status(report, 'inline_code'), 'pass')
        self.assertEqual(self.status(report, 'line_endings'), 'warning')
        self.assertIn('crlf before, lf after', json.dumps(report, ensure_ascii=False))

    def test_fenced_block_nested_in_a_list_item(self):
        done, _ = self.run_check(NESTED, NESTED.replace('## 2.', '## 2.'))
        self.assertEqual(done.returncode, 0, done.stderr)
        done, report = self.run_check(NESTED, NESTED.replace('./cat', './catalogue'))
        self.assertEqual(done.returncode, 1)
        self.assertEqual(self.status(report, 'fenced_code'), 'fail')

    def test_unsupported_syntax_is_unverified_rather_than_passed(self):
        html = '# Notes\n\n<Callout type="warning">The old spelling exits 2.</Callout>\n\n' \
               'Run `widgetctl sync --dry-run` first.\n'
        edited = html.replace('Run `widgetctl sync --dry-run` first.',
                              'First run `widgetctl sync --dry-run`.')
        done, report = self.run_check(html, edited)
        self.assertEqual(done.returncode, 2, done.stderr)
        self.assertEqual(self.status(report, 'unverified_construct'), 'unverified')
        allowed, report = self.run_check(html, edited, 'copyedit', '--allow-unverified')
        self.assertEqual(allowed.returncode, 0, allowed.stderr)
        self.assertEqual(self.status(report, 'unverified_construct'), 'unverified')

    def test_a_document_with_no_protected_region_is_not_reported_as_checked(self):
        done, report = self.run_check('# Title\n\nOne sentence.\n', '# Title\n\nOne clause.\n')
        self.assertEqual(done.returncode, 2, done.stderr)
        self.assertEqual(self.status(report, 'coverage'), 'unverified')

    def test_empty_and_non_utf8_inputs_are_invalid(self):
        empty, report = self.run_check('   \n', BASE)
        self.assertEqual(empty.returncode, 2)
        self.assertIsNone(report)
        self.assertIn('empty', empty.stderr)
        binary, report = self.run_check('# Отчёт\n'.encode('cp1251'), '# Отчёт\n')
        self.assertEqual(binary.returncode, 2)
        self.assertIsNone(report)
        self.assertIn('UTF-8', binary.stderr)
        missing = subprocess.run(
            [sys.executable, '-B', str(SCRIPT), 'preserve', '--before', str(self.root / 'none.md'),
             '--after', str(self.root / 'none.md'), '--mode', 'copyedit'],
            capture_output=True, text=True)
        self.assertEqual(missing.returncode, 2)
        self.assertEqual(missing.stdout, '')

    def test_chinese_document_with_unchanged_latin_commands_passes(self):
        done, report = self.run_check(CHINESE, CHINESE.replace(
            '该命令是幂等的，网络中断后重复执行是安全的。', '该命令是幂等的，重复执行是安全的。'))
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(self.status(report, 'fenced_code'), 'pass')
        self.assertEqual(self.status(report, 'inline_code'), 'pass')

    def test_full_width_punctuation_inside_a_command_is_refuted(self):
        for before, after in [('`widgetctl sync --dry-run`', '`widgetctl sync --dry-run，`'),
                              ('--dry-run --timeout 30', '--dry-run，--timeout 30')]:
            with self.subTest(before=before):
                done, _ = self.run_check(CHINESE, CHINESE.replace(before, after))
                self.assertEqual(done.returncode, 1)

    def test_full_width_punctuation_in_chinese_prose_is_not_a_defect(self):
        half = CHINESE.replace('不会写入服务器。', '不会写入服务器.')
        done, report = self.run_check(half, CHINESE)
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(self.status(report, 'inline_code'), 'pass')

    def test_rewrite_allows_reordering_but_not_changing_a_block(self):
        reordered = """# Preview a sync

## Troubleshooting

See the [report](logs/sync.md).

## Usage

Run `widgetctl sync --dry-run` to list the files.

```bash
widgetctl sync --dry-run --timeout 30
```
"""
        original = """# Preview a sync

Run `widgetctl sync --dry-run` to list the files.

```bash
widgetctl sync --dry-run --timeout 30
```

## Troubleshooting

See the [report](logs/sync.md).
"""
        done, report = self.run_check(original, reordered, 'rewrite')
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(self.status(report, 'fenced_code'), 'pass')
        self.assertEqual(self.status(report, 'table_row'), 'not-applicable')
        done, report = self.run_check(original, reordered.replace('--timeout 30', '--timeout 60'),
                                      'rewrite')
        self.assertEqual(done.returncode, 1)
        self.assertEqual(self.status(report, 'fenced_code'), 'fail')
        strict, _ = self.run_check(original, reordered, 'copyedit')
        self.assertEqual(strict.returncode, 0, 'a moved section is outside what this tool judges')

    def test_scanner_reads_without_writing_and_reports_line_numbers(self):
        source = self.root / 'one.md'
        source.write_bytes(BASE.encode('utf-8'))  # text mode would rewrite endings on Windows
        fingerprint = hashlib.sha256(source.read_bytes()).hexdigest()
        text, endings = MODULE['read_document'](source)
        document = MODULE['scan'](text, endings, 'copyedit')
        self.assertEqual(endings, 'lf')
        self.assertEqual([region.line for region in document.fenced_code], [10])
        self.assertEqual([region.text for region in document.link_destination], ['logs/sync.md'])
        self.assertEqual(len(document.table_row), 3)
        self.assertEqual(document.unverified, [])
        self.assertEqual(fingerprint, hashlib.sha256(source.read_bytes()).hexdigest())
        self.assertEqual([p.name for p in self.root.iterdir()], ['one.md'])


if __name__ == '__main__':
    unittest.main()
