# Russian, English and Simplified Chinese documentation

Three profiles, not one profile translated three times. Choose the profile by
the language of the prose. In a mixed document the prose language decides the
editorial rules, and the technical strings keep their original form.

## What is the same in all three

Identifiers, CLI flags, environment variables, API names, file names, error
codes and configuration keys are never translated, never re-cased and never
"localized": `--dry-run` stays `--dry-run` in Russian and Chinese prose, and
`WIDGET_TOKEN` stays `WIDGET_TOKEN`. A project glossary may fix how an ordinary
technical concept is rendered in prose; it does not rename an interface.

Punctuation inside code spans, fenced blocks, commands, paths, URLs, regular
expressions and sample output is preserved byte for byte. Outside those regions
the prose uses its own normative punctuation. The two rules meet most often in
Chinese documentation, where a full-width comma is correct in the sentence and
destroys the command one line below.

Automatic checks are language-scoped. A word-density threshold, a `\b` word
boundary and a maximum line length are properties of space-separated writing:
they do not transfer to Chinese, where they either match nothing or flag every
line. Enable such rules per language, run any style checker — for example
[Vale](https://vale.sh/) — in advisory mode first, and confirm on a known-good
file in that language before letting a rule block anything.

## Russian

Defects to look for: clerical padding that replaces a verb with a noun stack;
calques from English word order; false emotion in a reference page; vague
generalities in place of a parameter.

Defective:

> Осуществляется выполнение операции по установке пакета, что позволяет в
> кратчайшие сроки приступить к работе с продуктом.

Legitimate, and not to be flagged:

> Установите пакет: `pip install widgetctl`. Команда ставит CLI и его
> зависимости — на это нужно около минуты.

The second example keeps the em dash, keeps the Latin command untouched and
repeats the term «команда» rather than hunting for a synonym. Normative Russian
punctuation, including the em dash and the dash in an elliptical sentence, is
correct; a rule borrowed from an English style guide that bans dashes does not
apply here. Do not chop sentences into verbless fragments to look brisk, and do
not replace a repeated technical term with a near-synonym: in documentation,
repetition is precision.

## English

Defects to look for: empty run-ups, unearned superlatives, "simply" and "just"
in front of a step that is not simple, and a marketing register inside a
reference page.

Defective:

> Our powerful CLI seamlessly empowers you to simply manage everything you
> need, right out of the box.

Legitimate, and not to be flagged:

> `widgetctl sync` copies the local catalogue to the server. It is idempotent,
> so a repeated run after a network failure is safe.

Formal words are not banned: "therefore", "however" and the passive voice are
all fine where they read naturally, and a passive is often the right choice when
the actor is irrelevant ("the token is rotated every 24 hours"). English rules
stay in this section; they are not the source of the Russian or Chinese ones.

## Simplified Chinese (zh-CN)

Defects to look for: an empty opening that states the topic without adding
anything; a closing paragraph that repeats the section; mechanical parallel
lists where the material has one point; advertising clichés in a technical
document; and half-width punctuation used in prose out of habit.

Defective:

> 随着技术的不断发展，本工具为广大用户提供了强大而全面的解决方案,帮助您轻松应对
> 各种复杂场景。

Legitimate, and not to be flagged:

> 运行 `widgetctl sync --dry-run` 可以先查看将要上传的文件，不会写入服务器。
> 该命令是幂等的，网络中断后重复执行是安全的。

The second example is correct as it stands. Full-width punctuation（，。、：；「」）
in the prose is normative, a four-character idiom used accurately is normal
technical Chinese, and a parallel construction that lists three real options is
not "machine-like". Do not convert full-width prose punctuation to half-width,
and do not touch the half-width punctuation inside `--dry-run`, a path or a JSON
sample. Keep Latin terms, product names and commands unchanged; a space around
an inline Latin run is a project formatting convention, not a correctness issue.

## Keeping a translation in step with its original

A translated document is a second copy of a technical contract. Compare it with
the original before touching its style, and report in this order:

1. **Commands and code.** Every command, flag, path, environment variable and
   sample output identical to the original, character for character.
2. **Numbers.** Counts, versions, ports, timeouts, limits and the parameter each
   number is attached to.
3. **Route status.** What the original marks as verified, exercised, documented
   only, planned or deprecated must carry the same status in the translation.
4. **Version labels.** The release, branch or revision the document describes.
5. **Caveats.** Negations, conditions, platform restrictions and warnings.

Any divergence in those five is an `error`, and the original wins unless the
original is itself wrong — in which case report both documents rather than
fixing one quietly. A difference in sentence order, connectives, register or
paragraph split is not a defect: translations legitimately differ in style, and
rewriting a fluent translation to mirror English syntax makes it worse. When the
original changes, list which translated sections the change touches; a
translation silently left behind is the common failure, and it looks fine.
