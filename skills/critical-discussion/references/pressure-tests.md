# Pressure tests

Use when choosing which sides of an idea to examine and how to try to break it.
Pick what fits the idea; do not run the whole list at the user.

## Sides by kind of artifact

Use these as prompts for what has not yet been discussed, not as a mandatory
pass. If the artifact is not listed, ask what categories of consideration that
kind of thing has.

- **Software or system:** the problem and its users, data, interfaces, state
  and lifecycle, failure handling, concurrency, scale, security and
  authorization, privacy, observability, testing, deployment and rollback,
  migration, cost, maintenance and ownership, dependencies, edge cases,
  accessibility, documentation.
- **Product or feature:** who has the problem, the alternatives including doing
  nothing, value, distribution, effort, risks and assumptions, the smallest
  version that tests the idea, how success is measured.
- **Process or workflow:** who does each step, what happens on failure, what is
  automated versus remembered, how it is checked, what it costs each time.
- **Research or argument:** the question, prior work, evidence per claim, the
  strongest counterargument, the scope, what would change the conclusion.
- **Any decision:** options including the status quo, criteria, reversibility,
  time horizon, who is affected, the worst case, second-order effects, the cost
  of delay.

## Ways to break an idea

- **Premortem:** assume it failed a year from now and write why. Usually the
  most productive single test.
- **Inversion:** how would we guarantee it fails? Avoid those paths.
- **Steelman, then attack:** build the strongest version first and challenge
  that, never a weak caricature.
- **Second-order effects:** "and then what?" for the users, maintainers and
  neighbouring systems.
- **Outside view:** how often do efforts of this kind succeed, and why do they
  usually fail?
- **Falsifiability:** what evidence would show the idea is wrong? If nothing
  could, it is a belief rather than a plan.
- **Chesterton's fence:** before removing something, establish why it exists.
- **Adversary:** for security, abuse or competition, how would someone exploit it?
- **Extremes:** what happens at ten times or a tenth of the scale, budget or use?
- **Change of perspective:** the maintainer, the newcomer, the operator, the
  user who never reads documentation.

Fixation on a familiar solution or on the first example hides simpler options.
When the discussion has stayed inside one frame, reverse a core assumption and
see what changes.
