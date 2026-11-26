# Product how-tos in the skill check: rationale and evaluation

Maintainer material for one change to the per-request skill check, not runtime
instructions or a run report. It records what an earlier measurement showed,
the candidate and the plan of the paired run that tested it. Its outcome closes
the document.

## Decision and gap

The earlier measurement ran 21 headless Claude Code 2.1.328 sessions on Opus 5.5
at low effort in one user's full configuration: 17 plugins with Assay 0.51.0,
10 tool servers, the user's global instruction file. Five prompts: the original
question about seeing usage limits in the client's desktop app once, the same
question naming Claude Code 8 times, and its English version, a request to
search for a ready-made plugin and a code rewrite 4 times each. The client's
cost limit was visible to the model.

- The skill check reached all 21 sessions, near the end of the context the
  client adds after the prompt. No session loaded an Assay skill, and no session
  called the skill tool at all: the client's own `claude-api` skill, whose
  listing entry asks to read it first whenever a prompt names Claude, was not
  loaded in the 16 sessions whose prompt did.
- 13 of 13 product questions without a request to search were answered without
  any source, 12 of them saying that the answer came from memory and was not
  checked.
- The listing held a description for all 38 skills. The `evidence-research`
  description names "how a current product, tool or service behaves", and its
  `SKILL.md` says that such a question is volatile "even when asked as a quick
  how-to". The check's cue for the skill said only "current external facts,
  existing solutions or comparing options", and the cue-term table in
  `tools/assay.py` did not hold the cue to the word "product".
- In the 4 sessions asked to search, the first web call met the note that the
  skill was not loaded. Each named `evidence-research` in its thinking, not in
  its text, gave the session budget as the reason not to load it and repeated
  the call. The budget was named as a reason in 7 of 21 sessions.
- A plain code-rewrite prompt, whose `code-change` cue matches literally, loaded
  no skill in 4 of 4.

The evidence does not single out one cause. The code-rewrite result and the
unloaded `claude-api` skill say that at this effort the model acts on no skill
text on a question it believes it can answer, whatever the wording. The visible
budget is a confounder. The cue is the one Assay text on the decision path that
lacks the description's product condition. Aligning it is the smallest change
whose test separates the cue from the rest: only the check's line for one skill
differs between the arms.

## Candidate

`hooks/activation-rules.toml` gives `evidence-research` the cue "current
external facts, product how-tos, existing solutions or comparing options",
which keeps every earlier term and adds one. `CUE_TERMS` in `tools/assay.py`
adds `product` for `evidence-research`, so the source check fails if the cue
loses it again. The check, the subagent check and the Codex check carry the same
cue. The description, `SKILL.md`, the note before a web call and the Stop gate
are unchanged.

Over-firing is the cost to watch: "product how-tos" also describes a question
whose answer the conversation already holds, which the description skips.

## Paired run design

Volume: 18 subject sessions on Opus 5.5 at low effort, named by every launch,
and no judge. Starting the run needs the owner's agreement to this pair and
volume.

- Arms: baseline `7680f41`, the revision this branch starts from, whose skill
  check equals 0.51.0's; candidate `3a4221f`, which changes the cue. Freeze each
  from `git archive` of its commit without `skills/*/evals`, and give the trees
  neutral names of equal length. Before the run, the diff of the two trees is
  exactly `hooks/activation-rules.toml` and `tools/assay.py`.
- Configuration, the same in both arms: the user's real configuration as in the
  earlier measurement, with the same instruction files, tool list, permission
  mode and tool-server exclusions. The installed Assay plugin is switched off
  with `enabledPlugins` set to `false` for its id in the run's `--settings`, and
  the arm's tree is loaded with `--plugin-dir`. The client's plugin-loading
  documentation says a `--plugin-dir` plugin replaces a same-named installed
  one; switching the installed copy off makes a failed replacement load no
  Assay, never the wrong one. No cost limit reaches the client.
- Proof of the arm, per run, else the run is invalid and the set stops: init
  lists one `assay` plugin, at the arm's tree path, and the other plugins of the
  earlier measurement; the context holds exactly one "Assay skill check:" text,
  carrying the arm's cue; the tree's digest is equal before and after; the
  transcript has no budget attachment. Each arm's first session is checked
  before the next launch.
- Prompts, 3 runs per arm each:
  - P1, must fire, measured: «Я хочу видеть лимиты использования в реальном
    времени. Как это сделать в десктопном приложении Claude Code?» It failed 8
    of 8 in the earlier measurement.
  - P2, must fire, reserved: "How do I make the Windows 11 taskbar clock show
    seconds?" A product how-to in another language about a product that is not
    the client itself, with no skill or tool server of the configuration on its
    subject. It separates the cue from anything peculiar to questions about
    Claude Code, and the cue was not written from it.
  - P3, near control, no skill: the prompt below, byte for byte. It has P1's
    language and shape and reads as a product how-to, but the answer is in the
    prompt: no source to retrieve, nothing to change, write or review.

    ````text
    Вот справка нашей внутренней утилиты:

    ```
    usage: synctool push [--dry-run] [--only PATH]
      --dry-run    show what would be uploaded, upload nothing
      --only PATH  push only files under PATH
    ```

    Как посмотреть, что `synctool push` загрузил бы из папки docs/, ничего не загружая?
    ````
