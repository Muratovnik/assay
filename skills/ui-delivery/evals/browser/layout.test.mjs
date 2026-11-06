import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { chromium } from 'playwright';
import { measureText, compareEdges, compareRow, indicatorStyle, indicatorDiff } from '../../assets/playwright/layout.mjs';

const html = await readFile(new URL('./layout-fixture.html', import.meta.url), 'utf8');
const context = { build: 'synthetic-layout', scenario: 'layout', state: 'rendered', data: 'fixed-settings' };
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

const LIST = { heading: '#heading', theme: '#theme', units: '#units', contrast: '#contrast', more: '#more',
  digest: '#digest', digestBox: '#digest-box', quiet: '#quiet', folded: '#folded' };
const measureList = (page) => measureText(page, { context, targets: LIST });
// The fixture's policy: the section header, row labels and disclosure share one text edge;
// the contrast row is a declared sub-item, at least 16px in from its parent row.
const edgeRule = { groups: [['heading', 'theme', 'units', 'more']], offsets: [{ target: 'contrast', from: 'theme', min: 16 }] };
const edgeOracle = (measurement) => {
  const result = compareEdges(measurement, edgeRule);
  assert.ok(result.pass, result.findings.map((finding) => finding.detail).join('; '));
};
const rowOracle = (measurement) => {
  const result = compareRow(measurement, { control: 'digestBox', text: 'digest' });
  assert.ok(result.pass, result.detail);
};

test('Aligned list: shared edge, declared indent and first-line checkbox pass', () => withPage('list', 'good', async (page) => {
  const measurement = await measureList(page);
  edgeOracle(measurement);
  rowOracle(measurement);
  const { units, contrast, digest } = measurement.targets;
  assert.equal(units.lines.length, 1, 'screen-reader-only text adds no line');
  assert.ok(contrast.firstLine.x - measurement.targets.theme.firstLine.x >= 16);
  // Label and value of a row share one merged line box.
  assert.equal(contrast.lines.length, 1);
  // The label wraps, so passing compareRow shows it uses the first line, not the block center.
  assert.ok(digest.lines.length >= 2, 'the checkbox label wraps at this width');
}));

test('Fault control: a marker on one row type moves its text edge', () => withPage('list', 'marker', async (page) => {
  const measurement = await measureList(page);
  assert.throws(() => edgeOracle(measurement), { code: 'ERR_ASSERTION' });
  const [finding] = compareEdges(measurement, edgeRule).findings;
  assert.equal(finding.kind, 'edge');
  assert.ok(finding.targets.includes('units'));
  assert.ok(Math.max(...finding.values) - Math.min(...finding.values) >= 10);
}));

test('Fault control: a flattened sub-item loses its declared indentation', () => withPage('list', 'flat', async (page) => {
  const measurement = await measureList(page);
  assert.throws(() => edgeOracle(measurement), { code: 'ERR_ASSERTION' });
  assert.deepEqual(compareEdges(measurement, edgeRule).findings.map(({ kind, targets }) => ({ kind, targets })),
    [{ kind: 'offset', targets: ['contrast', 'theme'] }]);
}));

test('Fault control: a hit-area wrapper pushes the checkbox off the first line', () => withPage('list', 'hit-wrapper', async (page) => {
  const measurement = await measureList(page);
  assert.throws(() => rowOracle(measurement), { code: 'ERR_ASSERTION' });
  assert.ok(compareRow(measurement, { control: 'digestBox', text: 'digest' }).delta > 2, 'the box sits below the first line');
  edgeOracle(measurement);
}));

test('Hidden, transparent, screen-reader-only and collapsed text is missing, not a pass', () => withPage('list', 'good', async (page) => {
  const { targets } = await measureList(page);
  for (const name of ['quiet', 'folded']) {
    assert.deepEqual(targets[name].lines, [], name);
    assert.equal(targets[name].firstLine, null, name);
  }
  const result = compareEdges({ context, targets }, { groups: [['theme', 'quiet']] });
  assert.equal(result.pass, false);
  assert.deepEqual(result.findings.map(({ kind, targets }) => ({ kind, targets })), [{ kind: 'missing', targets: ['quiet'] }]);
  assert.equal(compareRow({ context, targets }, { control: 'digestBox', text: 'quiet' }).pass, false);
}));

const TEXT = { summary: '#summary' };
const fullyShown = (target) => {
  assert.equal(target.clipped.overflow, false, 'text is cut');
  assert.equal(target.clipped.ellipsis, false, 'text is truncated with an ellipsis');
  assert.equal(target.clipped.nowrap, false, 'text cannot wrap');
  assert.ok(target.lines.length >= 2, 'the summary wraps at this width');
};
test('Wrapped text inside a scrolling panel is fully shown', () => withPage('text', 'good', async (page) => {
  const measurement = await measureText(page, { context, targets: TEXT });
  fullyShown(measurement.targets.summary);
  assert.equal(await page.evaluate(() => {
    const panel = document.querySelector('#panel');
    return panel.scrollHeight > panel.clientHeight;
  }), true, 'the panel itself scrolls, so the check is about this text only');
}));

test('Fault control: nowrap with ellipsis is reported as truncated', () => withPage('text', 'ellipsis', async (page) => {
  const { targets: { summary } } = await measureText(page, { context, targets: TEXT });
  assert.throws(() => fullyShown(summary), { code: 'ERR_ASSERTION' });
  assert.deepEqual(summary.clipped, { overflow: true, ellipsis: true, nowrap: true, lineClamp: false });
  assert.equal(summary.lines.length, 1);
}));

