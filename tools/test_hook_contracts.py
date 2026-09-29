"""Offline contract tests. Fixtures are not model or native-client evidence."""
from __future__ import annotations

import copy
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'hooks'))
sys.path.insert(0, str(ROOT / 'skills/route-subagents/scripts'))
from runtime import activation, events, state
from runtime import cli
from route_evidence.client_capabilities import contract, claude_overrides, codex_route_check, host_settings
from route_evidence.core import EvidenceError
from route_evidence.pipeline_store import PipelineStore


class ActivationTests(unittest.TestCase):
    def setUp(self):
        self.rules, self.fingerprint = activation.load_rules(ROOT)

    def test_independent_bilingual_positive_negative_and_explicit_fixtures(self):
        cases = json.loads((ROOT / 'tools/fixtures/hooks/prompts.json').read_text(encoding='utf-8'))
        for case in cases:
            with self.subTest(prompt=case['prompt']):
                decision = activation.evaluate({'hook_event_name':'UserPromptSubmit','prompt':case['prompt']}, self.rules)
                self.assertEqual(case['rules'], decision['rule_ids'])
                self.assertLessEqual(len(decision['context']), activation.MAX_CONTEXT)
                self.assertLessEqual(len(decision['rule_ids']), 2)

    def test_bounds_and_non_prompt_events_abstain(self):
        for prompt in (None, {}, 'Implement '+ 'x' * activation.MAX_PROMPT):
            self.assertEqual([], activation.select(prompt, self.rules))
        self.assertEqual({'rule_ids':[], 'context':''}, activation.evaluate({'hook_event_name':'PreToolUse','prompt':'Implement'}, self.rules))

    def test_no_permissions_no_input_echo_and_does_not_mutate_event(self):
        event = {'hook_event_name':'UserPromptSubmit','prompt':'Implement SECRET_SENTINEL'}
        original = copy.deepcopy(event)
        output, error = cli.process(event, 'claude', {})
        self.assertIsNone(error)
        self.assertEqual(original, event)
        self.assertEqual({'hookEventName','additionalContext'}, set(output['hookSpecificOutput']))
        self.assertNotIn('SECRET_SENTINEL', json.dumps(output))
        self.assertIn('read-only', output['hookSpecificOutput']['additionalContext'])

    def test_disabled_missing_and_modified_skills(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shutil.copyfile(ROOT/'catalog.toml', root/'catalog.toml')
            (root/'hooks').mkdir()
            shutil.copyfile(ROOT/'hooks/activation-rules.toml', root/'hooks/activation-rules.toml')
            target = root/'skills/code-change/SKILL.md'
            target.parent.mkdir(parents=True)
            target.write_text('revision-one\n', encoding='utf-8')
            rules, first = activation.load_rules(root)
            self.assertEqual(['code-change'], [r['id'] for r in rules])
            target.write_text('revision-two\n', encoding='utf-8')
            self.assertNotEqual(first, activation.load_rules(root)[1])
            self.assertEqual([], activation.load_rules(root, disabled_skills=['skill/code-change'])[0])
            self.assertEqual([], activation.load_rules(root, disabled_rules=['code-change'])[0])
            with self.assertRaises(ValueError):
                activation.load_rules(root, disabled_skills=['missing'])
            target.unlink()
            self.assertEqual([], activation.load_rules(root)[0])

    def test_unknown_duplicate_and_invalid_patterns_are_errors(self):
        original = (ROOT/'hooks/activation-rules.toml').read_text(encoding='utf-8')
        for replacement in (original.replace('skill/code-change', 'skill/unknown'),
                            original.replace('id = "code-change"', 'id = "audit"'),
                            original.replace("'^(?:implement", "'(?:implement")):
            with self.subTest(replacement=replacement[-100:]), tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp); (root/'hooks').mkdir()
                shutil.copyfile(ROOT/'catalog.toml', root/'catalog.toml')
                (root/'hooks/activation-rules.toml').write_text(replacement, encoding='utf-8')
                with self.assertRaises(ValueError):
                    activation.load_rules(root)


