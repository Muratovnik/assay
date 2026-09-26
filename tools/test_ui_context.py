"""Tests for the opt-in read-only UI source fingerprint command."""
import hashlib
import json
import runpy
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / 'skills/ui-delivery/scripts/ui_context.py'
# Execute the script without importlib's bytecode cache beside canonical skill source.
inspect_sources = runpy.run_path(str(SCRIPT))['inspect_sources']


class ContextTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'tokens.css').write_text('--example: initial;', encoding='utf-8')

    def test_loading_test_module_leaves_skill_source_unchanged(self):
        test_copy = self.root / 'tools/test_ui_context.py'
        script_copy = self.root / 'skills/ui-delivery/scripts/ui_context.py'
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

    def test_fingerprint_matches_bytes_without_writing(self):
        before = {p.name: p.read_bytes() for p in self.root.iterdir()}
        result = inspect_sources(self.root, ['tokens=tokens.css'])
        self.assertEqual(result, [{'role': 'tokens', 'path': 'tokens.css',
            'sha256': hashlib.sha256(before['tokens.css']).hexdigest()}])
        self.assertEqual(before, {p.name: p.read_bytes() for p in self.root.iterdir()})
        (self.root / 'tokens.css').write_text('changed', encoding='utf-8')
        self.assertNotEqual(result[0]['sha256'], inspect_sources(self.root, ['tokens=tokens.css'])[0]['sha256'])

    def test_invalid_paths_roles_missing_and_duplicate_sources(self):
        for value in ['tokens=../outside', 'tokens=/absolute', 'tokens=a/../tokens.css',
            'tokens=a\\b', 'tokens=a//b', 'tokens=C:/tokens.css', 'tokens=.env',
            'tokens=.git/config', 'tokens=missing.css', 'Tokens=tokens.css', 'tokens=']:
            with self.subTest(value=value), self.assertRaises(ValueError):
                inspect_sources(self.root, [value])
        with self.assertRaises(ValueError):
            inspect_sources(self.root, ['tokens=tokens.css'] * 2)
        with self.assertRaises(ValueError):
            inspect_sources(self.root, [])

    def test_symlink_is_not_followed(self):
        try:
            (self.root / 'alias').symlink_to(self.root / 'tokens.css')
        except OSError as error:
            self.skipTest(f'host cannot create symlink: {error}')
        with self.assertRaisesRegex(ValueError, 'symlink'):
            inspect_sources(self.root, ['tokens=alias'])

    def test_cli_json_and_nonzero_error(self):
        good = subprocess.run([sys.executable, str(SCRIPT), '--root', str(self.root),
            '--source', 'tokens=tokens.css'], text=True, capture_output=True)
        self.assertEqual(good.returncode, 0, good.stderr)
        self.assertNotIn(str(self.root), good.stdout)
        self.assertEqual(json.loads(good.stdout)['sources'][0]['path'], 'tokens.css')
        bad = subprocess.run([sys.executable, str(SCRIPT), '--root', str(self.root),
            '--source', 'tokens=missing.css'], text=True, capture_output=True)
        self.assertEqual(bad.returncode, 2)
        self.assertEqual(bad.stdout, '')


if __name__ == '__main__':
    unittest.main()
