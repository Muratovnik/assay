/** Optional examples for an existing Playwright harness; no runner or policy installation. */
const nonEmpty = (value, name) => {
  if (typeof value !== 'string' || !value.trim()) throw new TypeError(`${name} is required`);
  return value;
};

export function evidenceContext(context) {
  const result = {};
  for (const key of ['build', 'scenario', 'state', 'data']) {
    result[key] = nonEmpty(context?.[key], key);
  }
  return result;
}

/** One synchronous DOM observation. Does not scroll, focus, click or wait for settlement.
 * Top-document CSS selectors only. These are observations, NOT an actionability oracle.
 * No field values, text contents, HTML, URL query strings or cookies are collected.
 */
export async function observeUi(page, { context, targets, regions = {} }) {
  const provenance = evidenceContext(context);
  for (const [group, entries] of Object.entries({ targets, regions })) {
    if (!entries || typeof entries !== 'object' || Array.isArray(entries)) {
      throw new TypeError(`${group} must be a selector map`);
    }
    for (const [name, selector] of Object.entries(entries)) {
      nonEmpty(name, 'target name');
      nonEmpty(selector, 'selector');
    }
  }
  if (!Object.keys(targets).length) throw new TypeError('at least one target is required');
  const observed = await page.evaluate(({ targets, regions }) => {
    const one = (selector) => {
      const matches = document.querySelectorAll(selector);
      if (matches.length !== 1) throw new Error(`Expected one target: ${selector}; got ${matches.length}`);
      return matches[0];
    };
    const viewport = { width: innerWidth, height: innerHeight };
    const rectangle = (r) => ({ x: r.x, y: r.y, width: r.width, height: r.height });
    const targetData = Object.fromEntries(Object.entries(targets).map(([name, selector]) => {
      const element = one(selector);
      const r = element.getBoundingClientRect();
      const style = getComputedStyle(element);
      const width = Math.max(0, Math.min(r.right, innerWidth) - Math.max(r.left, 0));
      const height = Math.max(0, Math.min(r.bottom, innerHeight) - Math.max(r.top, 0));
      const positions = [[0.5, 0.5], [0.1, 0.1], [0.9, 0.1], [0.1, 0.9], [0.9, 0.9]];
      const hits = positions.map(([fx, fy]) => {
        const x = r.left + r.width * fx;
        const y = r.top + r.height * fy;
        const receiver = r.width > 0 && r.height > 0 ? document.elementFromPoint(x, y) : null;
        return { x, y, receivesPointer: !!receiver && (receiver === element || element.contains(receiver)) };
      });
      return [name, {
        selector, rect: rectangle(r),
        viewportIntersection: r.width * r.height > 0 ? width * height / (r.width * r.height) : 0,
        focused: document.activeElement === element,
        disabled: element.matches(':disabled'), ariaDisabled: element.getAttribute('aria-disabled'),
        display: style.display, visibility: style.visibility, opacity: style.opacity,
        hits,
      }];
    }));
    const regionData = Object.fromEntries(Object.entries(regions).map(([name, selector]) => {
      const element = one(selector);
      return [name, { selector, scrollLeft: element.scrollLeft, scrollTop: element.scrollTop,
        clientWidth: element.clientWidth, clientHeight: element.clientHeight,
        scrollWidth: element.scrollWidth, scrollHeight: element.scrollHeight }];
    }));
    return { viewport, scroll: { x: scrollX, y: scrollY }, targets: targetData, regions: regionData,
      reducedMotion: matchMedia('(prefers-reduced-motion: reduce)').matches,
      forcedColors: matchMedia('(forced-colors: active)').matches,
      observedAt: new Date().toISOString() };
  }, { targets, regions });
  return { context: provenance, ...observed };
}

/** Bounded observations across a transition; the caller performs the real trigger.
 * Sampling may miss frames. This is not a video, smoothness score or endpoint approval.
 */
