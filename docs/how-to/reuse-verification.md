# Reuse a recorded verification command

Use this in an Assay checkout when a verification result was captured with
`tools/command_receipt.py` and you need to compare it with the current candidate.
It is an optional contributor utility, not a tool installed by a singleton skill.
It needs Python's standard library and neither calls a model nor installs anything.

First decide which guarantee and exact command are relevant. The utility compares
only the files you name. It does not discover dependencies, check an external
service, determine whether tests are adequate or approve task completion.

## Capture an authorized check

Run from the repository root. Create an existing task-owned evidence directory
outside the source tree, such as `../assay-evidence`. Command output may contain
private data; do not publish that directory or its logs by default.

The following example captures the focused receipt tests and the two source files
they exercise. Use the same interpreter and environment for the intended check.

```text
python -B tools/command_receipt.py --execute --cwd . --output-parent ../assay-evidence --input tools/command_receipt.py --input tools/test_receipt_reuse.py -- python -B -m unittest tools.test_receipt_reuse
```

The JSON output supplies `packet`, `state`, `exit_code` and `manifest_sha256`.
Retain the packet path and digest in the owning task, outside the packet directory.
A failed run is retained too; do not replace it with a fabricated success record.
The capture command runs one direct process, not a sandbox. Imports, fixtures,
credentials and descendants remain the caller's responsibility.

## Compare without executing again

Replace `RECEIPT_DIRECTORY` and `RETAINED_DIGEST` below with those retained values.
The command after `--` must match the captured argument vector exactly; it is
compared as data, never executed by `reuse`.

```text
python -B tools/command_receipt.py reuse --receipt RECEIPT_DIRECTORY --manifest-sha256 RETAINED_DIGEST --cwd . --input tools/command_receipt.py --input tools/test_receipt_reuse.py -- python -B -m unittest tools.test_receipt_reuse
```

| Exit | Meaning |
| --- | --- |
| 0 | `matching-recorded-inputs`: successful recorded command, same working directory, same named input population and bytes, with no recorded input drift during the run |
| 1 | `not-reusable`: an identified mismatch or an unsuccessful prior run; inspect `mismatches` |
| 2 | Missing or invalid evidence/input, such as an unavailable file or a tampered receipt; no match established |

Every successful comparison still reports `command_executed: false` and
`acceptance_verified: false`. The comparison does not rewrite the receipt,
refresh its date or pretend the check has just run. Committing identical content
or changing an unrelated file does not invalidate the named byte comparison.
Adding a newly required input does: it was not covered by the old population.

## Decide what the comparison establishes

Before retaining a result, check that the named population is sufficient and that
relevant configuration, dependencies, interpreter, environment and external state
still match. The same `python` argument can resolve to a different executable if
PATH changes. Hash equality does not establish those conditions, exclude transient
writes or prove trusted provenance. A local digest protects recorded bytes, not
the truth of a report or isolation from the author of the receipt.

A mismatch calls for an affected check or investigation, not automatically every
suite. An unavailable comparison leaves that evidence unverified. Keep mandatory
owner gates and consumer-boundary checks even when a narrower receipt matches.
The method-level decision belongs to
[verification scope](../../skills/code-change/references/verification-scope.md).
