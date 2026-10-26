# Changelog

Generated from the commit history under the
[Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) Angular
preset. Sections and entry format follow
[`conventional-changelog-angular`](https://github.com/conventional-changelog/conventional-changelog/tree/master/packages/conventional-changelog-angular);
every entry links to the commit that introduced it.

## [0.32.3](https://github.com/Muratovnik/assay/compare/v0.32.2...v0.32.3) (2026-10-26)

### Bug Fixes

* **route-subagents:** a standing authorization to delegate in the user's own instructions that apply across projects now counts as authority, limited to the work its stated conditions describe; a project instruction still cannot grant it. The session reminder says "when the user authorizes subagents" instead of "requests", and eval cases O34-O35 cover the standing authorization and the repository-instruction control ([8cb7fcc](https://github.com/Muratovnik/assay/commit/8cb7fcc76a0957fdbd37e410e288a0a670836b32))

## [0.32.2](https://github.com/Muratovnik/assay/compare/v0.32.1...v0.32.2) (2026-10-22)

### Bug Fixes

* **route-subagents:** the session reminder shows the launch label form `<class>: <task>` instead of a class name from one route table, so a renamed table no longer gets an example with a class it lacks ([8fde00a](https://github.com/Muratovnik/assay/commit/8fde00a0d0d30855e8376ae8bbd8a1312a56a785))

## [0.32.1](https://github.com/Muratovnik/assay/compare/v0.32.0...v0.32.1) (2026-10-22)

### Bug Fixes

* **hooks:** the report check no longer asks again for an edit or a new file that an earlier message of the turn already reported with its line. A subagent's report or a task notification does not start a turn, so the check used to reach back to the owner's last prompt and repeat the request after every relayed message; in the live session where it repeated, 9 files were named before the fix and none after ([48d14e3](https://github.com/Muratovnik/assay/commit/48d14e3f8bac3901d06e604010842668f3af1e05))

## [0.32.0](https://github.com/Muratovnik/assay/compare/v0.31.0...v0.32.0) (2026-10-22)

Makes the hooks cheaper to run and quieter where they had nothing to say. A
hook starts in about half the time, a subagent's report or a task notification
gets one skill-check line instead of the full list, and a launch the routing
guard could not check is refused instead of running unrouted.

### Features

* **hooks:** the Claude manifest starts `python` in exec form, without Git Bash or shell quoting. The `Agent` and `Task` entry sets `onFailure: "block"` (Claude Code 2.1.295 or later), so a launch the guard could not check is refused; other tools go ahead as before. `SubagentStop` allows 15 seconds, because 33 of 1,018 live report checks passed 5 and were dropped ([df78da2](https://github.com/Muratovnik/assay/commit/df78da22f9cf89964f08c6c67ffc1e9101cbf298))
* **hooks:** a prompt that starts with `<task-notification>`, or carries `<agent-message` and `[Subagent hand-back]`, gets one line asking to decide again which skills apply if the report changes the task, and keeps the owner's last suggestion for a restore. Four of five full checks in 30 live sessions went to such prompts. A message from another session still gets the full check ([ed65d34](https://github.com/Muratovnik/assay/commit/ed65d34ff921e92ff96937f300041464c6b2f8bd))
* **hooks:** the first external fetch while evidence-research is not loaded is refused once, like an owner question without critical-discussion; the repeat passes. As a note it arrived with the source already read and was followed by a load in 4 of 14 live cases. Rule `midturn-evidence-research` ([3156df7](https://github.com/Muratovnik/assay/commit/3156df7e0b2b88e3e8317000afbfd2fad86f4a53))
* **route-subagents:** the assignment packet states a return budget, by default about 1,500 tokens with longer detail in a named file, and tells the worker to send long command output to a file. A dependent chain that prints long logs, or a batch of task-record updates, counts as context-heavy work for one worker ([a0b1e24](https://github.com/Muratovnik/assay/commit/a0b1e246a00a9e099023446284555fc127d9e505))

### Performance Improvements

* **hooks:** routing evidence and host observations load only where a launch or session start needs them. A synthetic `PreToolUse` on Windows takes 145-160 ms instead of 300-320 ms ([93089da](https://github.com/Muratovnik/assay/commit/93089da6d874c743cebf2a07196beb221d2a62d3))

### Bug Fixes

* **route-subagents:** route-candidates matches a harness by lexical identity, so `claude-code` finds "Claude Code", and prices a board that publishes only run totals as total per attempt when every priced row ran the same number of attempts ([f95c051](https://github.com/Muratovnik/assay/commit/f95c051f92047f9fb4f4ae53e15f5e54cff106b0))

## [0.31.0](https://github.com/Muratovnik/assay/compare/v0.30.0...v0.31.0) (2026-10-19)

Moves the hooks from "load the skill" to "apply its rule at the decision point".
A question to the owner waits for critical-discussion, a scenario rerun five
times points at the diagnostic reference, and a turn that changed code or wrote
a plan is held to the verification, reuse and existing-solution lines the skills
now ask for. The checks see that a line is missing, not whether it is right.

### Features

* **hooks:** an `AskUserQuestion` call while critical-discussion is not loaded is refused once with a note naming the need behind the choice, doing nothing, existing solutions and each option's basis; the repeated call passes. The row always takes the `deny` form because a note reaches the model only after the owner has answered. Rule `midturn-critical-discussion` ([b3cc40b](https://github.com/Muratovnik/assay/commit/b3cc40b8bee8693859b213feb50c83c21e28d037), [a1fe3a3](https://github.com/Muratovnik/assay/commit/a1fe3a3f251d26192999f51810af58eda1af9c3a))
* **hooks:** the fifth `Bash` or `PowerShell` run of the same script or test command since the owner's last message, while code-change's `references/diagnostic-reproducer.md` is unread since the latest compaction, gets one note pointing at that reference. Task notifications and compactions do not restart the count; results and exit codes are not read. Rule `rerun-diagnostic-reproducer` ([8e736e0](https://github.com/Muratovnik/assay/commit/8e736e0badff57fd46ec468480950421c5babab3), [9ca6a86](https://github.com/Muratovnik/assay/commit/9ca6a86d400d9e308bb9565d5b349e53b967ab60))
* **skills:** code-change asks for `Verified: <check> — <environment> — after <change>` and `Not verified: <what> — <why>` lines after editing code, and ui-delivery refers to them; the reuse line is written for every new source file, as `Reuse: not applicable — <why>` for project-specific code; implementation-planning asks a plan file for a `What already exists` section. Localized labels count ([dd36093](https://github.com/Muratovnik/assay/commit/dd3609372992373ede98c8898c7403b9c99f0c4e))
* **hooks:** at `Stop` and `SubagentStop`, a turn that edited code, created a source file or wrote a plan without the matching line continues once with one note listing each missing line; a shell edit is seen through the files the turn stages with `git add`. It joins a branch-check note in the same continuation. Rules `report-verification`, `report-reuse`, `plan-existing` ([e0d886d](https://github.com/Muratovnik/assay/commit/e0d886d2d49873604c98d5436a85fd0baf30ba3a))
* **critical-discussion:** the description and the skill check cue cover choosing between approaches and framing a request or decision, and the skip narrows from "plan" to "write a plan"; three discovery cases cover the change. Discovery has not been run ([3b143ec](https://github.com/Muratovnik/assay/commit/3b143ecdcff67926682fb4843b9540e8f1543ee1), [ae01c7e](https://github.com/Muratovnik/assay/commit/ae01c7ef2fd9674f3cf1cbd94db950e3770dd4b1))

### Bug Fixes

* **code-change:** verification scope says that behavior depending on the consumer's environment — operating system, installed build, user profile, host process or runtime version — is checked there, and a pass elsewhere is a reported gap ([7b7a361](https://github.com/Muratovnik/assay/commit/7b7a36134b38d83bc981832f075da6b510d4710d))

## [0.30.0](https://github.com/Muratovnik/assay/compare/v0.29.0...v0.30.0) (2026-10-19)

Finishes the routing cleanup of 0.29.0. Exempt agent types are a plain list,
the routing checklist at session start follows the configuration the launch
check uses, including the plugin binding, and a worker names the skills it
loaded on the first line of its report.

### ⚠ BREAKING CHANGES

* **routing:** `pipeline.unrouted_agents` takes only a list of agent types. The object form that mapped a type to `baseline`, `inherit` or a model was validated but never used after the advisor's removal; a configuration that still has it, an empty `{}` included, is refused and refuses launches with a message saying what to write instead, for example `[]` for `{}` ([fcd04d7](https://github.com/Muratovnik/assay/commit/fcd04d7c078b53d4c7e87401eacfa4fb3dbf0838))

### Features

* **hooks:** the routing checklist at session start appears whenever the hook resolves a routing configuration with a route table for its client, through `ASSAY_ROUTING_CONFIG` or the `routing.json` binding, instead of only when the variable is set. It now describes the route table — a task class at the start of the launch's description with exactly that class's model and effort — instead of the removed advisor. A retired or unreadable configuration keeps the checklist and adds why launches are refused; session start never fails over routing ([02d061e](https://github.com/Muratovnik/assay/commit/02d061e449ddc3f5f8fc3cf056adc8ba786afa9a), [d34c547](https://github.com/Muratovnik/assay/commit/d34c5472083b928575d0d3a3c0c84dc09bb87de5))

### Bug Fixes

* **route-subagents:** a packet tells its worker to name each Assay skill it loaded on the first line of the report, with an example such as Used `assay:code-change`, instead of pointing at an undefined `Assay:` line; an exact output format the packet fixes still takes precedence. In paired diagnostic runs on Haiku with identical packets, the example form named the loaded skills in 3 of 3 reports against 1 of 3 for the previous wording ([5d9e409](https://github.com/Muratovnik/assay/commit/5d9e4091b47f38c0c9fa918e49c114cc9f7137dd))

## [0.29.0](https://github.com/Muratovnik/assay/compare/v0.28.1...v0.29.0) (2026-10-19)

Assay drops the parts that stopped producing evidence: the frozen routing
advisor, the required routing mode, routing execution history and telemetry,
and the feedback recorder with the hook event log. The
route table and its launch check stay as they were, and so do the benchmark
evidence service, host observations and every other hook. Configurations and
bindings left in the old form are refused with a message naming the fix, never
skipped; the upgrade steps are in the route table reference.

### ⚠ BREAKING CHANGES

* **routing:** routing configuration schema 5 is required. A configuration that names an older schema or still carries the sections `advisor`, `policy`, `telemetry` or `task_evidence`, or the required-mode `pipeline` keys, is refused with one message listing every key to remove; `pipeline.mode` accepts only `evidence-only`, and there is no migration command ([8d93796](https://github.com/Muratovnik/assay/commit/8d93796cba96b46a098b98c42ab1861083700a4c))
* **routing:** the plugin's routing binding `routing-telemetry.json` is renamed to `routing.json` with the same `config` and `cache_dir`; a binding left under the old name refuses route-table launches until it is renamed, and `ASSAY_ROUTING_TELEMETRY_CONFIG` is refused while `ASSAY_ROUTING_CONFIG` is kept. Hooks doctor reports `routing_binding_found` and `routing_config_found` instead of `routing_telemetry_bound` ([8d93796](https://github.com/Muratovnik/assay/commit/8d93796cba96b46a098b98c42ab1861083700a4c))
* **routing:** the MCP tools `prepare_routing`, `get_advisor_input`, `complete_routing`, `get_routing_decision`, `authorize_routing_launch` and `record_routing_outcome` are removed, and `get_routing_context` no longer takes a task query; the router commands for advice, history, replay, telemetry and task evidence and `tools/assay.py claude-routes` are removed. Agent definitions that `claude-routes` generated are not deleted for you: remove them and their `.assay-routing-v2` manifest and lock as the upgrade steps describe ([8d93796](https://github.com/Muratovnik/assay/commit/8d93796cba96b46a098b98c42ab1861083700a4c), [b0da5a2](https://github.com/Muratovnik/assay/commit/b0da5a2b73f52e9be04deee94abba50a7a6c6922))
* **hooks:** the hook options `record_events`, `feedback_capture` and `feedback_trigger` are removed, and a hook configuration that still names one is refused with a message listing it; feedback records and hook events are no longer written, and the feedback commands and their doctor keys no longer exist. Route-table enforcement does not depend on these options ([6f2652f](https://github.com/Muratovnik/assay/commit/6f2652fec95d14f80305e1352d88e67607f1f135))

### Documentation

* **routing:** describe configuration schema 5, the `routing.json` binding, the doctor keys and the upgrade from 0.28 in the route table reference and the hooks guide, and remove the advisor, required-mode and telemetry prose from the references, the architecture overview and the installation guide in all three languages ([b0da5a2](https://github.com/Muratovnik/assay/commit/b0da5a2b73f52e9be04deee94abba50a7a6c6922))

## [0.28.1](https://github.com/Muratovnik/assay/compare/v0.28.0...v0.28.1) (2026-10-18)

### Bug Fixes

* **routing:** recognize Codex's namespaced `collaborationspawn_agent` tool name so native launches are checked against the configured class, model and effort instead of bypassing the route table. A recognized launch is denied when its configured routing binding is unreadable or invalid, and malformed launch input cannot bypass the check ([e69fc8f](https://github.com/Muratovnik/assay/commit/e69fc8f890014e339c3ac0ccb3b7a2b852ea09fd))

## [0.28.0](https://github.com/Muratovnik/assay/compare/v0.27.1...v0.28.0) (2026-10-17)

### Features

* **check:** the source check requires every file under `references/` and `examples/` to be linked from its skill's own SKILL.md, instead of accepting a file reached only through another reference, and a reference over 100 lines to open with a `## Contents` list that links its other second-level headings. Eight references in route-subagents, technical-writing and ui-delivery are now linked from their SKILL.md and 44 long references open with a contents list. Skill frontmatter rejects the reserved words claude and anthropic in a name and XML tags in a name or description ([e178c9c](https://github.com/Muratovnik/assay/commit/e178c9c91fb4e10882e77f339e3f271b9e6980c7))
* **install:** `plan`, `install-links` and `uninstall-links` take a repeatable `--kind skill|profile`, so the two profiles can be linked beside a client plugin that already supplies the skills; with `--kind profile` the skill link chain and the explicit-skill prerequisite do not apply. In Codex, which cannot take agent definitions from a plugin, this removes the second listed copy of every skill ([4f9fbdc](https://github.com/Muratovnik/assay/commit/4f9fbdc82fee8514a5898aaa0c295ddfee5bde68))

## [0.27.1](https://github.com/Muratovnik/assay/compare/v0.27.0...v0.27.1) (2026-10-17)

### Bug Fixes

* **check:** the hint check reads a description's "Use for" and "Use on" clause as its trigger part, as it already read "Use when", and the software-architecture hint names architecture. In paired first-turn runs on Sonnet from an empty directory, a question about a project's architecture loaded software-architecture in 3 of 3 runs in Russian and in English, against 2 of 3 before; a variable rename loaded it in none ([11a1459](https://github.com/Muratovnik/assay/commit/11a1459508b7b95608a1891a8c26842723af297c))
* **feedback:** the correction journal skips a leading block a client inserts before the request, such as an editor selection, and «вижу» counts as a correction only with a finding («вижу, что …») or a mention of the agent, so an observation that opens a new task no longer becomes a candidate ([1381118](https://github.com/Muratovnik/assay/commit/1381118b6884542e85a9ac9b0fec3bae727df0bc))

## [0.27.0](https://github.com/Muratovnik/assay/compare/v0.26.0...v0.27.0) (2026-10-17)

### Features

* **activation:** the critical-discussion hint names the judgment ("whether an idea, plan or tool is worth it or covers a need") instead of the topic, and the evidence-research description no longer claims gap assessment. In paired first-turn runs with the owner's full plugin set, a request to review which skills a library lacks loaded critical-discussion in 3 of 3 runs on Sonnet and on Opus, against 0 of 3 and 1 of 3 before; near-negative requests gained no false loads ([d5324a9](https://github.com/Muratovnik/assay/commit/d5324a9db40f3c7b78bfb1b57f7e0533418610a4))
* **check:** the source check fails a skill reference or example that no relative link reaches from its SKILL.md, a skill without `agents/openai.yaml` or without a row in any of the three README tables, and a skill hint that shares no key term with the trigger part of its description ([dae5d9e](https://github.com/Muratovnik/assay/commit/dae5d9e1c536941e69e6fc7e55761ec1f89c8233), [e52ad4d](https://github.com/Muratovnik/assay/commit/e52ad4d0e50d60a4544f5e83a6bc7b772e803800), [6b81a3d](https://github.com/Muratovnik/assay/commit/6b81a3db399062ae4c3e7e2db349df070be10f04))
* **code-change:** a confirmed defect gets a variant analysis branch that sweeps for its other occurrences, and a question about why something fails, with no repair requested, takes a read-only diagnostic entry that changes nothing ([0515b92](https://github.com/Muratovnik/assay/commit/0515b928eec250f9fb482f9be884a5e8e8b90894), [84bb4f7](https://github.com/Muratovnik/assay/commit/84bb4f7ce23bed29977472c2b3b1ec4bfe0569c5))
* **feedback:** the correction grammar of the feedback journal reads the first six sentences of a request and recognises many more Russian and English correction phrasings, still without a model call ([25fe138](https://github.com/Muratovnik/assay/commit/25fe1387d4ab905c6b42755f21ea17cf8d772faa))
* **hooks:** in Claude Code a tool call that shows the work of a skill the session has not loaded (an external fetch, a source, test, interface or documentation edit, a skill file edit) gets one note per skill and request naming the skill and the decision it governs. `skill_note_form = "deny"` refuses the first such call instead; each row turns off by its own ID in `disabled_rules`. Codex is not covered: its skill loads cannot yet be recognised reliably ([5bd66be](https://github.com/Muratovnik/assay/commit/5bd66bec4d804210beba4c58d1f894ba6daf675b))
* **instruction-maintenance:** add a method for editing, compressing, reviewing and extending agent instruction files without losing a rule's trigger, force, quantifiers, negations or identifiers; it reports a size target it cannot meet instead of dropping rules and routes a lesson to its layer. In paired runs on a dense instruction file it kept every probed qualifier where ordinary editing lost four or five, and it loaded on its own for three of four instruction-editing requests ([a81827f](https://github.com/Muratovnik/assay/commit/a81827fc6abf15af78b15df411c88183dd47dd07))

### Bug Fixes

* **hooks:** the skill check bound is raised so the check no longer exceeds it with the current skills, and a test keeps room for one more skill entry ([f95ac85](https://github.com/Muratovnik/assay/commit/f95ac851a4394aaeb5a2827f97226bfcf070765f))

## [0.26.0](https://github.com/Muratovnik/assay/compare/v0.25.0...v0.26.0) (2026-10-16)

### Features

* **critical-discussion:** add a discussion method that challenges an idea or tool instead of agreeing by default. It recovers the underlying need, treats an example as a sample of the system rather than its scope, compares the idea with doing nothing and with existing solutions, requires coverage and migration evidence before calling a part unnecessary, and changes its position only on new evidence. implementation-planning, research-driven-change and product-flow-mapping route idea-only discussion to it. Its evaluation corpus is not yet executed, so no model run supports the method yet ([39bdc9b](https://github.com/Muratovnik/assay/commit/39bdc9b2485a138cbdb9fb7cb77ff076273c2c4c))
* **hooks:** in Claude Code a turn that visibly meets the reading condition of a loaded skill's reference without reading it continues once, with one note naming each such reference. The signs are an edited `.vue` file (code-change's Vue structure), changed check configuration or `git mv` (effective quality checks), a reviewer launch (independent-audit's bounded review), a new plan file (implementation-planning's units), an edited interface file (ui-delivery's acceptance and visual judgment), documentation prose in Russian or Chinese (technical-writing's languages) and a claim that no solution exists or none qualifies (evidence-research's search and coverage). Each row turns off by its own ID in `disabled_rules`, and a disabled skill drops its rows ([660a9a0](https://github.com/Muratovnik/assay/commit/660a9a0d79370f14e5f70d6e917740877ebcaac7), [ee2ec0b](https://github.com/Muratovnik/assay/commit/ee2ec0b5f98b60bf5cb82c13b1a9594d42b19ed8))

## [0.25.0](https://github.com/Muratovnik/assay/compare/v0.24.0...v0.25.0) (2026-10-13)

### Features

* **hooks:** the skill check no longer asks for an `Assay:` line at the start of every reply and again at the end. The agent names each skill it starts applying once, as `assay:<name>` with its purpose, and stays quiet while the skills in use still fit; in Claude Code the check lists the skills the session already loaded. The Claude skill gate reads announcements and loads from the transcript, so a resumed, forked or compacted session keeps its loads, and its continuation keeps the answer already given instead of asking for a new one ([ca560cf](https://github.com/Muratovnik/assay/commit/ca560cf5f3c23defc4be56700e61efb68f7b403c))
* **hooks:** in Claude Code the first WebFetch result of a request gets a note that the result is a model's answer about the page, not its text, and that a conclusion resting on the page needs the downloaded text. A turn that says a file or URL was read in full continues once when the transcript shows the file read only in part or the URL opened only through WebFetch. `disabled_rules` turns them off separately as `fetch-note` and `read-claims` ([2ed9334](https://github.com/Muratovnik/assay/commit/2ed93340d86f147a7b77b13f34c05d66db581b24))

### Bug Fixes

* **hooks:** the skill check says that a missing tool does not make a skill inapplicable, so an agent without web tools no longer skips evidence-research and answers from memory ([18d26b6](https://github.com/Muratovnik/assay/commit/18d26b6f0ed1cb6a222fc433419e6d59df002716))
* **hooks:** a turn with no full-read claim stops the transcript scan at its start, so a stop in a long session stays within the hook's timeout ([f3d8c45](https://github.com/Muratovnik/assay/commit/f3d8c450e5e7d02a218d7422408a2834afb25155))

## [0.24.0](https://github.com/Muratovnik/assay/compare/v0.23.1...v0.24.0) (2026-10-12)

### Features

* **hooks:** subagents get the Assay skill check at their start in Claude Code and Codex, since they never receive the per-request check; it says the skills their packet names apply and where to read each SKILL.md without the skill tool. In Claude Code the skill gate also holds a subagent's report to the skills that subagent loaded. route-subagents packets now name the Assay skills their work needs ([ec035d3](https://github.com/Muratovnik/assay/commit/ec035d39e254b9ef1bb4831b2b200e1a9510e05a))
* **retrospective:** add a tool-neutral retrospective skill that reviews a period of agent work for recurring friction, reconciles it with the rules already in force and proposes evidence-backed, owner-routed changes for the user to decide ([b59b7a1](https://github.com/Muratovnik/assay/commit/b59b7a1a90dbf2f3781bf7eafb9056a57309f276))

## [0.23.1](https://github.com/Muratovnik/assay/compare/v0.23.0...v0.23.1) (2026-10-12)

### Bug Fixes

* **route-subagents:** the refusal of an agent launch made inside a Claude subagent no longer starts with a doubled `Assay:` prefix ([603f28e](https://github.com/Muratovnik/assay/commit/603f28e7f2eff653921720dd14fdc7be007eba6c))

## [0.23.0](https://github.com/Muratovnik/assay/compare/v0.22.0...v0.23.0) (2026-10-12)

### Features

* **route-subagents:** with an evidence-only Claude configuration the hook refuses an agent launch made inside a subagent, since Claude Code lets subagents nest by default and such a child skips the primary's route choice; the refusal names the one-level rule and tells the worker to do the step itself or name it in its report. Codex hook input does not name the calling agent, so the references point to `agents.max_depth` there and say why the rule exists ([6cde3c5](https://github.com/Muratovnik/assay/commit/6cde3c559b0bccfe344a2fad02f5dbc7e9c8cbf3))

## [0.22.0](https://github.com/Muratovnik/assay/compare/v0.21.0...v0.22.0) (2026-10-12)

### Features

* **route-subagents:** with a route table configured, a spawn the table does not check (a continuation, an owner-exempt agent type or a switched-off check) gets a short pointer to the table and the rule for choosing a class instead of the advisor-era launch reminder; without a table the reminder is unchanged ([6aa22d6](https://github.com/Muratovnik/assay/commit/6aa22d6fcdafd640eccb5102edd1de1fa755ba45))

## [0.21.0](https://github.com/Muratovnik/assay/compare/v0.20.0...v0.21.0) (2026-10-12)

### Features

* **route-subagents:** a route-table refusal now also says how to choose a class: by the work, not by a pair chosen beforehand, and the less demanding class when two fit; an admitted launch gets a note naming its class and asking for a one-line reason, which nothing enforces. A session still holding an older skill learns the rule from the hook reply alone ([9e04d7d](https://github.com/Muratovnik/assay/commit/9e04d7ddf5ba1b14603ee9c4b245505539ebcca0))

### Bug Fixes

* **route-subagents:** show a Codex task-name example the client accepts (`gather_...`) in a class refusal ([7489836](https://github.com/Muratovnik/assay/commit/748983659575c6f448e7d21670241cc64f5d8cd7))

### Documentation

* **hooks:** say that a Claude launch without a route table must name both model and effort ([a142ee4](https://github.com/Muratovnik/assay/commit/a142ee4e329db9e7fb27690d9562e6af9484c2bb))

## [0.20.0](https://github.com/Muratovnik/assay/compare/v0.19.0...v0.20.0) (2026-10-12)

### Features

* **route-subagents:** enforce an owner route table of task classes, each with one model and effort, on Claude `Agent`/`Task` and Codex `spawn_agent` launches in evidence-only mode: a launch declares its class at the start of the Claude `description` or the Codex `task_name` and must carry that class's pair; a missing or unknown class, another pair, a Codex `fork_turns` that inherits the parent's settings, a Codex custom agent file that pins other settings and a `CLAUDE_CODE_EFFORT_LEVEL` that overrides the call are refused with the class list; `routing_status` returns the table, and `route-candidates` proposes the cheapest cached pair within a score band of the best ([fd1835c](https://github.com/Muratovnik/assay/commit/fd1835cb0728dc3ebb6c50d6f51b359f170fc4c0))

### Documentation

* **route-subagents:** make the route table the default routing path and mark the routing advisor, local task evidence and required routing as frozen; state that Claude Code 2.1.292 and later takes effort in the spawn call, that the Codex hook checks `spawn_agent` launches when a table is configured, and that `PreToolUse` runs for every tool ([e4a81ea](https://github.com/Muratovnik/assay/commit/e4a81ea19afac312bb8471d5a88bab94a51dbc47))

Without a route table, launches are checked as in 0.19.0. The table check was
exercised with synthetic hook events; a live Codex launch through it has not
yet been observed.

## [0.19.0](https://github.com/Muratovnik/assay/compare/v0.18.0...v0.19.0) (2026-10-12)

### Features

* **route-subagents:** refuse an evidence-only Claude subagent launch that names no model or no effort, so a routed child never silently inherits the session's settings, and record which model and effort each launch actually ran with as `host_observations`; `pipeline.explicit_routes: "off"` turns the check off ([9addee6](https://github.com/Muratovnik/assay/commit/9addee6a0d5b74f51a5f126db1ae44ce01f3be94))
* **route-subagents:** bind benchmark labels to the available models by the host provider's brand instead of a stored table of names, so a new model binds as soon as it is in the inventory; ambiguous or duplicate labels are excluded rather than guessed ([249998e](https://github.com/Muratovnik/assay/commit/249998e817e8509e4eeca34cbbc7f46c210e842b))
* **route-subagents:** take Claude's effort levels from the client, so an inventory entry may omit them, and reject placeholders such as `default` or `inherit` as levels ([46809a4](https://github.com/Muratovnik/assay/commit/46809a42b8764769f06bf912635a500255d5a3ed))
* **route-subagents:** keep a route whose published score interval lies wholly below an adequate alternative's out of price selection, and choose between unpriced routes by effort and measured quality instead of candidate ID ([5967587](https://github.com/Muratovnik/assay/commit/59675873bfc3d8d7618e1f466c84e20939c53544))

## [0.18.0](https://github.com/Muratovnik/assay/compare/v0.17.7...v0.18.0) (2026-10-11)

### Features

* **hooks:** replace the English/Russian phrase hints with a short per-request skill check: the agent states which Assay skills apply and loads them, whatever the language of the request; explicit skill choices still work ([20282e0](https://github.com/Muratovnik/assay/commit/20282e01ba73a069a39d9d7df7dca2474e8d5e98))
* **hooks:** in Claude Code, continue a turn whose reply names Assay skills the session has not loaded, so they are loaded and the work is checked against them; the skill check now asks for the loads before any other tool call and judges skills by the task rather than by the tools at hand ([39ade63](https://github.com/Muratovnik/assay/commit/39ade63482bd52345958df8f9b1242a7bb1ce5f9))

### Bug Fixes

* **evidence-research:** treat how a current product or tool behaves, and whether a ready-made solution exists, as research rather than a lookup from memory ([fa90c2e](https://github.com/Muratovnik/assay/commit/fa90c2e246c1a5a4e8a47caa21185e2e2af2ab62))
* **hooks:** let the read-only reviewer and documentation researcher return their reports in Claude Code, and let the researcher use the web tools its profile grants ([cbc52d2](https://github.com/Muratovnik/assay/commit/cbc52d2654633f21adeaaa7cd807970a39a9b3e5))
* **profiles:** launch the read-only reviewer and documentation researcher only when delegation has been authorized ([87d06f3](https://github.com/Muratovnik/assay/commit/87d06f35cab65b047e3cacd7e8326f24fd4728ff))
* **routing:** keep rejected or unavailable routing from launching subagents with inherited maximum settings, and check fallback launch arguments locally ([3ca06ba](https://github.com/Muratovnik/assay/commit/3ca06ba79e3493c6871a3ec2edc9d7f627a12751))

## [0.17.7](https://github.com/Muratovnik/assay/compare/v0.17.6...v0.17.7) (2026-10-11)

### Bug Fixes

* **tests:** create scratch parents for routing telemetry and hook identity fixtures in fresh checkouts ([c311020](https://github.com/Muratovnik/assay/commit/c31102066d5a15ed07c9754b74cc17665ab56c9b))

## [0.17.6](https://github.com/Muratovnik/assay/compare/v0.17.5...v0.17.6) (2026-10-11)

### Features

* **routing:** retain task and execution evidence for retrospectives with explicit privacy controls ([a47eedb](https://github.com/Muratovnik/assay/commit/a47eedb7df6184ae56739564dbd309e8f3cdbaea))

### Bug Fixes

* **routing:** preserve boundaries and distinguish requested launch settings from observed native execution in telemetry ([996ed8d](https://github.com/Muratovnik/assay/commit/996ed8d1e58a0290f4071b1283713aeb7c2ceb40))
* **routing:** reject invalid advisor exchanges before execution and preserve their diagnostic evidence ([42891c0](https://github.com/Muratovnik/assay/commit/42891c0985a20d1b31cb76cc1c035729aea24d6b))
* **routing:** provide bounded reviewer handoffs, correct Codex and Claude usage identity, and restrict reading profiles to the capabilities their clients can enforce ([9025bf4](https://github.com/Muratovnik/assay/commit/9025bf44bd31bbe828f1dc2ef9db0f64d8fb31bf))

Reviewer launches now require the objective, review mode, frozen contracts,
snapshot, owned scope and oracle status. Codex reading profiles disable shell,
apps, goals and further delegation; Claude profiles use a reading-tool allowlist.
Hook enforcement still depends on native hook trust and available worker identity.
These changes do not establish general task-adequacy accuracy or subscription
quota savings.

## [0.17.5](https://github.com/Muratovnik/assay/compare/v0.17.4...v0.17.5) (2026-10-10)

### Bug Fixes

* **technical-writing:** trace acquisition, prerequisites and first use through the reader's own task and actual artifact handoffs; clarify delegated checks and validate evidence reconstruction metadata before writing files ([e8a7732](https://github.com/Muratovnik/assay/commit/e8a7732aeb7b228d971ad168c42c696913f779f4))

The retained study distinguishes failed original workflows from a separately
corrected derivative. Its reserved comparison is a tie; it does not establish a
general improvement in effectiveness or autonomous reliability.

## [0.17.4](https://github.com/Muratovnik/assay/compare/v0.17.3...v0.17.4) (2026-10-09)

### Bug Fixes

* **routing:** preserve adequate selection, dispatch identity and complete cost evidence ([bd39402](https://github.com/Muratovnik/assay/commit/bd39402379bc54e6d4d6fae8039010a79b518ea3))

## [0.17.3](https://github.com/Muratovnik/assay/compare/v0.17.2...v0.17.3) (2026-10-09)

### Bug Fixes

* **evals:** validate UI case/rubric pairs and labelled trigger formats, and preserve complete runtime resources in frozen skill packets while excluding evaluator data ([dd57baf](https://github.com/Muratovnik/assay/commit/dd57baf243b2c4f5a9fec5694efeab26a7c64afd))
* **writing:** match content and detail to the document's purpose, distinguish durable records from transient prose, and keep examples and review reports within the reader's needs ([a9a7b74](https://github.com/Muratovnik/assay/commit/a9a7b746c382be1f57cd960be1635ec6b005fc85))

## [0.17.2](https://github.com/Muratovnik/assay/compare/v0.17.1...v0.17.2) (2026-10-08)

### Bug Fixes

* **writing:** select claims and detail for the document's purpose, check delivered review reports for unnecessary repetition, and preserve the narrower scope of copyedits and preserve-all requests ([4812353](https://github.com/Muratovnik/assay/commit/4812353dda751a4818eebff2b50a154262961b83))

## [0.17.1](https://github.com/Muratovnik/assay/compare/v0.17.0...v0.17.1) (2026-10-07)

Delegation uses task-specific recommendations by default. A binding caller
choice now requires a declared justification or an actual user-confirmation
reference, including partial choices and choices with an omitted origin.

### Bug Fixes

* **routing:** reject unexplained caller overrides before retrieval, preserve justified exceptions and their provenance, retain history privacy and diagnostic replay, and keep user choices and dispatch constraints binding ([6e676b1](https://github.com/Muratovnik/assay/commit/6e676b14bb67c5114f933fb23c1e8115f6eb39bf))

## [0.17.0](https://github.com/Muratovnik/assay/compare/v0.16.1...v0.17.0) (2026-10-07)

Native routing now asks whether each model and effort pair can meet the concrete
assignment, then compares measured costs among adequate candidates. New configs
use this policy; existing configs retain their declared policy until explicitly
migrated with `migrate-config --native-decisions`.

### Features

* **routing:** use named task-adequacy questions and packet-local evidence, select adequate routes by comparable benchmark or supported paired task costs, separate unknown adequacy and cost from fallback, and include task criteria and privacy scope in cache identity ([2da38a0](https://github.com/Muratovnik/assay/commit/2da38a0cc22d0f12743729f6a63838ed45a4e4fb))

### Bug Fixes

* **routing:** remove the shared 24 KiB native input ceiling while keeping a separate result limit and complete candidate inventory ([14c656e](https://github.com/Muratovnik/assay/commit/14c656e19140758572a97bc895a2993177ef743d))
* **routing:** preserve explicit-choice provenance and distinguish selected routes from recorded fallback ([0a481a9](https://github.com/Muratovnik/assay/commit/0a481a97ea4b07278346631fde241310451f1acf))
* **routing:** compare benchmark quality and expense without anchoring the recommendation to the caller baseline ([671c860](https://github.com/Muratovnik/assay/commit/671c8607526cda2dc461d31d54cd0e45434cf441))
* **routing:** preserve packet assessment bindings when cached advice is reused ([a8f2542](https://github.com/Muratovnik/assay/commit/a8f2542e5b33c20dd3461d0faf8fda11e55edf39))
* **routing:** put readable quality and expense evidence alongside the complete native snapshot ([a1e4d2d](https://github.com/Muratovnik/assay/commit/a1e4d2d3ba6470fd30e4408533b9b7eb092b3117))
* **routing:** deliver large private Claude inputs through native tools and validate foreground replies ([c795675](https://github.com/Muratovnik/assay/commit/c79567504ff2f482d64fc89ac2c889131796aca6))
* **routing:** accept an omitted empty uncertainty list for known assessments while requiring grounds for unknown judgments ([6a6eafe](https://github.com/Muratovnik/assay/commit/6a6eafe2d9fc30e113fd665909cae4fa058cc680))

Cost comparisons stay within matching cohorts and cost units. Task inference,
unmeasured alternatives and conflicting evidence remain explicit uncertainties;
benchmark USD does not establish subscription quota savings or the cost of a new
assignment. Structural checks do not establish the accuracy of every adequacy
judgment.

## [0.16.1](https://github.com/Muratovnik/assay/compare/v0.16.0...v0.16.1) (2026-10-06)

Technical documentation now selects material for its reader and publication
surface before arranging it, and the finished draft is reviewed for passages
that add nothing this reader needs. Three foundational research studies are
published in English and Russian.

### Bug Fixes

* **technical-writing:** select, condense, move or remove material for the reader, task, publication surface and authorized scope before choosing headings; make README demonstration, installation and first-use blocks conditional, so a catalog-managed install or automatic operation gets no ritual section; review the finished draft for re-explained familiar terms, claims repeated across prose, headings and table cells, process provenance and purposeless modifiers, while keeping necessary conditions, newcomer explanations, acceptance evidence and required notices; reconcile related current claims after a behavior change; keep the preservation checker's strict exit codes and report an authorized deletion instead of hiding it; add 13 public regression cases and two discovery inputs ([d5766ab](https://github.com/Muratovnik/assay/commit/d5766ab2670dc1fd98127cab8bd2764d6196be0f))

### Documentation

* **research:** publish the research-quality, software-engineering and LLM reasoning and behavior control studies in English and Russian, with paired indexes ([46740f2](https://github.com/Muratovnik/assay/commit/46740f2eb8d0db046eec2842f8b20a0354837ee6))

The technical-writing change was exercised on a small set of synthetic tasks
with one model configuration, and those tasks are now public. Automatic
discovery, other models and broader prose quality have not been established.

## [0.16.0](https://github.com/Muratovnik/assay/compare/v0.15.0...v0.16.0) (2026-10-06)

Code changes now establish the capability a guarantee needs and consider
existing implementations before writing their own, entered by concrete kinds of
behavior rather than a judgment of materiality. Corrections and acceptable
examples can be kept as explicit local records for later review, and the Claude
evidence reviewer promises only the boundary the client keeps.

### ⚠ BREAKING CHANGES

* **profiles:** the Claude `evidence-reviewer` is a bounded reader with `Read`, `Grep` and `Glob`; it no longer reruns the oracle or loads skills, so callers include snapshot-bound receipts for the named oracle and pass audit criteria by path, and a packet without receipts is refused; the Codex projection keeps the oracle ([18fd6c6](https://github.com/Muratovnik/assay/commit/18fd6c6b023a0c53656bb96cffbdc83db2442b3b))

### Features

* **code-change:** establish which capability provides an unchecked guarantee before choosing the implementation; enter the reuse reference before writing or keeping own code for behavior that commonly has an existing implementation, such as parsing, validation, retries, caching, dates, hashing, CLI arguments, HTTP clients, pathfinding or asset loading; name a semantic mismatch as the gap instead of skipping the check; report the decision in a `Reuse:` line and an unrequested missing capability in an optional proposal line ([18fd6c6](https://github.com/Muratovnik/assay/commit/18fd6c6b023a0c53656bb96cffbdc83db2442b3b))
* **implementation-planning:** list the conditions a project should supply, separating observable facts from owner decisions, and the costly decision categories that need the contract check, each with a nearby control ([18fd6c6](https://github.com/Muratovnik/assay/commit/18fd6c6b023a0c53656bb96cffbdc83db2442b3b))
* **evidence-research:** borrow code, behavior or assets from another project through one procedure for provenance, terms, compatibility and the permitted operation; mark sources recalled from memory as not opened, name independence axes, compare on a discriminating basis without a query quota and stop in four stated situations ([18fd6c6](https://github.com/Muratovnik/assay/commit/18fd6c6b023a0c53656bb96cffbdc83db2442b3b))
* **hooks:** record corrections and allowed examples with an explicit command, keep the storage mode separate from the optional correction-grammar trigger, review metadata records with codes and a basis reference instead of text, and print the record command in `doctor`; recognize Russian lookups for an existing implementation ([18fd6c6](https://github.com/Muratovnik/assay/commit/18fd6c6b023a0c53656bb96cffbdc83db2442b3b))

### Bug Fixes

* **route-subagents:** keep the session reminder to three sentences while preserving the subagent planning step for any wording of the request; add the routing checklist at session start only when routing is configured, and tell packet builders what a reviewer without the oracle needs ([18fd6c6](https://github.com/Muratovnik/assay/commit/18fd6c6b023a0c53656bb96cffbdc83db2442b3b))
* **tools:** check heading anchors in links between skill files ([18fd6c6](https://github.com/Muratovnik/assay/commit/18fd6c6b023a0c53656bb96cffbdc83db2442b3b))

### Documentation

* **how-to:** describe project conditions for agents, client settings that guard tests and check configuration, feedback records with their privacy limits, and what each install route lacks ([18fd6c6](https://github.com/Muratovnik/assay/commit/18fd6c6b023a0c53656bb96cffbdc83db2442b3b))

The added evaluation cases are public synthetic examples, and no model run was
performed for this release. Better decisions, task outcomes or lower cost have
not been established.

## [0.15.0](https://github.com/Muratovnik/assay/compare/v0.14.0...v0.15.0) (2026-10-04)

Task continuation now recovers the selected work, current constraints and
applicable verification. Repairs trace connected preparation stages to the
consumer outcome, and command receipts can compare named inputs with a retained
successful run.

### Features

* **workflow:** load relevant methods before decisions, preserve live hints for plain continuation requests, carry unresolved outcomes and applicable evidence between stages, compare exact command receipts with explicit acceptance limits, and evaluate delivered artifacts with five executable scenarios and valid controls ([26f00fd](https://github.com/Muratovnik/assay/commit/26f00fd414c9a16194cc8b554bb05f474c277b11))

### Bug Fixes

* **tests:** publish complete readiness markers separately for each acquisition worker and verify that cancellation stops every detected process, releases the source lock and preserves cache failure semantics ([26f00fd](https://github.com/Muratovnik/assay/commit/26f00fd414c9a16194cc8b554bb05f474c277b11))

Both collections delivered all five public synthetic exercises in a bounded
comparison. General improvements in task success and execution cost remain
unestablished.

## [0.14.0](https://github.com/Muratovnik/assay/compare/v0.13.0...v0.14.0) (2026-10-04)

Code changes now choose evidence of correctness before deciding to add tests.
Existing coverage can be reused when sufficient, while explicit testing requests,
required project checks and real consumer boundaries retain their protection.

### Features

* **code-change:** choose verification before adding tests, distinguish diagnostic checks from regression protection, refresh results when relevant inputs change, and reconcile completion with the original consumer outcome; planning links to this decision and test-writing retains independent expectations ([8531707](https://github.com/Muratovnik/assay/commit/853170764f9515aaa288679290a7fbc183de8e0d))

The additional evaluation cases are public synthetic examples. Improved task
outcomes and lower execution cost have not been established by a paired comparison.

## [0.13.0](https://github.com/Muratovnik/assay/compare/v0.12.1...v0.13.0) (2026-10-04)

UI delivery now researches suitable references before custom implementation,
starting with the existing design system and the concrete gap. Runtime changes
connect generated-code compilation, actual build inputs and identity lifetime to
evidence from the reached execution stage. Codex SessionEnd hooks use the client's
three-second timeout limit.

### Features

* **ui:** research visual direction, component patterns or product behavior before a material custom implementation; use Refero Styles and The Component Gallery as optional reference catalogs, record the mechanism, fit, limits and adoption decision, and reuse sufficient existing evidence for local repairs ([795482b](https://github.com/Muratovnik/assay/commit/795482b9fd0698f04e41d2a40afe03c5ca829d6a))

### Bug Fixes

* **skills:** validate final generated code with the operation's compiler and references, account for actual runtime inputs and scoped drift, test identity guarantees over the consumer's required lifetime, and distinguish enabled functions, reached stages and helper success from completed operations; add 12 decision scenarios without claiming measured task effectiveness ([8200322](https://github.com/Muratovnik/assay/commit/820032212f18e86d8cbcba1c508b100611c6cfcd))
* **hooks:** set Codex SessionEnd to three seconds so loading the plugin no longer requires the client to clamp its timeout; preserve other hook limits ([cfdccc1](https://github.com/Muratovnik/assay/commit/cfdccc1541b967c52b02bb324599961c7f548732))

### Documentation

* **ui-delivery:** refresh Figwright 0.6.0 guidance for end-to-end connection checks, process-scoped file claims, actual resize results and variant property ownership; pin source references and retain older-adapter recovery paths conditionally ([427e345](https://github.com/Muratovnik/assay/commit/427e345a5c9a0d1cec6290e70be20884f5eff2c5))

## [0.12.1](https://github.com/Muratovnik/assay/compare/v0.12.0...v0.12.1) (2026-10-02)

Planning and delegation now connect risky dependencies to evidence from their
real consumers. Resource recovery distinguishes partial acquisition, cancellation
and an uncertain result after a lost reply. Routing receipts report invalid input
instead of silently dropping it.

### Bug Fixes

* **workflows:** verify material prerequisites before dependent work, test real producer output at its consumer and check the supported delivery path; preserve resource ownership through failures, distinguish a product defect from a wrong oracle or broken fixture, and retain current evidence in handoffs; add 13 public regression and control scenarios for evaluating these decisions ([f39fc01](https://github.com/Muratovnik/assay/commit/f39fc0170a4a34b0e90151c66a0bc876b4fe2bed))
* **hooks:** honour an explicit English or Russian plan-only modifier in the first request paragraph, including restored session hints, while preserving explicit skill choices and ignoring quoted examples ([f39fc01](https://github.com/Muratovnik/assay/commit/f39fc0170a4a34b0e90151c66a0bc876b4fe2bed))
* **route-subagents:** expose typed receipt input and output schemas, reject unknown fields and malformed or excessive evidence references with actionable errors, preserve supported legacy aliases and nullable observations, and keep CLI help usable without the optional MCP SDK ([f39fc01](https://github.com/Muratovnik/assay/commit/f39fc0170a4a34b0e90151c66a0bc876b4fe2bed))

## [0.12.0](https://github.com/Muratovnik/assay/compare/v0.11.0...v0.12.0) (2026-10-01)

Subagent routing now starts by identifying useful, bounded work before substantial
solo work begins. Delegation hints preserve the requested primary workflow when
the optional routing skill is unavailable or disabled.

### Features

* **route-subagents:** plan useful delegation around a concrete outcome, its consumer, launch timing and full cost; defer a packet only with a specific trigger, and check and use its return before integrating it; session reminders introduce this planning step early, with bounded English and Russian hints for direct delegation requests ([96096c1](https://github.com/Muratovnik/assay/commit/96096c16e35d93788352e9f6db869058c0b47d89))

### Bug Fixes

* **hooks:** preserve implementation, review or research as the primary workflow when the delegation hint is disabled, missing or explicitly negated; recognise file paths, dotted identifiers and URLs inside delegation arguments without crossing sentence boundaries, and invalidate saved intent when the delegation grammar changes ([96096c1](https://github.com/Muratovnik/assay/commit/96096c16e35d93788352e9f6db869058c0b47d89))

## [0.11.0](https://github.com/Muratovnik/assay/compare/v0.10.0...v0.11.0) (2026-09-30)

Assay now gives bounded skill hints for the current prompt and client, and
preserves required routing decisions when optional hints are unavailable.
UI delivery and comment cleanup retain the evidence needed to verify a change.
Existing evidence-only routing configurations keep their behavior.

### ⚠ BREAKING CHANGES

* **route-subagents:** private advisor launches in Claude required mode now need `CLAUDE_CODE_DISABLE_BACKGROUND_TASKS=1` in the environment that starts Claude; without it the guard refuses the launch, because background completion notifications can expose the private advisor result; this native switch disables all background tasks for that Claude session, including worker and Bash tasks; Assay does not change client settings automatically ([9ef9a84](https://github.com/Muratovnik/assay/commit/9ef9a84f0036b571724cb7560dcaf8e683c64c15))

### Features

* **hooks:** add client-specific manifests, prompt hints, bounded optional session state, diagnostics and read-only routing preflight; reintroduce skill reminders after resume and compaction, omit quoted examples and code from prompt matching, and keep basic reminders and required routing guards available without the optional parser ([9ef9a84](https://github.com/Muratovnik/assay/commit/9ef9a84f0036b571724cb7560dcaf8e683c64c15))
* **skills:** preserve UI evidence through implementation and handoff, and keep unresolved feedback and essential evidence when cleaning up comments ([2394b5a](https://github.com/Muratovnik/assay/commit/2394b5a05afaf33f07920929a374d2dd29faa237))

### Bug Fixes

* **route-subagents:** replace private Claude advisor returns with schema-valid neutral results, preflight every selectable advisor route against its generated definition, and refuse protected launches on unsupported required-mode adapters ([9ef9a84](https://github.com/Muratovnik/assay/commit/9ef9a84f0036b571724cb7560dcaf8e683c64c15))

## [0.10.0](https://github.com/Muratovnik/assay/compare/v0.9.0...v0.10.0) (2026-09-29)

Required routing now passes the routed model in the Agent call and generates
definitions only for effort, which the call cannot carry. A rolling alias is
resolved by the host rather than guessed, a configured baseline answers when the
advisor cannot, and every route is checked before the first launch.
Evidence-only configurations keep their behavior.

### ⚠ BREAKING CHANGES

* **route-subagents:** required mode needs a `baseline`, and without one launches outside `unrouted_agents` are refused; agent types in `unrouted_agents` no longer inherit the parent's model but launch with the baseline model unless the configuration gives them a model or `"inherit"`, and a different model from the caller must be routed; generated definitions no longer stop a worker whose observed effort differs from its route, the mismatch blocks continuation once it stops; run `tools/assay.py claude-routes` again after upgrading, then `claude-routes --prune` to remove the definitions of 0.9.0 ([e4521bb](https://github.com/Muratovnik/assay/commit/e4521bb985eb615c4308d8f3ec247b5c4a21204b))

### Features

* **route-subagents:** route a profile listed in `pipeline.profiles` with the model alias in the Agent call and one generated definition per profile and effort, keeping model-pinned variants for full model IDs, which the call does not accept; record what the host resolves each alias to, so a changed resolution becomes an inventory event that suspends the alias's confirmed evidence names until `inventory-confirm` runs again; select the baseline as a fallback when the advisor abstains, gives invalid advice, ends without a result or is disabled; report which cached benchmark sources name each inventory model with up to five candidate spellings, and confirm one with `inventory-confirm --evidence-name`; check every selectable route, the baseline per profile and the model of each exempt type in `doctor` and `routing_status`; keep the launch reminder silent on Claude launches in required mode, and delete the generation lock with `claude-routes --remove` ([e4521bb](https://github.com/Muratovnik/assay/commit/e4521bb985eb615c4308d8f3ec247b5c4a21204b))

## [0.9.0](https://github.com/Muratovnik/assay/compare/v0.8.0...v0.9.0) (2026-09-29)

Skill evaluation adds evaluation design and bounded iterative improvement, and
route-subagents adds an opt-in required routing mode for Claude Code. Every
existing routing configuration keeps its behavior unless it selects that mode.

### Features

* **route-subagents:** add an opt-in required routing mode for Claude Code in which a separately launched advisor fetches its private input and submits its own answer, workers run through immutable model/effort definitions generated by `tools/assay.py claude-routes`, and the plugin hook admits only registered launches; user choices, owner-listed native agents and existing agent definitions stay usable, the inventory is renewed without a reconnect, and `claude-routes --remove` uninstalls the definitions; without `pipeline.mode: "required"` the hooks return no decision and the evidence-only workflow is unchanged ([54edf80](https://github.com/Muratovnik/assay/commit/54edf80f13a7bd5bfdd76aeae43c05a344cec079))
* **skill-evaluation:** design an evaluation with a covered task population, calibrated evaluators, blinded and order-varied comparisons and separate working, selection and final evidence, and improve a skill in bounded steps against a fixed baseline, objective, budget and stopping rule; optional case metadata is validated and the repository accepts only public metadata ([f00e1e9](https://github.com/Muratovnik/assay/commit/f00e1e93fc8f7a23f89c6d7b9d99e569ec44fb2d))

## [0.8.0](https://github.com/Muratovnik/assay/compare/v0.7.0...v0.8.0) (2026-09-26)

Two new methods: product flow mapping, which reconstructs an existing product's
journeys from evidence for a redesign or test handoff, and research-driven change,
which carries an evidence-backed change through planning, implementation, review
and delivery. Three skills are renamed to match their scope, and the source checks
now parse metadata and links with maintained parsers and check every skill as a
standalone copy.

### ⚠ BREAKING CHANGES

* `code-maintenance` is now `code-change`, `operations-ui-delivery` is now `ui-delivery` and `skill-design` is now `skill-evaluation`, together with their catalog IDs, native link targets and adapters; no old-name aliases are shipped, so remove existing links with the previous revision before installing this one ([7716739](https://github.com/Muratovnik/assay/commit/7716739440ffa2eed65012a2ceb5069a7467a034))

### Features

* **product-flow-mapping:** reconstruct an existing product's journeys and trace its screens, states and controls to evidence, keeping observed, adopted and proposed behavior apart, with a bidirectional inventory and paired description and screenshot frames for a designer; UI acceptance and design transfer route journey reconstruction to it, and test writing consumes the same scenarios ([630e59c](https://github.com/Muratovnik/assay/commit/630e59ca2164a468df851a52318150d33827a947))
* **research-driven-change:** carry a change from need through evidence, decision, plan unit, implementation, verification and the requested delivery, entering at existing research, a plan, a changed artifact or review feedback without restarting sufficient prior work; research, planning, code change, skill evaluation and audit link back to it and keep their own authority ([5b76f5c](https://github.com/Muratovnik/assay/commit/5b76f5c5f12f5ad0116af940308fb83a5862e87b))

### Bug Fixes

* parse skill frontmatter and adapter YAML with one local safe loader and check name, description, compatibility, allowed-tools and metadata against the Agent Skills specification; parse links with markdown-it-py, including reference links and HTML resources, and check the full collection and every single skill in copied layouts with declared optional peers; `uninstall-links` no longer depends on unrelated publication checks but still refuses linked sources, foreign targets and modified adapters ([7716739](https://github.com/Muratovnik/assay/commit/7716739440ffa2eed65012a2ceb5069a7467a034))

## [0.7.0](https://github.com/Muratovnik/assay/compare/v0.6.0...v0.7.0) (2026-09-26)

Two new methods: implementation planning for a bounded change or a staged
roadmap, and software architecture for boundaries, contracts and code placement.
Skills now link to the method that owns a rule instead of restating it, so each
criterion has one owner.

### Features

* **implementation-planning:** plan a bounded change or a staged roadmap from the actual project, with outcome-sized units, real dependencies, observable acceptance and the readiness of the next stage, then replan affected work and continue safely after an interruption; code maintenance, UI delivery and independent audit link to it, and independent audit also reviews plans ([74a203c](https://github.com/Muratovnik/assay/commit/74a203c6f33f29c48fd5b58b1fe022ffed0a5dd5))
* **software-architecture:** reconstruct a system's current architecture, design boundaries, place and share code, assess a proposal or an implementation and apply an adopted FSD profile; code maintenance, implementation planning and independent audit link to it for boundary, contract and placement decisions ([07eecca](https://github.com/Muratovnik/assay/commit/07eecca30e936e3540aa34c0057ddc6b917418b4))

### Bug Fixes

* **skills:** give each contract and reuse criterion one owner: planning keeps contract-change authority and recovery from recurring complaints, effective quality checks keep exception and end-state probes, reuse and migration keep delegation, exception approval and the terminal-state policy; a facade now expresses visual tokens through the library's theme where one exists ([06d9236](https://github.com/Muratovnik/assay/commit/06d92362e771277b62f1e0a9f03979ec0babd06a))

## [0.6.0](https://github.com/Muratovnik/assay/compare/v0.5.0...v0.6.0) (2026-09-23)

Subagent routing now scopes vendor guidance to the exact models a host has and
brings benchmark evidence up to date when that inventory changes. The UI skill
gains a procedure for organizing a design-system library for its consumers and
a clearer account of what a complete transfer requires.

### Features

* **operations-ui-delivery:** organize a design-system library for its consumers, cover broad transfer completeness and capture readiness, add Figma library mechanics through the Figwright adapter, and resume interrupted multi-step work from the current artifact ([f005a6c](https://github.com/Muratovnik/assay/commit/f005a6cd2f036b8b5f8d0de8cdd60b9206fe10ac))
* **route-subagents:** scope GPT-6 and Opus 5.5 guidance to the models and surfaces it documents, match reviewed CursorBench model names, give a newly confirmed inventory one bounded early benchmark check with per-model matching diagnostics, and read Terminal-Bench 4.0 from the publisher's public JSON API before the opt-in browser route ([519cf94](https://github.com/Muratovnik/assay/commit/519cf94698ccc9bc6af625df8cfb18713e4f8d9f))

### Bug Fixes

* **route-subagents:** check a new inventory only against sources the host can fetch, so a browser-only source with the browser disabled keeps its fresh snapshot instead of recording a failure and backing off ([066cf4f](https://github.com/Muratovnik/assay/commit/066cf4f6a96f7802c91eb0bdd9dd5a4199391a30))
* **route-subagents:** report fresh data during a backoff as cached, and evict the oldest inventory checks first when the history is full ([f56e4a4](https://github.com/Muratovnik/assay/commit/f56e4a41ac776c8d31daf5e47f2374fa864eb290))
* **route-subagents:** let an enabled browser read Terminal-Bench when the API refuses an anonymous read; rate limits and other client errors still never substitute for it ([f5de75b](https://github.com/Muratovnik/assay/commit/f5de75b637ee05b36896c2d94125132ed94bd0bc))

Guidance scope and model-name matching are registry contracts checked against
fixtures, not live retrievals or model evaluations; confirm the Terminal-Bench
API with the online smoke in the installed environment before relying on it. The
new UI decision cases are specifications, and no behavioral run is claimed.
Reconnect the MCP server after updating its code.

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
