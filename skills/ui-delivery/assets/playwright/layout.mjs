/** Optional layout measurements for an existing Playwright harness; no runner or policy installation.
 * Synchronous DOM reads: the helpers never scroll, click, focus, blur or wait. Top-document CSS
 * selectors only. Geometry and computed styles are returned; no text contents, field values or HTML.
 */
import { evidenceContext } from './evidence.mjs';

const INDICATOR_PROPERTIES = [
  'outlineStyle', 'outlineWidth', 'outlineColor', 'outlineOffset', 'boxShadow',
  'borderTopWidth', 'borderRightWidth', 'borderBottomWidth', 'borderLeftWidth',
  'borderTopColor', 'borderRightColor', 'borderBottomColor', 'borderLeftColor', 'backgroundColor',
];

const selector = (value, name) => {
  if (typeof value !== 'string' || !value.trim()) throw new TypeError(`${name} selector is required`);
  return value;
};

const tolerance = (value) => {
  if (!Number.isFinite(value) || value < 0) throw new TypeError('tolerance must be a non-negative number');
  return value;
};

const measuredTargets = (measurement) => {
  evidenceContext(measurement?.context);
  const targets = measurement?.targets;
  if (!targets || typeof targets !== 'object' || Array.isArray(targets)) {
    throw new TypeError('measurement must come from measureText');
  }
  return targets;
};

const measured = (targets, name, role) => {
  if (typeof name !== 'string' || !Object.hasOwn(targets, name)) {
    throw new TypeError(`${role} names no measured target: ${String(name)}`);
  }
  return targets[name];
};

const px = (value) => `${Math.round(value * 10) / 10}px`;

/** Text line boxes, first-line position and clipping of each target, as currently rendered.
 * Visible text: a non-blank text node whose box is displayed, not visibility-hidden, not under
 * opacity 0 and not cut away by an ancestor with non-visible overflow; screen-reader-only text
 * (a clip box of 2px or less, a zero clip rect, clip-path inset(50%)) does not count.
 * Field values and placeholders are not text nodes and are not measured.
 */
