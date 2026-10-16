# Diagnostic reproducers

Use when the cause is unclear, attempts keep changing the symptom, or the
evidence needs to survive a handoff. Without repair authority, start with the
read-only entry; the steps after it apply to both. This is conditional
detail, not another automatic skill or permission to edit production during an
audit. Keep an already justified narrow repair proportional.

## Read-only entry: why does this not work

Use for "why does X not connect, not show up or stay red" and similar, when no
repair is requested, or before a repair of such a symptom. It grants no repair
authority. It follows the steps below with these differences:

- **Find what is in effect before explaining.** Identify the installation,
  configuration layer and process that actually produce the symptom: which
  version and path resolve, which setting won, which running process or session
  serves the request and whether it started before the last change. Read these
  from the live system, not from the files that should apply, earlier notes or
  recall; those are hypotheses until observed.
- **Check availability before saying unavailable.** Run the cheapest observation
  that would show the thing present (list, resolve, status, read-only call) before
  claiming a tool, service, file, permission or route is missing. Report
  separately: absent, present but unreachable from here, present but not loaded
  in this session, and not checked.
- **Stay read-only.** Observe without changing state: no edit, setting change,
  reinstall, restart or stopped process unless the user authorizes it. An action
  that would only test a guess, such as restarting to see whether it recovers, is a
  repair. Name it as the next step and ask.
- **Prefer a distinguishing observation to a trial edit.** Pick the one reading
  that separates the live explanations, as in the boundary probe below, rather
  than changing something and watching the symptom.
- **End with a cause or a bounded hypothesis.** A cause cites what was observed
  and where. Otherwise give the hypotheses still standing, the observation that
  would separate them and what that observation needs authorized. Do not present
  a plausible mechanism as the finding.

A question about how a third-party product is documented to behave is
[evidence-research](../../evidence-research/SKILL.md), not this entry; take its
current-source findings back here only as hypotheses about the local setup.
A request to fix a known defect is an ordinary repair, not this entry.

## Reproducer steps

Start from the reported consumer outcome and the owner contract. Find the
smallest existing test, command, captured request or event replay that exposes
that outcome. A command failing for an unrelated setup problem is not the
reproducer. Read logs and source to build plausible causal explanations; absence
of a fully automated loop does not prohibit reasoning or require speculation.
State which explanations are supported and which still need a distinguishing
observation. Avoid fixed hypothesis counts or automatic architectural escalation
based on the number of attempts.

Different setup errors can leave the same consumer boundary unreached. Before
another costly run or repair handoff, trace the connected prerequisites against
the current inputs and identify the blocking transition. Use
[runtime boundaries](runtime-boundaries.md) when generated inputs, compilation or
staged execution are involved. Carry the furthest verified boundary, remaining
consumer outcome and next distinguishing observation in the existing task; do not
create another progress store. A changed error message or completed local edit
alone does not establish advancement. A probe that eliminates a plausible cause
or verifies a needed prerequisite can be useful progress without a product edit.

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

For a repair, before calling it complete, recheck the original unminimized scenario
and preserve relevant regression protection using
[test-writing](../../test-writing/SKILL.md). When the confirmed cause could recur
elsewhere, continue with [variant analysis](variant-analysis.md). An immediately passing characterization
or a new failure outside write scope is not permission to change the contract.
Remove only task-owned temporary instrumentation, retain decisive private
receipts in the existing evidence location, and report unresolved causes or
verification limits instead of manufacturing a causal conclusion.

The procedure adapts the useful reproducer/minimization/boundary-probe ideas
examined in the non-UI review, not their numerical rules or mandatory orchestration.
Its usefulness on real project incidents still needs an actual comparison;
unit tests of a reproducer classifier do not establish better model debugging.
