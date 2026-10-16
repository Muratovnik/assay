# Evaluation protocol and current limits

Coordinator material, not runtime instructions. Use the existing
`tools/eval_assets.py` input/rubric protocol; no new runner, model dependency or
paid campaign is needed.

## Conditions

Compare the same prompt, input files, permissions and model settings with (A)
the enabled Assay collection without instruction-maintenance and (B) the same
collection with it. A third useful condition is a general instruction-file
improver from the client's plugin ecosystem, where one is installed. Run
discovery cases through the client's normal route with the actual enabled
collection; explicit loading does not show automatic selection. Include Russian
and English prompts.

Build input-only packets with `tools/eval_assets.py prepare`. Keep this file,
the rubric and earlier answers out of the executor's reach; the packet verifier
does not enforce filesystem isolation.

## What the cases protect

| Case | Defect it detects | Nearby valid behavior it must allow |
| --- | --- | --- |
| C01 | Lost qualifiers, conjuncts and exclusivity under a size target; silent drops | A smaller cut that keeps every rule and reports the missed target |
| C02 | Deleting a rule to fix its stale reference; inventing a target | Repointing to a documented equivalent |
| C03 | Editing during a review; missing cross-file contradictions and history in instructions | Treating a nested file as an intended scoped override once the owner confirms it |
| C04 | Wrong-layer moves; dropped trigger and timing; curating memory before acceptance | Proposing the linter without implementing it |
| C05 | Writing beside an import so only one client reads the rule | Asking which file is the source |
| C06 | Ceremony on a trivial correction (control) | A direct one-word fix |
| C07 | Assuming instruction inheritance into an independent nested repository | Reporting that the nested owner must approve |

D01-D04 should select the method; D05-D08 are near misses owned by
technical-writing, text-writing, skill-evaluation and retrospective.

Judge the delivered files and report, not their length or the number of checks.
Count, per case, lost conditions (trigger, quantifier, negation, conjunct, scope),
changed identifiers, wrong-layer placements and silent drops.

## Design evidence so far

Before the skill text was written, its author compared ordinary editing, the
criteria of an installed general instruction-file improver applied by hand, and
the draft rules on copies of two real tasks: compressing a dense instruction file
by about 30% and moving one stored lesson. Ordinary editing and the improver's
criteria met the size target by dropping about twenty conditions each
(exclusivity words, one or two conjuncts of a "never ... without" rule,
retirement gates, negations) and put a conditional procedure and an incident into
always-on instructions. The draft rules kept every inventoried rule but reached
only a 10-17% reduction, and one pass shortened five exact paths; that is why
the method reports the size conflict and checks identifiers separately. One
author produced and scored every condition, knowing the target decisions, on one
file and one lesson. This is design evidence, not a measurement, and those inputs
are not part of this corpus.

## Current verification boundary

The corpus has 7 task cases and 8 discovery cases, written from the method's
brief; none has been run. Repository gates check pair structure and
registration only. Reserve at least one further case outside the tracked tree
before tuning on these cases, for example a SKILL.md body compression with a
reference that must keep its reading condition; once a tracked case informs a
revision it is regression material, not held-out evidence.
