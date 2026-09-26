"""Regression probes for the designer handoff, not just its map's structure."""
from __future__ import annotations

import copy
from html.parser import HTMLParser
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from tools.test_product_flow_mapping import M, MapError, fixture, png


class HtmlInventory(HTMLParser):
    def __init__(self, source: str):
        super().__init__()
        self.ids: list[str] = []
        self.fragments: list[str] = []
        self.feed(source)

    def handle_starttag(self, tag: str, attrs) -> None:
        values = dict(attrs)
        if 'id' in values:
            self.ids.append(values['id'])
        if values.get('href', '').startswith('#'):
            self.fragments.append(values['href'][1:])


class ProductFlowReviewTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix='flow-review-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.map = fixture()

    def plan(self) -> dict:
        return M['handoff'](self.map, M['check'](self.map, self.root), {})

    def page(self) -> str:
        return M['render_html'](self.map, self.plan())

    def add_capture(self, rid='CAP_VIEW') -> None:
        import hashlib
        data = png()
        (self.root / 'screen.png').write_bytes(data)
        digest = hashlib.sha256(data).hexdigest()
        self.map['captures'] = [dict(
            id=rid, state_id='VIEW', file='screen.png', sha256=digest,
            width=16, height=8, scope='Synthetic fixture', source_revision='example-v1',
            readiness='Synthetic pixels ready', captured_at='2026-09-26T12:00:00Z',
            simulated=True, redaction='reviewed', evidence_ids=['CODE'], callouts=[
                dict(number=1, action_id='COPY', box=[0.1, 0.1, 0.2, 0.2], image_sha256=digest)])]
        self.map['scenarios'][1]['steps'][0]['capture_ids'] = [rid]

    def test_html_preserves_screen_state_and_action_explanations(self) -> None:
        self.map['screens'][0]['purpose'] = 'SCREEN_PURPOSE_SENTINEL'
        self.map['states'][0]['conditions'] = 'STATE_CONDITIONS_SENTINEL'
        self.map['actions'][0]['effect'] = 'ACTION_EFFECT_SENTINEL'
        self.map['actions'][0]['role'] = 'ACTION_ROLE_SENTINEL'
        page = self.page()
        for value in ('SCREEN_PURPOSE_SENTINEL', 'STATE_CONDITIONS_SENTINEL',
                      'ACTION_EFFECT_SENTINEL', 'ACTION_ROLE_SENTINEL'):
            with self.subTest(value=value):
                self.assertIn(value, page)

    def test_handoff_keeps_orphan_action_records_not_just_their_ids(self) -> None:
        unused = {**copy.deepcopy(self.map['actions'][0]), 'id': 'UNEXAMINED',
                  'label': 'Unexamined menu item', 'effect': 'Unknown effect; inspect its handler'}
        self.map['actions'].append(unused)
        plan = self.plan()
        self.assertIn(unused, plan['actions'])
        self.assertIn('Unknown effect; inspect its handler', M['render_html'](self.map, plan))
        self.assertTrue(any('UNEXAMINED' in gap for gap in plan['report']['recorded_gaps']))

    def test_composite_step_anchors_cannot_collide(self) -> None:
        # Both IDs are legal; naive joining produces step-FLOW-A-OPEN twice.
        a = copy.deepcopy(self.map['scenarios'][1])
        b = copy.deepcopy(a)
        a.update(id='FLOW-A', steps=[{**a['steps'][0], 'id': 'OPEN'}])
        b.update(id='FLOW', steps=[{**b['steps'][0], 'id': 'A-OPEN'}])
        self.map['scenarios'] += [a, b]
        parsed = HtmlInventory(self.page())
        self.assertEqual(len(parsed.ids), len(set(parsed.ids)))
        self.assertLessEqual(set(parsed.fragments), set(parsed.ids))

    def test_proposed_branch_is_not_a_current_flow_continuation(self) -> None:
        scenario = self.map['scenarios'][0]
        scenario['steps'][0].update(layer='observed', evidence_ids=['CODE'])
        scenario['steps'][2].update(layer='proposed', evidence_ids=['CODE'])
        plan = self.plan()
        opened = next(pair for pair in plan['pairs'] if pair['key'] == 'EDIT_FLOW/OPEN')
        self.assertEqual(opened['next_step_keys'], [])
        self.assertEqual(set(opened['related_step_keys']), {'EDIT_FLOW/ABANDON', 'EDIT_FLOW/COMMIT'})
        self.assertTrue(any('mixed claim layers' in gap for gap in plan['report']['recorded_gaps']))

    def test_same_layer_branches_remain_navigable(self) -> None:
        opened = next(pair for pair in self.plan()['pairs'] if pair['key'] == 'EDIT_FLOW/OPEN')
        self.assertEqual(set(opened['next_step_keys']), {'EDIT_FLOW/ABANDON', 'EDIT_FLOW/COMMIT'})
        self.assertEqual(opened['related_step_keys'], [])

    def test_capture_numbers_have_a_readable_action_legend(self) -> None:
        self.add_capture()
        plan = self.plan()
        pic = plan['pairs'][6]['right_frame']['captures'][0]
        self.assertEqual(pic['callouts'][0]['label'], 'Copy link')
        self.assertIn('Callouts', M['render_html'](self.map, plan))

    def test_same_state_capture_does_not_invent_temporal_evidence(self) -> None:
        self.add_capture()
        moment = self.plan()['pairs'][6]['right_frame']['captures'][0]['moment']
        self.assertIn('UNSPECIFIED', moment)
        self.assertNotIn('BEFORE', moment)

    def test_reserved_capture_id_uses_a_portable_output_filename(self) -> None:
        self.add_capture('CON')
        output = self.root / 'bundle'
        M['export'](self.map, self.root, output, {})
        saved = M['read_json'](output / 'map.json')
        self.assertNotEqual(Path(saved['captures'][0]['file']).stem.upper(), 'CON')
        self.assertTrue((output / saved['captures'][0]['file']).is_file())
        M['check'](saved, output)

    def test_export_preserves_a_file_created_during_publication(self) -> None:
        output = self.root / 'bundle'
        mkdir = Path.mkdir
        def concurrent_note(path, *args, **kwargs):
            result = mkdir(path, *args, **kwargs)
            if path == output:
                (output / 'notes.json').write_text('USER OWNED', encoding='utf-8')
            return result
        with mock.patch.object(Path, 'mkdir', concurrent_note):
            with self.assertRaises((OSError, MapError)):
                M['export'](self.map, self.root, output, {})
        self.assertEqual((output / 'notes.json').read_text(), 'USER OWNED')
        self.assertFalse((output / 'index.html').exists())
        self.assertFalse(list(self.root.glob('.flow-map-*')))

    def test_old_execution_revision_remains_a_gap_without_any_capture(self) -> None:
        self.map['evidence'].append(dict(id='OLD_RUN', kind='runtime', locator='prior trace',
            revision='example-v0', detail='The action ran only on the previous build.'))
        self.map['scenarios'][1]['steps'][0].update(layer='observed', verification='executed',
                                                  evidence_ids=['OLD_RUN'])
        report = M['check'](self.map, self.root)
        self.assertTrue(any('OLD_RUN' in gap and 'revision' in gap for gap in report['recorded_gaps']))

    def test_non_runtime_source_revision_is_not_forced_to_match_build(self) -> None:
        self.map['evidence'][0]['revision'] = 'adopted-contract-2019'
        report = M['check'](self.map, self.root)
        self.assertFalse(any('adopted-contract-2019' in gap for gap in report['recorded_gaps']))

    def test_diff_propagates_inventory_only_evidence(self) -> None:
        self.map['evidence'].append(dict(id='MENU_SPEC', kind='requirement',
            locator='menu contract', revision='v1', detail='Copy is allowed'))
        entry = next(x for x in self.map['inventory'] if x['target_id'] == 'COPY')
        entry['evidence_ids'] = ['MENU_SPEC']
        previous = copy.deepcopy(self.map)
        self.map['evidence'][-1]['detail'] = 'Copy now needs a permission check'
        diff = M['compare'](previous, self.map)
        self.assertTrue(diff['coverage_review_required'])
        self.assertEqual(diff['affected_scenarios'], ['EXPORT_FLOW'])

    def test_diff_of_excluded_inventory_source_still_requests_review(self) -> None:
        self.map['evidence'].append(dict(id='RETIREMENT', kind='requirement',
            locator='owner decision', revision='v1', detail='Reset retired'))
        self.map['inventory'].append(dict(id='INV_OLD', kind='action',
            evidence_ids=['RETIREMENT'], disposition='excluded', target_id='', reason='Reset retired'))
        previous = copy.deepcopy(self.map)
        self.map['evidence'][-1]['detail'] = 'Reset restored'
        diff = M['compare'](previous, self.map)
        self.assertTrue(diff['coverage_review_required'])

    def test_shared_control_can_keep_one_identity_on_two_screens(self) -> None:
        self.map['screens'].append(dict(id='RESULT', title='Result', purpose='Result detail'))
        self.map['states'].append(dict(id='RESULT_VIEW', screen_id='RESULT', title='Ready',
            conditions='Result opened', evidence_ids=['CODE']))
        action = next(item for item in self.map['actions'] if item['id'] == 'COPY')
        action['shared_screen_ids'] = ['RESULT']
        scenario = copy.deepcopy(self.map['scenarios'][1])
        scenario.update(id='RESULT_EXPORT', entry_state_ids=['RESULT_VIEW'], terminal_state_ids=['RESULT_VIEW'])
        scenario['steps'] = [{**scenario['steps'][0], 'before': 'RESULT_VIEW', 'after': 'RESULT_VIEW'}]
        self.map['scenarios'].append(scenario)
        plan = self.plan()
        self.assertEqual(plan['reverse_index']['actions']['COPY'], ['EXPORT_FLOW', 'RESULT_EXPORT'])
        self.assertEqual(sum(item['id'] == 'COPY' for item in plan['actions']), 1)
        # Callouts can refer to the same control on the secondary surface.
        self.add_capture()
        self.map['captures'][0]['state_id'] = 'RESULT_VIEW'
        self.map['scenarios'][1]['steps'][0]['capture_ids'] = []
        self.map['scenarios'][-1]['steps'][0]['capture_ids'] = ['CAP_VIEW']
        self.plan()

    def test_shared_control_cannot_claim_a_missing_or_duplicate_screen(self) -> None:
        action = next(item for item in self.map['actions'] if item['id'] == 'COPY')
        for screens in (['MISSING'], [action['screen_id']]):
            with self.subTest(screens=screens):
                action['shared_screen_ids'] = screens
                with self.assertRaises(MapError) as caught:
                    self.plan()
                self.assertEqual(caught.exception.code, 1)

    def test_every_declared_entry_needs_a_recorded_result_path(self) -> None:
        self.map['states'].append(dict(id='UNCONNECTED', screen_id='COLLECTION',
            title='Unconnected entry', conditions='Direct entry candidate', evidence_ids=['CODE']))
        self.map['scenarios'][0]['entry_state_ids'].append('UNCONNECTED')
        with self.assertRaises(MapError) as caught:
            self.plan()
        self.assertEqual(caught.exception.code, 1)
        self.assertIn('entry has no recorded terminal', str(caught.exception))
        self.map['scenarios'][0]['entry_state_ids'][-1] = 'DRAFT'
        self.plan()  # A second entry with a real path remains valid.

    def test_export_never_mutates_source_or_notes(self) -> None:
        self.add_capture()
        notes = {'EDIT_FLOW/OPEN': 'Owner text', 'OLD/STEP': 'Keep unmatched'}
        before = (copy.deepcopy(self.map), copy.deepcopy(notes))
        M['export'](self.map, self.root, self.root / 'bundle', notes)
        self.assertEqual((self.map, notes), before)


if __name__ == '__main__':
    unittest.main()
