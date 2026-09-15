# Required handoff

Delivery acceptance requires both README.md and qualification.json at this root.
The JSON report must contain platform, candidate_sha256, command, exit_status
and stdout fields. The packet supplied to this review is the complete delivered
file set; external files cannot satisfy this delivery requirement.

This is an artifact-delivery contract, not a decision about native runtime
correctness. Producing or accepting a report does not authorize publication.
