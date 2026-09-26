# Product-flow mapping: research transfer

Decision: implement a reusable method for reconstructing existing journeys and
mapping them to controls, states and evidence. Baseline: Assay
`28fd8817fcc408d07fbfd2ac7ad47c4fd9ae218a`; research carried forward from the
2026-09-26 design discussion. Vendor tools were not run in a comparative trial.
The owner's subsequent correction requires direct reuse of the existing tools,
not a new capture, rendering or export system inside this skill.

| Source / method | Transfer | Local owner / distinguishing check |
| --- | --- | --- |
| [NN/g task analysis](https://www.nngroup.com/articles/task-analysis/) | Recover goals and context without inferring actual user needs solely from controls. | Discovery; label inferred goals and keep an independent inventory. |
| [NN/g wireflows](https://www.nngroup.com/articles/wireflows/) | Combine screen context with actions and state changes. | Handoff; same-URL dialogs and unchanged-screen actions survive. |
| [NN/g prototype specifications](https://www.nngroup.com/articles/prototype-specifications/) | Explain consequences alongside pictures. | Paired frames; the reader finds prerequisites, effects and recovery without code. |
| [Flow Canvas](https://github.com/Nayat44/flow-canvas) | Adapt action-linked images and stable scenario references. | Use the idea, not its renderer or app injection; code does not always override requirements. |
| [UX Flow Designer](https://github.com/ThomasPraun/ux-flow-designer) | Adapt goals, preconditions, alternatives and the screen index. | Writing aid; reject mandatory prototype creation for documentation. |
| [Scribe](https://get.scribehow.com/) and [Folge](https://folge.me/) | Action/image pairs can support an explanation. | Recording one path does not establish coverage or justify adopting/recreating a recording product. |
| [Overflow](https://overflow.io/) and [Supademo](https://docs.supademo.com/customize/chapters/conditional-branching) | Navigable paths and explicit alternatives. | Branch presentation is not proof of supported behavior. |
| [Playwright screenshots](https://playwright.dev/docs/screenshots), [traces](https://playwright.dev/docs/trace-viewer) and [reporters](https://playwright.dev/docs/test-reporters#html-reporter) | Reuse available capture/inspection and existing fixtures. | Browser-checks owner; no new recorder, renderer or report framework. Test reports do not replace the requested Figma file. |
| [Existing Figwright procedure](../../skills/operations-ui-delivery/references/figwright.md) | Use the established adapter and its installed vendor documentation. | Direct authorized frame/image/annotation operations and readback; no intermediary exporter. |
| [Feature-Driven End-to-End Test Generation](https://arxiv.org/html/2408.01894v2) | Treat generated functions as candidates to check. | Inventory and evidence; count supported outcomes, not generated cards. |
| [Temac](https://arxiv.org/html/2506.00520v1) | Breadth followed by targeted gaps. | Discovery; retain distinct actions and self-transitions. |

These sources support method choices, not measured quality or savings for Assay.
Automatic test exploration does not itself validate designer comprehension.
Historical links do not establish the command set available in a particular
session; the installed tool documentation and exposed schemas govern operations.

## Ownership and consumers

operations-ui-delivery delegates reconstruction and the designer-facing inventory
to this method, retaining UI quality, capture and canvas criteria. test-writing
consumes the same scenario with requirement authority separate from observations;
its oracle rules remain unchanged. See the
[two handoff views](../../skills/product-flow-mapping/examples/consumer-handoffs.md).

The earlier implementation introduced an optional standard-library exporter and
its own map format. That was an unjustified expansion: a standalone viewer and
interchange layer were not needed for the requested method and Figma handoff.
They are removed, including their validator, examples and export-only tests.
Useful lessons from their review remain presentation/evidence criteria, not code.

Playwright/browser tools supply observations; Figwright supplies Figma operations.
The skill supplies the scenario explanation, coverage reasoning and evidence
limits. Existing project notes are sufficient for working records. No new CLI,
schema, service, provider, model or task store is required. A missing connection
remains a stated limitation, not permission to recreate its capabilities.

## Evaluation boundary

The [evaluation protocol](../../skills/product-flow-mapping/evals/evaluation.md)
separates packaging checks from actual discovery and behavior evidence. The
examples and corpus are synthetic. Fresh comparisons need their own receipts;
no live Routevane UI, Figma handoff or physical device was exercised by authoring
these instructions.
