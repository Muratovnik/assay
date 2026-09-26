# Product-flow mapping: research transfer

Decision: implement a reusable method for reconstructing existing journeys and
mapping them to controls, states and evidence. This is not a new crawler,
product-design system or test framework. Baseline: Assay
`28fd8817fcc408d07fbfd2ac7ad47c4fd9ae218a`; research carried forward from the
2026-09-26 design discussion. Vendor tools were not run in a comparative trial.

| Source / method | Transfer | Local owner / discriminating check |
| --- | --- | --- |
| [NN/g task analysis](https://www.nngroup.com/articles/task-analysis/) | Recover goals and context, without inferring actual user needs solely from controls. | Discovery; label inferred goals and keep an independent inventory. |
| [NN/g wireflows](https://www.nngroup.com/articles/wireflows/) | Combine screen context with actions and state transitions. | Handoff; same-URL dialogs and unchanged-screen exports survive. |
| [NN/g prototype specifications](https://www.nngroup.com/articles/prototype-specifications/) | Describe functional consequences alongside pictures. | Paired frames; reader can find prerequisites, effect and recovery without code. |
| [Flow Canvas](https://github.com/Nayat44/flow-canvas) | Adapt action-linked images and stable state/transition IDs. | Evidence and handoff; do not adopt code-always-wins or an injected application route. |
| [UX Flow Designer](https://github.com/ThomasPraun/ux-flow-designer) | Adapt goal, precondition, alternate-path and screen-index structure. | Scenario template; reject mandatory prototype creation for documentation. |
| [Scribe](https://get.scribehow.com/) and [Folge](https://folge.me/) | Recorded action/image pairs are useful draft material; portable local output is useful. | Do not treat a recorded happy path as a complete inventory or require a vendor subscription. |
| [Overflow](https://overflow.io/) and [Supademo](https://docs.supademo.com/customize/chapters/conditional-branching) | Navigable maps and explicit alternatives. | Handoff; branch presentation is not proof the product supports the branch. |
| [Playwright test agents](https://playwright.dev/docs/test-agents) and [traces](https://playwright.dev/docs/trace-viewer) | Reuse existing exploration/observation and fixtures. | Existing browser-checks owner; do not install another runner or auto-generate tests. |
| [Feature-Driven End-to-End Test Generation](https://arxiv.org/html/2408.01894v2) | Treat generated functions as candidates requiring validation. | Inventory and evidence; count supported outcomes, not generated cards. |
| [Temac](https://arxiv.org/html/2506.00520v1) | Breadth followed by targeted exploration of gaps. | Discovery; reject merging distinct actions or dropping self-transitions. |

These sources support design choices, not numerical quality/savings claims for
Assay. Research on automatic test exploration does not validate a designer handoff.
Source revisions and platform capability need rechecking when they affect an actual
adapter operation; historical links do not prove today's command availability.

## Ownership and concrete consumers

operations-ui-delivery already requires broad scenario mapping before acceptance;
it now delegates reconstruction and designer-facing inventory to this skill and
retains UI quality/capture/canvas criteria. test-writing consumes the same model
with expected-behavior authority separate from observations. Its oracle rules
remain unchanged. See the [two concrete handoff views](../../skills/product-flow-mapping/examples/consumer-handoffs.md).

The standard-library helper is optional: it validates references and declared
provenance, exports offline paired pages plus an adapter-neutral handoff manifest,
and compares snapshots. It cannot establish semantic completeness, execute a
browser trace, detect all secrets or claim a Figma write. A small task remains
ordinary prose. No provider, model, daemon, paid service or second task store is
introduced.

## Evaluation and transfer boundary

The [evaluation protocol](../../skills/product-flow-mapping/evals/evaluation.md)
separates authored, structurally checked, discovered and behaviorally exercised
results. Fresh client comparisons remain unexecuted until a receipt says otherwise.
The examples are synthetic. No live Routevane UI or physical device was exercised
as part of authoring this skill.
