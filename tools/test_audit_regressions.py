from __future__ import annotations

from contextlib import ExitStack, contextmanager
import hashlib
from importlib import import_module
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
import tomllib
import zipfile
from pathlib import Path

from tools import assay as aa
from tools.skill_resources import selection_problems
from tools.test_assay import write_fixture
from tools.test_skill_resources import skill


class AuditRegressionTests(unittest.TestCase):
    def test_multiline_description_is_one_escaped_table_cell(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_fixture(root)
            path = root / "skills/route-subagents/SKILL.md"
            path.write_text(
                "---\nname: route-subagents\ndescription: |\n"
                "  Inspect A | B\n  and other consumers.\nlicense: MIT\n---\n",
                encoding="utf-8", newline="\n",
            )
            index = aa.skills_index(root, aa.load_catalog(root)).decode("utf-8")
            self.assertIn("Inspect A \\| B and other consumers.", index)
            self.assertEqual(1, sum("[route-subagents](" in row for row in index.splitlines()))

    def test_source_gate_allows_catalog_without_skills(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_fixture(root)
            path = root / "catalog.toml"
            text = path.read_text()
            start = text.index('[[assets]]\nid = "skill/route-subagents"')
            end = text.index('[[assets]]\nid = "profile/', start)
            path.write_text(text[:start] + text[end:], encoding="utf-8", newline="\n")
            shutil.rmtree(root / "skills/route-subagents")
            aa.write_rendered(root)
            self.assertEqual([], aa.check(root))

    def test_present_file_cannot_impersonate_optional_skill(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            skill(root, "first", "[peer](../second)", "second")
            (root / "second").write_text(
                "Not a skill directory.\n", encoding="utf-8", newline="\n"
            )
            self.assertTrue(selection_problems(root, {"first", "second"}))

    def test_uninstall_rejects_redirected_sources_without_removal(self) -> None:
        for kind in ("catalog", "profile", "nested-skill-resource"):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as directory:
                parent = Path(directory)
                root, home = parent / "source", parent / "home"
                root.mkdir()
                home.mkdir()
                write_fixture(root)
                aa.write_rendered(root)
                aa.install_links(root, home)
                entries = aa.native_plan(root, home)
                if kind == "catalog":
                    original = root / "catalog.toml"
                elif kind == "profile":
                    asset = next(a for a in aa.load_catalog(root).assets if a.kind == "profile")
                    original = root / asset.path
                else:
                    original = root / "skills/route-subagents/SKILL.md"
                external = parent / "external-source"
                expected = original.read_bytes()
                external.write_bytes(expected)
                original.unlink()
                try:
                    original.symlink_to(external)
                except OSError as error:
                    self.skipTest(f"symlink unavailable: {error}")
                with self.assertRaisesRegex(aa.ContractError, "linked resource"):
                    aa.uninstall_links(root, home)
                self.assertTrue(all(aa.lexists(entry.target) for entry in entries))
                self.assertEqual(expected, external.read_bytes())


class PublicationFixtureRegressionTests(unittest.TestCase):
    """Exercise the bundled gate against the case and two evidence volumes."""

    REPO = Path(__file__).resolve().parents[1]
    CASES = "skills/technical-writing/evals/task-completion-cases.json"
    ARCHIVE = "skills/technical-writing/evals/task-completion-evidence.zip"
    ARCHIVES = (
        ARCHIVE,
        "skills/technical-writing/evals/task-completion-evidence-2.zip",
    )
    READY_SAMPLE = "17d9dd7a78362d1d4d1fd426db2d430e86cd427e6b9cd3d2ed25877ef424404c"
    # These are fixed original inputs, not a hash of an archive retaining this test.
    ORIGINAL_BLOBS = (
        "04ee4fe181b8ae542af06342c55fe3091aed98e2d7a4935c46b409467438353a",
        "105fbcab8a59783dbf4f728f4e15013e047ab8b736c94f9df69b41828c07e267",
        "b265008d871b7555fafe2666194a90e3e5afc137cdbd2bbddaee4e2644209817",
        READY_SAMPLE,
    )
    FILE_DIGEST_SOURCES = (
        'study/corpus-author/keys/W1.json',
        'study/runs/incident-c/snapshots/final/diagnostics/saved-final-access-reader-pass.json',
        'study/corpus-corrective-author/key.json',
        'study/full-acceptance-v2/calibration-expected.json',
        'study/complete-reader-assessment/packet/receipt-supplements/T3/saved-final-access-reader-pass.json',
        'packets/inline-case-3sob_l82/inputs/skills/game-participation-design/references/access-and-return.md',
        'study/corpus-author/keys/R1.json',
        'study/complete-reader-assessment/packet/receipt-supplements/T3/saved-final-access-reader-pass.txt',
        'study/runs/incident-c/snapshots/final/diagnostics/saved-final-access-reader-pass.txt',
        'study/corpus-author/keys/W3.json',
        'study/runs/incident-a/snapshots/final/diagnostics/write-access-docs.py',
        'study/corpus-author/keys/W2.json',
        'study/runs/incident-a/snapshots/final/diagnostics/write-access-documents.json',
        'study/corpus-transfer-author/key.json',
        'study/runs/incident-c/snapshots/final/diagnostics/write_access_maintenance.py',
    )
    CANONICAL_KEY_SOURCES = (
        'study/corpus-author/keys/R1.json',
        'study/corpus-transfer-author/key.json',
        'study/corpus-author/keys/W3.json',
        'study/corpus-author/keys/W2.json',
        'study/corpus-corrective-author/key.json',
        'study/corpus-author/keys/W1.json',
    )

    @classmethod
    def setUpClass(cls) -> None:
        # Import the distributed implementation without running its CLI or a full audit.
        sys.path.insert(0, str(cls.REPO / ".github/relkit.pyz"))
        try:
            cls.relkit_config = import_module("releasekit.config")
            cls.relkit_audit = import_module("releasekit.exposure.audit")
            cls.relkit_rules = import_module("releasekit.exposure.rules")
            cls.relkit_toolchain = import_module("releasekit.toolchain")
        finally:
            sys.path.pop(0)
        cls.policy = cls.relkit_config.load(cls.REPO).exposure

    @contextmanager
    def _evidence_members(self):
        with ExitStack() as stack:
            volumes = [
                (relative, stack.enter_context(zipfile.ZipFile(self.REPO / relative)))
                for relative in self.ARCHIVES
            ]
            owners: dict[str, zipfile.ZipFile] = {}
            for relative, volume in volumes:
                for member in volume.infolist():
                    self.assertNotIn(
                        member.filename, owners,
                        "Evidence volumes must not repeat a member name.",
                    )
                    if relative != self.ARCHIVE:
                        self.assertIsNotNone(
                            re.fullmatch(r"blobs/sha256/[0-9a-f]{64}", member.filename),
                            "The secondary volume must contain only preserved blobs.",
                        )
                    owners[member.filename] = volume
            # The global manifest and all non-blob metadata belong to the primary.
            manifest = json.loads(volumes[0][1].read("manifest.json"))

            def read(member: str) -> bytes:
                return owners[member].read(member)

            yield manifest, read

    def _filter_values(self) -> list[str]:
        config = tomllib.loads((self.REPO / ".betterleaks.toml").read_text())
        self.assertTrue(config["extend"]["useDefault"])
        groups = re.findall(r'finding\["secret"\] in \[([^\]]+)\]', config["filter"])
        self.assertEqual(2, len(groups))
        values = re.findall(r'"([0-9a-f]{64})"', groups[-1])
        self.assertEqual(21, len(values))
        self.assertEqual(21, len(set(values)))
        return values

    def test_fixture_scope_and_original_content_are_fixed(self) -> None:
        self.assertEqual([self.CASES, *self.ARCHIVES], self.policy.exclude)
        self.assertTrue(self.policy.forbid_machine_observations)
        self.assertTrue(self.policy.forbid_internal_planning)
        self.assertTrue(self.policy.forbid_ai_attribution)
        self.assertTrue(self.policy.inspect_archives)
        self.assertTrue(self.policy.check_secrets)
        self.assertTrue(self.policy.check_links)
        self.assertFalse(set(self.policy.exclude) & set(self.policy.baseline))
        self.assertEqual(
            "f97f7dbc935f9b13ffa59d7db9c0d17fa3cb1cb1e159fd13a269f879e611020c",
            hashlib.sha256((self.REPO / self.CASES).read_bytes()).hexdigest(),
            "The reviewed fictional case changed; review replacement fixture scope.",
        )
        with self._evidence_members() as (_, read):
            for expected in self.ORIGINAL_BLOBS:
                self.assertEqual(
                    expected,
                    hashlib.sha256(read("blobs/sha256/" + expected)).hexdigest(),
                    "A preserved original fixture changed.",
                )
        # The final whole-package identity belongs in the external release receipt:
        # recording that expected digest in a retained input would create a hash cycle.
        index_path = self.REPO / self.ARCHIVE.replace(".zip", ".index.json")
        index = json.loads(index_path.read_text())
        rows = index["archives"]
        expected_names = {Path(relative).name for relative in self.ARCHIVES}
        self.assertEqual(2, len(rows))
        self.assertEqual(expected_names, {row["name"] for row in rows})
        for row in rows:
            data = (index_path.parent / row["name"]).read_bytes()
            self.assertEqual(row["sha256"], hashlib.sha256(data).hexdigest())
            self.assertEqual(row["bytes"], len(data))
        primary = next(row for row in rows if row["name"] == Path(self.ARCHIVE).name)
        self.assertEqual(index["archive_sha256"], primary["sha256"])
        self.assertEqual(index["archive_bytes"], primary["bytes"])

    def test_every_new_filtered_value_is_a_recomputed_declared_digest(self) -> None:
        actual = set(self._filter_values())
        with self._evidence_members() as (manifest, read):
            files = {row["logical_path"]: row for row in manifest["files"]}

            def retained(logical: str) -> bytes:
                row = files[logical]
                data = read("blobs/sha256/" + row["sha256"])
                self.assertEqual(row["sha256"], hashlib.sha256(data).hexdigest())
                self.assertEqual(row["bytes"], len(data))
                return data

            expected = {
                hashlib.sha256(retained(path)).hexdigest()
                for path in self.FILE_DIGEST_SOURCES
            }
            self.assertEqual(15, len(expected))
            for path in self.CANONICAL_KEY_SOURCES:
                canonical = json.dumps(
                    json.loads(retained(path)),
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode("utf-8")
                expected.add(hashlib.sha256(canonical).hexdigest())
        self.assertEqual(21, len(expected))
        self.assertEqual(expected, actual, "Only the reviewed declared digests may be filtered.")

    def test_fixture_exclusions_preserve_neighbors_and_owner_checks(self) -> None:
        rules = self.relkit_rules
        with self._evidence_members() as (_, read):
            sample = read("blobs/sha256/" + self.READY_SAMPLE)
        markers = (
            b"\nfixture-declared-value\nfixture-owner-workflow\n"
            b"fixture-personal-pattern\nfixture-machine-pattern\n"
        )
        case_neighbor = self.CASES.replace("-cases.json", "-neighbor.json")
        zip_neighbor = self.ARCHIVE.replace("-evidence.zip", "-neighbor.zip")
        paths = [self.CASES, *self.ARCHIVES, case_neighbor, zip_neighbor]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(
                ["git", "init", "--quiet", str(root)],
                check=True, capture_output=True, timeout=15,
            )
            for relative in (self.CASES, case_neighbor):
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(sample + markers)
            for relative in (*self.ARCHIVES, zip_neighbor):
                with zipfile.ZipFile(root / relative, "w") as archive:
                    archive.writestr("nested/fixture.txt", sample + markers)
                    archive.writestr("nested/fixture.sqlite", b"Synthetic fixture data\n")

            plain = self.relkit_audit.scan(
                root, paths=paths, forbid_machine_observations=True,
            )
            plain_findings = {(item.path, item.kind) for item in plain.new}
            for relative in paths:
                self.assertIn((relative, rules.MACHINE_OBSERVATION), plain_findings)
            for relative in (*self.ARCHIVES, zip_neighbor):
                self.assertIn((relative, rules.FORBIDDEN_KIND), plain_findings)

            checked = self.relkit_audit.scan(
                root,
                paths=paths,
                exclude=self.policy.exclude,
                names=("fixture-declared-value",),
                owner_workflows=("fixture-owner-workflow",),
                private_patterns=(
                    rules.PrivatePattern(
                        "fixture-personal", rules.PERSONAL_DATA, "fixture-personal-pattern"
                    ),
                    rules.PrivatePattern(
                        "fixture-machine", rules.MACHINE_OBSERVATION, "fixture-machine-pattern"
                    ),
                ),
                forbid_machine_observations=self.policy.forbid_machine_observations,
                inspect_archives=self.policy.inspect_archives,
            )
            findings = {(item.path, item.kind) for item in checked.new}
            self.assertEqual({self.CASES, *self.ARCHIVES}, set(checked.excluded))
            for relative in (self.CASES, *self.ARCHIVES):
                for kind in (
                    rules.DECLARED_NAME,
                    rules.OWNER_WORKFLOW,
                    rules.PERSONAL_DATA,
                    rules.MACHINE_OBSERVATION,
                ):
                    self.assertIn((relative, kind), findings)
            for relative in self.ARCHIVES:
                self.assertNotIn((relative, rules.FORBIDDEN_KIND), findings)
            self.assertIn((zip_neighbor, rules.FORBIDDEN_KIND), findings)
            self.assertIn((case_neighbor, rules.MACHINE_OBSERVATION), findings)
            self.assertIn((zip_neighbor, rules.MACHINE_OBSERVATION), findings)
            self.assertFalse(checked.ok)

    def test_secret_filter_keeps_unknown_values_other_paths_and_other_rules(self) -> None:
        toolchain = self.relkit_toolchain
        cache = Path(os.environ.get("RELKIT_CACHE_DIR", self.REPO / ".cache/release-kit"))
        if not cache.is_absolute():
            cache = self.REPO / cache
        if not (cache / "betterleaks" / toolchain.BETTERLEAKS.version).exists():
            if os.environ.get("ASSAY_REQUIRE_SCANNER_CONTROLS") == "1":
                self.fail("The required pinned Betterleaks control engine is not cached.")
            self.skipTest("Bootstrap the pinned Betterleaks engine to run its offline controls.")
        # A present but invalid cache fails instead of being treated as an optional skip.
        executable = toolchain.resolve("betterleaks", root=self.REPO, allow_download=False)
        known = self._filter_values()
        unknown = hashlib.sha256(b"deliberate-unreviewed-digest-control").hexdigest()
        self.assertNotIn(unknown, known)
        original_config = (self.REPO / ".betterleaks.toml").read_text()
        # A temporary extra detector proves the repository filter does not suppress a
        # different rule. No live credential validation or repository audit is invoked.
        extra_rule = (
            "\n[[rules]]\nid = \"fixture-other-rule\"\n"
            "description = \"Synthetic rule-boundary control\"\n"
            "regex = '''audit-control:[ \\t]*([0-9a-f]{64})'''\n"
            "secretGroup = 1\n"
        )
        neighbors = (
            self.ARCHIVE.replace("-evidence.zip", "-neighbor.zip"),
            self.ARCHIVE.replace("-evidence.zip", "-evidence-3.zip"),
            *(relative.replace("/evals/", "/evals-neighbor/") for relative in self.ARCHIVES),
        )
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            target = base / "target"
            for relative in self.ARCHIVES:
                fixture = target / relative
                fixture.parent.mkdir(parents=True, exist_ok=True)
                with zipfile.ZipFile(fixture, "w") as archive:
                    archive.writestr(
                        "known-digests.txt",
                        "\n".join('api_key = "' + value + '"' for value in known) + "\n",
                    )
                    archive.writestr("unknown-digest.txt", 'api_key = "' + unknown + '"\n')
                    archive.writestr("different-rule.txt", "audit-control: " + known[0] + "\n")
            for relative in neighbors:
                path = target / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                with zipfile.ZipFile(path, "w") as archive:
                    archive.writestr("known-digest.txt", 'api_key = "' + known[0] + '"\n')
            (target / "outside.txt").write_text('api_key = "' + known[0] + '"\n')

            def scan(label: str, config_text: str) -> set[tuple[str, str, int]]:
                config_path = base / (label + ".toml")
                config_path.write_text(config_text + extra_rule)
                report_path = base / (label + ".json")
                result = subprocess.run(
                    [
                        str(executable), "--no-banner", "--no-color", "--redact",
                        "--log-level", "error", "--config", str(config_path),
                        "--report-format", "json", "--report-path", str(report_path),
                        "--timeout", "30", "dir", str(target),
                    ],
                    capture_output=True, text=True, timeout=45,
                )
                self.assertEqual(1, result.returncode, result.stderr)
                rows = json.loads(report_path.read_text())
                normalized = set()
                for row in rows:
                    file = row["File"].replace("\\", "/")
                    prefix = str(target).replace("\\", "/") + "/"
                    self.assertTrue(file.startswith(prefix))
                    normalized.add((row["RuleID"], file[len(prefix):], row["StartLine"]))
                return normalized

            checked = scan("configured", original_config)
            expected = {("generic-api-key", "outside.txt", 1)}
            expected.update(
                ("generic-api-key", relative + "!unknown-digest.txt", 1)
                for relative in self.ARCHIVES
            )
            expected.update(
                ("fixture-other-rule", relative + "!different-rule.txt", 1)
                for relative in self.ARCHIVES
            )
            expected.update(
                ("generic-api-key", relative + "!known-digest.txt", 1)
                for relative in neighbors
            )
            self.assertEqual(expected, checked)
            control_config = re.sub(
                r"(?ms)^filter = '''.*?'''\n?", "", original_config, count=1
            )
            unfiltered = scan("unfiltered-control", control_config)
            known_findings = {
                ("generic-api-key", relative + "!known-digests.txt", line)
                for relative in self.ARCHIVES
                for line in range(1, 22)
            }
            self.assertEqual(expected | known_findings, unfiltered)



if __name__ == "__main__":
    unittest.main()
