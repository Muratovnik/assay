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

1. Freeze the reader packet: the document and the version/site context a real
   reader has. Exclude the repository, private chat, prior drafts and author
   explanations that are not available to that reader.
2. Give the reader the goal a real reader would arrive with, phrased as
   questions: "What do you run first?", "What do you need before starting?",
   "How do you know it worked?". Ask about version only if applicability is
   part of the reader's decision, and provide the same versioned-site context
   a real reader has. Do not force a version header into every page.
3. **The reader answers only from the document.** Every answer carries the
   quoted fragment it comes from. When the document does not answer, the reader
   writes "not in the document" — never a reconstruction from general knowledge,
   and never a guess with a hedge.
4. Use one pass by default. Collect the answers without arguing or starting an
   approval loop. A separately authorized repeated reading can confirm a repair,
   but it is no longer fresh-reader evidence.

## Reading the result

A "not in the document" on a load-bearing question is a `warning`, or an `error`
when it blocks the reader's task — a missing prerequisite or an unstated working
directory required for the commands. An unnamed version matters only when it
changes applicability. A quoted answer that is correct but hard to find
is a structure finding, not a wording one. A wrong answer with a quotation can indicate ambiguity or a reader error.
Compare it with the actual passage before deciding to edit.

Do not treat disagreement as a mandate to rewrite. Fix the gap the reader hit,
keep the rest, and note any finding you consciously declined.

## What it does not establish

Reader testing checks whether a document is followable. It does not check
whether the product behaves as described: a reader who can quote the install
command has not installed anything. Technical verification stays with the
project's own means — its tests, its build, an authorized run in a prepared
environment. Passing one of the two never substitutes for the other, and a
report that blurs them overstates both.
