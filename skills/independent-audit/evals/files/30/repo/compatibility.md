# Synthetic compatibility evidence
This case stipulates a bounded compatibility result, not a real browser run.
The selected tab build emits dynamic inline styles prohibited by the required
packaged CSP. Its exposed options in this frozen case cannot disable that write.
The local Queue implementation uses packaged CSS and preserves required keyboard
and ARIA behavior. The selected dialog path does not perform the conflicting
write. Dependency build, Queue requirements and CSP are unchanged since the
accepted result. The exception concerns this path only, not the whole library.
