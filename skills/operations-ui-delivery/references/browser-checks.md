# Browser actions and visual baselines

Use only for the applicable browser-testing mechanism; the Acceptance procedure
owns scenario design and evidence levels.

## Playwright actions

Reuse its existing fixtures, configuration and reporting. Prefer user-facing
role/name or label locators and retrying assertions. A generator can translate a
scenario plan into code, but review its assertions against the expected outcome;
a recorded sequence is not its own acceptance oracle.

Be precise about what an action or assertion establishes:

- `toBeVisible()` does not mean inside the viewport. `toBeInViewport()` checks
  intersection; choose a relevant ratio or geometry check where partial clipping
  matters. Neither alone proves the next step is understandable or unobstructed.
- Pointer actions such as `click()` can scroll their target into view. For an
  Add/reveal complaint, assert the intended feedback, viewport and focus state
  immediately after the real trigger, before the next action repairs that state.
- To verify tab order or returned focus, assert what the application did and
  navigate with `page.keyboard`; do not use `focus()` or `locator.press()` to
  manufacture the focus being tested. Explicit focus is valid for unrelated
  setup, not proof of keyboard reachability.
- Forced clicks, dispatched events and direct URLs may bypass the failing path.
  Use them only where that path is not the assertion's subject; they do not
  establish ordinary pointer operability or navigation reachability.

Example: Add at the top of a long list silently appends an editor below the fold.
A test that clicks Add and then the appended field can pass because the second
click scrolls. If the intended flow moves into the editor, assert its viewport
presence and expected focus before that click. A valid alternative keeps the
current position and exposes visible feedback plus an explicit route to the new
editor: assert that feedback and route first, then follow it. Do not require every
offscreen append to auto-scroll or steal focus.

## State-specific evidence

When the existing harness lacks the required observation, the optional
[Playwright examples](../assets/playwright/README.md) provide `observeUi`, bounded
`observeUiSequence`, `scanAccessibility` and `triageFindings`. Adapt only the needed
example; do not install a second runner, auto-enable hooks or copy all helpers.
These are examples, not a qualified cross-product runtime dependency.

Reproduce the chosen state deliberately. Reuse an existing story, fixture or
scenario when one exists; set data, time and access, and confirm fonts and
assets are ready before capturing. Do not wait for idle in a way that erases the
loading, transition or failure state under test. Distinguish viewport, full-page
and platform capture mechanisms. A native platform without Storybook or a
browser does not require installing one: take the available path and name the
gap. For capture used as transfer source material, the duties in
[Design transfer](design-transfer.md) apply.

Tie evidence to the build, scenario, current state and deterministic dataset.
Observe before another action scrolls, focuses or dismisses the obstacle. Pointer
hit samples and viewport intersection describe geometry, not complete operability,
keyboard access or visual quality. Actual activation and its effect remain part
of the scenario. Bounded sampling may miss intermediate frames; use the Motion
procedure when making claims about a running transition.

Open the relevant menu, dialog or error state before an accessibility scan, and
verify the intended scope is present. Use the owner's explicit rule selection.
Keep violations, incomplete results and engine failures distinct; incomplete is
not a pass. Existing known issues may use exact rule/target/scenario/state waivers
with reasons and expiry; retain expired or unmatched waivers for review. Never
silence a file or a whole rule to make a result green. A clean scan does not prove
keyboard completion, screen-reader announcements or full WCAG conformance.

Reuse the product's report attachments. DOM observations and screenshots are
separate captures, not an atomic snapshot. Review output for sensitive data;
the example omits values and raw HTML, but selectors and screenshots can still
identify records. Upload nothing automatically.

## Screenshot baselines

For screenshot comparisons, review the initial baseline against the intended UI
and compare in a controlled rendering environment. On failure, distinguish a
product regression, fixture/environment problem and intentional contract change.
Repair the responsible layer; do not weaken assertions, skip checks or refresh
snapshots just to obtain green. An approved visual change can legitimately update
the reviewed baseline while retaining behavior checks.

## Sources

- [Assertions](https://playwright.dev/docs/test-assertions)
- [Input](https://playwright.dev/docs/input)
- [Visual comparisons](https://playwright.dev/docs/test-snapshots)
- [Test Agents](https://playwright.dev/docs/test-agents)
- [Accessibility testing and its limits](https://playwright.dev/docs/accessibility-testing)
