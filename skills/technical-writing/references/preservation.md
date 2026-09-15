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
and no network connection is opened. Output is UTF-8 regardless of the console
code page, so a report quoting Chinese or Cyrillic text is readable and
redirectable on any terminal. The caller must be allowed to read both files.

## What each mode protects

`copyedit` compares, in order and as raw source slices: fenced code blocks with
their fences and info strings, inline code spans, link and image destinations,
the YAML frontmatter block, table rows, and blockquotes. A blockquote that opens
with an alert marker such as `[!NOTE]` is treated as editable commentary, not as
someone else's words.

`rewrite` compares fenced blocks, inline code spans, link destinations and the
frontmatter as a multiset: the same blocks must all still be there, in any
order, under any heading. Table rows and blockquotes are not protected, because
restructuring them is the point of a rewrite — but a command inside a table cell
is still compared, as an inline code span.

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
| `0` | Every protected region was preserved, and nothing was left unverified. |
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

Structural preservation is not semantic equivalence. All of the following pass
this check and can still be wrong:

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
- A code block written as an indented four-space block instead of a fence. Only
  fenced blocks are recognised.
- Anything inside an HTML block or an MDX-like tag. Those are reported
  `unverified`, never `pass`.

Known false positives: a prose fragment that looks like a tag, such as a
generic type written inline, is reported as an unclassifiable construct. A
destination containing brackets, spaces or balanced parentheses is not
extracted; the link marker is reported `unverified` instead, so an unread
destination never counts as an absent one.

One false positive goes the other way. A single unpaired backtick in prose
pairs with the opening backtick of the next code span, so the span the scanner
compares is not the one you see, and an edit to unrelated prose between them is
reported as `inline_code` `fail`. Close or escape the stray backtick in the
source; the document was ambiguous, and the check is reading it the way a
Markdown renderer does.

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
  from one existing file to another passes cleanly. Only a before/after
  comparison catches that.
- **Vale** applies a glossary and narrow style rules. Run it advisory first and
  raise a rule to blocking only after it has been shown not to fire on
  known-good text. See [Vale](https://vale.sh/) for its rule formats.

A tool that is not installed, a run that timed out, and an HTTP 403 are all
`unverified`. None of them is `pass`, and none of them shows a target is
broken. Report the missing check rather than dropping it: a skipped check that
disappears from the report turns into an implied success.

Language scope matters as much as tool availability. Line-length limits, word
counts and `\b` word boundaries are properties of space-separated writing and do
not transfer to Chinese, where they either match nothing or flag every line.
Disable such rules for Chinese content or scope them by language, and confirm
that a style checker supports the language at all by running it on a known-good
control file in that language before any rule is allowed to block.
