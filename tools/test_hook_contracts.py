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
import tomllib
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


SUGGESTS = 'The request suggests '
CHECK = 'Assay skill check:'


class ActivationTests(unittest.TestCase):
    def setUp(self):
        self.rules, self.fingerprint = activation.load_rules(ROOT)

    def test_independent_bilingual_positive_negative_and_explicit_fixtures(self):
        cases = json.loads((ROOT / 'tools/fixtures/hooks/prompts.json').read_text(encoding='utf-8'))
        check = activation.skill_check(self.rules)
        for case in cases:
            with self.subTest(prompt=case['prompt']):
                decision = activation.evaluate({'hook_event_name':'UserPromptSubmit','prompt':case['prompt']}, self.rules)
                self.assertEqual(case['rules'], decision['rule_ids'])
                self.assertLessEqual(len(decision['rule_ids']), 2)
                self.assertTrue(decision['context'].endswith(check))
                self.assertEqual(bool(case['rules']), SUGGESTS in decision['context'])
                self.assertLessEqual(len(decision['context']), activation.MAX_CONTEXT + 1 + activation.MAX_CHECK)

    def test_skill_check_names_every_enabled_skill_once_within_its_bound(self):
        check = activation.skill_check(self.rules)
        self.assertTrue(check.startswith(CHECK))
        self.assertTrue(check.isascii())
        self.assertLessEqual(len(check), activation.MAX_CHECK)
        listed = [entry.split(' - ', 1)[0] for entry in check.split('Skills: ', 1)[1].rstrip('.').split('; ')]
        self.assertEqual([r['skill'].split('/', 1)[1] for r in self.rules], listed)
        catalog = tomllib.loads((ROOT / 'catalog.toml').read_text(encoding='utf-8'))
        self.assertEqual(sorted(a['id'] for a in catalog['assets'] if a['kind'] == 'skill'),
                         sorted(r['skill'] for r in self.rules))
        for prompt in ('2 + 2', 'Составь план', 'Use code-change'):
            with self.subTest(prompt=prompt):
                context = activation.evaluate({'hook_event_name':'UserPromptSubmit','prompt':prompt}, self.rules)['context']
                self.assertEqual(1, context.count(CHECK))
                self.assertTrue(context.endswith(check))

    def test_skill_check_leaves_room_for_one_more_skill(self):
        # A new skill adds its entry and its name in the loaded list. Without
        # this room the next skill fails load_rules and every skill hint drops.
        name = max((r['skill'].split('/', 1)[1] for r in self.rules), key=len)
        extra = {'id': 'explicit:skill/x' + name[1:], 'skill': 'skill/x' + name[1:], 'priority': 0,
                 'patterns': [], 'cue': 'x' * activation.MAX_CUE}
        length = activation.longest_check([*self.rules, extra])
        self.assertLessEqual(length, activation.MAX_CHECK,
                             f'one more skill with a {len(name)}-character name and a full cue would make the '
                             f'skill check {length} characters; raise MAX_CHECK or shorten cues')

    def test_bounds_and_non_prompt_events_abstain(self):
        for prompt in (None, {}, 'Use code-change '+ 'x' * activation.MAX_PROMPT):
            self.assertEqual([], activation.select(prompt, self.rules))
        self.assertEqual({'rule_ids':[], 'context':''}, activation.evaluate({'hook_event_name':'PreToolUse','prompt':'Use code-change'}, self.rules))

    def test_no_permissions_no_input_echo_and_does_not_mutate_event(self):
        event = {'hook_event_name':'UserPromptSubmit','prompt':'Use code-change for SECRET_SENTINEL'}
        original = copy.deepcopy(event)
        output, error = cli.process(event, 'claude', {})
        self.assertIsNone(error)
        self.assertEqual(original, event)
        self.assertEqual({'hookEventName','additionalContext'}, set(output['hookSpecificOutput']))
        self.assertNotIn('SECRET_SENTINEL', json.dumps(output))
        self.assertIn(SUGGESTS + 'code-change.', output['hookSpecificOutput']['additionalContext'])
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
            self.assertEqual(['explicit:skill/code-change'], [r['id'] for r in rules])
            target.write_text('revision-two\n', encoding='utf-8')
            self.assertNotEqual(first, activation.load_rules(root)[1])
            self.assertEqual([], activation.load_rules(root, disabled_skills=['skill/code-change'])[0])
            # Retired rule ids in old settings are accepted and change nothing.
            retired = activation.load_rules(root, disabled_rules=['code-change', 'delegation'])
            self.assertEqual(activation.load_rules(root), retired)
            unchecked, fingerprint = activation.load_rules(root, disabled_rules=['skill-check'])
            self.assertEqual(['explicit:skill/code-change'], [r['id'] for r in unchecked])
            self.assertEqual('', activation.skill_check(unchecked))
            self.assertNotEqual(retired[1], fingerprint)
            decision = activation.evaluate({'hook_event_name':'UserPromptSubmit','prompt':'Use code-change'}, unchecked)
            self.assertEqual(['explicit:skill/code-change'], decision['rule_ids'])
            self.assertNotIn(CHECK, decision['context'])
            for disabled in ({'disabled_skills': ['missing']}, {'disabled_rules': ['unknown-rule']}):
                with self.subTest(disabled=disabled), self.assertRaises(ValueError):
                    activation.load_rules(root, **disabled)
            target.unlink()
            self.assertEqual([], activation.load_rules(root)[0])

    def test_hook_settings_disable_skills_and_check_through_both_clients(self):
        cases = (
            ({}, ['explicit:skill/route-subagents'], True),
            ({'disabled_skills': ['skill/route-subagents']}, [], True),
            ({'disabled_rules': ['skill-check']}, ['explicit:skill/route-subagents'], False),
            ({'disabled_rules': ['delegation']}, ['explicit:skill/route-subagents'], True),
        )
        with tempfile.TemporaryDirectory() as temporary:
            config = Path(temporary) / 'hooks.json'
            for client in ('codex', 'claude'):
                for settings, selected, checked in cases:
                    with self.subTest(client=client, settings=settings):
                        config.write_text(json.dumps(settings), encoding='utf-8')
                        event = {'hook_event_name': 'UserPromptSubmit', 'prompt': '$route-subagents'}
                        before = copy.deepcopy(event)
                        result, error = cli.process(event, client, {'ASSAY_HOOK_CONFIG': str(config)})
                        self.assertIsNone(error)
                        self.assertEqual(before, event)
                        context = result.get('hookSpecificOutput', {}).get('additionalContext', '')
                        self.assertEqual(bool(selected), SUGGESTS + 'route-subagents.' in context)
                        self.assertEqual(checked, CHECK in context)
                        if checked:
                            self.assertEqual(not selected, 'route-subagents - ' not in context)

    def test_invalid_skill_map_documents_are_errors(self):
        original = (ROOT/'hooks/activation-rules.toml').read_text(encoding='utf-8')
        for replacement in (original.replace('skill/code-change', 'skill/unknown'),
                            original.replace('skill = "skill/test-writing"', 'skill = "skill/code-change"'),
                            original.replace('schema = 2', 'schema = 1'),
                            original.replace('cue = "writing or repairing tests"', 'cue = "тесты"'),
                            original.replace('cue = "writing or repairing tests"', 'cue = "' + 'x' * (activation.MAX_CUE + 1) + '"'),
                            original + '\n[[rules]]\nid = "code-change"\n'):
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
                    'transcript_path':'transcript-parent', 'turn_id':'turn-1','prompt':'Use code-change for SECRET_SENTINEL'}
    def apply(self, event=None, client='codex', **kwargs):
        event=self.event if event is None else event
        return state.apply(event, client, activation.evaluate(event,self.rules), self.rules,self.fp,
                           self.directory, clock=lambda:self.now, **kwargs)

    # The check is in every delivered prompt context, so delivery of the hint
    # itself is asserted by its sentence; suppression leaves the context empty.
    SUGGESTS = 'The request suggests code-change'

    def test_duplicates_real_turns_and_no_text_based_deduplication(self):
        self.assertIn(self.SUGGESTS, self.apply()['context'])
        self.assertEqual('', self.apply()['context'])
        self.assertIn(self.SUGGESTS, self.apply({**self.event,'turn_id':'turn-2'})['context'])
        # Claude's identical text may be a new request: no guessed turn id.
        self.assertIn(self.SUGGESTS, self.apply(client='claude')['context'])
        self.assertIn(self.SUGGESTS, self.apply(client='claude')['context'])

    def test_scope_does_not_merge_session_worktree_worker_or_transcript(self):
        self.apply()
        for change in ({'session_id':'different'}, {'cwd':'different'}, {'agent_id':'child'}, {'transcript_path':'child'}):
            with self.subTest(change=change):
                self.assertIn(self.SUGGESTS, self.apply({**self.event,**change})['context'])
        self.assertIsNone(events.identity({'session_id':'s','cwd':'c'}, 'codex'))
        self.assertIsNone(events.identity({**self.event,'transcript_path':{}}, 'codex'))

    def test_restore_clear_new_task_fingerprint_expiry(self):
        self.apply()
        post={**self.event,'hook_event_name':'PostCompact'}
        self.assertEqual('', self.apply(post)['context'])
        pre={**self.event,'hook_event_name':'PreToolUse','tool_name':'spawn_agent','tool_use_id':'next-call'}
        self.assertIn('Previous request suggested code-change', self.apply(pre)['context'])
        self.assertEqual('', self.apply(pre)['context'])
        compact={**self.event,'hook_event_name':'SessionStart','source':'resume'}
        self.assertIn('Previous request suggested code-change', self.apply(compact)['context'])
        self.assertEqual('', state.apply(compact,'codex',{'rule_ids':[],'context':''}, self.rules,'changed', self.directory,clock=lambda:self.now)['context'])
        self.apply({**self.event,'prompt':'What does this mean?','turn_id':'turn-2'})
        self.assertEqual('', self.apply(compact)['context'])
        self.apply({**self.event,'turn_id':'turn-3'})
        self.apply({**self.event,'hook_event_name':'SessionStart','source':'clear'})
        self.assertEqual('', self.apply(compact)['context'])
        self.apply({**self.event,'turn_id':'turn-4'})
        self.now += state.TTL+1
        self.assertEqual('', self.apply(compact)['context'])

    def test_session_end_and_postcompact_leave_no_restorable_context(self):
        self.apply()
        self.apply({**self.event,'hook_event_name':'SessionEnd'})
        self.assertEqual('', self.apply({**self.event,'hook_event_name':'PostCompact'})['context'])

    def test_records_are_bounded_and_contain_no_prompt_path_or_args(self):
        with patch.object(state,'MAX_OWN_RECORDS',3):
            for index in range(8):
                self.now+=1
                self.apply({**self.event,'turn_id':str(index)})
        with PipelineStore(self.directory, clock=lambda:self.now).transaction() as tx:
            for kind in state.KINDS:
                self.assertLessEqual(len(tx.values(kind)),3)
            self.assertEqual(3,len(tx.values('hook-seen')))
            serialized=json.dumps([tx.values(kind) for kind in state.KINDS])
            for private in ('SECRET_SENTINEL',self.event['cwd'], 'transcript-parent','session'):
                self.assertNotIn(private,serialized)


