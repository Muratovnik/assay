# Russian prose

The defects below were written for Russian, not translated from an English
list. Each one names what the reader loses, shows a defective fragment, and
shows a nearby fragment that looks similar and must be left alone.

## Defects

### 1. The empty run-up

The first sentence spends the reader's attention and returns neither a fact nor
a direction. Delete it and the text loses nothing.

> Дефект: «В современном мире скорость доставки изменений становится ключевым
> фактором успеха. Сборка теперь занимает 4 минуты вместо 11.»

> Допустимо: «Сборка теперь занимает 4 минуты вместо 11: мы перенесли кэш
> зависимостей на локальный диск агента.»

An opening sentence is legitimate when it names the subject of the section or
connects it to the previous one.

### 2. The hollow contrast

«Не X, а Y» promises a distinction and delivers a second evaluation, so the
reader ends the sentence knowing no more than at its start.

> Дефект: «Это не просто инструмент, это философия.»

> Допустимо: «Это не ускорение компилятора, а другой способ хранения кэша: сам
> компилятор мы не трогали.»

The second fragment removes a specific wrong reading. The construction itself is
not the defect and must not be banned.

### 3. The ceremonial closing

The final paragraph repeats what was said, in a raised voice, and gives the
reader nothing to do.

> Дефект: «В конечном счёте, будущее уже здесь.»

> Допустимо: «Если после обновления образа кэш не восстановился, напишите в
> канал дежурной смены.»

### 4. The unearned intensifier

An evaluation stands where the author has no measurement. The reader can neither
verify it nor decide anything by it.

> Дефект: «по-настоящему мощное и революционное решение».

> Допустимо: «самый частый источник падений в августе — таймаут импорта», когда
> это следует из приведённых данных.

A superlative with a source behind it is a fact, not a cliché.

### 5. Clerical padding

Verbal nouns and split predicates lengthen the sentence and hide who does what.
The reader has to reconstruct the actor.

> Дефект: «Осуществляется выполнение процедуры резервного копирования силами
> дежурной смены.»

> Допустимо: «Резервное копирование выполняет дежурная смена.»

A formal register is not itself a defect: in a policy or an order it is correct.
The defect is the padding, not the formality.

### 6. The invented third item

A third element is added for rhythm and carries no meaning of its own.

> Дефект: «Быстро, надёжно и удобно.»

> Допустимо: «Обновите образ агента, перезапустите пайплайн и убедитесь, что кэш
> восстановился.»

Three items because there are three actions. A list of three real things stays a
list of three things.

### 7. Invented feeling and borrowed experience

The editor attributes to the author a feeling, a check or an observation that
never happened. That changes the author's position and can simply be untrue.

> Дефект: «Признаюсь, я сам обжёгся на этом трижды.»

> Допустимо: «В августе эта ошибка повторилась трижды», если число взято из
> материала.

### 8. Synonym churn on a term

Replacing a repeated term with a near-synonym for variety makes the reader guess
whether one thing is meant or two.

> Дефект: «Настройте `APP_TRACE_DIR`. Эта опция, этот параметр среды, данная
> переменная…»

> Допустимо: повторить `APP_TRACE_DIR` столько раз, сколько нужно.

In a text about a system, repetition of a term is precision.

### 9. Modality drift during editing

An edit made "for clarity" turns a possibility into a promise, or the reverse.
This belongs to the meaning group, and it outranks every stylistic point above.

> Дефект: «может потребовать перезапуска» → «потребует перезапуска».

> Допустимо: «может потребовать перезапуска» → «иногда требует перезапуска».

## What is not a rule here

- **Dashes.** Normative Russian punctuation stays, including the em dash and the
  dash of an elliptical sentence. There is no quota on dashes, and a rule
  borrowed from an English style guide that bans them does not apply to Russian.
- **Formal words.** There is no stop list of formal vocabulary; the genre
  decides. A statement of policy is allowed to read like one.
- **Repeated structure.** Identically built paragraphs are correct where the
  material is uniform.
- **Sentence length.** Terse fragments are not the target, and enlivening a text
  with interjections is not the editor's job.
- **Identifiers.** `--dry-run`, `APP_TRACE_DIR`, API and file names keep their
  original spelling and case inside Russian prose. A project glossary may fix
  how an ordinary technical concept is rendered; it does not rename an
  interface.
- **A zero-defect count.** A text scrubbed until no heuristic fires is not
  thereby accurate or useful.
