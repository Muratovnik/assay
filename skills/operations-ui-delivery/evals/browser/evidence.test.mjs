import { test } from 'node:test';
import assert from 'node:assert/strict';
import { evidenceContext, scanAccessibility, triageFindings } from '../../assets/playwright/evidence.mjs';

const context = { build: 'abc', scenario: 'edit', state: 'error-open', data: 'synthetic' };
const finding = { kind: 'violation', rule: 'button-name', target: ['#save'] };
const waiver = { rule: 'button-name', target: ['#save'], scenario: 'edit', state: 'error-open',
  reason: 'Fixture deliberately demonstrates a broken control', expires: '2026-10-01' };
const report = (findings = [finding]) => ({ context, findings });
test('evidence requires build, scenario, state and dataset identity', () => {
  assert.deepEqual(evidenceContext(context), context);
  for (const key of Object.keys(context)) assert.throws(() => evidenceContext({ ...context, [key]: '' }), TypeError);
});
test('deduplicate the same rule/target but keep a different element', () => {
  const result = triageFindings(report([finding, finding, { ...finding, target: ['#delete'] }]), [], '2026-09-12');
  assert.equal(result.active.length, 2);
});
test('waivers cannot cross scenario, state, rule, target or expiry', () => {
  assert.equal(triageFindings(report(), [waiver], '2026-09-12').waived.length, 1);
  for (const patch of [{ scenario: 'other' }, { state: 'closed' }, { rule: 'image-alt' },
    { target: ['#other'] }, { expires: '2026-09-11' }]) {
    const result = triageFindings(report(), [{ ...waiver, ...patch }], '2026-09-12');
    assert.equal(result.active.length, 1); assert.equal(result.unusedWaivers.length, 1);
  }
});
test('missing reasons, broad scopes and invalid dates are refused', () => {
  for (const patch of [{ reason: '' }, { rule: '*' }, { target: ['*'] }, { target: [] },
    { expires: 'never' }, { expires: '2026-02-30' }]) {
    assert.throws(() => triageFindings(report(), [{ ...waiver, ...patch }], '2026-09-12'), TypeError);
  }
});
test('incomplete results never become clean through a waiver', () => {
  const result = triageFindings(report([{ ...finding, kind: 'needs-review' }]), [waiver], '2026-09-12');
  assert.equal(result.needsReview.length, 1); assert.equal(result.waived.length, 0);
});
test('unknown finding kinds and invalid observation dates fail closed', () => {
  assert.throws(() => triageFindings(report([{ ...finding, kind: 'clean' }])), TypeError);
  assert.throws(() => triageFindings(report(), [], '2026-02-30'), TypeError);
});
const page = { locator: () => ({ count: async () => 1, isVisible: async () => true }) };
const base = { context, scope: '#editor', rules: ['button-name'] };
test('adapter binds scope and rules; preserves incompletes and omits HTML', async () => {
  const calls = [];
  const builder = { include: (scope) => { calls.push(scope); return builder; },
    withRules: (rules) => { calls.push(rules); return builder; }, analyze: async () => ({
      testEngine: { name: 'stub' }, timestamp: 'synthetic',
      violations: [{ id: 'button-name', nodes: [{ target: ['#save'], html: 'SECRET' }] }],
      incomplete: [{ id: 'color-contrast', nodes: [{ target: ['#caption'] }] }],
    }) };
  const result = await scanAccessibility(page, { ...base, createBuilder: () => builder });
  assert.deepEqual(calls, ['#editor', ['button-name']]);
  assert.deepEqual(result.findings.map((f) => f.kind), ['violation', 'needs-review']);
  assert.equal(JSON.stringify(result).includes('SECRET'), false);
});
test('adapter propagates analyzer failure; invisible or missing scope is not a pass', async () => {
  const builder = { include: () => builder, withRules: () => builder,
    analyze: async () => { throw new Error('engine failed'); } };
  await assert.rejects(scanAccessibility(page, { ...base, createBuilder: () => builder }), /engine failed/);
  const invisible = { locator: () => ({ count: async () => 1, isVisible: async () => false }) };
  await assert.rejects(scanAccessibility(invisible, { ...base, createBuilder: () => builder }), /visible container/);
  await assert.rejects(scanAccessibility(page, { ...base, rules: [], createBuilder: () => builder }), /rule IDs/);
});
