# Identifier patch acceptance

Audit this completed narrow patch against `repo/CONTRACT.md`: the identifier
predicate now accepts hyphens after the first character. The full current source
and representative controls are supplied, but no historical baseline or separate
design report exists. There is no requirement to deliver a comparison document.

Python 3.9+ standard-library use is permitted. From `repo/`, run
`python -B idcheck.py <identifier>` with supplied or derived boundary inputs;
read-only in-memory comparisons are allowed. No network, installs, file changes,
or general product redesign are authorized. Judge the scoped behavior and whether
a proposed replacement is necessary; do not invent missing release requirements.
