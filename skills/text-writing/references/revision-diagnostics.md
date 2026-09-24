# Optional revision diagnostics

Read when an authorized before/after comparison could expose an overlooked change.
Do not run this for every message, require author notes when the brief is sufficient,
or use measurements to replace reading. Review mode alone authorizes no execution.

## What to run

The canonical [revision checker](../scripts/revision_check.py) belongs to
`text-writing`. Technical-writing consumers may reuse it when that skill is
available alongside theirs. A standalone technical-writing installation need not
contain it: compare manually instead of silently installing a dependency. The
script needs Python 3.11+ and only the standard library; it reads local UTF-8 files,
emits a report, and writes no files, invokes no model and makes no network calls.

```text
python <text-writing-directory>/scripts/revision_check.py before.md after.md --source notes.md --json
python <text-writing-directory>/scripts/revision_check.py before.md after.md --style --language ru --term API --json
```

`before` is the text being edited, not an arbitrary collection of source notes.
Repeat `--source` for explicitly permitted factual sources. An author-style sample
is not a factual source for the new text. Sources are not fetched, authenticated
or executed. Each must contain nonempty text. For drafting without a before text,
use ordinary source review rather than inventing a baseline just to run the tool.

## Read factual changes as questions

The report contains added and removed numbers, quantities (number plus a recognized
unit or currency), numeric dates, versions and HTTP(S) URLs. Each has its source
label and 1-based line/column. Inputs are identified by SHA-256 of decoded text
encoded as UTF-8 (an initial UTF-8 BOM is removed); these are not raw-file hashes.
No source passages or private notes are persisted by the tool.

Comparison uses complete typed tokens, not substring containment: `10` is not
supported by `100`, and `10 ms` differs from `10 s`. Whitespace in thousands groups
and a Unicode minus are normalized; unit case and decimal separators are not.
The tool deliberately does not infer unit conversions, locale-dependent numeric
equivalence or that two URL spellings lead to the same page. Inspect such findings.
Dates are recognized spellings, not validated calendar values. Relative links,
spelled-out numbers, entity names and arbitrary units are outside its coverage.
URL extraction is best-effort, not a CommonMark parser; unusual punctuation can
change which suffix is recognized. Facts in code are scanned too, not executed.

An addition that matches a supplemental source is listed separately with matching
locations. Check that the source supports the actual relationship, not just the
same token. Only removals from `before` are reported: unused background facts from
notes need not be inserted into the final text. Repeated mentions do not count as
new facts or require repeated sentences to survive a rewrite.

A clean token inventory proves neither factuality nor preservation of meaning.
Read negations, uncertainty, who or what a value describes, which action a deadline
qualifies, and necessary versus sufficient conditions. The same `10` can now count
a different thing. A supported correction may legitimately change a value; a
warning is not a reason to restore an error. Do not demand zero findings.

Keep using the technical-writing preservation check for its protected Markdown
regions. This diagnostic is not a replacement, and its URL scanner does not extend
the preservation check's contract.

## Optional style and overediting observations

`--style` requires explicit `--language en` or `--language ru`. There is no corpus
calibration for either language and no human/AI classification. Other language
values remain visibly `unverified`; there is no fallback to English bands.

The report compares word count, approximate sentence segments and their lengths,
paragraphs, ATX headings and list items. It excludes recognized frontmatter, fenced
code and inline code. Indented code, HTML, tables and unclosed fences/frontmatter
make style coverage unverified. Sentence splitting is approximate, particularly
for abbreviations, lists and punctuation-heavy prose. Setext headings and complex
Markdown are not supported as structural metrics. Use the rendered document too.

Both texts need at least 100 prose words by default. `--min-style-words` changes that
coverage guard, not a target for the document or a research-derived quality cutoff.
Do not lengthen a short message to satisfy it. Missing coverage is not a style defect.

A rise in sentence segments with shorter segments prompts a question about lost
connections; removed headings/list items prompt a question about navigation.
`--term` supplies literal, case-sensitive terms to compare; repetitions are not a
blacklist. These are review questions, not automatic overediting verdicts. A
requested summary can correctly lose headings, detail or repetition. Compare the
brief, original and author's intended voice before deciding whether to restore
anything. Do not impose a target rhythm, a ban on three-item lists, or extra passes
until every observation disappears. Recheck after a material edit, not on a schedule.

## Status and automation contract

Text and JSON come from the same report. The JSON `claims` object always keeps
factuality, meaning preservation and writing quality `unverified`. `observed` means the declared diagnostic
completed, **not** that the text passed a factuality or writing-quality test.
`review` means unsupported additions or removals need interpretation.
`unverified` retains missing/invalid coverage. Style is `not-requested` by default.

| Exit | Meaning |
| --- | --- |
| `0` | Requested diagnostics completed. Advisory fact changes may still exist. |
| `1` | With `--strict`, factual token changes remain for review. No claim is made that they are false. |
| `2` | Invalid/unreadable/empty input, nothing inspectable, or requested style coverage is unavailable. |

`--strict` opts into a token-review gate, not a truth gate; it never blocks on style
metrics alone. Unavailable requested coverage takes exit `2` even when token
changes were found; those findings remain in the report. Consumers must inspect
both dimensions rather than treat `2` as an absence of findings. This differs from
the preservation check's refutation-first precedence. There is no flag to hide
unverified coverage. Without `--style`, a pair containing no recognized facts exits
`2`; with usable style observations it can complete while factual coverage remains
explicitly unverified. `--term` without `--style` is an input error.

Inputs are limited to 2,000,000 bytes each, NUL bytes are rejected, and file errors
have an `unverified` JSON report with `--json`. CLI output is explicitly UTF-8, including redirected output on Windows.
Configure the receiving terminal or pipe consumer to decode UTF-8. Keep reports outside the final document unless the reader needs a real
unresolved limitation. The checker adds no authorization to read additional files.
