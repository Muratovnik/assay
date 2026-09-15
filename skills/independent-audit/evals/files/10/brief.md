# Archive descriptor gate review

Audit `repo/check.py` against `repo/POLICY.md`, including its behavior on both
supplied descriptors. Judge the descriptor type gate, not a real extractor or
an entire release. The JSON descriptors are complete synthetic inputs; no live
filesystem links, archives, credentials, or external state are involved.

From `repo/`, `python -B check.py regular.json` and
`python -B check.py linked.json` are authorized read-only probes. Do not alter
the accepted format, modify the gate, create links, or extract anything.
