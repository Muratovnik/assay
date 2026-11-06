// Evaluator-only browser oracle for rendered-review-cases.json. Never place this
// file, the reference fixes or the rubric in an executor's directory.
//
//   node rendered-review-oracle.mjs --case RR1 --dir <directory with index.html>
//
// Prints {"case": ..., "results": [{check, kind, status, detail}]} and exits 0
// whenever it produced results; 2 when it could not run at all. A check is
// "fail" when a geometric or behavioral expectation is refuted and
// "inconclusive" when the elements it needs cannot be located (or an
// unexpected browser error stopped it, named in detail).
//
// Locators use visible text, roles and accessible names only, never class
// names or ids, so a restructured screen is still measured:
// - text positions come from Range client rects of the first character of a
//   visible text node matching a fixed anchor (the line box, not the element);
// - a "visible" text node has a parent that passes checkVisibility with
//   opacity and visibility and is not clipped away by an overflow/clip
//   ancestor;
// - line boxes of a block are the Range client rects of all its visible text,
//   merged by vertical overlap.
import assert from 'node:assert/strict';
import { access } from 'node:fs/promises';
import { join, resolve } from 'node:path';
import { pathToFileURL, fileURLToPath } from 'node:url';
import { chromium } from 'playwright';

export class Inconclusive extends Error {
  constructor(message) {
    super(message);
    this.name = 'Inconclusive';
    this.code = 'ERR_INCONCLUSIVE';
  }
}

const VIEWPORTS = { 1280: { width: 1280, height: 800 }, 390: { width: 390, height: 844 } };
const CLOCK_START = new Date('2026-11-06T09:00:00Z');

export function launchBrowser() {
  return chromium.launch({
    ...(process.env.UI_TEST_CHROMIUM ? { executablePath: process.env.UI_TEST_CHROMIUM } : {}),
  });
}

