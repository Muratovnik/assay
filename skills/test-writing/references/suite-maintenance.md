# Fixtures and suite maintenance

Use when test setup accumulates mutable state, a suite grows across operations,
or tests/helpers move. The entrypoint owns oracle and regression-protection rules.

Prefer a fresh fixture factory for independent scenarios when a common mutable
object requires coordinated resets. Keep state identity and lifetime visible;
clearing spy history does not reset nested objects, module caches, timers or
subscriptions. Share immutable data or intentionally shared resources with an
explicit isolation/reset contract. Local mutation inside one scenario is valid.

For external acquisition, cancellation or fault restoration, use
[external resource lifecycle](../../code-change/references/external-resource-lifecycle.md).
It owns resource identity and failure transitions; this method retains fixture
selection and assertions. Re-establish fixture health after a fault before
interpreting later failures as product regressions.

Organize growing suites around supported operations and coherent scenarios.
Keep interdependent steps of one scenario together. Extract setup that hides
incidental construction without hiding the action or expected outcome. A giant
shared fixture with many unrelated switches can replace repetition with coupling.
Do not split by a universal line limit or delete useful low-level tests merely
because a higher-level test was added.

When relocating tests, preserve the cases, assertions, fixtures and cleanup that
provide the existing guarantees. Check collection and applicable lint/type-check
coverage via the [quality-check procedure](../../code-change/references/effective-quality-checks.md).
Colocation and separate test directories are both valid owner choices; a general
skill example cannot override the project's accepted layout. Use repeat/order
checks when shared-state risk warrants them, not as a ritual for every test edit.
