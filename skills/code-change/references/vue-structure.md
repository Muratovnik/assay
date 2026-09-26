# Vue structure

Use for component responsibility, reactive ownership and composable boundaries.
Use the [architecture method](../../software-architecture/SKILL.md) for material
ownership and placement decisions; this procedure owns their Vue implementation
detail without choosing a product's folder architecture.

## Component and composable boundaries

Keep a component's rendered purpose and the operations it coordinates legible.
Extract a child when it owns a coherent UI interaction, not merely because a
template has several sections. Keep the parent responsible for composition;
avoid a chain of prop/event forwarding layers with no useful boundary.

Use a composable for reusable or independently owned reactive behavior and
lifecycle. Give it a focused interface that makes dependencies, returned state,
mutations and cleanup visible. Pure transformations can remain ordinary
functions. A huge composable receiving the whole component's state can preserve
the original coupling while only shortening the SFC.

Trace important operations through UI, state and domain owners. Keep application
rules out of presentation helpers when they serve other consumers. Place code
by real ownership and the project's import contract, not an imposed FSD layout
or a rule that every component needs a model file.

Vue documents composable
[extraction for code organization](https://vuejs.org/guide/reusability/composables.html#extracting-composables-for-code-organization),
not only reuse, so a local composable can own one consumer's upload, cancellation
and cleanup without moving to a global shared layer.

## Reactive ownership and lifecycle

Prefer a minimal authoritative state and computed derivations. Use watchers for
effects or necessary synchronization with an explicit reason; do not create
parallel writable representations merely to avoid deriving a value. Drafts,
caches and external synchronization need their own reconciliation contract.

Use explicit props/events for parent-child contracts. For shared injected state,
make the provider and supported mutation actions clear. Module-level reactive
state intentionally shares a lifetime: distinguish that from per-instance state,
especially across remounts, tests and server requests. Verify the relevant Vue
version before relying on reactivity, destructuring or script-context behavior.

For SSR, trace whether mutable user/session state is created per request or shared
by the server process; a module singleton can cause
[cross-request state pollution](https://vuejs.org/guide/scaling-up/ssr.html#cross-request-state-pollution).
An immutable shared lookup table or intentional client-app state is a different
case. Do not prescribe a new state library without examining the existing owner.

Subscriptions, listeners and asynchronous work belong to a lifecycle with cleanup
and handling for stale completion where it can affect the user. The operational
UI method's [data lifecycle](../../ui-delivery/references/data-lifecycle.md)
owns detailed user-visible pending, failure, retry and invalidation behavior.

## Styles and SFC boundaries

Keep component-specific styles with the component by default. Extract shared
tokens, themes or reusable style assets when they have a real shared consumer;
preserve scoping, cascade and build behavior. An external scoped stylesheet can
be legitimate under a project convention. Moving it only to meet a line target
does not demonstrate simpler responsibility.

Do not split script contexts or introduce a shared helper solely because a lint
error appears. Trace the actual rule and installed framework/compiler support.
Vue supports limited use of a normal script alongside script setup; check the
[documented constraints](https://vuejs.org/api/sfc-script-setup.html#usage-alongside-normal-script)
for the actual use instead of declaring the combination impossible.

Preserve component contracts during extraction: props, emitted payloads,
slots, focus/selection behavior, async effects and exposed interfaces as relevant.
Tests and runner selection belong to the testing method; do not adopt a test
library or copy version-sensitive browser configuration from a generic example.