class ReviewerBoundaryTests(unittest.TestCase):
    def test_required_effort_variant_keeps_the_reading_boundary(self):
        result = cli.reviewer_boundary({"hook_event_name": "PreToolUse",
            "agent_type": "assay-evidence-reviewer-low-0123456789abcdef", "tool_name": "Write"}, {})
        self.assertEqual(result["hookSpecificOutput"]["permissionDecision"], "deny")
        self.assertEqual(cli.reviewer_boundary({"hook_event_name": "PreToolUse",
            "agent_type": "assay-evidence-reviewer-not-a-variant", "tool_name": "Write"}, {}), {})

    def test_review_claim_tick_memory_file_and_nested_tool_calls_are_denied(self):
        for client in ("codex", "claude"):
            for tool in ("mcp__planning__claim_work_item", "mcp__planning__tick_work_item_checklist_item",
                         "mcp__memory__save", "apply_patch", "Write", "Bash", "spawn_agent", "Agent", "exec"):
                with self.subTest(client=client, tool=tool):
                    result, _ = cli.process({"hook_event_name": "PreToolUse", "agent_type": "assay:evidence-reviewer",
                                             "tool_name": tool, "tool_input": {}}, client, {})
                    self.assertEqual(result["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_read_tools_and_writable_worker_remain_available(self):
        for client in ("codex", "claude"):
            for role, tool in (("evidence-reviewer", "Read"), ("evidence-reviewer", "mcp__openaiDeveloperDocs__fetch_openai_doc"),
                               ("evidence-reviewer", "mcp__serena__find_symbol"), ("worker", "mcp__planning__claim_work_item")):
                result = cli.reviewer_boundary({"hook_event_name": "PreToolUse", "agent_type": role, "tool_name": tool}, {})
                self.assertEqual(result, {})
        self.assertEqual(cli.reviewer_boundary({"hook_event_name": "PreToolUse", "tool_name": "Write"}, {}), {})

    def test_reading_roles_can_hand_back_their_report(self):
        for client in ("codex", "claude"):
            for role in ("assay:evidence-reviewer", "official-docs-researcher",
                         "assay-evidence-reviewer-medium-0123456789abcdef"):
                with self.subTest(client=client, role=role):
                    result, _ = cli.process({"hook_event_name": "PreToolUse", "agent_type": role,
                                             "tool_name": "SubagentHandback", "tool_input": {"message": "findings"}},
                                            client, {})
                    self.assertNotEqual("deny", result.get("hookSpecificOutput", {}).get("permissionDecision"))

    def test_boundary_allows_each_rendered_claude_tool_only_for_its_profile(self):
        rendered = {}
        for path in sorted((ROOT / "adapters/claude/agents").glob("*.md")):
            line = next(line for line in path.read_text(encoding="utf-8").splitlines() if line.startswith("tools:"))
            rendered[path.stem] = [tool.strip() for tool in line.split(":", 1)[1].split(",") if tool.strip()]
        self.assertEqual({"evidence-reviewer", "official-docs-researcher"}, set(rendered))
        for role, tools in rendered.items():
            for tool in tools:
                with self.subTest(role=role, tool=tool):
                    self.assertEqual({}, cli.reviewer_boundary(
                        {"hook_event_name": "PreToolUse", "agent_type": "assay:" + role, "tool_name": tool}, {}))
        for tool in sorted(set(rendered["official-docs-researcher"]) - set(rendered["evidence-reviewer"])):
            with self.subTest(denied=tool):
                result = cli.reviewer_boundary({"hook_event_name": "PreToolUse",
                                                "agent_type": "assay:evidence-reviewer", "tool_name": tool}, {})
                self.assertEqual("deny", result["hookSpecificOutput"]["permissionDecision"])

    def test_native_start_identity_is_used_without_parent_session_guess(self):
        (ROOT / "tmp").mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=ROOT / "tmp") as tmp:
            env = {"PLUGIN_DATA": tmp}
            worker = "11111111-2222-7333-8444-555555555555"
            cli.reviewer_boundary({"hook_event_name": "SubagentStart", "session_id": "parent", "agent_id": worker,
                                   "agent_type": "evidence-reviewer"}, env)
            result = cli.reviewer_boundary({"hook_event_name": "PreToolUse", "session_id": "parent",
                "transcript_path": "/logs/rollout-" + worker + ".jsonl", "tool_name": "mcp__planning__claim_work_item"}, env)
            self.assertEqual(result["hookSpecificOutput"]["permissionDecision"], "deny")
            self.assertEqual(cli.reviewer_boundary({"hook_event_name": "PreToolUse", "session_id": "parent",
                "agent_id": "other-worker", "tool_name": "Write"}, env), {})


class ExplicitRouteTests(unittest.TestCase):
    """Claude launches name a model and an effort instead of inheriting both."""

    def setUp(self):
        tmp=tempfile.TemporaryDirectory(); self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name); self.project=self.root/'project'/'nested'; self.project.mkdir(parents=True)
        self.home=self.root/'home'
        home=patch.object(Path,'home',return_value=self.home); home.start(); self.addCleanup(home.stop)

    def environment(self, pipeline=None, client='claude', variable='PLUGIN_DATA'):
        config=self.root/'config.json'
        config.write_text(json.dumps({'schema_version':5,'client':client,
                                      **({'pipeline':pipeline} if pipeline is not None else {})}),encoding='utf-8')
        if variable=='ASSAY_ROUTING_CONFIG':
            return {variable:str(config)}
        data=self.root/'plugin-data'; data.mkdir(exist_ok=True)
        (data/'routing.json').write_text(json.dumps({'config':str(config),'cache_dir':str(self.root/'cache')}),
                                         encoding='utf-8')
        return {variable:str(data)}

    def launch(self, **supplied):
        return {'hook_event_name':'PreToolUse','tool_name':'Agent','session_id':'s','tool_use_id':'t',
                'cwd':str(self.project),'tool_input':{'prompt':'Do the bounded task',**supplied}}

    def reason(self, event, environment, client='claude'):
        result,error=cli.process(event,client,environment)
        self.assertIsNone(error)
        output=result.get('hookSpecificOutput',{})
        return output.get('permissionDecisionReason') if output.get('permissionDecision')=='deny' else None

    def definition(self, directory, name, frontmatter):
        directory.mkdir(parents=True,exist_ok=True)
        (directory/(name+'.md')).write_text('---\nname: '+name+'\n'+frontmatter+'---\nWork.\n',encoding='utf-8')

    def test_a_launch_missing_either_setting_is_refused_with_the_remedy(self):
        env=self.environment()
        for supplied,missing in (({},'model and effort'),({'model':'sonnet'},'effort'),({'effort':'low'},'model'),
                                 ({'model':'sonnet','effort':''},'effort')):
            with self.subTest(supplied=supplied):
                reason=self.reason(self.launch(**supplied),env)
                self.assertIn('explicit '+missing+' in this Agent call',reason)
                self.assertIn('explicit instruction the Agent effort field asks for',reason)
        self.assertIsNone(self.reason(self.launch(model='sonnet',effort='low'),env))
        self.assertIsNone(self.reason(self.launch(model='haiku',effort='max',subagent_type='Explore'),env))

    def test_a_routing_configuration_variable_applies_the_same_check(self):
        env=self.environment(variable='ASSAY_ROUTING_CONFIG')
        self.assertIn('explicit model and effort',self.reason(self.launch(),env))
        self.assertIsNone(self.reason(self.launch(model='sonnet',effort='medium'),env))

    def test_forks_continuations_exemptions_and_opt_out_pass(self):
        exempt=self.environment({'mode':'evidence-only','unrouted_agents':{'Explore':'inherit'}})
        self.assertIsNone(self.reason(self.launch(subagent_type='fork'),exempt))
        self.assertIsNone(self.reason(self.launch(resume='agent-1'),exempt))
        self.assertIsNone(self.reason(self.launch(subagent_type='Explore'),exempt))
        self.assertIn('explicit model and effort',self.reason(self.launch(subagent_type='Plan'),exempt))
        self.assertIsNone(self.reason(self.launch(),self.environment({'mode':'evidence-only','explicit_routes':'off'})))

    def test_a_definition_pinning_both_settings_is_explicit(self):
        project=self.project.parent/'.claude'/'agents'
        self.definition(project,'pinned','model: haiku\neffort: low\n')
        self.definition(project,'model-only','model: "sonnet"\n')
        self.definition(project,'inheriting','model: inherit\neffort: high\n')
        self.definition(self.home/'.claude'/'agents','personal','model: opus\neffort: medium\n')
        self.definition(self.home/'.claude'/'agents','model-only','model: opus\neffort: medium\n')
        env=self.environment()
        self.assertIsNone(self.reason(self.launch(subagent_type='pinned'),env))
        self.assertIsNone(self.reason(self.launch(subagent_type='personal'),env))
        self.assertIsNone(self.reason(self.launch(subagent_type='model-only',effort='low'),env))
        # The nearest definition decides; a user one never fills a project gap.
        self.assertIn('explicit effort',self.reason(self.launch(subagent_type='model-only'),env))
        self.assertIn('explicit model',self.reason(self.launch(subagent_type='inheriting'),env))
        # Plugin agents and path-like names are not read from disk.
        self.definition(project,'evidence-reviewer','model: haiku\neffort: low\n')
        for kind in ('assay:evidence-reviewer','../pinned','.hidden'):
            with self.subTest(kind=kind):
                self.assertIn('explicit model and effort',self.reason(self.launch(subagent_type=kind),env))

    def test_a_client_without_the_effort_field_is_sent_to_definitions(self):
        env=self.environment({'mode':'evidence-only','host':{'version':'2.1.250','surface':'cli'}})
        self.assertIn('definition whose frontmatter sets effort',self.reason(self.launch(model='sonnet'),env))
        self.assertIn('explicit model',self.reason(self.launch(effort='low'),env))

    def test_other_clients_tools_modes_and_missing_bindings_are_untouched(self):
        self.assertIsNone(self.reason(self.launch(),{}))
        self.assertIsNone(self.reason({**self.launch(),'tool_name':'Bash'},self.environment()))
        self.assertIsNone(self.reason({**self.launch(),'hook_event_name':'PostToolUse'},self.environment()))
        self.assertEqual({},cli.explicit_routes(self.launch(),'claude',self.environment(client='codex')))
        self.assertEqual({},cli.explicit_routes(self.launch(),'codex',self.environment()))

    def test_an_invalid_setting_is_rejected_and_refuses_configured_delegation(self):
        from route_evidence.pipeline_config import settings
        with self.assertRaisesRegex(EvidenceError,'invalid_pipeline_explicit_routes'):
            settings({'pipeline':{'explicit_routes':'sometimes'}})
        output=cli.explicit_routes(self.launch(),'claude',
                                  self.environment({'mode':'evidence-only','explicit_routes':'sometimes'}))
        self.assertEqual('deny',output['hookSpecificOutput']['permissionDecision'])
        self.assertIn('routing configuration could not be validated',
                      output['hookSpecificOutput']['permissionDecisionReason'])


class HostObservationTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory(); self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name); self.now=1800000000.0

    def observe(self, event):
        from route_evidence import host_observations
        host_observations.observe(event,self.root,clock=lambda: self.now)

    def summary(self):
        from route_evidence import host_observations
        return host_observations.summary(self.root,clock=lambda: self.now)

    def launch(self, tool, **supplied):
        return {'hook_event_name':'PreToolUse','tool_name':'Agent','session_id':'s','tool_use_id':tool,
                'tool_input':{'prompt':'x',**supplied}}

    def test_alias_resolution_and_applied_effort_in_either_order(self):
        background=self.launch('t1',model='sonnet',effort='xhigh')
        self.observe(background)
        self.observe({**background,'hook_event_name':'PostToolUse',
                      'tool_response':{'agentId':'a1','resolvedModel':'claude-sonnet-5-5'}})
        self.observe({'hook_event_name':'SubagentStop','session_id':'s','agent_id':'a1','effort':{'level':'high'}})
        foreground=self.launch('t2',model='haiku',effort='low')
        self.observe(foreground)
        self.observe({'hook_event_name':'SubagentStop','session_id':'s','agent_id':'a2','effort':{'level':'low'}})
        self.observe({**foreground,'hook_event_name':'PostToolUse',
                      'tool_response':json.dumps({'agentId':'a2','resolvedModel':'claude-haiku-5-5'})})
        result=self.summary()
        self.assertEqual({'sonnet':'claude-sonnet-5-5','haiku':'claude-haiku-5-5'},
                         {row['alias']:row['model'] for row in result['aliases']})
        self.assertEqual({('claude-sonnet-5-5','xhigh','high'),('claude-haiku-5-5','low','low')},
                         {(row['model'],row['requested'],row['applied']) for row in result['efforts']})

    def test_failures_forks_and_unrequested_settings_record_nothing(self):
        self.observe(self.launch('t0'))
        self.observe({'hook_event_name':'SubagentStop','session_id':'s','agent_id':'a0','effort':{'level':'max'}})
        self.assertFalse((self.root/'host-observations').exists())
        self.observe(self.launch('t1',model='opus',subagent_type='fork'))
        failed=self.launch('t2',model='opus',effort='low')
        self.observe(failed)
        self.observe({**failed,'hook_event_name':'PostToolUseFailure','tool_response':{'resolvedModel':'claude-opus-5-5'}})
        self.assertEqual({'aliases':[],'efforts':[]},self.summary())

    def test_observations_expire_instead_of_becoming_a_registry(self):
        from route_evidence import host_observations
        launch=self.launch('t1',model='opus')
        self.observe(launch)
        self.observe({**launch,'hook_event_name':'PostToolUse','tool_response':{'resolvedModel':'claude-opus-5-5'}})
        self.assertEqual(1,len(self.summary()['aliases']))
        self.now+=host_observations.KEEP_SECONDS+1
        self.assertEqual([],self.summary()['aliases'])

    def test_an_unavailable_store_is_reported_without_failing_routing(self):
        from route_evidence import host_observations
        from route_evidence.cache import Cache
        from route_evidence.service import RoutingService
        service=RoutingService(Cache(self.root),client='claude',clock=lambda: self.now)
        with patch.object(host_observations,'summary',side_effect=EvidenceError('pipeline_store_unavailable')):
            self.assertEqual('unavailable',service.host_observations()['status'])

    def test_hook_events_observe_launches_through_the_binding_and_the_service_reports_them(self):
        from route_evidence.cache import Cache
        from route_evidence.service import RoutingService
        config=self.root/'config.json'
        config.write_text(json.dumps({'schema_version':5,'client':'claude'}),encoding='utf-8')
        data=self.root/'plugin-data'; data.mkdir()
        (data/'routing.json').write_text(json.dumps({'config':str(config),'cache_dir':str(self.root)}),encoding='utf-8')
        env={'PLUGIN_DATA':str(data)}
        launch=self.launch('t1',model='fable',effort='medium')
        for event in (launch,{**launch,'hook_event_name':'PostToolUse',
                              'tool_response':{'agentId':'a1','resolvedModel':'claude-fable-5-1'}}):
            result,error=cli.process(event,'claude',env,clock=lambda: self.now)
            self.assertIsNone(error)
        service=RoutingService(Cache(self.root),client='claude',clock=lambda: self.now)
        self.assertEqual([('fable','claude-fable-5-1')],
                         [(row['alias'],row['model']) for row in service.host_observations()['aliases']])


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
        result=self.invoke(b'{"hook_event_name":"UserPromptSubmit","prompt":"Use code-change for SECRET_SENTINEL"}')
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
        with patch.object(cli, 'explicit_routes',return_value=denied), patch.object(cli,'load_rules',side_effect=RuntimeError('SECRET')):
            result,error=cli.process(event,'claude',{})
        self.assertEqual(denied,result); self.assertNotIn('SECRET',error)
        with patch.object(cli,'explicit_routes',return_value={}), patch.object(cli,'load_rules',side_effect=ImportError()):
            result,error=cli.process(event,'claude',{})
        self.assertEqual(cli.reminder(event, {}),result); self.assertTrue(error)

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
                   'transcript_path':'root','turn_id':'1','prompt':'Use code-change'}
            cli.process(event,'codex',env)
            result,error=cli.process({**event,'hook_event_name':'PostCompact'},'codex',env)
            self.assertEqual({},result); self.assertIsNone(error)
            pre={**event,'hook_event_name':'PreToolUse','tool_name':'spawn_agent','tool_use_id':'t'}
            result,error=cli.process(pre,'codex',env)
            context=result['hookSpecificOutput']['additionalContext']
            self.assertIn('route-subagents',context)
            self.assertIn('Previous request suggested code-change',context)
            self.assertLess(len(context),1000)

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
            # Missing evidence is not a successful configuration check.
            self.assertEqual(2,result.returncode,result.stderr)
            self.assertFalse(json.loads(result.stdout)['launch_verified'])


if __name__=='__main__':
    unittest.main()
