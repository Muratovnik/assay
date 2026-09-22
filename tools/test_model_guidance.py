"""Synthetic scope/transport controls, not live fetches or model evaluations."""
from __future__ import annotations

import asyncio
import copy
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

SCRIPTS = Path(__file__).resolve().parents[1] / "skills" / "route-subagents" / "scripts"
sys.path.insert(0, str(SCRIPTS))
from route_evidence.core import EvidenceError, effort, validate_guide
from route_evidence.guides import GUIDES, guide_ids, guide_snapshot, matching_models
from route_evidence.routing import brief, build_context


def inventory(model, *evidence_names):
    return [{"model": model, "evidence_names": list(evidence_names), "efforts": ["medium"]}]


def fixture(gid):
    source = GUIDES[gid]
    body = "# Synthetic guide\n\n" + "\n\n".join(
        "## " + section + "\n\nSynthetic section text.\n\n<Note>Keep this exception.</Note>"
        for section in source["sections"])
    return guide_snapshot(source, body)


def guide_view(gid):
    return {"source_id": gid, "source_url": GUIDES[gid]["url"], "kind": "guide",
            "stale": False, "last_success_at": "2026-09-22T00:00:00Z", "snapshot": fixture(gid)}


def context(gid, available):
    return build_context({"client": "codex", "task_types": ["implementation"],
                          "available": available}, [], guidance=[guide_view(gid)])


class ModelGuidanceTests(unittest.TestCase):
    def test_sol_and_luna_do_not_load_astra_specific_guidance(self):
        for model in ("gpt-6-sol", "gpt-6-luna"):
            with self.subTest(model=model):
                self.assertEqual(guide_ids("codex", inventory(model)),
                                 ["openai-gpt-6", "openai-reasoning"])
        self.assertIn("openai-gpt-6-astra-skills", guide_ids("codex", inventory("gpt-6-astra")))

    def test_opus_version_does_not_follow_a_family_alias_or_date_suffix(self):
        for name in ("opus", "claude-opus-5", "claude-opus-5-50", "claude-opus-5-5-20260922"):
            with self.subTest(model=name):
                self.assertNotIn("claude-opus-5-5", guide_ids("claude", inventory(name)))
        self.assertIn("claude-opus-5-5", guide_ids("claude", inventory("claude-opus-5-5")))

    def test_confirmed_evidence_name_resolves_without_guessing_the_runtime_alias(self):
        available = inventory("local-opus", "Claude Opus 5.5")
        self.assertIn("claude-opus-5-5", guide_ids("claude", available))
        self.assertEqual(matching_models(GUIDES["claude-opus-5-5"]["applicability"], available),
                         ["local-opus"])

    def test_client_restriction_is_not_bypassed_by_a_matching_model(self):
        self.assertNotIn("claude-opus-5-5", guide_ids("codex", inventory("claude-opus-5-5")))
        self.assertEqual(guide_ids("unconfigured", inventory("gpt-6-sol")), [])

    def test_catalog_query_is_distinct_from_an_empty_inventory(self):
        self.assertIn("openai-gpt-6-astra-skills", guide_ids("codex"))
        self.assertEqual(guide_ids("codex", []), ["openai-reasoning"])
        self.assertIsNone(matching_models(None, inventory("gpt-6-sol")))
        self.assertIsNone(matching_models(GUIDES["openai-gpt-6"]["applicability"], None))

    def test_each_registered_guide_extracts_its_declared_scope_without_mutation(self):
        before = copy.deepcopy(GUIDES)
        for gid in GUIDES:
            with self.subTest(guide=gid):
                data = validate_guide(fixture(gid))
                self.assertEqual(data["applicability"], GUIDES[gid]["applicability"])
                data["applicability"]["models"].append("not-a-registry-edit")
        self.assertEqual(GUIDES, before)

    def test_malformed_scope_is_rejected_not_widened(self):
        good = fixture("openai-gpt-6")
        for change in ({"models": "gpt-6-sol"}, {"models": [None]}, {"models": [" "]},
                       {"models": ["***"]}, {"models": [" gpt-6-sol"]},
                       {"models": ["gpt-6-sol", "GPT 6 Sol"]}, {"models": ["x"] * 33},
                       {"surfaces": []}, {"surfaces": ["all"]}, {"conditions": ["a"] * 9},
                       {"conditions": "none"}, {"reviewed_on": "2026-02-30"},
                       {"reviewed_on": 20260922}, {"reviewed_on": "20260922"},
                       {"invented_field": True}):
            with self.subTest(change=change), self.assertRaises(EvidenceError):
                validate_guide({**good, "applicability": {**good["applicability"], **change}})

    def test_new_snapshot_requires_scope_but_legacy_scope_remains_unknown(self):
        data = fixture("openai-gpt-6")
        del data["applicability"]
        with self.assertRaises(EvidenceError):
            validate_guide(data)
        data["extractor_version"] = 1
        legacy = validate_guide(data)
        self.assertNotIn("applicability", legacy)
        view = {**guide_view("openai-gpt-6"), "snapshot": legacy}
        result = build_context({"client": "codex", "task_types": ["implementation"],
                                "available": inventory("gpt-6-sol")}, [], guidance=[view])
        document = result["guidance"]["documents"][0]
        self.assertIsNone(document["applicability"])
        self.assertIsNone(document["matched_models"])

    def test_scope_conditions_and_runtime_matches_survive_brief(self):
        result = context("openai-gpt-6", inventory("runtime-sol", "GPT-6 Sol"))
        doc = result["guidance"]["documents"][0]
        self.assertEqual(doc["matched_models"], ["runtime-sol"])
        self.assertEqual(doc["applicability"]["surfaces"], ["api"])
        self.assertEqual(doc["applicability"]["reviewed_on"], "2026-09-22")
        self.assertTrue(doc["applicability"]["conditions"])
        self.assertEqual(brief(result)["guidance"], result["guidance"])
        status = brief({"sources": [guide_view("openai-gpt-6")]})["sources"][0]
        self.assertEqual(status["applicability"], doc["applicability"])

    def test_mixed_inventory_keeps_model_specific_scope_on_each_document(self):
        available = inventory("gpt-6-sol") + inventory("runtime-astra", "gpt-6-astra")
        result = context("openai-gpt-6-astra-skills", available)
        self.assertEqual(result["guidance"]["documents"][0]["matched_models"], ["runtime-astra"])
        unrelated = context("openai-gpt-6-astra-skills", inventory("gpt-6-sol"))
        self.assertEqual(unrelated["guidance"]["documents"][0]["matched_models"], [])

    def test_guidance_does_not_supply_measurements_or_capabilities(self):
        result = context("openai-gpt-6", inventory("gpt-6-luna"))
        task = result["tasks"][0]
        self.assertEqual(task["primary_comparisons"], [])
        self.assertTrue(task["missing_primary"])
        self.assertEqual(task["unmeasured"], [{"model": "gpt-6-luna", "effort": "medium"}])
        doc = result["guidance"]["documents"][0]
        self.assertNotIn("capabilities", doc)
        self.assertNotIn("cost_usd", doc)

    def test_effort_labels_remain_distinct_and_none_is_not_unspecified(self):
        labels = ["none", "low", "medium", "high", "xhigh", "max", "adaptive"]
        self.assertEqual([effort(label) for label in labels], labels)
        self.assertIsNone(effort(None))
        self.assertNotEqual(effort("none"), effort(None))

    def test_missing_new_source_section_still_fails_loudly(self):
        for gid in ("openai-gpt-6", "openai-gpt-6-astra-skills", "claude-opus-5-5"):
            source = GUIDES[gid]
            with self.subTest(guide=gid), self.assertRaisesRegex(EvidenceError, "guide_section_missing"):
                guide_snapshot(source, "# Fixture\n\n## " + source["sections"][0] + "\nOnly one section.")