export async function observeUiSequence(page, options, samples) {
  if (!Number.isSafeInteger(samples) || samples < 1 || samples > 600) {
    throw new TypeError('samples must be between 1 and 600 (capture resource bound)');
  }
  const result = [];
  for (let index = 0; index < samples; index++) {
    result.push(await observeUi(page, options));
    if (index + 1 < samples) {
      await page.evaluate(() => new Promise((resolve) => requestAnimationFrame(() => resolve())));
    }
  }
  return result;
}

/** Use a fresh owner-configured @axe-core/playwright builder. Open the state FIRST.
 * Rule selection is explicit. Scan/attachment errors propagate; no fallback to a pass.
 * The returned summary intentionally excludes raw HTML. Preserve incompletes separately.
 */
export async function scanAccessibility(page, { context, scope, rules, createBuilder }) {
  const provenance = evidenceContext(context);
  nonEmpty(scope, 'scope');
  if (!Array.isArray(rules) || !rules.length || rules.some((id) => typeof id !== 'string' || !id.trim())) {
    throw new TypeError('explicit rule IDs are required');
  }
  if (typeof createBuilder !== 'function') throw new TypeError('createBuilder is required');
  const target = page.locator(scope);
  if (await target.count() !== 1 || !await target.isVisible()) {
    throw new Error('Accessibility scope must identify one visible container in the intended state');
  }
  const raw = await createBuilder({ page }).include(scope).withRules([...new Set(rules)]).analyze();
  const flatten = (items, kind) => items.flatMap((item) => item.nodes.map((node) => ({
    kind, rule: item.id, target: node.target, impact: item.impact ?? null, helpUrl: item.helpUrl,
  })));
  return { context: provenance, scope, rules: [...new Set(rules)],
    engine: raw.testEngine, observedAt: raw.timestamp,
    findings: [...flatten(raw.violations, 'violation'), ...flatten(raw.incomplete, 'needs-review')] };
}

/** Exact, state-local waivers, never file globs or taste rules. No composite quality score.
 * Unmatched/expired waivers remain visible so stale exceptions cannot silently accumulate.
 */
export function triageFindings(report, waivers = [], today = new Date().toISOString().slice(0, 10)) {
  evidenceContext(report.context);
  const validDate = (value) => typeof value === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(value)
    && !Number.isNaN(Date.parse(value)) && new Date(value).toISOString().slice(0, 10) === value;
  if (!validDate(today)) throw new TypeError('today must be an ISO calendar date');
  const exactTarget = (target) => Array.isArray(target) && target.length > 0
    && target.every((part) => typeof part === 'string' && part.trim() && !part.includes('*'));
  for (const waiver of waivers) {
    for (const key of ['rule', 'scenario', 'state', 'reason']) nonEmpty(waiver[key], `waiver.${key}`);
    if (!exactTarget(waiver.target) || !validDate(waiver.expires) || waiver.rule.includes('*')) {
      throw new TypeError('waivers require an exact target/rule and valid expiry date');
    }
  }
  const unique = new Map();
  for (const item of report.findings) {
    if (!['violation', 'needs-review'].includes(item.kind) || !Array.isArray(item.target)) {
      throw new TypeError('unsupported finding');
    }
    nonEmpty(item.rule, 'finding.rule');
    const key = JSON.stringify([item.kind, item.rule, item.target]);
    if (!unique.has(key)) unique.set(key, item);
  }
  const used = new Set();
  const active = [], waived = [], needsReview = [];
  for (const item of unique.values()) {
    // An inconclusive result cannot become a successful check by adding a waiver.
    if (item.kind === 'needs-review') { needsReview.push(item); continue; }
    const index = waivers.findIndex((w) => w.rule === item.rule
      && JSON.stringify(w.target) === JSON.stringify(item.target)
      && w.scenario === report.context.scenario && w.state === report.context.state && w.expires >= today);
    if (index < 0) active.push(item);
    else { used.add(index); waived.push({ finding: item, waiver: waivers[index] }); }
  }
  return { context: report.context, active, needsReview, waived,
    unusedWaivers: waivers.filter((_, index) => !used.has(index)) };
}
