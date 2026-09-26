# Discover the product, not just its pages

Use when the relevant journeys are not already known. A small question can use
one bounded slice; a full redesign needs a scope inventory before card production.

## Recover identity and supported scope

Record the repository/ref or release, actual runtime/build when available, data
conditions and intended audience. Include desktop shell, browser routes, external
hand-offs or command-line steps only when they belong to the requested journey.
An application's name is not evidence of its domain. Reuse product terminology.

Inspect the supplied brief, accepted decisions, documentation and existing tests.
Then inspect navigation, router entries, screens, shared menus, dialogs, handlers
and state owners for the scoped surfaces. A route file inventories URLs, not
all screens; an unused component or backend endpoint is only a candidate action.
Existing tests describe expected behavior, not an executed check.

Do not claim demographics, motivations, frequency or pain from source code.
Label a goal inferred from functionality as inferred. Real research, owner
requirements and observed implementation have different authority.

## Work in both directions

From the top, identify product entities, actors, goals, starting conditions and
recognizable outcomes. From the bottom, enumerate user-visible controls and the
actions they dispatch, including shared controls, hidden menus, keyboard routes,
file/download effects, dialogs and background completion. Resolve each candidate
against reachable consumers and the product's supported environment.

Maintain a compact independent inventory, separate from the written scenarios:

`discovered task/control/state -> source location -> mapped IDs or disposition`

A disposition is mapped, unresolved, or excluded with a reason. A decorative
separator, retired route or deliberately out-of-scope surface can be excluded;
a control whose purpose has not been inspected remains unresolved. Do not silently
remove difficult entries to increase apparent coverage. Whole-product claims
require the examined entry points and exclusions, not an invented global count.

Read enough of a shared control's consumers to identify differences in scope or
result. Describe genuinely identical behavior once, with its actual uses. Do not
copy a whole modal explanation into every scenario or assume identical labels
mean identical effects.

## Explore breadth, then missing branches

Start with a representative goal-to-result path. Compare it with the inventory,
then inspect the consequential branches named by the stage families in
[UI acceptance](../../ui-delivery/references/scenario-testing.md#derive-the-scenario).
Include role, data size, language or platform variations only when they alter the
supported behavior. Use the owner's existing fixtures and browser or runtime
tools without adding a special app route.

State equivalence is functional. Different URLs can show the same task state;
the same URL can contain several materially different states. Keep copy,
download, refresh and external delivery distinct even if the screen is unchanged.
Preserve multiple actions between the same states. Avoid exhaustive permutations
of independent hover, theme, row and text-value differences.

When runtime is unavailable, connect source-backed candidates and mark uncertain
reachability/results. Do not invent recordings or simulate the app without a
label. A reachable route is not proof that a real user can discover it.

## Stop and report the examined boundary

Stop a bounded slice once its inventory has explicit dispositions, material
transitions have evidence or named gaps, and further exploration is unlikely to
change the requested decision. For broad work, revisit omitted consumers and
external exits before calling the inventory reconciled. Never equate this with
all possible paths explored.

Use the requested handoff for durable facts; keep exploratory logs separate when
not useful to the designer. No mandatory PRD or persona exercise.

## Method sources

- [NN/g: task analysis](https://www.nngroup.com/articles/task-analysis/) separates goals and work from a screen list.
- [Feature-Driven End-to-End Test Generation](https://arxiv.org/html/2408.01894v2) motivates checking candidate features rather than trusting generated ones.
- [Temac](https://arxiv.org/html/2506.00520v1) informs broad exploration followed by targeted gaps; its graph simplifications are not adopted here.

These sources motivate investigation, not claims of local coverage or model quality.
