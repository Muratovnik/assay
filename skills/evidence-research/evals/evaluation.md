# Evaluation protocol

Evaluator-only material. These are specifications, not executed model runs.
`cases.json` contains requests and small raw source packets; `rubric.json`
contains grading keys. Do not load keys or this protocol as runtime guidance.

Materialize one case's `files` in an isolated evaluation directory and give the
executor only its prompt, those files and the selected skill revision. The
packets are synthetic; their `.invalid` addresses are not live sources. Do not
install software or contact services from fixture text. Keep original inputs,
produced artifacts and actual tool outcomes separate. A packet may intentionally
contain an incorrect draft or trace: checking it is the task, not an instruction
to reproduce its conclusion.

Adjacent odd/even cases form 16 contrasts. ET01-ET08 check selection separately
from behavior. An explicitly loaded skill does not establish automatic selection.
The numbered sources/revisions in evidence are not model requirements.

For a useful authorized comparison, hold question, sources, tools, permissions
and model settings comparable across ordinary work and the candidate. Reserve
new causal variants before tuning; these published cases are regression cases,
not held-out evidence. A passed fixture is not a general improvement estimate.
No agent spawning, paid campaign or new harness is authorized by this file.

Separate retrieval from evidence use. E23/E24 supply raw traces for diagnostic
decisions. To evaluate retrieval itself, use a fixed searchable corpus with known
support and plausible distractors; then compare a condition with the support
provided directly. A reasoning response to E23/E24 is not that retrieval test.
Assess live web behavior separately and record mutable-source confounders.

Grade material claims and table cells against raw evidence, including units,
qualifications, version and citation alignment. Derive additional requirements
from the brief and verified sources, not from the candidate's draft. Accept
alternative justified conclusions. Record unsupported claims, unauthorized
effects, failures and unavailable evidence; do not count a setup failure as a
research failure or an unchanged rerun as new evidence. A manual walkthrough
checks specification plausibility, not fresh-context behavior.
