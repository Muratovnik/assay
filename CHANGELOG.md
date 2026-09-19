# Changelog

Generated from the commit history under the
[Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) Angular
preset. Sections and entry format follow
[`conventional-changelog-angular`](https://github.com/conventional-changelog/conventional-changelog/tree/master/packages/conventional-changelog-angular);
every entry links to the commit that introduced it.

## [0.2.0](https://github.com/Muratovnik/assay/compare/v0.1.0...v0.2.0) (2026-09-19)

Two writing methods join the library, and the documentation set now exists in
English, Russian and Simplified Chinese: the README, the install guide, the
architecture and evaluation notes, the upgrade how-to, the discovery
explanation, the contributing guide and the security policy.

### Features

* **technical-writing:** a method for product documentation — README, how-to, tutorial, reference, explanation, runbook, ADR/RFC and release notes — written from its sources rather than from memory ([bd05e0f](https://github.com/Muratovnik/assay/commit/bd05e0fd4e5a83f50ae4f0f1c78c063d802213d7))
* **technical-writing:** a read-only preservation check that compares the protected regions of an edited document and reports what it could not classify instead of passing it ([a7cc3aa](https://github.com/Muratovnik/assay/commit/a7cc3aae6e19a1a1b34784ed4e35165081eba028))
* **technical-writing:** a README module with a selectable house style and two skeletons, public product and internal document ([95d39b6](https://github.com/Muratovnik/assay/commit/95d39b68cbfeb82b3e2b266bc8af8867850be787))
* **technical-writing:** the bundled README profile adopted as a project standard, scoped to the owner's public repositories and stated as such ([25293df](https://github.com/Muratovnik/assay/commit/25293dfbddb038c72b2f2844b8e029ea9f43cd5a))
* **text-writing:** an editorial method for ordinary prose — messages, letters, articles, portfolio and product copy — with separate profiles for Russian, English and Simplified Chinese ([f73fc02](https://github.com/Muratovnik/assay/commit/f73fc0221ac584b57e53e304b0ac4d536e4444c0))
* **text-skills:** a composition method shared by both writing skills ([59d0bbc](https://github.com/Muratovnik/assay/commit/59d0bbc46d7c4c68c08da208228ba1512166cf38))
* **text-skills:** the C1 method revision, with byte-exact fixtures admitted to the preservation suite ([e0d078e](https://github.com/Muratovnik/assay/commit/e0d078ec6042744d7a0fc4802f06ed139caa12ce))
* **tools:** the generated catalog block is now verified in every document that carries it, so a translated architecture page cannot drift from the catalog ([c101950](https://github.com/Muratovnik/assay/commit/c10195056563f806581eed611e91e3e8a72fcde2))

### Bug Fixes

* **technical-writing:** an unread link and an empty document are no longer reported as preserved ([d9430fc](https://github.com/Muratovnik/assay/commit/d9430fca5966c28899adf13fae41478ffe5f8bd6))
* **technical-writing:** the preservation check emits UTF-8, and a refuted region now outranks a merely unverified one in the exit code ([17adb58](https://github.com/Muratovnik/assay/commit/17adb5817e96bf12f4c8ac3f038a2a62ce2e61d7))
* **text-writing:** the protocol, the author profile and the Chinese control are exact ([1e6fb49](https://github.com/Muratovnik/assay/commit/1e6fb49d9ddc9e3577bbac7b93718e5c9642960f))
* **ci:** the exposure probe looks inside the ignored directories instead of naming them, which a fresh clone does not have ([15b0851](https://github.com/Muratovnik/assay/commit/15b085134caa0926dfcdbf846b7b55e9f33fe04d))
* **tests:** a reaped process entry is treated as a finished process ([8b93609](https://github.com/Muratovnik/assay/commit/8b936096c96ddda6419e6d97318f7c3a62f5d6a5))

## [0.1.0](https://github.com/Muratovnik/assay/releases/tag/v0.1.0) (2026-09-15)

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