class CapabilitiesTests(unittest.TestCase):
    expected={'model':'sonnet','effort':'low'}

    def test_claude_no_per_call_effort_and_no_configured_runtime_proof(self):
        result=contract('claude', {'surface':'cli','version':'2.1.251'})
        self.assertIs(result['per_call_effort'], False)
        self.assertIsNone(result['observed_effort'])
        self.assertFalse(result['installed_version_verified'])
        self.assertEqual('call_definition_environment_parent', result['model_precedence'])
        for host in ({}, {'surface':'desktop','version':'2.1.251'}, {'surface':'cli','version':'next'}):
            self.assertEqual('unknown', contract('claude', host)['model_precedence'])
        with self.assertRaises(EvidenceError):
            host_settings({'unsupported':True})

    def test_versioned_override_precedence_and_force(self):
        env={'CLAUDE_CODE_SUBAGENT_MODEL':'opus'}
        for host in ({}, {'surface':'cli','version':'2.1.250'}, {'surface':'ide','version':'2.1.251'}):
            self.assertEqual(['model_environment_override'], claude_overrides(self.expected, env, host)['conflicts'])
        host={'surface':'cli','version':'2.1.251'}
        self.assertEqual([], claude_overrides(self.expected, env, host)['conflicts'])
        forced={**env,'CLAUDE_CODE_SUBAGENT_MODEL_FORCE':'1'}
        self.assertEqual(['model_environment_override'], claude_overrides(self.expected, forced, host)['conflicts'])
        self.assertIn('forced_model_unresolved', claude_overrides(self.expected, {'CLAUDE_CODE_SUBAGENT_MODEL_FORCE':'true'}, host)['unverified'])

    def test_auto_inherit_effort_environment_are_not_literal_routes(self):
        modern={'surface':'cli','version':'2.1.196'}
        self.assertEqual([], claude_overrides(self.expected, {'CLAUDE_CODE_SUBAGENT_MODEL':'inherit'}, modern)['conflicts'])
        self.assertTrue(claude_overrides(self.expected, {'CLAUDE_CODE_SUBAGENT_MODEL':'inherit'})['conflicts'])
        self.assertEqual(['effort_default_unresolved'], claude_overrides(self.expected, {'CLAUDE_CODE_EFFORT_LEVEL':'auto'})['unverified'])
        self.assertEqual(['effort_environment_override'], claude_overrides(self.expected, {'CLAUDE_CODE_EFFORT_LEVEL':'high'})['conflicts'])

    def test_codex_custom_config_beats_spawn_and_unknown_model_default(self):
        expected={'model':'worker','effort':'low'}
        spawn={'model':'worker','model_reasoning_effort':'low','message':'preserve'}
        schema={'properties':{'model':{},'model_reasoning_effort':{},'message':{}}}
        result=codex_route_check(expected, spawn, definition={'model':'other','model_reasoning_effort':'high'}, tool_schema=schema, spawn_fields={'model':'model','effort':'model_reasoning_effort'})
        self.assertEqual({'model':'other','effort':'high'}, result['configured'])
        self.assertEqual(['model_configuration_override','effort_configuration_override'], result['conflicts'])
        self.assertEqual('preserve', spawn['message'])
        result=codex_route_check(expected, {'model':'worker'}, parent={'model_reasoning_effort':'low'}, tool_schema=schema, spawn_fields={'model':'model','effort':'model_reasoning_effort'})
        self.assertIn('effort_unresolved', result['unverified'])
        self.assertFalse(result['launch_verified'])
        self.assertIn('spawn_field_not_exposed:model', codex_route_check(expected, spawn, spawn_fields={'model':'model','effort':'model_reasoning_effort'})['conflicts'])
        self.assertIsNone(contract('codex')['strict_adapter'])
        self.assertTrue(contract('codex')['input_rewrite_requires_allow'])

    def test_native_argument_names_are_not_inferred_from_config_names(self):
        expected={'model':'worker','effort':'low'}
        supplied={'model':'worker','reasoning_effort':'low'}
        schema={'properties':{'model':{},'reasoning_effort':{'enum':['low','high']}}}
        result=codex_route_check(expected,supplied,tool_schema=schema)
        self.assertIn('spawn_field_binding_unverified:effort',result['unverified'])
        self.assertIsNone(result['configured']['effort'])
        binding={'model':'model','effort':'reasoning_effort'}
        result=codex_route_check(expected,supplied,tool_schema=schema,spawn_fields=binding)
        self.assertEqual(expected,result['configured']); self.assertEqual([],result['conflicts'])
        result=codex_route_check(expected,{**supplied,'reasoning_effort':'unsupported'},tool_schema=schema,spawn_fields=binding)
        self.assertIn('spawn_value_not_exposed:reasoning_effort',result['conflicts'])

    def test_preflight_invalid_schema_and_inputs(self):
        for supplied in ([], 'string', None):
            with self.assertRaises(EvidenceError):
                codex_route_check(self.expected, supplied)
        with self.assertRaises(EvidenceError):
            codex_route_check(self.expected, {}, tool_schema={'properties':[]})


class StateTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.directory=Path(self.tmp.name)/'data'; self.now=1000.
        self.rules,self.fp=activation.load_rules(ROOT)
        self.event={'hook_event_name':'UserPromptSubmit','session_id':'session', 'cwd':str(Path(self.tmp.name)/'work'),
                    'transcript_path':'transcript-parent', 'turn_id':'turn-1','prompt':'Implement SECRET_SENTINEL'}
    def apply(self, event=None, client='codex', **kwargs):
        event=self.event if event is None else event
        return state.apply(event, client, activation.evaluate(event,self.rules), self.rules,self.fp,
                           self.directory, clock=lambda:self.now, **kwargs)

    def test_duplicates_real_turns_and_no_text_based_deduplication(self):
        self.assertTrue(self.apply()['context'])
        self.assertEqual('', self.apply()['context'])
        self.assertTrue(self.apply({**self.event,'turn_id':'turn-2'})['context'])
        # Claude's identical text may be a new request: no guessed turn id.
        self.assertTrue(self.apply(client='claude')['context'])
        self.assertTrue(self.apply(client='claude')['context'])

    def test_scope_does_not_merge_session_worktree_worker_or_transcript(self):
        self.apply()
        for change in ({'session_id':'different'}, {'cwd':'different'}, {'agent_id':'child'}, {'transcript_path':'child'}):
            with self.subTest(change=change):
                self.assertTrue(self.apply({**self.event,**change})['context'])
        self.assertIsNone(events.identity({'session_id':'s','cwd':'c'}, 'codex'))
        self.assertIsNone(events.identity({**self.event,'transcript_path':{}}, 'codex'))

    def test_restore_clear_new_task_fingerprint_expiry(self):
        self.apply()
        post={**self.event,'hook_event_name':'PostCompact'}
        self.assertEqual('', self.apply(post)['context'])
        pre={**self.event,'hook_event_name':'PreToolUse','tool_name':'spawn_agent','tool_use_id':'next-call'}
        self.assertIn('Previous request', self.apply(pre)['context'])
        self.assertEqual('', self.apply(pre)['context'])
        compact={**self.event,'hook_event_name':'SessionStart','source':'resume'}
        self.assertIn('Previous request', self.apply(compact)['context'])
        self.assertEqual('', state.apply(compact,'codex',{'rule_ids':[],'context':''}, self.rules,'changed', self.directory,clock=lambda:self.now)['context'])
        self.apply({**self.event,'prompt':'What does this mean?','turn_id':'turn-2'})
        self.assertEqual('', self.apply(compact)['context'])
        self.apply({**self.event,'turn_id':'turn-3'})
        self.apply({**self.event,'hook_event_name':'SessionStart','source':'clear'})
        self.assertEqual('', self.apply(compact)['context'])
        self.apply({**self.event,'turn_id':'turn-4'})
        self.now += state.TTL+1
        self.assertEqual('', self.apply(compact)['context'])

    def test_session_end_and_default_no_event_recording(self):
        self.apply()
        with PipelineStore(self.directory, clock=lambda:self.now).transaction() as tx:
            self.assertEqual([], tx.values('hook-event'))
        self.apply({**self.event,'hook_event_name':'SessionEnd'})
        self.assertEqual('', self.apply({**self.event,'hook_event_name':'PostCompact'})['context'])

    def test_recording_is_bounded_and_contains_no_prompt_path_or_args(self):
        with patch.object(state,'MAX_OWN_RECORDS',3):
            for index in range(8):
                self.now+=1
                self.apply({**self.event,'turn_id':str(index)},record=True)
        with PipelineStore(self.directory, clock=lambda:self.now).transaction() as tx:
            for kind in state.KINDS:
                self.assertLessEqual(len(tx.values(kind)),3)
            records=tx.values('hook-event')
            self.assertEqual(3,len(records))
            serialized=json.dumps(records)
            for private in ('SECRET_SENTINEL',self.event['cwd'], 'transcript-parent','session'):
                self.assertNotIn(private,serialized)
            self.assertEqual('command_input_unattested', records[0]['evidence'])


