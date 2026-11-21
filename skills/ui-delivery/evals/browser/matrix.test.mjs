import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { chromium } from 'playwright';
import { compareEdges, measureText } from '../../assets/playwright/layout.mjs';
import { parseMatrix, sweepMatrix } from '../../assets/playwright/matrix.mjs';

const read = (name) => readFile(new URL(name, import.meta.url), 'utf8');
const html = await read('./matrix-fixture.html');
const matrixText = await read('./matrix-fixture.json');
const matrix = parseMatrix(matrixText);
const executable = process.env.UI_TEST_CHROMIUM ? { executablePath: process.env.UI_TEST_CHROMIUM } : {};
const context = { build: 'synthetic-matrix', scenario: 'orders' };
let browser;
before(async () => { browser = await chromium.launch({ ...matrix.launch, ...executable }); });
after(async () => { await browser?.close(); });

// The product's declared measurements. A title is cut when measureText reports any clipping flag:
// with the default, a declared ellipsis that hides nothing is not one. Scrolled to its end, the list
// cuts the row half out of view by design, so that state checks the last row only, which must show.
const TITLES = Object.fromEntries([1, 2, 3, 4, 5, 6].map((n) => [`title${n}`, `#order-${n} .card-title`]));
const PANEL = { panelTitle: '#panel-title', period: '#label-period', status: '#label-status', owner: '#label-owner' };
const titlesCut = (targets, { shown = false } = {}) => async (page, cell) => {
  const measurement = await measureText(page, { context: cell, targets });
  const findings = [];
  for (const [name, target] of Object.entries(measurement.targets)) {
    if (Object.values(target.clipped).some(Boolean)) findings.push({ class: 'text-cut', kind: 'cut', targets: [name] });
    if (shown && !target.lines.length) findings.push({ class: 'text-cut', kind: 'not-shown', targets: [name] });
  }
  return { findings };
};
const measurements = {
  'titles-cut': titlesCut(TITLES),
  'last-title-cut': titlesCut({ title6: TITLES.title6 }, { shown: true }),
  'panel-edges': async (page, cell) => {
    const result = compareEdges(await measureText(page, { context: cell, targets: PANEL }),
      { groups: [Object.keys(PANEL)] });
    return { findings: result.findings.map(({ kind, targets }) => ({ class: 'panel-edge', kind, targets })) };
  },
};

async function withPage(run) {
  const session = await browser.newContext();
  try {
    const page = await session.newPage();
    page.setDefaultTimeout(3000);
    await run(page);
  } finally { await session.close(); }
}
const loader = (page, variant, loads = []) => async ({ width, state, data }) => {
  loads.push({ width, state, data });
  const { orders } = JSON.parse(await read(`./${data.path}`));
  await page.setContent(html.replace('<script>', `<script>window.fixture = ${JSON.stringify({ variant, orders })};`));
};
const cellsWith = (result) => result.cells.map(({ width, state, measured, findings }) => `${width} ${state} ${measured} ${findings}`);

test('Fault: a title cut only with the filters panel open at 900 px is found in that cell alone', () => withPage(async (page) => {
  const loads = [];
  const result = await sweepMatrix(page, { context, matrix: matrixText, load: loader(page, 'fault', loads), measurements });
  assert.equal(result.pass, false);
  assert.deepEqual(cellsWith(result), [
    '1280 default true 0', '1280 filters-open true 0', '1280 list-end true 0',
    '900 default true 0', '900 filters-open true 1', '900 list-end true 0',
  ]);
  assert.deepEqual(result.findings.map(({ width, state, measurement, targets, onlyInState }) =>
    ({ width, state, measurement, targets, onlyInState })),
  [{ width: 900, state: 'filters-open', measurement: 'titles-cut', targets: ['title2'], onlyInState: true }]);
  assert.equal(result.context.data, 'path:matrix-data.json', 'the data source is noted');
  assert.equal(loads.length, 6, 'every cell starts from a fresh load');
  assert.deepEqual(loads[0], { width: 1280, state: 'default', data: { path: 'matrix-data.json' } });
}));

