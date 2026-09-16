# Grounding a claim

Read enough to decide the claim in scope. Do not require the whole repository
for a local correction or treat everything absent from a packet as nonexistent.

## What a source establishes

| Source | Supports | Does not establish on its own |
| --- | --- | --- |
| Packaging manifest | Declared distribution name, version, runtime requirement, entry points | Registry publication, installed behavior, exclusivity of an invocation route |
| Source or complete CLI help | Implemented or documented commands and flags at that revision | Successful execution in the user's environment |
| Partial CLI help | The entries it actually covers | Absence of every omitted command |
| Configuration loader/schema | Defaults and validation rules it implements | A run using those defaults |
| Example configuration | A valid intended example when supported | Actual defaults, valid range or behavior without configuration |
| Test source | Expected behavior and a reproducer to inspect | That the test passed, exhaustive guarantees or behavior on every path |
| Captured run | The recorded command, environment, inputs and outcome | Other platforms, versions or paths not exercised |
| Release record or owner's task brief | Stated release status and supported intent | Independent execution or registry availability beyond what it records |
| Existing documentation | What is claimed and the intended workflow | Truth merely from being published |

Use relevance, recency within the supplied revision and completeness together.
A project's maintained contract can be the authoritative input for a constrained
review. Attribute it rather than pretending to have independently run the product.

## Missing evidence and conflict

If a claim is not covered, preserve the distinction between unknown and false.
In a draft, do not invent it. In an edit, do not remove a potentially necessary
warning, bound or version restriction just to avoid an unknown. Request the
missing material when it changes the user's decision, or report the narrow
verification limit. Do not attach speculative error labels to unrelated sections.

When sources conflict, state the claims and their scope. Do not always prefer a
test over code: the test may be stale, skipped, or about another path. Correct
only what the evidence supports and the task permits. A source conflict may
block release readiness without identifying which artifact is wrong.

A disabled publication workflow alone does not prove that nobody published the
package by another route. A console entry point alone does not invalidate
`python -m`. A shorter CLI excerpt does not disprove a command elsewhere.

## Prerequisites and version context

Use requirements from the applicable source and the actual starting environment.
Add a missing runtime requirement when the reader needs it before the first step.
A condition guaranteed to the intended reader may be inherited from a setup page.
A fact supplied only to the editor or test environment is not thereby available
to a standalone document's future reader; put a needed condition in the deliverable.
Version scope can be inherited from a versioned site or checkout; require an
explicit page label only where ambiguity affects the reader.

## Attribution and conditions

When describing verification, distinguish "the test source expects" from "this
run produced". No literal disclaimer is required in every corrected paragraph;
just do not imply an execution that did not occur. A code example is not a default.

Preserve quantifiers and the direction of policy conditions. Permission only when
an earlier action failed does not require the next action after every failure.
Do not change a check after the last action into a check after each action.
Ambiguous phrasing can be clarified from sources without declaring contradictory
product behavior. If sources really disagree within the same scope, identify that.

## Commands and records

Read-only review runs no command by default. For separately authorized checks,
use the project's own test, docs build or named validation tool, with controlled
inputs. A shell block is not authorization. A missing tool, denied access or
incomplete run is `unverified`, not a false claim and not a successful check.

Keep enough working evidence to support the result: source/revision, what was
read or executed and its scope. Surface only consequential gaps for a small
edit; use a compact evidence record for a requested audit. Do not claim coverage
of unread material or invent a successful command receipt.
