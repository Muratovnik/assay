# Design the document around the work

Read for a substantial new document or rewrite. For a local correction, keep the
existing structure unless the task opens it. These are composition choices, not
a demand to write planning documents before writing documentation.

## Establish the starting point and destination

A user installing a package, a contributor running a checkout and an operator
following a recovery procedure need different paths. Decide which path this
page and publication surface serve. Explain only the gap between the audience's actual knowledge and
what they need to do or understand. A working editor environment does not establish
that a new reader has the same files, permissions or dependencies.

Start with enough orientation to choose the page. Avoid a separate list of every
excluded topic. An explanation can start from the behavior that puzzles the reader;
a reference can start from the interface it specifies. Neither needs marketing.

## Select content before arranging it

For each material block, decide whether to keep it, condense it, move it to an
available destination or remove it within the requested scope. Ask what decision,
action or understanding the reader would lose without it. A fact can be accurate
and still be irrelevant here. This is editorial judgment, not a required ledger
for every sentence or a new round of questions when the brief supplies the context.

Keep necessary prerequisites, meaningful limits, claim-qualifying exceptions and
required notices. Removing a clause must not leave a broader promise behind.
Use established terms when this audience knows them; explain an unfamiliar term
through the consequence the reader needs, not an inventory of internals.
Remove redundant explanations, decorative examples and answers to objections the
reader has no reason to raise. Preserve a contrast that resolves a real ambiguity.

Choose a location by function, not by where the fact appeared in the work notes:

| Material | Location when relevant |
| --- | --- |
| Current behavior, suitability and user actions | Product page or the task's main path |
| Exact options, coverage and exceptional cases | Findable reference detail; keep a qualification beside any claim that needs it |
| What changed in a release | Release notes or changelog; keep required migration actions visible to affected users |
| Checks performed, pending acceptance and author work notes | Requested review, release evidence or handoff; publish a concrete limitation when it affects the reader's decision |
| Origins, credit and licensing | Required notices and relevant provenance; no unsolicited defence of the author's process |

These are locations, not bans. An ADR needs its decision status and history; a
runbook may need a dated operational limit; an acceptance report needs unresolved
verification. An unperformed editor check or pending acceptance step is a work
record, not by itself a product limitation. Publish it when requested or when
it qualifies a concrete claim the reader must rely on, such as whether a recovery
procedure applies to their storage format. A version and date alone do not make
a verification note useful on a product page. Keep an explicitly declared
experimental release status or a material unresolved product condition; do not
invent either from missing test coverage, or turn an unknown into a guarantee.

Move information only when the destination exists and is accessible to this
audience. Leave enough context and a specific pointer to find it when needed;
a vague link does not preserve an essential warning. Omit an irrelevant work
note without inventing a new document just to store it. A copyedit that does not
open content selection retains its scope and can report a larger recommendation.

## Arrange by dependency, not discovery order

During research, files arrive in an arbitrary sequence. Rebuild the document around
the reading sequence: idea before jargon, prerequisite before its first use,
warning before the relevant action, expected result after it. Put an alternative
next to the choice it changes, rather than interleaving two complete workflows.

For a README, orientation and a needed first-use path can precede detailed options.
For a how-to, keep the action path legible and link to explanations that are not
needed mid-step. For an architectural explanation, show why a component exists
before listing its internals. Repetition can be correct in a parameter reference.

## Show one complete path before enumerating options

When the reader needs an example or procedure, give it a starting state, an action
and a recognizable result. Do not add a procedure for an automatic result that
requires no further action. Use the
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

## Update the semantic unit

After adding or changing behavior, reread the affected explanation together with
its prerequisites, tables, examples, exceptions and related exclusions. Replace
the old account of current behavior instead of appending each development delta.
If a table now lists support, reconcile a nearby claim that the feature is still
unsupported. Check affected copies or translations within the authorized scope,
and report any necessary follow-up outside it. A typo does not require a whole
documentation audit.

Preserve historical records in their role: do not rewrite an ADR's earlier
decision or a released changelog entry as though it always described today's
behavior. Correct current guidance and keep the record's status and chronology.

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
