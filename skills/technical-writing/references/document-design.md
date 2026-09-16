# Design the document around the work

Read for a substantial new document or rewrite. For a local correction, keep the
existing structure unless the task opens it. These are composition choices, not
a demand to write planning documents before writing documentation.

## Establish the starting point and destination

A user installing a package, a contributor running a checkout and an operator
following a recovery procedure need different paths. Decide which path this
page serves. Explain only the gap between the audience's actual knowledge and
what they need to do or understand. A working editor environment does not establish
that a new reader has the same files, permissions or dependencies.

Start with enough orientation to choose the page. Avoid a separate list of every
excluded topic. An explanation can start from the behavior that puzzles the reader;
a reference can start from the interface it specifies. Neither needs marketing.

## Arrange by dependency, not discovery order

During research, files arrive in an arbitrary sequence. Rebuild the document around
the reading sequence: idea before jargon, prerequisite before its first use,
warning before the relevant action, expected result after it. Put an alternative
next to the choice it changes, rather than interleaving two complete workflows.

For a README, orientation and a complete first example can precede detailed options.
For a how-to, keep the action path legible and link to explanations that are not
needed mid-step. For an architectural explanation, show why a component exists
before listing its internals. Repetition can be correct in a parameter reference.

## Show one complete path before enumerating options

An example has a starting state, an action and a recognizable result. Use the
actual interface and supported output. If the result has variable fields, mark
the example as illustrative instead of inventing a captured terminal transcript.
Explain what a parameter changes at the point where the reader chooses it.

Invented teaching contract: an export command writes a new file, refuses an
existing destination unless replacement is explicitly requested, and does not
modify source records. A useful description would distinguish output replacement
from source mutation. Saying merely "safe export" hides the decision. Do not add
a replacement flag to real documentation unless that product supports it.

A how-to can stop at an observable success. It does not need a generic "next steps"
section. A tutorial may guide a learner through a smaller controlled example;
a reference should not become that tutorial. Use the appropriate type, not all types.

## Explain mechanisms at the needed depth

Connect cause and consequence. "Requests are queued" names a component; explaining
what the reader can observe while work is queued makes it useful. Do not infer
speed, reliability or exactly-once behavior from the mere presence of a queue.

For a trade-off, name the concrete competing need and supported consequence. Avoid
invented alternatives simply to give every decision three options. State a real
limitation where it changes suitability, rather than hiding it after a long pitch.

## Read the finished page without the research context

Does a reader know where to run the command, which path is theirs, and how to tell
whether it worked? Does the explanation answer its opening question? Do terms
refer to the same thing throughout? Is the main path obscured by reference detail?

Fix the gap the reader would hit. Do not repeat all sources, all passed checks,
or every known prerequisite. Existing linked context can be enough if it is
actually available to this reader. Essential cautions should not be hidden behind
a vague link. Research evidence stays in an audit note when requested; the document
contains the information needed to use it.

Clarity review is not execution. Run project checks only when authorized, and
separate a documented procedure from one exercised in the named environment.
