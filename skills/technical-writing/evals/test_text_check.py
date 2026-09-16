"""Offline tests of the shipped check's narrow contract, never of model quality.

Run: python -B -m unittest discover -s skills/technical-writing/evals -p 'test_*.py'
Only the shipped check is executed, with test-created files, no document commands.
"""
from __future__ import annotations
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE.parent / 'scripts' / 'text_check.py'
FIXTURES = HERE / 'fixtures' / 'preservation'

class PreservationTests(unittest.TestCase):
    def invoke(self, before, after, mode='copyedit', extra=()):
        args = [sys.executable, '-B', str(SCRIPT), 'preserve', '--before', str(before),
                '--after', str(after), '--mode', mode, '--json', *extra]
        old = {p: p.read_bytes() for p in (before, after) if p.exists()}
        result = subprocess.run(args, capture_output=True, timeout=10)
        for path, content in old.items():
            self.assertEqual(path.read_bytes(), content, 'check must not modify inputs')
        return result, json.loads(result.stdout) if result.stdout.strip() else None

    def pair(self, a, b, mode='copyedit', extra=()):
        with tempfile.TemporaryDirectory(prefix='assay-text-check-') as d:
            p, q = Path(d)/'before.md', Path(d)/'after.md'
            p.write_bytes(a.encode() if isinstance(a,str) else a)
            q.write_bytes(b.encode() if isinstance(b,str) else b)
            return self.invoke(p,q,mode,extra)

    def assert_kind(self, report, kind, status):
        self.assertTrue(any(c['kind']==kind and c['status']==status for c in report['checks']), report)

    def test_source_fixture_matrix(self):
        samples=[('c01-fence',1,'copyedit'),('c02-inline',1,'copyedit'),
                 ('c03-link',1,'copyedit'),('c04-front',1,'copyedit'),
                 ('c05-table',1,'copyedit'),('c06-ru',0,'copyedit'),
                 ('c07-crlf',0,'copyedit'),('c08-nested',1,'copyedit'),
                 ('c09-html',2,'copyedit'),('c10-empty',2,'copyedit'),
                 ('c11-bytes',2,'copyedit'),('c12a-zh',1,'copyedit'),
                 ('c12b-zh',0,'copyedit'),('c13-reorder',0,'rewrite')]
        for name,code,mode in samples:
            with self.subTest(name=name):
                suffix = '.bin' if name == 'c11-bytes' else '.txt'
                result,report=self.invoke(FIXTURES/(name+'-before'+suffix),FIXTURES/(name+'-after'+suffix),mode)
                self.assertEqual(result.returncode,code,result.stderr.decode('utf-8','replace'))
                if report: self.assertEqual(report['exit_code'],code)

    def test_equivalent_prose_is_not_a_preservation_failure(self):
        a='## Setup\n\nSet `poll_seconds` as shown:\n\n```toml\npoll_seconds = 8\n```\n'
        b=a.replace('Set `poll_seconds` as shown:', 'You can set `poll_seconds` here:')
        result,report=self.pair(a,b)
        self.assertEqual(result.returncode,0)
        self.assert_kind(report,'fenced_code','pass')

    def test_code_change_fails_even_when_both_values_could_be_valid(self):
        a='```toml\npoll_seconds = 8\n```\n'
        result,report=self.pair(a,a.replace('8','12'))
        self.assertEqual(result.returncode,1)
        self.assert_kind(report,'fenced_code','fail')

    def test_changed_existing_link_is_still_preservation_failure(self):
        result,report=self.pair('[ref](../a.md)\n','[ref](../b.md)\n')
        self.assertEqual(result.returncode,1)
        self.assert_kind(report,'link_destination','fail')

    def test_plain_prose_has_no_structural_coverage(self):
        result,report=self.pair('Ready.\n','Ready.\n')
        self.assertEqual(result.returncode,2)
        self.assert_kind(report,'coverage','unverified')

    def test_allow_unverified_does_not_forgive_zero_coverage(self):
        result,report=self.pair('Ready.\n','Ready.\n',extra=('--allow-unverified',))
        self.assertEqual(result.returncode,2)
        self.assert_kind(report,'coverage','unverified')

    def test_allow_unverified_does_not_prove_html_preservation(self):
        a='Keep `mode`.\n\n<Notice>before</Notice>\n'
        result,report=self.pair(a,a.replace('before','after'),extra=('--allow-unverified',))
        self.assertEqual(result.returncode,0)
        self.assert_kind(report,'unverified_construct','unverified')

    def test_strict_html_is_unverified(self):
        a='Keep `mode`.\n\n<Notice>before</Notice>\n'
        result,report=self.pair(a,a)
        self.assertEqual(result.returncode,2)
        self.assert_kind(report,'unverified_construct','unverified')

    def test_failure_retains_unknown_construct(self):
        a='Use `--preview`.\n\n<Notice>text</Notice>\n'
        result,report=self.pair(a,a.replace('--preview','--apply'))
        self.assertEqual(result.returncode,1)
        self.assert_kind(report,'inline_code','fail')
        self.assert_kind(report,'unverified_construct','unverified')

    def test_crlf_reports_warning_but_preserves_content(self):
        result,report=self.pair(b'Use `x`.\r\n',b'Use `x`.\n')
        self.assertEqual(result.returncode,0)
        self.assert_kind(report,'line_endings','warning')

    def test_missing_input_is_not_success(self):
        with tempfile.TemporaryDirectory() as d:
            q=Path(d)/'after.md';q.write_text('Use `x`.\n')
            result,report=self.invoke(Path(d)/'absent.md',q)
            self.assertEqual(result.returncode,2)
            self.assertIsNone(report)

    def test_invalid_utf8_is_not_success(self):
        result,report=self.pair(b'\xff',b'Use `x`.\n')
        self.assertEqual(result.returncode,2)
        self.assertIsNone(report)

    def test_both_empty_is_not_success(self):
        result,report=self.pair('','')
        self.assertEqual(result.returncode,2)
        self.assertIsNone(report)

    def test_reordering_is_allowed_only_in_rewrite(self):
        a='```text\na\n```\n\n```text\nb\n```\n'
        b='```text\nb\n```\n\n```text\na\n```\n'
        self.assertEqual(self.pair(a,b)[0].returncode,1)
        self.assertEqual(self.pair(a,b,'rewrite')[0].returncode,0)

    # The next tests pin limitations so nobody can advertise an exit 0 as a
    # semantic/document-validity verdict. They deliberately contain bad prose.
    def test_limitation_negation_change_is_not_detected(self):
        a='Use `clean`. Never run before approval.\n'
        b='Use `clean`. Always run before approval.\n'
        self.assertEqual(self.pair(a,b)[0].returncode,0)

    def test_limitation_example_does_not_establish_default(self):
        a='This example uses 8 seconds.\n\n```toml\npoll_seconds = 8\n```\n'
        b=a.replace('This example uses','The implementation defaults to')
        self.assertEqual(self.pair(a,b)[0].returncode,0)

    def test_limitation_destination_existence_is_not_checked(self):
        a='See [ref](missing-file.md).\n'
        self.assertEqual(self.pair(a,a)[0].returncode,0)

    def test_limitation_heading_association_is_not_checked(self):
        a='## Preview\n\n```sh\ntool --preview\n```\n'
        b=a.replace('## Preview','## Destructive apply')
        self.assertEqual(self.pair(a,b)[0].returncode,0)

if __name__ == '__main__':
    unittest.main()
