# Optional Playwright evidence examples

Use the existing product harness and reporting. These are small, project-adaptable
examples, not a new installed skill, runner or stable cross-product package API.
Node.js is needed only for these examples, not for Agent Assets source validation
or native-client installation. No dependency is installed by importing them.

## Observe the risky state before helpers change it

```js
import { observeUi, observeUiSequence } from './evidence.mjs';

const context = { build: testedRevision, scenario: 'create-connection',
  state: 'after-add', data: fixtureRevision };
await page.getByRole('button', { name: 'Add connection' }).click();
const evidence = await observeUi(page, {
  context, targets: { editor: '#connection-name', save: '#save-connection' },
  regions: { workspace: '#workspace' },
});
await testInfo.attach('after-add-observation', {
  body: JSON.stringify(evidence, null, 2), contentType: 'application/json',
});
```

The selectors must identify exactly one element in the top document. Missing or
ambiguous selectors fail; there is no fallback to an unrelated element. Focus,
viewport intersection, sampled hit reception and scroll offsets are observations,
not a generic accessibility/actionability certificate. The scenario still needs
real activation, its intended effect and the legitimate neighboring control.
Shadow-root/frame traversal and assistive-technology output are not implemented.

For an affected transition, call `observeUiSequence(page, options, sampleCount)`
after the real trigger, with a capture budget chosen for that task. It yields
bounded observations separated by animation-frame opportunities; tool overhead
can miss frames. It does not prove smoothness, capture every frame or replace a
recording when that is required. The 600-sample ceiling is a resource guard, not
a UI-performance requirement. The helpers never disable motion or set focus.

## Scan an actually open state

```js
import AxeBuilder from '@axe-core/playwright';
import { scanAccessibility, triageFindings } from './evidence.mjs';

await page.getByRole('button', { name: 'Open editor' }).click();
await expect(page.locator('#editor')).toBeVisible();
const report = await scanAccessibility(page, {
  context: { build: testedRevision, scenario: 'edit', state: 'error-open', data: fixtureRevision },
  scope: '#editor', rules: ownerSelectedRuleIds,
  createBuilder: ({ page }) => new AxeBuilder({ page }),
});
const result = triageFindings(report, approvedStateLocalWaivers);
await testInfo.attach('accessibility', {
  body: JSON.stringify({ report, result }, null, 2), contentType: 'application/json',
});
expect(result.active).toEqual([]);
expect(result.needsReview, 'Unresolved accessibility results need review').toEqual([]);
// Keep unusedWaivers visible for removal/review; never treat them as waived findings.
```

Use a fresh builder and the project's actual `@axe-core/playwright` dependency.
Do not change rule selection, add dependencies, download browsers or attach live
customer data without the owning task's permission. Scope presence is checked;
engine errors propagate. `incomplete` results remain `needs-review`, even when a
waiver matches. No full-WCAG, keyboard, screen-reader or visual-quality claim follows.

Waivers match exact rule, target array, scenario and state, require a reason and
an ISO expiry date, and are returned in the report rather than discarded. Wildcard
waivers are refused. A changed target, expired waiver or different state remains
an active finding. Only flat top-document selector targets can currently be waived;
more complex axe targets remain findings. Unknown finding kinds are rejected.
There is no automatic ignore-file, autofix, hook or taste-based rule.

The summaries omit raw HTML and input values. CSS selectors and images can still
contain identifying data: inspect artifacts before sharing. DOM observation,
accessibility scan and screenshot are different captures, not an atomic state.

## Measure alignment instead of judging a screenshot

```js
import { measureText, compareEdges, compareRow, indicatorStyle, indicatorDiff } from './layout.mjs';

const context = { build: testedRevision, scenario: 'settings', state: 'default', data: fixtureRevision };
await page.setViewportSize({ width: 390, height: 844 });
const layout = await measureText(page, { context, targets: {
  header: '#display-header', theme: '#theme-row', units: '#units-row', contrast: '#contrast-row',
  more: '#more-display', digest: '#digest-label', digestBox: '#digest-box',
} });
// Decided before measuring: contrast is a sub-item, indented at least 16px.
const edges = compareEdges(layout, {
  groups: [['header', 'theme', 'units', 'more']],
  offsets: [{ target: 'contrast', from: 'theme', min: 16 }],
});
expect(edges.findings).toEqual([]);
const row = compareRow(layout, { control: 'digestBox', text: 'digest' });
expect(row.pass, row.detail).toBe(true);

const snapshot = () => indicatorStyle(page, { context, target: '#apply' });
const initial = await snapshot();
await page.getByRole('button', { name: 'Apply changes' }).click();
const afterPointer = await snapshot();
await page.locator('#apply-hint').click();  // moves focus off and sets where Tab starts
await page.keyboard.press('Tab');
const afterKeyboard = await snapshot();
expect(afterKeyboard.active).toBe(true);
expect(indicatorDiff(initial, afterKeyboard)).not.toEqual([]);
expect(indicatorDiff(initial, afterPointer)).toEqual([]);  // only if the product's policy says so
```

