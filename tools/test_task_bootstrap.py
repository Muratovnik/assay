"""First-use provisioning, cache reuse and failure isolation without remote calls."""
import asyncio
import copy
import hashlib
import io
import json
from pathlib import Path
import sys
import tarfile
import tempfile
import threading
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills/route-subagents/scripts"))
from route_evidence.task_bootstrap import CorpusProvisioner, provision, setup
from route_evidence.task_evidence import TaskEvidence
from route_evidence.cache import source_lock
from route_evidence.core import EvidenceError
from test_task_evidence import corpus, PACKET, CANDIDATES


def release_fixture():
    raw = json.dumps({"records": [{"index": i, "origin_query": "Fix case " + str(i),
        "score": i % 2, "cost": 0.2, "prompt_tokens": 10, "completion_tokens": 20} for i in range(4)]}).encode()
    name = "bench-release/livecodebench/test/historical/results.json"
    data = io.BytesIO()
    with tarfile.open(fileobj=data, mode="w:gz") as archive:
        member = tarfile.TarInfo(name)
        member.size = len(raw)
        archive.addfile(member, io.BytesIO(raw))
    definition = {"url": "https://example.org/pinned.tar.gz", "members": {
        name: {"sha256": hashlib.sha256(raw).hexdigest(), "rows": 4}}, "tasks": 4, "installed_tasks": 2,
        "manifest": {"source": corpus()["source"], "datasets": {"livecodebench": {
            "task_types": ["implementation"], "metric": "pass-at-1", "harness": "fixture",
            "efforts": {}, "priced_models": ["historical"]}}}}
    response = io.BytesIO(data.getvalue())
    response.geturl = lambda: definition["url"]
    return definition, response


