# Diagnostic reproducers

Use for an authorized repair when the cause is unclear, attempts keep changing
the symptom, or the evidence needs to survive a handoff. This is conditional
detail, not another automatic skill or permission to edit production during an
audit. Keep an already justified narrow repair proportional.

Start from the reported consumer outcome and the owner contract. Find the
smallest existing test, command, captured request or event replay that exposes
that outcome. A command failing for an unrelated setup problem is not the
reproducer. Read logs and source to build plausible causal explanations; absence
of a fully automated loop does not prohibit reasoning or require speculation.
State which explanations are supported and which still need a distinguishing
observation. Avoid fixed hypothesis counts or automatic architectural escalation
based on the number of attempts.

When safe and useful, reduce irrelevant inputs and steps while rechecking that
the same symptom persists. Probe the boundary that distinguishes the explanations:
for example, whether the input reached a component, whether configuration was
applied, or whether the state transition occurred. Do not log all secrets or make
several unrelated repairs and infer which one worked. Use existing task-owned
fixtures and execution limits; a copied project still has access to host services.

For a regression between known states, use the owner's existing bisection tools
in an authorized disposable checkout. Classify untestable builds separately from
the target failure. If the owner's reproducer compares independently justified
good and bad stdout bytes, limit that oracle to deterministic successful
commands. Classify unfamiliar output, setup failures and timeouts as untestable
(125); use an appropriate project-specific oracle for crashes and performance.
Keep expected bytes and the checker stable across revisions.
See [Git's bisect contract](https://git-scm.com/docs/git-bisect) for skip semantics.

Before calling the repair complete, recheck the original unminimized scenario
and preserve relevant regression protection using
[test-writing](../../test-writing/SKILL.md). An immediately passing characterization
or a new failure outside write scope is not permission to change the contract.
Remove only task-owned temporary instrumentation, retain decisive private
receipts in the existing evidence location, and report unresolved causes or
verification limits instead of manufacturing a causal conclusion.

The procedure adapts the useful reproducer/minimization/boundary-probe ideas
examined in the non-UI review, not their numerical rules or mandatory orchestration.
Its usefulness on real project incidents still needs an actual comparison;
unit tests of a reproducer classifier do not establish better model debugging.
