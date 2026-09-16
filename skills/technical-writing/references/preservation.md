# Preservation of an edited document

Use when an existing document is being copyedited or rewritten and the question
is whether the edit stayed inside the area it was allowed to touch. This is a
structural check, not a judgement about meaning, and it is optional: read the
document and the edit first.

## The command

The [preservation check](../scripts/text_check.py) compares two files and
reports which protected regions survived the edit. Run it from wherever the
skill is installed:

```text
python <skill-directory>/scripts/text_check.py preserve --before <old file> --after <new file> --mode copyedit
```

`--mode rewrite` for a restructuring edit, `--json` for a machine-readable
report, `--allow-unverified` to keep an unclassifiable construct from deciding
the exit code. It uses only the standard library, reads the two files, and
writes nothing: no command inside the document is executed, no model is called
and no network connection is opened. The script emits UTF-8; configure the receiving terminal or consumer to
decode it as UTF-8 for Chinese and Cyrillic output. The caller must be allowed to read both files and execute this named check.
A review request alone does not authorize execution.

## What each mode protects

`copyedit` compares, in order and as raw source slices: fenced code blocks with
their fences and info strings, inline code spans, link and image destinations,
the YAML frontmatter block, table rows, and blockquotes. A blockquote that opens
with an alert marker such as `[!NOTE]` is treated as editable commentary, not as
someone else's words.

`rewrite` compares fenced blocks, inline code spans, link destinations and the
frontmatter as a multiset: the same blocks must all still be there, in any
order, under any heading. Table rows and blockquotes are not protected, because
restructuring them is the point of a rewrite — but an inline-code command inside a simple table cell
is still compared when the scanner recognizes it. Do not assume this covers
complex table/HTML syntax.

Table protection is deliberately coarse: the whole row is compared, so editing
the prose in a description cell is reported as a change. That is the safe
direction for a copyedit. If the wording in a cell genuinely has to change, make
that edit deliberately rather than expecting the check to bless it.

## Statuses and exit codes

| Status | Meaning |
| --- | --- |
| `pass` | Every region of this kind is byte-identical after normalising line endings. |
| `fail` | A protected region changed; the report names the line and the fragment. |
| `unverified` | Nothing could be concluded: a construct the scanner cannot classify, or a document with no protected region at all. |
| `warning` | Line endings changed between the two files. The content comparison still ran. |
| `not-applicable` | No region of this kind exists, or this mode does not protect it. |

| Exit code | Meaning |
| --- | --- |
| `0` | No preservation failure; by default nothing was left unverified. With `--allow-unverified`, inspect the retained statuses. |
| `1` | At least one protected region changed. |
| `2` | Nothing was refuted and nothing could be concluded, or the input was invalid. |

An empty file, an unreadable file and input that is not valid UTF-8 all exit `2`
with a message and no report: they are not results. A document in which no
protected region exists also exits `2`, because a check that inspected nothing
must not read as success.

When a run has both a failure and an unverified construct the exit code is `1`:
a refuted region is a known result and outranks evidence that is merely
missing. `2` is reserved for a run that refuted nothing and could not finish.
Read the checks rather than the code alone. `--allow-unverified` only
changes the code: the `unverified` status stays in the report, and a change
inside the construct it covers is still not being checked. Do not use the flag
to turn a document the scanner cannot read into a green result.

## What this cannot establish

Structural preservation is not semantic equivalence. The following errors can survive a
structurally passing result:

- A correct code block moved under the wrong heading. Both modes compare the
  blocks, not the section they belong to.
- A number kept but rebound to a different parameter — `30` still present, now
  attached to the wrong flag.
- A condition dropped from the prose around a preserved command, including the
  clause that made the command safe.
- A negation or a status inverted in prose: "not more than" to "not less than",
  "proposed" to "available".
- Prose in a table cell or an alert blockquote in `rewrite` mode, and any prose
  anywhere in either mode.
- A change inside an indented four-space code block in a document that also
  contains some recognized protected content. Only fenced blocks are protected.

HTML blocks and MDX-like tags are a different limitation: the script reports
`unverified`; they are not examples of full coverage with a clean strict result.

Known false positives: a prose fragment that looks like a tag, such as a
generic type written inline, is reported as an unclassifiable construct. A
destination containing brackets, spaces or balanced parentheses is not
extracted; the link marker is reported `unverified` instead, so an unread
destination never counts as an absent one.

Another scanner limitation concerns an unpaired backtick. A single unpaired backtick in prose
pairs with the opening backtick of the next code span, so the span the scanner
compares is not the one you see, and an edit to unrelated prose between them is
reported as `inline_code` `fail`. Inspect the source and intended rendering. This observation does not establish
compatibility with every Markdown renderer or authorize changing the source.

The claim this check supports is narrow: "the protected regions of the document
are unchanged". Everything else still needs reading, and a run of the command
does not replace the source check that a technical statement requires.

## Existing linters

Where a project already runs them, read their output and map it into the same
statuses. Nothing here installs anything.

- **markdownlint-cli2** reports structural Markdown conventions against the
  project's own configuration. A rule it enforces is a house convention, not
  evidence of quality; a line-length rule in particular proves nothing.
- **lychee** resolves links. It answers whether a destination exists, never
  whether the destination is still the right one: a link silently retargeted
  from one existing file to another passes cleanly. A before/after
  comparison detects the changed target directly; semantic review is still needed.
- **Vale** applies a glossary and narrow style rules. Run it advisory first and
  raise a rule to blocking only after it has been shown not to fire on
  known-good text. See [Vale](https://vale.sh/) for its rule formats.

A tool that is not installed, a run that timed out, and an HTTP 403 are all
`unverified`. None of them is `pass`, and none of them shows a target is
broken. Report the missing check rather than dropping it: a skipped check that
disappears from the report turns into an implied success.

Language scope matters as much as tool availability. Do not assume an English word-based heuristic
or its thresholds transfers to Chinese. Tokenization and boundary behavior need
a language-specific check. Disable inapplicable rules or scope them by language, and confirm
that a style checker supports the language at all by running it on a known-good
control file in that language before any rule is allowed to block.

## Interpret the result in the right context

A protected value changed during copyedit is a preservation failure even if
both values would be valid configurations. Cite the before/after difference;
do not claim the example is an implementation default without another source.
Equivalent unprotected wording can be accepted while reverting a changed code
block or link. A style preference is a separate, optional judgment.

Link identity and link resolution are different checks. Resolve a relative
path against the actual source document directory or the documented site base,
not against the directory containing an evaluation alias. For example,
`../reference/options.md` from `docs/how-to/setup.md` normalizes to
`docs/reference/options.md`; `reference/options.md` does not. If the source path
or renderer base is unknown, do not claim a destination was verified. This
script compares link strings; it does not check destination existence, anchors
or renderer-specific routing.

The script does not validate the final reply's Markdown wrapper. An actual
Markdown file must not have an extra fence around the entire document. If its
literal source is shown in a reply, use an outer fence longer than any matching
fence in that content. Inspect the delivered artifact, not just quoted commands.

`--allow-unverified` is not part of an acceptance shortcut. Keep default strict
handling for an automated gate; an explicitly accepted unsupported construct
still remains unverified in the report. A clean structural result never proves
that qualifiers, defaults or command-to-section relationships stayed correct.
