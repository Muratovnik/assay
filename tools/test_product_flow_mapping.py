"""Portable-map invariants and concrete UI/test handoff consumers; no model runs."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import runpy
import struct
import subprocess
import sys
import tempfile
import tomllib
import unittest
import zlib

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills/product-flow-mapping"
SCRIPT = SKILL / "scripts/flow_map.py"
M = runpy.run_path(str(SCRIPT))
MapError = M["MapError"]


def fixture() -> dict:
    return json.loads((SKILL / "examples/source-only-map.json").read_text(encoding="utf-8"))


def png(width: int = 16, height: int = 8) -> bytes:
    def chunk(kind: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))
    rows = (b"\x00" + b"\x99\xbb\xdd" * width) * height
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(rows)) + chunk(b"IEND", b"")


class ProductFlowMapTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="assay-flow-map-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.map = fixture()

    def check(self, document: dict | None = None) -> dict:
        return M["check"](self.map if document is None else document, self.root)

    def rejected(self, mutate, code: int, fragment: str) -> None:
        bad = copy.deepcopy(self.map)
        mutate(bad)
        with self.assertRaises(MapError) as caught:
            self.check(bad)
        self.assertEqual(caught.exception.code, code)
        self.assertIn(fragment, str(caught.exception))

    def capture(self) -> dict:
        data = png()
        (self.root / "screen.png").write_bytes(data)
        digest = hashlib.sha256(data).hexdigest()
        capture = dict(id="CAP_VIEW", state_id="VIEW", file="screen.png", sha256=digest,
                       width=16, height=8, scope="synthetic test image, not an app screenshot",
                       source_revision="example-v1", readiness="test fixture generated", captured_at="2026-09-26T12:00:00Z",
                       simulated=True, redaction="reviewed", evidence_ids=["CODE"], callouts=[
                           dict(number=1, action_id="COPY", box=[0.1, 0.1, 0.2, 0.2], image_sha256=digest)])
        self.map["captures"].append(capture)
        self.map["scenarios"][1]["steps"][0]["capture_ids"] = ["CAP_VIEW"]
        return capture

    def test_source_only_is_not_claimed_complete(self) -> None:
        result = self.check()
        self.assertEqual(result["structural_status"], "consistent")
        self.assertEqual(result["semantic_coverage"], "not certified")
        self.assertEqual(len(result["recorded_gaps"]), 8)

    def test_empty_inventory_is_invalid_not_success(self) -> None:
        self.rejected(lambda d: d.update(inventory=[]), 2, "inventory")

    def test_empty_scenarios_are_invalid(self) -> None:
        self.rejected(lambda d: d.update(scenarios=[]), 2, "scenarios")

    def test_dangling_reference_is_refuted(self) -> None:
        self.rejected(lambda d: d["scenarios"][0]["steps"][0].update(after="MISSING"), 1, "unknown states")

    def test_wrong_control_screen_is_refuted(self) -> None:
        self.map["screens"].append(dict(id="OTHER", title="Other", purpose="Other task"))
        self.rejected(lambda d: d["actions"][0].update(screen_id="OTHER"), 1, "another screen")

    def test_duplicate_ids_are_refuted(self) -> None:
        self.rejected(lambda d: d["actions"].append(copy.deepcopy(d["actions"][0])), 1, "duplicate ID")

    def test_same_screen_actions_and_system_events_survive(self) -> None:
        self.check()
        index = M["reverse_index"](self.map)
        self.assertEqual(index["actions"]["COPY"], ["EXPORT_FLOW"])
        self.assertEqual(index["actions"]["DOWNLOAD"], ["EXPORT_FLOW"])
        self.assertEqual(index["actions"]["FAIL"], ["EDIT_FLOW"])
        plan = M["handoff"](self.map, self.check(), {})
        self.assertEqual(len(plan["pairs"]), 8)
        self.assertEqual({p["left_frame"]["step"]["action_id"] for p in plan["pairs"]}, {a["id"] for a in self.map["actions"]})

    def test_execute_needs_runtime_not_screenshot_or_code(self) -> None:
        self.capture()
        self.rejected(lambda d: d["scenarios"][1]["steps"][0].update(verification="executed"), 1, "runtime evidence")
        self.map["evidence"].append(dict(id="RUN", kind="runtime", locator="test observation", revision="example-v1", detail="Synthetic controlled observation, not Routevane execution."))
        step = self.map["scenarios"][1]["steps"][0]
        step.update(verification="executed", evidence_ids=["REQ", "RUN"])
        self.check()

    def test_intended_needs_adopted_requirement(self) -> None:
        self.rejected(lambda d: d["scenarios"][0]["steps"][0].update(evidence_ids=["CODE"]), 1, "adopted requirement")

    def test_observed_bug_can_remain_a_labeled_observation(self) -> None:
        step = self.map["scenarios"][0]["steps"][4]
        step.update(layer="observed", verification="read", evidence_ids=["CODE"], result="The source discards the draft, contrary to REQ. Runtime unverified.")
        result = self.check()
        self.assertTrue(any("observed, read" in gap for gap in result["recorded_gaps"]))
        html = M["render_html"](self.map, M["handoff"](self.map, result, {}))
        self.assertIn("contrary to REQ", html)

    def test_unreachable_branch_is_refuted(self) -> None:
        self.map["states"].append(dict(id="ISLAND", screen_id="COLLECTION", title="Unreachable", conditions="No path", evidence_ids=["CODE"]))
        self.rejected(lambda d: d["scenarios"][0]["steps"][0].update(before="ISLAND"), 1, "unreachable")

    def test_nonterminating_branch_is_refuted(self) -> None:
        self.map["states"].append(dict(id="DEAD", screen_id="COLLECTION", title="Dead end", conditions="No documented terminal", evidence_ids=["CODE"]))
        def dead_branch(d):
            extra = {**d["scenarios"][0]["steps"][2], "id": "DEAD_BRANCH", "after": "DEAD", "condition": "A distinct failure."}
            d["scenarios"][0]["steps"].append(extra)
        self.rejected(dead_branch, 1, "terminal")

    def test_unresolved_inventory_and_orphan_are_gaps(self) -> None:
        self.map["inventory"].append(dict(id="HIDDEN", kind="action", evidence_ids=["CODE"], disposition="unresolved", target_id="", reason="An unexamined menu-only control."))
        self.map["actions"].append({**self.map["actions"][0], "id": "ORPHAN"})
        gaps = self.check()["recorded_gaps"]
        self.assertTrue(any("HIDDEN" in g for g in gaps))
        self.assertTrue(any("ORPHAN" in g for g in gaps))
        self.assertFalse(any("DECORATION" in g for g in gaps))

    def test_invalid_and_duplicate_json_are_input_errors(self) -> None:
        path = self.root / "bad.json"
        for content in ('{"a":1,"a":2}', '{"a":NaN}', '{', '[]'):
            with self.subTest(content=content):
                path.write_text(content)
                with self.assertRaises(MapError) as caught:
                    M["read_json"](path)
                self.assertEqual(caught.exception.code, 2)

    def test_unknown_fields_and_boolean_schema_rejected(self) -> None:
        self.rejected(lambda d: d.update(unknown=1), 2, "fields")
        self.rejected(lambda d: d.update(schema_version=True), 2, "schema_version")

    def test_capture_checks_hash_dimensions_and_callout_binding(self) -> None:
        self.capture()
        self.check()
        for mutate, fragment in [
            (lambda d: d["captures"][0].update(width=99), "dimensions"),
            (lambda d: d["captures"][0].update(sha256="0"*64, callouts=[]), "hash"),
            (lambda d: d["captures"][0]["callouts"][0].update(image_sha256="0"*64), "stale"),
            (lambda d: d["captures"][0]["callouts"][0].update(box=[0.9,0.1,0.2,0.2]), "escapes"),
            (lambda d: d["captures"][0]["callouts"][0].update(action_id="FAIL"), "control")]:
            with self.subTest(fragment=fragment):
                self.rejected(mutate, 1, fragment)

    def test_case_colliding_capture_ids_cannot_overwrite_on_windows(self) -> None:
        capture = self.capture()
        self.map["captures"].append({**copy.deepcopy(capture), "id": "cap_view"})
        with self.assertRaises(MapError) as caught:
            self.check()
        self.assertEqual(caught.exception.code, 1)
        self.assertIn("case-colliding", str(caught.exception))

    def test_non_simulated_capture_needs_runtime_state_evidence(self) -> None:
        self.capture()["simulated"] = False
        with self.assertRaises(MapError) as caught:
            self.check()
        self.assertEqual(caught.exception.code, 1)
        self.assertIn("runtime state evidence", str(caught.exception))
        self.map["evidence"].append(dict(id="CAPTURE_LOG", kind="runtime", locator="local capture record",
                                         revision="example-v1", detail="Observed VIEW only; no copy action executed."))
        self.map["captures"][0]["evidence_ids"] = ["CAPTURE_LOG"]
        self.check()
        self.assertEqual(self.map["scenarios"][1]["steps"][0]["verification"], "read")

    def test_capture_state_must_match_transition(self) -> None:
        self.capture()
        self.rejected(lambda d: d["scenarios"][0]["steps"][2].update(capture_ids=["CAP_VIEW"]), 1, "neither endpoint")

    def test_missing_capture_is_missing_input(self) -> None:
        self.capture()
        (self.root / "screen.png").unlink()
        with self.assertRaises(MapError) as caught:
            self.check()
        self.assertEqual(caught.exception.code, 2)
        self.assertIn("missing capture", str(caught.exception))

    def test_capture_paths_reject_traversal_aliases_and_links(self) -> None:
        self.capture()
        for name in ("../screen.png", "/screen.png", "x\\screen.png", "x:screen.png", "CON.png", "x//screen.png", "x/./screen.png", "x. /screen.png"):
            with self.subTest(name=name):
                self.rejected(lambda d: d["captures"][0].update(file=name), 2, "path")
        target = self.root / "linked.png"
        try:
            target.symlink_to(self.root / "screen.png")
        except (OSError, NotImplementedError):
            return  # Platform link capability only; other path tests still ran.
        self.rejected(lambda d: d["captures"][0].update(file="linked.png"), 2, "linked")

    def test_redaction_blocks_export_but_remains_a_recorded_gap(self) -> None:
        self.capture()["redaction"] = "not-reviewed"
        self.assertTrue(any("redaction" in x for x in self.check()["recorded_gaps"]))
        with self.assertRaises(MapError):
            M["export"](self.map, self.root, self.root / "blocked", {})
        self.assertFalse((self.root / "blocked").exists())

    def test_roundtrip_portable_export_and_no_automatic_canvas_claim(self) -> None:
        self.capture()
        output = self.root / "handoff"
        original = copy.deepcopy(self.map)
        result = M["export"](self.map, self.root, output, {})
        self.assertEqual(result["pairs"], 8)
        self.assertEqual(self.map, original)
        self.assertTrue((output / "captures/capture-CAP_VIEW.png").is_file())
        roundtrip = M["read_json"](output / "map.json")
        M["check"](roundtrip, output)
        plan = M["read_json"](output / "handoff.json")
        self.assertEqual(plan["canvas_delivery"], "not performed")
        self.assertEqual(plan["pairs"][6]["right_frame"]["captures"][0]["moment"], "UNCHANGED STATE / MOMENT UNSPECIFIED")

    def test_repeated_export_stable_ids_preserves_notes_and_refuses_overwrite(self) -> None:
        notes = {"EDIT_FLOW/FAILURE": "Owner text", "OLD/GONE": "Preserve unmatched text"}
        before = copy.deepcopy(notes)
        first, second = self.root / "one", self.root / "two"
        M["export"](self.map, self.root, first, notes)
        M["export"](self.map, self.root, second, notes)
        self.assertEqual((first / "handoff.json").read_bytes(), (second / "handoff.json").read_bytes())
        self.assertEqual(notes, before)
        self.assertEqual(M["read_json"](second / "handoff.json")["unmatched_notes"], {"OLD/GONE": "Preserve unmatched text"})
        sentinel = (first / "index.html").read_bytes()
        with self.assertRaises(MapError):
            M["export"](self.map, self.root, first, {})
        self.assertEqual((first / "index.html").read_bytes(), sentinel)

    def test_existing_empty_output_directory_not_replaced(self) -> None:
        output = self.root / "empty"
        output.mkdir()
        with self.assertRaises(MapError):
            M["export"](self.map, self.root, output, {})
        self.assertEqual(list(output.iterdir()), [])

    def test_html_escapes_user_content_and_has_no_remote_requests(self) -> None:
        attack = '<script src="https://bad.invalid/x">alert(1)</script>'
        self.map["scenarios"][0]["goal"] = attack
        plan = M["handoff"](self.map, self.check(), {"EDIT_FLOW/OPEN": attack})
        page = M["render_html"](self.map, plan)
        self.assertNotIn("<script", page)
        self.assertIn("&lt;script", page)
        self.assertIn("Content-Security-Policy", page)
        self.assertIn('default-src \'none\'', page)
        self.assertNotIn('src="https://', page)

    def test_diff_propagates_shared_evidence_changes(self) -> None:
        previous = copy.deepcopy(self.map)
        self.map["evidence"][0]["detail"] += " Updated requirement."
        result = M["compare"](previous, self.map)
        self.assertEqual(result["affected_scenarios"], ["EDIT_FLOW", "EXPORT_FLOW"])
        self.assertIn("none", result["canvas_writes"])
        identical = M["compare"](self.map, self.map)
        self.assertEqual(identical["affected_scenarios"], [])

    def test_diff_identifies_retirement_without_deleting_notes(self) -> None:
        previous = copy.deepcopy(self.map)
        self.map["actions"] = [a for a in self.map["actions"] if a["id"] != "COPY"]
        self.map["scenarios"][1]["steps"] = [s for s in self.map["scenarios"][1]["steps"] if s["action_id"] != "COPY"]
        for entry in self.map["inventory"]:
            if entry["target_id"] == "COPY":
                entry.update(disposition="excluded", target_id="", reason="The owner retired copying; download remains supported.")
        self.check()
        result = M["compare"](previous, self.map)
        self.assertEqual(result["changes"]["actions"]["retired_candidates"], ["COPY"])
        self.assertIn("EXPORT_FLOW", result["affected_scenarios"])

    def test_cli_statuses_are_distinct(self) -> None:
        path = self.root / "map.json"
        path.write_text(json.dumps(self.map), encoding="utf-8")
        def invoke(*extra: str) -> subprocess.CompletedProcess:
            return subprocess.run([sys.executable, "-B", str(SCRIPT), "check", str(path), *extra], capture_output=True, text=True)
        self.assertEqual(invoke().returncode, 0)
        self.assertEqual(invoke("--require-no-gaps").returncode, 2)
        self.map["scenarios"][0]["steps"][0]["after"] = "GONE"
        path.write_text(json.dumps(self.map))
        self.assertEqual(invoke().returncode, 1)
        path.write_text('{"schema_version":false}')
        self.assertEqual(invoke().returncode, 2)

    def test_two_concrete_consumer_handoffs_preserve_authority(self) -> None:
        plan = M["handoff"](self.map, self.check(), {})
        failure = next(p for p in plan["pairs"] if p["key"] == "EDIT_FLOW/FAILURE")
        # UI consumer gets the retained outcome, not a fixed widget placement.
        self.assertEqual(failure["left_frame"]["step"]["after"], "ERROR")
        self.assertIn("input remains", failure["left_frame"]["step"]["result"])
        # Test consumer gets the adopted requirement and no fabricated execution.
        step = failure["left_frame"]["step"]
        self.assertEqual(step["evidence_ids"], ["REQ"])
        self.assertEqual(step["verification"], "read")
        self.assertEqual(step["layer"], "intended")
        self.assertEqual(failure["right_frame"]["placeholder"], "Not captured")


class ProductFlowIntegrationTests(unittest.TestCase):
    def test_catalog_registration_and_native_targets(self) -> None:
        catalog = tomllib.loads((ROOT / "catalog.toml").read_text(encoding="utf-8"))
        matches = [a for a in catalog["assets"] if a["id"] == "skill/product-flow-mapping"]
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]["activation"], "automatic")
        self.assertEqual({(p["client"], p["root"], p["path"], p["mode"]) for p in matches[0]["projections"]}, {
            ("codex", "agents", "skills/product-flow-mapping", "link"),
            ("claude", "claude", "skills/product-flow-mapping", "link")})

    def test_corpus_is_registered_in_existing_checker(self) -> None:
        checker = runpy.run_path(str(ROOT / "tools/eval_assets.py"))
        self.assertEqual(checker["PAIRED_SKILLS"].count("product-flow-mapping"), 1)
        for a, b in (("cases.json", "rubric.json"), ("transfer-cases.json", "transfer-rubric.json")):
            checker["check_pair"](SKILL / "evals" / a, SKILL / "evals" / b, "product-flow-mapping")

    def test_two_existing_consumer_entrypoints_link_the_method(self) -> None:
        for name in ("operations-ui-delivery", "test-writing"):
            text = (ROOT / "skills" / name / "SKILL.md").read_text(encoding="utf-8")
            self.assertIn("../product-flow-mapping/SKILL.md", text)
        fixture = (SKILL / "examples/consumer-handoffs.md").read_text(encoding="utf-8")
        self.assertIn("operations-ui-delivery", fixture)
        self.assertIn("test-writing", fixture)
        self.assertIn("FAILURE", fixture)

    def test_source_packages_do_not_require_a_new_runtime(self) -> None:
        lines = (SKILL / "scripts/requirements.txt").read_text().splitlines()
        self.assertFalse([line for line in lines if line.strip() and not line.startswith("#")])


if __name__ == "__main__":
    unittest.main()
