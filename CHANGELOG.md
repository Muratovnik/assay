# Changelog

All notable changes to assay are documented here, newest first. The format
follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the versions
follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-09-15

First public release. The library existed privately before this; those revisions
are not listed, because their numbering, evidence and decisions belonged to a
workspace this repository no longer describes.

### Added

- Eight skills, each with its own references and evaluation data:
  `code-maintenance`, `test-writing`, `test-audit`, `independent-audit`,
  `evidence-research`, `operations-ui-delivery`, `route-subagents` and
  `skill-design`.
- Two agent profiles as capability boundaries rather than personas:
  `evidence-reviewer`, which reviews a frozen packet through a read-only oracle,
  and `official-docs-researcher`, which answers one bounded question from primary
  documentation. Neither pins a model.
- A guarded link lifecycle: `plan` reports every target and rollback target
  without writing, `install-links` preflights the whole vector before the first
  write, and `uninstall-links` removes only exact links or adapter bytes.
- Optional benchmark-evidence routing for model and effort selection, as a local
  MCP server the user registers themselves. It is not required, and no paid
  campaign or per-spawn network hook is part of it.
- Evidence utilities for repeatable checks: frozen input-only evaluation packets,
  command receipts, native loader inspection and scoped quality-tool probes. They
  execute only after an explicit `--execute`, and a capture is not a sandbox.
- Six source gates on Linux and Windows, plus a publication audit and an
  owner-side pre-push guard.

### Notes

No model runs in continuous integration and no skill carries a score. What the
evaluation data does and does not establish is documented in
`docs/evaluation.md`.
