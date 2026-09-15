# CSV importer acceptance

Audit the importer and its implementation choice against `repo/CONTRACT.md`.
The two input files are synthetic supported examples, not an exhaustive format
suite. This immutable packet has no Git history. Python 3.9+ is the existing
runtime; no third-party dependency or network access is needed for the review.

From `repo/`, running `python -B importer.py simple.csv` and the same command with
`quoted.csv` is authorized. Read-only standard-library comparisons in memory are
also permitted. Do not edit source, install packages, or implement a replacement.
Return acceptance evidence and any justified remedy, not a general release audit.
