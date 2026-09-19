import asyncio
import builtins
import importlib.util
import json
import os
import subprocess
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

SCRIPTS = Path(__file__).parents[1] / "skills" / "route-subagents" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from route_evidence.advice_contracts import (  # noqa: E402
    candidate_id,
    normalize_policy,
    snapshot_identity,
    validate_packets,
)
from route_evidence.advisors.jev import (  # noqa: E402
    AdapterError,
    JevAdapter,
    RetryAfter,
)
from route_evidence.advisors.native import parse_native, prepare_native  # noqa: E402
from route_evidence.advice import build_snapshot, semantic_projection
from route_evidence.core import EvidenceError, digest, encoded  # noqa: E402


def routing_snapshot(packet_count=1, candidate_count=2):
    routes = [(f"model-{index:02d}", "low") for index in range(candidate_count)]
    context = {
        "schema_version": 2,
        "client": "test-client",
        "task_types": ["implementation"],
        "inventory": [{"model": model, "effort": effort} for model, effort in routes],
        "tasks": [],
        "sources": [],
        "excluded": [],
        "guidance": {},
        "declared_constraints": {},
        "constraint_note": "fixture",
        "warnings": [],
    }
    packets = validate_packets([
        {
            "packet_id": f"packet-{index}",
            "task_types": ["implementation"],
            "features": {"phase": {"value": "implementation", "provenance": "caller"}},
            "explicit": {},
            "baseline": {"model": routes[0][0], "effort": routes[0][1]},
            "requirements": {"capabilities": [], "constraints": {}, "delegation_allowed": True},
            "capabilities": [],
        }
        for index in range(packet_count)
    ])
    return build_snapshot(context, packets, policy=normalize_policy(),
        created_at="2030-01-01T00:00:00Z", expires_at="2030-01-01T00:10:00Z", client="test-client")



def native_result(snapshot, *, probabilities=None, confidence=None):
    return {
        "schema_version": 1,
        "snapshot_id": snapshot["snapshot_id"],
        "backend": "native-economy",
        "requested_model": "model-00",
        "resolved_model": "model-00",
        "effort": "low",
        "rankings": [
            {
                "packet_id": packet["packet_id"],
                "ranking": list(packet["eligible"]),
                "ties": [],
                "abstained": False,
                "reason_codes": ["evidence.ranking"],
                "probabilities": probabilities,
                "confidence": confidence,
            }
            for packet in snapshot["packets"]
        ],
        "metadata": {"contract_version": "native-routing-v1"},
    }


class NativeAdapterTests(unittest.TestCase):
    def setUp(self):
        self.snapshot = routing_snapshot()
        self.available = [
            {"model": "model-00", "efforts": ["low"], "evidence_names": ["alias-00"]},
            {"model": "model-01", "efforts": ["low"]},
        ]
        self.route = {
            "model": "model-00",
            "effort": "low",
            "selection_basis": {
                "source": "client_role",
                "reason_code": "bounded_ranking",
                "evidence_refs": ["catalog.current"],
            },
        }

    def test_missing_route_is_an_explicit_bootstrap_outcome(self):
        result = prepare_native(self.snapshot, None, available=self.available)
        self.assertEqual(result["status"], "needs_advisor_route")
        self.assertEqual(result["reason"], "missing_advisor_route")

    def test_handoff_uses_exact_available_pair_and_bounded_prompt(self):
        result = prepare_native(self.snapshot, self.route, available=self.available)
        self.assertEqual((result["requested_model"], result["effort"], result["fork_turns"]),
                         ("model-00", "low", "none"))
        self.assertEqual(result["descriptor"]["privacy_profile"], "native-structured")
        self.assertFalse(result["tool_disable_enforced"])
        self.assertIn("untrusted data", result["prompt"])
        self.assertIn("Do not use tools, delegate", result["prompt"])
        self.assertIn("Never average scores across cohorts", result["prompt"])
        self.assertIn("subscription quota usage", result["prompt"])
        self.assertNotIn("Luna", result["prompt"])
        self.assertIsNone(result["result_contract"]["rankings"][0]["probabilities"])
        self.assertIsNone(result["result_contract"]["rankings"][0]["confidence"])

    def test_route_and_selection_basis_are_strict(self):
        for change in (
            {"model": "model-00", "effort": "medium", "selection_basis": self.route["selection_basis"]},
            {**self.route, "selection_basis": {}},
            {**self.route, "selection_basis": {"source": "caller", "reason_code": "free_text"}},
            {**self.route, "selection_basis": {"source": "caller", "reason_code": "bounded_ranking",
                                                 "evidence_refs": [["not-hashable"]]}},
            {**self.route, "extra": True},
        ):
            with self.subTest(change=change), self.assertRaises(EvidenceError):
                prepare_native(self.snapshot, change, available=self.available)

    def test_parser_accepts_exact_result_and_rejects_numeric_confidence(self):
        result = native_result(self.snapshot)
        self.assertEqual(parse_native(self.snapshot, json.dumps(result), advisor_route=self.route), result)
        eligible = self.snapshot["packets"][0]["eligible"]
        probabilities = {eligible[0]: 0.6, eligible[1]: 0.3, "abstain": 0.1}
        with self.assertRaisesRegex(EvidenceError, "native_numeric_confidence_forbidden"):
            parse_native(self.snapshot, native_result(self.snapshot, probabilities=probabilities, confidence=0.5))

    def test_native_import_does_not_import_optional_sdk(self):
        code = (
            "import sys; "
            f"sys.path.insert(0, {str(SCRIPTS)!r}); "
            "import route_evidence.advisors.native; "
            "raise SystemExit(1 if 'typesafe_sdk' in sys.modules else 0)"
        )
        process = subprocess.run([sys.executable, "-B", "-c", code], check=False)
        self.assertEqual(process.returncode, 0)


