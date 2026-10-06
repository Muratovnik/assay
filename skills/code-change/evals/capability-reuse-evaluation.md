# Capability and reuse entry: rationale and evaluation

Maintainer material for this method change, not runtime instructions or a model
run report. The shipped inputs and rubrics are public working material, not
production incidents or unseen final cases.

## Decision and current gap

The requested outcomes are that an agent notices a capability the result needs
but the request did not name, such as a missing validator on a consumer path, and
considers an existing implementation before writing its own mechanics. Neither
outcome means "always add a tool" or "always prefer a library".

The inspected baseline is `315e1f6607e551dc30c175a21bac224271f72f4e` (0.15.0).
Reuse criteria already existed in the reuse reference, and planning already
connected necessary enabling work to the requested result. The entry into both
was a model-judged predicate: code-change sent the agent to the reuse reference
only before a "material decision", and nothing on the code-change path asked
which capability provides a guarantee before choosing the implementation. Writing
own code usually happens exactly when the agent does not consider the choice
material, and the final report had no addressable place showing whether existing
options were checked.

The change replaces that first predicate with a list of behavior that commonly
has an existing implementation, adds a narrowly conditioned capability step owned
by planning's scope reference, adds a reuse report line and an optional proposal
line, and adds two hint rules for Russian lookups that the hint grammar missed.
The two other entry conditions of the reuse reference, standard visual states and
staged adoption, are unchanged; the existing UI cases remain their control.

Only a one-line helper and project-specific business logic skip the reference. An
existing option that breaks the required semantics is not an exemption the agent
can declare for itself: it is the gap the reuse line names, and it does not end
the search for a fitting capability. The reuse line is required whenever the
change introduces or keeps such behavior, including when a native or installed
capability performs it. Copying or adapting another project's resource enters the
borrowing procedure directly from the code-change method.

No captured failing native-client trajectory was supplied. A missing criterion, a
branch that was not loaded and a rule that was read but not applied remain
competing explanations for any particular incident. This change addresses the
entry point; it does not establish which explanation caused a past failure.

## Cases and controls

| Case | Protected outcome | Legitimate case an overbroad rule would reject |
| --- | --- | --- |
| CR01 | Native TOML reading instead of a hand-made parser or an extra dependency | — (positive case) |
| CR02 | — | Project business logic implemented directly without a reuse ritual |
| CR03 | Existing repository validation reused on the import path | No competing validator and no optional proposal when a check covers the guarantee |
| CR04 | A missing consumer guarantee provided or reported, not hidden by a green test | The unrelated save loader stays out of scope |
| CR05 | A rejected first candidate leads to the fitting native capability, with the gap named | — (positive case; the in-process tests pass for the per-process candidate too) |

The hint rules have paired should-not-fire fixtures in
`tools/fixtures/hooks/prompts.json`: log inspection phrased with the same verb,
quoted and fenced wording, an explanation request and unrelated "can I" questions.

## Evidence boundary

Structural checks and offline replay establish that the files are valid and that
the grammar recognizes the listed wording. They do not show that a client
selected the skill, that the reference was read before the decision, that a
`Reuse:` line was filled from an actual lookup, or that results improved. No model
run or paired comparison was performed for this change.

An observation in ordinary work should record, for a task that created new
mechanics: the available route and Assay revision, whether the reference was read
before the implementation choice when a trace shows it, the decision, the
consumer-path check and the report lines. Without a trace, the reading order
stays unknown; the presence of a report line is a pointer for review, not
evidence of the lookup.
