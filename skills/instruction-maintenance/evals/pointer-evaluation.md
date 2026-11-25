# Preservation pointer: rationale and owed pilot

Maintainer material for one wording change, not runtime instructions or a run
report. The cases are synthetic and public; none has been run by a model.

## Decision and gap

At `9e03dca` rule 2 said that the qualifier rules and the structural check for
code spans and links belong to technical writing's preservation reference, and
that the check does not read prose qualifiers. It gave no condition for using
the reference, and the reference called itself optional. The reference holds no
qualifier rules for instruction files: those are this skill's rule inventory.
The sentence named the wrong owner and gave an agent no reason to open the file.

In the maintainers' own sessions, edits of instruction files did not open the
reference, including edits that compressed or moved text, and this skill's own
rule inventory was opened in a minority of those. A sample of the edits
compared with their commits found no rule lost silently: every changed code span
or link was a deliberate change. This is a text defect and a candidate, not a
measured harm.

The candidate names the condition (after compressing, merging or moving text),
the action (the structural check in rewrite mode on the old and new text), what
it reports, and the skip (an addition or a single local correction). The
reference stays optional unless the task or the method being followed asks for
it, so technical writing's own default does not change.

## Cases and controls

| Case | Protected outcome | Legitimate work an overbroad reading would burden |
| --- | --- | --- |
| PP01 | A compression keeps every identifier byte-exact, a prohibition hidden in an explanatory sentence, and reports the size it could not reach | — |
| PP02 | A merge across directories keeps the docs-only scope and re-bases relative destinations so they resolve | — |
| PP03 | A procedure moved into a skill file arrives byte-exact, with a pointer that names when to read it | — |
| PP04 | — | Adding one rule needs no check |
| PP05 | — | Correcting one path in view needs no check |

Before the rubric was frozen, the structural probes were run on hand-written
outputs. PP01: a compression that cut only explanation and history reached 18%
and failed `inline_code` on a duplicate `make check` that left with an
explanatory sentence, which the report must name; shortening the signing
command and dropping the drill anchor added a `link_destination` failure. PP02:
a merge that copied `assets/README.md` and `../CONTRIBUTING.md#screenshots`
unchanged passed `link_destination`, and the correct re-based merge failed it,
so byte comparison alone rewards the broken links and the link-resolution probe
decides. PP03: a move that dropped `SIGN=1` failed `inline_code` on that span; the
correct move failed only on the pointer's added path and the re-based archive
link. These runs calibrate the probes; they say nothing about a model's
behaviour.

## Owed paired pilot

Proposed volume, not yet agreed: 30 sessions and 2 spare on Opus 5.5 at high
effort, the model that made most of the observed instruction edits.

- Arms: `skills/instruction-maintenance` and `skills/technical-writing` at
  `9e03dca` against the commit that adds this file. Both arms load
  instruction-maintenance explicitly; the packet holds both skills of its arm, so
  the relative link and `scripts/text_check.py` resolve.
- Cases and repeats: PP01 to PP05, three runs per case per arm. The two spare
  sessions replace infrastructure failures only, never a completed run. Fix the
  run order before starting and alternate the arms.
- Packets: `python tools/eval_assets.py prepare --cases <cases file> --case <id>
  --method <arm>/skills/instruction-maintenance --method
  <arm>/skills/technical-writing --output-parent <evidence directory>`. The
  executor may run Python on the packet's own `text_check.py` and nothing
  else; it installs nothing and runs no `git`.
- Trace: whether `preservation.md` was read, whether `text_check.py preserve`
  ran and in which mode, whether `rule-inventory.md` was read, and tokens, turns
  and wall time.
- Grading: run the rubric's verification probes on each saved project, then the
  `required` and `reject` items, from the saved files and the report. No model
  judge is needed.
- Effect: the candidate reads the reference or runs the check in at least six of
  its nine PP01 to PP03 runs, the baseline in at most one, and the candidate in at
  most one of its six PP04 and PP05 runs.
- Outcome: an improvement in meaning preserved is claimed only when the
  candidate meets every `required` item with no `reject` item in at least three
  more PP01 to PP03 runs than the baseline.
- No effect: a process difference of two or fewer. Check in the traces whether
  rule 2 was reached before revising the text; another paraphrase is not the next
  step.
- Harm: the candidate runs the check in two or more control runs, or meets the
  hard requirement in two or more fewer PP01 to PP03 runs than the baseline.

Three runs per arm show a large difference or a regression; they cannot show a
small one. These are selection cases: if the text is revised after the pilot,
they become regression material, and a new held-out case is written outside the
tracked tree first.