// In-page helpers, installed before the screen's own scripts.
function installProbe() {
  const TEXT_SKIP = new Set(['SCRIPT', 'STYLE', 'TEMPLATE', 'NOSCRIPT', 'TITLE']);
  function shownElement(element) {
    if (!element.checkVisibility({ opacityProperty: true, visibilityProperty: true })) return false;
    const box = element.getBoundingClientRect();
    return box.width > 0 && box.height > 0;
  }
  function clippedAway(rect, node) {
    for (let element = node.parentElement; element && element !== document.documentElement; element = element.parentElement) {
      const style = getComputedStyle(element);
      const clips = style.overflowX !== 'visible' || style.overflowY !== 'visible'
        || style.clip !== 'auto' || style.clipPath !== 'none';
      if (!clips) continue;
      const box = element.getBoundingClientRect();
      const width = Math.min(rect.right, box.right) - Math.max(rect.left, box.left);
      const height = Math.min(rect.bottom, box.bottom) - Math.max(rect.top, box.top);
      if (width < 1 || height < 1 || box.width <= 2 || box.height <= 2) return true;
    }
    return false;
  }
  function visibleTextNodes(root) {
    const nodes = [];
    const walker = document.createTreeWalker(root || document.body, NodeFilter.SHOW_TEXT);
    for (let node = walker.nextNode(); node; node = walker.nextNode()) {
      const parent = node.parentElement;
      if (!node.data.trim() || !parent || TEXT_SKIP.has(parent.tagName) || !shownElement(parent)) continue;
      nodes.push(node);
    }
    return nodes;
  }
  function plain(rect) {
    return { left: rect.left, right: rect.right, top: rect.top, bottom: rect.bottom, width: rect.width, height: rect.height };
  }
  function charRect(node, index) {
    const range = document.createRange();
    range.setStart(node, index);
    range.setEnd(node, index + 1);
    const rects = Array.from(range.getClientRects()).filter((rect) => rect.width > 0.5 && rect.height > 0.5);
    if (!rects.length || clippedAway(rects[0], node)) return null;
    return plain(rects[0]);
  }
  // Every visible occurrence of a pattern inside single text nodes.
  function find(source, flags) {
    const matches = [];
    for (const node of visibleTextNodes()) {
      const pattern = new RegExp(source, (flags || '').replace('g', '') + 'g');
      for (let match = pattern.exec(node.data); match; match = pattern.exec(node.data)) {
        const offset = match[0].search(/\S/);
        const rect = charRect(node, match.index + Math.max(offset, 0));
        if (rect) matches.push({ text: match[0], ...rect });
        if (!match[0].length) pattern.lastIndex += 1;
      }
    }
    return matches;
  }
  function lineBoxes(root) {
    const lines = [];
    for (const node of visibleTextNodes(root)) {
      const start = node.data.search(/\S/);
      const end = node.data.length - (node.data.length - node.data.trimEnd().length);
      const range = document.createRange();
      range.setStart(node, start);
      range.setEnd(node, end);
      for (const rect of range.getClientRects()) {
        if (rect.width <= 0.5 || rect.height <= 0.5 || clippedAway(rect, node)) continue;
        const middle = (rect.top + rect.bottom) / 2;
        const line = lines.find((item) => middle > item.top && middle < item.bottom);
        if (line) {
          line.left = Math.min(line.left, rect.left);
          line.right = Math.max(line.right, rect.right);
          line.top = Math.min(line.top, rect.top);
          line.bottom = Math.max(line.bottom, rect.bottom);
        } else lines.push(plain(rect));
      }
    }
    return lines.sort((a, b) => a.top - b.top);
  }
  // The innermost element that holds a block of text from its first to its
  // last anchor; null when the first anchor is absent or ambiguous.
  function block(firstSource, lastText) {
    const hits = visibleTextNodes().filter((node) => new RegExp(firstSource).test(node.data));
    if (hits.length !== 1) return null;
    let element = hits[0].parentElement;
    const normal = (text) => text.replace(/[\s ]+/g, ' ');
    while (element && !normal(element.textContent).includes(lastText)) element = element.parentElement;
    return element;
  }
  function blockReport(firstSource, lastText) {
    const element = block(firstSource, lastText);
    if (!element) return null;
    const clipping = [];
    for (let node = element; node && node !== document.body; node = node.parentElement) {
      const style = getComputedStyle(node);
      const hidesOverflow = style.overflowX !== 'visible' || style.overflowY !== 'visible';
      if (hidesOverflow && (node.scrollWidth > node.clientWidth + 1 || node.scrollHeight > node.clientHeight + 1)) {
        clipping.push(`${node.tagName.toLowerCase()} clips overflow (${node.scrollWidth}x${node.scrollHeight} in ${node.clientWidth}x${node.clientHeight})`);
      }
      if (node === element || element.contains(node)) {
        if (style.textOverflow === 'ellipsis') clipping.push('text-overflow: ellipsis');
        if (/nowrap|^pre$/.test(style.whiteSpace) || style.textWrapMode === 'nowrap') clipping.push(`white-space: ${style.whiteSpace}`);
        if (style.webkitLineClamp && style.webkitLineClamp !== 'none') clipping.push(`line-clamp: ${style.webkitLineClamp}`);
      }
    }
    for (const inner of element.querySelectorAll('*')) {
      const style = getComputedStyle(inner);
      if (style.textOverflow === 'ellipsis' && style.overflowX !== 'visible') clipping.push('inner text-overflow: ellipsis');
      if (/nowrap/.test(style.whiteSpace) && inner.textContent.trim()) clipping.push(`inner white-space: ${style.whiteSpace}`);
    }
    return { lines: lineBoxes(element), clipping };
  }
  // A checkbox's painted box and the first line of its label text.
  function checkboxGeometry(control) {
    let row = control;
    while (row && !visibleTextNodes(row).length) row = row.parentElement;
    if (!row) return null;
    const text = visibleTextNodes(row).find((node) => !control.contains(node)) || visibleTextNodes(row)[0];
    if (!text) return null;
    const first = text.data.search(/\S/);
    const glyph = charRect(text, first);
    if (!glyph) return null;
    const paints = (element) => {
      const style = getComputedStyle(element);
      if (element.tagName === 'INPUT') return style.appearance !== 'none' || parseFloat(style.borderTopWidth) > 0;
      if (element.tagName === 'svg' || element.tagName === 'IMG') return true;
      const visibleColor = (value) => !/rgba\([^)]*,\s*0\)|transparent/.test(value);
      return (parseFloat(style.borderTopWidth) > 0 && visibleColor(style.borderTopColor))
        || visibleColor(style.backgroundColor) || style.backgroundImage !== 'none';
    };
    const candidates = [control, ...row.querySelectorAll('*')].filter((element) => {
      if (element.contains(text) && element !== control) return false;
      if (!shownElement(element)) return false;
      const box = element.getBoundingClientRect();
      return box.width >= 10 && box.width <= 32 && box.height >= 10 && box.height <= 32 && paints(element);
    });
    if (!candidates.length) return { text: text.data.trim(), textCenter: (glyph.top + glyph.bottom) / 2, box: null };
    const box = candidates
      .map((element) => element.getBoundingClientRect())
      .sort((a, b) => b.width * b.height - a.width * a.height)[0];
    return {
      text: text.data.trim(),
      textCenter: (glyph.top + glyph.bottom) / 2,
      box: plain(box),
      boxCenter: (box.top + box.bottom) / 2,
    };
  }
  function focusStyle(element) {
    const style = getComputedStyle(element);
    return {
      outline: `${style.outlineStyle} ${style.outlineWidth} ${style.outlineColor} ${style.outlineOffset}`,
      boxShadow: style.boxShadow,
      border: `${style.borderTopColor} ${style.borderRightColor} ${style.borderBottomColor} ${style.borderLeftColor} ${style.borderTopWidth}`,
      background: `${style.backgroundColor} ${style.backgroundImage}`,
    };
  }
  window.__renderedReviewProbe = { find, lineBoxes, blockReport, checkboxGeometry, focusStyle };
}

