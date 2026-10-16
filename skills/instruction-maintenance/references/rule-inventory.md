# Rule inventory

Use before compressing, merging, reordering or moving instruction text, and
again as the oracle for the final check. Skip it for a single local correction
whose sentence keeps its trigger and force unchanged.

## Record each rule

One line per rule is enough. Record what changes the rule's meaning if lost:

| Field | Examples |
| --- | --- |
| Trigger | "before changing a contract", "after the checks pass", "while the deploy can still be split" |
| Actor and object | who is bound; which file, command or repository the rule governs |
| Force | must, must not, may, by default, prefer |
| Quantifier | only, every, any, at most, completely, at any age, the one command |
| Negation | never, no, not, nothing, without |
| Conjunct list | "a ticket, a backup and a reviewer"; "health checks, a canary, a restore drill and a traffic check" |
| Scope list | "commit, PR, release note or artifact" |
| Exception | "unless", "except", rationale that names when the rule does not apply |
| Identifier | path, command, flag, setting, skill name, heading anchor |

Keep the inventory outside the delivered file. It is working material.

## Meaning changes to watch

- A conjunct dropped from a prohibition with "without" widens what is allowed.
- A dropped trigger turns a conditional rule into an always-on one, often an
  obligation nobody intended.
- "Only", "the one", "exactly" and "at any age" carry exclusivity; their loss
  admits other actors, commands or ages.
- "May" becoming "should" adds an obligation; "must" becoming "prefer" removes
  one.
- A shortened path or renamed command is a changed identifier even when a reader
  can guess the target. Agents search and execute it literally.
- Merging two rules can move a condition from one to both, or from both to one.

Equivalent wording is allowed. The question is whether an agent following the new
text would act differently in some case the old text decided.

## When the size target conflicts with retention

Dense instruction files often cannot lose a third of their words without losing
rules. Cut in this order and stop when the target is met:

1. exact duplicates and restatements of a rule given elsewhere in scope;
2. explanation that carries no condition, exception or priority;
3. relocation of a conditional procedure to a document loaded when it applies,
   with a pointer that names the situation, not just the file.

If the target is still missed, deliver the retained version and report: the
measured size, the gap, and each remaining rule that would have to be dropped
or relocated, for the owner to decide. Do not choose for them by deleting.

## Verify the result

For each inventory entry, find the new text and confirm trigger, force,
quantifiers, negations, conjunct and scope lists, exceptions and identifiers.
Record its disposition: kept, moved (destination and pointer), or removed by
decision. Then compare the identifier sets of old and new text, for example code
spans and link targets; the structural preservation check in
[technical writing](../../technical-writing/references/preservation.md) covers
those regions in rewrite mode but not prose qualifiers.

A passing word count or a clean structural check does not show that the rules
survived. Report what was checked and how.
