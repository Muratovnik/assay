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
import skill_reminder

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

    def spawn(self, tool='t1', **supplied):
        return {'hook_event_name': 'PreToolUse', 'tool_name': 'spawn_agent', 'session_id': 's', 'tool_use_id': tool,
                'cwd': str(self.root), 'tool_input': {'message': 'Do the bounded task', **supplied}}

    def decide(self, event, environment, client='claude'):
        result, error = cli.process(event, client, environment)
        output = result.get('hookSpecificOutput', {})
        denied = output.get('permissionDecision') == 'deny'
        return ('deny' if denied else 'allow'), output.get('permissionDecisionReason' if denied else 'additionalContext'), error


class SessionChecklistTests(Fixture):
    """The routing checklist appears at session start whenever the launch check would find a configuration."""
    CHECKLIST = 'Before every authorized subagent launch'

    def start(self, environment, source='startup'):
        result, error = cli.process({'hook_event_name': 'SessionStart', 'source': source, 'session_id': 's'},
                                    'claude', environment)
        self.assertIsNone(error)
        return result['hookSpecificOutput']['additionalContext']

    def test_the_resolved_fact_overrides_the_variable_in_the_reminder(self):
        event = {'hook_event_name': 'SessionStart', 'source': 'startup'}

        def context(**resolved):
            return skill_reminder.reminder(event, {'ASSAY_ROUTING_CONFIG': 'x.json'}, **resolved)[
                'hookSpecificOutput']['additionalContext']
        self.assertIn(self.CHECKLIST, context())
        self.assertIn(self.CHECKLIST, context(routing=True))
        self.assertNotIn(self.CHECKLIST, context(routing=False))
        self.assertIn('blocked until it is fixed: why not.', context(routing=True, problem='why not'))
        # A problem without routing is not shown: there is no checklist for it to follow.
        self.assertNotIn('blocked', context(routing=False, problem='why not'))

    def test_a_binding_alone_shows_the_checklist(self):
        text = self.start(self.bind(self.config()))
        self.assertTrue(text.startswith('Assay is installed.'))
        self.assertIn(self.CHECKLIST, text)
        # The owner names the classes, so the reminder shows the form, not one table's class.
        self.assertIn('`<class>: <task>`', text)
        self.assertIn('routing_status', text)
        self.assertIn('references/routing-failure.md', text)
        self.assertNotIn('routing configuration is refused', text)

    def test_the_variable_alone_shows_the_checklist(self):
        text = self.start({'ASSAY_ROUTING_CONFIG': str(self.config())})
        self.assertIn(self.CHECKLIST, text)
        self.assertNotIn('routing configuration is refused', text)

    def test_without_a_variable_or_binding_there_is_no_checklist(self):
        for environment in ({}, {'PLUGIN_DATA': str(self.data)}):
            with self.subTest(environment=sorted(environment)):
                text = self.start(environment)
                self.assertIn('Assay is installed.', text)
                self.assertNotIn(self.CHECKLIST, text)

    def test_every_session_start_source_shows_it(self):
        environment = self.bind(self.config())
        for source in ('startup', 'resume', 'clear', 'compact', 'fork'):
            with self.subTest(source=source):
                self.assertIn(self.CHECKLIST, self.start(environment, source))

    def test_only_a_route_table_for_this_client_shows_the_checklist(self):
        tableless = self.config({'schema_version': 5, 'client': 'claude'}, name='tableless.json')
        other = self.config({'schema_version': 5, 'client': 'codex', 'routes': TABLE}, name='other.json')
        matching = self.config(name='matching.json')
        for config, shown in ((tableless, False), (other, False), (matching, True)):
            for label, environment in (('binding', self.bind(config)),
                                       ('variable', {'ASSAY_ROUTING_CONFIG': str(config)})):
                with self.subTest(config=config.name, via=label):
                    text = self.start(environment)
                    self.assertEqual(shown, self.CHECKLIST in text)
                    self.assertIn('Assay is installed.', text)
                    self.assertNotIn('routing configuration is refused', text)

    def test_the_variable_wins_over_the_binding_as_in_the_launch_check(self):
        retired = self.config({'schema_version': 4, 'client': 'claude'}, name='retired.json')
        environment = {**self.bind(retired), 'ASSAY_ROUTING_CONFIG': str(self.config())}
        self.assertNotIn('routing configuration is refused', self.start(environment))

    def test_a_retired_configuration_keeps_the_checklist_and_says_why_launches_are_blocked(self):
        retired = self.config({'schema_version': 4, 'client': 'claude', 'routes': TABLE,
                               'telemetry': {'mode': 'off'}})
        for label, environment in (('binding', self.bind(retired)), ('variable', {'ASSAY_ROUTING_CONFIG': str(retired)})):
            with self.subTest(via=label):
                text = self.start(environment)
                self.assertIn(self.CHECKLIST, text)
                self.assertIn('routing configuration is refused', text)
                self.assertIn('remove telemetry and set schema_version to 5.', text)
                self.assertNotIn(str(self.root), text)

    def test_a_retired_binding_name_keeps_the_checklist_and_names_the_rename(self):
        (self.data / 'routing-telemetry.json').write_text('{}', encoding='utf-8')
        text = self.start({'PLUGIN_DATA': str(self.data)})
        self.assertIn(self.CHECKLIST, text)
        self.assertIn(RENAMED, text)

    def test_an_unreadable_configuration_keeps_the_checklist_without_leaking_its_error(self):
        broken = self.root / 'broken.json'
        broken.write_text('{not json', encoding='utf-8')
        missing = self.root / 'missing.json'
        for config in (broken, missing):
            for label, environment in (('binding', self.bind(config)), ('variable', {'ASSAY_ROUTING_CONFIG': str(config)})):
                with self.subTest(config=config.name, via=label):
                    text = self.start(environment)
                    self.assertIn(self.CHECKLIST, text)
                    self.assertIn('every launch it covers is blocked until it is fixed: it could not be validated', text)
                    self.assertNotIn(str(self.root), text)

    def test_an_object_form_of_exempt_agents_is_named_at_session_start(self):
        config = self.config({'schema_version': 5, 'client': 'claude', 'routes': TABLE,
                              'pipeline': {'unrouted_agents': {}}})
        text = self.start(self.bind(config))
        self.assertIn(self.CHECKLIST, text)
        self.assertIn('Replace it with the list of its agent types', text)


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
        self.assertEqual(loaded['pipeline']['unrouted_agents'], ['Explore'])
        self.assertEqual(set(loaded['routes']['classes']), {'gather', 'code'})
        with self.assertRaisesRegex(EvidenceError, 'unknown_pipeline_configuration'):
            load_config(self.config({'schema_version': 5, 'client': 'claude', 'pipeline': {'novel': 1}}))

    def test_exempt_agents_are_a_list_of_valid_unique_type_names(self):
        for value in (['Explore', 'Explore'], [{'name': 'Explore'}], ['assay-general-purpose-low-x'], ['bad name'],
                      [''], 'Explore', None, ['t%d' % n for n in range(65)]):
            with self.subTest(value=value), self.assertRaisesRegex(EvidenceError, 'invalid_pipeline_unrouted_agents'):
                settings({'pipeline': {'unrouted_agents': value}})
        listed = settings({'pipeline': {'unrouted_agents': ['Explore', 'plugin:reviewer']}})
        self.assertEqual(listed['unrouted_agents'], ['Explore', 'plugin:reviewer'])
        self.assertEqual(settings({'pipeline': {'unrouted_agents': ['t%d' % n for n in range(64)]}})
                         ['unrouted_agents'][-1], 't63')
        self.assertEqual(settings({})['unrouted_agents'], [])
        # Normalization is stable, so the hook and the server read the same policy.
        self.assertEqual(settings({'pipeline': listed}), listed)

    def test_the_object_form_of_exempt_agents_is_refused_as_removed_in_schema_5(self):
        for value in ({}, {'Explore': 'inherit'}, {'Explore': 'baseline'}, {'Explore': {'model': 'haiku'}}):
            with self.subTest(value=value), self.assertRaises(RetiredConfiguration) as caught:
                settings({'pipeline': {'unrouted_agents': value}})
            message = str(caught.exception)
            self.assertIn('object form', message)
            self.assertIn('removed', message)
            self.assertIn('schema 5', message)
            self.assertIn('Replace it with the list of its agent types', message)
            self.assertIn('{} with []', message)
        # Loading a schema 5 file reaches the same refusal, and nothing is partly accepted.
        for value in ({}, {'Explore': 'inherit'}):
            with self.subTest(file=value), self.assertRaises(RetiredConfiguration):
                load_config(self.config({'schema_version': 5, 'client': 'claude', 'routes': TABLE,
                                         'pipeline': {'unrouted_agents': value}}))

    def test_an_object_form_refuses_launches_with_the_message_and_a_list_exempts_its_type(self):
        for value in ({}, {'Explore': 'inherit'}):
            config = self.config({'schema_version': 5, 'client': 'claude', 'routes': TABLE,
                                  'pipeline': {'unrouted_agents': value}})
            for label, environment in (('binding', self.bind(config)),
                                       ('variable', {'ASSAY_ROUTING_CONFIG': str(config)})):
                with self.subTest(value=value, via=label):
                    decision, reason, error = self.decide(
                        self.launch(description='code: x', model='sonnet', effort='high'), environment)
                    self.assertEqual(decision, 'deny')
                    self.assertIn('Replace it with the list of its agent types', reason)
                    self.assertIn('object form', reason)
                    self.assertNotIn('could not be validated', reason)
                    self.assertNotIn(str(self.root), reason)
        listed = self.config({'schema_version': 5, 'client': 'claude', 'routes': TABLE,
                              'pipeline': {'unrouted_agents': ['Explore']}}, name='listed.json')
        environment = self.bind(listed)
        # A listed type keeps its own settings; any other type must still follow the table.
        self.assertEqual(self.decide(self.launch(subagent_type='Explore'), environment)[0], 'allow')
        self.assertEqual(self.decide(self.launch(subagent_type='Plan', description='fix it'), environment)[0], 'deny')

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

    def test_a_codex_binding_under_its_old_name_refuses_launches(self):
        codex = {'schema_version': 5, 'client': 'codex', 'routes': TABLE}
        environment = self.bind(self.config(codex), name='routing-telemetry.json')
        self.assertFalse((self.data / 'routing.json').exists())
        for supplied in ({'task_name': 'gather_survey', 'model': 'haiku', 'reasoning_effort': 'medium',
                          'fork_turns': 'none'},
                         {'task_name': 'survey'}):
            with self.subTest(supplied=supplied):
                decision, reason, _ = self.decide(self.spawn(**supplied), environment, 'codex')
                self.assertEqual(decision, 'deny')
                self.assertIn(RENAMED, reason)
        # Other tools are not launches; the hook keeps answering them.
        result, error = cli.process({**self.spawn(), 'tool_name': 'read_file'}, 'codex', environment)
        self.assertNotEqual('deny', result.get('hookSpecificOutput', {}).get('permissionDecision'))
        # Once renamed, the same launch is checked against the table instead.
        self.bind(self.config(codex))
        good = self.spawn(task_name='gather_survey', model='haiku', reasoning_effort='medium', fork_turns='none')
        self.assertEqual('allow', self.decide(good, environment, 'codex')[0])

    def test_removed_hook_options_do_not_switch_the_route_table_off(self):
        # The hook options are refused and reported, but the launch check is decided first and stays.
        environment = self.bind(self.config())
        admitted = self.launch(description='gather: survey', model='haiku', effort='medium')
        unlabelled = self.launch(description='survey', model='haiku', effort='medium')
        removed = {'record_events': True, 'feedback_capture': 'metadata', 'feedback_trigger': 'explicit'}
        for hook in (removed, *({name: value} for name, value in removed.items())):
            path = self.root / 'hooks.json'
            path.write_text(json.dumps(hook), encoding='utf-8')
            names = sorted(hook)
            with self.subTest(options=names):
                scoped = {**environment, 'ASSAY_HOOK_CONFIG': str(path)}
                decision, reason, error = self.decide(unlabelled, scoped)
                self.assertEqual(decision, 'deny')
                self.assertIn('task class', reason)
                self.assertIn(', '.join(names), error)
                decision, context, error = self.decide(admitted, scoped)
                self.assertEqual(decision, 'allow')
                self.assertIn('admitted as class `gather`', context)
                self.assertIn(', '.join(names), error)

    def test_a_retired_configuration_named_directly_refuses_launches(self):
        retired = {'schema_version': 4, 'client': 'claude', 'routes': TABLE, 'advisor': {'enabled': False}}
        bare = {'schema_version': 4, 'client': 'claude', 'routes': TABLE}
        for document in (retired, bare):
            environment = {'ASSAY_ROUTING_CONFIG': str(self.config(document))}
            with self.subTest(document=sorted(document)):
                # A launch the table would admit is refused as well: the check never silently stops applying.
                decision, reason, _ = self.decide(self.launch(description='code: x', model='sonnet', effort='high'),
                                                  environment)
                self.assertEqual(decision, 'deny')
                self.assertIn('set schema_version to 5', reason)
                self.assertNotIn(str(self.root), reason)
                self.assertEqual('deny', self.decide(self.launch(description='x'), environment)[0])
        self.assertIn('advisor', self.decide(self.launch(), {'ASSAY_ROUTING_CONFIG': str(self.config(retired))})[1])
        codex = {'ASSAY_ROUTING_CONFIG': str(self.config({'schema_version': 4, 'client': 'codex'}))}
        decision, reason, _ = self.decide(self.spawn(task_name='x'), codex, 'codex')
        self.assertEqual(decision, 'deny')
        self.assertIn('set schema_version to 5', reason)
        # The same launch under schema 5 is admitted, so the refusal comes from the retired schema.
        current = {'ASSAY_ROUTING_CONFIG': str(self.config(name='current.json'))}
        self.assertEqual('allow', self.decide(self.launch(description='code: x', model='sonnet', effort='high'),
                                              current)[0])

    def test_without_a_binding_or_configuration_a_launch_passes_and_nothing_is_recorded(self):
        launch = self.launch(description='gather: survey', model='haiku', effort='medium')
        events = (launch, {**launch, 'hook_event_name': 'PostToolUse',
                           'tool_response': {'agentId': 'a1', 'resolvedModel': 'claude-haiku-5-5'}},
                  {**launch, 'hook_event_name': 'SubagentStop', 'agent_id': 'a1'},
                  # No table applies, so even a launch the table would refuse passes.
                  self.launch(tool='t2', description='survey', model='opus', effort='max'))
        empty = self.root / 'empty-data'; empty.mkdir()
        for environment in ({}, {'PLUGIN_DATA': str(empty)}):
            for event in events:
                with self.subTest(environment=sorted(environment), event=event['hook_event_name']):
                    result, error = cli.process(event, 'claude', environment)
                    output = result.get('hookSpecificOutput', {})
                    self.assertIsNone(error)
                    self.assertNotIn('permissionDecision', output)
                    self.assertNotIn('updatedInput', output)
        decision, _, _ = self.decide(self.spawn(task_name='x'), {}, 'codex')
        self.assertEqual(decision, 'allow')
        self.assertFalse(self.cache.exists())
        self.assertEqual([], [path for path in self.root.rglob('*') if 'host-observations' in path.parts])
        # The binding file is what turns recording on, so the same events with one do record.
        self.bind(self.config())
        for event in events[:2]:
            cli.process(event, 'claude', {'PLUGIN_DATA': str(self.data)})
        self.assertTrue((self.cache / 'host-observations').exists())

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