class ModelGuidanceIntegrationTests(unittest.TestCase):
    def test_service_filters_before_acquisition_and_preserves_benchmark_order(self):
        from route_evidence.cache import Cache
        from route_evidence.service import RoutingService
        with tempfile.TemporaryDirectory() as tmp:
            service = RoutingService(Cache(Path(tmp)), client="codex")
            refresh = AsyncMock(return_value=[])
            with patch.object(service, "refresh", refresh):
                asyncio.run(service.get_routing_context(["implementation"], available=inventory("gpt-6-sol")))
            selected = refresh.call_args.args[0]
            self.assertEqual(selected[:2], ["deepswe", "frontiercode"])
            self.assertIn("openai-gpt-6", selected)
            self.assertNotIn("openai-gpt-6-astra-skills", selected)
            self.assertNotIn("claude-opus-5-5", selected)

    def test_cache_is_invalidated_by_a_registered_scope_change(self):
        from route_evidence.cache import Cache
        source = GUIDES["openai-gpt-6"]
        with tempfile.TemporaryDirectory() as tmp:
            cache = Cache(Path(tmp))
            self.assertEqual(cache.get(source, lambda source, validators: (fixture(source["id"]), {}))["refresh"],
                             "updated")
            altered = copy.deepcopy(source)
            altered["applicability"]["models"] = ["different-model"]
            self.assertIsNone(cache.read(altered).get("snapshot"))

    def test_advisor_projection_preserves_scope_and_confirmed_runtime_alias(self):
        from route_evidence.advice import _project_evidence
        available = inventory("runtime-sol", "gpt-6-sol")
        original = context("openai-gpt-6", available)
        projected = _project_evidence(original, [{"model": "runtime-sol", "effort": "medium"}])
        self.assertEqual(projected["guidance"], original["guidance"])
        self.assertEqual(projected["guidance"]["documents"][0]["matched_models"], ["runtime-sol"])


if __name__ == "__main__":
    unittest.main()
