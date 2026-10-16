# Variant analysis

Use after a defect is confirmed (its cause is established by a reproducer or by
source) and the cause is a mistaken assumption that other code could share. Skip
it for an unconfirmed symptom, which belongs to
[diagnostic reproducers](diagnostic-reproducer.md) first, and for a cause that is
unique to one call site, such as a mistyped constant. This is a bounded search
for sibling occurrences, not a repository-wide audit or a licence to repair
outside the agreed write scope.

## State the cause as a rule

Write down the violated assumption in terms of meaning, not text: what must hold,
which code relies on it and which input or state breaks it. "A truthiness test
treats a legitimate zero as absent" describes a class of mistakes; the one
expression that was fixed describes a single spelling of it. Record the evidence
that the cause, rather than a coincidence, produced the failure.

## Build a query that finds the seed

Express the rule as one or more searches: text, structure-aware or reference
queries, type-based lookups, or reading every caller of the affected operation.
Run each against the original defect first. A query that misses the known case
cannot be trusted to find unknown ones; a query that returns most of the
codebase needs a narrower condition, not a quick skim.

## Widen one dimension at a time

Change one thing per round so a hit or a miss stays interpretable:

- other spellings of the same mistake (a default operator, a coercion, a helper
  that wraps the check);
- other routes to the same state or contract, such as sibling entry points,
  adapters, fallbacks and the compatibility path;
- other consumers of the same value or format;
- other places the rule is restated: migrations, generated or copied code,
  configuration, documentation and tests.

Keep test code in the search when the defect concerns tests (shared state,
isolation, fixtures). Excluding it would remove the subject.

## Judge each candidate by context

A pattern match does not prove the cause. For each candidate establish whether
the vulnerable input can reach it, what the value domain actually is, whether a
caller guarantees the condition and whether a later boundary normalizes the value
deliberately. Classify it as confirmed, plausible but not demonstrated, or excluded,
and keep the evidence behind an exclusion. Unreachable code is a note, not a
finding. No match does not prove absence: say which queries and dimensions were
covered.

## Close the sweep

Repair confirmed variants only inside the authorized scope and report the rest to
the owner. Make the check that protects the fix discriminate the original case and
at least one variant, using [test-writing](../../test-writing/SKILL.md) for the
oracle. When the same mistake keeps being easy to make, name that as an interface
question for the owner; changing the interface is a
[design decision](../../software-architecture/SKILL.md), not part of the sweep.
Report the rule, the queries and dimensions searched, confirmed variants, excluded
candidates with reasons, unresolved candidates and the coverage limit. An audit of
such a sweep uses its
[completeness criteria](../../independent-audit/references/evidence-and-probes.md#reconcile-claims-with-receipts).

A required CI rule, a fixed noise ratio and automatic delegation are not part of
this method; a recurring pattern may deserve a rule if the owner decides so.

## Method references

- [Trail of Bits variant analysis](https://github.com/trailofbits/skills/blob/d3323cefbcf645678b8dc481de204b02ad3d02dc/plugins/variant-analysis/skills/variant-analysis/SKILL.md)
  studies the same seed-to-pattern workflow; it is a reference, not a dependency.
