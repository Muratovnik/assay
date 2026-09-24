# Record a material rule decision

Use for a new generalization, changed automated gate or repeated rule failure.
A spelling correction needs no new record. Extend the existing evaluation record,
not the user's deliverable or a second tracker. Executors must not read this record
or grading keys while performing the evaluated task.

Before tuning, write the outcome the rule protects and a legitimate near-neighbor
it must not reject. Distinguish a measured pattern, the interpretation of that
pattern and the intervention being proposed. An external correlation is not proof
that forcing the correlated feature improves local outcomes.

## Minimal record

- Identity and scope: stable rule ID, language, genre, skill/input revision or hash,
  owner question and date. State what is explicitly out of scope.
- Basis: primary source or incident, relevant observation, confounders and whether
  this is external reported evidence, static inspection, a deterministic fixture,
  a walkthrough or a fresh comparative run. Record sources that contradict the idea.
- Contrast: the changed condition, failure case and valid control, with separate
  withheld cases reserved before tuning. A case used to design the rule is regression
  coverage, not a held-out result.
- Observation: preserve failure and overcorrection cases, actual output/artifact
  references and available cost/time metadata. Missing evidence stays missing.
- Decision: `proposed`, `retain`, `weaken`, `remove`, `reject` or `defer`, the narrow
  reason and the evidence needed to revisit it. Give old IDs when superseding rules.

Do not fill outcome fields with hypothetical results. It is valid to retain a
bounded diagnostic after implementation tests while leaving its effect on writing
quality untested. Keep raw user data outside tracked source and future executor
packets; a compact redacted record and immutable evidence references are enough.

## Do not collapse distinct outcomes

For writing changes, assess meaning/factual fidelity, task/genre fit, editorial
restraint and voice, authorized effects, and final delivery separately. A lost
condition cannot be compensated by better style metrics. Report each material
finding with its location and evidence, including valid controls and regressions.

Keep optional numeric style observations outside those judgments. Reader preference
requires actual reader evidence; an LLM preference remains a model-judge opinion.
An authorship detector score is neither. Measure costs only from captured runs,
including retries, and never infer savings from shorter text or fewer headings.

Keep the experiment proportional: relevant defect/control pairs first, then a
previously reserved case for a material generalization when fresh execution is
authorized. No mandatory multi-model campaign, repeated clean-check count, paid
runner or new platform follows from this record. Use the existing evaluation tools.
