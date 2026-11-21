# User remarks on a delivered interface

Use when a user remarks on an interface they have been shown or given, before
acting on the remark, and for the class closure of any visual or interaction
repair. A remark is evidence about the product and about the checks that let it
through; fixing the named spot is where the work starts, not where it ends. In
one product, 42 of 94 remarks were against a rule already written down, 9 were
regressions and 43 asked for something no rule said; 28 repeated a class of
defect that had already been named.

## Contents

- [Classify the remark](#classify-the-remark)
- [Against a written rule](#against-a-written-rule)
- [Regression](#regression)
- [New requirement](#new-requirement)
- [Close the defect class](#close-the-defect-class)

## Classify the remark

Decide the kind from the product's written rules and its history, not from how
the remark is worded:

- **rule**: a rule the product already has in writing (its design document, an
  acceptance check, a component contract) says what the remark says;
- **regression**: the behavior was right in an earlier revision and is not now;
- **requirement**: no written rule covers it; the user is stating a new one.

A regression that also breaks a written rule takes both procedures and is
recorded as a regression. When no source settles whether a rule exists, the
remark is a requirement: an unwritten rule is not yet an oracle.

The record of each remark, the tracker step, checklist line or note where the
work tracks it, starts with its kind word and a colon, in the form of the review
[verdict lines](../../route-subagents/references/review-and-continuity.md#state-the-verdict-on-its-own-lines):

```text
rule: section header text starts 6 px right of the row labels at 390 px
regression: the filter menu closes on the first keystroke again
requirement: long project names wrap instead of being cut
```

## Against a written rule

The rule existed, so a check either did not run or ran and missed it. Find why:
the property it did not measure, the state it did not enter (an open panel or
menu, a table view, a window near the end of its span) or the data it did not
use (real long names, a full list, a scrollbar the test browser hid). Fix the
check first, so that it fails on the reported spot, then fix the spot and see it
pass. A missing state or data set joins those the product's
[measurement](visual-judgment.md#measure-alignment-instead-of-judging-a-screenshot)
covers. Fixing only the spot leaves the next breach of the same rule for the user to
find.

## Regression

Write a test that fails on the revision the user saw, or on the last revision
where the behavior broke, and passes after the fix; keep it in the product's
tests. A test that passes on that base does not reproduce the remark: find the
state, data or width that does before fixing. Test design follows
[Acceptance](scenario-testing.md#choose-distinguishing-checks).

## New requirement

Propose the rule in terms a measurement can decide, and show its consequence on
real data: which screens and elements it changes, at which widths and states,
and what it costs elsewhere, such as a longer row or a wrapped label. It becomes
a check only after the user confirms it; until then the remark stays open as a
question. A rule an agent wrote, including one in the project's design document,
is not the oracle, as the
[interface review](../../route-subagents/references/review-and-continuity.md#review-an-interface-change)
treats such a premise.

## Close the defect class

Whatever the kind, close the defect class before finishing a visual or
interaction repair: name the class, find its shared owner (component, style,
token or layout rule), list the consumers it reaches and check each, or one
representative of each distinct composition, with the same measurement as the
reported spot. Report that list; a defect fixed only where it was reported is
still open elsewhere. A one-off copy or data edit needs no sweep. Defect closure
stays narrower than systemic acceptance, as
[Acceptance](scenario-testing.md#derive-the-scenario) says.
