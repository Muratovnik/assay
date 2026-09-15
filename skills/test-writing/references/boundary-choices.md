# Boundary choices

Read this when the chosen testing technique risks confusing a contract with an
implementation detail. These are conditional decisions, not smell-based bans.

## Structural checks and interaction assertions

An internal class, helper call, private state field or DOM shape usually is not
the guarantee. Prefer the observable effect at the chosen boundary. Conversely,
a public type/export, serialization format, published CSS hook or deliberate
architecture rule can be the contract. Explain that connection and exercise a
valid alternative and prohibited case where useful. Text scans establish text
properties, not runtime behavior or absence of dynamic use.

Call counts and ordering can be important for a protocol, avoiding duplicate
charges or ensuring a forbidden service is not called. They are incidental when
only the final stored value matters. A spy at an external boundary can observe
a real obligation; asserting on a stub's own configured answer usually cannot.

## Doubles and real effects

Use a real dependency when it is safe, controllable and needed for the claim.
Use a fake, stub or mock to isolate nondeterminism, expense or an error boundary.
Know which production behavior was removed. An in-memory fake can model domain
logic without proving disk durability, transaction semantics or vendor fidelity.
Reuse contract tests or a safe integration check where that difference matters.
Do not require a real paid service merely to avoid mocks.

For persistence, recovery and data safety, observe state through the supported
read/reopen/retry path and inspect prohibited effects. Returning success or
calling a save helper alone is narrower evidence. Inject only the relevant
fault into disposable data; keep the normal control and recovery case intact.

## UI and snapshots

Choose stable user-facing roles/names or explicit test hooks for interaction.
Assert visibility, accessibility, focus, viewport presence and actual state
only when the intended flow requires each. A locator can auto-scroll and a
helper can set focus: observe application-driven transitions before helpers
repair them. Hiding a button does not establish server authorization.

Use focused snapshots for a reviewed expected representation. Keep meaningful
fields precise and control irrelevant volatile fields without masking errors.
Text/DOM snapshots do not establish rendered appearance; screenshots do not
establish saved state or behavior. For an approved visual change, inspect the
changed baseline and preserve unrelated behavioral assertions.

## Properties, examples and operation sequences

Use properties when an independent relation or invariant exists. Check that
generated inputs reach the intended domain and that filters/preconditions do
not remove the interesting boundary or every case. Preserve a concrete example
and a minimized counterexample. A property failure can mean a product defect,
an invalid property or invalid input generation; diagnose before changing code.

Round-trip tests establish agreement between encoder and decoder, not necessarily
external format correctness: both can share a compensating bug. Add a trusted
external vector or independent reference when interoperability is required.
Ordering alone does not prove a sort preserved all elements; derive the full
property from the contract. Algebraic laws also have domains and can be wrong
for overflow or floating-point semantics.

Do not mechanically reject `f(x) == f(x)`: two calls may meaningfully test
determinism of a stateful operation. Comparing a result to the same unchanged
result is different. A no-crash smoke or an expected exception can be a genuine,
narrow assertion even without a conventional equality check.

Use generated action sequences for stateful contracts when they add value over
ordinary examples. Keep interdependent steps inside one scenario and isolate
different test cases. Control clocks, randomness and shared state enough to
reproduce outcomes; an intentional concurrency test is not forbidden merely
because its execution involves scheduling.

## Legacy behavior and changing contracts

For characterization, record what is observed, which consumer might rely on it
and what remains undecided. Do not call the captured result a verified business
requirement. When intent changes, trace affected callers and replace the old
expectation with an approved one. Preserve useful cases rather than regenerating
the suite wholesale from the new implementation.
