# Simplified Chinese prose

Defects written for Chinese, with Chinese examples. None of them is a
translation of an English rule, and no rule from the English profile transfers
here without its own example.

## Measures that do not apply to Chinese

- **Per-word density.** Chinese prose has no spaces between words, so "how many
  times word X occurs per 100 words" is undefined without segmentation, and
  segmentation introduces its own errors. A density threshold measured on
  English says nothing here.
- **`\b` word boundaries.** A regular expression that relies on word boundaries
  matches nothing inside a run of Chinese characters, or matches arbitrarily at
  the edges of Latin fragments. A rule written with `\b` is not a Chinese rule.
- **Line length.** Limits of 80, 100 or 120 characters come from monospaced
  Latin typesetting. One Chinese character occupies the width of two Latin ones,
  and a line may break almost anywhere, so a character count does not measure
  readability.
- Consequently, a word-based or line-based style rule is enabled for Chinese
  files only after it has been checked against a known-good Chinese text, never
  by default because the tool offers it.

## Defects

### 1. The empty opening

The first sentence announces the age or the trend and says nothing about the
subject.

> 缺陷：在当今这个飞速发展的时代，可观测性已经变得前所未有的重要。
> 同类：众所周知，……；随着技术的不断进步，……

> 合格：本节说明三个新增的追踪开关。

An opening is legitimate when it names what the section covers.

### 2. The empty conclusion

A closing paragraph reaches for 总而言之 or 综上所述, repeats the text and asks
for nothing the reader can do.

> 缺陷：总而言之，只有不断赋能每一位工程师，才能拥抱更加美好的未来。

> 合格：如果更新镜像后缓存仍未恢复，请在值班频道反馈。

### 3. Marketing filler in a text with another job

Promotional evaluations arrive where the reader wanted a change or a number.

> 缺陷：全新升级的一站式解决方案，真正强大，助力团队打造闭环，全面赋能业务。

> 合格：新版本把依赖缓存移到了构建机本地磁盘。

In product copy an evaluation is allowed when it has a stated basis; in a note
to colleagues it is padding either way.

### 4. The hollow contrast

不仅仅是……更是…… promises a distinction and delivers a second evaluation.

> 缺陷：这不仅仅是一个开关，更是一种全新的理念。

> 合格：这不是编译器的改动，而是缓存位置的改动。

The second sentence removes a specific misunderstanding, so the construction
stays.

### 5. Empty parallelism

Symmetrical clauses built for rhythm, with one point or none behind them.

> 缺陷：更快、更稳、更智能，让每一次构建都充满可能。

> 合格：需要你做三件事：更新构建机镜像、重启流水线、确认缓存已经恢复。

### 6. Tour-guide framing

Talk about the text instead of the text.

> 缺陷：接下来，让我们一起来看看这对你意味着什么。

> 合格：下面列出三个变化的配置项。

### 7. Invented feeling and borrowed experience

The editor gives the author an experience the material does not contain.

> 缺陷：说实话，我自己也在这个问题上栽过好几次跟头。

> 合格：8 月这个错误出现过三次。

### 8. Courtesy in place of an answer

A formula of apology or gratitude occupies the place where the reader's question
should have been answered.

> 缺陷：给您带来的不便，我们深表歉意，并将持续努力优化产品体验。

> 合格：给您带来不便，抱歉。临时方案是手工以 UTF-8 导入。

An apology is fine when the substance stands next to it.

## Legitimate Chinese that must not be flagged

- **Normative full-width punctuation.** 。，、；：？！（）「」《》 are correct in
  Chinese prose. Converting them to half-width `.,;:?!()` is a defect, not a
  cleanup. The reverse holds too: inside an English sentence or a quoted English
  phrase the punctuation stays half-width.
- **Four-character idioms used accurately.** 循序渐进、一目了然、对症下药、
  有的放矢 are ordinary literary Chinese. The form is not a machine signature;
  only an idiom standing in place of content is a defect.
- **Genuine parallel structure.** Uniformly built items in a list or a reference
  section reflect uniform material, and demanding variety damages them.
- **The spacing convention.** A space between Chinese text and Latin letters or
  digits — 从 11 分钟缩短到 4 分钟, `APP_TRACE_DIR` 用于指定目录 — is set and
  preserved, and no space is added next to full-width punctuation.
- **Half-width digits and identifiers.** 30 天, `--trace-level`, `basic`.
  Identifiers are never translated, re-cased or converted to full-width forms,
  and neither are numbers.
- **顿号 in an enumeration.** `off`、`basic` 和 `full` is correct Chinese
  punctuation; replacing 、 with commas is not a correction.
- **Mixing writing systems is a separate matter.** Simplified and traditional
  forms in one text are a real defect, but it is a question of variant
  consistency, not of anti-slop editing, and it is decided with the author.
