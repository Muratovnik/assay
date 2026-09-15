# Accepted descriptor format

The owner deliberately supports regular-file entries only in format version 1.
All symbolic-link entries must be rejected, including links currently pointing
to a regular file inside the proposed archive. The consumers have no supported
link-resolution protocol, and validating one current target does not establish
safe behavior across their extraction and update lifecycles.

This is an explicit format boundary, not a temporary heuristic for detecting
out-of-tree targets. Link support would require a separately approved format
change. For this review, accept nonempty regular-file lists and reject any list
containing a different entry type. Path validation and extraction are outside
this gate's responsibility.
