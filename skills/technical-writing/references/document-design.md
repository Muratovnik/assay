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

Select propositions, not source sentences. An author's suggested wording or account
of how material was researched, selected or written is not a product property.
Include that account only when this document's task requires assessing the process
or its result, or it supplies a necessary qualification or notice. Rephrasing it
neutrally does not make it relevant. Keep a required attribution independently of
an unnecessary claim about the author's effort or originality.

Keep necessary prerequisites, meaningful limits, claim-qualifying exceptions and
required notices. Removing a clause must not leave a broader promise behind.
Use the knowledge established for this audience, not everything an unknown visitor
might need. A role such as "developer" does not establish familiarity with every
product concept. A brief that explicitly establishes a concept does settle that
part of the starting point. Keep new consequences involving a known concept;
its definition does not itself fill a gap.

Choose a location by function, not by where the fact appeared in the work notes:

| Material | Location when relevant |
| --- | --- |
| Current behavior, suitability and user actions | Product page or the task's main path |
| Exact options, coverage and exceptional cases | Findable reference detail; keep a qualification beside any claim that needs it |
| What changed in a release | Release notes or changelog; keep required migration actions visible to affected users |
| Checks performed, pending acceptance and author work notes | Requested review, release evidence or handoff; publish a concrete limitation when it affects the reader's decision |
| Origins, credit and licensing | Required notices and provenance needed for this reader's decision; omit an unneeded account of the author's process, whether defensive or neutral |

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

## Review the finished content

Review the actual draft against the reader and task before delivery. Checking that
each statement is supported covers only one direction: also check why it is here.
Use this pass for content reviews too; a true sentence can still be an editorial
defect. Apply the review to the opened scope, without a required checklist file.

1. **Locate surplus.** Inspect definitions beside familiar terms, adjacent
   paraphrases, repeated features, examples, qualifiers and copied source notes.
   Identify the exact passage and what new decision, action, distinction, reason
   or evidence it supplies. If deleting it loses none that this reader needs,
   remove it. If only part contributes, keep that part and merge the overlap.
   Do not justify a repetition merely by calling it "clarification" or "context".
   Inspect modifiers too: what supported class, condition, degree or uncertainty
   changes if the word is removed? Keep a technical distinction or intentional
   emphasis the reader needs; cut a modifier that only endorses the author's work.
   A wording suggestion in notes is not evidence of such a distinction.
2. **Check the remaining meaning.** Read the shortened passage with its conditions,
   exceptions and the relevant source. It must still say who can do what, when,
   with which limits and result. Keep explanations the audience needs, required
   notices, and evidence used by the document's decision. A warning at the action
   it governs or repeated identity in a reference can have a useful second role.
3. **Close actual gaps.** Confirm that the reader can answer the page's question
   or follow its route, including real setup and recognizable success where needed.
   Repair a found defect, then stop when the scoped requirements hold. No deletion
   quota, target word count, mandatory rewrite or recursive self-review follows.

Compare claims across prose, headings and tables, not just within sentences.
Give each table column a distinct information role. A column that paraphrases
another is surplus; a status shared by every row can be stated once above the
table. Keep differing statuses and per-item conditions visible. A short decision
summary can precede detailed evidence, but the detail must add something beyond
the summary. For example, "Check: passed; meaning: the check passed" needs one
result, while "passed on Linux; Windows untested" preserves a meaningful limit.

Attribute a supported paragraph or table at a clear shared location. Do not add
another sentence saying that the same facts came from the same source when the
attribution is already unambiguous. Repeat or separate citations when the source,
claim scope or independently readable section requires it. Do not drop evidence
links or turn a supplied result into the writer's own verification.

These invented examples vary the reader's need; they are not product facts or
phrases to ban:

| Context and draft | Editorial decision |
| --- | --- |
| Role reference for administrators who know read-only access: "Observer is read-only. Observers can read the data but cannot change it." | Keep "Observer has read-only access." The definition adds nothing for this reader. |
| First-use guide for a newcomer who does not know read-only access: the same draft | Keep the explanation, for example "Observers can view the data but cannot change it." The technical label is optional if not needed elsewhere. |
| The role reference also states that Observers can export restricted rows | Keep that permission. Read-only access does not tell the administrator which rows can be exported. |
| An acceptance report includes a failed compatibility check and a note that its author rewrote the prose twice | Keep the check's subject, result and unresolved decision; omit the editing history. Evidence needed for acceptance does not make every work note relevant. |

An already suitable paragraph can remain unchanged. A review finding names the
passage, the reader's established context and the missing contribution; a mere
alternative phrasing is still a preference. Keep this editing analysis outside
the finished document. Clarity review is not execution or proof of successful
installation; use only authorized project checks.