// Records calls to the simulated server so a refresh can be told from a pause.
function installServerProbe() {
  let api;
  window.__renderedReviewCalls = [];
  try {
    Object.defineProperty(window, 'requestsApi', {
      configurable: true,
      enumerable: true,
      get() { return api; },
      set(value) {
        if (value && typeof value.fetchSite === 'function') {
          const original = value.fetchSite;
          value.fetchSite = function (...args) {
            window.__renderedReviewCalls.push({ site: args[0], at: Date.now() });
            return original.apply(this, args);
          };
        }
        api = value;
      },
    });
  } catch { /* the screen defines the API differently; calls stay unobserved */ }
}

async function withPage(browser, dir, width, run, { clock = false } = {}) {
  const context = await browser.newContext({ viewport: VIEWPORTS[width], reducedMotion: 'reduce' });
  try {
    const page = await context.newPage();
    page.setDefaultTimeout(3000);
    await page.addInitScript(installProbe);
    if (clock) {
      await page.addInitScript(installServerProbe);
      await page.clock.install({ time: CLOCK_START });
    }
    await page.goto(pathToFileURL(join(dir, 'index.html')).href);
    await page.evaluate(() => document.fonts.ready.then(() => true));
    if (clock) {
      const now = await page.evaluate(() => Date.now());
      await page.clock.pauseAt(now + 50);
    }
    return await run(page);
  } finally {
    await context.close();
  }
}

const escape = (text) => text.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
const round = (value) => Math.round(value * 10) / 10;
const find = (page, source, flags = '') =>
  page.evaluate(([s, f]) => window.__renderedReviewProbe.find(s, f), [source, flags]);

async function one(page, source, label) {
  const matches = await find(page, source);
  if (matches.length !== 1) throw new Inconclusive(`${label}: expected one visible occurrence, found ${matches.length}`);
  return matches[0];
}

