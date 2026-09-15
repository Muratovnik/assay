# Evidence packet acceptance

Assess the submitted verification summary in `repo/summary.json` against the
recorded observations and supplied probe. Acceptance requires evidence of both
an actual trailing LF (code point 10) and a literal backslash followed by `n`.
Each coverage claim must identify the observation that actually used that value,
with its real exit and output. This is evidence qualification, not acceptance
of a product runtime or proof of a previous hosted execution.

The full frozen subject is supplied in `repo/`. Read all files. From there,
`python -B probe.py controls.json` is the only authorized executable probe;
it emits observations without writing files. Do not edit, search elsewhere,
install anything, or infer Git identity from the surrounding directory.
