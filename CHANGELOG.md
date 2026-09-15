# Changelog

Generated from the commit history under the
[Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) Angular
preset. Sections and entry format follow
[`conventional-changelog-angular`](https://github.com/conventional-changelog/conventional-changelog/tree/master/packages/conventional-changelog-angular);
every entry links to the commit that introduced it.

## 0.1.0 (2026-09-15)

First public release. The library existed privately before this, and those
revisions are not listed: their numbering and evidence belonged to a workspace
this repository no longer describes.

### Features

* eight skills with their references and evaluation data: `code-maintenance`, `test-writing`, `test-audit`, `independent-audit`, `evidence-research`, `operations-ui-delivery`, `route-subagents` and `skill-design` ([11c4c93](https://github.com/Muratovnik/assay/commit/11c4c930005b754217db9f23c0bbfe0d4f22f695))
* **profiles:** two agent profiles as capability boundaries rather than personas, `evidence-reviewer` and `official-docs-researcher`, neither pinning a model ([11c4c93](https://github.com/Muratovnik/assay/commit/11c4c930005b754217db9f23c0bbfe0d4f22f695))
* **install:** a guarded link lifecycle where `plan` reports every target and rollback target without writing, `install-links` preflights the whole vector before the first write, and `uninstall-links` removes only exact links or adapter bytes ([11c4c93](https://github.com/Muratovnik/assay/commit/11c4c930005b754217db9f23c0bbfe0d4f22f695))
* **render:** client manifests, profile adapters and the skills index generated from `catalog.toml` and `VERSION`, verified byte-for-byte by the source check ([11c4c93](https://github.com/Muratovnik/assay/commit/11c4c930005b754217db9f23c0bbfe0d4f22f695))
* **route-subagents:** optional benchmark-evidence routing for model and effort selection, as a local MCP server the user registers themselves ([11c4c93](https://github.com/Muratovnik/assay/commit/11c4c930005b754217db9f23c0bbfe0d4f22f695))
* **tools:** evidence utilities for repeatable checks: frozen input-only evaluation packets, command receipts, native loader inspection and scoped quality-tool probes, each executing only after an explicit `--execute` ([11c4c93](https://github.com/Muratovnik/assay/commit/11c4c930005b754217db9f23c0bbfe0d4f22f695))
* **ci:** seven source gates on Linux and Windows, a publication audit and an owner-side pre-push guard ([11c4c93](https://github.com/Muratovnik/assay/commit/11c4c930005b754217db9f23c0bbfe0d4f22f695))