// RR1 — request list.
const RR1_HEADERS = ['Корпус\\s+А', 'Корпус\\s+Б'];
const RR1_TITLES = [
  'Протечка под раковиной в санузле, 2 этаж',
  'Не закрывается дверь на лестничную клетку',
  'Плановый осмотр вентиляции на кровле',
  'Шумит насос в тепловом пункте',
  'Заменить ламели жалюзи в переговорной 305',
  'Не работает домофон у центрального входа',
  'Течёт кран в комнате отдыха, 1 этаж',
  'Сломан доводчик на двери склада',
  'Мигает свет на парковке, уровень −1',
  'Проверить пожарные датчики в серверной',
];
const RR1_PARENT = 'Плановый осмотр вентиляции на кровле';
const RR1_SUBTASKS = ['Проверить крепление вентиляторов', 'Очистить решётки воздухозаборников'];

async function rr1Edges(browser, dir) {
  const notes = [];
  for (const width of [1280, 390]) {
    await withPage(browser, dir, width, async (page) => {
      const headers = [];
      for (const source of RR1_HEADERS) headers.push((await one(page, source, 'section header')).left);
      const disclosure = (await one(page, 'Архив', 'archive disclosure')).left;
      const titles = [];
      for (const title of RR1_TITLES) titles.push((await one(page, escape(title), 'request title')).left);
      const edge = headers[0];
      assert.ok(Math.abs(headers[1] - edge) <= 1, `${width}px: section headers start at ${round(edge)} and ${round(headers[1])}`);
      assert.ok(Math.abs(disclosure - edge) <= 1,
        `${width}px: archive label starts at ${round(disclosure)}, section header label at ${round(edge)}`);
      for (const [index, left] of titles.entries()) {
        assert.ok(Math.abs(left - edge) <= 1 || left >= edge + 12,
          `${width}px: request title "${RR1_TITLES[index]}" starts at ${round(left)}, header label at ${round(edge)}`);
      }
      notes.push(`${width}px header ${round(edge)}, archive ${round(disclosure)}, titles ${round(Math.min(...titles))}`);
    });
  }
  return notes.join('; ');
}

async function rr1Defaults(browser, dir) {
  return withPage(browser, dir, 1280, async (page) => {
    const priority = (await find(page, 'обычн', 'i')).length;
    const status = (await find(page, 'можно\\s+брать', 'i')).length;
    const anchors = [];
    for (const source of [...RR1_HEADERS, 'Архив']) anchors.push(await one(page, source, 'list anchor'));
    const titles = {};
    for (const title of RR1_TITLES) titles[title] = await one(page, escape(title), 'request title');
    anchors.push(...Object.values(titles));
    const inRow = async (title, source, label) => {
      const start = titles[title];
      const next = anchors.filter((anchor) => anchor.top > start.top + 1).sort((a, b) => a.top - b.top)[0];
      const values = await find(page, source, 'i');
      const placed = values.some((value) => {
        const middle = (value.top + value.bottom) / 2;
        return middle >= start.top - start.height && (!next || middle < next.top);
      });
      assert.ok(placed, `${label} is not visible on the row of "${title}" (${values.length} visible occurrence(s) elsewhere)`);
    };
    assert.ok(priority <= 1, `the default priority wording is visible ${priority} times`);
    assert.ok(status <= 1, `the default status wording is visible ${status} times`);
    await inRow('Не закрывается дверь на лестничную клетку', 'высок', 'the high priority');
    await inRow('Не работает домофон у центрального входа', 'жд[её]т\\s+детал', 'the waiting-for-parts status');
    return `default priority shown ${priority}x, default status shown ${status}x; exceptions on their rows`;
  });
}

