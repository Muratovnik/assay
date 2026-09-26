# Evidence tools

These tools make selected checks repeatable. They do not install skills, change
client settings, spawn agents, manage task state, or certify model quality.
`command_receipt.py`, `quality_scope.py`, and `repro_check.py` execute only after
an explicit `--execute`. Their commands may still have effects: the caller must
review the executable, imports, hooks, inputs, credentials and output location.
A command capture is not a sandbox or an independent oracle.

## Source gates

Use Python 3.11+ in an isolated environment. Install the validation dependency
with `python -m pip install -r requirements-tools.txt`; no tool installs it for
you. PyYAML parses native adapter data, with a local SafeLoader that rejects
duplicate keys, aliases, unsafe tags and ambiguous invocation booleans. This
is a supported adapter subset, not a claim to validate every possible YAML
extension. Block, flow, quoted and folded scalar forms remain supported.

The audit-packet suite requires an existing project-owned ignored temporary
directory. From this repository root, initialize it for the current shell:

```powershell
New-Item -ItemType Directory -Force .cache/audit-eval-tests | Out-Null
$env:AUDIT_EVAL_TEST_TMP = (Resolve-Path .cache/audit-eval-tests).Path
```

```sh
mkdir -p .cache/audit-eval-tests
export AUDIT_EVAL_TEST_TMP="$PWD/.cache/audit-eval-tests"
```

```text
python -B tools/check.py --all
```

The original owner tests still run. The added audit-packet tests were already
present but absent from the workflow. `catalog_docs.py --write` updates only
the marked architecture table; it never rewrites the independent expected
inventory in `compatibility_fixture.py`. Evaluation validation checks declared
case/rubric IDs and input paths. It does not execute fixture code or a model.
The Markdown-only skill-evaluation evaluation remains explicitly manual.

## Frozen input-only packets

```text
python tools/eval_assets.py prepare --cases skills/evidence-research/evals/cases.json --case E05 --output-parent <existing-evidence-directory>
python tools/eval_assets.py prepare --cases skills/code-change/evals/cases.json --case C04 --method skills/code-change --output-parent <existing-evidence-directory>
```

Use `--collection triggers` or `--collection discovery_cases` with the actual
corpus field and a matching ID. Omit `--method` for a no-method packet; repeat
it only for explicitly selected criteria. For a baseline/candidate comparison,
provide the actual frozen method directories from the respective revisions.
Never substitute today's skill for the historical baseline.

The preparer reuses the audit utility's path guard, method snapshot and packet
verifier. It includes the selected prompt/context/files and, when requested,
`SKILL.md`, references and adapter bytes. It excludes other cases, rubrics,
previous answers and grading fields. The manifest identifies the source-corpus
bytes. Retain the returned manifest digest outside the packet, then verify with:

```text
python skills/independent-audit/evals/verify_packet.py <packet> --manifest-sha256 <retained-digest>
```

An existing rubric elsewhere on the host remains readable unless the executor's
owner enforces isolation. A fresh directory, instruction or matching final hash
cannot establish blind execution, absence of transient effects or correctness.
Source packages are never overwritten; a failed preparation may leave a partial
new packet for inspection. Outputs must be outside the selected source packages.

## Capture one authorized command

```text
python tools/command_receipt.py --execute --cwd <project> --output-parent <existing-evidence-directory> --input <contract-file> --input <subject-file> --timeout 120 -- <executable> <arguments>
```

The process starts without a shell and without stdin. Put prompts and secrets
in appropriate task-owned files/environment; do not put secrets in arguments.
A fresh directory retains intent, argv/cwd, hashes of explicitly named inputs,
stdout/stderr bytes, exit status, launch errors, timeouts and final input drift.
Input hashes keep the selected paths: linked inputs are resolved again after
execution, so changed bytes, broken links and targets outside the project are
reported as drift. Equal bytes do not establish unchanged link topology.
The returned manifest digest must be retained independently. No unchanged rerun
is substituted for a failed attempt, and stdout is not silently truncated.

These are sensitive raw records, not files to commit. They may contain secrets
printed by the child. Review/redact a separate publication copy and keep the
original digest bound to the private original. The tool does not inspect or
record the environment, hash every dependency, authorize the command, or track
all native tool calls. On timeout it terminates only the direct child: descendants
and external state remain unverified. A caller requiring a stronger boundary
must use its existing execution sandbox/process supervision instead.

## Native loader evidence

Capture a separately authorized fresh-client run using the caller's existing
launcher. Record client version, prompt, model/effort, selected source files and
effective settings. For Claude's supported stream representation, the native
command needs `--output-format stream-json --verbose`; do not add `--bare` to an
automatic-discovery experiment without accounting for the discovery it disables.
No example here authorizes a paid run or changes global settings.

