# TypeScript and Vue conventions profile

Use for TS/Vue style decisions. This is a reusable baseline for a project or
scope that adopts it, not evidence that every existing project already has.
Explicit user preferences and owner conventions take precedence. In an existing
project without adoption, follow verified local conventions; suggest adoption
only when it resolves an actual inconsistency. Record a consequential adoption
once in the owning instructions/configuration, without a mandatory migration.

## Baseline within the adopted scope

- Prefer `const` for bindings that are not reassigned. Use `let` for intentional
  reassignment; binding immutability does not make an object immutable.
- Use `UPPER_SNAKE_CASE` for named, stable domain/configuration constants such as
  a fixed limit or protocol marker. Ordinary local values, callbacks, computed
  values and reactive references remain `camelCase`; not every `const` is a
  constant in this sense. Preserve public/API and externally dictated names.
- Prefer arrow functions for ordinary callbacks and function-valued bindings.
  Preserve declarations or methods when hoisting, overloads, `this`, constructors,
  generators or a framework contract make them the clearer correct choice.
  Do not rewrite function forms without checking their semantics.
- Keep separate assignments explicit when they represent separate fields or
  transitions. A lint rule should encode the agreed syntax scope, not infer state
  ownership from spelling. Fresh scenario objects belong to the testing method.
- Prefer established SFC layout and component naming. For new Composition API
  components, use the project's supported TypeScript and script-setup style;
  preserve legitimate Options API, mixed scripts and framework requirements.

Make enforceable conventions mechanical in the project's existing formatter,
linter or type checker where the rule fits. Keep semantic exceptions explicit
and verify the effective rule with the
[quality-check procedure](effective-quality-checks.md). A configured convention
and its fitness are separate questions; never disable it silently for a pass.
