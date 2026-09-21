# Changelog

Generated from the commit history under the
[Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) Angular
preset. Sections and entry format follow
[`conventional-changelog-angular`](https://github.com/conventional-changelog/conventional-changelog/tree/master/packages/conventional-changelog-angular);
every entry links to the commit that introduced it.

## [0.5.0](https://github.com/Muratovnik/assay/compare/v0.4.0...v0.5.0) (2026-09-21)

The operational UI skill now covers the whole life of a UI artifact: designing a
new screen, implementing a reference in code, transferring an existing interface
into an editable design, editing a component library, and reviewing any of them.

### Features

* **operations-ui-delivery:** cover every layout mode from one entrypoint and add conditional procedures for the component system, design transfer and the Figwright adapter ([856bbc1](https://github.com/Muratovnik/assay/commit/856bbc1a8af3b22f5843b60575edc74c5f766ee6))

Each mode names what establishes quality and which check distinguishes it. The
new procedures own what the existing ones did not: shared bases, transitive
reuse and property effects that must be observable; the duties that only a
transfer carries, from fixing the source to migrating without breaking
relations; and the adapter rules for reading documentation before choosing a
method, checking every result and recovering from a partial write. Existing
owners gained the source of truth for each decision, theme and token resolution
through the composition, geometry depth, asset provenance and capture readiness.

These are instructions, not a runner: nothing here installs a tool or measures
behavior. The library-organization commands are named from the adapter source
at a pinned revision ([baa643f](https://github.com/Muratovnik/assay/commit/baa643f56e550788d44080035c3cd58f2e8985cf)),
so a client should still be asked which tools it exposes.

## [0.4.0](https://github.com/Muratovnik/assay/compare/v0.3.0...v0.4.0) (2026-09-20)

### Features

* **routing:** ship plugin reminders for applicable skills at session start and after context compaction, and reinforce required routing before subagent launches ([e248ab8](https://github.com/Muratovnik/assay/commit/e248ab842fa200b93107b13ec4855bd7f2f0e716))

Reminders are included in the full Codex and Claude Code plugin. They require
Python 3.11+ available as `python`; Codex also requires native hook trust.
Skills-only installations do not connect plugin hooks. These bounded reminders
make no model or network calls and do not enforce or authorize delegation.

## [0.3.0](https://github.com/Muratovnik/assay/compare/v0.2.0...v0.3.0) (2026-09-20)

Subagent routing gains optional advice, historical task evidence and estimates of
the cost of a complete work chain. Recommendations remain advisory: the caller
chooses and launches workers using its current model inventory.

### Features

* **routing:** request bounded advice through a caller-selected native economy model or the optional Jev adapter, with policy checks and local decision history; external advice requires separate consent ([b8bd160](https://github.com/Muratovnik/assay/commit/b8bd160a87480a2b452b3c66ba02948efe977cca))
* **routing:** retrieve similar measured tasks and estimate complete-chain costs, including retries, verification and coordination; API prices, tokens and subscription quota remain separate, and missing measurements stay unknown ([04e58f9](https://github.com/Muratovnik/assay/commit/04e58f9929a59ab29e7b618f2475d5fb58b29a9c))
* **routing:** automatically prepare a missing public task corpus when task evidence is enabled, or prefetch it with `task-setup`; pinned source checksums, cache reuse, offline mode and download status cover the first-use workflow ([9926ea1](https://github.com/Muratovnik/assay/commit/9926ea16bf27e0ea443748fd12a4766bd60a4d85))

### Bug Fixes

* **routing:** retain historical results and costs when the source models are absent from the current inventory, without transferring their scores to newer models or letting empty candidate estimates crowd out evidence ([54c3fba](https://github.com/Muratovnik/assay/commit/54c3fba539a3545ae1e56216ad6bc994c20f16e4))

Task evidence is opt-in through `task_evidence.enabled` in a v2 routing
configuration. The initial corpus covers 528 LiveCodeBench tasks and 13 historical
models; it is coding-task context, not measured subscription savings or coverage
of every workflow. Reconnect the MCP server after updating its code or configuration.

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
