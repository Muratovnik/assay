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

For a substantial rewrite, establish the requested outcome before assessing the
existing outline. Trace the route from the reader's starting point to that outcome:
which functional gaps need new material, which sections still serve it, and which
belong on another route? Polishing the current sections cannot resolve a missing
way to obtain or use the product. Retained contributor or operator procedures
within scope also need usable paths. A local copyedit does not open these decisions.

Start with enough orientation to choose the page. Avoid a separate list of every
excluded topic. An explanation can start from the behavior that puzzles the reader;
a reference can start from the interface it specifies. Neither needs marketing.

## Select content before arranging it

First establish what this document needs to answer. Use the request, publication
surface and the reader's actual work to bound those questions. Add the prerequisites,
causal connections and conditions needed to answer them. An explanation can develop
understanding without prescribing an action. A procedure can anticipate a supported
failure or recovery step without waiting for the user to ask about it. Do not infer
a reader's worry, misconception, comparison or new goal just because a sentence
could answer it.

Choose the information before its wording: the main claims, their necessary
qualifications and the explanation or evidence serving those questions. Then keep,
condense, move or remove source material within scope. Topic relevance and factual
support do not establish a place in that selection. Ask which established question
or concrete dependency a detail serves; "the reader might appreciate it" does not
supply one. Apply this directly on small tasks, without a mandatory outline file
or additional user questions when the brief supplies the context.

Choose the level of detail too. An overview may need a capability, a release note
the affected class and changed behavior, and a reference an exact item. Name an
individual instance when it identifies the actual scope, a necessary target, a
meaningful exception or a useful example. A member of an already clear class does
not earn a mention merely because it appears in a test, source note or recent fix.
Do not replace a precise affected item with a broader claim to make prose shorter.

Keep procedural detail with the operation it qualifies. When an overview links
to a separate procedure, retain the conditions needed to choose or enter that
route; leave option meanings, defaults and exceptional branches with the command
or decision they explain. An isolated parameter warning can introduce a mechanism
the page never asks the reader to use. Bring it into the overview when it changes
the present choice or prevents a concrete mistake on that path. Do not add a new
procedure merely to justify retaining its detail, or move a necessary warning
past the action it governs.

While composing, keep this selection boundary: a new substantive aside needs the
same task connection as a main claim. A link can identify its destination without
selling an imagined use for it. Explain a non-obvious destination or actual choice
when the reader needs that distinction. A real contrast describes relevant behavior
or alternatives; an invented contrast introduces another question to the document.

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

## Match precision to the surface

A fact can be correct at this revision and still be a poor standing description.
Consider a routine product change: which introductory claims would need editing,
and does their precision help this reader recognize, choose or use the product?
Do this as a content decision, not a forecast or a new maintenance checklist.

| Statement's role | Appropriate precision |
| --- | --- |
| Standing introduction, repository About text or package summary | Identify the product and its useful purpose. Include changing detail when it affects suitability; a snapshot of the repository's size or the writer's latest checks usually does not. |
| Current catalog, interface reference or compatibility contract | Keep the exact inventory, identifier, limit or supported version the reader needs, with its maintained source. |
| Dated release note, measurement or acceptance record | Keep the relevant change, date/version, denominator and conditions that make the result interpretable. |

These roles can coexist on one page. A product with a fixed capacity may need
that capacity in its introduction. A deprecation or support restriction can
change the first action and belongs before it. A catalog generated from source
can avoid manual synchronization, but generation alone does not justify copying
its total into every heading or description.

If precise detail serves no purpose here, remove the claim within the opened
scope; replacing it with "several", "many" or "recent" can leave the same padding.
If it matters, keep it exact and put it where the reader can use it. Do not make
a compatibility bound vague, erase a material limitation, or add a date merely
to rescue an unnecessary statement. Stable copy still changes when the product's
identity, suitability or required action changes.

## Arrange by dependency, not discovery order

During research, files arrive in an arbitrary sequence. Rebuild the document around
the reading sequence: idea before jargon, prerequisite before its first use,
warning before the relevant action, expected result after it. Put an alternative
next to the choice it changes, rather than interleaving two complete workflows.

For a README, orientation and a needed first-use path can precede detailed options.
For a how-to, keep the action path legible and link to explanations that are not
needed mid-step. For an architectural explanation, show why a component exists
before listing its internals. Repetition can be correct in a parameter reference.

Describe the work in terms the audience uses. A taxonomy of internal components,
validation stages or method responsibilities is not automatically an explanation
of the product. Keep technical names when they identify an interface or a useful
concept; explain an unfamiliar concept before making the reader act on it.

## Establish procedure conditions

For each retained in-scope procedure, establish the conditions needed for its
documented result before judging the prose. An authoritative interface or
configuration contract can supply them; otherwise trace the available implementation
and relevant configured branch. When an inspected entry point delegates applicable
checks, follow those calls far enough to identify the conditions. Bound this
reading to the selected route and result. A diagnostic may legitimately report
absent state; do not inventory every source assertion or possible environment.

