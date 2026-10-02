# Workflow transition probes

Coordinator data for the collection, not instructions to an executor doing a
user task. `workflow-cases.json` contains synthetic public working inputs;
`workflow-rubric.json` and `workflow-case-metadata.json` stay with the evaluator.
The first twelve inputs assess decisions under a present read-only request.
WF-13 exercises a bounded edit and unnecessary activation. These inputs do not
execute a native workload or establish behavior during real dispatch.

## Protected decisions

| Family | Invalid / nearby valid control | Owning procedure |
| --- | --- | --- |
| Readiness | Proposed/mock probe / current real-boundary observation | Planning units; delegation planning |
| Integration | Fabricated matching IDs / actual producer and opaque identity | Test-writing boundary choices |
| Lifecycle | Partial setup and unconfirmed cancellation / release only the owned subscription | Code-change external resource lifecycle |
| Replay | Completed effect with lost reply / verified rollback and permitted retry | Planning continuation |
| Acceptance | Unrelated or stale proof / current consumer-entry evidence | Evaluation calibration; owner tests |
| Combined transition | Contract drift, uncertain effect, compaction and narrowed authority | Relevant owners together |
| Repair | Wrong expectation and unhealthy fixture / causal diagnosis | Diagnostic reproducer; outcome and repair |
| Small task | One typo / unnecessary ceremony | Ordinary authoring; activation control |

Related invalid/valid cases share metadata groups. WF-11, WF-12 and WF-13 have
distinct groups. All cases are public development evidence, never a sealed final
population or an estimate of incident frequency. Reserve different groups outside
this repository for independent final evidence; a public label cannot seal them.

## Run and inspect

1. Freeze baseline/candidate bytes, collection, invocation route, instructions,
   permissions and model settings. Use ordinary discovery when testing selection;
   explicit loading proves only that route. Do not activate skill-evaluation in
   the executor merely because it stores these coordinator inputs.
2. Prepare one input-only packet with `tools/eval_assets.py prepare`. Retain the
   manifest digest outside it. Exclude rubric, metadata, earlier answers and
   reachable source/history copies of keys; record effective access limits.
3. Compare under comparable conditions. Keep incomplete runs and disagreements.
   Grade atomic criteria against decisive observations. Equivalent supported
   answers can pass; no exact wording or tool sequence is required.
4. Missing traces leave effects or discovery unverified. Reading a reference,
   printing PASS or matching final bytes cannot prove transient behavior. Decision
   cases support decision claims; execution claims require an authorized workload
   with observable effects.
5. Record false acceptance/rejection and full-chain cost: briefing, repair,
   verification and compaction. Separate user/external waits and critical-path
   time from accumulated worker durations. Compare relevant component omissions
   and the small-task control before attributing changes to an added stage.

Use the existing [paired pilot](../references/paired-pilot.md) and
[evaluation design](../references/eval-design.md), including calibration and
stopping criteria. These resources supply no runner, delegation authority, paid
campaign or universal score threshold. No model results are bundled here.

## Research and transfer boundary

- [Superpowers](https://github.com/obra/superpowers/blob/main/skills/subagent-driven-development/SKILL.md):
  bounded handoffs and scoped repair review; retain risk-based review and Assay's
  existing causal retry rule.
- [GSD Core](https://github.com/open-gsd/gsd-core/blob/main/docs/how-to/plan-a-phase.md):
  thin consumer scenario and gap-only replan; use the existing owning plan and
  only the unresolved boundary.
- [Spec Kit](https://github.github.io/spec-kit/reference/agentic-sdd.html):
  artifact consistency and gap convergence; agreement still needs independent
  behavioral acceptance.
- [LangGraph](https://docs.langchain.com/oss/python/langgraph/interrupts):
  interrupted nodes can replay effects; route to existing planning reconciliation.
- [Temporal](https://docs.temporal.io/activity-execution): cooperative cancellation;
  verify observed termination through the actual resource owner's mechanism.
- [pytest](https://docs.pytest.org/en/stable/how-to/fixtures.html#safe-fixture-structure):
  acquisition paired with teardown; external failures may still have partial effects.
- [Anthropic harness design](https://www.anthropic.com/engineering/harness-design-long-running-apps)
  and [agent evaluation](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents):
  consumer observations, calibrated grading and removal of unnecessary stages;
  these justify comparisons, not measured gains for Assay.
- [MCP tools](https://modelcontextprotocol.io/specification/2025-11-25/server/tools):
  visible schemas and actionable errors; check the installed SDK through actual
  stdio calls. An annotation does not establish effects or authority.

No external framework is required or installed by these probes.