class RuntimeTests(unittest.TestCase):
    def invoke(self, payload, client='claude', extra=(), environment=None):
        env={k:v for k,v in os.environ.items() if not k.startswith('ASSAY_') and k not in {'PLUGIN_DATA','CLAUDE_PLUGIN_DATA'}}
        env.update(environment or {})
        return subprocess.run([sys.executable,'-I','-B',str(ROOT/'hooks/runtime/cli.py'),'--client',client,*extra],
                              input=payload,capture_output=True,env=env,timeout=10)

    def test_alias_normalization_preserves_native_input_and_client(self):
        event={'hook_event_name':'PreToolUse','tool_name':'spawn_agent','tool_input':{'message':'x'}}
        got=events.normalize(event,'codex')
        self.assertEqual('spawn',got['operation']); self.assertEqual('spawn_agent',got['native_tool'])
        self.assertIs(event,got['payload'])
        self.assertIsNone(events.normalize(event,'claude')['operation'])
        self.assertIsNone(events.normalize({'hook_event_name':'PermissionDenied'},'codex'))

    def test_process_output_and_invalid_input_do_not_echo(self):
        result=self.invoke(b'{"hook_event_name":"UserPromptSubmit","prompt":"Implement SECRET_SENTINEL"}')
        self.assertEqual(0,result.returncode,result.stderr)
        self.assertEqual(b'', result.stderr)
        self.assertEqual({'hookEventName','additionalContext'},set(json.loads(result.stdout)['hookSpecificOutput']))
        self.assertNotIn(b'SECRET_SENTINEL',result.stdout)
        for raw in (b'SECRET_SENTINEL', b'[]', b'null', b'\xff', b' '*(cli.MAX_INPUT+1)):
            result=self.invoke(raw)
            self.assertEqual(1,result.returncode)
            self.assertEqual(b'',result.stdout)
            self.assertNotIn(b'SECRET_SENTINEL',result.stderr)

    def test_no_hint_failure_can_erase_a_guard_decision(self):
        event={'hook_event_name':'PreToolUse','tool_name':'Agent','tool_input':{}}
        denied={'hookSpecificOutput':{'hookEventName':'PreToolUse','permissionDecision':'deny','permissionDecisionReason':'test'}}
        with patch.object(cli, 'routing_result',return_value=denied), patch.object(cli,'load_rules',side_effect=RuntimeError('SECRET')):
            result,error=cli.process(event,'claude',{})
        self.assertEqual(denied,result); self.assertNotIn('SECRET',error)
        with patch.object(cli,'routing_result',return_value={}), patch.object(cli,'load_rules',side_effect=ImportError()):
            result,error=cli.process(event,'claude',{})
        self.assertEqual({},result); self.assertTrue(error)

    def test_codex_required_guard_denies_without_allow_or_rewrite(self):
        config={'client':'codex','pipeline':{'mode':'required'}}
        event={'hook_event_name':'PreToolUse','tool_name':'spawn_agent','tool_input':{'model':'x'}}
        with patch.object(cli,'load_config',return_value=config):
            result,error=cli.process(event,'codex',{'ASSAY_ROUTING_CONFIG':'configured'})
        self.assertIsNone(error)
        self.assertEqual('deny',result['hookSpecificOutput']['permissionDecision'])
        self.assertNotIn('updatedInput',json.dumps(result))
        self.assertEqual('x',event['tool_input']['model'])
        with patch.object(cli,'load_config',return_value=config):
            self.assertEqual({},cli.routing_result({**event,'tool_name':'apply_patch'},'codex',{'ASSAY_ROUTING_CONFIG':'configured'}))

    def test_bad_advisory_settings_are_nonblocking_and_readonly(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'settings.json'; raw='{"unknown":true}'; path.write_text(raw, encoding='utf-8')
            result=self.invoke(b'{"hook_event_name":"UserPromptSubmit","prompt":"Implement"}',environment={'ASSAY_HOOK_CONFIG':str(path)})
            self.assertEqual(0,result.returncode)
            self.assertEqual({},json.loads(result.stdout))
            self.assertEqual(raw,path.read_text(encoding='utf-8'))
            self.assertTrue(result.stderr)

    def test_doctor_does_not_claim_trust_or_native_execution_and_never_writes(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'settings.json'; raw=json.dumps({'hooks':{'PreToolUse':[{'matcher':'Agent','hooks':[{'type':'command','command':'foreign'}]}]}})
            path.write_text(raw, encoding='utf-8')
            report=cli.doctor('codex',{},settings_path=path)
            self.assertEqual('unknown',report['hooks_trusted'])
            self.assertEqual('unverified',report['native_execution'])
            self.assertTrue(report['conflicts'])
            self.assertFalse(report['settings_modified'])
            self.assertEqual(raw,path.read_text(encoding='utf-8'))

    def test_codex_postcompact_never_emits_unsupported_context(self):
        with tempfile.TemporaryDirectory() as tmp:
            env={'PLUGIN_DATA':str(Path(tmp)/'data')}
            event={'hook_event_name':'UserPromptSubmit','session_id':'s','cwd':'work',
                   'transcript_path':'root','turn_id':'1','prompt':'Implement'}
            cli.process(event,'codex',env)
            result,error=cli.process({**event,'hook_event_name':'PostCompact'},'codex',env)
            self.assertEqual({},result); self.assertIsNone(error)
            pre={**event,'hook_event_name':'PreToolUse','tool_name':'spawn_agent','tool_use_id':'t'}
            result,error=cli.process(pre,'codex',env)
            context=result['hookSpecificOutput']['additionalContext']
            self.assertIn('route-subagents',context)
            self.assertIn('code-change',context)
            self.assertLess(len(context),1000)

    def test_rebinding_cannot_erase_an_earlier_effort_mismatch(self):
        from routing_hook import observe_effort, _recheck_observed
        run={'route':{'model':'sonnet','effort':'low'},'binding':'start_order'}
        observe_effort(run,{'effort':{'level':'high'}})
        observe_effort(run,{'effort':{'level':'low'}})
        self.assertNotIn('route_mismatch',run)
        run['binding']='host_result'; _recheck_observed(run)
        self.assertTrue(run['route_mismatch'])
        _recheck_observed(run)
        self.assertTrue(run['route_mismatch'])

    def test_failed_guard_redacts_returns_and_blocks_unknown_handbacks(self):
        from routing_hook import failure
        returned={'hook_event_name':'PostToolUse','tool_name':'Agent','tool_response':{'secret':'SENTINEL'}}
        result=failure(returned,'plugin',True)
        self.assertIn('updatedToolOutput',result['hookSpecificOutput'])
        self.assertNotIn('SENTINEL',json.dumps(result))
        result=failure({'hook_event_name':'PreToolUse','tool_name':'SubagentHandback'},'plugin',True)
        self.assertEqual('deny',result['hookSpecificOutput']['permissionDecision'])

    def test_offline_replay_ignores_installed_environment(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'events.jsonl'
            path.write_text('{"hook_event_name":"UserPromptSubmit","prompt":"Implement"}\n', encoding='utf-8')
            nonexistent=Path(tmp)/'must-not-exist'
            result=self.invoke(b'',extra=('replay','--input',str(path)),environment={
                'ASSAY_ROUTING_CONFIG':str(nonexistent),'PLUGIN_DATA':str(nonexistent), 'ASSAY_HOOK_CONFIG':str(nonexistent)})
            self.assertEqual(0,result.returncode,result.stderr)
            self.assertEqual('synthetic_replay',json.loads(result.stdout)['evidence'])
            self.assertFalse(nonexistent.exists())

    def test_readonly_codex_preflight_cli(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'input.json'
            path.write_text(json.dumps({'expected':{'model':'x','effort':'low'},'supplied':{}}), encoding='utf-8')
            result=self.invoke(b'',client='codex',extra=('route-preflight','--input',str(path)))
            self.assertEqual(0,result.returncode,result.stderr)
            self.assertFalse(json.loads(result.stdout)['launch_verified'])


if __name__=='__main__':
    unittest.main()
