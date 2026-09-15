# Staged migration acceptance

Audit the current immutable source snapshot in `repo/`. No Git baseline is
provided. The complete consumers for this exercise are `clients/editor.json`
and `clients/partner.json`; there are no hidden live registrations to inspect.

This stage requires one canonical Runtime implementation, the editor using its
new path, and the partner's supported old interface forwarding to Runtime.
Both commands must return JSON with `owner: runtime` and exit 0. The documented
compatibility contract and historical material are part of the accepted design.
Do not broaden this to general repository or multi-platform release readiness.

Python 3.9+ and the standard library suffice. Launchers only print output and
exit. After inspecting effects, you may run them and the existing tests with
`python -B`. Do not modify the snapshot, install tools, or delegate. Report in
the conversation.
