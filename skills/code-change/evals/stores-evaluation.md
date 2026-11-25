# Shared stores and migrations: rationale and evaluation

Maintainer material for one proposed method change, not runtime instructions or
a run report. The cases are synthetic and public. The paired pilot below found
no effect, and the reference it tested was removed; the cases, rubric and probes
stay as regression data for any later change on this subject.

## Decision and gap

At `6242086` the library said only that a boundary contract carries atomicity,
retry or idempotency where the scenario needs them, that code rollback does not
restore migrated data, and that a concurrency test is allowed. Nothing said how
to implement a read-check-write under concurrent writers, where uniqueness is
enforced, that an external call stays out of a transaction, how a repeated
request avoids a repeated effect, or that a migration needs a reverse step that
has been run and an expand stage the previous release can live with. The change
added a conditional reference, `references/stores-and-migrations.md`, to
code-change and one route line in its skill file (`687d78b`). Deciding whether the contract needs these guarantees stays with
software-architecture, and test design with test-writing.

The approach was studied in an external MIT-licensed set of backend skills on
data integrity and database migrations. No text or code was copied. Engine
details specific to one server database and login rate limiting were left out.
That source reports fewer critical defects with its skills, but most of its gap
came from two tasks and its tasks were not held out from authoring. It
establishes nothing for this reference. No failure of this kind was looked for
in the maintainers' own projects: this closes a library gap, not an observed
harm.

## Cases and controls

SM01 to SM03 are the held-out cases the change was planned around: conditional
write, migration rollback and an external call inside a transaction. The
reference was written before them and quotes none of their scenarios.

| Case | Protected outcome | Legitimate work an overbroad rule would reject |
| --- | --- | --- |
| SM01 | 20 concurrent reservations of stock 10 give 10 successes and stock 0 | A last-writer-wins price edit stays unguarded |
| SM02 | A requested rename expands first, so the previous release and a rollback read and write every row; 001 unchanged; down and up work | An additive optional column is one plain migration |
| SM03 | No write lock is held during the charge; a repeated or concurrent request charges once | Two requests with equal content are two orders |
| SM04 | — | A read-only query on the same kind of store gains no lock, migration or key |

Before the rubric was frozen, each probe was run against hand-written
implementations: a read-then-write reserve against a conditional update and
`BEGIN IMMEDIATE`, an in-place rename against an expand migration with a trigger
and a dual write, a charge inside the insert's transaction with a lookup against
a committed pending order with a unique request id, and a plain read against a
copy that touched an existing function. Only the second of each pair passed.
These runs calibrate the probes; they say nothing about a model's behaviour.

## Paired pilot design

Agreed volume: 18 sessions on Sonnet at medium effort.

- Arms: `skills/code-change` at `6242086` against the commit that adds this file.
  Both arms load code-change explicitly with the same `skills/test-writing` and
  `skills/software-architecture` bytes, which the reference links to.
- Cases and repeats: SM01 to SM04, two runs per case per arm, 16 sessions. The
  remaining two replace infrastructure failures only, never a completed run;
  unused, they stay unspent. Fix the run order before starting and alternate
  the arms.
- Packets: `python tools/eval_assets.py prepare --cases <cases file> --case <id>
  --method <arm>/skills/code-change --method <arm>/skills/test-writing --method
  <arm>/skills/software-architecture --output-parent <evidence directory>`; the
  executor installs nothing and runs no `git`.
- Grading: run the rubric's verification probes on each saved project, then the
  `required` and `reject` items. Record from the trace whether
  `stores-and-migrations.md` was read, and tokens, turns and wall time.
- Hard requirement: every verification observation of the case holds and no
  `reject` item applies.
- Effect: the candidate meets the hard requirement in at least two more of its
  six SM01 to SM03 runs than the baseline, with no more SM04 failures.
- No effect: a difference of one or none. Both arms at five or six of six means
  the base method already gets this right and the reference only costs context;
  both at one or none, check the traces for the reference read before revising
  text.
- Harm: the baseline ahead by two or more, or an SM04 failure only in the
  candidate.

A tie is no demonstrated improvement, not equivalence. Two runs per arm show a
large difference or a regression; they cannot show a small one.

## Pilot outcome (2026-11-25)

- Compared: the candidate, a frozen plugin tree at `687d78b`, against the same
  tree without the reference and its route line, whose code-change bytes equal
  `6242086`; test-writing and software-architecture were identical in both.
  Each session loaded code-change explicitly in its own directory, with no MCP
  servers, `git` or `pip`.
- Volume: 16 sessions of the 18, all observed as Sonnet at medium effort; no
  invalid run, so the two spare sessions stayed unspent. Run order was fixed
  in advance and alternated the arms.
- Departure from the design: the packets were not built with
  `tools/eval_assets.py prepare`; every session had the whole frozen plugin
  tree. The arms differed only in the reference and its route line.
- Grading: the probes, recalibrated on hand-written implementations first,
  then the `required` and `reject` items blind to the arm, by one grader.
- Hard requirement: baseline 6 of 6 on SM01 to SM03 and 2 of 2 on SM04;
  candidate the same. Probes passed in 16 of 16 runs, and no `reject` item
  applied in any.
- The reference was read in 1 of the 8 candidate runs (an SM02 run).
- Required items, outside the hard requirement: SM01, SM03 and SM04 full in
  every run; SM02 baseline 4 and 3 of 5, candidate 4 and 4 of 5.
- Cost: baseline 110 turns, 315 s and 39,333 output tokens; candidate 105
  turns, 276 s and 33,695.
- Verdict: no effect, a difference of none with both arms at six of six, which
  the design reads as the base method already getting this right. No harm.

The reference was removed for that reason: it cost context without changing an
outcome. Two runs per arm on one model cannot exclude a small effect, and with
one read in eight the pilot barely exercised the reference's text. A later
change on this subject reuses these cases and needs a case the base method
fails.
