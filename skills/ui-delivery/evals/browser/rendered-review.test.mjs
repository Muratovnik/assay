// Self-test of the evaluator-only rendered-review oracle: every defect check
// must fail on the shipped screen with an outcome assertion (not a locator or
// timeout error), every control must pass there, and every check must pass
// once the reference fixes are applied. Each fix alone must clear only its own
// check, so a check cannot pass because of another defect's repair.
import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { CASES, launchBrowser, runCheck } from './rendered-review-oracle.mjs';
import { REFERENCE_FIXES, materialize } from './rendered-review-fixes.mjs';

let browser;
let root;
before(async () => {
  browser = await launchBrowser();
  root = await mkdtemp(join(tmpdir(), 'rendered-review-'));
});
after(async () => {
  await browser?.close();
  if (root) await rm(root, { recursive: true, force: true });
});

async function screen(caseId, fixes) {
  return materialize(caseId, await mkdtemp(join(root, `${caseId}-`)), fixes);
}

const failsOnOutcome = (caseId, check, dir) =>
  assert.rejects(runCheck(browser, caseId, check, dir), { code: 'ERR_ASSERTION' },
    `${caseId}/${check} must fail its outcome assertion`);

test('reference fixes cover exactly the defect checks', () => {
  for (const [caseId, checks] of Object.entries(CASES)) {
    const defects = checks.filter(({ kind }) => kind === 'defect').map(({ check }) => check).sort();
    assert.deepEqual(Object.keys(REFERENCE_FIXES[caseId]).sort(), defects, caseId);
  }
});

for (const [caseId, checks] of Object.entries(CASES)) {
  const defects = checks.filter(({ kind }) => kind === 'defect').map(({ check }) => check);

  for (const { check, kind } of checks) {
    test(`${caseId} shipped: ${check} (${kind}) ${kind === 'defect' ? 'fails' : 'passes'}`, async () => {
      const dir = await screen(caseId, []);
      if (kind === 'defect') await failsOnOutcome(caseId, check, dir);
      else await runCheck(browser, caseId, check, dir);
    });
  }

  test(`${caseId} reference-fixed: every check passes`, async () => {
    const dir = await screen(caseId, defects);
    for (const { check } of checks) await runCheck(browser, caseId, check, dir);
  });

  for (const fixed of defects) {
    test(`${caseId} fix for ${fixed} alone clears only ${fixed}`, async () => {
      const dir = await screen(caseId, [fixed]);
      await runCheck(browser, caseId, fixed, dir);
      for (const other of defects.filter((check) => check !== fixed)) await failsOnOutcome(caseId, other, dir);
    });
  }
}