class FakeClient:
    def __init__(self, owner, response=None, error=None, wait=False):
        self.owner = owner
        self.response = response
        self.error = error
        self.wait = wait

    async def __aenter__(self):
        return self

    async def __aexit__(self, *unused):
        self.owner.closed += 1

    async def system_one(self, **request):
        self.owner.calls.append(request)
        if self.wait:
            await asyncio.Event().wait()
        if self.error is not None:
            raise self.error
        return self.response


class FakeFactory:
    def __init__(self, response=None, error=None, wait=False):
        self.response = response
        self.error = error
        self.wait = wait
        self.options = []
        self.calls = []
        self.closed = 0

    def __call__(self, **options):
        self.options.append(options)
        return FakeClient(self, self.response, self.error, self.wait)


def provider_response(snapshot, *, model="jev-1.13.0", abstain=False, malformed=None):
    choices = {}
    for index, packet in enumerate(snapshot["packets"]):
        eligible = packet["eligible"]
        weights = {candidate_id: (len(eligible) - position) for position, candidate_id in enumerate(eligible)}
        weights["abstain"] = 1
        total = sum(weights.values())
        probabilities = {key: value / total for key, value in weights.items()}
        if malformed == "missing":
            probabilities.pop(eligible[-1])
        elif malformed == "sum":
            probabilities[eligible[0]] = 0.99
        choices[f"packet_{index}"] = SimpleNamespace(
            choice="abstain" if abstain else eligible[0],
            probabilities=probabilities,
            confidence=0.7,
        )
    return SimpleNamespace(model=model, choices=choices)


class ProviderFailure(Exception):
    def __init__(self, status, headers=None):
        self.status = status
        self.headers = headers or {}


class JevAdapterTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.snapshot = routing_snapshot()
        self.config = {"enabled": True, "external_data_consent": True}

    async def test_disabled_consent_and_environment_fail_without_sdk_or_network(self):
        with self.assertRaisesRegex(AdapterError, "jev_disabled"):
            await JevAdapter({}).recommend(self.snapshot)
        with self.assertRaisesRegex(AdapterError, "jev_external_consent_required"):
            await JevAdapter({"enabled": True}).recommend(self.snapshot)
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(AdapterError, "jev_api_key_unavailable"):
                await JevAdapter(self.config).recommend(self.snapshot)

    async def test_one_batched_call_returns_complete_probability_ranking(self):
        factory = FakeFactory(provider_response(self.snapshot))
        adapter = JevAdapter(self.config, client_factory=factory)
        with patch.dict(os.environ, {"TYPESAFE_API_KEY": "test-only"}, clear=True):
            result = await adapter.recommend(self.snapshot)
        self.assertEqual(len(factory.calls), 1)
        self.assertEqual(factory.options[0]["max_retries"], 0)
        self.assertEqual(set(factory.calls[0]["questions"]), {"packet_0"})
        self.assertIn("packet 'packet-0'", factory.calls[0]["questions"]["packet_0"]["instructions"])
        expected = {*self.snapshot["packets"][0]["eligible"], "abstain"}
        self.assertEqual(set(factory.calls[0]["questions"]["packet_0"]["criteria"]), expected)
        self.assertEqual(set(result["rankings"][0]["ranking"]), set(self.snapshot["packets"][0]["eligible"]))
        self.assertEqual(set(result["rankings"][0]["probabilities"]), expected)
        self.assertEqual(result["metadata"]["probability_semantics"], "provider_choice_distribution")
        self.assertEqual(factory.closed, 1)

    async def test_abstain_preserves_distribution_without_manufacturing_ranking(self):
        factory = FakeFactory(provider_response(self.snapshot, abstain=True))
        with patch.dict(os.environ, {"TYPESAFE_API_KEY": "test-only"}, clear=True):
            result = await JevAdapter(self.config, client_factory=factory).recommend(self.snapshot)
        ranking = result["rankings"][0]
        self.assertTrue(ranking["abstained"])
        self.assertEqual(ranking["ranking"], [])
        self.assertEqual(ranking["reason_codes"], ["provider.abstained"])

    async def test_all_sixty_four_options_are_sent_and_ranked(self):
        snapshot = routing_snapshot(candidate_count=64)
        factory = FakeFactory(provider_response(snapshot))
        with patch.dict(os.environ, {"TYPESAFE_API_KEY": "test-only"}, clear=True):
            result = await JevAdapter(self.config, client_factory=factory).recommend(snapshot)
        criteria = factory.calls[0]["questions"]["packet_0"]["criteria"]
        self.assertEqual(len(criteria), 65)
        self.assertEqual(len(result["rankings"][0]["ranking"]), 64)

    async def test_semantic_budget_does_not_count_choice_transport_twice(self):
        snapshot = routing_snapshot(candidate_count=64)
        remaining = 24000 - len(encoded(semantic_projection(snapshot)))
        snapshot["evidence"]["guidance"]["note"] = "Public fixture context. " * (remaining // 24)
        snapshot["evidence_hash"] = digest(snapshot["evidence"])
        snapshot["snapshot_id"] = snapshot_identity({k: v for k, v in snapshot.items() if k != "snapshot_id"})
        self.assertLess(len(encoded(semantic_projection(snapshot))), 24576)
        factory = FakeFactory(provider_response(snapshot))
        with patch.dict(os.environ, {"TYPESAFE_API_KEY": "test-only"}, clear=True):
            await JevAdapter(self.config, client_factory=factory).recommend(snapshot)
        self.assertEqual(len(factory.calls), 1)
        self.assertGreater(len(encoded(factory.calls[0])), 24576)
        self.assertEqual(len(factory.calls[0]["questions"]["packet_0"]["criteria"]), 65)

    async def test_malformed_probability_and_wrong_model_are_safe_failures(self):
        for response, code in (
            (provider_response(self.snapshot, malformed="missing"), "jev_invalid_choice_response"),
            (provider_response(self.snapshot, malformed="sum"), "jev_invalid_probability"),
            (provider_response(self.snapshot, model="jev-1.14.0"), "jev_model_mismatch"),
        ):
            with self.subTest(code=code), patch.dict(os.environ, {"TYPESAFE_API_KEY": "test-only"}, clear=True):
                with self.assertRaisesRegex(AdapterError, code):
                    await JevAdapter(self.config, client_factory=FakeFactory(response)).recommend(self.snapshot)

    async def test_401_429_and_529_are_bounded_and_never_retried(self):
        for status, code in ((401, "jev_authentication_failed"), (429, "jev_rate_limited"), (529, "jev_overloaded")):
            now = [1000.0]
            factory = FakeFactory(error=ProviderFailure(status, {"retry-after": "120"}))
            adapter = JevAdapter(self.config, clock=lambda: now[0], client_factory=factory)
            with self.subTest(status=status), patch.dict(os.environ, {"TYPESAFE_API_KEY": "test-only"}, clear=True):
                with self.assertRaisesRegex(AdapterError, code):
                    await adapter.recommend(self.snapshot)
                self.assertEqual(len(factory.calls), 1)
                if status in {429, 529}:
                    with self.assertRaises(RetryAfter) as caught:
                        await adapter.recommend(self.snapshot)
                    self.assertEqual(caught.exception.retry_at, 1120.0)
                    self.assertEqual(len(factory.calls), 1)

    async def test_deadline_closes_client_and_cancellation_propagates(self):
        factory = FakeFactory(wait=True)
        adapter = JevAdapter({**self.config, "timeout_seconds": 0.1}, client_factory=factory)
        with patch.dict(os.environ, {"TYPESAFE_API_KEY": "test-only"}, clear=True):
            with self.assertRaisesRegex(AdapterError, "jev_timeout"):
                await adapter.recommend(self.snapshot)
        self.assertEqual(factory.closed, 1)

        factory = FakeFactory(wait=True)
        adapter = JevAdapter(self.config, client_factory=factory)
        with patch.dict(os.environ, {"TYPESAFE_API_KEY": "test-only"}, clear=True):
            task = asyncio.create_task(adapter.recommend(self.snapshot))
            while not factory.calls:
                await asyncio.sleep(0)
            task.cancel()
            with self.assertRaises(asyncio.CancelledError):
                await task
        self.assertEqual(factory.closed, 1)

    async def test_optional_sdk_import_failure_is_a_safe_code(self):
        original_import = builtins.__import__

        def refused(name, *args, **kwargs):
            if name == "typesafe_sdk":
                raise ImportError("not installed")
            return original_import(name, *args, **kwargs)

        with (
            patch.dict(os.environ, {"TYPESAFE_API_KEY": "test-only"}, clear=True),
            patch("builtins.__import__", refused),
        ):
            with self.assertRaisesRegex(AdapterError, "jev_sdk_unavailable"):
                await JevAdapter(self.config).recommend(self.snapshot)

    def test_config_requires_fixed_endpoint_env_and_versioned_model(self):
        for config in (
            {"endpoint": "https://example.invalid"},
            {"api_key_env": "OTHER_KEY"},
            {"model": "jev-latest"},
            {"timeout_seconds": 5.1},
            {"unknown": True},
        ):
            with self.subTest(config=config), self.assertRaises(EvidenceError):
                JevAdapter(config)


@unittest.skipUnless(importlib.util.find_spec("typesafe_sdk"), "optional typesafe-sdk is not installed")
class JevSdkWireTests(unittest.IsolatedAsyncioTestCase):
    async def test_official_sdk_serializes_one_local_fake_http_request(self):
        import httpx2
        from typesafe_sdk import AsyncTypeSafeClient, RetryPolicy

        snapshot = routing_snapshot()
        observed = []

        def handler(request):
            body = json.loads(request.content)
            observed.append((request, body))
            answers = {}
            for name, question in body["questions"].items():
                labels = list(question["criteria"])
                probabilities = {label: 0.0 for label in labels}
                probabilities[labels[0]] = 1.0
                answers[name] = {"type": "choice", "choice": labels[0],
                                 "probabilities": probabilities, "confidence": 1.0}
            return httpx2.Response(200, json={"model": "jev-1.13.0", "answers": answers,
                                               "usage": {"input_tokens": 1, "output_tokens": 1}})

        def factory(**options):
            return AsyncTypeSafeClient(
                api_key=options["api_key"],
                model=options["model"],
                retry=RetryPolicy(max_retries=0),
                timeout=options["timeout"],
                base_url=options["base_url"],
                transport=httpx2.MockTransport(handler),
            )

        with patch.dict(os.environ, {"TYPESAFE_API_KEY": "test-only"}, clear=True):
            result = await JevAdapter(
                {"enabled": True, "external_data_consent": True}, client_factory=factory
            ).recommend(snapshot)
        self.assertEqual(len(observed), 1)
        request, body = observed[0]
        self.assertEqual(str(request.url), "https://api.typesafe.ai/v1/systemone")
        self.assertEqual(body["model"], "jev-1.13.0")
        self.assertEqual(set(body["questions"]), {"packet_0"})
        self.assertEqual(result["resolved_model"], "jev-1.13.0")

    async def test_official_sdk_http_errors_and_malformed_json_are_one_attempt(self):
        import httpx2
        from typesafe_sdk import AsyncTypeSafeClient, RetryPolicy

        snapshot = routing_snapshot()

        for status, code in (
            (401, "jev_authentication_failed"),
            (429, "jev_rate_limited"),
            (529, "jev_overloaded"),
            (200, "jev_provider_error"),
        ):
            attempts = []

            def handler(request):
                attempts.append(request)
                if status == 200:
                    return httpx2.Response(200, content=b"{", headers={"content-type": "application/json"})
                return httpx2.Response(status, json={"message": "test failure"}, headers={"retry-after": "1"})

            def factory(**options):
                return AsyncTypeSafeClient(
                    api_key=options["api_key"],
                    model=options["model"],
                    retry=RetryPolicy(max_retries=0),
                    timeout=options["timeout"],
                    base_url=options["base_url"],
                    transport=httpx2.MockTransport(handler),
                )

            with (
                self.subTest(status=status),
                patch.dict(os.environ, {"TYPESAFE_API_KEY": "test-only"}, clear=True),
                self.assertRaisesRegex(AdapterError, code),
            ):
                await JevAdapter(
                    {"enabled": True, "external_data_consent": True}, client_factory=factory
                ).recommend(snapshot)
            self.assertEqual(len(attempts), 1)


if __name__ == "__main__":
    unittest.main()