`measureText` returns each target's box, its visible text line boxes, the first
line's left edge and vertical center, and clipping flags. Line boxes come from the
rendered text, so padding, markers and wrappers that move the text are measured;
an element's own box is not its text edge. `firstLine` is `null` when nothing is
visible: hidden, transparent, collapsed and screen-reader-only text does not count,
and `compareEdges` reports such a target as `missing` rather than passing it.
`clipped` reports only text that is actually cut: `overflow` when a box that
hides overflow cuts it, and `ellipsis`, `nowrap` or `lineClamp` when that style is
in effect on the cut text. A style that cuts nothing at this width is not
reported. This default changed: earlier, the three style flags were set whenever
the style was in effect, and on one product's live screens that gave 110 flags
among 127 elements in open states where nothing was cut. Pass `declared: true`
to also get `declared`, the same three styles wherever they are in effect, cut or
not. `compareRow` compares a control's center with the first line of its label,
not the label block, so a wrapped label still checks. The
indicator snapshot holds computed outline, box-shadow, border and background
values plus the active and `:focus-visible` flags; `indicatorDiff` lists only the
visual properties that changed. A hover style also counts as a change, so move the
pointer away before a snapshot when the control has one.

These are observations at the conditions the caller sets up: the widths, states,
fonts and data of that run. A pass is not a design approval and says nothing
about widths or states that were not measured. Decide groups, offsets and
tolerances from the design before measuring; an exception declared after a
failure only hides the finding. The helpers never scroll, click, focus, blur or
wait, return no text contents, field values or HTML, and require each selector
to match exactly one top-document element. Shadow-root and frame traversal are
not implemented.

## Walk a measurement matrix

```js
import { chromium } from 'playwright';
import { readFile } from 'node:fs/promises';
import { parseMatrix, sweepMatrix } from './matrix.mjs';
import { measureText } from './layout.mjs';

const matrix = parseMatrix(await readFile('ui-matrix.json', 'utf8'));
const browser = await chromium.launch(matrix.launch);  // keeps scrollbars visible
const page = await browser.newPage();
const result = await sweepMatrix(page, {
  context: { build: testedRevision, scenario: 'orders' }, matrix,
  load: async ({ width, state, data }) => { await page.goto(ordersUrl); },  // data is in place
  measurements: {
    'text-cut': async (page, cell) => {
      const { targets } = await measureText(page, { context: cell, targets: orderTitles });
      return { findings: Object.entries(targets).filter(([, t]) => t.clipped.overflow)
        .map(([name]) => ({ class: 'text-cut', kind: 'cut', targets: [name] })) };
    },
    'row-edges': rowEdges,  // the product's own, built on compareEdges
  },
});
expect(result.unmeasured).toEqual([]);
expect(result.findings).toEqual([]);
```

`matrix.mjs` walks the product's
[measurement matrix](../../references/browser-checks.md#walk-the-measurement-matrix):
widths, states with their entry steps and measurement names, a data source and
the launch. It is a harness, not a detector: it finds nothing itself. For each
width it sets the viewport; for the default state and each declared state it
calls `load`, runs the entry steps with Playwright's waiting locators (`click`,
`hover`, `focus`, `fill`, `press`, `wait`), lets animations and smooth scrolling
settle, and runs that cell's measurements. Each returns `{ findings, inconclusive }`;
results carry their width, state and measurement, and a finding absent from the
default state at that width is marked `onlyInState`. `cells` lists every cell
with its measurement names, whether it was measured and its finding count. A
state that cannot be entered, or a measurement that throws, leaves its cell in
`unmeasured` with the reason, and `pass` stays false.

`parseMatrix` refuses a file without `launch.ignoreDefaultArgs: ['--hide-scrollbars']`
(or `true`): headless Chromium otherwise paints no classic scrollbar and gives it
no width, so content under it and a missing one both pass. It also refuses
duplicate or missing widths, a data entry that is not exactly one `path` or
`command`, unknown actions and state widths outside the matrix, and
`sweepMatrix` refuses a measurement name with no function, before anything runs.
The data source is noted in every context as `path:` or `command:`; the helper
never runs the command or reads the file, `load` puts the data in place.
`enterState`, `sweepStates` and `settle` are exported for a harness that keeps
its own loop. Settling waits at most one second; a spinner that never stops
reaches that bound and `settle` returns `false`.

## Qualification and sources

[Executable checks](../../evals/browser/README.md) exercise synthetic good/fault
variants and these helpers. They are not executed product acceptance or an agent
comparison. Promote relevant outcomes into the product's existing tests rather
than pointing production assertions at these fixtures.

- [Playwright accessibility integration and limitations](https://playwright.dev/docs/accessibility-testing)
- [Playwright visual comparisons](https://playwright.dev/docs/test-snapshots)
- [Playwright input and action behavior](https://playwright.dev/docs/input)

The examples are original glue, not a vendored detector engine. They reuse the
pattern of scoped findings, deduplication and reasoned exceptions described by
[Impeccable hooks](https://github.com/pbakaus/impeccable/blob/cb56ed6c19a07329a9fa0cd4e657bee040156593/.agents/skills/impeccable/reference/hooks.md),
without importing aesthetic bans, client hooks or its install lifecycle.
