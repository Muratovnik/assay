"""Routing configuration schema 5 and the plugin's routing binding.

A configuration or binding written for the removed advisor, required mode or
execution telemetry is refused with one message that says what to change; the
launch check never silently stops applying.
"""
from __future__ import annotations

import io
import json
import os
from contextlib import redirect_stdout
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'hooks'))
sys.path.insert(0, str(ROOT / 'skills/route-subagents/scripts'))
from runtime import cli
from route_evidence.core import EvidenceError, RetiredConfiguration
from route_evidence.pipeline_config import settings
from route_evidence.service import load_config

TABLE = {'classes': {
    'gather': {'model': 'haiku', 'effort': 'medium', 'when': 'search and read'},
    'code': {'model': 'sonnet', 'effort': 'high', 'when': 'ordinary implementation'},
}}
RENAMED = 'routing-telemetry.json was renamed to routing.json'


class Fixture(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(); self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.data = self.root / 'plugin-data'; self.data.mkdir()
        self.cache = self.root / 'cache'
        home = patch.object(Path, 'home', return_value=self.root / 'home'); home.start(); self.addCleanup(home.stop)

    def config(self, document=None, name='claude.json'):
        path = self.root / name
        path.write_text(json.dumps({'schema_version': 5, 'client': 'claude', 'routes': TABLE}
                                   if document is None else document), encoding='utf-8')
        return path

    def bind(self, config, name='routing.json'):
        (self.data / name).write_text(json.dumps({'config': str(config), 'cache_dir': str(self.cache)}),
                                      encoding='utf-8')
        return {'PLUGIN_DATA': str(self.data)}

    def launch(self, tool='t1', **supplied):
        return {'hook_event_name': 'PreToolUse', 'tool_name': 'Agent', 'session_id': 's', 'tool_use_id': tool,
                'cwd': str(self.root), 'tool_input': {'prompt': 'Do the bounded task', **supplied}}

    def decide(self, event, environment):
        result, error = cli.process(event, 'claude', environment)
        output = result.get('hookSpecificOutput', {})
        denied = output.get('permissionDecision') == 'deny'
        return ('deny' if denied else 'allow'), output.get('permissionDecisionReason' if denied else 'additionalContext'), error


class SchemaTests(Fixture):
    def test_removed_sections_and_keys_are_named_in_one_refusal(self):
        document = {'schema_version': 4, 'client': 'claude', 'routes': TABLE,
                    'advisor': {'enabled': False}, 'policy': {}, 'telemetry': {'mode': 'full'},
                    'task_evidence': {'retain_descriptions': True},
                    'pipeline': {'mode': 'required', 'state_dir': None, 'profiles': [], 'host': None}}
        with self.assertRaises(RetiredConfiguration) as caught:
            load_config(self.config(document))
        message = str(caught.exception)
        for name in ('advisor', 'policy', 'telemetry', 'task_evidence', 'pipeline.mode=required',
                     'pipeline.state_dir', 'pipeline.profiles', 'set schema_version to 5'):
            self.assertIn(name, message)
        # A kept key is not named as one to remove.
        self.assertNotIn('pipeline.host', message)

    def test_an_older_schema_without_removed_keys_is_told_the_version_to_set(self):
        for version in (1, 2, 3, 4):
            with self.subTest(version=version), self.assertRaises(RetiredConfiguration) as caught:
                load_config(self.config({'schema_version': version, 'client': 'claude'}))
            self.assertIn('set schema_version to 5', str(caught.exception))
            self.assertNotIn('remove', str(caught.exception))
        for version in (6, '5', None):
            with self.subTest(version=version), self.assertRaisesRegex(EvidenceError, 'schema_version=5') as caught:
                load_config(self.config({'schema_version': version, 'client': 'claude'}))
            self.assertNotIsInstance(caught.exception, RetiredConfiguration)

    def test_schema_5_keeps_the_launch_check_keys(self):
        loaded = load_config(self.config({
            'schema_version': 5, 'client': 'claude', 'routes': TABLE, 'preferences': {},
            'pipeline': {'mode': 'evidence-only', 'explicit_routes': 'require', 'unrouted_agents': ['Explore'],
                         'host': {'version': '2.1.300', 'surface': 'cli'}, 'inventory_ttl_hours': 24,
                         'inventory_file': None}}))
        self.assertEqual(loaded['pipeline']['unrouted_agents'], {'Explore': 'baseline'})
        self.assertEqual(set(loaded['routes']['classes']), {'gather', 'code'})
        with self.assertRaisesRegex(EvidenceError, 'unknown_pipeline_configuration'):
            load_config(self.config({'schema_version': 5, 'client': 'claude', 'pipeline': {'novel': 1}}))

    def test_exempt_agent_configuration_is_validated_and_normalized(self):
        for value, code in ((['Explore', 'Explore'], 'unrouted_agents'), ([{'name': 'Explore'}], 'unrouted_agents'),
                            (['assay-general-purpose-low-x'], 'unrouted_agents'),
                            ({'Explore': 'sometimes'}, 'unrouted_agent_model'),
                            ({'Explore': {'model': ''}}, 'unrouted_agent_model'),
                            ({'Explore': {'model': 'haiku', 'effort': 'low'}}, 'unrouted_agent_model')):
            with self.subTest(value=value), self.assertRaisesRegex(EvidenceError, code):
                settings({'pipeline': {'unrouted_agents': value}})
        listed = settings({'pipeline': {'unrouted_agents': ['Explore']}})
        self.assertEqual(listed['unrouted_agents'], {'Explore': 'baseline'})
        # Normalization is stable, so the hook and the server read the same policy.
        self.assertEqual(settings({'pipeline': listed}), listed)

    def test_the_launch_check_and_the_cli_pass_the_refusal_on(self):
        retired = self.config({'schema_version': 4, 'client': 'claude', 'routes': TABLE, 'telemetry': {'mode': 'off'}})
        decision, reason, _ = self.decide(self.launch(description='code: x', model='sonnet', effort='high'),
                                          self.bind(retired))
        self.assertEqual(decision, 'deny')
        self.assertIn('remove telemetry and set schema_version to 5', reason)
        self.assertNotIn(str(self.root), reason)
        import benchmark_router
        output = io.StringIO()
        with redirect_stdout(output):
            code = benchmark_router.main(['--cache-dir', str(self.cache), '--config', str(retired), 'status'])
        self.assertEqual(code, 2)
        self.assertIn('remove telemetry', json.loads(output.getvalue())['error'])


class BindingTests(Fixture):
    def test_the_binding_applies_the_route_table(self):
        environment = self.bind(self.config())
        decision, context, error = self.decide(self.launch(description='gather: survey', model='haiku',
                                                           effort='medium'), environment)
        self.assertEqual((decision, error), ('allow', None))
        self.assertIn('admitted as class `gather`', context)
        decision, reason, _ = self.decide(self.launch(description='survey', model='haiku', effort='medium'),
                                          environment)
        self.assertEqual(decision, 'deny')
        self.assertIn('task class', reason)

    def test_a_binding_under_its_old_name_refuses_launches(self):
        environment = self.bind(self.config(), name='routing-telemetry.json')
        for supplied in ({'description': 'gather: survey', 'model': 'haiku', 'effort': 'medium'},
                         {'description': 'survey'}):
            with self.subTest(supplied=supplied):
                decision, reason, _ = self.decide(self.launch(**supplied), environment)
                self.assertEqual(decision, 'deny')
                self.assertIn(RENAMED, reason)
        # Other tools are not launches; the hook keeps answering them.
        result, error = cli.process({**self.launch(), 'tool_name': 'Read'}, 'claude', environment)
        self.assertNotEqual('deny', result.get('hookSpecificOutput', {}).get('permissionDecision'))
        # Once renamed, the leftover file no longer matters.
        self.bind(self.config())
        self.assertEqual('allow', self.decide(self.launch(description='gather', model='haiku', effort='medium'),
                                              environment)[0])

    def test_the_removed_binding_variable_is_refused(self):
        binding = self.root / 'binding.json'
        binding.write_text(json.dumps({'config': str(self.config()), 'cache_dir': str(self.cache)}), encoding='utf-8')
        decision, reason, _ = self.decide(self.launch(description='gather', model='haiku', effort='medium'),
                                          {'ASSAY_ROUTING_TELEMETRY_CONFIG': str(binding)})
        self.assertEqual(decision, 'deny')
        self.assertIn('ASSAY_ROUTING_TELEMETRY_CONFIG was removed', reason)

    def test_an_explicit_configuration_does_not_need_the_binding(self):
        environment = {'ASSAY_ROUTING_CONFIG': str(self.config())}
        self.assertEqual('allow', self.decide(self.launch(description='code: x', model='sonnet', effort='high'),
                                              environment)[0])
        self.assertEqual('deny', self.decide(self.launch(description='x', model='sonnet', effort='high'),
                                             environment)[0])

    def test_host_observations_go_to_the_binding_cache_without_any_telemetry_setting(self):
        from route_evidence import host_observations
        environment = self.bind(self.config())
        launch = self.launch(description='gather: survey', model='haiku', effort='medium')
        for event in (launch, {**launch, 'hook_event_name': 'PostToolUse',
                               'tool_response': {'agentId': 'a1', 'resolvedModel': 'claude-haiku-5-5'}}):
            result, error = cli.process(event, 'claude', environment)
            self.assertIsNone(error)
        self.assertEqual([('haiku', 'claude-haiku-5-5')],
                         [(row['alias'], row['model']) for row in host_observations.summary(self.cache)['aliases']])

    def test_a_refused_launch_leaves_no_observation(self):
        environment = self.bind(self.config())
        cli.process(self.launch(description='survey', model='opus', effort='max'), 'claude', environment)
        self.assertFalse((self.cache / 'host-observations').exists())

    def test_codex_events_record_no_host_observation(self):
        environment = self.bind(self.config({'schema_version': 5, 'client': 'codex'}))
        cli.process({**self.launch(model='x', effort='low'), 'tool_name': 'spawn_agent'}, 'codex', environment)
        self.assertFalse((self.cache / 'host-observations').exists())

    def test_binding_paths_must_be_absolute_and_complete(self):
        for document in ({'config': 'relative.json', 'cache_dir': str(self.cache)},
                         {'config': str(self.config())},
                         {'config': str(self.config()), 'cache_dir': str(self.cache), 'extra': 1}):
            with self.subTest(document=document):
                (self.data / 'routing.json').write_text(json.dumps(document), encoding='utf-8')
                decision, reason, _ = self.decide(self.launch(description='gather', model='haiku', effort='medium'),
                                                  {'PLUGIN_DATA': str(self.data)})
                self.assertEqual(decision, 'deny')
                self.assertIn('could not be validated', reason)

    @unittest.skipUnless(os.name == 'nt', 'directory junctions are a Windows reparse point')
    def test_a_junction_ancestor_of_the_cache_is_rejected(self):
        target, link = self.root / 'junction-target', self.root / 'junction'
        target.mkdir()
        created = subprocess.run(['cmd', '/c', 'mklink', '/J', str(link), str(target)], capture_output=True, timeout=30)
        if created.returncode != 0:
            self.skipTest('junction creation unavailable')
        self.addCleanup(os.rmdir, link)  # removes only the link, never its target
        (self.data / 'routing.json').write_text(json.dumps({'config': str(self.config()),
                                                            'cache_dir': str(link / 'cache')}), encoding='utf-8')
        from runtime import routing_binding
        with self.assertRaisesRegex(EvidenceError, 'linked'):
            routing_binding.configuration({'PLUGIN_DATA': str(self.data)})
        self.assertEqual(list(target.iterdir()), [])


class DoctorTests(Fixture):
    def test_doctor_reports_whether_a_binding_was_found(self):
        report = cli.doctor('claude', {})
        self.assertFalse(report['routing_binding_found'])
        self.assertFalse(report['routing_config_found'])
        self.assertNotIn('routing_telemetry_bound', report)
        environment = self.bind(self.config({'schema_version': 5, 'client': 'claude', 'routes': TABLE,
                                             'pipeline': {'host': {'version': '2.1.300', 'surface': 'cli'}}}))
        report = cli.doctor('claude', environment)
        self.assertTrue(report['routing_binding_found'])
        self.assertTrue(report['routing_config_found'])
        # Capabilities follow the bound configuration's declared host.
        self.assertEqual(report['capabilities']['declared_host']['version'], '2.1.300')

    def test_doctor_refuses_a_binding_under_its_old_name(self):
        environment = self.bind(self.config(), name='routing-telemetry.json')
        with self.assertRaisesRegex(RetiredConfiguration, RENAMED):
            cli.doctor('claude', environment)
        command = [sys.executable, '-I', '-B', str(ROOT / 'hooks/runtime/cli.py'), 'doctor', '--client', 'claude']
        env = {k: v for k, v in os.environ.items() if not k.startswith('ASSAY_') and k not in {'CLAUDE_PLUGIN_DATA'}}
        result = subprocess.run(command, capture_output=True, text=True, timeout=30, env={**env, **environment})
        self.assertEqual(result.returncode, 2)
        self.assertIn(RENAMED, result.stderr)


if __name__ == '__main__':
    unittest.main()