class BootstrapTests(unittest.TestCase):
    def test_verified_release_install_reuse_and_holdout(self):
        definition, response = release_fixture()
        with tempfile.TemporaryDirectory() as temp:
            evidence = TaskEvidence(temp, {"enabled": True})
            with patch("urllib.request.urlopen", return_value=response) as network:
                self.assertEqual(provision(evidence, definition)["status"], "ready")
                installed = evidence.load()
                self.assertEqual(len(installed["corpus"]["records"]), 2)
                self.assertEqual(installed["corpus"]["records"][0]["observations"][0]["costs"]["api_usd"], 0.2)
                self.assertEqual(provision(evidence, definition)["status"], "ready")
                self.assertEqual(evidence.load(), installed)
                network.assert_called_once()
            self.assertEqual(list(evidence.root.glob("download-*")), [])

    def test_bad_checksum_and_missing_release_do_not_install(self):
        for corrupt in (True, False):
            definition, response = release_fixture()
            if corrupt:
                next(iter(definition["members"].values()))["sha256"] = "0" * 64
            else:
                definition["members"]["missing.json"] = {"sha256": "0" * 64, "rows": 4}
            with self.subTest(corrupt=corrupt), tempfile.TemporaryDirectory() as temp:
                evidence = TaskEvidence(temp, {"enabled": True})
                with patch("urllib.request.urlopen", return_value=response):
                    self.assertEqual(provision(evidence, definition)["status"], "failed")
                self.assertIsNone(evidence.load())
                with patch("urllib.request.urlopen") as network:
                    self.assertEqual(CorpusProvisioner(evidence).ensure()["status"], "failed")
                    network.assert_not_called()
                self.assertEqual(list(evidence.root.glob("download-*")), [])

    def test_disabled_offline_and_opt_out_never_launch_download(self):
        for config, offline, expected in (({}, False, "disabled"), ({"enabled": True}, True, "missing_offline"),
            ({"enabled": True, "auto_download": False}, False, "missing")):
            with self.subTest(expected=expected), tempfile.TemporaryDirectory() as temp:
                provider = CorpusProvisioner(TaskEvidence(temp, config), offline=offline)
                with patch("route_evidence.task_bootstrap.ProcessScope") as process:
                    self.assertEqual(provider.ensure()["status"], expected)
                    process.assert_not_called()

    def test_missing_transitions_to_present_without_blocking_or_duplicate_worker(self):
        started, release = threading.Event(), threading.Event()
        with tempfile.TemporaryDirectory() as temp:
            evidence = TaskEvidence(temp, {"enabled": True})
            provider = CorpusProvisioner(evidence)
            def download(*args, **kwargs):
                started.set()
                release.wait(5)
                evidence.install(corpus())
            with patch("route_evidence.task_bootstrap.setup", side_effect=download) as worker:
                try:
                    self.assertEqual(provider.ensure()["status"], "downloading")
                    self.assertTrue(started.wait(2))
                    self.assertEqual(provider.ensure()["status"], "downloading")
                    worker.assert_called_once()
                    release.set()
                    provider.thread.join(5)
                    self.assertEqual(provider.ensure()["status"], "present")
                    worker.assert_called_once()
                finally:
                    release.set()
                    provider.close()

    def test_cross_client_lock_and_manual_corpus_are_preserved(self):
        with tempfile.TemporaryDirectory() as temp:
            evidence = TaskEvidence(temp, {"enabled": True})
            evidence.root.mkdir()
            with source_lock(evidence.root / "acquisition.lock"), patch("urllib.request.urlopen") as network:
                self.assertEqual(provision(evidence)["status"], "downloading")
                network.assert_not_called()
            evidence.install(corpus())
            before = (evidence.root / "corpus.json").read_bytes()
            other = copy.deepcopy(corpus())
            other["source"]["revision"] = "replacement"
            evidence.install(other, replace=False)
            self.assertEqual((evidence.root / "corpus.json").read_bytes(), before)
            with patch("urllib.request.urlopen") as network:
                self.assertEqual(setup(evidence, offline=True)["status"], "ready")
                network.assert_not_called()

    def test_routing_exposes_missing_source_without_losing_local_contract(self):
        with tempfile.TemporaryDirectory() as temp:
            evidence = TaskEvidence(temp, {"enabled": True})
            evidence.provisioner = CorpusProvisioner(evidence, offline=True)
            result = asyncio.run(evidence.async_summarize([PACKET], CANDIDATES, {"fix": "repair cache"}))
            self.assertEqual(result["acquisition"]["status"], "missing_offline")
            self.assertNotIn("repair cache", json.dumps(result))

    def test_interrupted_worker_cleans_partial_download_and_retries_explicitly(self):
        with tempfile.TemporaryDirectory() as temp:
            evidence = TaskEvidence(temp, {"enabled": True})
            def interrupted(argv, payload):
                request = json.loads(payload)
                (Path(request["directory"]) / "partial.json").write_text("partial")
                raise EvidenceError("refresh_deadline_exceeded")
            with patch("route_evidence.task_bootstrap.ProcessScope.run", side_effect=interrupted):
                self.assertEqual(setup(evidence)["status"], "failed")
            self.assertIsNone(evidence.load())
            self.assertEqual(list(evidence.root.glob("download-*")), [])
            definition, response = release_fixture()
            def complete(argv, payload):
                request = json.loads(payload)
                return json.dumps(provision(evidence, definition, Path(request["directory"]))).encode()
            with patch("urllib.request.urlopen", return_value=response), patch(
                    "route_evidence.task_bootstrap.ProcessScope.run", side_effect=complete):
                self.assertEqual(setup(evidence)["status"], "ready")
            self.assertIsNotNone(evidence.load())

    def test_fixed_route_skips_setup_even_in_waiting_cli_mode(self):
        with tempfile.TemporaryDirectory() as temp:
            evidence = TaskEvidence(temp, {"enabled": True})
            evidence.provisioner = CorpusProvisioner(evidence)
            evidence.provisioner.wait = True
            with patch("route_evidence.task_bootstrap.setup") as worker:
                result = asyncio.run(evidence.async_summarize([PACKET], CANDIDATES[:1]))
                self.assertEqual(result["packets"][0]["status"], "skipped_fixed_route")
                worker.assert_not_called()


if __name__ == "__main__":
    unittest.main()
