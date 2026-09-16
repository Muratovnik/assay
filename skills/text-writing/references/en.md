# English prose

## Compose for the actual reader

Make the purpose visible, then develop the point with the evidence or example
it needs. Connect sentences when a logical link is missing; avoid both abrupt
fragments and elaborate tour-guide framing. Match formality and contractions
to the requested channel, not an imagined universal human style.

A concrete example can explain a distinction better than a series of abstract
benefits. Keep it hypothetical when it is not an observation. A requested personal
voice can retain warmth and opinions already present without inventing experience.
The pattern pairs below diagnose local problems, not the whole quality of a text.

Defects observed in English writing, with their own examples. This profile is
not the source of the Russian or Chinese ones: each language has its own
defects and its own legitimate neighbours.

## Defects

### 1. The empty opener

The first sentence describes the era, the industry or the general importance of
the subject. Removing it costs the reader nothing.

> Defective: "In today's fast-paced engineering landscape, build speed is no
> longer a nice-to-have."

> Legitimate: "Builds now take 4 minutes instead of 11 — we moved the dependency
> cache to the agent's local disk."

An opening line is fine when it names the subject of the section or ties it to
what came before.

### 2. The hollow contrast

"Not just X — it's Y" promises a clarification and supplies a second
evaluation instead.

> Defective: "Our build system isn't just a tool — it's a philosophy."

> Legitimate: "This is not a compiler change; it is a change in where the cache
> lives."

The second sentence rules out one specific misreading, which is what the shape
is for.

### 3. The ceremonial closer

A final paragraph restates the text in a raised voice and leaves the reader
without a next step.

> Defective: "At the end of the day, the future of shipping is already here."

> Legitimate: "If the cache is still cold after the image update, post in the
> on-call channel."

### 4. The unearned intensifier

"Robust", "seamless", "powerful", "game-changing" — a rating where there is no
measurement behind it.

> Defective: "a truly powerful, seamless observability experience".

> Legitimate: "the most frequent failure in August was the import timeout",
> where the data in front of you says so.

The word is not the problem. The missing measurement is.

### 5. The announcement voice

An internal note is written as a press release, so the reader has to strip the
packaging before finding what changed.

> Defective: "We're thrilled to announce that builds are faster."

> Legitimate: "Builds are faster as of today's agent image."

### 6. The manufactured triad

A third item joins the list for rhythm, not because the material has three
things in it.

> Defective: "Fast, reliable, and delightful."

> Legitimate: "Update the agent image, restart the pipeline and confirm the
> cache was restored."

### 7. Invented experience

The editor credits the author with a check, an observation or a scar that the
material never mentioned.

> Defective: "I've seen this bite teams firsthand."

> Legitimate: "This failed three times in August", where the count comes from
> the material.

### 8. Tour-guide framing

Narration about the narration, in place of the content it keeps promising.

> Defective: "Let's dive into what this means for you."

> Legitimate: "Three settings change. They are listed below."

### 9. Synonym churn on a name

An identifier is renamed mid-paragraph for variety, and the reader is left
wondering whether a second thing has been introduced.

> Defective: "Set `APP_TRACE_DIR`. This option, this environment setting, this
> variable…"

> Legitimate: repeat `APP_TRACE_DIR` as many times as the text needs it.

### 10. Grammar bent for tone

Sentence fragments, dropped subjects and stacked one-line paragraphs used to
sound decisive, where the reader needs the actor and the condition.

> Defective: "Rolled out. Cache moved. Faster now. Big win."

> Legitimate: "We moved the cache on Tuesday; builds have been faster since."

## What is not a rule here

- **The em dash.** It is not banned and has no quota. Neither is the semicolon.
- **The passive voice.** Correct wherever the actor is unknown or irrelevant —
  "the token is rotated every 24 hours" — and always subordinate to accuracy.
- **Formal words.** There is no stop list. "However", "therefore" and
  "accordingly" are ordinary English and belong wherever they read naturally.
- **Contractions.** Their presence or absence is a matter of genre, not a rule.
- **Repeated structure.** Uniform paragraphs suit uniform material.
- **Word-density thresholds.** A numeric "N per 100 words" limit is a property
  of the corpus it was measured on. Do not import one, and do not apply an
  English one beyond English.
