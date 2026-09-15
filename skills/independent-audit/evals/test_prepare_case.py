"""Mechanical packet/fixture checks; these are not model behavior evaluations."""

import ast
import csv
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import prepare_case as prep


def hashes(root):
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in root.rglob("*") if path.is_file()
    }


class PreparationTests(unittest.TestCase):
    def setUp(self):
        # Coordinator chooses an existing owning-project ignored scratch parent.
        parent = os.environ.get("AUDIT_EVAL_TEST_TMP")
        if not parent:
            raise RuntimeError("Set AUDIT_EVAL_TEST_TMP to an owning-project scratch directory")
        self.temporary = tempfile.TemporaryDirectory(
            prefix="independent-audit-tests-", dir=prep.plain_path(parent))
        self.owned_root = Path(self.temporary.name).resolve()
        self.parent = self.owned_root / "packets with spaces"
        self.parent.mkdir()

    def tearDown(self):
        # Cleanup is confined to this test's newly allocated private directory.
        self.assertEqual(Path(self.temporary.name).resolve(), self.owned_root)
        self.assertTrue(self.owned_root.name.startswith("independent-audit-tests-"))
        self.temporary.cleanup()

    def test_catalog_has_complete_real_inputs(self):
        cases = prep.load_cases()
        listed = {relative for case in cases.values() for relative in case["files"]}
        actual = {
            path.relative_to(prep.EVAL_ROOT).as_posix()
            for path in (prep.EVAL_ROOT / "files").rglob("*") if path.is_file()
        }
        self.assertEqual(listed, actual)
        self.assertEqual(set(cases), set(range(1, 32)))

    def test_packets_contain_only_whitelisted_inputs_and_runtime_skill(self):
        before = hashes(prep.SKILL_ROOT)
        for case_id, case in prep.load_cases().items():
            with self.subTest(case=case_id):
                packet = prep.prepare_case(case_id, self.parent)
                actual = hashes(packet)
                expected = {
                    "inputs/" + "/".join(Path(name).parts[2:]) for name in case["files"]
                } | set(prep.skill_snapshot(prep.SKILL_ROOT)) | {"prompt.txt", "manifest.json"}
                self.assertEqual(set(actual), expected)
                manifest = json.loads((packet / "manifest.json").read_text(encoding="utf-8"))
                self.assertEqual(manifest["files"], {
                    name: digest for name, digest in actual.items() if name != "manifest.json"
                })
                for name in case["files"]:
                    copied = packet / "inputs" / Path(*Path(name).parts[2:])
                    self.assertEqual(copied.read_bytes(), (prep.EVAL_ROOT / name).read_bytes())
        self.assertEqual(hashes(prep.SKILL_ROOT), before)

    def test_repeated_preparation_preserves_existing_files(self):
        sentinel = self.parent / "keep.txt"
        sentinel.write_text("unrelated work", encoding="utf-8")
        first = prep.prepare_case(1, self.parent)
        before = hashes(first)
        second = prep.prepare_case(1, self.parent)
        self.assertNotEqual(first, second)
        self.assertEqual(hashes(first), before)
        self.assertEqual(hashes(first), hashes(second))
        self.assertEqual(sentinel.read_text(encoding="utf-8"), "unrelated work")

    def pin_manifest(self, packet):
        return hashlib.sha256((packet / "manifest.json").read_bytes()).hexdigest()

    def test_postflight_verifies_full_inventory_without_git_discovery(self):
        # The parent marker must not become the identity of a frozen packet.
        decoy = self.parent / ".git"
        decoy.mkdir()
        (decoy / "HEAD").write_text("ref: refs/heads/unrelated\n", encoding="utf-8")
        packet = prep.prepare_case(13, self.parent)
        before = hashes(packet)
        with patch.object(subprocess, "run", side_effect=AssertionError("No Git/probes")):
            result = prep.verify_packet(packet, self.pin_manifest(packet))
        self.assertEqual(result["byte_integrity"], "pass")
        self.assertEqual(result["verified_files"], {
            key: value for key, value in before.items() if key != "manifest.json"
        })
        self.assertEqual(hashes(packet), before)

    def test_postflight_rejects_change_extra_missing_and_manifest_rewrite(self):
        for change in ("changed", "extra", "missing", "manifest"):
            with self.subTest(change=change):
                packet = prep.prepare_case(13, self.parent)
                pinned = self.pin_manifest(packet)
                target = packet / "inputs/repo/idcheck.py"
                if change == "changed":
                    target.write_text("changed\n", encoding="utf-8")
                elif change == "extra":
                    (packet / "unexpected.txt").write_text("extra", encoding="utf-8")
                elif change == "missing":
                    target.unlink()
                else:
                    target.write_text("changed\n", encoding="utf-8")
                    manifest = json.loads((packet / "manifest.json").read_text())
                    manifest["files"]["inputs/repo/idcheck.py"] = hashlib.sha256(target.read_bytes()).hexdigest()
                    (packet / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
                with self.assertRaises((ValueError, OSError)):
                    prep.verify_packet(packet, pinned)

    def test_postflight_missing_path_does_not_substitute_sibling(self):
        packet = prep.prepare_case(13, self.parent)
        with self.assertRaises(OSError):
            prep.verify_packet(packet.with_name(packet.name + "-missing"), self.pin_manifest(packet))

    def test_postflight_refuses_non_object_manifest_without_traceback(self):
        for value in (None, [], "not a manifest"):
            with self.subTest(value=value):
                packet = prep.prepare_case(13, self.parent)
                (packet / "manifest.json").write_text(json.dumps(value), encoding="utf-8")
                result = self.run_python(prep.EVAL_ROOT, "verify_packet.py", str(packet),
                                         "--manifest-sha256", self.pin_manifest(packet))
                self.assertEqual(result.returncode, 1)
                self.assertIn("Manifest must be an object", result.stderr)
                self.assertNotIn("Traceback", result.stderr)

    def test_postflight_refuses_new_link_before_descending(self):
        packet = prep.prepare_case(13, self.parent)
        foreign = self.owned_root / "foreign"
        foreign.mkdir()
        (foreign / "private.txt").write_text("sentinel", encoding="utf-8")
        try:
            os.symlink(foreign, packet / "foreign", target_is_directory=True)
        except (OSError, NotImplementedError) as exc:
            self.skipTest(f"Host cannot create test symlink: {exc}")
        with self.assertRaisesRegex(ValueError, "Linked"):
            prep.verify_packet(packet, self.pin_manifest(packet))

    def test_postflight_cli_uses_retained_manifest_digest(self):
        packet = prep.prepare_case(13, self.parent)
        result = self.run_python(prep.EVAL_ROOT, "verify_packet.py", str(packet),
                                 "--manifest-sha256", self.pin_manifest(packet))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["byte_integrity"], "pass")
        refused = self.run_python(prep.EVAL_ROOT, "verify_packet.py", str(packet),
                                  "--manifest-sha256", "0" * 64)
        self.assertEqual(refused.returncode, 1)

    def test_no_skill_baseline_keeps_identical_prompt_and_subject(self):
        with_skill = prep.prepare_case(2, self.parent)
        without_skill = prep.prepare_case(2, self.parent, with_skill=False)
        self.assertEqual(hashes(with_skill / "inputs"), hashes(without_skill / "inputs"))
        self.assertEqual((with_skill / "prompt.txt").read_bytes(),
                         (without_skill / "prompt.txt").read_bytes())
        self.assertFalse((without_skill / "skill").exists())

    def test_refuses_source_destination_and_invalid_case_without_allocation(self):
        before = set(self.parent.iterdir())
        with self.assertRaises(ValueError):
            prep.prepare_case(999, self.parent)
        with self.assertRaises(ValueError):
            prep.prepare_case(1, prep.SKILL_ROOT)
        with self.assertRaises(OSError):
            prep.prepare_case(1, self.parent / "not-created")
        self.assertEqual(set(self.parent.iterdir()), before)

    def test_rejects_unsafe_paths(self):
        for relative in ("../SKILL.md", "/tmp/a", "C:/a", "files\\1\\brief.md",
                         "files//1/brief.md", "files/1/./brief.md", "files/1/../2/brief.md"):
            with self.subTest(path=relative), self.assertRaises(ValueError):
                prep.input_file(prep.EVAL_ROOT, relative)

    def test_rejects_duplicate_catalog_inputs(self):
        root = self.owned_root / "catalog"
        brief = root / "files" / "1" / "brief.md"
        brief.parent.mkdir(parents=True)
        brief.write_text("Fixture brief", encoding="utf-8")
        catalog = {
            "skill_name": "independent-audit",
            "evals": [{"id": 1, "prompt": "Audit", "expected_output": "Result",
                       "assertions": ["Check"],
                       "files": ["files/1/brief.md", "files/1/brief.md"]}],
        }
        (root / "evals.json").write_text(json.dumps(catalog), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            prep.load_cases(root)

    def test_rejects_reparse_attribute(self):
        record = SimpleNamespace(st_mode=stat.S_IFDIR, st_file_attributes=0x400)
        with patch.object(Path, "lstat", return_value=record):
            with self.assertRaisesRegex(ValueError, "reparse"):
                prep.plain_path(self.parent)

    def test_rubric_cannot_be_listed_as_executor_input(self):
        root = self.owned_root / "catalog-with-leak"
        root.mkdir()
        catalog = {
            "skill_name": "independent-audit",
            "evals": [{"id": 1, "prompt": "Audit", "expected_output": "Hidden result",
                       "assertions": ["Hidden check"], "files": ["evals.json"]}],
        }
        (root / "evals.json").write_text(json.dumps(catalog), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "within their fixture"):
            prep.load_cases(root)

    def test_current_runtime_markdown_links_resolve_inside_snapshot(self):
        import re

        criteria = [prep.SKILL_ROOT.parent / name for name in (
            "code-maintenance", "test-writing", "test-audit",
            "evidence-research", "operations-ui-delivery")]
        packet = prep.prepare_case(1, self.parent, criteria_roots=criteria)
        skill = packet / "skill" / "independent-audit"
        for path in skill.rglob("*.md"):
            content = path.read_text(encoding="utf-8")
            for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", content):
                if target.startswith(("https://", "http://", "#")):
                    continue
                linked = (path.parent / target.split("#", 1)[0]).resolve()
                linked.relative_to((packet / "skill").resolve())
                self.assertTrue(linked.is_file(), f"Unresolved link in {path}: {target}")

    def test_explicit_criteria_snapshot_preserves_old_bytes_and_hides_evals(self):
        frozen = self.owned_root / "frozen" / "code-maintenance"
        frozen.mkdir(parents=True)
        (frozen / "SKILL.md").write_text("Frozen criteria\n", encoding="utf-8")
        (frozen / "evals").mkdir()
        (frozen / "evals" / "answers.json").write_text("hidden", encoding="utf-8")
        for with_skill in (False, True):
            packet = prep.prepare_case(18, self.parent, with_skill=with_skill,
                                       criteria_roots=[frozen])
            self.assertEqual((packet / "skill/code-maintenance/SKILL.md").read_text(),
                             "Frozen criteria\n")
            self.assertFalse((packet / "skill/code-maintenance/evals").exists())
            self.assertEqual((packet / "skill/independent-audit").exists(), with_skill)
            prep.verify_packet(packet, self.pin_manifest(packet))

    def test_criteria_reject_collision_and_output_inside_source_before_writes(self):
        source = prep.SKILL_ROOT.parent / "code-maintenance"
        before = list(self.parent.iterdir())
        for roots in ([source, source], [prep.SKILL_ROOT]):
            with self.assertRaisesRegex(ValueError, "Duplicate"):
                prep.prepare_case(18, self.parent, criteria_roots=roots)
        with self.assertRaisesRegex(ValueError, "outside the source"):
            prep.prepare_case(18, source, criteria_roots=[source])
        self.assertEqual(list(self.parent.iterdir()), before)

    def test_rejects_actual_symlink_when_host_supports_it(self):
        target = self.owned_root / "target.txt"
        target.write_text("Do not follow", encoding="utf-8")
        link = self.owned_root / "link.txt"
        try:
            os.symlink(target, link)
        except (OSError, NotImplementedError) as exc:
            self.skipTest(f"Host cannot create test symlink: {exc}")
        with self.assertRaisesRegex(ValueError, "Linked"):
            prep.input_file(self.owned_root, "link.txt")

    def run_python(self, cwd, *args):
        return subprocess.run([sys.executable, "-B", *args], cwd=cwd,
                              capture_output=True, text=True, timeout=20)

    def test_backend_controls_discriminate_supported_input_from_corruption(self):
        packet = prep.prepare_case(20, self.parent, with_skill=False)
        result = self.run_python(packet / "inputs/repo", "-c",
            "from service import decode; "
            "assert decode('{\"label\": \"a+b&c\"}') == {'label': 'a+b&c'}\n"
            "try: decode('[]')\n"
            "except ValueError: pass\n"
            "else: raise AssertionError('Must reject non-objects')")
        self.assertEqual(result.returncode, 0, result.stderr)
        packet = prep.prepare_case(27, self.parent, with_skill=False)
        repo = packet / "inputs/repo"
        before = hashes(repo)
        result = self.run_python(repo, "-c",
            "from gateway import build_path, health_path\n"
            "from urllib.parse import parse_qs, urlsplit, urlencode\n"
            "def decoded(path): return parse_qs(urlsplit(path).query)\n"
            "assert decoded(health_path()) == {'check': ['ready']}\n"
            "assert decoded(build_path('hello world')) == {'q': ['hello world']}\n"
            "for value in ('a+b', 'a&b=c'):\n"
            "    assert decoded(build_path(value)) != {'q': [value]}\n"
            "    assert decoded('/search?' + urlencode({'q': value})) == {'q': [value]}\n")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(hashes(repo), before)

    def test_seeded_case_has_green_smoke_and_real_failures(self):
        packet = prep.prepare_case(1, self.parent, with_skill=False)
        repo = packet / "inputs" / "repo"
        before = hashes(repo)
        smoke = self.run_python(repo, "-m", "unittest", "discover", "-s", "tests")
        self.assertEqual(smoke.returncode, 0, smoke.stderr)
        registration = json.loads((repo / "clients/editor.json").read_text(encoding="utf-8"))
        route = self.run_python(repo, *registration["command"][1:])
        self.assertEqual(route.returncode, 0)
        self.assertEqual(json.loads(route.stdout)["owner"], "legacy")
        invalid = self.run_python(repo, "tools/validate.py", "configs/missing-port.json")
        self.assertIn("ERROR", invalid.stderr)
        self.assertEqual(invalid.returncode, 0)
        self.assertEqual(hashes(repo), before)

    def test_valid_case_exercises_both_routes_without_source_changes(self):
        packet = prep.prepare_case(2, self.parent, with_skill=False)
        repo = packet / "inputs" / "repo"
        before = hashes(repo)
        result = self.run_python(repo, "-m", "unittest", "discover", "-s", "tests")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(hashes(repo), before)

    def test_evidence_candidate_digest_and_syntax_without_execution(self):
        repo = prep.EVAL_ROOT / "files" / "3" / "repo"
        record = json.loads((repo / "evidence/syntax-check.json").read_text(encoding="utf-8"))
        candidate = (repo / record["candidate"]).read_bytes()
        self.assertEqual(hashlib.sha256(candidate).hexdigest(), record["sha256"])
        ast.parse(candidate)
        self.assertFalse(record["executed_candidate"])
        self.assertFalse(record["native_startup"])

    def test_channel_pair_preserves_identical_subject_and_green_shape_gate(self):
        subject_hashes = []
        for case_id in (5, 6):
            packet = prep.prepare_case(case_id, self.parent, with_skill=False)
            repo = packet / "inputs" / "repo"
            before = hashes(repo)
            selection = json.loads((repo / "distribution.json").read_text(encoding="utf-8"))
            self.assertEqual(set(selection["files"]), {
                "README.md", "docs/design-record.md", "docs/notes.md",
            })
            # Each listed byte sequence is actually obtainable in the packet.
            for name in selection["files"]:
                self.assertTrue((repo / name).is_file())
                self.assertTrue((repo / name).read_bytes())
            result = self.run_python(repo, "tools/check.py")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["files"], 3)
            self.assertEqual(hashes(repo), before)
            subject_hashes.append(before)
        self.assertEqual(*subject_hashes)

    def read_rows(self, path):
        with path.open(encoding="utf-8", newline="") as stream:
            rows = list(csv.DictReader(stream))
        self.assertEqual(len({row["id"] for row in rows}), len(rows))
        return {row["id"]: row for row in rows}

    def test_export_has_valid_copied_rows_but_wrong_required_population(self):
        packet = prep.prepare_case(7, self.parent, with_skill=False)
        repo = packet / "inputs" / "repo"
        before = hashes(repo)
        source = self.read_rows(repo / "source.csv")
        delivered = self.read_rows(repo / "export.csv")
        expected = {key: row for key, row in source.items() if row["region"] == "North"}
        self.assertEqual(set(expected) - set(delivered), {"item-03"})
        self.assertEqual(set(delivered) - set(expected), {"item-02"})
        self.assertTrue(all(row == source[key] for key, row in delivered.items()))
        result = self.run_python(repo, "tools/check.py")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["units"], 30)
        self.assertEqual(sum(int(row["units"]) for row in expected.values()), 40)
        self.assertEqual(hashes(repo), before)

    def test_pending_choice_has_two_materially_distinct_populations(self):
        repo = prep.EVAL_ROOT / "files" / "8" / "repo"
        request = json.loads((repo / "request.json").read_text(encoding="utf-8"))
        self.assertIsNone(request["population"])
        source = self.read_rows(repo / "source.csv")
        delivered = self.read_rows(repo / "export.csv")
        north = {key: row for key, row in source.items() if row["region"] == "North"}
        self.assertEqual(delivered, source)
        self.assertEqual(set(delivered) - set(north), {"item-02"})
        self.assertNotEqual(delivered, north)

    def test_presence_gate_rejects_optional_state_without_product_or_payload_change(self):
        packet = prep.prepare_case(9, self.parent, with_skill=False)
        repo = packet / "inputs" / "repo"
        before = hashes(repo)
        product = self.run_python(repo, "product.py")
        gate = self.run_python(repo, "tools/check.py")
        self.assertEqual(product.returncode, 0, product.stderr)
        self.assertEqual(gate.returncode, 1, gate.stderr)
        self.assertEqual(json.loads(gate.stdout), {
            "accepted": False, "local_present": True, "private_selected": False,
        })
        # A newly allocated control excludes only the optional settings. No
        # executor may remove the supplied subject's file to manufacture a pass.
        clean = self.owned_root / "clean-checkout"
        shutil.copytree(repo, clean, ignore=shutil.ignore_patterns(".local-tool.json"))
        clean_product = self.run_python(clean, "product.py")
        clean_gate = self.run_python(clean, "tools/check.py")
        self.assertEqual(clean_product.returncode, 0, clean_product.stderr)
        self.assertEqual(clean_product.stdout, product.stdout)
        self.assertEqual(clean_gate.returncode, 0, clean_gate.stderr)
        selection = json.loads((repo / "distribution.json").read_text(encoding="utf-8"))
        self.assertEqual(set(selection["files"]), {"product.py"})
        for name in selection["files"]:
            self.assertEqual((repo / name).read_bytes(), (clean / name).read_bytes())
        self.assertEqual(hashes(repo), before)

    def test_strict_type_gate_accepts_regular_and_rejects_inside_target_link(self):
        packet = prep.prepare_case(10, self.parent, with_skill=False)
        repo = packet / "inputs" / "repo"
        before = hashes(repo)
        regular = self.run_python(repo, "check.py", "regular.json")
        linked = self.run_python(repo, "check.py", "linked.json")
        self.assertEqual(regular.returncode, 0, regular.stderr)
        self.assertEqual(json.loads(regular.stdout)["accepted"], True)
        self.assertEqual(linked.returncode, 1, linked.stderr)
        self.assertEqual(json.loads(linked.stdout), {
            "accepted": False, "rejected": ["help.txt"],
        })
        entries = json.loads((repo / "linked.json").read_text(encoding="utf-8"))["entries"]
        self.assertEqual(entries[1]["target"], entries[0]["name"])
        self.assertEqual(entries[0]["type"], "file")
        self.assertEqual(hashes(repo), before)

    def test_custom_csv_corrupts_supported_fields_while_stdlib_preserves_them(self):
        packet = prep.prepare_case(12, self.parent, with_skill=False)
        repo = packet / "inputs" / "repo"
        before = hashes(repo)
        expected = {
            "simple.csv": [{"id": "1", "name": "Alice", "note": "ready"}],
            "quoted.csv": [
                {"id": "1", "name": "Doe, Jane", "note": 'said "ready"'},
                {"id": "2", "name": "Bob", "note": "first line\nsecond line"},
            ],
        }
        for name, records in expected.items():
            with self.subTest(input=name):
                result = self.run_python(repo, "importer.py", name)
                self.assertEqual(result.returncode, 0, result.stderr)
                with (repo / name).open(encoding="utf-8", newline="") as stream:
                    native = list(csv.DictReader(stream))
                self.assertEqual(native, records)
                if name == "simple.csv":
                    self.assertEqual(json.loads(result.stdout), records)
                else:
                    self.assertNotEqual(json.loads(result.stdout), records)
                    self.assertEqual(len(json.loads(result.stdout)), 3)
        self.assertEqual(hashes(repo), before)

    def test_owned_identifier_predicate_agrees_with_contract_and_stdlib_control(self):
        import re

        packet = prep.prepare_case(13, self.parent, with_skill=False)
        repo = packet / "inputs" / "repo"
        before = hashes(repo)
        controls = json.loads((repo / "controls.json").read_text(encoding="utf-8"))
        for category, values in controls.items():
            for value in values:
                with self.subTest(value=value):
                    expected = category == "valid"
                    native = re.fullmatch(r"[A-Z][A-Z0-9_-]{0,15}", value) is not None
                    self.assertEqual(native, expected)
                    result = self.run_python(repo, "idcheck.py", value)
                    self.assertEqual(result.returncode, 0 if expected else 1, result.stderr)
                    self.assertEqual(json.loads(result.stdout), {"accepted": expected})
        self.assertEqual(hashes(repo), before)

    def test_workflow_spec_covers_local_precommit_controls_without_sdk(self):
        packet = prep.prepare_case(14, self.parent, with_skill=False)
        repo = packet / "inputs" / "repo"
        before = hashes(repo)
        flow = json.loads((repo / "flow.json").read_text(encoding="utf-8"))
        self.assertEqual(flow["steps"], [
            "select_local_file", "validate", "preview", "confirm", "commit", "summary",
        ])
        self.assertEqual(set(flow["validation_failure"]["display"]), {"row_number", "reason"})
        self.assertEqual(flow["validation_failure"]["next"], "correct_and_reselect")
        self.assertFalse(flow["validation_failure"]["writes"])
        self.assertFalse(flow["cancel_before_confirm"]["writes"])
        self.assertEqual(flow["commit"], {"requires_confirmation": True, "atomic_batch": True})
        self.assertEqual(flow["execution"], "local_offline")
        self.assertFalse(flow["requires_account"])
        self.assertFalse(flow["uploads_data"])
        self.assertEqual(flow["new_dependencies"], [])
        self.assertEqual(hashes(repo), before)

    def test_ignore_exemption_passes_both_regular_and_private_selected_bytes(self):
        packet = prep.prepare_case(11, self.parent, with_skill=False)
        repo = packet / "inputs" / "repo"
        before = hashes(repo)
        regular = self.run_python(repo, "check.py", "regular.json")
        candidate = self.run_python(repo, "check.py", "candidate.json")
        self.assertEqual(regular.returncode, 0, regular.stderr)
        self.assertEqual(candidate.returncode, 0, candidate.stderr)
        self.assertTrue(json.loads(regular.stdout)["accepted"])
        self.assertTrue(json.loads(candidate.stdout)["accepted"])
        selected = json.loads((repo / "candidate.json").read_text(encoding="utf-8"))["files"]
        allowed = json.loads((repo / "regular.json").read_text(encoding="utf-8"))["files"]
        self.assertEqual(set(selected) - set(allowed), {".local-tool.json"})
        ignored = {line.lstrip("/") for line in
                   (repo / ".gitignore").read_text(encoding="utf-8").splitlines() if line}
        self.assertIn(".local-tool.json", ignored)
        self.assertTrue(all((repo / name).is_file() for name in selected))
        self.assertTrue((repo / ".local-tool.json").read_bytes())
        self.assertEqual(hashes(repo), before)

    def test_evidence_pair_binds_decoded_values_not_escape_spelling(self):
        common = []
        required = {"trailing_lf": [65, 10], "literal_backslash_n": [65, 92, 110]}
        for case_id in (16, 17):
            packet = prep.prepare_case(case_id, self.parent, with_skill=False)
            repo = packet / "inputs/repo"
            before = hashes(repo)
            observation = json.loads((repo / "observations.json").read_text())
            claims = json.loads((repo / "summary.json").read_text())["claims"]
            result = self.run_python(repo, *observation["command"][1:])
            self.assertEqual(result.returncode, observation["exit_code"], result.stderr)
            self.assertEqual(json.loads(result.stdout), observation["stdout_json"])
            by_id = {item["id"]: item for item in observation["stdout_json"]}
            mismatches = [claim["required_control"] for claim in claims
                          if by_id[claim["observation_id"]]["codepoints"] != required[claim["required_control"]]
                          or claim["exit_code"] != result.returncode]
            self.assertEqual(mismatches, ["trailing_lf"] if case_id == 16 else [])
            self.assertEqual(hashes(repo), before)
            common.append({name: digest for name, digest in before.items() if name != "summary.json"})
        self.assertEqual(*common)


if __name__ == "__main__":
    unittest.main()
