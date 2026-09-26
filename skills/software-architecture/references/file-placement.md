# File placement and boundaries

Use to place new code, extract a responsibility or review a proposed structure.
Choose by ownership and the project's contracts, not file size or a fashionable tree.

## Decide in order

1. Establish framework/build constraints first: special route files, client/server
   execution, loading/registration, generated inputs, public package exports and
   supported paths. Verify the installed version for material framework semantics.
2. Identify the decision or operation, its reasons for change, consumers, state owner
   and lifetime. Follow actual dependencies rather than inferring them from names.
3. Try the narrowest existing owner. Colocate a helper with its consumer when that
   keeps the responsibility coherent and respects the dependency contract.
4. Extract a neighboring module when it hides meaningful complexity, isolates a
   lifecycle or gives a consumer a coherent operation. One consumer can be sufficient;
   merely spreading the same state and decisions across files is not an improvement.
5. Share code when consumers require the same semantics and compatible lifecycle.
   A known common invariant can deserve one owner before reuse bugs occur. Similar
   markup or identical current expressions alone do not demonstrate common ownership.
6. Consider a separate package, deployment or repository only for an additional real
   distribution, release, isolation or operating need. Multiple importers alone are
   not evidence for independent operation.

Make the chosen boundary's interface and consumer changes explicit. Keep orchestration,
business rules and presentation distinguishable where their responsibilities differ;
do not create empty layers ahead of requirements. `shared`, `utils` and `services`
are labels, not residual owners for code whose meaning has not been established.

## Evaluate both sides of extraction

Inspect the new unit together with its callers. What knowledge does it remove from
them? Can its owned rule or lifecycle change without coordinated edits elsewhere?
Passing an entire page's mutable state and many setters can preserve the original
coupling while only shortening the page.

A forwarding facade may protect a supported public contract, policy or replaceable
boundary; it needs no arbitrary minimum size or second adapter. Remove indirection
that no longer serves the task. Preserve a coherent large unit when splitting adds
coordination without benefit. Explicit project limits
remain applicable, but numerical size or coupling heuristics are not defect evidence
on their own. An import is a violation only under an applicable contract or supported
harmful dependency, not because a generic diagram would put it on another layer.

Distinguish reuse from synchronized truth. A cache, editable draft, generated view or
adapter can be legitimate when ownership, propagation and invalidation are clear.
Separate instances can use the same implementation without sharing mutable state.

## Express a real public surface

Choose interfaces that reveal inputs, outputs, failure and mutation authority without
exposing unrelated internals. A boundary may use exports, a function interface, routing
or registration; do not require `index.ts` in every directory. Account for aliases,
re-exports, type-only dependencies and runtime loading according to the actual contract.
Type-only does not grant an automatic exemption from a project dependency rule.

Use [FSD](fsd-profile.md) only under its adoption conditions. Vue implementation details
remain in [Vue structure](../../code-change/references/vue-structure.md). Other
frameworks use their own versioned contracts; do not infer a route from every colocated
file or dead code from the absence of a normal importer.

## Preserve consumers during moves

This method decides the target placement and which surface stays supported; what a
move must preserve and check follows the implementation method's
[structural-contract criteria](../../code-change/references/reuse-and-migration.md#preserve-structural-and-public-contracts).
Return the ownership reason, concrete placement, affected contracts and check; do not
silently refactor the application in response to a placement question.
