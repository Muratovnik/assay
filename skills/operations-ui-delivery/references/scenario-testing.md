# Scenario-led UI acceptance

Use to design or audit acceptance/regression checks. Ordinary fixes can use the
selected procedure's checks and the entrypoint's finish procedure; they do not
automatically require this file. For Playwright actions or screenshot baselines,
also read the applicable section of [browser checks](browser-checks.md).

## Derive the scenario

Connect the user's goal and starting state to the actual entry/actions, observable
result at risky transitions and committed/unchanged objects. Include relevant
save/cancel, failure, retry and return behavior. Use the brief and approved contract;
recorded clicks reveal current behavior, not necessarily correct expectations.
An API capability cannot resolve an unsettled product policy.

For broad work map supported journeys before generating tests, including older
and direct-entry paths. Link reported defects to these outcomes and look for
omitted consumers, states or scale conditions after the defect list turns green.
Record that omission check separately in existing task reporting. Defect closure
is narrower than systemic acceptance. A label-only change need not acquire a full
product specification or invented failure modes.

For a material workflow, account for entry/discovery, input/selection, commit,
pending, success/partial failure, departure and return. Check applicable keyboard,
assistive/non-hover access and load conditions across those stages. Mark a family
as covered, needing a check, inapplicable or unresolved in existing task evidence;
use the routed procedure for detail. Do not turn this into every-device testing
for a local repair. A fresh combination such as filter + pagination + return or
edit + row switch + late save can reveal gaps that isolated complaint cases miss.

## Choose distinguishing checks

For material changes cover successful completion, consequential boundary/failure,
recovery and risky intermediate states. Choose input classes by their effect on
the outcome; combine conditions only where their interaction matters. Reuse
existing coverage, focused unit/component checks for rules and application checks
for composed journeys. Do not create a second framework or exercise every state
permutation end-to-end.

Use deterministic isolated data and the requested build/runtime. Fixtures may
bypass unrelated setup, not the navigation, permission or transition under test.
Choose cardinality by risk: a three-item test can prove arithmetic, not usability
with hundreds of overlaps; an actual product cap of three makes that scale valid.
Exercise zero/one/several/large populations only where behavior or effort changes.

Choose viewport, zoom and input conditions from supported environments and the
specific interaction risk. A convenient fixed resolution is a harness setting,
not evidence of responsive acceptance. When layout is the guarantee, assert the
relevant geometry, visibility or operability under those conditions; do not add
arbitrary device coverage to a scenario whose result is independent of layout.

Assert distinguishable consumer outcomes, not only an editor badge, toast or
class. Do not invent propagation for explicitly local state. Preserve a nearby
valid control: mixed versus independent-parent selection, accidental shifting
versus intentional expansion, lost draft versus a recoverable failed save.

Ask whether the test could pass while the complaint remains true. In particular,
separate presence checks cannot prove mutually exclusive states, center clicks
cannot prove edge acquisition, and endpoint snapshots cannot prove motion. Use
the affected procedure's concrete oracle rather than duplicating all domain checks
here. Observe risky states before helpers scroll/focus/dismiss or requests settle.
CSS-only changes can break operability; choose coverage by guarantee, not extension.

## Check interaction under representative load

For dense collections, search, bulk work or expensive computation, exercise
typing, scrolling and the next action at realistic cardinality. Distinguish a
request legitimately pending from a main thread that prevents input or feedback.
Use existing measurement/profiling to locate an observed bottleneck; measure the
affected interaction again after a material optimization, under comparable data.

Do not infer performance from small fixtures or mandate virtualization after an
arbitrary row count. Debouncing every keystroke or imposing one request deadline
can damage the task. When virtualization is justified, check selection, identity,
focus and required navigation to offscreen items as well as speed; use
[Accessibility](accessibility-and-composites.md#match-semantics-to-the-interaction)
for the relevant composite model. Preserve a sufficient small native table.

## Evaluate the evidence

Use a bounded rendered review for hierarchy, density, ambiguous controls, copy and
the apparent next step. Automation can preserve an approved presentation but cannot
approve its meaning. A narrow objective invariant may have sufficient automated
evidence without a visual pass. The entrypoint governs preview/approval boundaries;
neither screenshots nor user approval replace required behavior checks.

Keep scenario/criterion → assertion → execution evidence or gap in the existing
task/test record. Separate specified, automated, executed, visually inspected and
user-approved results. Test count, an existing suite or missing runtime access
does not establish a pass. Distinguish harness evidence from the production path.
For visual baselines, the browser reference below owns review/update safeguards.

## Method references

- [Test design: input classes and transitions](https://github.com/stellarlinkco/myclaude/blob/f2e75c1263a2d5f09cdc4bb3dfe3635c635ff296/skills/test-cases/references/testing-principles.md)
- [Playwright: user-visible tests](https://playwright.dev/docs/best-practices)
- [Browser action and baseline checks](browser-checks.md)
- [gstack: functional and performance failure classes](https://github.com/garrytan/gstack/blob/0d1bd5616c0ef096bb7ccee336f63c60ee408618/qa/references/issue-taxonomy.md)

These are methods, not permission for installation, new roles or configuration.
