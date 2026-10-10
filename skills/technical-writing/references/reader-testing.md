# Reader testing

An author cannot un-know the product. A fresh reader can help find
the step that exists only in the author's head — the unset variable, the
directory nobody changed into, the account that had to be created first.

## When it applies

One bounded pass, for a substantial document whose readers cannot ask the author
— an onboarding guide, a public README, a runbook, an install document. Not for
a typo fix, a flag rename, a one-section edit or a routine review. If you cannot
name the decision the result will change, skip it.

## Authorization

Reader testing means delegating to a separate reader, so it happens only when
the user has already authorized delegation, and it follows whatever delegation
method the user's setup provides. Where the separate `route-subagents` skill is
installed, that skill owns packet scope, isolation, model choice and turn
limits; a single-skill install of this method does not ship it, and this file
does not depend on it. This skill grants no delegation of its own: no agent is started
because a document is long, because a pass would be interesting, or because
parallel readers would be faster. Without that authorization, do the equivalent
by hand — reread the document against the checklist below and report what a
newcomer could not answer — and say that no independent reader was used.

## The protocol

1. Freeze the reader packet: the saved document, the version/site context a real
   reader has, and prerequisites reachable through its documented handoffs. Exclude
   private chat, prior drafts and repository or author explanations unavailable on
   that reader's route. Establish expected task coverage from the original brief
   and [source-derived procedure conditions](document-design.md#establish-procedure-conditions),
   separately from the prose being tested; keep those author associations out of
   the reader packet.
2. Give the reader the goal a real reader would arrive with, phrased as
   questions: "What do you run first?", "What must be in place when you run this
   step, and what supplies it?", "How do you know it worked?". Ask about version
   only if applicability affects the reader's decision, using the versioned-site
   context a real reader has. Do not force a version header into every page.
3. **The reader answers only from the packet.** Every answer carries the quoted
   fragment and location it comes from, including an earlier setup or prerequisite
   handoff when applicable. When the route supplies no answer, write "not in the
   document" — never reconstruct it from general knowledge or a guess with a hedge.
4. Use one pass by default. Collect the answers without arguing or starting an
   approval loop. A separately authorized repeated reading can confirm a repair,
   but it is no longer fresh-reader evidence.

## Reading the result

Assess prerequisite answers against the applicable conditions at their first
dependent actions, following [condition review](document-design.md#establish-procedure-conditions).
A quotation is evidence of what the route says, not automatic proof that it supplies
the necessary setup. Accept concrete earlier setup, usable handoffs and genuinely
guaranteed reader context; a merely related passage does not establish coverage.

A "not in the document" on a load-bearing question is a `warning`, or an `error`
when it blocks the reader's task — a missing prerequisite or an unstated working
directory required for the commands. An unnamed version matters only when it
changes applicability. A correct answer that is hard to find is a structure
finding. A wrong answer with a quotation can indicate ambiguity or a reader error;
compare it with the actual passage and applicable source before deciding to edit.

Do not treat disagreement as a mandate to rewrite. Fix the gap the reader hit,
keep the rest, and note any finding you consciously declined.

## Complete writing review

When an independent review is already planned to assess the finished writing,
include content contribution alongside followability in that review. Use the
[finished-content review](document-design.md#review-the-finished-content) against
the original brief, including retained and source-supported prose. Correct task
answers alone do not establish that every explanation belongs.

For a relevance finding, quote the passage and the reader context it adds nothing
to. Explain what removing or merging it would change for the reader's understanding,
choice or action. Check the condition, necessary limit or notice that the proposed
edit might weaken. A qualification needs an actual claim or action to constrain;
an already-established distinction needs a separate useful role to appear again.
Propose the smallest supported repair. A wording preference or "could be shorter"
is insufficient; a scoped no-finding result is valid.

Keep the real-reader packet separate from the original brief and any authoritative
sources needed for editorial judgment. If one reviewer performs both checks, save
the reader-route answers before supplying editorial source context. A fact learned
from that later context cannot fill an earlier gap in the documented route. Do not
supply previous diagnoses, desired findings or the author's defense of a passage.

Use the existing review response and one localized check of accepted repairs,
including their affected conditions and neighboring claims. Do not add a reviewer
or repeat the whole review until it passes. Resolve a disagreement against the
same evidence and report any unresolved material issue. A repair reread is not
fresh-reader evidence. An explicitly followability-only review keeps its mandate;
without a planned independent review, use the author's existing saved-result
check within the opened scope.

## What it does not establish

Reader testing checks whether a document is followable. It does not check
whether the product behaves as described: a reader who can quote the install
command has not installed anything. Technical verification stays with the
project's own means — its tests, its build, an authorized run in a prepared
environment — with available paths and truthful limits as described in
[delivery checks](../SKILL.md#deliver-and-check-the-artifact). Source inspection
can establish an applicable condition without executing the operation. Passing
one kind of verification never substitutes for the other, and a report that
blurs them overstates both.
