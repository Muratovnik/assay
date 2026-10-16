# Need and scope

Use when the stated request may be a proxy for another need, an example may
hide the real scope, or the system around the idea is not yet known.

## Recover the need

- Restate the outcome without the proposed mechanism. If the restatement still
  names the mechanism, the need is not yet recovered.
- Ask "why" up the chain toward the outcome the user cares about, and stop at
  the first level that changes which solutions look reasonable.
- Ask what job the idea is hired to do and for whom. Distinguish who has the
  problem from who proposed the fix.
- List what would have to be true for the idea to be worth doing. The
  conditions that would hurt most if false are the load-bearing assumptions.
- Separate observed problems from the proposed explanation of their cause. A
  question such as "how do we add X" presupposes X; ask what problem X solves.

A need the user has stated explicitly and checkably is a fact, not a
hypothesis. Do not re-derive it.

## Find the class behind an example

An example ("for example, the export mode") is evidence about a class of
things. Identify the class: modes of the tool, consumers of the API, steps of
the workflow. The question usually applies to the class:

- "Do we cover all needs, for example mode X?" asks about the tool's coverage.
- "Is it worth keeping X, for example its cache?" asks about the component.

When the user names the boundary ("only mode X", "leave the rest"), the class
is that boundary. Keep to it; one labelled adjacent observation is allowed.

## Build an independent inventory

Do not take the completeness denominator from what has been discussed. Derive it
from independent sources: entry points, commands, modes, documented features,
open issues and requests, tests, configuration and consumers. For each item
record what need it serves and whether it is used.

Check both directions:

- each need has a supporting part of the system or a named gap;
- each significant part has a need or is a candidate for removal or reuse.

Scale the inventory to the decision. Say what was examined and what was not,
and why; "I did not read the plugin modules" is a useful limit, not a failure.