test('Control: titles that wrap under a declared ellipsis pass in every cell', () => withPage(async (page) => {
  const result = await sweepMatrix(page, { context, matrix, load: loader(page, 'control'), measurements });
  assert.deepEqual(cellsWith(result), [
    '1280 default true 0', '1280 filters-open true 0', '1280 list-end true 0',
    '900 default true 0', '900 filters-open true 0', '900 list-end true 0',
  ]);
  assert.equal(result.pass, true);
  // Setup check: the panel state was really entered and the long title really wraps there.
  await loader(page, 'control')({ width: 900, state: 'filters-open', data: matrix.data });
  await page.setViewportSize({ width: 900, height: matrix.height });
  await page.locator('#open-panel').click();
  const { targets } = await measureText(page, { context: { ...context, state: 'filters-open', data: 'path' },
    targets: { title2: TITLES.title2 }, declared: true });
  assert.ok(targets.title2.lines.length >= 2, 'the long title wraps at 900 px with the panel open');
  assert.equal(targets.title2.declared.ellipsis, true, 'the ellipsis is declared but cuts nothing');
}));

test('The matrix launch shows the scrollbars that Playwright hides by default', async () => {
  const gutter = async (instance) => {
    const page = await instance.newPage();
    try {
      await loader(page, 'control')({ data: matrix.data });
      return await page.evaluate(() => {
        const list = document.querySelector('#order-list');
        return { scrolls: list.scrollHeight > list.clientHeight, gutter: list.offsetWidth - list.clientWidth };
      });
    } finally { await page.close(); }
  };
  const hidden = await chromium.launch(executable);
  try {
    const shown = await gutter(browser), concealed = await gutter(hidden);
    assert.equal(shown.scrolls && concealed.scrolls, true, 'setup: the list scrolls');
    assert.equal(concealed.gutter, 0, 'the default launch gives the scrollbar no width');
    assert.ok(shown.gutter > 0, 'the matrix launch paints a scrollbar with width');
  } finally { await hidden.close(); }
});

test('A state that cannot be entered is unmeasured, not a pass', () => withPage(async (page) => {
  const broken = { ...JSON.parse(matrixText), widths: [900],
    states: [{ name: 'menu', enter: [{ action: 'click', selector: '#no-such-menu' }] }] };
  const result = await sweepMatrix(page, { context, matrix: broken, load: loader(page, 'control'), measurements });
  assert.equal(result.pass, false);
  assert.deepEqual(result.unmeasured.map(({ width, state }) => ({ width, state })), [{ width: 900, state: 'menu' }]);
  assert.match(result.unmeasured[0].reason, /could not enter the state/);
  assert.deepEqual(cellsWith(result), ['900 default true 0', '900 menu false 0']);
}));

test('Malformed matrices are refused before anything runs', () => withPage(async (page) => {
  const valid = JSON.parse(matrixText);
  const refused = [
    { ...valid, launch: {} },
    { ...valid, launch: { ignoreDefaultArgs: ['--mute-audio'] } },
    { ...valid, widths: [] },
    { ...valid, widths: [900, 900] },
    { ...valid, data: {} },
    { ...valid, data: { path: 'a.json', command: 'seed' } },
    { ...valid, measure: [] },
    { ...valid, states: [{ name: 'default', enter: [] }] },
    { ...valid, states: [{ name: 'x', enter: [{ action: 'drag', selector: '#a' }] }] },
    { ...valid, states: [{ name: 'x', enter: [], widths: [390] }] },
  ];
  for (const input of refused) assert.throws(() => parseMatrix(input), TypeError, JSON.stringify(input));
  assert.deepEqual(parseMatrix({ ...valid, data: { command: 'npm run seed:worst' } }).data, { command: 'npm run seed:worst' });
  await assert.rejects(sweepMatrix(page, { context, matrix: valid, load: loader(page, 'control'),
    measurements: { 'titles-cut': measurements['titles-cut'] } }), /no measurement function named panel-edges/);
  await assert.rejects(sweepMatrix(page, { context: { build: 'b' }, matrix: valid, load: loader(page, 'control'),
    measurements }), TypeError);
}));