test('Fault control: a short clipping parent cuts the wrapped text', () => withPage('text', 'cut', async (page) => {
  const { targets: { summary } } = await measureText(page, { context, targets: TEXT });
  assert.throws(() => fullyShown(summary), { code: 'ERR_ASSERTION' });
  assert.deepEqual(summary.clipped, { overflow: true, ellipsis: false, nowrap: false, lineClamp: false });
}));

// Real actions only: a mouse choice of the control, then a click on preceding text (which moves
// focus to the body and sets the sequential navigation start) and a real Tab.
async function indicatorRun(page) {
  const snapshot = () => indicatorStyle(page, { context, target: '#apply' });
  const initial = await snapshot();
  await page.locator('#apply').click();
  const pointer = await snapshot();
  await page.locator('#before').click();
  await page.keyboard.press('Tab');
  const keyboard = await snapshot();
  assert.equal(pointer.active, true, 'setup: the mouse choice focused the control');
  assert.equal(keyboard.active, true, 'setup: Tab reached the control');
  return { initial, pointer, keyboard };
}
const indicatorOracle = ({ initial, pointer, keyboard }) => {
  assert.notDeepEqual(indicatorDiff(initial, keyboard), [], 'keyboard focus shows no visible indicator');
  assert.deepEqual(indicatorDiff(initial, pointer), [], 'a pointer choice shows the keyboard indicator');
};
test('Indicator written for :focus-visible appears on Tab only', () => withPage('focus', 'visible-ring', async (page) => {
  const run = await indicatorRun(page);
  indicatorOracle(run);
  assert.equal(run.pointer.focusVisible, false);
  assert.equal(run.keyboard.focusVisible, true);
  assert.deepEqual(indicatorDiff(run.initial, run.keyboard).map((change) => change.property),
    ['outlineStyle', 'outlineWidth', 'outlineColor', 'outlineOffset']);
}));
for (const variant of ['any-focus', 'no-ring']) {
  test(`Fault control: indicator ${variant} fails the indicator assertion, not setup`, () => withPage('focus', variant, async (page) => {
    const run = await indicatorRun(page);
    assert.throws(() => indicatorOracle(run), { code: 'ERR_ASSERTION' });
  }));
}

test('Helpers do not move focus or scroll and return no page text', () => withPage('focus', 'visible-ring', async (page) => {
  await page.locator('#before').click();
  await page.keyboard.press('Tab');
  const state = () => page.evaluate(() => ({ active: document.activeElement.id,
    focusVisible: document.activeElement.matches(':focus-visible'), scroll: [scrollX, scrollY] }));
  const start = await state();
  assert.deepEqual(start, { active: 'apply', focusVisible: true, scroll: [0, 0] });
  const measurement = await measureText(page, { context, targets: { before: '#before', apply: '#apply', far: '#far' } });
  const snapshot = await indicatorStyle(page, { context, target: '#before' });
  assert.deepEqual(await state(), start);
  assert.ok(measurement.targets.far.rect.y > measurement.viewport.height, 'the far target stayed below the fold');
  assert.equal(snapshot.active, false);
}));

test('Returned objects contain no text from the page', async () => {
  const outputs = [];
  const strings = new Set();
  const collect = (page) => page.evaluate(() => {
    const found = [];
    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    for (let node = walker.nextNode(); node; node = walker.nextNode()) {
      if (node.parentElement.tagName !== 'SCRIPT' && node.parentElement.tagName !== 'STYLE' && node.data.trim()) found.push(node.data.trim());
    }
    return found;
  });
  await withPage('list', 'good', async (page) => {
    (await collect(page)).forEach((text) => strings.add(text));
    outputs.push(await measureList(page));
    outputs.push(await indicatorStyle(page, { context, target: '#more' }));
  });
  await withPage('text', 'ellipsis', async (page) => {
    (await collect(page)).forEach((text) => strings.add(text));
    outputs.push(await measureText(page, { context, targets: TEXT }));
  });
  assert.ok(strings.size >= 15, 'the search covers the fixture text');
  const json = JSON.stringify(outputs);
  for (const text of strings) assert.equal(json.includes(text), false, `returned data contains "${text}"`);
});

test('Missing or ambiguous selectors throw; malformed input is a TypeError', () => withPage('list', 'good', async (page) => {
  await assert.rejects(measureText(page, { context, targets: { absent: '#missing' } }), /Expected one target/);
  await assert.rejects(measureText(page, { context, targets: { rows: '.row' } }), /Expected one target/);
  await assert.rejects(indicatorStyle(page, { context, target: 'button, #heading' }), /Expected one target/);
  await assert.rejects(measureText(page, { context: { ...context, data: '' }, targets: LIST }), TypeError);
  await assert.rejects(measureText(page, { context, targets: {} }), TypeError);
  await assert.rejects(measureText(page, { context, targets: ['#theme'] }), TypeError);
  await assert.rejects(indicatorStyle(page, { context }), TypeError);
  const measurement = await measureList(page);
  assert.throws(() => compareEdges(measurement, { groups: [['theme', 'unknown']] }), TypeError);
  assert.throws(() => compareEdges(measurement, { groups: [['theme']] }), TypeError);
  assert.throws(() => compareEdges(measurement, { groups: [['theme', 'units']], tolerance: -1 }), TypeError);
  assert.throws(() => compareEdges(measurement, { groups: [['theme', 'units']], offsets: [{ target: 'contrast', from: 'theme' }] }), TypeError);
  assert.throws(() => compareEdges({ targets: measurement.targets }, { groups: [['theme', 'units']] }), TypeError);
  assert.throws(() => compareRow(measurement, { control: 'digestBox', text: 'nothing' }), TypeError);
  const one = await indicatorStyle(page, { context, target: '#more' });
  const other = await indicatorStyle(page, { context, target: '#heading' });
  assert.throws(() => indicatorDiff(one, other), TypeError);
  assert.throws(() => indicatorDiff(one, {}), TypeError);
}));
