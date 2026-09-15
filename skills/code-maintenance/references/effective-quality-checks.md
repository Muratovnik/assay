# Effective quality checks

Use when changing quality tooling, relocating covered files or claiming that a
tool protects a rule. Establish the intended guarantee before editing its config.

## Trace the active path

Follow the owner's actual invocation from package script, hook or CI job to the
loaded configuration and files it processes. A package dependency, imported
plugin, documented command or declared rule is not proof of enforcement.

Inspect resolved configuration for representative affected file classes and
overrides. With ESLint, use the installed version's effective-config diagnostics
for concrete paths and check rule severity and ignores. With a type checker,
inspect selected projects, references, included files and the invoked check mode.
A JS/JSDoc annotation can aid an editor without putting that file under CI checking.

Keep discovery, static checking and execution distinct. After moving a spec or
configuration file, verify that its tests are collected and that required lint
and type-check coverage still includes it. A successful build may exclude tests;
a passing runner need not type-check them. Existing intentional exclusions can
be valid; do not silently introduce an unagreed coverage requirement.

## Prove the claimed protection

For a material new or disputed gate, exercise a minimal known-invalid control
and a nearby permitted control through the relevant path in safe task-owned
resources. Use the real scope/extension/configuration; a control at another path
may hit a different override. Confirm the intended diagnostic, not any failure.
Keep the subject intact when reviewing rather than implementing.

Prefer existing tooling; do not add a general scanner or a second framework to
prove one rule. Source inspection can establish a disabled rule without execution,
but does not establish an unrun CI result. If a safe probe is unavailable, state
the precise evidence limit rather than treating registration as active protection.

Apply this also to update automation: inspect triggers, applicable package paths
and available run evidence before claiming it is absent, effective or broken.
Newer versions alone do not establish a project defect. Dependency freshness
and platform-support claims use the research method's
[component evidence](../../evidence-research/references/component-evidence.md).
