---
name: instruction-maintenance
description: Use when editing, compressing, merging or reviewing agent instruction files such as AGENTS.md, CLAUDE.md or a SKILL.md body, fixing their stale references, or moving an accepted lesson into instructions, a skill, a check or a record. Skip product docs (technical-writing), prose for people (text-writing) and judging whether a skill change improves behavior (skill-evaluation).
license: MIT
metadata:
  assay-optional-skills: "code-change retrospective skill-evaluation technical-writing text-writing"
---

# Instruction maintenance

An agent reads an instruction file as rules. An edit that reads better but
changes when a rule applies, who it binds or what it forbids is a defect, however
clean the prose. This method keeps the rules intact while instruction files are
shortened, reorganized, corrected, reviewed or extended with a lesson. It is not
a style guide and grants no authority beyond the request.

## Establish the edit

Recover the files in scope, the request (review, edit, compress, move a lesson)
and its target, such as a size limit. Read each affected file completely, the
files it imports or points to, and the owner's own rules for where lessons go;
those rules override the defaults below. Identify which agents read each file
and which file is the single source: a file that only imports another is not the
place to add text. When the edit touches more than one client's file, nested
files, imports or several repositories, read
[client instruction files](references/client-files.md).

A review grants findings, not edits. Removing a memory entry, editing another
owner's file or dropping a rule the size target cannot keep needs the owner's
decision.

## Rules

1. **Inventory before cutting.** Before compressing, merging or moving text, list
   each rule with its trigger, actor, force (must, may, must not), quantifiers,
   negations, conjunct lists, scope and exact identifiers. Use
   [rule inventory](references/rule-inventory.md); it is also the oracle for the
   final check.
2. **Preserve meaning, not wording.** "Only when" is not "when"; permission is
   not obligation. Dropping one conjunct from "never X without A, B and C" makes
   the rule permissive; dropping a trigger makes it overbroad. Keep paths,
   commands, setting names and anchors byte-exact. The qualifier rules and the
   structural check for code spans and links belong to technical writing's
   [preservation](../technical-writing/references/preservation.md); it does not
   read prose qualifiers, so the inventory still decides.
3. **A size target yields to retention.** When the target cannot be reached
   without losing a rule, do not cut silently. Report the gap and the rules that
   would have to go, or relocate a conditional procedure to a document that is
   loaded when it applies and leave a pointer that says when to read it. Removing
   rationale is fine unless it carries a condition or an exception.
4. **Choose the layer by how the rule is applied.** Always-on invariant: the
   nearest instruction file whose scope covers it. Conditional workflow: a skill
   or routed reference. Mechanically checkable fact: a validator, hook or test.
   History and incidents: the planning or audit record, not instructions. Split
   a mixed lesson by part; see [layers](references/layers.md).
5. **One source per rule.** Edit the rule where it lives. Do not copy it into a
   second client file or a parent file; independent repositories inherit nothing
   from each other, so each needs its own statement or an explicit pointer.
6. **Check references against the tree.** Every path, command, flag, skill
   name, heading and anchor an instruction names must exist now. Repoint a stale
   reference only when the new target means the same thing; otherwise report it.
   Never fix a stale reference by deleting the rule around it.
7. **No new policy in passing.** Compression and cleanup add no rule, tighten no
   scope and invent no guarantee. Report a contradiction between files with the
   rule the owner's precedence selects; do not resolve it by choice.

A review reports, with location and consequence: contradictions, duplicates,
stale references, rules separated from their condition, wrong-layer content and
files no agent loads.

## Verify

Map every inventory entry to its disposition: kept, moved (destination and
pointer), or removed by the owner's decision. An entry without a disposition is a
silent drop. Diff exact identifiers separately. Report size before and after,
dispositions, moves, removals awaiting decision and what was not checked, such as
whether a client actually loaded the file.

## Hand off

- Product documentation and repository descriptions:
  [technical-writing](../technical-writing/SKILL.md); prose for a person:
  [text-writing](../text-writing/SKILL.md).
- Whether a skill or instruction change improves behavior, a new skill, or a
  description or trigger edit: [skill-evaluation](../skill-evaluation/SKILL.md).
- Choosing which lessons from a period of work or a memory store to propose:
  [retrospective](../retrospective/SKILL.md). This method applies an accepted
  move; it does not select lessons.
- Implementing a validator or hook: [code-change](../code-change/SKILL.md).

`evals/` is maintainer data; never read it while doing a user's task.