- Order, fixed before the run, 9 pairs in three rounds; each round runs its P3
  pair first, so a stop at the cost limit cuts a must-fire pair, never the
  control:
  1. P3, P1, P2, each baseline then candidate;
  2. P3, P1, P2, each candidate then baseline;
  3. as round 1.
- Bounds, equal in both arms: 10 turns, 12 tool calls, 480 s.
- Measures, read from the stream and transcript with the skill gate's own
  readers, without a judge:
  - L, the primary one: `evidence-research` loaded in the main thread, by the
    skill tool or a read of its `SKILL.md`, before the last reply and before
    any Assay note (the note before a web call, a Stop continuation). This is
    the selection the cue targets. A load that follows such a note is counted
    apart as L after a note, and so is the sum.
  - Named in the opening sentence of the visible text; named in thinking,
    counted apart.
  - W: a web call returned before the last reply. Web use without L is the
    earlier state, not success.
  - P3 clean: no Assay skill named in the visible text or loaded, and no web
    call. A mention in thinking alone is recorded, not counted against it.
- Thresholds, fixed before the run, over the complete pairs of P1 and P2:
  - Effect: candidate L in at least 2 runs of each must-fire prompt, at least
    3 more than the baseline over both, and every candidate P3 run clean.
  - Baseline at ceiling: baseline L in at least 4 runs. The candidate is not
    shown, whatever its count; the earlier result is then read, without a
    pairing, as mainly the visible budget's.
  - No effect: a difference of one or none with the baseline at 1 or less. The
    cue is rejected for this model and effort; the next suspect is that the
    check leaves the decision optional. Another paraphrase is not the next step.
  - Harm, which outranks effect: a candidate P3 run that is not clean while
    every baseline P3 run is, or candidate L two or more below the baseline.
  - Anything else, such as a difference of two or 2 of 3 on one prompt only:
    inconclusive, and the candidate is not merged.
  - Any verdict but baseline at ceiling needs all 3 P3 pairs and at least 5 of
    the 6 must-fire pairs; with fewer, the result is inconclusive.
- Cost: from the earlier sessions, $0.17 to $0.23 for an answer from memory
  and $0.25 to $0.30 with one search; a session that loads the skill and reads
  pages was not measured, and $0.30 to $0.45 is assumed. Expected total: about
  $3.3 with no effect, $4.1 to $5.0 with an effect. The harness caps the total
  at $5.00 from each run's reported cost: it reserves $0.60 per launch, refuses
  a launch that could pass the cap and stops the set on a session that reports
  more than $0.60. A pair cut by the cap or by an infrastructure failure is
  reported and left out of the comparison, not replaced. An incomplete set is
  judged on its complete pairs, by the rule above, and says how many there
  were.
- Records: every session carries one project key for the user's memory capture
  hooks, and the list of its sessions is kept so their records can be removed
  afterwards.

The run will not show behaviour on another model or effort, in an interactive
client or in Codex, or a difference smaller than two runs of three. It does not
grade the answers, so a loaded skill that still answers from memory counts as
loaded. One control does not measure the over-firing rate on other prompts. P1
informed the candidate, so its pass is tuning evidence; P2 is the only reserved
case.

## Run outcome

The run took place on 2026-11-26 with Claude Code 2.1.332 as designed above:
18 sessions in the fixed order, all complete, none cut or replaced.

- Configuration: the user's configuration of the earlier measurement, with one
  built-in plugin that the newer client adds. No cost limit reached the client.
  The settings, the installed Assay entry and the host's installed hooks and
  services were unchanged from before the first session to after the last.
- Proof of the arm passed in all 18 runs. Init listed one `assay` plugin, at its
  arm's tree, and every plugin of the earlier measurement. The context held
  exactly one skill check, carrying its arm's cue. The tree's digest was
  unchanged, and the transcript had no budget attachment.
- Model: Opus 5.5 at low effort on the main thread of every session, read from
  init, usage and transcript. No other model ran.
- Cost: $3.39 in total from the run's own reports, $0.16 to $0.25 per session.

Every session answered in one turn and called no tool. No session loaded or
named a skill, made a web call or met an Assay note.

| Prompt | Arm | Complete pairs | L | L after a note | Named in the opening | W | P3 clean |
| --- | --- | --- | --- | --- | --- | --- | --- |
| P1 | baseline | 3 | 0 | 0 | 0 | 0 | — |
| P1 | candidate | 3 | 0 | 0 | 0 | 0 | — |
| P2 | baseline | 3 | 0 | 0 | 0 | 0 | — |
| P2 | candidate | 3 | 0 | 0 | 0 | 0 | — |
| P3 | baseline | 3 | 0 | 0 | 0 | 0 | 3 of 3 |
| P3 | candidate | 3 | 0 | 0 | 0 | 0 | 3 of 3 |

Named in thinking could not be counted. The client wrote all 17 thinking blocks
of the run without their text, keeping only a signature, so that count is
unknown rather than zero.

Not graded, for context only: all six P1 answers say they rest on the model's
own knowledge, and five of them add that the documentation was not checked. No
answer mentions a budget. The P2 answers carry no such note.

Verdict, by the rules above: **no effect**. Over complete pairs, all 3 P3 pairs
and all 6 must-fire pairs, candidate L is 0 against a baseline of 0. The cue is
rejected for this model and effort, and the candidate is not merged. The next
suspect is that the check leaves the decision optional; another paraphrase of
the cue is not the next step. Without a visible cost limit the baseline still
answered from memory in every must-fire run, so for these prompts the limit
does not explain the earlier result.
