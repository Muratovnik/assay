# Repository, onboarding, and release

A full prerelease audit covers files and consumer journeys even when gates pass. A narrow README review follows relevant entry points without silently expanding into qualification of every platform.

## Review files as product interfaces

Enumerate tracked files and relevant untracked/generated publication inputs. Establish purpose and consumer for root entries; review coherent source, documentation, and tooling groups, then exceptions. Distinguish nested independent roots, dependencies, generated output, and caches. State sampling/exclusions; do not claim every file was reviewed without coverage.

For significant files/groups establish audience (user, contributor, maintainer, integrator, tool), task, fact owner, discoverability, freshness, and role: canonical guidance, reference, explanation, example, projection, or historical/planning evidence. Recommend keep, merge, relocate, retire, or investigate only with a reason and preservation of unique constraints or unfinished work. Similar names, length, and document counts do not establish redundancy; disposition is not deletion authority.

Assess fitness for the destination separately from correctness and retention value. Establish why material content belongs in this delivery for its intended readers, using the brief, owner policy, and concrete reader needs. Public design rationale, contributor guidance, and intentionally published history can be appropriate; work useful only to a private operating process is not made suitable for every public channel by being accurate or labeled historical. Do not invent a universal ban on plans, history, or internal vocabulary.

Separate retained content, current normative role, and distribution fitness. A historical record can preserve imperative wording without instructing today's reader to execute it: assess its framing, entry points, links and actual consumers together. Conversely, an active onboarding path can prescribe a superseded procedure despite its status label. Show that contradiction or another concrete contract violation before blocking acceptance; possible wording clarification alone is optional advice. Neither archival framing nor grammatical form determines which recipients may receive the bytes.

Inspect root scripts and launchers: purpose, prerequisites, audience, supported environment, and relation to the main startup path should be discoverable without private history. Determine actual behavior before calling one redundant.

## Follow real reader journeys

From the advertised entry point, follow prerequisites, installation/startup, first useful action, troubleshooting, and deeper documentation for each in-scope audience. Public onboarding should not require reconstructing an internal implementation plan. Distinguish accessibility/navigation for the intended reader from suitability for distribution; a well-indexed document can still belong to the wrong audience.

Compare facts across README, requirements, examples, manifests, workflows, and packaging: versions, platform support, paths, commands, behavior, feature maturity, and security/storage/update/deletion claims. Distinguish different documentation roles without requiring a fixed folder scheme.

Check meaningful paths in code spans as well as Markdown links, stale commit references used as current guidance, and useful docs reachable only from a validator or internal index rather than the intended reader's path. An intentionally historical reference is not automatically stale guidance; a green link checker cannot establish navigation quality.

Preflight command effects, then where safe follow documented commands literally from the stated working directory with shipped templates. Do not silently fix a command or replace a failing example with a handwritten substitute. Record rescue steps and unexecuted portions.

For UX/DX claims observe the relevant rendered/interactive journey and failure states. A health endpoint does not prove catalog/discovery exposure or task completion. An unrelated screenshot or source inspection does not substitute for the candidate's interface.

## Distinguish checkout, environment, and distribution

A clean checkout is not a clean host. Record dependence on credentials (never values), private siblings, global tools/configuration, caches, and inherited environment. Worktrees and temporary directories may share host/Git state.

Separate local presence, Git tracking, artifact inclusion, required dependency, and actual loading/use. A clean-clone requirement does not alone prohibit optional local settings; a publication exclusion does not alone require local deletion. Conversely, ignored or optional state is not automatically safe: it may still be loaded, alter behavior, or enter a package. For a prohibition or exclusion check, identify which property it must enforce and test representative allowed and forbidden states, rather than treating a pathname or ignore rule as proof of every property.

Identify the actual in-scope distribution surfaces and their selection/access mechanisms: for example public repository trees or reachable history/tags, site builds, archives, packages, examples, and diagnostic bundles. Verify what recipients can obtain, not just what navigation advertises or which source paths changed. A move to an archive, a status label, or removing a link does not by itself exclude bytes from distribution. Conversely, a source file excluded from the named artifact is not thereby shipped. Current-tree cleanup does not establish historical withdrawal. Bound conclusions to the surfaces and stage actually inspected; do not demand remote publication to accept a local candidate or access unrelated private data.

For installation claims use the actual candidate archive/package, extracted tree, supported launcher, and shipped examples. Check applicable archive contents, licenses/notices, metadata, permissions/modes, relative paths, version identity, and startup/stop behavior, including process cleanup. Derive expectations from the owner's distribution contract, not a universal archive shape.

Exercise paths with spaces and realistic invalid input where relevant. Inspect failure diagnostics and exit/result status. A version response does not prove installation or useful operation. Cross-compilation does not prove native execution; one platform cannot satisfy another mandatory platform's claim.

Track:

`source identity -> artifact/digest -> platform/environment -> consumer action -> evidence`

Assess in-scope upgrade, backup/restore, rollback, and uninstall on disposable data. Do not manipulate real user data or devices. Keep rendering, validation, transport, activation, physical hardware, and clean-OS claims separate; simulation proves only the simulated layer.

## Judge the named release stage

Local candidate readiness, hosted validation, and downloaded published bytes are separate claims. Do not demand publication for local acceptance or treat workflow source as a successful hosted run. Use run-specific evidence for CI claims and downloaded bytes for published-artifact claims.

When integrity/provenance is required, bind the actual digest to the intended source, builder/workflow identity, and relevant parameters. An attestation/checksum file merely existing does not establish trusted coverage. Locate the packaging/validation owner before attributing a defect to shared release tooling.

Safely check applicable publication preconditions and refusal paths. Neither an audit nor its passing verdict authorizes tags, push, or publication. Keep required but unavailable platform, lifecycle, and integration evidence visible, not N/A.

## Reuse established mechanisms

Map existing gates to requirements and demonstrated gaps before recommending additions. Where useful, consult current primary sources:

- [Diataxis](https://diataxis.fr/how-to-use-diataxis/) for reader needs and document roles.
- [OpenSSF Best Practices](https://www.bestpractices.dev/en/criteria/0) for applicable criteria and [Scorecard](https://scorecard.dev/) for repository risk signals, not a complete release verdict.
- [SLSA verification](https://slsa.dev/spec/v1.2/verifying-artifacts) for source/build/artifact identity when provenance is used.

Recheck current documentation before prescribing behavior or versions. Frameworks are optional lenses, not imposed certifications. Prefer the maintained owner mechanism to an overlapping scanner or release framework. Owner policy defines acceptable content and exposure; semantic review evaluates purpose and consequences; gates enforce proven mechanical invariants. A secret, marker, schema, or link check is not evidence of audience fit unless it actually tests that claim. Do not replace semantic review with mandatory phrases, filename bans, file-count limits, or text-length assertions.

## Report this mode

Include actual file/audience coverage, significant purpose/disposition decisions, broken or confusing journeys, and the applicable source/artifact/platform evidence matrix. A green gate does not excuse omitted surfaces; missing evidence follows the main verdict rules.
