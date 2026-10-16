# Critical discussion: research transfer

Decision: implement a reusable method for discussing an idea, decision or
existing tool without agreeing by default. The method recovers the underlying
need, treats an example as a sample rather than the scope, compares the idea
with doing nothing and with existing solutions, and holds or revises a position
on evidence. Baseline: Assay `54d6727`. No source skill was run in a comparative
trial; the transfer is of method, not text.

The landscape was searched on 2026-10-16 with varied vocabulary across GitHub
code search for `SKILL.md`, skill catalogs and marketplaces, locally installed
marketplaces and vendor output styles. Twenty-five candidate `SKILL.md` files
were read in full. None combined triggering on ordinary discussion, refusing
default agreement, recovering the underlying need, and treating an example as a
sample of the system with the conclusion that part of it is unnecessary. The
claim is bounded by that search.

## Transfer from existing skills

Licences are listed per source. Where no licence was found, only the method is
used.

| Source / method | Licence | Transfer | Local owner / distinguishing check |
| --- | --- | --- | --- |
| [sparring-partner](https://github.com/QinghongLin/data2story-skill) (with its methodology, checklist and question references) | MIT | Framing before divergence, convergence and pressure tests; tools per phase (goal-level 5 Whys, jobs-to-be-done, "what would have to be true", premortem, steelman, Chesterton's fence, second-order effects); naming what has *not* been discussed; one or two sharp questions instead of a list. | [Pressure tests](../../skills/critical-discussion/references/pressure-tests.md). Reject its fixed minimum counts of objections and alternatives and its living document in the working directory. |
| softspark `brainstorm` | Apache-2.0 | The zero option; "is this already solved?"; what the codebase carries forever. | [Alternatives and reuse](../../skills/critical-discussion/references/alternatives-and-reuse.md). |
| gstack `office-hours` premise challenge | not checked | "Is this the right problem?" and "what existing code already partly solves it?" | Need and scope; method only. |
| alirezarezvani `office-hours` | not checked | Excitement and an "obvious" answer are reasons to check. | Reject mandatory written answers before any advice. |
| ninehills `think` | none found | Kill / Keep / Pivot verdict; "already works" during triage. | Dialogue verdict; method only. |
| openai `maintainer-review` | not checked | Restate the outcome without the mechanism; trace supported paths before calling something redundant. | Alternatives and reuse: a replacement claim requires path coverage. |
| jbonnier `sycophancy` | none found | Retreat only on a new fact, argument or constraint; "I looked for the weakness and found none" instead of an invented flaw; no flattering openers; quote the user's words. | [Dialogue](../../skills/critical-discussion/references/dialogue.md). Reject always opening with the opposing case and a mandatory closing question. |
| tj `thinking-socratic` | MIT | Close gaps from available sources first; ask the load-bearing question; stop at decision-ready; state assumptions, success and exclusions. | Dialogue. Reject explicit-only invocation. |
| Jeffallan `the-fool` | MIT | A change of perspective as a tool. | Reject a cast of personas. |
| OneWave-AI `grill-the-brief`, `devils-advocate` | MIT | Interrogate a vague brief before work. | Reject a permanent opposing role. |
| EveryInc `ce-ideate`, `ce-pov`; mattpocock `grilling`; obra `brainstorming`; other critique and red-team skills | various | Agreement on three points: need before solution, blind spots, no flattery. Parallel persona agents and scoring are not adopted. | Independent challenge remains optional and needs authorized delegation. |

No source stated that an example in the user's question is a sample rather
than the boundary. That rule, the system inventory and the verifiable
"written for nothing" claim are local additions.

## Transfer from the research foundations

| Passage | Transfer | Local owner / distinguishing check |
| --- | --- | --- |
| [Research quality §2.1](foundations/research-quality.md): separate the problem from the proposed explanation; the question must not presuppose it | Recover the need separately from the proposed solution. | Need and scope; a verified, explicit need is not re-interrogated. |
| [LLM reasoning control §3.2](foundations/llm-reasoning-control.md): hidden reference class | An example raises "a sample of what?" | Need and scope; an explicit narrow scope is respected (case C02). |
| LLM reasoning control §12.1: item counts are weak proxies | No quotas for objections, options or questions. | Sound-idea control (C03). |
| LLM reasoning control §12.3 and verification table: sycophancy; contrast the user's position with unchanged facts | Hold without new evidence, revise with it. | Paired cases C06/C07. |
| LLM reasoning control §11.1-11.2: same-context critics share blind spots and anchor on the proposal | Offer an independent challenger for costly decisions, only where delegation is authorized. | Dialogue; ordinary discussion uses no subagents. |
| LLM reasoning control §15.2: ownership bias | The agent's own counter-proposals receive the same checks. | Case C08. |
| LLM reasoning control §4.5: clarification overload | Ask only what changes the conclusion, after checking available sources. | Case C12. |
| LLM reasoning control §19.1: seven case classes | Structure of the evaluation corpus. | `evals/`. |
| Research quality §11.1, §17: anchoring, Einstellung, premature closure; premortem | Pressure-test tools; Einstellung names the fixation on an example. | Pressure tests. |
| Research quality §18: an alternative position also needs grounds | An objection without grounds is a defect, like agreement without grounds. | Sound-idea control. |
| Research quality §10.1, §14.1: states of knowledge; research conclusion versus decision | The verdict names its confidence and what would change it. | Dialogue. |
| [Software engineering §1.1, §3.1-3.2, §3.4, §8.7, §9.9](foundations/software-engineering.md): problem first; existing versus custom; abstraction needs a need; reuse creates obligations | "Written for nothing" requires coverage of supported paths, migration cost and obligations, not merely the existence of an alternative. | Alternatives and reuse; case C04. |

## Rejected considerations

- Fixed minimum numbers of objections, alternatives or questions.
- A persistent opposing role or contrarianism as the goal.
- Mandatory answers from the user before any view is given.
- Writing discussion notes or reports into the repository.
- Asserting from memory that a ready-made solution does or does not exist;
  [evidence research](../../skills/evidence-research/SKILL.md) owns that search.
- Persona casts, scoring scales and parallel critic agents by default.

## Ownership and consumers

Consumers are recurring requests to discuss ideas, decisions and existing tools
in several independent projects and both supported clients, and the Assay
skills that skip idea-only discussion: implementation planning, research-driven
change and product-flow mapping. They receive the recovered need and decision
when the user moves on to a plan, a change cycle or a scenario map. Evidence
research is an adjacent owner that performs the existence search. Software
architecture keeps boundary criteria, independent audit keeps audit verdicts.

## Evaluation boundary

[The evaluation protocol](../../skills/critical-discussion/evals/evaluation.md)
defines the cases and their limits. No paired run or discovery run has been
performed; the method is authored and structurally checked only.
