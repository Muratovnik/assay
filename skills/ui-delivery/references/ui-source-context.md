# Explicit UI source identity

Use only when a confirmed source-discovery or stale-byte problem needs an
additional check. Read the existing owner instructions first. No source lookup
failure, no mandatory command or new document.

The optional [command](../scripts/ui_context.py) accepts only sources selected by
the caller, relative to the owning product. For example, after confirming that
these paths actually exist and own the relevant decisions:

```text
python <skill-directory>/scripts/ui_context.py --root <product-directory> --source tokens=src/styles/tokens.css --source primitives=src/components/Button.vue
```

It prints role, relative path and SHA-256 to stdout, returns nonzero for missing,
unsafe or duplicate paths, and neither writes a manifest nor changes client
configuration. It does not crawl the repository, follow symlink sources, download
anything or search for credentials. Keep its output in existing task evidence, not in
skill source. The caller must have permission to read the selected files.

A hash establishes byte identity, not authority, semantic freshness or design
compliance. Choose sources from existing instructions and confirmed component
owners. Do not turn generated token values into a second normative source, require
a specific filename, infer that a missing DESIGN.md means greenfield, or call this
command a design-system detector. It is not a hostile-filesystem sandbox.
