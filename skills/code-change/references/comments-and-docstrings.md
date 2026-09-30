# Comments and docstrings

Use when writing, editing or assessing comments and documentation strings beside
code, including a standalone comment-cleanup request. This procedure owns that
bounded decision, not a prose style detector or a reason to refactor the code.
For read-only review, apply the criteria without changing files.

## Establish what may change

Read the requested files, surrounding code, applicable owner rules and relevant
consumers. Distinguish ordinary explanation, public API documentation, generated
text and text that affects tooling or runtime behavior. A comment-looking token
is not necessarily inert. Preserve executable code, names, imports, control flow,
unrelated formatting and the attachment of comments to their targets during a
comment-only edit. Do not run a broad formatter or cleanup across unrelated files.

Protect compiler, type-checker, linter, coverage and build directives, their
arguments and placement. Examples include `@ts-expect-error`, lint suppressions,
JSDoc type annotations and bundler annotations. Preserve licence, attribution,
safety and generation notices. Do not edit generated output instead of its owner.
Docstrings may be read through reflection, documentation tooling or doctests;
changes to those contracts are not automatically prose-only. If an authorized
request intentionally changes such semantics, treat it as a code/tooling or
public-documentation change with the applicable checks, not as harmless cleanup.
When their role is unclear, leave protected text intact and report the bounded gap.

## Keep information, remove repetition

Judge what the intended reader or consumer learns, not whether wording resembles
an alleged AI style. Remove or shorten narration that merely repeats an obvious
operation and supplies no required context. Preserve business rules, invariants,
non-obvious behavior, compatibility constraints, concurrency and security
reasoning, and actionable follow-up conditions. Public API documentation can be
necessary to readers who do not see the implementation, even when it looks
redundant beside the signature.

Keep issue links, affected versions and removal conditions when they explain a
workaround's continued need or when it can safely be retired. Length alone is not
a defect: do not impose a one- or two-line cap or remove causal reasoning because
it takes a paragraph. A useful section marker or consistent punctuation can stay.
Honor a requested editorial convention within its actual scope, not as a global
ban on words, emoji, separators or sentence shapes.

Correct a stale explanation only against sufficient evidence of the intended
contract. A disagreement with current code might be a code defect rather than an
obsolete comment. Do not silently erase a requirement to match a bug, invent a
reason, issue, measurement or removal date, or refactor the implementation to make
a rewrite true. Report an unresolved or out-of-scope discrepancy and continue the
safe requested edits. Leaving text unchanged is valid when it already does its
job; a requested useful rewrite is still allowed.

## Check the actual boundary

Review the complete diff and the resulting surrounding unit. Confirm that useful
facts and qualifications remain, executable content and unrelated formatting
were preserved, and protected text still governs the same target. Use existing
project tools for the language: relevant type/lint/build checks for directives
or annotations, documentation/doctest checks for their consumers, and affected
runtime tests where text is observable. Do not write a new comment parser or
strip comments with regular expressions to claim semantic equivalence. A
comment-only diff or unchanged syntax tree alone cannot prove unchanged tooling,
generated documentation or runtime-observed strings.

Check a redundant explanation and a nearby necessary constraint separately.
Include an actual protected directive or observable docstring when those occur
in scope. Do not demand the full application suite for a verified inert local
edit, but run owner-required checks. Report what changed, what was deliberately
preserved and the checks actually performed; label unavailable verification.

## Primary references

- [TypeScript: `@ts-expect-error` semantics](https://www.typescriptlang.org/docs/handbook/release-notes/typescript-3-9.html#-ts-expect-error-comments)
- [TypeScript: JSDoc types](https://www.typescriptlang.org/docs/handbook/jsdoc-supported-types.html)
- [Rollup: tree-shaking annotations](https://rollupjs.org/configuration-options/#treeshake-annotations)
- [Python: documentation strings](https://docs.python.org/3/tutorial/controlflow.html#documentation-strings)
- [Python: doctest consumers](https://docs.python.org/3/library/doctest.html)
