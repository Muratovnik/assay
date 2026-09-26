# Feature-Sliced Design profile

Read only when the project has adopted FSD or the user explicitly requests an
assessment of FSD as a candidate. Frontend code, familiar directory names or a
personal preference do not activate this profile. Evaluating adoption does not
authorize converting the project.

## Establish the applicable contract

Identify the adopted version, project decisions and intentional exceptions. The
research basis for this profile is the FSD v2.1-oriented upstream skill reviewed
on 2026-09-25; this is not a claim about every installed project's version or all
future upstream recommendations. Check the relevant current primary documentation
before a version-sensitive decision:

- [FSD documentation](https://feature-sliced.design/docs)
- [Official FSD skills](https://github.com/feature-sliced/skills)
- [Steiger](https://github.com/feature-sliced/steiger), when considering enforcement

Separate mandatory project rules from upstream recommendations and optional local
conventions. Keep authorized exceptions visible; do not silently relax an adopted
import contract or report absence of FSD as a defect in a non-FSD project.

## Apply the method, not an empty template

Start with required entry points and coherent local ownership. Introduce layers and
slices only where responsibilities warrant them; do not precreate empty entities,
features or widgets. Locate a slice by its meaning and consumers, then check its
allowed dependency direction and public surface under the adopted profile.

Check same-level coupling, cross-slice access, public API bypasses and accumulation
in shared code against those actual rules. Include aliases, re-exports and relevant
type dependencies; text matching alone does not establish a boundary. FSD is not a
backend or independently deployed service architecture merely because it names layers.

The upstream skill's reuse-oriented extraction advice is not a universal prohibition
on a single-consumer module; decide extraction and sharing with
[file placement](file-placement.md) and make a deliberate project exception explicit
where needed.

## Verify proportionately

Use an existing project checker where it expresses the adopted rules; do not install
Steiger or another linter simply because this reference mentions it. Verify version,
coverage and diagnostics through [effective checks](../../code-change/references/effective-quality-checks.md).
Review semantic ownership and runtime behavior separately from lint results. Changes
in upstream guidance call for a documented local decision, not automatic migration.