async function rr1Tree(browser, dir) {
  const notes = [];
  for (const width of [1280, 390]) {
    await withPage(browser, dir, width, async (page) => {
      const parent = (await one(page, escape(RR1_PARENT), 'parent request')).left;
      for (const subtask of RR1_SUBTASKS) {
        const left = (await one(page, escape(subtask), 'sub-task')).left;
        assert.ok(left >= parent + 12, `${width}px: sub-task "${subtask}" starts at ${round(left)}, parent title at ${round(parent)}`);
        notes.push(`${width}px +${round(left - parent)}`);
      }
    });
  }
  return `sub-task indent ${notes.join(', ')}`;
}

// RR2 — request detail card.
const RR2_TITLE = ['Замена фильтров', 'техническом помещении'];
const RR2_DETAILS = ['Корпус\\s+А', 'срок 8 ноября'];
const RR2_DESCRIPTION = ['Приточная установка', 'этой же заявки'];

async function blockLines(page, [first, last], label) {
  const report = await page.evaluate(([f, l]) => window.__renderedReviewProbe.blockReport(f, l), [first, last]);
  if (!report || !report.lines.length) throw new Inconclusive(`${label}: text block not found`);
  return report;
}

async function rr2MetaWrap(browser, dir) {
  return withPage(browser, dir, 390, async (page) => {
    const title = await blockLines(page, RR2_TITLE, 'title');
    const details = await blockLines(page, RR2_DETAILS, 'details line');
    const column = title.lines[0].left;
    for (const [index, line] of details.lines.entries()) {
      assert.ok(line.left >= column - 1,
        `390px: details line ${index + 1} starts at ${round(line.left)}, title column at ${round(column)}`);
    }
    return `390px: ${details.lines.length} details line(s) start at ${details.lines.map((line) => round(line.left)).join(', ')}; title at ${round(column)}`;
  });
}

async function rr2TextWrap(browser, dir) {
  return withPage(browser, dir, 390, async (page) => {
    const notes = [];
    for (const [anchors, label] of [[RR2_TITLE, 'title'], [RR2_DESCRIPTION, 'description']]) {
      const { lines, clipping } = await blockLines(page, anchors, label);
      assert.ok(lines.length >= 2, `390px: ${label} occupies ${lines.length} line`);
      for (const [index, line] of lines.entries()) {
        assert.ok(Math.abs(line.left - lines[0].left) <= 1,
          `390px: ${label} line ${index + 1} starts at ${round(line.left)}, first line at ${round(lines[0].left)}`);
      }
      assert.ok(!clipping.length, `390px: ${label} is clipped (${clipping.join('; ')})`);
      notes.push(`${label} ${lines.length} lines`);
    }
    return `390px: ${notes.join(', ')}, no clipping`;
  });
}

async function rr2Checkbox(browser, dir) {
  const notes = [];
  for (const width of [1280, 390]) {
    await withPage(browser, dir, width, async (page) => {
      const controls = await page.getByRole('checkbox').elementHandles();
      if (controls.length !== 4) throw new Inconclusive(`${width}px: expected 4 checkboxes, found ${controls.length}`);
      for (const control of controls) {
        const geometry = await control.evaluate((element) => window.__renderedReviewProbe.checkboxGeometry(element));
        if (!geometry) throw new Inconclusive(`${width}px: a checkbox has no visible label text`);
        if (!geometry.box) throw new Inconclusive(`${width}px: no painted box found for "${geometry.text}"`);
        const offset = geometry.boxCenter - geometry.textCenter;
        assert.ok(Math.abs(offset) <= 2,
          `${width}px: box center is ${round(offset)} px from the first text line center for "${geometry.text}"`);
        notes.push(round(offset));
      }
    });
  }
  return `box-to-first-line offsets ${notes.join(', ')}`;
}

// RR3 — requests of a site.
const RR3_TITLES = {
  north: [
    'Заменить уплотнитель на воротах гаража',
    'Прочистить ливнёвку у въезда',
    'Отрегулировать доводчик в тамбуре',
    'Закрепить отходящий плинтус в коридоре',
    'Поменять лампы в подсобке',
  ],
  south: [
    'Починить кодовый замок калитки',
    'Убрать наледь с козырька',
    'Проверить давление в системе отопления',
    'Заменить смеситель в душевой',
    'Подтянуть крепление поручня на лестнице',
  ],
};

