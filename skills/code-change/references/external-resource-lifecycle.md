# External resource lifecycle

Use when implementation or its test harness acquires a process, connection,
subscription, temporary configuration or another resource whose effects outlive
a function call. Ordinary pure transformations need none of this procedure.

## Identify acquisition and ownership

Inspect the actual SDK and supported lifecycle before choosing a wrapper. Name
the acquisition boundary, resource identity, owner, consumers and release action.
Distinguish a resource created by this operation from one it merely connects to.
A transport's disposal can terminate its child process; closing a connection is
not evidence that every process or remote effect ended.

Keep ownership observable as soon as acquisition succeeds, before a later
connection or initialization can fail. Use a supported handle or identity that
cannot accidentally select a replacement resource; a name or unverified PID is
insufficient. Pair release with the acquired resource, rather than placing all
cleanup after the last successful setup step. Partial external effects may exist
even when the acquisition call reports failure.

For temporary configuration, establish exact owned fields, original state and a
supported restore path before mutation. Restore must preserve intervening foreign
changes outside that boundary. If complete restoration cannot be established,
retain the evidence and report the specific residue instead of claiming cleanup.

## Exercise relevant failure transitions

Select transitions affected by the change, using task-owned resources and the
existing test runner. Do not impose a full matrix on an unrelated local edit.

| Transition | Required observation |
| --- | --- |
| Resource acquired, later setup fails | Acquired resource is released or explicitly retained with its owner and reason |
| Caller times out or requests cancellation | Observe whether the worker stopped and its effects ceased; a cancelled await is narrower evidence |
| Shutdown or transport disposal | Intended owned resources end; connected foreign resources remain available |
| Cleanup itself fails | Preserve the primary failure and cleanup failure, identify residue, and establish the next safe action |
| Temporary state is restored | Inspect the owned state through its supported read path; unrelated state remains intact |
| Fixture recovery fails | Treat dependent results as unavailable until fixture health is re-established |

Give required cleanup a bounded opportunity after the main operation's deadline,
using the framework's supported cancellation/timeout semantics. An already
cancelled token may prevent cleanup from running. No universal grace period or
permission to force-kill a foreign process follows.

For lost replies, interrupted operations or reconnect/retry, use
[continuation's reconciliation rule](../../implementation-planning/references/continuation.md#reconcile-before-continuing).
This procedure verifies resource state; planning owns whether the recorded work
and effects may be continued or repeated under present authority.

## Keep fault injection and evidence bounded

Inject faults into isolated copies or owned resources. Verify the affected
fixture is healthy before using later failures as evidence about the product.
An immutable input directory or fresh context does not isolate a database,
installed package, shared port or native process.

Acceptance identifies the actual artifact and relevant data/configuration,
operation, observation and remaining resources. A read event, successful dispose
call or old PASS is not the observation. Retain a normal successful control and
a relevant foreign-resource or unrelated-state control when those guarantees
are load-bearing. Use [test writing](../../test-writing/SKILL.md) for independent
expectations and real-boundary assertions; no new process manager or harness is
required by this method.
