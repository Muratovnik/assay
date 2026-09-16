# The optional author profile

A profile records how one person writes, so that a draft sounds like them
instead of like the average of everything. It is optional: the method works
without one, and an absent profile is never a reason to invent a voice.

## What it holds

A short Markdown file with these sections, each of them about form:

- **Form of address.** How the author addresses colleagues, clients and
  strangers; whether they use a greeting, and which one.
- **Tone.** The register the author keeps, and the one they never use.
- **Permitted informality.** Slang, humour, exclamation marks, emoji, first
  person plural or singular — stated as allowed, avoided or forbidden.
- **Characteristic vocabulary.** Words and constructions the author actually
  uses, and near-synonyms they avoid.
- **Formatting.** Paragraph length, lists, headings, dashes, whether a message
  ends with a question or a summary.
- **Explicitly allowed examples.** Two or three short fragments the author has
  agreed may be used as style references.

## What it must not hold

Style only. No employer, address, family circumstances, health, travel, salary,
client names, credentials or anything else that identifies a person or their
situation. If a sample contains such a detail, the profile records the manner
and drops the detail.

The profile belongs with the author's own material — their notes, their private
directory, their own repository — and is never committed here. Keeping it local
does not make it private in every sense: whatever is loaded into a task is sent
to the model provider that runs it, so the same restraint applies to a sample
pasted into a single request.

## How samples are used

A sample supplies manner: sentence length, greeting, the way a request is made,
the way bad news is broken. It never supplies content. Facts, numbers,
commitments, opinions and personal circumstances from a sample do not enter the
new text, even when they would fit, because the new text is about something
else and the reader will read them as current.

Use only samples the author chose for this purpose. Do not go looking for more:
no reading of mail, chat history or documents to infer a style, and no copying
of a third party's writing as a model without their agreement.

## When it changes

Update the profile after the author corrects something and confirms the
correction is general — "I never open with 'Hope this finds you well'" — not
after every draft. A profile rewritten from each generation drifts towards
whatever the model produced last time, which is the opposite of its purpose.

## A short example

The content below is invented, and shows the shape rather than any real
person's voice.

```markdown
# Style profile — internal messages

- Address: first name, no greeting line in chat; "Добрый день" in email to
  people outside the team.
- Tone: plain and direct. No enthusiasm the situation does not contain.
- Informality: no emoji, no exclamation marks. Contractions are fine in English.
- Vocabulary: says "сборка", not "билд"; "проблема", not "челлендж".
- Formatting: two to four sentences per paragraph; a bulleted list only when
  there are at least three items; ends a request with a direct question.
- Allowed samples: `samples/status-note.md`, `samples/decline.md`.
```
