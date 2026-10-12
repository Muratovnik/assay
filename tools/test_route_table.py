"""Route table contract: the owner's class pairs, enforced on Claude and Codex spawns.

Fixtures describe native spawn payloads; they are not native-client evidence.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'hooks'))
sys.path.insert(0, str(ROOT / 'skills/route-subagents/scripts'))
from runtime import cli
from route_evidence.core import EvidenceError
from route_evidence.service import load_config

CLAUDE_TABLE = {'basis': 'fixture', 'classes': {
    'gather': {'model': 'haiku', 'effort': 'medium', 'when': 'search and read'},
    'code': {'model': 'sonnet', 'effort': 'high', 'when': 'ordinary implementation'},
}}
CODEX_TABLE = {'classes': {
    'gather': {'model': 'gpt-6-luna', 'effort': 'medium', 'when': 'search and read'},
    'code': {'model': 'gpt-6.1-sol', 'effort': 'high', 'when': 'ordinary implementation'},
}}


class RouteTableTests(unittest.TestCase):

    def setUp(self):
        tmp = tempfile.TemporaryDirectory(); self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.project = self.root / 'project'; self.project.mkdir()
        self.home = self.root / 'home'
        home = patch.object(Path, 'home', return_value=self.home); home.start(); self.addCleanup(home.stop)

    def config(self, client='claude', routes=None, pipeline=None, name='config.json'):
        document = {'schema_version': 4, 'client': client, 'telemetry': {'mode': 'off'}}
        if routes is not None:
            document['routes'] = routes
        if pipeline is not None:
            document['pipeline'] = pipeline
        path = self.root / name
        path.write_text(json.dumps(document), encoding='utf-8')
        return path

    def environment(self, client='claude', routes=None, pipeline=None, **extra):
        return {'ASSAY_ROUTING_CONFIG': str(self.config(client, routes, pipeline)), **extra}

    def reason(self, event, environment, client):
        result, error = cli.process(event, client, environment)
        self.assertIsNone(error)
        output = result.get('hookSpecificOutput', {})
        return output.get('permissionDecisionReason') if output.get('permissionDecision') == 'deny' else None

    def claude(self, **supplied):
        return {'hook_event_name': 'PreToolUse', 'tool_name': 'Agent', 'session_id': 's', 'tool_use_id': 't',
                'cwd': str(self.project), 'tool_input': {'prompt': 'Do the bounded task', **supplied}}

    def codex(self, **supplied):
        return {'hook_event_name': 'PreToolUse', 'tool_name': 'spawn_agent', 'session_id': 's',
                'tool_use_id': 't', 'cwd': str(self.project),
                'tool_input': {'message': 'Do the bounded task', **supplied}}

    def test_a_claude_launch_follows_its_declared_class(self):
        env = self.environment(routes=CLAUDE_TABLE)
        self.assertIsNone(self.reason(self.claude(description='code: fix the parser', model='sonnet',
                                                  effort='high'), env, 'claude'))
        self.assertIsNone(self.reason(self.claude(description='gather', model='haiku', effort='medium'),
                                      env, 'claude'))
        for supplied, expected in (
                ({'description': 'fix the parser', 'model': 'sonnet', 'effort': 'high'}, 'task class'),
                ({'description': 'review: diff', 'model': 'sonnet', 'effort': 'high'}, 'task class'),
                ({'model': 'sonnet', 'effort': 'high'}, 'task class'),
                ({'description': 'code: x', 'model': 'opus', 'effort': 'high'}, "model='opus'"),
                ({'description': 'code: x', 'model': 'sonnet', 'effort': 'max'}, "effort='max'"),
                ({'description': 'code: x', 'model': 'sonnet'}, 'effort=None'),
                ({'description': 'codex: x', 'model': 'sonnet', 'effort': 'high'}, 'task class')):
            with self.subTest(supplied=supplied):
                reason = self.reason(self.claude(**supplied), env, 'claude')
                self.assertIn(expected, reason)
                self.assertIn('gather = haiku/medium', reason)

    def test_claude_exemptions_and_opt_out_pass(self):
        env = self.environment(routes=CLAUDE_TABLE,
                               pipeline={'mode': 'evidence-only', 'unrouted_agents': {'Explore': 'inherit'}})
        self.assertIsNone(self.reason(self.claude(subagent_type='fork'), env, 'claude'))
        self.assertIsNone(self.reason(self.claude(resume='agent-1'), env, 'claude'))
        self.assertIsNone(self.reason(self.claude(subagent_type='Explore'), env, 'claude'))
        self.assertIn('task class', self.reason(self.claude(subagent_type='Plan'), env, 'claude'))
        self.assertIn('`gather: ...`', self.reason(self.claude(subagent_type='Plan'), env, 'claude'))
        off = self.environment(routes=CLAUDE_TABLE, pipeline={'mode': 'evidence-only', 'explicit_routes': 'off'})
        self.assertIsNone(self.reason(self.claude(), off, 'claude'))

    def test_an_environment_effort_override_is_refused_unless_it_matches(self):
        launch = self.claude(description='code: x', model='sonnet', effort='high')
        mismatch = self.environment(routes=CLAUDE_TABLE, CLAUDE_CODE_EFFORT_LEVEL='max')
        self.assertIn('CLAUDE_CODE_EFFORT_LEVEL', self.reason(launch, mismatch, 'claude'))
        same = self.environment(routes=CLAUDE_TABLE, CLAUDE_CODE_EFFORT_LEVEL='high')
        self.assertIsNone(self.reason(launch, same, 'claude'))

    def test_a_codex_spawn_follows_its_class_without_inheriting(self):
        env = self.environment('codex', CODEX_TABLE)
        good = {'task_name': 'code_parser_fix', 'model': 'gpt-6.1-sol', 'reasoning_effort': 'high',
                'fork_turns': 'none', 'agent_type': 'worker'}
        self.assertIsNone(self.reason(self.codex(**good), env, 'codex'))
        self.assertIsNone(self.reason(self.codex(**{**good, 'fork_turns': 3}), env, 'codex'))
        for change, expected in (({'fork_turns': None}, 'fork_turns'), ({'fork_turns': 'all'}, 'fork_turns'),
                                 ({'reasoning_effort': 'low'}, "reasoning_effort='low'"),
                                 ({'model': 'gpt-6-luna'}, "model='gpt-6-luna'"),
                                 ({'task_name': 'parser_fix'}, 'task class'),
                                 # A task name is an identifier, so the example continues with an underscore.
                                 ({'task_name': 'parser_fix'}, '`gather_...`')):
            supplied = {key: value for key, value in {**good, **change}.items() if value is not None}
            with self.subTest(change=change):
                self.assertIn(expected, self.reason(self.codex(**supplied), env, 'codex'))

    def test_a_codex_agent_file_that_pins_other_settings_is_refused(self):
        env = self.environment('codex', CODEX_TABLE)
        agents = self.home / '.codex' / 'agents'; agents.mkdir(parents=True)
        (agents / 'pinned.toml').write_text('name = "pinned"\nmodel = "gpt-6-luna"\n', encoding='utf-8')
        (agents / 'same.toml').write_text('name = "same"\nmodel_reasoning_effort = "high"\n', encoding='utf-8')
        launch = {'task_name': 'code', 'model': 'gpt-6.1-sol', 'reasoning_effort': 'high', 'fork_turns': 'none'}
        self.assertIn('pins model', self.reason(self.codex(agent_type='pinned', **launch), env, 'codex'))
        self.assertIsNone(self.reason(self.codex(agent_type='same', **launch), env, 'codex'))
        project = self.project / '.codex' / 'agents'; project.mkdir(parents=True)
        (project / 'same.toml').write_text('model_reasoning_effort = "low"\n', encoding='utf-8')
        self.assertIn('pins model_reasoning_effort', self.reason(self.codex(agent_type='same', **launch), env, 'codex'))

    def context(self, event, environment, client):
        result, error = cli.process(event, client, environment)
        self.assertIsNone(error)
        output = result.get('hookSpecificOutput', {})
        self.assertNotEqual(output.get('permissionDecision'), 'deny')
        return output.get('additionalContext', '')

    def test_a_refusal_says_how_to_choose_a_class_not_only_which_exist(self):
        # A primary holding an older skill learns the selection rule from the refusal alone.
        claude = {'ASSAY_ROUTING_CONFIG': str(self.config(routes=CLAUDE_TABLE, name='claude.json'))}
        codex = {'ASSAY_ROUTING_CONFIG': str(self.config('codex', CODEX_TABLE, name='codex.json'))}
        for reason in (self.reason(self.claude(description='fix the parser', model='sonnet', effort='high'), claude, 'claude'),
                       self.reason(self.claude(description='code: fix', model='opus', effort='medium'), claude, 'claude'),
                       self.reason(self.codex(task_name='parser_fix', fork_turns='none'), codex, 'codex')):
            self.assertIn('not the class whose pair you already chose', reason)
            self.assertIn('take the less demanding one', reason)

    def test_an_admitted_launch_is_reminded_to_record_its_reason_without_being_held(self):
        claude = {'ASSAY_ROUTING_CONFIG': str(self.config(routes=CLAUDE_TABLE, name='claude.json'))}
        codex = {'ASSAY_ROUTING_CONFIG': str(self.config('codex', CODEX_TABLE, name='codex.json'))}
        note = self.context(self.claude(description='code: fix the parser', model='sonnet', effort='high'),
                            claude, 'claude')
        self.assertIn('admitted as class `code` (sonnet/high)', note)
        self.assertIn('why the work fits its class', note)
        note = self.context(self.codex(task_name='gather_logs', model='gpt-6-luna', reasoning_effort='medium',
                                       fork_turns='none'), codex, 'codex')
        self.assertIn('admitted as class `gather` (gpt-6-luna/medium)', note)
        # Exempt launches and launches without a table get no class note.
        self.assertNotIn('admitted as class', self.context(self.claude(subagent_type='fork'), claude, 'claude'))
        self.assertNotIn('admitted as class', self.context(
            self.claude(description='code: fix', model='sonnet', effort='high'), self.environment(), 'claude'))

    def test_a_launch_the_table_does_not_check_is_pointed_at_the_table(self):
        # With a table, the generic launch reminder's advisor-era wording would contradict it.
        table = {'ASSAY_ROUTING_CONFIG': str(self.config(routes=CLAUDE_TABLE, name='claude.json'))}
        exempt = {'ASSAY_ROUTING_CONFIG': str(self.config(
            routes=CLAUDE_TABLE, pipeline={'mode': 'evidence-only', 'unrouted_agents': {'Explore': 'inherit'}},
            name='exempt.json'))}
        off = {'ASSAY_ROUTING_CONFIG': str(self.config(
            routes=CLAUDE_TABLE, pipeline={'mode': 'evidence-only', 'explicit_routes': 'off'}, name='off.json'))}
        codex = {'ASSAY_ROUTING_CONFIG': str(self.config(
            'codex', CODEX_TABLE, pipeline={'mode': 'evidence-only', 'unrouted_agents': {'explorer': 'inherit'}},
            name='codex.json'))}
        for event, environment, client in ((self.claude(subagent_type='fork'), table, 'claude'),
                                           (self.claude(resume='agent-1'), table, 'claude'),
                                           (self.claude(subagent_type='Explore'), exempt, 'claude'),
                                           (self.claude(description='fix it'), off, 'claude'),
                                           (self.codex(agent_type='explorer', task_name='scan'), codex, 'codex')):
            with self.subTest(client=client, supplied=event['tool_input']):
                note = self.context(event, environment, client)
                self.assertIn("outside the owner's route table check", note)
                self.assertNotIn('routing checkpoint', note)
        # Without a table the generic reminder stays.
        self.assertIn('routing checkpoint', self.context(self.claude(subagent_type='fork'), self.environment(), 'claude'))

    def test_without_a_table_codex_is_untouched_and_claude_keeps_the_explicit_check(self):
        self.assertIsNone(self.reason(self.codex(task_name='x'), self.environment('codex'), 'codex'))
        self.assertIn('explicit model and effort', self.reason(self.claude(), self.environment(), 'claude'))

    def test_a_claude_subagent_cannot_launch_agents_of_its_own(self):
        # Nesting is on by default in current Claude Code; only the primary routes.
        table = {'ASSAY_ROUTING_CONFIG': str(self.config(routes=CLAUDE_TABLE, name='claude.json'))}
        off = {'ASSAY_ROUTING_CONFIG': str(self.config(
            routes=CLAUDE_TABLE, pipeline={'mode': 'evidence-only', 'explicit_routes': 'off'}, name='off.json'))}
        admitted = self.claude(description='code: fix the parser', model='sonnet', effort='high')
        for environment in (table, off, self.environment()):
            for supplied in (admitted['tool_input'], {'subagent_type': 'fork'}, {'resume': 'agent-1'}):
                with self.subTest(environment=environment, supplied=supplied):
                    event = {**self.claude(**supplied), 'agent_id': 'child-1', 'agent_type': 'general-purpose'}
                    reason = self.reason(event, environment, 'claude')
                    self.assertTrue(reason.startswith('Assay: only the primary agent launches agents'), reason)
                    self.assertIn('name that step in your report', reason)
        self.assertIsNone(self.reason(admitted, table, 'claude'))
        self.assertIsNone(self.reason({**self.claude(), 'agent_id': 'child-1', 'tool_name': 'Read'}, table, 'claude'))
        # Without a routing configuration ordinary delegation is untouched.
        self.assertIsNone(self.reason({**admitted, 'agent_id': 'child-1'}, {}, 'claude'))
        # Codex hook input does not name the calling agent, so the hook claims nothing there.
        codex = {'ASSAY_ROUTING_CONFIG': str(self.config('codex', CODEX_TABLE, name='codex.json'))}
        good = self.codex(task_name='code_fix', model='gpt-6.1-sol', reasoning_effort='high', fork_turns='none')
        self.assertIsNone(self.reason({**good, 'agent_id': 'child-1'}, codex, 'codex'))

    def test_other_tools_and_another_clients_configuration_are_untouched(self):
        env = self.environment(routes=CLAUDE_TABLE)
        self.assertIsNone(self.reason({**self.claude(), 'tool_name': 'Read'}, env, 'claude'))
        self.assertIsNone(self.reason(self.codex(task_name='x'), env, 'codex'))

    def test_the_table_is_validated_with_the_configuration(self):
        load_config(self.config(routes=CLAUDE_TABLE))
        bad = (
            ('claude', {'classes': {}}),
            ('claude', {'classes': {'Code': {'model': 'sonnet', 'effort': 'high', 'when': 'x'}}}),
            ('claude', {'classes': {'code_x': {'model': 'sonnet', 'effort': 'high', 'when': 'x'}}}),
            ('claude', {'classes': {'code': {'model': 'inherit', 'effort': 'high', 'when': 'x'}}}),
            ('claude', {'classes': {'code': {'model': 'sonnet', 'effort': 'ultra', 'when': 'x'}}}),
            ('claude', {'classes': {'code': {'model': 'sonnet', 'effort': 'high'}}}),
            ('claude', {'classes': {'code': {'model': 'sonnet', 'effort': 'high', 'when': ' '}}}),
            ('codex', {'classes': {'code': {'model': 'gpt-6.1-sol', 'effort': 'default', 'when': 'x'}}}),
            ('claude', {'classes': CLAUDE_TABLE['classes'], 'extra': 1}),
            ('gemini', CLAUDE_TABLE),
        )
        for client, routes in bad:
            with self.subTest(client=client, routes=routes):
                with self.assertRaises(EvidenceError):
                    load_config(self.config(client, routes))
        load_config(self.config('codex', {'classes': {'code': {'model': 'gpt-6.1-sol', 'effort': 'ultra',
                                                               'when': 'x'}}}))

    def test_routing_status_shows_the_table_before_any_launch(self):
        from route_evidence.cache import Cache
        from route_evidence.service import RoutingService
        cache = Cache(self.root / 'cache')
        configured = RoutingService(cache, client='claude', advisor_config=load_config(self.config(routes=CLAUDE_TABLE)),
                                    offline=True).status()
        self.assertEqual(configured['routes']['classes']['code'],
                         {'model': 'sonnet', 'effort': 'high', 'when': 'ordinary implementation'})
        bare = RoutingService(cache, client='claude', advisor_config=load_config(self.config()), offline=True).status()
        self.assertEqual(bare['routes'], {'status': 'not_configured'})

    def test_candidates_propose_the_cheapest_pair_indistinguishable_from_the_best(self):
        from route_evidence.route_table import candidates
        rows = [{'model': 'A', 'effort': 'low', 'score': 0.40, 'cost_usd': 0.1, 'subset': 'main'},
                {'model': 'B', 'effort': 'high', 'score': 0.50, 'cost_usd': 0.4, 'subset': 'main'},
                {'model': 'C', 'effort': 'medium', 'score': 0.55, 'cost_usd': 0.8, 'subset': 'main'},
                {'model': 'C', 'effort': 'max', 'score': 0.54, 'cost_usd': 6.0, 'subset': 'main'},
                {'model': 'D', 'effort': 'low', 'score': 0.90, 'cost_usd': 0.01, 'subset': 'other'},
                {'model': 'E', 'effort': 'low', 'score': None, 'cost_usd': 0.01, 'subset': 'main'}]
        result = candidates(rows, band=0.07, subset='main')
        by = {(r['model'], r['effort']): r for r in result['rows']}
        self.assertEqual(set(by), {('A', 'low'), ('B', 'high'), ('C', 'medium'), ('C', 'max')})
        self.assertEqual([k for k, r in by.items() if r['proposal']], [('B', 'high')])
        self.assertEqual({k for k, r in by.items() if r['within_band']}, {('B', 'high'), ('C', 'medium'), ('C', 'max')})
        self.assertFalse(by[('C', 'max')]['frontier'])
        self.assertTrue(by[('A', 'low')]['frontier'])
        self.assertTrue(candidates(rows, band=0.0, subset='main')['rows'][2]['proposal'])
        self.assertEqual(candidates(rows, band=0.07, subset='none')['status'], 'no_measured_pairs')
        with self.assertRaises(EvidenceError):
            candidates(rows, band=1.5)

    def test_an_invalid_table_follows_the_configuration_source_contract(self):
        # An explicitly selected configuration that fails validation blocks the
        # spawn; a telemetry binding that cannot be read keeps ordinary delegation.
        launch = self.claude(model='sonnet', effort='high')
        explicit = self.environment(routes={'classes': {}})
        self.assertIn('routing doctor', self.reason(launch, explicit, 'claude'))
        binding = self.root / 'binding.json'
        binding.write_text(json.dumps({'config': str(self.config(routes={'classes': {}})),
                                       'cache_dir': str(self.root / 'cache')}), encoding='utf-8')
        result, error = cli.process(launch, 'claude', {'ASSAY_ROUTING_TELEMETRY_CONFIG': str(binding)})
        self.assertNotEqual('deny', result.get('hookSpecificOutput', {}).get('permissionDecision'))
        self.assertIn('telemetry unavailable', error)


if __name__ == '__main__':
    unittest.main()