export async function measureText(page, { context, targets } = {}) {
  const provenance = evidenceContext(context);
  if (!targets || typeof targets !== 'object' || Array.isArray(targets)) {
    throw new TypeError('targets must be a selector map');
  }
  for (const [name, value] of Object.entries(targets)) {
    if (!name.trim()) throw new TypeError('target name is required');
    selector(value, name);
  }
  if (!Object.keys(targets).length) throw new TypeError('at least one target is required');
  const observed = await page.evaluate((targets) => {
    const SKIP = new Set(['SCRIPT', 'STYLE', 'TEMPLATE', 'NOSCRIPT', 'TITLE']);
    const one = (selector) => {
      const matches = document.querySelectorAll(selector);
      if (matches.length !== 1) throw new Error(`Expected one target: ${selector}; got ${matches.length}`);
      return matches[0];
    };
    const ancestors = function* (node) {
      for (let element = node.parentElement; element && element !== document.documentElement;
        element = element.parentElement) yield element;
    };
    const hidesX = (style) => style.overflowX !== 'visible';
    const hidesY = (style) => style.overflowY !== 'visible';
    // Overflow does not apply to inline boxes or to elements without a box.
    const boxed = (style) => style.display !== 'inline' && style.display !== 'contents';
    const clientBox = (element) => {
      const rect = element.getBoundingClientRect();
      const left = rect.left + element.clientLeft;
      const top = rect.top + element.clientTop;
      return { left, top, right: left + element.clientWidth, bottom: top + element.clientHeight };
    };
    const zeroClip = (style) => {
      if (style.position !== 'absolute' && style.position !== 'fixed') return false;
      const match = /^rect\((.*)\)$/.exec(style.clip);
      if (!match) return false;
      const [top, right, bottom, left] = match[1].split(/[\s,]+/).map(parseFloat);
      if ([top, right, bottom, left].some(Number.isNaN)) return false;
      return right <= left || bottom <= top;
    };
    // The screen-reader-only pattern and collapsed clip boxes hide the whole node.
    const concealed = (node) => {
      for (const element of ancestors(node)) {
        const style = getComputedStyle(element);
        if (zeroClip(style) || style.clipPath === 'inset(50%)') return true;
        if (boxed(style) && ((hidesX(style) && element.clientWidth <= 2)
          || (hidesY(style) && element.clientHeight <= 2))) return true;
      }
      return false;
    };
    const rendered = (node) => {
      const parent = node.parentElement;
      if (!node.data.trim() || !parent || SKIP.has(parent.tagName)) return false;
      if (getComputedStyle(parent).visibility !== 'visible') return false;
      let box = parent;
      while (box && getComputedStyle(box).display === 'contents') box = box.parentElement;
      return !!box && box.checkVisibility({ opacityProperty: true }) && !concealed(node);
    };
    const textRects = (node) => {
      const range = document.createRange();
      range.setStart(node, node.data.search(/\S/));
      range.setEnd(node, node.data.trimEnd().length);
      return Array.from(range.getClientRects()).filter((rect) => rect.width > 0.5 && rect.height > 0.5);
    };
    const clippedAway = (rect, node) => {
      for (const element of ancestors(node)) {
        const style = getComputedStyle(element);
        if (!boxed(style)) continue;
        const box = clientBox(element);
        if (hidesX(style) && Math.min(rect.right, box.right) - Math.max(rect.left, box.left) < 1) return true;
        if (hidesY(style) && Math.min(rect.bottom, box.bottom) - Math.max(rect.top, box.top) < 1) return true;
      }
      return false;
    };
    // Text is cut when a box on its path hides overflow on an axis, has more content than room
    // on that axis, and this text extends past its padding box there. A scroll container whose
    // other content overflows does not count against text that is fully inside it.
    const cut = (node, rects) => {
      const left = Math.min(...rects.map((r) => r.left)), right = Math.max(...rects.map((r) => r.right));
      const top = Math.min(...rects.map((r) => r.top)), bottom = Math.max(...rects.map((r) => r.bottom));
      for (const element of ancestors(node)) {
        const style = getComputedStyle(element);
        if (!boxed(style)) continue;
        const box = clientBox(element);
        if (hidesX(style) && element.scrollWidth > element.clientWidth + 1
          && (left < box.left - 1 || right > box.right + 1)) return true;
        if (hidesY(style) && element.scrollHeight > element.clientHeight + 1
          && (top < box.top - 1 || bottom > box.bottom + 1)) return true;
      }
      return false;
    };
    // Rects of one line overlap vertically by at least half the shorter one.
    const mergeLines = (rects) => {
      const lines = [];
      for (const rect of [...rects].sort((a, b) => a.top - b.top)) {
        const line = lines.find((item) => Math.min(item.bottom, rect.bottom) - Math.max(item.top, rect.top)
          >= Math.min(item.bottom - item.top, rect.height) / 2);
        if (line) {
          line.left = Math.min(line.left, rect.left); line.right = Math.max(line.right, rect.right);
          line.top = Math.min(line.top, rect.top); line.bottom = Math.max(line.bottom, rect.bottom);
        } else lines.push({ left: rect.left, right: rect.right, top: rect.top, bottom: rect.bottom });
      }
      return lines.sort((a, b) => a.top - b.top)
        .map((line) => ({ x: line.left, y: line.top, width: line.right - line.left, height: line.bottom - line.top }));
    };
    const measure = (element) => {
      const visible = [];
      const clipped = { overflow: false, ellipsis: false, nowrap: false, lineClamp: false };
      const walker = document.createTreeWalker(element, NodeFilter.SHOW_TEXT);
      for (let node = walker.nextNode(); node; node = walker.nextNode()) {
        if (!rendered(node)) continue;
        const rects = textRects(node);
        if (!rects.length) continue;
        const shown = rects.filter((rect) => !clippedAway(rect, node));
        if (!shown.length) continue;
        visible.push(...shown);
        if (cut(node, rects)) clipped.overflow = true;
        const parentStyle = getComputedStyle(node.parentElement);
        if (parentStyle.textWrapMode === 'nowrap' || /^(nowrap|pre)$/.test(parentStyle.whiteSpace)) clipped.nowrap = true;
        // text-overflow and line-clamp act on the block container that holds the text.
        for (let box = node.parentElement; box; box = box.parentElement) {
          const style = getComputedStyle(box);
          if (style.textOverflow === 'ellipsis' && hidesX(style)) clipped.ellipsis = true;
          if ([style.webkitLineClamp, style.lineClamp].some((value) => value && value !== 'none')) clipped.lineClamp = true;
          if ((box === element || !element.contains(box)) && boxed(style)) break;
        }
      }
      const lines = mergeLines(visible);
      const box = element.getBoundingClientRect();
      return {
        rect: { x: box.x, y: box.y, width: box.width, height: box.height },
        lines,
        firstLine: lines.length ? { x: lines[0].x, centerY: lines[0].y + lines[0].height / 2 } : null,
        clipped,
      };
    };
    const result = {};
    for (const [name, selector] of Object.entries(targets)) result[name] = { selector, ...measure(one(selector)) };
    return { viewport: { width: innerWidth, height: innerHeight }, targets: result };
  }, targets);
  return { context: provenance, ...observed };
}

/** Pure. Same-role groups should share a first-line text edge; offsets declare intended indentation:
 * `target`'s first line starts at least `min` px right of `from`'s. A target without visible
 * text is a `missing` finding, never a silent pass.
 */
