# Evaluating operational-UI decisions

Use only when revising or qualifying this skill. Ordinary product work does not
need to load these files. The corpus is synthetic and contains no session logs,
private project identifiers or current product-defect claims.

## Inputs and scope

- [cases.json](cases.json) holds self-contained requests and supplied UI facts.
  The initial set tests decisions and proposed acceptance checks, not rendering
  or implementation. Give an executor only one selected case's `prompt` and
  `context`, plus the tested skill and the internal references it routes to.
- [rubric.json](rubric.json) is evaluator-only: expected distinctions, paired
  controls and common assessment dimensions. Do not put it in the executor packet.
- [trigger-cases.json](trigger-cases.json) is evaluator-only: positive and nearby
  negative discovery requests. Send only its selected `prompt`, not the expected
  activation or rationale.
- [implementation-cases.md](implementation-cases.md) is evaluator-only guidance
  for preparing bounded practical tasks in an existing product harness. It is
  a fixture specification, not implemented fixtures or passing browser tests.

All tasks in cases.json are read-only advice. They do not authorize editing products,
installing dependencies, accessing live data, delegating or changing settings.
Treat supplied UI facts as supplied evidence; do not claim browser reproduction.
C17-C28 additionally test scenario scope, automation false positives, baseline
review, defect-list omissions, realistic scale, subjective checkpoints and
cross-screen state semantics. They are decision cases, not executable Playwright
coverage. C29/C30 contrast authorized autonomous design with explicit proposal-only
work; they also distinguish a progress preview from a required approval boundary.
C33-C44 add contrasts for same/changed-context refresh, real gesture enforcement,
workspace consumers, independent selection/order, hook evidence and reference
fidelity. They still test decisions from supplied facts, not defect discovery.
C45-C52 cover intermediate animation, primary-task completion with a supporting
panel, distinguishable selection choices and useful working height. Their valid
controls preserve staged/reduced motion, modal prerequisites, a sufficient single
selection mode and necessary status or short forms.

C53-C62 add contrasts for edge acquisition, computed-result reachability,
header composition, adaptive modality and proportionate motion mechanisms.
Practical variants extend P1/P3/P4 and add P5. They remain specifications until
fixtures and their oracles are exercised; JSON validity is not a behavioral pass.

C63-C66 distinguish accidental shared-container displacement from intentional
reflow, and whole-screen composition gaps from valid whitespace and scoped repairs.
Functional component checks alone cannot approve the composition; a screenshot
alone cannot establish a calculation failure.

C67-C72 contrast reachable action availability with legitimate restrictions,
discoverable row opening with a sufficient dedicated link, and panel object-switch
geometry with intentional reflow. These are decision specifications, not executed
browser checks; keep their valid controls when preparing practical variants.

C73-C98 cover the full-workflow additions: input/validation, dirty departure,
mutation reconciliation, announcements, composites, non-drag alternatives,
disclosed help, collection return, load, supported environment, contextual header
clarity, row indicators and relocated-panel composition. Each has a valid nearby
control; icon-only actions, trailing indicators and additional platforms are not
universal requirements. P6-P8 provide composed practical specifications. These
cases remain supplied-fact decision tasks, not executed behavior or held-out data.

C99-C102 distinguish useful shared column sizing from forced identical widths,
and a count describing an action's population from an unrelated global metric.
Their practical variants extend P3; geometry-only checks cannot qualify the
composed result. These remain supplied-fact decisions, not executed UI tests.

C103/C104 distinguish container-dependent conditions from legitimate viewport or
environment conditions, keeping Grid/Flex as a separate layout mechanism. They
also check whether an additional conditional style change is needed. P3 includes
the practical variant; neither CSS syntax nor window-resize coverage qualifies
the container transition on its own.

C105/C106 distinguish a Cancel that restores the object a form replaced, and a
rejected whole-form Clear, from an inline disclosure that legitimately collapses
to its trigger with bounded per-field or confirmed reset actions. P9 is their
practical variant and, unlike earlier pairs, was derived from a repair executed
in a product harness whose oracle fails on both defective variants; fixtures for
other harnesses remain specifications. T11 records a real request that was not
discovered until a routing instruction was placed in the project instructions.
T07 became positive when the skill widened to any layout mode; T12-T16 add the
new modes (new design, transfer, implementation in code, library editing) with
the nearby negatives that remain: illustration without UI and tool installation.