```text
python tools/native_smoke.py --client claude --receipt <command-packet> --manifest-sha256 <retained-digest> --require test-audit --forbid test-writing
```

The inspector correlates captured `Skill` calls and results, retains other
observed tool calls including errors, requires a terminal success and keeps
forbidden attempts even when they failed. Model prose saying it used a skill
is not a loader receipt. `observed-loader-contract` means only that the named
loader-event conditions held in the captured stream, not that the task, sandbox
or complete selection policy passed. Inspect `adverse_calls` separately.

**Qualification is deliberately partial.** The parser has synthetic event tests,
not a fresh Claude/Codex execution qualification. An explicit Skill call does not
prove automatic discovery; a negative loader check does not prove absence of
file-based method reads. The supported Codex projection returns `unverified`
because it has no qualified native skill-activation event mapping. Shell text
mentioning `SKILL.md` is not substituted. CLI exit codes are 0 for observed loader
conditions, 1 for a refuted loader condition, and 2 for missing/invalid evidence.
Do not score this as general skill effectiveness or a completed client smoke.

## Quality-tool probes

Use the project's already installed Node executable and actual JS tool entrypoint;
no `npx`, package installation or configuration mutation is performed. Work in
an authorized disposable project when using controls. Include relevant lockfiles,
configuration and source files with repeated `--input`; this defines the captured
source subset, not a claim that all transitive configuration is inventoried.

```text
python tools/quality_scope.py eslint --execute --node node --entry <project-eslint-js-entry> --root <project> --output-parent <evidence-directory> --input eslint.config.js --file src/example.js --rule no-eval --invalid src/invalid-control.js --valid src/valid-control.js
python tools/quality_scope.py tsc --execute --node node --entry <project-tsc-js-entry> --root <project> --output-parent <evidence-directory> --input tsconfig.json --project tsconfig.json --require-file tests/example.spec.ts
```

ESLint inspects effective severity at every named path and, when both controls
are provided, runs the intended rule on each. The scoped claim is error-level
enforcement, not warnings under a separate `--max-warnings` policy. Fatal parse
errors, another file's result or another diagnostic do not establish detection.
A permitted control must exit cleanly. A configuration-only observation is not
an executed lint result. Controls may use different extensions/overrides only
when that difference is actually relevant to the claimed guarantee.

TypeScript captures `--showConfig` and `--listFilesOnly`; missing required paths
refute the selected inclusion claim. `selection-only` is not type-check success,
project-reference build coverage or a CI receipt. Run actual owner gates for
those claims. Version output and every probe command remain in separate retained
receipts, including failure. Process execution still has ordinary project effects.

## Bounded diagnostic reproducer

```text
python tools/repro_check.py --execute --cwd <disposable-project> --output-parent <evidence-directory> --input <subject-file> --good-stdout <relative-good-control> --bad-stdout <relative-bad-control> -- <executable> <arguments>
```

Good and bad stdout bytes must be distinct and independently justified by the
contract. The deliberately narrow classifier accepts only a successful command:
exact good bytes return 0, exact known-bad bytes return 1, and crashes, timeouts,
input changes or unfamiliar output return 125 (not testable). This supports an
owner-prepared `git bisect run` without initiating any Git operation here. Keep
the classifier and control contract stable across examined revisions. This is
not a general flaky-test, performance or crashing-program oracle; use an existing
project-specific reproducer for those cases.

The conditional [diagnostic procedure](../skills/code-change/references/diagnostic-reproducer.md)
explains when a reproducer, minimization or bisection is useful without imposing
arbitrary hypothesis counts or blocking an already justified small repair.

## Primary references and evidence boundaries

- [Codex skill adapter format](https://developers.openai.com/codex/skills/):
  `policy.allow_implicit_invocation`, not a same-named key anywhere in YAML.
- [Agent Skills specification](https://agentskills.io/specification): skills,
  references and scripts are distinct package components.
- [Claude programmatic output](https://code.claude.com/docs/en/headless):
  structured output and discovery-related invocation caveats.
- [ESLint CLI](https://eslint.org/docs/latest/use/command-line-interface):
  print-config versus lint diagnostics and exit semantics.
- [TypeScript CLI](https://www.typescriptlang.org/docs/handbook/compiler-options.html):
  configuration/file selection versus actual checking.
- [Git bisect](https://git-scm.com/docs/git-bisect): a skipped revision is not bad.

These are mutable official references, checked on 2026-09-12. They document
mechanisms, not measured gains for these skills: the utility tests here are
executed, while native discovery and behavioural qualification are not. See
[what the evaluations establish](../docs/evaluation.md).
