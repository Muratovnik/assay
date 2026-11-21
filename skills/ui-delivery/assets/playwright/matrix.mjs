/** Walks a product's measurement matrix: each supported width times each declared state, with the
 * measurement the product names for that cell. A harness, not a detector: it resizes the viewport,
 * reloads through the caller's `load`, runs the state's entry steps with real Playwright actions and
 * waits for animations, then calls the product's own measurement functions. It finds nothing itself.
 */
import { evidenceContext } from './evidence.mjs';

const SETTLE_MS = 1000;
const HIDDEN_SCROLLBARS = '--hide-scrollbars';

const nonEmpty = (value, name) => {
  if (typeof value !== 'string' || !value.trim()) throw new TypeError(`${name} must be a non-empty string`);
  return value;
};

const ACTIONS = {
  click: (page, step) => page.locator(nonEmpty(step.selector, 'step selector')).click(),
  hover: (page, step) => page.locator(nonEmpty(step.selector, 'step selector')).hover(),
  focus: (page, step) => page.locator(nonEmpty(step.selector, 'step selector')).focus(),
  fill: (page, step) => page.locator(nonEmpty(step.selector, 'step selector')).fill(String(step.value ?? '')),
  press: (page, step) => {
    nonEmpty(step.key, 'press key');
    return step.selector ? page.locator(step.selector).press(step.key) : page.keyboard.press(step.key);
  },
  wait: (page, step) => page.locator(nonEmpty(step.selector, 'step selector')).waitFor({ state: 'visible' }),
};

/** Waits (lets time pass) until the document's running animations finish and no scroll offset has
 * changed for three animation frames (a smooth scroll is not an animation), at most one second,
 * then two animation frames. Returns false when the bound was reached.
 */
export async function settle(page) {
  return page.evaluate((limit) => new Promise((resolve) => {
    let done = false;
    const finish = (value) => {
      if (done) return;
      done = true;
      requestAnimationFrame(() => requestAnimationFrame(() => resolve(value)));
    };
    const offsets = () => {
      let value = `${scrollX},${scrollY}`;
      for (const element of document.querySelectorAll('*')) {
        if (element.scrollTop || element.scrollLeft) value += `;${element.scrollTop},${element.scrollLeft}`;
      }
      return value;
    };
    requestAnimationFrame(() => {
      setTimeout(() => finish(false), limit);
      Promise.all(document.getAnimations().map((animation) => animation.finished.catch(() => {}))).then(() => {
        let last = offsets(), still = 0;
        const tick = () => {
          if (done) return;
          const now = offsets();
          still = now === last ? still + 1 : 0;
          last = now;
          if (still >= 3) finish(true);
          else requestAnimationFrame(tick);
        };
        requestAnimationFrame(tick);
      });
    });
  }), SETTLE_MS);
}

const checkState = (state) => {
  if (!state || typeof state.name !== 'string' || !state.name.trim() || !Array.isArray(state.enter)) {
    throw new TypeError('a state needs a name and an enter array');
  }
  for (const step of state.enter) {
    if (!ACTIONS[step?.action]) throw new TypeError(`unknown state action: ${String(step?.action)}`);
  }
};

/** Enters a declared state (acts): runs its steps with Playwright's strict, waiting locators, then
 * settles. Steps: { action: 'click' | 'hover' | 'focus' | 'wait', selector },
 * { action: 'fill', selector, value } or { action: 'press', key, selector? }.
 */
export async function enterState(page, state) {
  checkState(state);
  for (const step of state.enter) await ACTIONS[step.action](page, step);
  await settle(page);
}

const findingKey = (finding) => JSON.stringify([finding.class, finding.kind, finding.targets]);

/** Runs `measure(page, context)` in the default state and in each declared state (acts: calls
 * `load(state)` before every state, then enters it). `measure` returns { findings, inconclusive }.
 * Every state ends up in `measured` or in `unmeasured` with the reason; findings and inconclusive
 * results carry their state, and a finding absent from the default state is marked `onlyInState`.
 * Passes only when every state was measured and nothing was found.
 */
export async function sweepStates(page, { context, load, states = [], measure } = {}) {
  const provenance = evidenceContext(context);
  if (typeof load !== 'function' || typeof measure !== 'function') throw new TypeError('load and measure must be functions');
  if (!Array.isArray(states)) throw new TypeError('states must be an array');
  const names = new Set(['default']);
  for (const state of states) {
    checkState(state);
    if (names.has(state.name)) throw new TypeError(`duplicate state: ${state.name}`);
    names.add(state.name);
  }
  const measured = [], unmeasured = [], results = {}, findings = [], inconclusive = [];
  for (const state of [{ name: 'default', enter: [] }, ...states]) {
    const stateContext = { ...provenance, state: state.name };
    try {
      await load(state);
      await enterState(page, state);
    } catch (error) {
      unmeasured.push({ state: state.name, reason: `could not enter the state: ${error.message.split('\n')[0]}` });
      continue;
    }
    let result;
    try {
      result = await measure(page, stateContext);
    } catch (error) {
      unmeasured.push({ state: state.name, reason: `measurement failed: ${error.message.split('\n')[0]}` });
      continue;
    }
    measured.push(state.name);
    results[state.name] = result;
    findings.push(...(result?.findings ?? []).map((finding) => ({ ...finding, state: state.name })));
    inconclusive.push(...(result?.inconclusive ?? []).map((entry) => ({ ...entry, state: state.name })));
  }
  const inDefault = new Set(findings.filter((finding) => finding.state === 'default').map(findingKey));
  for (const finding of findings) finding.onlyInState = finding.state !== 'default' && !inDefault.has(findingKey(finding));
  return { context: provenance, pass: measured.length > 0 && !unmeasured.length && !findings.length && !inconclusive.length,
    measured, unmeasured, findings, inconclusive, results };
}