async function visibleTitles(page, titles) {
  const shown = [];
  for (const title of titles) if ((await find(page, escape(title))).length) shown.push(title);
  return shown;
}

async function siteTrigger(page) {
  for (const role of ['button', 'combobox']) {
    const locator = page.getByRole(role, { name: /Участок/ });
    if (await locator.count() === 1) return locator;
  }
  throw new Inconclusive('site trigger (button or combobox named "Участок") not found');
}

async function settle(page) {
  await page.clock.runFor(1000);
  const shown = await visibleTitles(page, RR3_TITLES.north);
  assert.ok(shown.length === RR3_TITLES.north.length, `initial list shows ${shown.length} of 5 requests after 1 s`);
}

async function chooseByMouse(page, name) {
  const trigger = await siteTrigger(page);
  await trigger.click();
  const option = page.getByRole('option', { name: new RegExp(name) });
  if (await option.count() !== 1) throw new Inconclusive(`option "${name}" not found after opening the trigger`);
  await option.click();
  return trigger;
}

const styleOf = (locator) => locator.evaluate((element) => window.__renderedReviewProbe.focusStyle(element));
const describeDifference = (focused, blurred) => Object.keys(focused)
  .filter((key) => focused[key] !== blurred[key])
  .map((key) => `${key}: "${focused[key]}" vs blurred "${blurred[key]}"`);

async function rr3PointerRing(browser, dir) {
  return withPage(browser, dir, 1280, async (page) => {
    await settle(page);
    const trigger = await chooseByMouse(page, 'Южный');
    await page.waitForTimeout(300);
    const focused = await trigger.evaluate((element) => element === document.activeElement);
    const after = await styleOf(trigger);
    await trigger.evaluate((element) => element.blur());
    await page.waitForTimeout(300);
    const blurred = await styleOf(trigger);
    const difference = describeDifference(after, blurred);
    assert.ok(!difference.length, `after a mouse choice the trigger shows an indicator (${difference.join('; ')})`);
    return `no indicator after mouse choice; focus ${focused ? 'returned to' : 'not on'} the trigger`;
  }, { clock: true });
}

async function rr3KeyboardRing(browser, dir) {
  return withPage(browser, dir, 1280, async (page) => {
    await settle(page);
    const trigger = await siteTrigger(page);
    let reached = false;
    for (let step = 0; step < 15 && !reached; step += 1) {
      await page.keyboard.press('Tab');
      reached = await trigger.evaluate((element) => element === document.activeElement);
    }
    assert.ok(reached, 'the trigger is not reachable with Tab');
    await page.waitForTimeout(300);
    const focused = await styleOf(trigger);
    await trigger.evaluate((element) => element.blur());
    await page.waitForTimeout(300);
    const blurred = await styleOf(trigger);
    const difference = describeDifference(focused, blurred);
    assert.ok(difference.length > 0, 'keyboard focus on the trigger shows no indicator');
    return `keyboard indicator: ${difference.join('; ')}`;
  }, { clock: true });
}

async function rr3Refresh(browser, dir) {
  return withPage(browser, dir, 1280, async (page) => {
    await settle(page);
    const callsBefore = await page.evaluate(() => window.__renderedReviewCalls.length);
    if (!callsBefore) throw new Inconclusive('calls to the simulated server were not observed');
    const start = await page.evaluate(() => Date.now());
    for (let elapsed = 100; elapsed <= 11000; elapsed += 100) {
      await page.clock.runFor(100);
      const shown = await visibleTitles(page, RR3_TITLES.north);
      if (shown.length !== RR3_TITLES.north.length) {
        const calls = await page.evaluate(() => window.__renderedReviewCalls);
        const last = calls.filter((call) => call.at <= start + elapsed).pop();
        const into = last ? start + elapsed - last.at : null;
        assert.fail(`the list shows ${shown.length} of 5 requests ${into === null ? '' : `${into} ms after a reload started`}`.trim());
      }
    }
    const calls = await page.evaluate(() => window.__renderedReviewCalls.length);
    assert.ok(calls > callsBefore, 'no periodic reload of the site within 11 s');
    return `list stayed visible through ${calls - callsBefore} reload(s), sampled every 100 ms`;
  }, { clock: true });
}

