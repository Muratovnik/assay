# Alternatives and reuse

Use when the discussion concerns building versus reusing, keeping versus
replacing, or the claim that part of a system is unnecessary.

## Always include doing nothing

State what happens if nothing changes: who keeps the problem, what it costs and
whether that cost is growing. Doing nothing is a real option and sometimes the
best one. Also ask whether the problem is already solved, partly or wholly,
somewhere in the project or platform.

## Compare the candidates

Consider, in order of usual cost:

1. doing nothing or changing a process;
2. an existing capability of the project or its platform;
3. a maintained external solution, adopted or adapted;
4. building it.

For each, weigh the coverage of the actual need, integration, maintenance,
security, licensing, operating constraints and the cost of replacing it later.
Popularity and fewer dependencies are not proof of fit. Reuse creates
obligations: updates, compatibility and the risk of the dependency failing.

Whether a ready-made solution exists, and how mature it is, are research
questions. Use [evidence research](../../evidence-research/SKILL.md) for them,
including its search-coverage procedure for an "it does not exist" claim. In
the discussion keep the claim bounded to what was actually examined.

## "This was written for nothing"

The claim is useful and testable. Before making it:

- name the replacement and where it comes from;
- trace the supported paths of the existing part and check the replacement
  covers each; an uncovered path used in practice defeats a plain replacement;
- estimate migration cost, the obligations the replacement brings and the
  remaining maintenance of the current part;
- check why the part exists (Chesterton's fence): a constraint may still apply.

Then give one of:

- **Kill**: the part serves no current need, or a replacement covers it at
  lower total cost; name the migration.
- **Keep**: the part works and replacing it costs more than it saves. "Could be
  replaced" is not a reason to replace working software.
- **Pivot**: adapt an existing solution, or narrow the part to what only it
  provides.

Without the checks, present the claim as a hypothesis and say what would
confirm it.