export function compareEdges(measurement, { groups, offsets = [], tolerance: limit = 1 } = {}) {
  const targets = measuredTargets(measurement);
  tolerance(limit);
  if (!Array.isArray(groups) || !groups.length) throw new TypeError('groups must be a non-empty array');
  for (const group of groups) {
    if (!Array.isArray(group) || group.length < 2 || new Set(group).size !== group.length) {
      throw new TypeError('each group must list at least two distinct target names');
    }
    group.forEach((name) => measured(targets, name, 'group'));
  }
  if (!Array.isArray(offsets)) throw new TypeError('offsets must be an array');
  for (const offset of offsets) {
    measured(targets, offset?.target, 'offset.target');
    measured(targets, offset?.from, 'offset.from');
    if (!Number.isFinite(offset.min)) throw new TypeError('offset.min must be a number');
  }
  const findings = [];
  const missing = new Set();
  const present = (name) => {
    if (targets[name].firstLine) return true;
    if (!missing.has(name)) {
      missing.add(name);
      findings.push({ kind: 'missing', targets: [name], values: [null], detail: `${name} has no visible text` });
    }
    return false;
  };
  for (const group of groups) {
    const names = group.filter(present);
    if (names.length < 2) continue;
    const values = names.map((name) => targets[name].firstLine.x);
    const low = values.indexOf(Math.min(...values)), high = values.indexOf(Math.max(...values));
    const spread = values[high] - values[low];
    if (spread > limit) {
      findings.push({ kind: 'edge', targets: names, values,
        detail: `first-line x differs by ${px(spread)}: ${names[low]} at ${px(values[low])}, ${names[high]} at ${px(values[high])}; tolerance ${px(limit)}` });
    }
  }
  for (const { target, from, min } of offsets) {
    if (![target, from].map(present).every(Boolean)) continue;
    const values = [targets[target].firstLine.x, targets[from].firstLine.x];
    const indent = values[0] - values[1];
    if (indent < min - limit) {
      findings.push({ kind: 'offset', targets: [target, from], values,
        detail: `${target} starts ${px(indent)} right of ${from}; declared at least ${px(min)}, tolerance ${px(limit)}` });
    }
  }
  return { pass: findings.length === 0, findings };
}

/** Pure. The vertical center of `control`'s box against the center of `text`'s first line. */
export function compareRow(measurement, { control, text, tolerance: limit = 2 } = {}) {
  const targets = measuredTargets(measurement);
  const box = measured(targets, control, 'control').rect;
  const line = measured(targets, text, 'text').firstLine;
  tolerance(limit);
  if (!(box.width > 0 && box.height > 0)) return { pass: false, delta: null, detail: `${control} has no rendered box` };
  if (!line) return { pass: false, delta: null, detail: `${text} has no visible text` };
  const delta = box.y + box.height / 2 - line.centerY;
  return { pass: Math.abs(delta) <= limit, delta,
    detail: `${control} center is ${px(Math.abs(delta))} ${delta > 0 ? 'below' : 'above'} the first line of ${text}; tolerance ${px(limit)}` };
}

/** Computed indicator styles of one element as it is now. Does not focus or blur: the caller
 * performs the real pointer or keyboard action between snapshots.
 */
export async function indicatorStyle(page, { context, target } = {}) {
  const provenance = evidenceContext(context);
  selector(target, 'target');
  const observed = await page.evaluate(({ target, properties }) => {
    const matches = document.querySelectorAll(target);
    if (matches.length !== 1) throw new Error(`Expected one target: ${target}; got ${matches.length}`);
    const element = matches[0];
    const style = getComputedStyle(element);
    return { active: document.activeElement === element, focusVisible: element.matches(':focus-visible'),
      style: Object.fromEntries(properties.map((name) => [name, style[name]])) };
  }, { target, properties: INDICATOR_PROPERTIES });
  return { context: provenance, selector: target, ...observed };
}

/** Pure. Visual properties that differ between two snapshots of the same target; the active and
 * focus-visible flags are ignored. An outline with style none or zero width and the color of a
 * zero-width border side are not visible, so their other values do not count as a change.
 */
export function indicatorDiff(before, after) {
  for (const [label, snapshot] of [['before', before], ['after', after]]) {
    if (!snapshot?.style || INDICATOR_PROPERTIES.some((name) => typeof snapshot.style[name] !== 'string')) {
      throw new TypeError(`${label} must come from indicatorStyle`);
    }
  }
  if (before.selector !== after.selector) throw new TypeError('snapshots must describe the same target');
  const visible = (style) => {
    const shown = { ...style };
    if (style.outlineStyle === 'none' || parseFloat(style.outlineWidth) === 0) {
      for (const name of ['outlineStyle', 'outlineWidth', 'outlineColor', 'outlineOffset']) shown[name] = 'none';
    }
    for (const side of ['Top', 'Right', 'Bottom', 'Left']) {
      if (parseFloat(style[`border${side}Width`]) === 0) shown[`border${side}Color`] = 'none';
    }
    return shown;
  };
  const a = visible(before.style), b = visible(after.style);
  return INDICATOR_PROPERTIES.filter((name) => a[name] !== b[name])
    .map((property) => ({ property, before: before.style[property], after: after.style[property] }));
}
