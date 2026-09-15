# Data lifecycle in the visible UI

Use for async counts, forecasts, derived summaries, refresh, writes/retries and
shared-data invalidation. A correct query or state store does not establish a truthful UI:
follow the result to every affected visible consumer.

## Identify what the result describes

Establish the relevant object/composition, target or format, source revision,
coverage and freshness. Use the product's existing state and cache mechanisms.
The same selected IDs can yield different results after a source update or
target change. Verify suspicious values against their meaning and actual input:
zero can be correct; missing or partial observations do not establish zero.

Do not add a cache library, automatic external refresh or new backend semantics
to avoid resolving the existing contract. An explicit refresh action has an
object scope and may have external effects; reuse the authorized owner path.

## Establish that a valid result is reachable

For computed counts or forecasts, follow input → eligibility → calculation →
visible consumer. Identify what makes the inputs sufficient under the product
contract and verify a known result from such inputs. A message saying that data
is insufficient is not successful acceptance merely because it renders cleanly.

- Failure: sufficient inputs always show an unavailable state; a test only checks
  the label or injects the final answer, bypassing eligibility and computation.
- Decision: find the first broken boundary and repair its owner within scope.
  Distinguish result value, input coverage, freshness and request state; these
  can vary independently and need not fit one mutually exclusive enum.
- Check: use deterministic sufficient inputs with an independently known result,
  then truly insufficient inputs. Supply or repair the missing prerequisite
  through the supported path and observe the result without a test-only reload.
  An injected response can test presentation but cannot qualify the calculation
  path. Pair a focused arithmetic check with the composed path where necessary.
- Valid control: a computed zero, an explicitly limited partial result and a
  genuinely unmet prerequisite can all be correct. Do not fabricate values,
  invent deadlines or add polling/external refresh to make every state succeed.

For example, synthetic sets with a known shared member and disjoint sets
distinguish a nonzero intersection from a true zero. Keep the actual formula,
eligibility and recovery policy in the owning product. User-facing state meanings
and supported next steps belong in [content and recovery](content-and-recovery.md).

## Separate initial loading from refreshing

For a refresh of the same context, retain the last applicable result with
understandable freshness or failure feedback where needed. Avoid replacing it
with a blank, zero or full loading skeleton solely because a request started.
During a changed context, do not present the previous object's or target's result
as current. Clear it, label it as a previous result, or use another product-defined
transition that preserves that distinction. Empty and unavailable remain separate.

- Failure: the producer retains a valid count during refresh but its table
  returns no value whenever pending is true, making the count blink.
- Decision: define the visible transition, then reconcile request state and
  presentation. A retained array alone does not satisfy that contract.
- Valid control: after switching to another target, hiding the old count while
  the new one loads can be correct. Do not fix blinking by showing stale numbers
  without their old identity, or by hiding all refresh feedback.
- Check: hold a response pending; observe before, during and after success or
  failure. Also change context and let an older response arrive last. Verify
  the visible values, attribution and available actions, not only stored data.

When rows replace the object inside an already open panel, test that transition
separately from opening the panel. Switch A → B → A with controlled pending,
failure and late responses. Inspect identity, content, controls and geometry
during loading, not only after settlement. A temporary empty body or placeholder
can collapse and re-expand the panel even when final data is correct. Preserve
appropriate shell anchors or placeholder space without displaying A as B or
retaining an action bound to the wrong object. Respect intended content reflow
and product-defined scroll/focus changes; do not freeze every panel height or
mask the problem with a delay. Use [Interaction](interaction-and-layout.md#design-geometry-across-transitions)
for affected geometry and [Motion](motion-and-transitions.md) when animated.

## Reconcile writes and retries

Bind a write to its intended object and submitted revision, distinguishing its
pending result from any newer draft. Route pointer and keyboard activation through
the same operation owner. Prevent duplicate effects where repetition is not
intended; a loading style alone is insufficient. Scope pending restrictions to
the affected operation rather than locking unrelated work.

Use the existing mutation/conflict contract. On optimistic failure, reconcile the
affected change without rolling back newer valid edits or unrelated successes.
A timeout or lost response may leave the server outcome unknown: do not announce
confirmed failure or blindly repeat a non-idempotent operation. Use supported
status lookup, retry identity or reconciliation; report the unresolved outcome
when the owner provides no safe way to determine it. No new backend protocol,
automatic retries or idempotency service is implied by this procedure.

- Check: repeat activation by click and Enter while pending and count actual
  effects; fail an optimistic update; edit again before the old save completes;
  exercise a conflict and a lost response when supported. Inspect committed data,
  draft and feedback, not just request completion. Include recovery or cancel
  only according to the operation's actual capabilities.
- Valid control: independent writes may run concurrently. A rejected old version
  may require explicit reconciliation rather than automatic merging. Cancelling
  a local wait does not establish that the server operation was cancelled.

For draft departure use [Actions](actions-and-scope.md#preserve-drafts-across-departure);
for the submission trigger use [Forms](forms-and-input.md#give-submission-one-owner).

## Trace invalidation through consumers

Follow source mutation → invalidation → request → result state → presentation.
Include consumers already open elsewhere when the product requires them to
update. Determine the existing signals, such as save completion, source revision
or return/focus refresh; do not introduce global polling by default.

- Failure: refreshing a library source leaves a composing screen's count stale
  because its request depends only on selected IDs. A unit test of refresh passes.
- Decision: use the existing state owner to notify the affected consumers and
  reject late results that no longer describe their current context.
- Valid control: local row density or an explicitly frozen snapshot should not
  automatically refresh shared data. Check the agreed propagation boundary.
- Check: start from the place the user encounters the need, perform the allowed
  update, and inspect the consuming view without a test-only reload that repairs
  propagation. Test direct entry/reload separately when initialization is affected.

Use the existing test harness to control response order, delay and failure with
deterministic data. Observe risky intermediate states before waiting for final
settlement. A resting screenshot or waiting until the network is idle can miss
the transition under review. Reuse focused model tests for arithmetic and request
ordering; add composed checks where producer and consumer can disagree.

## Method references

- [Cloudscape: loading, refreshing and partial failure](https://cloudscape.design/patterns/general/loading-and-refreshing/)
- [Impeccable: concurrent and failed mutations](https://github.com/pbakaus/impeccable/blob/4bee58d89e4b3d3b4a1c44cfd2445dce03cf09e6/.agents/skills/impeccable/reference/harden.md)
- [Test design: input classes and state transitions](https://github.com/stellarlinkco/myclaude/blob/f2e75c1263a2d5f09cdc4bb3dfe3635c635ff296/skills/test-cases/references/testing-principles.md)
- [Storybook: controlled network responses](https://storybook.js.org/docs/writing-stories/mocking-data-and-modules/mocking-network-requests)
- [Playwright: assertions for readiness rather than network idle](https://playwright.dev/docs/api/class-page#page-wait-for-load-state)

These are behavior and testing references, not permission to install their stack.
