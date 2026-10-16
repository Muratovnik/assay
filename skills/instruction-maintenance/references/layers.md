# Layers for a lesson or rule

Use when a lesson, note or rule is being added, moved or questioned as misplaced.
The owner's own routing rules decide first; this table is the default when they
say nothing.

## Choose by how the rule must be applied

| The content is | It belongs in | Because |
| --- | --- | --- |
| An invariant that applies to every task in a scope | The nearest instruction file whose scope covers it | It must be in context before the agent decides anything |
| A procedure or criteria that matter only in a recognizable situation | A skill or a reference the instructions route to | Loading it everywhere costs context and dilutes the always-on rules |
| A fact a program can check (a forbidden word, a required file, a format) | A validator, hook or test | A check fails reliably; a sentence is only read |
| An incident, its evidence or a decision's history | The planning, audit or decision record | Instructions say what to do, not what happened |
| A personal preference | The user-level or local file that is not shared | Others should not inherit it |

A lesson often mixes these. Split it: the procedure goes to the conditional
layer with its trigger intact, the incident stays as evidence in the record,
and a mechanical part becomes a check proposal. Keep the trigger in the moved
text; "backfill in batches before adding the constraint" without "when adding a
NOT NULL column to a large table" is a different rule.

## Neighbouring cases that are legitimate

- A short conditional rule that nearly every task meets can stay always-on.
- A check proposal does not retire the instruction until the check exists and
  fails on the case it targets. Until then keep both.
- A rule that a nested file states differently for its subtree is a scoped
  override, not a duplicate, when the owner intends it.
- A lesson specific to one repository stays with that repository, not in a
  user-wide file.

## Moving out of a memory store

A stored lesson is the owner's data. Propose the move with destination, exact
text and how to undo it; edit or retire the memory entry only after the owner
accepts. Selecting which entries to move belongs to the retrospective method's
[memory review](../../retrospective/references/memory-retrospective.md). Write
into instructions only verified content: a lesson whose claim no longer matches
the current tree is reported, not promoted.

Implementing an accepted validator or hook is ordinary code work in its owning
repository, under that repository's gates.
