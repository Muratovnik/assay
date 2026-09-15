# Local migration acceptance

Review the current immutable source snapshot in `repo/`. No Git history or live
host registration is supplied; do not infer which commit introduced a problem.

Required for this stage:

1. `runtime/launcher.py` is the canonical launcher, owned by Runtime.
2. All consumers listed in `repo/clients/` execute that canonical owner. This
   directory is the complete consumer population for this isolated exercise.
3. `tools/validate.py` accepts valid JSON configuration and rejects missing,
   non-integer, boolean, or out-of-range ports with a diagnostic and nonzero exit.

Retained historical documentation is allowed. Deleting all legacy files is not
a requirement; active consumer behavior is. Packaging, native multi-platform
qualification, deployment, and live workstation settings are outside scope.

Python 3.9+ and its standard library suffice. The candidate scripts only print
output and exit; they do not start real services. You may inspect and run them
locally using `python -B` after reviewing their effects. Keep the snapshot
unchanged and report in the conversation. Do not install dependencies or delegate.
