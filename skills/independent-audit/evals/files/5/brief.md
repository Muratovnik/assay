# Publication candidate acceptance

Audit the frozen bundle in `repo/` for the public product-reference channel.
The owner requires product behavior and design rationale useful to users or
integrators. Historical design decisions are allowed when they explain supported
compatibility. Operational work-allocation and review-process records are kept
for the maintainer handoff, not distributed through this public channel.

`distribution.json` is the complete selection for the proposed public bundle;
all listed bytes will be available to recipients whether linked or not. No other
tree, Git history, remote or installed service is in scope. Accept selection and
content fitness, not a claim that publication has already run. Inspect all
supplied files; `python -B tools/check.py` from `repo/` is an authorized read-only
check. Do not edit, build a replacement, or publish.
