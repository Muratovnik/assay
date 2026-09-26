import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { chromium } from 'playwright';
import { observeUi, observeUiSequence } from '../../assets/playwright/evidence.mjs';

const html = await readFile(new URL('./fixture.html', import.meta.url), 'utf8');
const context = { build: 'synthetic-fixture', scenario: 'fixture', state: 'after-action', data: 'fixed-A-B' };
let browser;
before(async () => {
  browser = await chromium.launch({
    ...(process.env.UI_TEST_CHROMIUM ? { executablePath: process.env.UI_TEST_CHROMIUM } : {}),
  });
});
after(async () => { await browser?.close(); });
async function withPage(scenario, variant, run) {
  const session = await browser.newContext({ viewport: { width: 900, height: 650 } });
  try {
    const page = await session.newPage();
    await page.setContent(html.replace('<script>', `<script>window.fixture = ${JSON.stringify({ scenario, variant })};`));
    page.setDefaultTimeout(5000);
    await run(page);
  } finally { await session.close(); }
}
const observe = (page, targets, regions) => observeUi(page, { context, targets, regions });

async function cancelOracle(page) {
  await page.getByRole('button', { name: 'Add connection' }).click();
  await page.getByRole('textbox', { name: 'Name' }).fill('Unsaved draft');
  const cancel = page.getByRole('button', { name: 'Cancel', exact: true });
  assert.equal(await cancel.count(), 1, 'The form needs a real Cancel, not whole-form Clear');
  await cancel.click();
  assert.equal(await page.locator('#card').isVisible(), true, 'Cancel must restore the replaced object');
  assert.equal(await page.locator('#editor').isVisible(), false, 'Cancel must leave the editor');
  assert.equal(await page.evaluate(() => document.activeElement.id), 'card');
  assert.equal(await page.evaluate(() => window.writes), 0);
  await page.getByRole('button', { name: 'Add connection' }).click();
  assert.equal(await page.locator('#name').inputValue(), '');
}
test('P9: Cancel restores the object, drops only draft, does not write', () => withPage('cancel', 'good', cancelOracle));
for (const variant of ['lost-object', 'clear-only']) {
  test(`P9 fault control: ${variant} fails the outcome assertion, not setup`, () =>
    withPage('cancel', variant, async (page) => assert.rejects(cancelOracle(page), { code: 'ERR_ASSERTION' })));
}
test('P9 valid control: inline Cancel can collapse to its trigger', () => withPage('cancel', 'inline', async (page) => {
  await page.locator('#add').click(); await page.locator('#name').fill('draft'); await page.locator('#cancel').click();
  assert.equal(await page.locator('#card').isVisible(), true);
  assert.equal(await page.evaluate(() => document.activeElement.id), 'add');
  assert.equal(await page.evaluate(() => window.writes), 0);
}));
for (const variant of ['empty-hidden', 'empty-disabled']) {
  test(`P9 empty-state policy control: ${variant}`, () => withPage('cancel', variant, async (page) => {
    assert.equal(await page.locator('#editor').isVisible(), true);
    assert.equal(await page.locator('#cancel').isVisible(), false);
    assert.equal(await page.locator('#add').isVisible(), variant === 'empty-disabled');
    await page.locator('#name').fill('First connection');
    await page.getByRole('button', { name: 'Save', exact: true }).click();
    assert.equal(await page.evaluate(() => window.writes), 1);
  }));
}
const revealOracle = (observation) => {
  assert.equal(observation.targets.editor.viewportIntersection, 1, 'editor must be in viewport before another click');
  assert.equal(observation.targets.editor.focused, true, 'application must focus the editor');
};
for (const variant of ['good', 'silent']) {
  test(`C17 Add/reveal: ${variant}`, () => withPage('add', variant, async (page) => {
    await page.locator('#add').click();
    const result = await observe(page, { editor: '#name' });
    if (variant === 'good') revealOracle(result);
    else {
      assert.throws(() => revealOracle(result), { code: 'ERR_ASSERTION' });
      // This later click repairs the viewport. The earlier failure must remain evidence.
      await page.locator('#name').click();
      assert.equal((await observe(page, { editor: '#name' })).targets.editor.viewportIntersection, 1);
    }
  }));
}
test('C18 valid control: explicit feedback preserves position until requested', () => withPage('add', 'feedback', async (page) => {
  await page.locator('#add').click();
  const before = await observe(page, { editor: '#name', trigger: '#add' });
  assert.equal(before.scroll.y, 0); assert.equal(before.targets.editor.viewportIntersection, 0);
  assert.equal(await page.locator('#feedback').isVisible(), true);
  await page.keyboard.press('Tab');
  assert.equal(await page.evaluate(() => document.activeElement.id), 'open');
  await page.keyboard.press('Enter'); revealOracle(await observe(page, { editor: '#name' }));
}));
const pointerOracle = (result) => assert.equal(result.targets.save.hits.every((p) => p.receivesPointer), true);
for (const variant of ['good', 'blocked']) {
  test(`P3 supporting panel: ${variant}`, () => withPage('panel', variant, async (page) => {
    await page.locator('#open').click();
    const result = await observe(page, { save: '#save' });
    if (variant === 'blocked') assert.throws(() => pointerOracle(result), { code: 'ERR_ASSERTION' });
    else {
      pointerOracle(result);
      await page.getByRole('button', { name: 'Save document' }).click();
      assert.equal(await page.evaluate(() => window.writes), 1);
      assert.equal(await page.locator('#panel').isVisible(), true);
    }
  }));
}
test('P3 parent completion by real Tab/Enter with panel open', () => withPage('panel', 'good', async (page) => {
  await page.locator('#open').click(); await page.keyboard.press('Tab');
  assert.equal(await page.evaluate(() => document.activeElement.id), 'save');
  await page.keyboard.press('Enter'); assert.equal(await page.evaluate(() => window.writes), 1);
  assert.equal(await page.locator('#panel').isVisible(), true);
}));
for (const variant of ['good', 'late-response']) {
  test(`P1 target-switch variant rejects an obsolete response: ${variant}`, () => withPage('async', variant, async (page) => {
    // A local fake service controls response order; it does not inject rendered state.
    await page.locator('#a').click(); await page.locator('#b').click();
    assert.deepEqual(await page.evaluate(() => Object.keys(window.pending)), ['A', 'B']);
    await page.evaluate(() => window.pending.B({ label: 'Result B' }));
    await page.waitForFunction(() => document.querySelector('#result').textContent === 'Result B');
    await page.evaluate(() => window.pending.A({ label: 'Result A' }));
    await page.waitForFunction(() => window.lastCompleted === 'A');
    assert.equal(await page.locator('#identity').textContent(), 'B');
    const check = () => assert.equal(result, 'Result B', 'old result must not be attributed to B');
    const result = await page.locator('#result').textContent();
    if (variant === 'good') check(); else assert.throws(check, { code: 'ERR_ASSERTION' });
  }));
}
for (const variant of ['good', 'bad']) {
  test(`P3 container transition at fixed viewport: ${variant}`, () => withPage('container', variant, async (page) => {
    await page.locator('#name').fill('Retained draft'); await page.locator('#toggle').click();
    const result = await observe(page, { field: '#name', save: '#save' }, { form: '#form-space' });
    assert.equal(result.viewport.width, 900); assert.equal(await page.locator('#name').inputValue(), 'Retained draft');
    const check = () => assert.ok(result.targets.save.rect.y >= result.targets.field.rect.y + result.targets.field.rect.height,
      'this fixture requires the compact stacked arrangement');
    if (variant === 'bad') assert.throws(check, { code: 'ERR_ASSERTION' });
    else { check(); await page.locator('#save').click(); assert.equal(await page.evaluate(() => window.writes), 1); }
    await page.locator('#toggle').click(); assert.equal(await page.locator('#name').inputValue(), 'Retained draft');
  }));
}
test('Observation is non-mutating; missing and ambiguous targets fail explicitly', () => withPage('cancel', 'good', async (page) => {
  await page.locator('#add').click(); await page.locator('#name').fill('secret draft');
  const a = await observe(page, { editor: '#name' }); const b = await observe(page, { editor: '#name' });
  assert.deepEqual(a.scroll, b.scroll); assert.equal(b.targets.editor.focused, true);
  assert.equal(JSON.stringify(b).includes('secret draft'), false);
  await assert.rejects(observe(page, { absent: '#missing' }), /Expected one target/);
  await assert.rejects(observe(page, { ambiguous: 'button' }), /Expected one target/);
}));

test('P3 valid control: genuine modal prerequisite suspends parent action', () => withPage('panel', 'modal', async (page) => {
  await page.locator('#open').click();
  const covered = await observe(page, { save: '#save' });
  assert.equal(covered.targets.save.hits.some((p) => p.receivesPointer), false);
  assert.equal(await page.evaluate(() => window.writes), 0);
  await page.getByRole('button', { name: 'Back', exact: true }).click();
  assert.equal(await page.evaluate(() => document.activeElement.id), 'open');
  await page.keyboard.press('Tab'); await page.keyboard.press('Enter');
  assert.equal(await page.evaluate(() => window.writes), 1);
}));
test('bounded observations retain provenance and do not alter focus or input', () => withPage('cancel', 'good', async (page) => {
  await page.locator('#add').click(); await page.locator('#name').fill('draft');
  const samples = await observeUiSequence(page, { context, targets: { editor: '#name' } }, 3);
  assert.equal(samples.length, 3);
  assert.ok(samples.every((s) => s.context.build === context.build && s.targets.editor.focused));
  assert.equal(await page.locator('#name').inputValue(), 'draft');
  await assert.rejects(observeUiSequence(page, {}, 0), /samples/);
}));