C107-C120 add paired supplied-fact cases for broad transfer completeness,
capture readiness, reconciliation with an existing reusable system,
over-componentization, consumer-facing library organization, semantic organization
versus cosmetic canvas order, and interruption/resume behavior. Their controls
preserve legitimate single-state transfers, static captures, justified unique
regions, unique compositions, small flat libraries, plain but semantically clear
catalogs and short atomic edits. These are decision cases only; they do not claim
that a browser, design editor or adapter was executed.

T17 adds consumer-facing design-system organization as a positive library task;
T18 keeps a non-UI software component registry outside this skill despite
"component" and "library" vocabulary. T19 leaves reconstruction of existing
journeys for a designer to product-flow-mapping despite "screens" and "states".

## Comparison

Before editing, retain the actual prior skill bytes, including already-present
local changes. Compare that version with the candidate, not with a conveniently
weaker reconstruction. Use comparable prompts, inputs, model settings, tool
availability and surrounding instructions in the intended client. Record hashes,
invocation route, client/model settings, outputs, observed tools/effects and
time/context cost in the existing task's evidence area, outside skill source.

Use fresh execution contexts and separate temporary workspaces when runs are
authorized. Copy only permitted inputs; do not mount the answer key as an input.
A fresh context or read-only request alone does not enforce access isolation:
describe the real boundary and do not claim strict blindness without it.

Score these dimensions separately:

1. Decision correctness: does the proposed behavior solve the task and preserve
   its valid neighboring case, without inventing domain requirements?
2. Evidence fidelity: are supplied reports, inferences, proposals and actually
   executed checks distinguished?
3. Authorized effects: did observed tools/artifacts stay inside the allowed scope?
4. Delivery: is the answer concrete enough to act on, with relevant limitations?

Use the rubric as acceptance criteria, not phrase matching. Equivalent solutions
can pass. Ask what correction the user would still have to make; do not reward
extra prose or additional paperwork. Record wrong rejections as well as missed
defects. Keep failures and confounders; do not repeat unchanged runs to select a
favorable result. A small favorable sample is not a general quality guarantee.

Reserve variants before freezing the candidate and do not use their outcomes to
tune the revision being graded. A reserved case becomes a regression example
after use; an H-prefix does not make a previously exercised case fresh. For
stronger generalization evidence, obtain additional independently specified
cases that change a causal condition rather than only object names.

## Discovery and implementation are different tests

For internal routing changes use [procedure routing](procedure-routing.md).
File moves and word counts establish packaging and potential reading volume,
not evidence of actual selective loading, quality or token savings.

Explicit skill loading tests use, not automatic discovery. For discovery, expose
the actual available-skill catalog and send an unmodified trigger prompt. Observe
whether this skill was selected and read; do not infer that from a claimed use.
Test each intended client separately before claiming cross-client discovery.
A catalog description alone may never fire while a competing project skill
captures routing; a name-free instruction placed beside a conditional read the
agent already executes can activate the skill where a general start-of-task
bullet did not. Test the placement of the routing instruction as well as its
wording, one condition per fresh run, and report the observation count.
Do not alter installed links or user configuration just to improve a test score.

To qualify implemented UI behavior, promote a relevant case into the product's
existing component/browser test setup with deterministic data. Start from the
actual trigger and assert the user-visible outcome, including its valid control.
Use existing screenshot/accessibility tooling where appropriate. A screenshot
diff can preserve a bad baseline, and a code assertion can pass while the action
is inaccessible. No new testing framework or cloud upload is implied here.

Use the practical specifications when the claim concerns finding and fixing a
defect, not merely explaining supplied facts. Agree a bounded run count and use
the actual before/candidate skill bytes plus the ordinary-instructions baseline
where useful. Do not automatically run every case on every model or spawn roles.
Prefer fewer causally discriminating tasks to a large repetition of known answers.

Report only established levels: package validated, decision walkthrough,
independent decision execution, discovered by the client, implemented behavior,
or supported old/new comparison. A manual walkthrough is self-review. JSON and
link checks establish corpus integrity, not decision quality.

## Method references

- [Skill iteration and prior-version baselines](https://github.com/anthropics/skills/blob/main/skills/skill-creator/SKILL.md)
- [Playwright: user-visible behavior](https://playwright.dev/docs/best-practices)
- [Storybook: interaction tests](https://storybook.js.org/docs/writing-tests/interaction-testing)

These references explain methods; their scripts, agents, services and package
installation instructions are not part of this evaluation contract.

C31/C32 preserve intentional familiar styling while requiring correction of
actual visual/interaction defects. These are decision controls, not renderer tests.