async function rr3Switch(browser, dir) {
  return withPage(browser, dir, 1280, async (page) => {
    await settle(page);
    await chooseByMouse(page, 'Южный');
    await page.clock.runFor(100);
    const stale = await visibleTitles(page, RR3_TITLES.north);
    assert.ok(!stale.length, `100 ms after switching sites ${stale.length} of the previous site's requests are visible`);
    await page.clock.runFor(600);
    const fresh = await visibleTitles(page, RR3_TITLES.south);
    assert.ok(fresh.length === RR3_TITLES.south.length, `700 ms after switching ${fresh.length} of 5 new requests are visible`);
    return 'old list gone at +100 ms, new list shown at +700 ms';
  }, { clock: true });
}

export const CASES = {
  RR1: [
    { check: 'edges', kind: 'defect', run: rr1Edges },
    { check: 'defaults', kind: 'defect', run: rr1Defaults },
    { check: 'tree', kind: 'control', run: rr1Tree },
  ],
  RR2: [
    { check: 'checkbox', kind: 'defect', run: rr2Checkbox },
    { check: 'meta-wrap', kind: 'defect', run: rr2MetaWrap },
    { check: 'text-wrap', kind: 'control', run: rr2TextWrap },
  ],
  RR3: [
    { check: 'pointer-ring', kind: 'defect', run: rr3PointerRing },
    { check: 'keyboard-ring', kind: 'control', run: rr3KeyboardRing },
    { check: 'refresh', kind: 'defect', run: rr3Refresh },
    { check: 'switch', kind: 'control', run: rr3Switch },
  ],
};

// Resolves with a detail on pass; rejects with an AssertionError
// (code ERR_ASSERTION) on fail and Inconclusive when elements are missing.
export function runCheck(browser, caseId, check, dir) {
  const entry = CASES[caseId]?.find((item) => item.check === check);
  if (!entry) throw new Error(`unknown check ${caseId}/${check}`);
  return entry.run(browser, resolve(dir));
}

export async function evaluateCase(browser, caseId, dir) {
  const results = [];
  for (const { check, kind } of CASES[caseId]) {
    try {
      results.push({ check, kind, status: 'pass', detail: await runCheck(browser, caseId, check, dir) });
    } catch (error) {
      const status = error?.code === 'ERR_ASSERTION' ? 'fail' : 'inconclusive';
      const detail = error?.code === 'ERR_ASSERTION' || error instanceof Inconclusive
        ? error.message : `error: ${String(error?.message || error).split('\n')[0]}`;
      results.push({ check, kind, status, detail });
    }
  }
  return { case: caseId, results };
}

async function main(argv) {
  const value = (flag) => {
    const index = argv.indexOf(flag);
    return index >= 0 ? argv[index + 1] : undefined;
  };
  const caseId = value('--case');
  const dir = value('--dir');
  if (!CASES[caseId] || !dir) {
    console.error('usage: node rendered-review-oracle.mjs --case RR1|RR2|RR3 --dir <directory>');
    return 2;
  }
  try {
    await access(join(dir, 'index.html'));
  } catch {
    console.error(`no index.html in ${dir}`);
    return 2;
  }
  const browser = await launchBrowser();
  try {
    console.log(JSON.stringify(await evaluateCase(browser, caseId, dir)));
  } finally {
    await browser.close();
  }
  return 0;
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  process.exitCode = await main(process.argv.slice(2));
}