const names = (value, label) => {
  if (!Array.isArray(value) || !value.length) throw new TypeError(`${label} must be a non-empty array of measurement names`);
  value.forEach((name) => nonEmpty(name, `${label} entry`));
  return [...value];
};

/** Pure. Validates a matrix (an object or its JSON text) and returns a normalized copy:
 * { widths, height, launch, data, measure, states }. A launch that keeps Chromium's
 * --hide-scrollbars default is refused: a check without scrollbars misses what they cover.
 */
export function parseMatrix(input) {
  const matrix = typeof input === 'string' ? JSON.parse(input) : input;
  if (!matrix || typeof matrix !== 'object' || Array.isArray(matrix)) throw new TypeError('matrix must be an object');
  const { widths, height = 800, launch, data, measure, states = [] } = matrix;
  if (!Array.isArray(widths) || !widths.length || widths.some((width) => !Number.isInteger(width) || width <= 0)
    || new Set(widths).size !== widths.length) throw new TypeError('widths must be distinct positive integers');
  if (!Number.isInteger(height) || height <= 0) throw new TypeError('height must be a positive integer');
  const ignored = launch?.ignoreDefaultArgs;
  if (!launch || typeof launch !== 'object' || !(ignored === true || (Array.isArray(ignored) && ignored.includes(HIDDEN_SCROLLBARS)))) {
    throw new TypeError(`launch must show scrollbars: ignoreDefaultArgs: ['${HIDDEN_SCROLLBARS}']`);
  }
  const sources = ['path', 'command'].filter((key) => data && Object.hasOwn(data, key));
  if (sources.length !== 1) throw new TypeError('data must name exactly one of path or command');
  nonEmpty(data[sources[0]], `data ${sources[0]}`);
  if (!Array.isArray(states)) throw new TypeError('states must be an array');
  const seen = new Set(['default']);
  const normalized = states.map((state) => {
    checkState(state);
    if (seen.has(state.name)) throw new TypeError(`duplicate or reserved state name: ${state.name}`);
    seen.add(state.name);
    const only = state.widths ?? widths;
    if (!Array.isArray(only) || !only.length || only.some((width) => !widths.includes(width))) {
      throw new TypeError(`state ${state.name}: widths must be a non-empty subset of the matrix widths`);
    }
    return { name: state.name, enter: state.enter.map((step) => ({ ...step })), widths: [...only],
      measure: state.measure === undefined ? names(measure, 'measure') : names(state.measure, `state ${state.name} measure`) };
  });
  return { widths: [...widths], height, launch: { ...launch }, data: { [sources[0]]: data[sources[0]] },
    measure: names(measure, 'measure'), states: normalized };
}

/** Walks the matrix (acts): for each width it sets the viewport, then sweeps the default state and
 * every state declared for that width, calling `load({ width, state, data })` before each and the
 * named `measurements[name](page, context)` of the cell; their findings and inconclusive results
 * are joined. The data source is noted in every context; the caller's `load` puts it in place.
 * Launch the browser with `matrix.launch`. Passes only when every cell was measured and nothing
 * was found; each cell is reported with its width, state, measurements and result.
 */
export async function sweepMatrix(page, { context, matrix: input, load, measurements } = {}) {
  const matrix = parseMatrix(input);
  if (typeof load !== 'function') throw new TypeError('load must be a function');
  if (!measurements || typeof measurements !== 'object') throw new TypeError('measurements must map names to functions');
  for (const name of [matrix.measure, ...matrix.states.map((state) => state.measure)].flat()) {
    if (typeof measurements[name] !== 'function') throw new TypeError(`no measurement function named ${name}`);
  }
  const data = matrix.data.path ? `path:${matrix.data.path}` : `command:${matrix.data.command}`;
  const base = evidenceContext({ ...context, state: 'default', data });
  const cells = [], findings = [], inconclusive = [], unmeasured = [];
  for (const width of matrix.widths) {
    await page.setViewportSize({ width, height: matrix.height });
    const states = matrix.states.filter((state) => state.widths.includes(width));
    const declared = new Map([['default', matrix.measure], ...states.map((state) => [state.name, state.measure])]);
    const sweep = await sweepStates(page, {
      context: base, states,
      load: (state) => load({ width, state: state.name, data: matrix.data }),
      measure: async (page, cellContext) => {
        const joined = { findings: [], inconclusive: [] };
        for (const name of declared.get(cellContext.state)) {
          const result = await measurements[name](page, { ...cellContext, width, measurement: name });
          joined.findings.push(...(result?.findings ?? []).map((finding) => ({ ...finding, measurement: name })));
          joined.inconclusive.push(...(result?.inconclusive ?? []).map((entry) => ({ ...entry, measurement: name })));
        }
        return joined;
      },
    });
    for (const [state, measure] of declared) {
      const missed = sweep.unmeasured.find((entry) => entry.state === state);
      cells.push({ width, state, measure, measured: !missed, ...(missed ? { reason: missed.reason } : {}),
        findings: sweep.findings.filter((finding) => finding.state === state).length });
    }
    findings.push(...sweep.findings.map((finding) => ({ ...finding, width })));
    inconclusive.push(...sweep.inconclusive.map((entry) => ({ ...entry, width })));
    unmeasured.push(...sweep.unmeasured.map((entry) => ({ ...entry, width })));
  }
  return { context: base, pass: !unmeasured.length && !findings.length && !inconclusive.length,
    cells, findings, inconclusive, unmeasured };
}
