# What the evaluations establish

Every skill ships an `evals/` directory. It is worth being precise about what
those files prove, because the honest answer is narrower than "the skill works".

## What is in an evals directory

A skill's evaluation data is inputs and grading criteria kept apart from each
other: `cases.json` (or a differently named case collection) holds the task
prompts and their context, and `rubric.json` holds what a good answer must and
must not contain. Some skills add a `trigger-cases.json` for the separate
question of whether the skill should activate at all, and `evaluation.md`
describes how a run is set up.

They are evaluation data, not runtime instructions. A skill's own text says so:
while performing a user's task, the skill must not read its own cases or rubrics.
Reading the grading key is how a method starts scoring well without getting
better.

## What the gates check

`python tools/eval_assets.py check` validates structure: every declared case has
an id, every rubric entry points at a case that exists, every referenced input
path resolves, and no case smuggles a grading field into the input side. It does
not execute a fixture and it does not run a model.

The audit packet suite (`skills/independent-audit/evals/test_prepare_case.py`)
does execute: it builds frozen input-only packets and verifies that preparation
excludes rubrics, other cases and previous answers, and that a packet's manifest
digest matches what was actually written.

So the gates establish that the evaluation material is internally consistent and
that packet preparation is honest. They establish nothing about answer quality.

## What is deliberately not proven

No model is run in CI. There is no score in this repository, no leaderboard and
no claim that a skill improves outcomes by some percentage. Measuring that needs
a paid run against a frozen baseline, and a result would belong to the client,
model and date it was measured on rather than to the skill.

Static files also cannot prove discovery. That a skill is installed where a
client documents its skill root does not prove the client loaded it, and a model
saying it used a skill is not evidence that it did. `tools/native_smoke.py`
exists for exactly this gap: it inspects a captured client run and reports
whether the loader events actually occurred. Its verdict is deliberately narrow,
and for Codex it returns `unverified` because there is no qualified mapping from
its events to a skill activation.

The same caution applies to sandboxes. An agent profile's adapter asks for a
read-only sandbox; whether the session honoured it is a property of the run, not
of the file. Verify the effective policy rather than reading the adapter.

## If you want to evaluate a skill yourself

Use the frozen-packet preparer so the method under test sees only inputs:

```text
python tools/eval_assets.py prepare --cases skills/<skill>/evals/cases.json --case <id> --output-parent <your evidence directory>
```

Retain the returned manifest digest somewhere outside the packet, then verify the
packet with `skills/independent-audit/evals/verify_packet.py` before and after
the run. Comparing a method against a baseline means using the baseline's own
frozen directory from its revision, not today's copy of the skill.
