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