Relate each condition to the first documented action whose execution needs it,
including requirements enforced by calls inside that action. Read the route from
its stated starting point through that action. Account for conditions genuinely
guaranteed to this reader, established by preceding steps, or supplied by a usable
prerequisite handoff. The handoff must be reachable before the dependent action
and identify the setup the reader needs. A related passage or vague assurance of
readiness does not establish a concrete condition. One concrete setup can satisfy
several conditions without enumerating each separately.

Ask: could a reader follow this route as written and still reach that first
dependent action with a known applicable condition missing? If so, repair the
setup or handoff before that action. A check that merely reports missing state
does not establish readiness. A documented setup or repair step, or a usable
remediation handoff, can supply the condition before the dependent action. Do not
require a condition before the step that creates it, import an inactive branch's
requirements, or repeat setup genuinely guaranteed by the reader's context.

Keep the source-to-condition-to-action associations in working reasoning or
existing evidence, outside the product text; no new record is mandatory. Use
authorized source reading to document a procedure even when performing its live
action is outside the task's authority. Recheck these associations against the
saved route after editing; plausible setup prose or a passing preservation check
cannot establish condition coverage.

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

After a substantive rewrite or change to a current claim, reread the affected
explanation together with its prerequisites, tables, examples, exceptions and
related exclusions. Include retained introductions, headings and summaries that
describe the same current behavior. Replace the old account instead of appending
each development delta.
If a table now lists support, reconcile a nearby claim that the feature is still
unsupported. Check affected copies or translations within the authorized scope,
and report any necessary follow-up outside it. A typo does not require a whole
documentation audit.

Locate the canonical owner of an affected statement. For generated text, follow
its generation rule to the source text that creates it; a package manifest or
README may be another generated copy. Inspect the applicable generator or template
to locate the actual owner. Change canonical source and regenerate through the
project's authorized mechanism when that is the contract, then reread the resulting
projections within scope. Editing a generated copy alone will not survive
regeneration. Keep independently maintained surfaces
in the scoped update or identify the exact remaining change. Proposed GitHub About
text and updated local metadata do not establish that the remote field was updated.

Preserve historical records in their role: do not rewrite an ADR's earlier
decision or a released changelog entry as though it always described today's
behavior. Correct current guidance and keep the record's status and chronology.

## Review the finished content

Review the saved result against the original reader outcome and opened scope,
including material retained without changes. Checking that each statement is
supported covers only one direction: also check why it is here. Use this pass
for content reviews too; a true sentence can still be an editorial defect.
No additional checklist file is required.

1. **Confirm the reader can finish.** Read the page continuously from orientation
   to the requested result. Check all retained in-scope routes, including connected
   developer procedures, using the [condition review](#establish-procedure-conditions).
   Headings, terms, links, setup and recognizable success must carry this reader
   without the editor's private context or an unrelated contributor workflow.
   Resolve functional gaps even when no existing sentence states them incorrectly.
2. **Compare contribution with omission.** Inspect retained and added material:
   introductions, inventories and counts, whole passages, definitions, examples,
   repetitions, qualifiers and modifiers. Compare what the reader can understand,
   choose or do with and without each detail. Losing a true fact alone does not establish a lost
   task contribution. Identify the established question, necessary dependency,
   useful explanation, meaningful distinction or required notice that removal would
   weaken. Calling material "inventory", "clarification" or "context" supplies no
   such connection. A true example can add facts without adding understanding;
   a benefit or reassurance can invent a new concern. Keep useful precision,
   examples and explanatory depth; remove or merge material whose omission loses
   no contribution. Keep the contributing part of a mixed sentence. For modifiers,
   check the supported class, condition, degree, uncertainty or needed emphasis
   they convey; a wording suggestion in notes does not establish that distinction.
3. **Recheck the edited meaning and route.** Read changed passages with their
   conditions, exceptions and relevant sources. They must still say who can do
   what, when, with which limits and result, and supply prerequisites before the
   first dependent action. Preserve explanations this audience needs, required
   notices and evidence used by the document's decision. A warning at its action
   or repeated identity in a reference can have a useful second role. Repair a
   found defect, then stop when the scoped requirements hold. No deletion quota,
   target word count, mandatory rewrite or recursive polishing follows.

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
| A scheduling overview says all overnight jobs resume; a fixture names one job | The fixture name adds no scope or explanation. Keep the class-level behavior. |
| A scheduling reference says only the `reindex` job can resume | Keep that exact name; dropping it would broaden the claim. |
| A configuration reference adds an unsolicited argument against editing files by hand | Omit the argument unless the task or actual operation makes that alternative relevant. A supported fact about the editor does not establish a reader objection. |
| A guide asks how local edits interact with an automatic reload | Explain that interaction and its consequences, including a concrete example if it helps. The contrast now answers the task. |

An already suitable paragraph can remain unchanged. A review finding names the
passage, the reader's established context and the missing contribution; a mere
alternative phrasing is still a preference. Keep this editing analysis outside
the finished document. Clarity review is not execution or proof of successful
installation; use only authorized project checks.
