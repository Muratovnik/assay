# Canonical ownership and compatibility

Runtime owns `runtime/launcher.py`, the only behavioral implementation.
The editor uses this path. The external Partner v1 consumer requires
`legacy/launcher.py`; Runtime owns that entry point as a forwarding adapter.
Behavior changes must be made in the canonical implementation, not copied.

The old interface remains supported until Partner v2 is certified against the
new interface. At that milestone, update the partner registration and retire
the adapter together. This stage deliberately precedes that milestone.

The complete consumer set is `clients/`. Commands run from this repository's
root and must emit `owner: runtime` with exit 0. No long-lived process is created.
