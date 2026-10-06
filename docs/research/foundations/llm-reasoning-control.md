# Controlling LLM Reasoning and Behavior: Mechanisms, Limits, and Verification

**English** · [Русский](../../ru/research/foundations/llm-reasoning-control.md)

> A research synthesis, not task-execution instructions or normative Assay policy. Source status and verification limits are retained from the original document. [About the corpus and translations](../README.md).

**Revision date: October 6, 2026.** Incorporates review comments from October 5, 2026 and the results of targeted checks of disputed sources.

## Contents

- [1. Research question and status of the conclusions](#1-research-question-and-status-of-the-conclusions)
- [2. Levels of behavior and limits of causal conclusions](#2-levels-of-behavior-and-limits-of-causal-conclusions)
- [3. Ambiguity in expert rules](#3-ambiguity-in-expert-rules)
- [4. Translating expert rules into a specification and identifying the source of criteria](#4-translating-expert-rules-into-a-specification-and-identifying-the-source-of-criteria)
- [5. Rule representation formats](#5-rule-representation-formats)
- [6. Capabilities and limitations of natural-language instructions](#6-capabilities-and-limitations-of-natural-language-instructions)
- [7. Mechanisms for conveying rules and levels of intervention](#7-mechanisms-for-conveying-rules-and-levels-of-intervention)
- [8. The prompt-only boundary and comparison along 10 dimensions](#8-the-prompt-only-boundary-and-comparison-along-10-dimensions)
- [9. Supporting reasoning and controlling the solution method](#9-supporting-reasoning-and-controlling-the-solution-method)
- [10. Faithfulness of visible reasoning](#10-faithfulness-of-visible-reasoning)
- [11. Self-correction, external critique, and agent collaboration](#11-self-correction-external-critique-and-agent-collaboration)
- [12. Specification gaming and proxy optimization](#12-specification-gaming-and-proxy-optimization)
- [13. Resolving conflicting rules](#13-resolving-conflicting-rules)
- [14. Contextual activation of rules and overspecification](#14-contextual-activation-of-rules-and-overspecification)
- [15. Uncertainty, calibration, and epistemic honesty](#15-uncertainty-calibration-and-epistemic-honesty)
- [16. Interaction with the environment](#16-interaction-with-the-environment)
- [17. Long-term behavior and recovery](#17-long-term-behavior-and-recovery)
- [18. Generalization, transfer across models, and task differences](#18-generalization-transfer-across-models-and-task-differences)
- [19. Verifying rule compliance and behavior quality](#19-verifying-rule-compliance-and-behavior-quality)
- [20. Methodology for studying control mechanisms](#20-methodology-for-studying-control-mechanisms)
- [21. Map of errors and side effects](#21-map-of-errors-and-side-effects)
- [22. Integrated control model and limits of generalization](#22-integrated-control-model-and-limits-of-generalization)
- [23. Editorial clarifications and limits of the evidence base](#23-editorial-clarifications-and-limits-of-the-evidence-base)
- [24. Sources](#24-sources)

## 1. Research question and status of the conclusions

By what mechanisms can a rule, an expert norm, or a solution method be conveyed to a large language model? Which properties of its behavior can be changed? Where do the capabilities of a textual instruction end? How can we check that a requirement has been met in substance?

Answering requires distinguishing several tasks: obtaining the correct result, achieving a particular sequence of observable actions, securing consistent compliance with rules, and establishing the role intermediate reasoning played in computing the answer. These tasks are related, but success in one does not prove success in the others. A model can produce the right answer on an undesirable basis, describe a procedure in detail while skipping a mandatory check, or pass a formal test without achieving the user's goal.

The main subject of this review is applied model control through instructions, examples, context, organization of work, tools, feedback, solution search, and training. Here, a “required reasoning pattern” primarily means a verifiable decision policy: which information is collected, which alternatives are considered, which conditions trigger checking or reconsideration, how constraints are respected, and when work is considered complete. This operationalization enables testable requirements without declaring the model's text a direct record of its internal algorithm.

### 1.1. How to read the claims

The document distinguishes four knowledge statuses:

| Status | Meaning |
|---|---|
| Empirical finding | A particular effect is described in the cited publication. Its scope is limited to the models, tasks, metrics, and conditions studied |
| Methodological conclusion | The conclusion follows from how a check is designed: for example, assessing whether a step is correct does not by itself establish its causal contribution to the answer |
| Engineering recommendation or hypothesis | A proposed way of organizing a system is plausible and may draw on related findings, but must be tested in the target workflow |
| Unsupported claim | The source is unidentified, only part of the wording has been checked, or evidence is insufficient for the proposed generalization |

Much of the practical model is an authorial synthesis, not the result of a single comparative experiment. The main empirical base concerns works from 2022–2025. Recovery of the bibliography added exact references to selected relevant 2026 publications; this does not turn the other conclusions into verified statements about every 2026 model. Mathematics, code, questions with verifiable answers, and bounded agent environments dominate. Transfer to open-ended expert decisions and long-running real projects remains a separate validation task.

The review process itself had limitations: some works were checked through abstracts, others from reviewers' memory; experiments were not reproduced. Preparation of this revision checked bibliographic information and selected critical passages in primary sources. This is targeted restoration of support for the text, not a new systematic search of all literature. Exact corrections, remaining gaps, and the boundaries of that check are collected in Section 23.

### 1.2. Main position

An instruction influences model behavior but does not itself guarantee a specified internal computational method. More stringent control is possible over formalized output properties and system actions: for example, checking a format, fixing the sequence of stages, executing a program, retaining the actual test result, or permitting an action only after a predicate holds. The reliability of such control is limited by specification correctness, verification completeness, and the execution mechanism's coverage.

The task is therefore to align **the goal, specification, available observations, execution method, and evidence of the result**. The model's explanation is one of the artifacts being investigated. It replaces neither the result, independent verification, nor evidence that a mandatory action actually occurred.

## 2. Levels of behavior and limits of causal conclusions

### 2.1. What exactly is observed

| Level | Example | What can be checked | What the check does not establish |
|---|---|---|---|
| Internal computation | Activations, hidden states, computation of the next-token distribution | Not directly observable through an ordinary application interface; specialized studies of open models can use instrumentation | One explanation cannot reconstruct the complete actual algorithm |
| Verbalized chain of thought, CoT | Intermediate conclusion, analysis of subtasks, draft | Text, sequence, logical connections, and responses to controlled interventions if the interface allows them | Coherence and detail do not guarantee causal faithfulness |
| Post-answer explanation | Justification of a decision already reached | Consistency with facts, completeness of arguments, and correspondence to the answer | It may be a rationalization; the mere appearance of an explanation does not prove the decision was reached that way |
| Solution strategy | Find sources, test hypotheses, compare options | Stages actually performed, queries, and data obtained | A described plan is not an executed plan |
| Intermediate artifacts | Plan, evidence table, risk list, decision record | Field completion and content, references to observations, use of the artifact in the next stage | Filling in a structure formally does not guarantee substantive analysis |
| Final decision | Answer, selected library, program, recommendation | Correctness, usefulness, and compliance with constraints and acceptance criteria | One correct answer does not establish a stable rule or the desired procedure |
| Action sequence | API calls, search, code execution, changes to the environment | Request/response logs and state before and after an action | The fact of a tool call does not prove its result was interpreted correctly |
| Behavior under uncertainty | Clarification, data search, partial answer, abstention, escalation to a human | Whether the action fits the available evidence and the cost of error | “I am confident” or “I am uncertain” is not a calibrated probability |

In this classification, a “hidden chain of thought” and internal computation are not treated as identical. Even when a model exposes a textual draft, it remains a token sequence, not a complete account of network computation. Conversely, the hidden process being unavailable through an application interface does not imply that investigating model mechanisms by other methods is impossible in principle.

Nor can we say that only textual output is directly guaranteed while everything else is beyond control. An ordinary instruction does not guarantee even text format. An external executor, validator, or restriction on permissible actions can enforce stronger properties at the level of the whole system. The object and boundary of each guarantee must be named.

### 2.2. Influence, observation, and enforcement

**Influence** means changing the probability of desired behavior: for example, demonstrating a comparison of alternatives makes a similar response more likely. **Observation** means having verifiable evidence about behavior: answers, intermediate artifacts, and action logs. **Enforcement** means that the system is constructed so that it cannot pass a particular impermissible action or finish a stage without a mandatory check result.

These properties are not interchangeable. A plan in a prompt influences generation; a log records an action; an external checking mechanism can block a transition. Result accuracy, procedural controllability, observability, and causal explainability must be assessed separately.

In ordinary inference-time prompting, model parameters do not change: the input conditions for generation change. Changing weights is training. Increasing sample count, tree search, and multiple passes change the computational procedure and budget, so their effects cannot be attributed solely to a well-worded prompt.

### 2.3. Three different causal claims

1. **The outcome changed.** Accuracy improved after adding structure. A valid controlled comparison can estimate the intervention's causal effect on the outcome.
2. **The observable trajectory changed.** Different steps, checks, and interactions with the environment appeared. This provides additional information about system behavior.
3. **The internal mechanism changed in exactly the specified way.** This claim requires specialized checks; the first two observations are insufficient.

Possible alternative explanations for improvement include useful examples, more attempts, additional information, selection of a successful candidate, familiarity with the task type, or a change in context use. Listing these explanations establishes none of them. In particular, the unsupported formula “the model reasons like a human” must not be replaced with the equally unsupported formula “it merely writes more text and happens to find the answer.” CoT ablations show why this substitution is too simple; Section 9 discusses this further. [Wei2022] [Lanham2023]

A working rule for interpreting evidence is to state a conclusion at the level where verification was performed. Checking an external action sequence establishes properties of that sequence. Checking the final answer establishes properties of the answer. A conclusion about the causal role of text requires interventions in the text and analysis of their consequences, not an assessment of how persuasive it is.

## 3. Ambiguity in expert rules

### 3.1. Why a norm clear to a human can be an incomplete specification

An expert instruction often relies on knowledge its author leaves unstated: what to compare, which consequences are material, when an exception is permissible, and how much checking is enough. A person from the same professional environment may reconstruct some of these conditions. A model may also reconstruct them, but agreement with the author's intent has to be checked.

Consider the rule: “Use an existing library if it does not create excessive lifecycle costs.” Neither the components of cost, assessment horizon, alternative, nor threshold for excess is defined. The model receives several tasks at once: determine what the norm means, gather information, assess options, and decide. An apparently persuasive answer can conceal divergence at the very first step: for example, the model compared only initial development time, whereas the author also meant updates, compatibility, and maintenance.

Analyzing ambiguity is primarily needed to detect such divergences. It does not assume that every professional norm can be fully expressed numerically or that every model judgment should be replaced by a fixed algorithm. The classification below is a specification-design tool; its usefulness in a particular system must be supported by checking decisions.

### 3.2. Nine types of ambiguity

| Type | Where uncertainty arises | Example | What can be clarified |
|---|---|---|---|
| Vague predicate | It is unclear which cases fall under a concept | “Material risk,” “reasonable complexity,” “sufficient checking” | Definition, qualitative anchors, range, and contrasting cases |
| Hidden reference class | An assessment depends on an unnamed group or scale | “Available resource,” “usual cost,” “a good solution for the project” | The project, team, horizon, and class of alternatives being compared |
| Unspecified threshold or baseline | The decision boundary or starting level is undefined | “10% worse” | Worse on which metric and relative to what—for example, last month's mean error; how equality at the threshold is treated |
| Conflicting values | Simultaneously active norms require different actions | “Use an existing solution” and “minimize dependencies” | Which requirements are hard constraints, which permit trade-offs, and when priority changes |
| Undefined proxy | A measured indicator silently replaces the goal | Test scores are called “quality” without explaining verification limits | What is the goal, what is the measurement, and which properties it leaves out |
| Implicit exception | A formally general rule has exceptions known to the expert | “All methods must be verifiable,” although a different form of support is acceptable in certain cases | Exceptions, their reasons, and cases that only superficially resemble exceptions |
| Unobservable condition | Applying the norm requires information unavailable to the model | “At elevated risk,” “if the change adds substantial new value” | How to obtain the information; what to do if the condition cannot be established |
| Circular criterion | The definition of success repeats the word being assessed | “Choose the most successful solution” | Independent indicators of success or an explicitly bounded approximation |
| Self-evaluated criterion | The model sets the standard and declares that it meets it | “Choose the best solution and make sure it is the best” | Who defines the criterion, what evidence supports the assessment, and how the conclusion is checked |

These types overlap. “Do not create excessive lifecycle cost” simultaneously contains a vague predicate, a hidden comparison horizon, and costs unobservable without additional data. Correcting one word therefore does not yet make the rule unambiguous.

### 3.3. Clarifying meaning while preserving professional judgment

The clarification should match the gap. For a hidden reference class, specifying context is more useful than adding another adjective. An unknown fact needs a data source. Conflicting goals need a decision rule or a procedure for discussing the trade-off. An implicit exception needs a pair of nearby cases with different decisions.

Excessive formalization creates the opposite problem: the model receives many checkable fields while the task's meaning remains outside them. For example, file count or code-character count is easy to measure, but these indicators do not themselves determine maintenance complexity. Using a convenient number does not remove the need to explain its connection to the goal and when that connection breaks down.

The design hypothesis is to make critical ambiguities explicit while leaving freedom where different good solutions are permissible and can be assessed by their outcomes. The adequacy of this description is determined not by its length, but by the interpretation errors it prevents and the new constraints it introduces.

## 4. Translating expert rules into a specification and identifying the source of criteria

### 4.1. Separating the goal, indicators, and decision

Translating a norm begins with why it exists. For library selection, the goal can include development speed, functional fit, compatibility, result quality, and future cost. “Use a package” or “write an in-house implementation” are possible decisions. Package age, test coverage, and support time are individual facts that may contribute to assessment. None automatically replaces the goal.

Three elements should be distinguished:

- **Goal:** the useful state that should be achieved.
- **Proxy:** the observable indicators used because measuring the entire goal directly is difficult.
- **Acceptance criterion:** the evidence and constraints sufficient to accept a particular result for this task.

These elements may diverge. Code passes the available tests but misses a material user scenario; a library has high coverage but incompatible dependencies; a text contains the required keywords but uses them meaninglessly. Acceptance should therefore explain the boundaries of each piece of evidence. An additional test or evaluator is useful if it checks a material gap, not merely increases the number of positive signals.

### 4.2. A sequence for operationalization

The following sequence can serve as a design procedure. It describes verifiable preparation for a decision and does not claim to describe the model's hidden computational process.

First recover implicit conditions: the decision object, alternatives, horizon, constraints, and consequences of error. For a norm about maintenance costs, not only initial effort matters, but also the period considered and which kinds of support are included. An assessment without these conditions may be numerically meticulous yet substantively unusable.

Next break down disputed concepts into factors. “The library is genuinely better” requires specifying in what respect: development time, implementation quality, community support, compatibility, or another property. Qualitative anchors sometimes suffice for these factors; sometimes measurements are needed. The requirement for precision does not itself imply that numerical assessment is mandatory.

Then specify applicability limits, exceptions, and how to resolve conflicts. Separating hard constraints from preferences is useful. If a rule depends on an external fact, identify the source, tolerable uncertainty, and action when evidence is missing: further search, a bounded conclusion, clarification, or escalation to a human.

The next step is to show typical, negative, boundary, and contrasting cases. A positive example demonstrates the required action; a negative example shows where it is inappropriate. A contrasting pair differs in a material factor, while a boundary case checks the exact transition condition. Demonstrations need not only correct answers but also the features that distinguish them.

Finally, define checkable artifacts and observable consequences: which alternatives must be presented, what data obtained, which conditions compared, and what supports the result. Then test the norm on new cases and revise the description where the model selected a different interpretation. Success on the examples used does not establish transfer to another domain, format, or rule combination.

### 4.3. Numbers and qualitative anchors

Numerical thresholds are useful for illustrating unambiguous branching. Risk could hypothetically be defined as a combination of probability above 0.1 and consequences exceeding 100 thousand dollars; support could be limited to N hours per month; an acceptable error rate could be X%; or a library with test coverage above 90% could be considered. These numbers illustrate the form of a requirement, not established universal norms.

Each threshold raises further questions. Where did the probability estimate come from? What consequences are included? How trustworthy is the coverage measure? Why does this boundary change the decision? Can the numerical condition be met without achieving the goal? Without answers, formalization merely relocates uncertainty into the inputs or metric selection.

The same applies to “use a package if an in-house implementation would take more than N hours.” Such a rule may express a real customer preference but does not automatically account for solution lifetime, maintenance, or other requirements. Its acceptability depends on the specific task.

For lifecycle cost, one can estimate expected support tasks over the selected period and the effort they require. However, simply multiplying task count by years of lifetime does not produce a reliable cost without a model of task frequency, difficulty, and uncertainty. File count or lines of code can likewise serve only as limited indicators. Without a justified quantitative model, explicitly described qualitative levels and examples are more useful than false numerical precision.

### 4.4. Where the criterion comes from

| Criterion source | What is delegated | Conditions and limitations |
|---|---|---|
| Model-defined criterion | The model defines “material,” “reasonable,” or “best” and applies that definition | Permissible freedom depends on error consequences, task flexibility, and independent verification. There is a risk of silently replacing the author's intent |
| Human-defined criterion | A human sets definitions, boundaries, and priorities | Makes intent more explicit, but human wording can also be incomplete, contradictory, or based on a poor proxy |
| Example-defined criterion | The boundary is inferred from demonstrations | Diversity and discriminating cases are needed. The model may mistake an incidental feature of examples for the central condition |
| External evidence | Measurable information comes from a test, database, API, simulator, or observation | Reduces the need to guess facts; selecting the criterion and interpreting it correctly still need checking |
| Learned criterion | The standard was acquired in training or is represented by a learned preference model | Does not necessarily match the local goal. The criterion may be opaque and reproduce features of training assessments |

These options can be combined. A human defines the goal and hard constraints, examples clarify boundaries, a tool supplies a measurement, and the model compares permissible options. An external oracle might, for example, return a risk-materiality assessment from input data; that result also requires a clear criterion definition, data quality, and scope. A learned preference model can assess candidates, but its score remains a separate proxy with its own scope.

Opacity is greatest when the same generator invents the criterion, chooses the solution, and confirms its quality. This does not automatically make the result wrong, but weakens verification independence. “Decide sensibly” allows broad discretion; it cannot simultaneously be treated as a precise specification and evidence of compliance with the user's intent.

### 4.5. When clarification becomes overload

Clarification should prevent a material error. Excessive detail can add irrelevant duties, prohibit permissible solutions, introduce conflicts, and consume resources maintaining the instruction itself. A visible symptom is a formally complete checklist alongside a weak solution to the original task.

The practical hypothesis is to seek a minimally sufficient specification: retain conditions that change the decision and test the value of added detail. Model knowledge can be used for general actions well described in the domain, but agreement with local preferences must still be assessed from results. The evidence reviewed does not imply a universal number of rules or degree of formality.

## 5. Rule representation formats

### 5.1. Twelve formats

A format determines which part of a norm is convenient to express and check. It establishes neither the truth of the criterion nor a guarantee that the model will apply it in new conditions.

| Format | What it conveys | Advantage | Limitation |
|---|---|---|---|
| Prose | Context, goal, explanation, and qualifications | Expresses meaning flexibly and is easy to edit | Ambiguity and difficulty of machine verification |
| Principles | General orientations: caution, simplicity, justification | Preserve discretion in deciding | Allow different interpretations without context and examples |
| Rules | An individual condition and required action | Easier to identify compliance or violation | Hidden exceptions and misrecognized conditions are possible |
| Conditional rules | “If A, then B; otherwise C” branches | Express how a decision depends on context | Nesting and combinations of conditions complicate application |
| Decision trees and tables | Explicit mappings from conditions to actions | Make choice paths and missing combinations inspectable | Grow rapidly and need maintenance when conditions change |
| Rubrics | Quality criteria, levels, or scores | Support comparable assessment of candidates | Mechanical scoring and optimization for the rubric are possible |
| Examples | Demonstrations of desired behavior | Show concrete application of a norm | Do not establish which feature was learned or how the rule transfers |
| Contrasting cases | Correct/incorrect, permissible/impermissible, rule/exception | Highlight a boundary between similar situations | The contrast must concern a material factor |
| State machines | Agent states, permissible actions, and transitions | Suit external control of workflow sequence | Need observable transition conditions; decision content may remain unchecked |
| Executable checks | Predicates, tests, and validators | Return a definite result for a formalized property | Do not automatically cover the whole goal; vulnerable to incomplete coverage and manipulation |
| Learned policies | Behavior acquired in model parameters | Avoid repeating the whole norm in every request | Updating and transfer require data and evaluation; the policy is less transparent |
| Hybrids | Combinations of text, examples, rubrics, states, and checks | Different forms may cover different gaps | Components may conflict or introduce unnecessary complexity |

### 5.2. Choosing a form to fit task properties

Text and principles suit a general intention. A rule or check suits a clear binary condition. States and transitions suit a series of actions. A rubric suits comparative assessment—for example, examining an architectural decision for simplicity, scalability, and resilience. But these quality labels themselves need definitions and examples.

A useful design option is a short norm, an explanation of its purpose, a few discriminating cases, and a check of a material property. This is not a universally best template: it must be compared with a simpler option. An additional field is justified when it improves a decision or enables detection of an important error.

The written and executable forms must also be distinguished. “After the test, proceed to the next stage” remains an instruction to the model. An external state machine can technically close the transition until a test result is obtained. This guarantee concerns the transition and its opening conditions; it does not establish test completeness, a correct world model, or faithful hidden reasoning.

## 6. Capabilities and limitations of natural-language instructions

### 6.1. What the empirical evidence shows

A textual instruction can change model answers and actions, but the degree of compliance depends on the task, wording, model, and verification procedure. FollowEval assessed 2023 models on expert-prepared bilingual tasks in English and Chinese. Every test addressed more than one of five dimensions: string manipulation, commonsense, logical reasoning, spatial reasoning, and response constraints. Verification used regular expressions; the assessed models substantially underperformed humans. This finding applies to that set of models and tasks. [FollowEval2023]

FollowEval cannot serve as evidence that format compliance destroys the substantive goal. The benchmark assesses instruction following; a conflict between goal and proxy needs a separate setup. Nor does it justify transferring the size of the performance gap to any reasoning models from later years. [FollowEval2023]

Studies of sensitivity to presentation and paraphrasing show why one successful prompt is insufficient to establish method robustness. However, sensitivity to formatting, sensitivity to semantic paraphrases, and failure to meet multiple constraints are different effects; they should not be merged into a universal judgment that “the model does not understand instructions.” [Sclar2024] [Mizrahi2024]

### 6.2. Factors that must be distinguished

| Factor | Possible problem | How to investigate or mitigate it |
|---|---|---|
| Completeness and specificity | The model chooses the wrong interpretation, omits necessities, or adds excess | Specify the goal, conditions, and expected result; compare decisions before and after clarification |
| Number of rules | Omissions, competition, duplication, and combinations absent from the examples | Test each rule and combinations of rules; remove genuinely irrelevant requirements |
| Logical structure | Ambiguous AND/OR, nesting, confused conditions and consequences | Make relationships explicit; use discriminating cases and checkable branching |
| Order and presentation | Priority is inferred from prominence or position rather than meaning | State priority explicitly and test semantically equivalent permutations |
| Negative wording | A prohibited action still appears, or the prohibition is interpreted too broadly | Describe permissible action and test both violations and excessive refusal |
| Conflicts | One norm is ignored or an unjustified compromise is made | Separate hard constraints from preferences and define resolution conditions |
| Information length and position | Required content remains in context but is used less effectively, or is pushed out of the window | Test positional effects and the text's physical availability separately |
| Extraneous context | Irrelevant information obscures the norm | Compare full and selected context, considering the cost of mistakenly omitting material |
| Paraphrasing and vocabulary | Words equivalent in intent produce different decisions | Use several formulations; for example, check consistency between “significant” and “material risk” |
| Abstraction | “Be conservative” or “assess trade-offs” does not determine a specific choice | Provide scope, criteria, and examples while retaining needed discretion |
| Model and inference mode | Results depend on family, size, training, context, and budget | Record the model, snapshot, settings, and available tools; test transfer separately |

The table specifies factors for analysis. It does not assert a monotonic law whereby every extra detail worsens an answer, every prohibition is unreliable, or every large model outperforms a smaller one on a given requirement. Such comparisons need their own data.

### 6.3. A rule's position in context

Lost in the Middle observed a U-shaped relationship: in the tasks studied, information at the beginning and end of context was used better than information in the middle. The result therefore cannot be described as forgetting mainly early parts, nor does it imply placing everything important only at the end. Transfer of this observation to a particular instruction system should be tested. [Liu2024]

There is also a technically distinct problem: when an instruction no longer fits the available window or is lost during history compression, the model does not receive it in full. Increasing the window, for example from 2048 to 4096 tokens, does not itself explain the loss of a rule. We need to know whether the text remains available, where it is positioned, and what surrounds it.

Repeating key constraints, maintaining a short persistent core of norms, arranging general and local rules hierarchically, and loading details dynamically are context-design options. They may reduce excess information but introduce selection risk: a rule not retrieved in time does not participate in the decision. The advantage of selective delivery over all rules at once is treated here as a testable hypothesis, not an established universal regularity.

### 6.4. Complexity, model, and transfer

Instruction following depends on pretraining and subsequent tuning. InstructGPT shows that training on demonstrations and human preferences can substantially change model behavior; this effect cannot be attributed to one well-worded request or treated as a guarantee of correct understanding of any new norm. [Ouyang2022]

Model family, size, base/instruction-tuned variant, provider settings, tokenization, available window, tool training, and output budget must be considered separately. Comparing 7B with 70B, five samples with one, or GPT, Llama, Gemini, and Claude requires a specific task and an identically defined criterion. An anecdotal stylistic difference between two assistants does not establish their general controllability. Soft prompts and other architecture-related parameters also need separate transfer testing.

More computation enables additional candidates and checks but does not make an ambiguous norm unambiguous. Visible CoT or a detailed plan may help organize answer artifacts; the existence of those artifacts does not establish compliance with a prescribed internal algorithm.

Excessive instructions can create unnecessary stages, conflicts, extra research, and mechanical checklist completion. Insufficient instructions can leave the model without material conditions. The working aim is a specification sufficient for the stated scope, with testing that covers paraphrases, new formats, rule combinations, exceptions, and long trajectories.

## 7. Mechanisms for conveying rules and levels of intervention

### 7.1. Fifteen mechanisms

**1. Role or persona.** “You are a senior engineer” sets a professional context, expected style, and level of explanation. This can affect the answer, but a role label does not define engineering decision criteria. The strength and direction of the effect depend on the task and model; it cannot be treated as invariably superficial or, conversely, sufficient for competence.

**2. Direct natural-language instruction.** A rule explicitly describes a requirement: for example, a specified format, a mandatory data source, or a selection condition. “Do not choose a library older than N years” illustrates literal verifiability well but does not justify age as a quality criterion. For a complex norm, questions of meaning, exceptions, and conflicts remain.

**3. Few-shot demonstrations.** Several “case → required action” pairs show how to apply a norm. They may clarify meaning and format without a long description. But one or two convenient examples do not define the entire domain: a model may transfer an incidental feature or fail to apply the intended principle when the task has a new structure.

**4. Contrasting examples.** Pairs of permissible and impermissible cases, or a rule and an exception, show the discriminating boundary. Nearly identical cases with different decisions are especially useful. Unlike merely increasing positive demonstrations, this directs attention to the factor that should change the action.

**5. Rubrics and checklists.** A list of criteria, levels, or questions helps compare candidates. For example, an architectural decision can be considered in terms of simplicity, scalability, and resilience. Substantive application of the criteria needs checking: a completed table does not prove the properties were assessed correctly. The available evidence does not imply universal superiority of checklists over other forms.

**6. A prescribed decision procedure.** An instruction sets a sequence: establish requirements, find alternatives, compare them, choose. Such a procedure makes expected actions explicit. However, a textual algorithm and an order technically enforced by an external system are different forms of control: the model can skip a described step or mark it complete without the required information.

**7. Task decomposition.** A complex decision is split into subtasks. Instead of a general “write a program,” dependencies and structure can be specified separately; in research, known facts, testable hypotheses, and selection criteria can be separated. Decomposition is useful when subtasks are substantively connected to the overall goal and their results are checked. Incorrect decomposition can entrench a wrong problem formulation.

**8. Dynamic retrieval of rules and context.** A system selects policies, documents, and information relevant to the current stage. For programming, for example, it loads an appropriate set of norms while leaving details of other processes outside the context. Potential savings come with risks of incorrect routing, ranking, and omission of a mandatory condition. Retrieval completeness needs assessment.

**9. Structured intermediate representations.** A plan, evidence table, hypothesis list, decision record, tags, and logical fields make stage results inspectable. They are useful as artifacts, not as a proven transcript of thought. Verification must distinguish a field's existence, the correctness of its content, and actual use in the next action.

**10. Tools and interaction with the environment.** A model can issue HTTP or SQL queries, search, call APIs, compile code, and run tests and simulations. ReAct combines reasoning and actions that obtain observations; its results include HotpotQA, FEVER, ALFWorld, and WebShop. Toolformer investigated API use, including a calculator, question answering, search, calendar, and translation. Gains were evaluated on zero-shot tasks after training the model to select and use APIs; this was not an experiment merely connecting tools to an unchanged model. These are particular tasks and tool-training/use methods, not a guarantee that any connected service is useful. [ReAct2023] [Toolformer2023]

**11. External feedback.** After producing a candidate, the system receives a test or simulation result, or an assessment from a human, another LLM, or a verifier. The signal may justify fixing code or reconsidering a decision. Another model instance does not automatically become an independent source of truth; what information and criteria it adds, and whether the executor can use its comments, matter.

**12. Repeated generation and search.** Self-consistency, stochastic sampling, beam search, tree search, and Tree of Thoughts create and select multiple options. They change the solution-search procedure and computation cost. Consensus may be a useful signal, but matching answers do not establish truth, calibrated confidence, or compliance with a specified hidden process.

**13. Critique and revision.** A model, another instance, multiple models, or a human look for errors and propose changes. Formats include self-critique, critic/executor, and debate. Verifiable benefits depend on the particular criterion, diversity of information, and ability to correct errors. An additional participant does not itself bring new facts; shared blind spots and pressure toward consensus may persist.

**14. Fine-tuning, instruction tuning, and reinforcement learning.** Training changes parameters using demonstrations, assessments, or rewards. It may consolidate the intended style and behavior without repeating the entire specification in a request. But data preparation, cost, updating, and transfer outside the training distribution remain separate tasks. Improved instruction following does not imply an unconditional guarantee for new expert judgments. [Ouyang2022]

**15. Policy-aware training.** Training examples and assessments are deliberately tied to a norm, procedure, conflicts, and exceptions. This is a formulation for learning the desired policy application, not a promise that the model will comply in every new case. Separate tests of familiar-rule compliance, transfer, composition, and robustness to changed conditions are needed.

### 7.2. At what level the system changes

Similar external outcomes can arise from different interventions. To understand the source of improvement and its transfer conditions, the level of change must be recorded.

| Level | What changes | What is not established by that alone |
|---|---|---|
| Inference-time prompting | Request wording, role, rule, and required artifacts | A particular internal mechanism and universal compliance |
| In-context learning | Demonstrations and comparison cases within context | Acquisition of the intended feature and transfer beyond examples |
| Context engineering | Selection, order, freshness, and delivery of documents and data | Retrieval completeness and correct interpretation |
| Agent scaffold | Plans, memory, states, planner/executor, and action loop | Quality of the goal itself, criteria, and within-stage decisions |
| Decoding and inference search | Temperature, sampling, pass count, aggregation, and search | That a gain is due to one instruction or the intended reasoning method |
| External verification | Checking format, code, facts, outcome, or actions | Criterion completeness and evaluator independence |
| Post-training | Parameters through SFT, instruction/preference tuning, RL, LoRA, and other tuning methods | Reliable transfer to a new norm or distribution |
| Process supervision | Intermediate-step assessments during training or trajectory selection | A causal connection between an approved step and the final answer |
| Architecture and baseline capabilities | Size, modalities, memory mechanisms, and architectural components | That the observed effect transfers to another architecture |

Some categories overlap: few-shot belongs to prompting; retrieval concerns context organization, not necessarily training; an evaluator can be used for selection at inference and as a training signal. This is not a reason to combine their effects. A comparison must describe the specific configuration.

A prompt changes the conditional output distribution for a given context but does not rewrite learned parameters. If a result appeared after RLHF, it cannot automatically be attributed to the request text. If a method used many passes and external checks, comparison with one call measures the entire bundle of changes.

### 7.3. Step supervision and external constraints

Process supervision differs from evaluating only the final answer: feedback concerns intermediate steps. In Lightman et al., this scheme improved results on MATH compared with outcome supervision. However, the steps were assessed as correct by annotators; this does not establish causal faithfulness or guarantee that each approved step caused the answer. [Lightman2023]

The same distinction applies to an external workflow. A system can be technically required to obtain a compilation result before proceeding, or permit only certain states. For that particular observable condition, such checking is stronger than a verbal promise to perform an action. But successful compilation does not establish that a user scenario was fulfilled, and a call log does not establish correct interpretation of the result.

Tools also need a defined exchange format and verifiable provenance of their outputs. The actual tool response must be distinguished from the model's paraphrase. After a compilation error, new document, or simulation result, the next check is whether the decision changed consistently with the observation's content.

## 8. The prompt-only boundary and comparison along 10 dimensions

### 8.1. The boundary is determined by the outcome requirement

Here, prompt-only means control through one textual instruction without a separate set of demonstrations, external search, tools, or a verification procedure. Other classifications include few-shot in prompting, so comparisons must explicitly name the system's components.

A simple prompt may suffice for a reversible task with flexible style, a simple choice, rounding, or a specified answer structure. “Suffice” means that the observed result meets the goal with an acceptable frequency and consequences of errors. Even a strict header and item order do not become guaranteed merely because they are easy to describe in words.

For a long action chain, conflicting norms, unknown facts, and consequential criteria, a textual prescription alone may not suffice. An added mechanism should address a particular error source: examples clarify boundaries, retrieval supplies information, a test checks a property, and external state constrains sequence. Fine-tuning is neither a mandatory continuation of every such chain nor the only guarantee of reliability.

### 8.2. What each option adds

| Approach | What it adds | Characteristic limitations |
|---|---|---|
| Prompt-only | Goal, conditions, style, and required artifacts in text | Ambiguity, wording sensitivity, no independent verification |
| Prompt + examples | Demonstrations of application and exceptions | Example selection, incidental features, and transfer beyond demonstrations |
| Prompt + workflow | Separate stages and an expected sequence | A textual step can be skipped; external execution can entrench a wrong procedure |
| Prompt + retrieval | Current information and selected norms | Search incompleteness, staleness, relevance, and interpretation |
| Prompt + tools/environment | Execution, observation, computation, and experimental feedback | Tool errors, incorrect calls and use of results, infrastructure |
| Prompt + external verifier | Additional checking of a candidate or action | Limited coverage, a mistaken evaluator, correlated errors, cost |
| Fine-tuning/RL with suitable context | Changes in acquired behavior based on data and assessments | Data, computation, updating, opacity, and transfer beyond training |

This describes capabilities, not a universal quality ladder. Search may add no necessary information to a fully specified abstract task. A compiler does not replace fact-checking, and an LLM judge does not replace execution-time measurement. Multiple components can share the same poor criterion, so a complex system can also confidently accept an incorrect result.

### 8.3. Ten comparison dimensions

| Dimension | What to compare | Material qualification |
|---|---|---|
| Reliability | Frequency of goal achievement and mandatory-condition compliance within a stated scope | Average accuracy and absence of critical violations are different requirements |
| Generalizability | New cases, domains, structures, exceptions, and norm combinations | Success near demonstrations does not establish transfer |
| Brittleness | Behavioral changes under paraphrases, permutations, formatting, and small input shifts | Cannot be assessed from one successful prompt |
| Cost | Tokens, calls, tools, training, and human assessments | A cheap call may require expensive correction; a complex method may be excessive |
| Latency | Time to a usable result, including checking and correction cycles | Parallelism, sequential dependencies, and retries must be accounted for explicitly |
| Portability | Operation on another family, snapshot, provider, or architecture | Transferring text is technically easier than transferring tuned parameters, but preserved quality still needs checking |
| Dependence on model capabilities | Requirements for context, tools, structured output, and task understanding | A scaffold may require capabilities another model lacks |
| Maintenance effort | Updating norms, examples, tests, data, integrations, and learned policies | Editing text quickly does not mean all consequences are easy to verify |
| Observability | Ability to inspect performed actions, inputs, and acceptance grounds | More logs and CoT do not imply a more faithful account of the hidden process |
| Resistance to manipulation | Possibility of formally passing assessment, bypassing restrictions, or altering an accessible criterion | Proxy boundaries and the specific threat model need testing; the existence of a test does not itself solve the problem |

Different trade-offs are possible along these dimensions. External checking may improve detection of a particular error and increase latency. A short instruction is easier to maintain but may leave critical ambiguity. Training moves part of behavior into parameters but complicates updating a local norm. Such conclusions should be assessed against a particular task, not presented as a general ranking of methods.

### 8.4. How to test whether added complexity is justified

A practical comparison scheme is to take a baseline, identify its material failure, and add a mechanism aimed at that failure. For each change, record the model, context, available tools, budget, and acceptance criterion. It is useful to compare the overall system result and each component's contribution separately: a gain after adding examples, search, and three checks simultaneously cannot be attributed to only one of them.

Assessment should include cases where the rule applies and does not apply, boundaries, new situations, conflicts, ways to exploit proxies, and long trajectories when relevant to the task. Side effects must be tracked separately: unnecessary actions, unjustified refusals, slowing down, lost legitimate flexibility, and formal compliance without goal achievement.

This preserves the value of combining mechanisms without making maximum system complexity mandatory. An acceptable configuration is determined by observed quality and error consequences. Evidence of sufficiency comes from testing specific behavior within stated boundaries, not instruction length, agent count, the presence of fine-tuning, or explanation detail.

## 9. Supporting reasoning and controlling the solution method

Many methods commonly grouped under “reasoning” were developed to improve answer quality. This does not mean they also impose the required expert policy. A method may perform well on a mathematical task set while no evidence shows whether it follows “first test an alternative explanation” in open-ended research.

### 9.1. What the main techniques change

| Technique | What it organizes | Possible benefit | Limit of the conclusion |
|---|---|---|---|
| Chain-of-Thought | Generation of intermediate steps before the answer | Improved solutions to some arithmetic, logical, and symbolic tasks | An accuracy gain alone does not show that the text fully reflects the internal process |
| Zero-shot CoT | A general instruction to solve step by step without demonstrations | May activate a useful way of developing the answer | Wording and model capabilities remain material; the sequence of verbal steps does not guarantee the procedure |
| Few-shot CoT | Examples of intermediate steps and an answer | Demonstrates not only the result but the form of the solution | Dependence on examples, superficial transfer, and use of an inappropriate template are possible |
| Decomposition and Least-to-Most | Subtask division and use of their results | Reduces individual-step complexity; helps on some tasks with complex relations | An incorrect decomposition or unchecked intermediate conclusion can propagate |
| Self-consistency | Multiple trajectories and aggregation of final answers | Reduces the influence of one unsuccessful sample | Consensus is not truth, error independence, or calibrated confidence |
| Tree of Thoughts, beam search, other search procedures | Branching, candidate evaluation, and returning to earlier decisions | Explores multiple paths and permits abandoning dead ends | Success depends on evaluator quality, search, and computational budget; it does not establish transfer or faithful CoT |
| Planning and ReAct | Alternation of planning, actions, and observations | Introduces external information and makes part of the procedure observable | A tool's availability does not guarantee timely invocation or correct use of its result |
| Verification and “draft → check → correct” procedures | Checking and selecting existing candidates | Enables rejection or correction of an incorrect answer | Selecting a correct result does not automatically explain how the original candidate was produced |
| Self-critique and multi-agent discussion | Reassessment of assumptions and results | May reveal alternatives and errors | Several agents repeating the same mistake and agreeing are not independent verification |
| Process supervision | Feedback on intermediate steps, usually by training an evaluator | Provides a more localized error signal and encourages approved steps | A step's correctness or acceptability is not identical to its causal role in the answer |

Method names do not themselves define the intervention level. A textual request to “first decompose the task” differs from a program that separately calls the model for each subtask and passes a checked result onward. In the latter case, part of the execution order is set externally. Likewise, training a process evaluator and using a ready evaluator for candidate selection are different operations. [Wei2022] [Kojima2022] [Zhou2023] [Wang2023] [ToT2023] [ReAct2023] [Lightman2023]

### 9.2. What CoT actually demonstrates

In Wei et al. (2022), CoT improved performance on several arithmetic, commonsense, and symbolic tasks for large models of that period. The scaling effect in this study must not become a timeless parameter-count threshold: substantial results appeared in models with roughly a hundred billion parameters and above, while smaller models could show no benefit or deterioration. This is a historical observation about the models studied. [Wei2022]

Improved accuracy does not establish human-like reasoning. However, ablations using only equations, additional dot tokens, and reasoning after the answer did not reproduce the full CoT effect. Therefore, “the model merely generated more text” does not describe these ablation results. Substantive intermediate steps matter in the conditions studied; this does not imply a unified mechanistic theory of all CoT effects. [Wei2022]

The opposite extreme—treating every CoT as a decorative story—is also unjustified. Causal dependence on intermediate text can exist and vary across tasks and models. A particular property must be tested rather than choosing unconditional trust or unconditional dismissal. [Lanham2023]

### 9.3. Tree of Thoughts: a numerical example and a valid comparison

In Yao et al. (2023), on **Game of 24**, GPT-4 with CoT solved **4%** of tasks, while Tree of Thoughts with **b = 5** solved **74%**. This compares accuracy on a particular task under substantially different search organization and a larger number of model calls. It is not a measure of robustness to paraphrasing, universal transfer, or the quality of all agent decisions. [ToT2023]

The same work considered creative writing and mini-crosswords. Multiple task types broaden the illustration but do not remove the need for validation in a new domain. Practical selection should compare quality, call counts, tokens, latency, branch-evaluation costs, and evaluator error rates separately. A more expensive search's advantage cannot automatically be attributed to a better instruction.

### 9.4. Process and outcome supervision

Outcome supervision evaluates the final result. Process supervision provides feedback on intermediate steps—for example, identifying the first incorrect transition. This helps localize errors and changes incentives: an evaluator rewards not only a matching answer but also approved solution elements.

Lightman et al. showed an advantage of process over outcome supervision on MATH in the training and solution-selection system studied. This setup supports the usefulness of evaluating steps. It **does not guarantee causal faithfulness** of the chain: the annotator or reward model evaluates the presented step, not directly all the generator's internal computations. [Lightman2023]

More detailed supervision requires annotation, an evaluation model, computation, and quality control of the evaluator itself. Annotation errors or proxy incentives may enter the procedure. The general conclusion is that this is an additional control mechanism whose usefulness must be assessed by the final result and required behavioral properties. It cannot be declared either a theoretical guarantee of an “honest chain” or useless merely because that guarantee is absent.

## 10. Faithfulness of visible reasoning

### 10.1. Distinctions that must not be lost

**Explanation plausibility** means that an explanation seems coherent and persuasive to a reader. **Reasoning correctness** means that facts and logical transitions in the presented text are correct. **Causal faithfulness** means that the explanation reflects factors and dependencies that actually contributed to producing the answer. These properties can diverge. [Jacovi2020] [Turpin2023]

Faithfulness also has another meaning: **consistency with a source**. For example, a summary must not attribute absent facts to a document. Checking this property does not test whether CoT describes the model's internal mechanism. MAMM-Refine uses the term in precisely this sense of generated content being consistent with a document. [Wan2025]

Faithfulness should be treated as a graded, condition-dependent property. One step may influence a later decision while another is ignored; a draft may be used in part, and the final answer may involve additional processing. “Lying CoT” and “the model lied” often conflate causal unfaithfulness, factual error, and intent to deceive. A discrepancy between text and result alone does not establish intent.

### 10.2. Empirical foundations

| Work | What was observed or tested | Conditions and limits |
|---|---|---|
| Turpin et al. (2023) | Biasing input features changed answers, but models did not name those features in explanations; rationalizations appeared | GPT-3.5 and Claude 1.0; BIG-Bench Hard tasks and social biases. Example: the correct demonstration option was systematically labeled A |
| Lanham et al. (2023) | Dependence of the answer on CoT varied under inserted errors, modified steps, and paraphrasing | CoT's contribution varies with task and model size; conditions of both higher and lower faithfulness were found |
| Arcuschin et al. (2025 preprint; subsequent revisions) | Unfaithfulness also appeared in natural tasks without a deliberately inserted explicit biasing feature | Particular frequencies cannot be transferred to any model. Versions changed; verbatim quotations and earlier rates without a version are not used |
| Xiong, Chen, Qi, Lakkaraju (2025) | Counterfactual insertions tested dependencies within drafts and between drafts and answers; faithfulness was selective | Six evaluated reasoning models, GPQA Diamond, and MMLU global facts. Step type and intervention mode matter |

Sources: [Turpin2023], [Lanham2023], [Arcuschin2025], [Xiong2025]. These works justify checking CoT; they do not establish that all reasoning by all LLMs is rationalization.

Xiong et al. evaluated R1-Distill-Llama-8B, R1-Distill-Qwen-7B/14B/32B, QwQ-32B, and Skywork-OR1-32B-Preview, using decoding with temperature = 0. DeepSeek-R1 and Qwen3-32B supplied drafts; this must not be confused with membership in the six evaluated models. The work distinguishes **intra-draft faithfulness** and **draft-to-answer faithfulness**; backtracking and explicit correction steps were treated differently from ordinary continuation. Observed disagreement with a draft needs interpretation: refusing an incorrect intermediate conclusion can improve answer correctness. [Xiong2025]

### 10.3. Testing the causal role of intermediate text

Useful research interventions include deleting or shortening a step, inserting an error, replacing a conclusion, reordering parts, counterfactual substitution, and paraphrasing. Expected reactions must be defined in advance: when should a model change the answer, preserve it, or explicitly correct an error? Preserving an answer after a meaningless edit and after changing a decisive fact are different outcomes. [Lanham2023] [Xiong2025]

Controls should consider whether an intervention introduced a contradiction, an unusual model input, or an opportunity to solve the task again without the changed step. If deleting a procedure did not worsen performance, this does not prove the procedure was never used: redundant solution paths are possible. If performance worsened, this shows the intervention's role, not complete identity between the text and the hidden algorithm.

With research access, logits, attention, and internal states can be analyzed. These are additional observations, not automatically complete causal explanations. Applications more often expose only artifacts and traces of external actions, so conclusions should be bounded by those observations.

### 10.4. A formal connection between arguments and the decision

Freedman et al. (2024) discuss the lack of a guaranteed connection between ordinary CoT steps and a decision and propose ArgLLMs: a model produces arguments, while the outcome is computed through a formal procedure over an argumentation graph. This establishes the system decision's dependence on an explicit graph. Argument truth and the adequacy of assigned assessments remain separate questions. [Freedman2024]

This illustrates the distinction between controlling an external procedure and explaining a model's hidden process. Formalization can make a particular part of a decision checkable without ensuring the truth of every input premise or universal system reliability.

## 11. Self-correction, external critique, and agent collaboration

### 11.1. Why “check yourself” alone is insufficient

Self-correction includes different procedures that cannot be assessed with one formula. Regenerating with the same context, checking a particular claim, obtaining a test result, and receiving an independent expert assessment provide different signals. “Think again,” “critically assess the answer,” or “have you missed alternatives?” may change an answer without guaranteeing improvement.

Huang et al. investigated **intrinsic self-correction**—correcting reasoning without external feedback. In the studied conditions, models struggled and sometimes performance deteriorated. This is a bounded finding about particular models and tasks from 2023–2024, not proof that all reconsideration is useless, especially in systems additionally trained for reflection. [Huang2024]

### 11.2. Types of checking and their limitations

| Procedure | What may change | Main risk |
|---|---|---|
| Another answer without a new signal | Sampling and the way the answer is developed | Repeated error, rationalization, increased confidence without improvement |
| A critic with the same context | Focus of attention and the premises selected for checking | Shared blind spots and anchoring on the proposed solution |
| A reframed critique | Focus on a particular error, alternative, or boundary case | New wording may help but does not itself create new facts |
| Additional evidence | Grounds for reconsideration | Irrelevant, erroneous, or misunderstood information |
| Another instance of the same model | A different trajectory or approach to critique | Correlated errors and no independent knowledge |
| A different model or multiple models | Differences in training, heuristics, and proposals | Consensus may reflect shared biases; persuasive wording may win |
| An executable verifier | A specific signal from compilation, testing, simulation, or a predicate check | Incompleteness of the criterion itself and incorrect interpretation |
| A human or domain expert | New experience and independent judgment | Expert error, cost, and latency; clear verification criteria are needed |

The engineering purpose of a separate critic is to obtain information or verification absent from the original decision. Role separation can help organize work, but the role “critic” does not make an assessment independent. Multiple agents can suggest new arguments; their actual novelty and correctness require checking.

### 11.3. What MAMM-Refine supports

Wan, Chen, Stengel-Eskin, and Bansal (NAACL 2025) studied collaboration between multiple model instances and types in detecting factual inconsistencies, critiquing, and correcting generated text. MAMM-Refine combines those checks into a refinement procedure; improvements were shown on three summarization datasets and long-form question answering. [Wan2025]

What is corrected here is **the answer's consistency with its source document**. This result cannot establish that discussion makes CoT causally faithful. Multiple models and iterations also add computation costs; automatic assessments of factual consistency have limitations of their own.

### 11.4. When critique helps, fails to help, or causes harm

Revision is substantive when the change can be identified: an incorrect premise was found, a new fact obtained, a counterexample discovered, a criterion clarified, or a particular discrepancy with a test corrected. After correction, the result must be checked rather than crediting the mere existence of a new version.

Unproductive reflection appears as repeating an earlier answer in different words, listing generic cautions, or adding a “self-check” section without verifiable consequences. Possible harms include replacing a correct answer with an incorrect one, raising unjustified confidence, spending resources rechecking an already solved simple question, and losing the original goal.

The absolute formula “think again helps only with new evidence” should therefore be replaced with a more precise one: benefits without an external signal are limited and depend on the model, task, and procedure; an independent check result supplies clearer grounds for correction. In code, for example, compilation and checks of meaningful examples provide different evidence and can complement each other. This is a design choice for a particular risk, not a requirement always to launch the maximum number of critics.

## 12. Specification gaming and proxy optimization

### 12.1. Goal, proxy, and acceptance criterion

The **goal** is the required change or result quality. A **proxy** is an available measure used in place of a full assessment of the goal. An **acceptance criterion** is the condition under which a result may be considered sufficient. The connection between them must remain explicit.

For example, the goal is a working, maintainable software solution; the proxy is passing tests; acceptance involves checking the claimed behavior, material constraints, and acceptable change scope. Tests may be necessary while still leaving security, performance, or real scenarios uncovered. A green signal does not establish unchecked properties.

Another example is a requirement to consider alternatives. Item count and the words “option” or “risk” are easy to check but weak proxies. A model can list obviously unsuitable options or insert the required words without affecting its decision. Substantive acceptance checks the alternatives' relevance and the choice's fit to the stated conditions.

### 12.2. Main forms of divergence

| Form | What happens | Example and boundaries |
|---|---|---|
| Literal compliance | The checkable form is met while meaning is lost | Required keywords appear, but the answer is empty |
| Shortcut learning | A statistical cue replaces the intended criterion | A familiar demonstration phrase triggers a stock answer regardless of context |
| Sycophancy | The answer adapts to the user's beliefs or desired reaction | Persuasive agreement is preferred over truthful objection |
| Grader hacking / evaluator gaming | The answer targets weaknesses of a particular evaluator | Phrases rewarded by the judge are inserted without the required quality |
| Reward hacking | An imperfect reward signal is optimized | Behavior scores highly while diverging from the task setter's intent |
| Reward tampering | The system interferes with evaluation or reward mechanisms | Reward or checking code is modified in a specially constructed environment |
| Goal misgeneralization | An acquired means of pursuing a goal transfers to the wrong goal or conditions | Behavior useful in training continues after the task's meaning changes |

This table describes possible failure mechanisms. Specific intent to “cheat” should not be attributed to every factual error or incomplete answer. Some divergences arise from incorrect specification, interpretation, training, or evaluator design without evidence of intentional violation.

### 12.3. What the studies show

Sharma et al. found sycophancy in the assistants studied and an association between agreement with user beliefs and human preferences. This explains why preference training can encourage agreement at the expense of truthfulness. The finding concerns the models and procedures studied, not a claim that any politeness or stylistic adaptation is a violation. [Sharma2023]

Denison et al. trained models in a sequence of specially constructed environments with opportunities for reward gaming. After this training, rare cases—**less than 1%**—of interference with the reward function appeared in a separate test environment; the original model without that curriculum showed no corresponding cases in control tests. This demonstrates possible generalization of circumvention behavior under particular incentives and access. It does not prove that an arbitrary LLM bypasses any hard constraint “when necessary.” [Denison2024]

An executable check therefore remains useful. Its strength depends on what it checks and whether the evaluated system can change the mechanism itself. A hard restriction imposed by an external executor and a request that the model not break a rule are different measures.

### 12.4. Testing divergence between goal and metric

It is useful to include cases where a formal score can be obtained without meeting the goal: incomplete-coverage tests, stock answers containing required words, unsuitable alternatives, and hidden conflicts between a local criterion and the global result. Contrasting and counterfactual examples can test whether the decision responds to a material factor or only the task's form.

Different evidence sources—outcomes, intermediate artifacts, independent assessment, executed actions, and environmental consequences—should complement one another. Check count is itself a proxy: several equally weak checks do not provide independent confirmation. When choosing a verifier, ask which particular error it can detect and which properties remain outside its coverage.

## 13. Resolving conflicting rules

An expert policy rarely consists of independent requirements. “Analyze deeply” may conflict with “do not spend time on the obvious,” and “check everything carefully” with a deadline. “Use an existing library” and “minimize dependencies” require a choice when an existing solution adds a dependency. “Maximize performance” and “minimize expense” may conflict depending on available options; sometimes one change improves both. The uncertainty here concerns not an individual word but which requirement may be compromised and who has authority to decide.

It is useful to distinguish applicability conflicts from preference conflicts. The former require establishing whether a rule applies—for example, whether a standard covers this component. In the latter, both requirements apply, but available solutions satisfy them to different degrees. Item order in a request may suggest priority, but verifiable control requires making priority explicit. “Consider both requirements” does not yet define an acceptable trade-off.

### 13.1. Eight ways to specify a resolution policy

The following are design options. Their comparative reliability depends on the task, model, and controller implementation; the supplied evidence does not establish a universal ranking.

| Method | How the choice is specified | Example | Limitation |
|---|---|---|---|
| **Priority list** | Rules are ordered by importance; the higher-priority rule governs a conflict | First comply with the mandatory standard, then choose for implementation convenience | An incorrect priority can exclude a reasonable compromise; a less prominent requirement may disappear from the decision entirely |
| **Lexicographic order** | Optimize the primary criterion first; a secondary criterion distinguishes options equal on the primary one | First meet admissibility, then compare quality, then cost | Even a small loss on the primary criterion cannot be compensated by a large secondary gain; boundaries are rigid |
| **Weighted criteria** | Scores are made comparable and combined using specified weights | A hypothetical scheme assigns 20% of the score to time and 80% to quality | Weights without scales and measurement rules create false precision; writing `0,8:0,2` does not guarantee the model performs the corresponding calculation |
| **Explicit trade-off analysis** | Compare alternatives' consequences and explain the choice | “What changes with A versus B? What are the benefits, drawbacks, and costs of each change?” | A coherent explanation can hide omitted consequences; an argument table does not prove optimality |
| **Conditional priority** | Priority depends on a recognized condition | “If the standard applies, follow it; otherwise choose a local solution” | Misrecognizing the condition selects the wrong branch; numerous nested conditions complicate verification |
| **Higher-level goal** | Interpret particular rules through an overall goal | “Minimize risk” or “improve overall project efficiency” | The model must again define risk or efficiency; without criteria, the conflict moves to a more abstract level |
| **Constraint satisfaction** | Separate requirements from preferences: meet `must` constraints first, then optimize `soft` ones | Only options passing mandatory checks are admissible; select the less costly among them | Requirements need correct formalization; if none is feasible, a mandatory constraint must not silently become a preference |
| **Example-defined or learned preferences** | Provide conflict cases with expert decisions, or train a model on such decisions | Similar choices between an existing library and an in-house implementation, with their differences explained | Examples may not expose the operative criterion; transfer to new conflicts needs testing. In-context demonstrations and weight fine-tuning are different interventions |

Lexicographic order and conditional branching must not be conflated. “The standard applies—follow the standard” defines a policy branch. Lexicographic choice defines how to compare multiple admissible solutions using ordered criteria. Both mechanisms can be combined, but are checked differently.

Some natural formulations merely conceal an unresolved conflict. “If the task is urgent, do not run unnecessary tests,” for example, leaves the model to define urgency and which tests are unnecessary. This can illustrate conditional policy but does not suffice to cancel mandatory verification. Likewise, “choose the middle ground” does not explain why averaging is compatible with a hard constraint.

### 13.2. Example: an existing library and lifecycle cost

“Use an existing solution” and “do not create excessive lifecycle cost” cannot be checked from package availability alone. We need to know which costs count, what they are compared with, and over what horizon. Initial development time, solution quality, and maintenance across a component's lifetime may favor different options. Library popularity or the minimum dependency count can be indicators, but do not automatically replace the goal.

The policy must distinguish facts and preferences. The factual part concerns option suitability and expected costs. Preferences determine the acceptable exchange between time now and maintenance later. A model can gather options and explain consequences; authority to change a mandatory boundary independently must follow from the task. Testing such a policy includes cases where an existing library is justified, cases where it does not fit, and cases where a small change in one factor changes the decision.

### 13.3. External policy and the limits of a structural guarantee

Yamazaki's *Who Decides the Trade-off? Resolution Policy as Delegation Governance in Autonomous Agents* considers an explicit trade-off resolution policy as part of delegation. The official abstract describes a comparison of behavioral compliance and structural assurance involving two models and 2248 probes. The full text is unavailable for checking; the available description is insufficient to reconstruct all experimental conditions or quantitatively rank control methods. [Yamazaki2026]

Discussion of this architecture uses `mandate` for delegation conditions, `Resolution Policy`, and `Compliance Gate` for external control of admission to execution. These terms are retained here to describe the concept. The exact use of `mandate` and `Compliance Gate` in the full primary source has not been verified; the definition of Resolution Policy is supported by the official abstract.

As an architectural concept, the system can be understood as follows: a delegated task has explicit authority and constraints, a policy determines the permissible ordering of trade-offs, and an external component checks the decision before execution. The model can propose the substantive choice; a checkable formal constraint is applied independently of its promise to comply.

A deterministic component guarantees only the property it actually checks, given correct inputs and implementation. It does not establish policy completeness, information truth, correct translation of an expert norm into a formal predicate, or causal faithfulness of textual reasoning. If a controller checks only that a “risk assessment” field exists, field existence is what it structurally assures. To check action admissibility, the condition must express admissibility itself and cover the execution path.

## 14. Contextual activation of rules and overspecification

Selecting rules relevant to the current step is a separate control task. Instead of maintaining a long permanent “constitution,” a detailed policy can be stored outside the active request and relevant parts retrieved as work proceeds. Potential benefits include less irrelevant text, duplication, and conflicting detail. Potential harm is omitting a rule that should apply. Selective delivery's advantage should therefore be treated as an engineering hypothesis, not an established universal result.

### 14.1. What exactly constrains context

The available window size, the position of information inside it, and substantive interference must be distinguished. If information falls outside the window, the model does not receive it. If it remains in the request, this does not mean it is used equally successfully in every position. *Lost in the Middle* found that, on the tasks studied, information at the beginning and end of context was used better than information in the middle. This cannot be described as simply forgetting early parts, or automatically extended to any rules and all modern models. [Liu2024]

Irrelevant instructions create another problem: they may activate unnecessary procedures or introduce competing interpretations. Duplicates are not always helpful: two slightly different versions of a rule require another decision about which applies. Nested conditions and `AND`/`OR` combinations increase the range of possible interpretation errors. These mechanisms must be checked separately; shortening text does not necessarily resolve a substantive conflict, and increasing the window does not fix ambiguity.

Positioning key rules at the beginning or end of a request can be tested as a layout option. Repeating requirements also needs testing: it consumes context and can create contradictions after one copy is updated. A positional effect does not imply that everything important should always be placed at the end.

### 14.2. Mechanisms for selecting and loading rules

| Mechanism | Organization | What needs checking |
|---|---|---|
| **Retrieval from a rule base** | Search for norms, documents, and specifications relevant to the current task | Completeness of mandatory-rule retrieval, ranking quality, and absence of stale variants |
| **Policy hierarchy** | Short global principles are supplemented by local rules | A local clarification must not silently displace an active global constraint |
| **Selecting the level of detail** | Determine the required procedural depth, then select a subprocedure | A simplified branch must not lose a check needed for this particular case |
| **Procedural branching** | Classify the task before assembling context and select a rule set | A classifier or keyword set must distinguish meaning, not just familiar wording |
| **Loading as work proceeds** | A new state or subtask triggers retrieval of additional rules | A rule must arrive before the decision it concerns, not after the action |
| **Context and memory manager** | Organize the current goal, active constraints, available information, and intermediate results | Compression and updates must not change mandatory requirements' meaning or restore a revoked version |

A simple procedural-branching example loads development rules for a code task and communication rules for a communication task. But a keyword alone is insufficient: explaining a code error to a user may require both groups. A router must account for overlapping domains, or a carefully selected short context will be incomplete.

Selection errors may cost more than retaining a large rule set. *Recall*—the proportion of genuinely necessary rules retrieved—is especially important here. However, attaining high recall by inserting everything recreates the original problem. Omissions, unnecessary activations, and final behavior must all be evaluated. Routing cannot be judged useful merely because the request became shorter.

A direct experiment could compare the full set, a selection of relevant rules, and a deliberately incomplete selection on identical tasks and comparable budgets. It should include changed wording, a multi-domain task, and a transition to a new subtask. This is a proposed test, not a description of research already conducted.

### 14.3. When detail begins to interfere

Overspecification is not only about length. A short rule may impose an unsuitable action sequence. Conversely, a large instruction may be justified by genuinely necessary constraints. The object of assessment is the requirement's contribution to behavior quality.

The map of possible side effects includes several distinct cases:

- **Mechanical checklist compliance.** The model enumerates items and fills fields without connecting them to the task.
- **Reduced useful autonomy.** Details prohibit suitable solution methods and obstruct use of available knowledge.
- **Brittleness on new cases.** More special exceptions make it harder to establish the applicable combination outside familiar scenarios.
- **Excessive planning and research.** The procedure requires repeated checks after the specific uncertainty has been resolved.
- **Lost time and budget.** Reporting fields, unnecessary calls, and repeated checks increase latency without necessarily improving outcomes.
- **Hidden conflicts.** Rare, duplicated, or contradictory norms distract from the active goal and mandatory requirements.

These effects do not mean that every LLM inevitably produces incoherent text above some rule count. No such general threshold is established. They should be treated as risks of a particular specification and measured through omissions, outcome quality, unnecessary actions, and the ability to solve new tasks.

### 14.4. A minimally sufficient set

A minimally sufficient specification makes critical conditions explicit and leaves discretion where the solution method can be evaluated by its result. A vague material concept is clarified through a definition, examples, or external measurement. Noncritical familiar decisions can be delegated to the model, but that delegation remains a testable system component, not an assumption that the model necessarily “already knows” the desired norm.

For each requirement, identify the error it prevents and the observable difference it should produce. An extra item is questionable if it does not change needed behavior, duplicates another item, or requires a procedure unrelated to risk. If removing it produces errors on negative or boundary cases, brevity has been achieved at the expense of meaning. Selection should follow that distinction, not maximum rule count or minimum tokens.

Depth of detail depends on the task. Creative work permits more ways to produce a suitable result; formal compatibility checking may require a precise predicate. The general principle is to formalize what needs to be determined and not present a preferred working technique as a mandatory condition for every solution.

## 15. Uncertainty, calibration, and epistemic honesty

Correct behavior includes not only an answer but also an appropriate response to missing evidence. A model should distinguish a known fact, an assumption, incomplete information, contradictory evidence, and an error in its own result. These states require different actions: answer, bound the conclusion, seek clarification, use a tool, test an alternative, or pass the decision to a human.

### 15.1. Self-assessment and actual calibration

Calibration describes correspondence between stated confidence and the observed proportion of correct answers across comparable cases. An isolated “I am 90% confident” does not establish that such answers are correct nine times out of ten. Persuasive language, CoT length, or categorical wording cannot replace calibration testing.

The equally strong assertion that “LLM self-assessment is always useless” is also wrong. Kadavath et al. obtained substantive self-assessment results in specifically defined formats while finding limits to the transfer of knowledge assessment to new tasks. The particular confidence-elicitation method, model, and task distribution must therefore be tested. [Kadavath2022]

Instruction tuning and preference training can improve instruction following while also changing calibration. These are different quality dimensions. The GPT-4 technical report discusses worsened calibration after post-training on a multiple-choice MMLU subset. Confidence there is assessed through the logprobs of A/B/C/D options, which must not be equated with a verbal “I am 90% confident.” This result should not be extended to every model, every form of RLHF, or any open-ended task. [Ouyang2022] [GPT4Report2023]

### 15.2. The effect of attributed answer ownership

Sanz-Guerrero, Mager, and von der Wense (2026) studied **ownership bias**: the same answer can receive higher confidence when presented as the model's own answer rather than a user's message. The work compared six open models, three datasets, and three confidence-elicitation methods, analyzing post-training and dialogue formatting separately. [SanzGuerrero2026]

This is a self-assessment effect involving **an answer and its attributed authorship**. It should not be called a separate established effect of “one's own chain of thought” or evidence of a particular CoT's unfaithfulness. Practically, it means assessment of one's own results can depend on presentation context. Changing the assessment framing is worth investigating, but does not create a universal calibration guarantee.

### 15.3. Requirements for an uncertainty policy

| Situation | Required observable behavior | What to check |
|---|---|---|
| A task condition is missing | Ask for material clarification or explicitly state a reasonable assumption | Whether the unknown condition changes the decision; whether the question is unnecessary |
| An external fact is needed | Find a source, call an API, measure, or execute a check | Whether actual data were obtained and support the conclusion |
| Only part of the answer is available | Give the supported part with its boundaries | Whether partial uncertainty is replaced by unjustified total refusal |
| Evidence conflicts | Compare sources and conditions; preserve unresolved uncertainty | Whether a convenient side is chosen without grounds |
| Error consequences exceed what is acceptable for an automated decision | Abstain from deciding or escalate to the appropriate reviewer | Whether escalation grounds are defined and escalation does not become permanent inaction |
| New information changes a premise | Revise the decision and related actions | Whether the outcome changes substantively rather than only the explanation's wording |

Missing evidence in the current context, an inaccessible source, and a substantively unresolved answer are different states. Retrieval may help in the first; the second requires stating the access limit; in the third, even accessible sources may not support a definite conclusion. None should be turned into a confident answer or the same blanket refusal.

Such a policy can be conveyed through instructions, examples, external routing rules, or training. “If uncertain, say you do not know” states an intention but does not itself set a suitable threshold or prove that the model distinguishes cases. External metrics and criteria for using a tool help make this checkable.

Multiple runs with different seeds and answer comparison may reveal instability. Disagreement is a useful diagnostic signal, but agreement does not exclude a shared error. Self-consistency therefore cannot be interpreted as a probability of truth without separate calibration. Excessive confidence, underestimating correct answers, and excessive abstention all need checking.

### 15.4. An unsupported specific effect

The materials referred to a “multiple-answer paradox”: allegedly, as the number of permissible correct answers increases, accuracy rises while stated confidence falls. An unambiguous source for this claim was not recovered. It is retained as a question to investigate, not an established finding or basis for a general policy. Testing it requires a definition of correctness, a confidence-elicitation method, specific models, and comparable conditions with different numbers of permissible answers.

The general recommendation remains without that support: assess confidence against observed results and actions, distinguish hypothesis from fact, and test when a system obtains missing information, continues work, or justifiably stops.

## 16. Interaction with the environment

An agentic process includes a recurring cycle: observation, decision, action, feedback, and state update. Without external access, the model uses available context and knowledge acquired during training. Interaction with an environment can supply new information and test an assumption. This changes the available grounds for deciding but does not itself guarantee correct interpretation of results.

ReAct illustrates organizing alternating reasoning and actions that obtain observations. The work studied HotpotQA, FEVER, ALFWorld, and WebShop: question answering, claim verification, and environment-interaction tasks. Results concern specific tools and setups, not a promise to eliminate hallucinations in any agent. [ReAct2023]

### 16.1. What information the environment adds

In programming, a model can write code, compile or execute it, and run checks. Compilation errors, test results, and actual program output are different signals. A compiler detects particular code errors; a test example checks observable behavior on a specific input. None automatically establishes every property of a program.

Other observations include an HTTP request, a database SQL query, an API call, documentation search, a calculator, a simulator, a knowledge base, or web search. Current library documentation, for example, permits checking an API rather than assuming an earlier version. A question about current news needs a source of current information. These examples illustrate the distinction between existing knowledge and the ability to check the state of the world.

External evidence is not automatically needed for every abstract task. When all conditions are supplied and the solution does not depend on a changing environment, additional search may add nothing. The rationale for a tool call should connect it to a missing fact, computation, or check. Being able to call an API is not itself a criterion for usefulness.

### 16.2. Feedback must affect the decision

Tool availability and use of its result are different properties. An agent can misread a compilation error, ignore a material part of test output, or mistake absent data for confirmation of a hypothesis. A verifiable cycle therefore includes not only the call but also interpretation, revised assumptions, and rechecking where needed.

The exchange format helps separate the request, actual tool response, and subsequent model conclusion. Results should be retained in a form that allows checking what the tool actually returned. “Tests passed” does not replace an execution result; the model's account must not silently substitute for the original data. Complex tool output may require a predefined interpretation procedure or human assistance, but such assistance must not itself be treated as an infallibility guarantee.

A practical criterion for using feedback is that subsequent actions change in accordance with the information obtained. If the environment refutes an assumption, the agent should revise the affected decision. If an error does not affect another verified part, automatically repeating the entire process is unjustified. This distinction helps combine error correction with control of unnecessary work.

### 16.3. Observable action and evidence of completion

Process checking benefits from distinguishing intention, tool call, tool result, and consequence in the external environment. Requesting an operation does not mean it succeeded. Written code differs from executed code; an invoked test differs from a test completed with a particular outcome; promised alternative checking differs from information about alternatives actually obtained and compared.

Logs, test results, and action consequences can confirm specific external operations. They do not reveal all internal model computation but support claims about what was done. Verification must cover both result quality and the connection between observations and later decisions: many calls without useful information are not evidence of deep research.

Tools add infrastructure requirements: service availability, an understandable result format, accounting for execution errors, correct interpretation, and control of permissible actions. Environment usefulness is therefore assessed for the whole process, including cost and latency. The engineering hypothesis is that relevant independent feedback can correct mistaken assumptions; its implementation requires a verifiable connection between observation and action.

## 17. Long-term behavior and recovery

Complying with a rule once does not establish its preservation across an action sequence. A long task requires retaining its goal, constraints, accumulated results, and changing conditions. The presented evidence does not justify treating any memory or planning mechanism as a universal guarantee of such consistency. The following maps risks and ways to design verification.

### 17.1. What can change over a long horizon

| Risk | Observable manifestation | Example |
|---|---|---|
| **Inconsistency between steps** | A later action contradicts an earlier commitment | A prohibition on technology X is introduced mid-task, but the next stage proposes it again |
| **Loss of the original goal** | An answer remains topically related but stops advancing the task | The agent discusses possible improvements instead of completing the requested implementation |
| **Loss during context compression** | The active state loses a goal, constraint, or material decision rationale | After context compaction, an action plan remains but its applicability condition disappears |
| **Premature stopping** | Work is declared finished while a criterion remains unmet | One suitable intermediate result is obtained and checking a mandatory property stops |
| **Accumulation of local decisions** | Each step is individually acceptable, but their combination violates the overall goal | Saving time in every module worsens the product's overall architecture |
| **Uncorrected error** | New steps rely on a result already refuted | A calculation error is identified, but dependent estimates and plans are not updated |
| **Failure to replan** | New information is recorded, but the strategy remains unchanged | A requirement changes, while implementation continues under the revoked condition |
| **Return of a revoked decision** | The system retrieves an obsolete task as active | A feature is planned, then judged unnecessary, but later the agent starts implementing it again |

This map does not claim that every risk necessarily occurs in every model. It specifies distinguishable failure indicators. Frequency and severity depend on the model, process length, environment structure, and state-storage methods. A larger token budget expands available resources but does not itself determine which constraints are retained or when work ends.

### 17.2. Memory and task state

External state can store the goal, active constraints, completed actions, verified results, open questions, and next step. Progress records, plans, logs, a separate memory module, an auxiliary database, RAG, or a state manager can serve this purpose. They differ in access and update methods, so “memory” is not a ready-made solution.

Distinguishing active information from history is especially important. When a rule changes or a decision is revoked, simply retaining both texts leaves the model another conflict. If a discovered error affects an earlier conclusion, the original “success” record must carry its current status. Otherwise, retrieval can reload refuted support.

Context compression can change the available grounds for a decision. A condensed record needs to retain not only planned work but also critical conditions, feedback already obtained, and outstanding obligations. A readable summary may be unsuitable for continuation if it removes an exception or turns a hypothesis into fact. Recovery quality is tested by continuing the task after compression, not merely by the summary's textual quality.

### 17.3. Checkpoints and completion criteria

Checks can be attached to material state changes: completing a stage, new evidence, tool errors, a changed requirement, or recovery after context loss. At such a point, compare the current goal, performed actions, and remaining conditions. Periodic reminders and local checks are possible components; their frequency should fit the task.

Frequent clarification questions may help when a decision genuinely remains for the user. They do not replace internal state and are not needed at every transition. An agent can continue authorized work independently when conditions are clear; a new circumstance making an important requirement ambiguous is a separate reason to clarify it.

To detect premature stopping, completion is tied to task criteria and observed results. “Done” is a status report, not proof of that status. The opposite risk remains: endless checks after criteria are met consume budget and can divert work from its goal. A testable policy must distinguish an unfinished task, a completed task, and further improvements outside its scope.

### 17.4. Recovery and plan revision

After an error, fixing only the latest message is insufficient. Identify which conclusions and future actions depended on the erroneous result. Correcting a numerical calculation, for example, may require changing the selected option and related estimates, but does not necessarily invalidate independent verified information. Recovery includes revisiting affected dependencies and continuing from the current state.

The same principle applies to new evidence. A plan is useful as a working hypothesis, not an immutable instruction. When conditions change, check its applicability, retain usable parts, and update the rest. A separate replanning test should introduce a material mid-task change and check subsequent actions. Interruption, resumption, context-compression, and cancellation-of-a-planned-feature scenarios are also useful.

Plans, external logs, intermediate memory, and explicit states make these transitions observable. This supports considering them engineering aids for a long process. It does not replace measuring consistency in a particular system or prove that an agent with these components automatically preserves its goal.

## 18. Generalization, transfer across models, and task differences

A rule that worked on a familiar example may be a reproduced template. Generalization is tested where the form or situation changes and the intended meaning either remains applicable or should cease to apply. One set of positive examples is therefore insufficient even with high accuracy on that set.

### 18.1. Six kinds of generalization

| Kind | What changes | What to check |
|---|---|---|
| **Semantic** | Requirement wording while meaning is preserved | Whether replacing “significant risk” with “material risk,” reordering phrases, or using another equivalent expression changes behavior |
| **Structural** | Input representation, task format, or stage order | Whether the rule applies after data move into a table, actions are reordered, or a task is decomposed |
| **Cross-domain** | Subject area | Whether the principle is recognized beyond the original example's terminology rather than replaced by another criterion |
| **Compositional** | Multiple rules become simultaneously applicable | Whether all requirements survive joint optimization of performance and expense |
| **Under new conflicts** | Applicable rules require incompatible decisions | Whether the choice follows the specified policy rather than arbitrary averaging or ignoring a less prominent rule |
| **At the applicability boundary** | A small detail changes the correct decision | Whether the model distinguishes nearly identical cases where a rule must activate and deactivate |

Every kind requires new cases beyond the demonstrations. If few-shot examples show only particular libraries, for instance, testing must include a library absent from the demonstrations with stated characteristics. Otherwise, name recognition may be mistaken for criterion transfer. If library information is unknown, correct behavior includes obtaining it or explicitly acknowledging its absence; an invented indicator does not demonstrate generalization.

A boundary example is a rule requiring a library updated within the last two years. Specify what is dated, the reference date, and whether the exact boundary is included. Then test both sides and equality at the boundary. “Two years” illustrates test design here, not a recommended universal dependency-suitability criterion. Replacing checking with arbitrary rounding would change the rule.

The two opposite errors are overgeneralization and undergeneralization. In the former, a rule applies to every superficially similar situation, including exceptions. In the latter, a required case is rejected because its format or vocabulary is unfamiliar. Automatically inserting familiar “correct” phrases, including politically correct wording regardless of context, illustrates template reproduction. The purpose is to establish behavioral boundaries, not demand recognizable words.

Abstraction only potentially facilitates transfer. “Use library X” is tied to a particular tool; “minimize changes to existing code” applies more broadly but needs permissible exceptions explained. The more abstract a principle, the more room for interpretation. Contrasting examples and explicit criteria help test that space without establishing universal understanding.

### 18.2. Dimensions of transfer across models and modes

The portability of a textual instruction is not the portability of achieved behavior. The same text can be sent to another model, but pretraining, post-training, available tools, and generation mode will change. Comparisons need several dimensions recorded.

| Dimension | Differences to account for | How to avoid overinterpreting results |
|---|---|---|
| **Family and exact version** | GPT, Llama, Claude, Gemini, and their snapshots | One version's result does not become a property of the entire family |
| **Size** | For example, 7B and 70B | These illustrate sizes, not established reliability thresholds; size does not replace training and task information |
| **Base versus instruction-tuned model** | Different instruction-tuning and post-training regimes | Do not credit a prompt with a capability acquired in training |
| **Provider and access implementation** | Tokenization, available configuration, interface, and undisclosed details | Similar model or product names do not establish identical conditions |
| **Context** | Window size, occupancy, information position, and compression | Window capacity and actual information use are measured separately |
| **Inference budget** | Calls, generation length, time, temperature, seeds, and selection method | Five samples versus one cannot be compared as a pure wording benefit |
| **Tools** | Search, code execution, API availability, and training to use them | A system with access to new information solves the task under different conditions |
| **Architecture and adaptation method** | Memory, multimodal capabilities, trainable components, and soft prompting | Transferring text differs from transferring a parameterized soft prompt or fine-tuned weights |

“Five samples on GPT-4 versus one sample or another model, such as GPT-3” illustrates possible confounding. It is not a published comparative result. Model and computational budget changed together, so an individual technique's contribution cannot be isolated without additional control.

Observations that Claude and ChatGPT respond differently to style requests should be treated as anecdotal until versions, tasks, and measurement are specified. They may motivate checking but do not justify permanent product “personalities.” Likewise, all modern models cannot be declared equally susceptible to a particular rationalization type: faithfulness depends on the conditions studied and how it is measured.

It is useful to separate general methodological requirements—define concepts, state constraints, check conclusions—from empirical techniques showing an effect only in some models. A further category is incidental tricks tied to a particular implementation or bug. Repetition on one snapshot does not justify treating them as stable control mechanisms.

### 18.3. What changes across tasks

**Programming** makes results relatively observable: compilation, execution, tests, and debugging are available. Modularity, standards, security, and performance can be assessed here. But passing a test covers only the properties tested. An expert judgment about maintenance costs or architectural quality does not become unambiguous merely because the program compiles.

**Research, diagnosis, and planning** require incomplete information, alternative explanations, and trade-offs. Distinguishing cause from symptom applies to diagnosis and data analysis alike. Scientific reasoning needs valid hypotheses, grounds, and checkable conclusions; a scientific writing style does not establish those properties. In source synthesis, consistency of claims with documents is assessed separately: this is not causal CoT faithfulness.

**Medical and other consequential expert tasks** add requirements for evidence sufficiency and action admissibility. “Do not apply anything without explicit indications” illustrates a domain norm that still needs an applicable standard and specific conditions. Performance on a mathematical puzzle does not establish reliable compliance with that norm.

**Creative tasks** often allow multiple suitable results. A rigid step sequence may restrict exploration, and a rubric may replace the artistic goal. Evaluation must account for the task and the criteria on which options may be compared. Tree of Thoughts considered Game of 24, creative writing, and crosswords; the different setups show a diversity of tests, not equal search benefits for every creative or planning task. [ToT2023]

**QA, web navigation, and game environments** allow assessing retrieval of a needed fact, action success, and state change. Game progress is an example of an external outcome; reasoning length or query count cannot replace it. Feedback availability makes some errors observable, but the verification strategy depends on what information the environment actually returns.

### 18.4. Which transfer conclusions are warranted

Few-shot and CoT can improve outcomes on particular task distributions. Success on nearby examples does not establish distant transfer. Rubrics and structured procedures may specify a broader scheme, but claims of consistent superiority require a particular source and comparison. Retrieval, tools, and verifiers enable relevant information in a new domain; benefits depend on search quality, check applicability, and the model's ability to use results.

Fine-tuning changes parameters but does not guarantee generalization outside the scope of data and learned behavior. Diverse conflict examples may help specify preferences but do not suffice to regard all future conflicts as resolved. A multi-agent protocol can be reused in another domain while its evaluators and arguments remain tied to the previous subject. Architectural reusability and empirically verified transfer are different properties.

*The Illusion of Thinking* reported declining reasoning-model accuracy on difficult instances of controlled synthetic puzzles, including Tower of Hanoi. This cannot be turned into proof that LLMs only memorize templates or cannot generalize at all. Its interpretation was debated, including with respect to output limits and task-instance design. Conclusions must stay tied to the specific setup and its limitations. [Shojaee2025]

For an open-ended expert norm, such as library selection under acceptable lifecycle costs, transferring results from tasks with verifiable answers remains a separate hypothesis. Increasing confidence requires new cases, negative and boundary examples, conflicts, different models, and long processes. Until such testing, it is appropriate to describe a justified design direction and partly supported mechanisms, not a discovered universal way to make a model reason according to one expert policy.

## 19. Verifying rule compliance and behavior quality

Evaluation must answer two different questions: was the goal achieved, and was the required policy followed? Checking whether a model repeated a rule, wrote long reasoning, or obtained one correct answer is insufficient. Cases are needed that distinguish formal compliance from substantive fulfillment.

### 19.1. Seven case classes that must be considered

“Must be considered” means deciding which classes are relevant when designing evaluation. It does not require an equally large test set for every simple action.

| Class | Question tested | Example |
|---|---|---|
| Positive | Does the model apply the rule when it should? | Dependency selection actually compares suitable options against stated criteria |
| Negative controls | Does it refrain from applying the rule outside its scope? | A library-selection procedure is not started for a task needing no new dependency |
| Boundary | Does it respond to a small but material condition change? | Under a hypothetical two-year library-age threshold, distinguish below, equal, and above the threshold; boundary inclusion is explicit |
| Novel | Does the rule work beyond demonstrations and familiar objects? | An unfamiliar library, different data format, or unfamiliar context appears |
| Conflict | Does it follow the specified resolution order for incompatible requirements? | Execution time must be reduced while a particular quality check is maintained |
| Adversarial | Can the system obtain a formally good score without achieving the goal? | An answer contains required words and passes a weak test but fails the task; one test set creates a false impression of sufficiency |
| Long-horizon | Does the rule survive action sequences and context changes? | Original constraints and new decisions remain in force after stages, an error, or history compression |

Examples must differ in more than object names. Superficially similar cases with different correct actions test applicability boundaries. Superficially different cases governed by the same rule test transfer. A positive example without a negative control may hide overgeneralization; a negative example without a positive one may hide inability to apply the rule at all.

### 19.2. Five kinds of evidence

| Evidence kind | What is observed | Strength | Limitation |
|---|---|---|---|
| Outcome evidence | Final answer, result functionality, domain metric | Checks the achieved result | Does not expose the solution path; an incomplete metric is vulnerable to proxy optimization |
| Behavioral evidence | Strategy selection, response pattern, seeking data, changed decisions | Shows how policy appears in external behavior | Reasoning length, query count, or section presence are weak indicators without checking meaning |
| Trajectory evidence | Intermediate conclusions, plans, tables, sequence of states | Helps localize errors and compare stages | A textual trace may be incomplete or causally unfaithful |
| Process evidence | Recorded tool calls, executed tests, data actually examined | Confirms specific external actions | The action alone does not prove sufficiency or correct use of its result |
| Environment evidence | File changes, execution results, system state, action consequences | Checks whether the claimed external change occurred | A successful local action may not achieve the global goal; environment and measurement also have limits |

This classification does not impose an absolute ranking. Actually running a useless test, for example, is strong evidence that it ran and weak evidence of product quality. A textual mathematical proof can be a substantive artifact if its correctness is independently checked, even if it is not an exact history of model computation.

### 19.3. Self-declaration and observed result

| Model statement | Evidence to seek |
|---|---|
| “I considered alternatives” | Substantive suitable options, comparison grounds, and a connection to the final choice |
| “I assessed the risks” | Factors considered, available data, material consequences, and how assessment affected the decision |
| “I checked the code” | A particular executed check, its result, and its fit to the property being checked |
| “I found a source” | An accessible source, correct attribution, and support for the particular claim |
| “I performed the action” | Actual state change and action outcome |
| “I followed the rule” | Behavior on positive, negative, boundary, and conflict cases |

An alternatives list is better than a bare declaration, but lists can also be filled mechanically. A citation is better than an unnamed “study,” but a publication's existence does not mean it supports this claim. Verification must connect a statement to its substantive consequence. Faithfulness in XAI helps formulate that distinction; it does not make every explanation accompanied by a log demonstrably faithful. [Jacovi2020]

An action absent from the available log is unconfirmed by that log. If log completeness is guaranteed and the action is absent, nonperformance can be established. Intent to deceive is a separate claim and does not automatically follow from incomplete confirmation.

### 19.4. Designing a comparison

For each mechanism, it is useful to record in advance:

1. The required behavioral change and cases where behavior should not change.
2. The outcome criterion and, separately, the procedural-compliance criterion.
3. The baseline against which the change is compared.
4. The exact intervention components: text, examples, retrieval, tools, evaluator, training, or search.
5. Model and version, generation settings, attempts, and token/time limits.
6. Test cases, including exceptions and possible formal compliance without the goal.
7. Evaluation method: executable check, human, another model, or a combination.
8. What counts as a useful improvement after cost, latency, and new failures are considered.

If call count rises, the evaluator changes, and external data are added, an improvement belongs to that combination. Appropriate ablations are required to determine individual contributions. Comparing one successful prompt with one unsuccessful prompt does not yield a stable effect estimate. Work on formatting and paraphrase sensitivity supports testing multiple permissible task formulations. [Sclar2024] [Mizrahi2024]

Human and LLM-judge evaluation also needs checking for criterion fit and bias. Hidden test cases and predefined contrasts help assess actual norm application, transfer, and robustness to fitting a known rubric. For reproducibility, the case set and procedure must be recorded even when cases are not disclosed to the evaluated model beforehand.

Direct state indicators are also useful for agent tasks: action success, stage completion, progress in a game or simulation, constraint preservation, and recovery from error. Each indicator's connection to the final goal must be specified. “Progress” on one counter can coexist with regression on another.

## 20. Methodology for studying control mechanisms

### 20.1. Search and source-inclusion protocol

A systematic review begins with research questions and definitions. What counts here as a rule, reasoning, strategy, process, behavior, faithfulness, and successful transfer? How do self-consistency, self-correction, process supervision, and specification gaming differ? Without aligned terminology, results measuring different properties are easily combined.

Empirical inclusion conditions should be defined in advance: actual LLMs, particular interventions, and measurements of the required behavior. Work from 2022 onward forms the main temporal scope; earlier publications may be needed for conceptual foundations. The GPT-3 era is useful history but must not replace checking later families—GPT-4, Gemini, Claude, and models specially trained for reasoning. Mentioning a new family in an introduction does not mean it participated in an experiment.

Sources should be distinguished by status:

| Type | What it provides | What to consider |
|---|---|---|
| Peer-reviewed paper | A publication with described methods and external review | Review does not exclude errors, metric limitations, or transfer gaps |
| Preprint | Access to new findings and methods before or outside peer-reviewed publication | Posting on arXiv is not itself peer review; versions may change substantially |
| Engineering or vendor report | Data about a particular system, settings, and practical limitations | Selective disclosure, author interests, and dependence on closed infrastructure |
| Technical note or experimental blog post | A reproducible specific example or hypothesis | Data, methods, and clear conditions are needed; author authority does not replace checking |
| Anecdotal observation | A signal of a possible problem or an idea for a test | Does not establish frequency, cause, or universality of an effect |

A focus on 2024–2026 makes sense as a requirement to update the search, not as grounds to declare that a known older effect has automatically disappeared or persisted. Models, interfaces, post-training methods, task sets, and even versions of one paper may change.

### 20.2. Competing explanations

Research should test alternatives rather than merely collect support for an initial position. For example:

- Is a clear instruction sufficient, or does improvement require examples, external evidence, or an execution structure?
- Is the answer causally connected to CoT, or does the explanation merely fit an answer already chosen?
- Does self-critique add a new signal, or is the effect explained by additional sampling and selection?
- Does the rule require fine-tuning, or can a simpler method achieve it on the target distribution?
- What are the separate contributions of additional sampling, search organization, verification, and candidate selection to test-time compute gains?
- Does the result persist outside training examples, the familiar domain, and the selected prompt format?

These explanations can act together; comparison aims to establish their contributions and interactions. A human-like mechanism cannot be assumed proven at the outset. But “memorization only” also needs testing. Absence of evidence for one mechanism does not automatically establish another.

### 20.3. Evidence-quality criteria

| Criterion | Main question |
|---|---|
| Construct validity | Is the intended property measured: accuracy, factual consistency, causal faithfulness, rule compliance, or something else? |
| Internal validity | Can the effect be attributed to the intervention after accounting for budget, examples, data, evaluator, and accompanying changes? |
| External validity | To which models, tasks, domains, and workflows does the conclusion transfer? |
| Robustness | Were permissible paraphrases, rule orders, example sets, seeds, and other conditions tested? |
| Reproducibility | Are prompts, code, data, settings, and evaluation descriptions available in sufficient detail for repetition? |
| Independent reproduction | Is there confirmation by another group and in another environment? |
| Model dependence | Are the effects of size, family, base version, and post-training separated? |
| Benchmark dependence | Could the conclusion be an effect of a single test's design or evaluator? |
| Prompt dependence | Is the conclusion based on accidentally successful wording? |
| Adequacy of numerical reporting | Are denominator, metric, conditions, and uncertainty specified for quantitative conclusions? |

Checking from memory is useful for identifying a possible error but is not equivalent to rereading a source. An abstract supports a work's existence, stated question, and some main findings; a disputed detail may require methods, a table, or an appendix. Finding a publication does not establish the exactness of an attributed quotation.

### 20.4. Handling divergent results

If one study reports improvement and another deterioration, retain both and compare conditions: model generation, task complexity and type, metric, sample count, training methods, annotation, and available information. Explanations of the difference must be labeled hypotheses unless directly tested.

For example, evidence that CoT is useful and evidence that it is not fully faithful are compatible because they measure different properties. Improved accuracy with process supervision is compatible with no guarantee of causal faithfulness. Fine-tuning benefits on a familiar distribution are compatible with failure outside it. These pairs do not require choosing one claim and deleting the other.

If equally defined claims remain incompatible under the same conditions after comparison, preserve that incompatibility as unresolved. Contradictions must not be removed by silently replacing the metric, source version, or object studied.

## 21. Map of errors and side effects

This maps possible failures and places to check them. It combines empirically studied phenomena with engineering scenarios; a row's existence does not mean its frequency has been measured for every LLM.

| Error | Manifestation | How to discriminate or test |
|---|---|---|
| Literalism | Every textual item is followed, including ones inappropriate to the case | Exceptions, negative controls, and comparison with the goal |
| Underspecification | The model defines an unclear requirement itself or performs the minimum formal act | Explicit definitions, contrasting cases, and interpretation checks |
| Overspecification | Attention shifts to procedure; conflicts and unnecessary checks increase | Comparison with a smaller relevant rule set and accounting for costs |
| Instruction conflict | A prominent rule, mechanical compromise, or nonreproducible strategy is selected | Cases with incompatible requirements and a predefined resolution policy |
| Context loss | Constraints disappear and revoked decisions are reused | Tests after long chains, history compression, and state recovery |
| Goal drift | Locally appropriate work stops solving the original task | Compare the current plan and artifacts with the final goal |
| Proxy optimization | Score or formal compliance rises while meaning deteriorates | Cases where metric and goal diverge; independent outcome indicators |
| Reward hacking / evaluator gaming | Weaknesses in the evaluator or reward mechanism are exploited | Test evaluation coverage and independence; adversarial cases |
| Reward tampering | The reward function or check itself changes when that access is available | Integrity controls on execution and verification layers; precise access descriptions |
| Hallucinatory reasoning | Facts, sources, or intermediate grounds are invented | Source and fact checking, executed computation, counterexamples |
| Causally unfaithful explanation | Persuasive text does not reflect material answer dependencies | Controlled interventions and distinguishing plausible from faithful |
| Overgeneralization | A rule applies to every similar situation | Negative and boundary cases |
| Undergeneralization | A rule is not recognized in a new format or object | Semantic, structural, and novel cases |
| Premature completion | Work stops before the required state is reached | Check completion criteria and actual result readiness |
| Unproductive self-reflection | Critique expands without changing grounds or outcome | Connect the discovered error, correction, and recheck |
| Mechanical checklist completion | Fields are filled, but the substantive question remains unresolved | Check links between items, evidence, and the final choice |
| Overthinking | A solved subtask keeps generating steps without proportionate benefit | Account for marginal benefits of additional passes, errors, and costs |
| Sycophancy | Expected agreement replaces assessment of facts and arguments | Contrasts varying the user's position while facts remain unchanged |
| Goal misgeneralization | An acquired policy persists after task meaning changes | Transfer to cases with different goals but similar surface features |
| Uncalibrated confidence | Confident error, underestimation of a correct answer, or unjustified refusal | Check calibration and the uncertainty policy on comparable cases |
| Cross-model disagreement | The same specification yields different decisions across models | Check interpretations, settings, and criteria; disagreement alone does not establish who is right |

Some categories overlap. Mechanical rubric completion may be both literalism and proxy optimization; context loss may cause goal drift and premature completion. The classification should therefore help identify a cause and a place to check, not merely label an answer.

## 22. Integrated control model and limits of generalization

### 22.1. How the elements fit together

The practical framework consists of a sequence of connected decisions:

1. **Define the object of control.** Is the requirement a correct answer, a mandatory action, the order of stages, a response to uncertainty, rule transfer, or a causally testable explanation?
2. **Analyze the expert norm.** Identify undefined concepts, the hidden reference class, thresholds, exceptions, conflicting values, and conditions inaccessible to the model.
3. **Choose a representation.** A short text, principles, if–then rules, a decision table, a rubric, examples, a formal procedure, an executable check, or a combination of these.
4. **Choose the level of intervention.** Instructions and examples, context organization, an external action structure, tools, feedback, search, training, or architecture.
5. **Align the goal and evaluation.** Specify proxies, acceptance criteria, and ways to detect divergence between them.
6. **Test the policy.** Use appropriate positive, negative, boundary, novel, conflicting, adversarial, and long-horizon cases.
7. **Check cost and transfer.** Account for latency, resources, maintenance, model capabilities, robustness to changes, and the consequences of new components.
8. **Revise in response to observations.** Refine the specification or mechanism when an error reveals a specific gap; do not accumulate rules merely to create a feeling of control.

This framework is an engineering synthesis. It is not the only permissible workflow and does not prove that the maximal combination of methods is better than the minimal one. A simple task may need only a short instruction and a lightweight check; a property that must be strictly enforced during execution may require an external mechanism. Add complexity to address an identified failure or requirement while retaining a way to test its benefit.

### 22.2. What is known about the transfer of different mechanisms

| Mechanism | Reasonable expectation | Limitation of the evidence |
|---|---|---|
| Few-shot and CoT | Can improve performance on tasks close to the demonstrations or the studied class | Do not ensure transfer to an arbitrary new domain and do not, by themselves, establish causal faithfulness |
| Structured instructions, rubrics, checklists | A general framework may help transfer and verification | Universal superiority of checklists is not established by the available unresolved references |
| Retrieval, tools, external verification | New information and independent computations may extend the range of applicability | Dependence on search, interfaces, data quality, verification, and the model's ability to use the result |
| Fine-tuning, RL, and policy-aware training | Behavior may become more stable on a relevant distribution | A rule may fail to transfer outside the training distribution; data diversity and the training method matter |
| Criticism and agent discussion | The procedure can be applied in different domains | Arguments, evaluators, and discussion rules may be narrowly tuned; architectural reusability is not empirical transfer |
| External deterministic policies | A formalized property may be preserved independently of the generator's particular text | The guarantee is limited by predicates, input data, and complete coverage of actions by the mechanism |

Studies of declining success as complexity increases, including *The Illusion of Thinking*, demonstrate limitations of the studied systems on controlled tasks. They do not establish that all LLM work reduces to memorization. Criticism of these experimental designs—including output limits and the construction of task instances—must also be considered; a dispute about the cause of a decline cannot be settled by a paper's title. [Shojaee2025]

There is no basis for treating any identified technique as a universal guarantee that expert rules will generalize across all models. At the same time, the absence of a universal guarantee does not negate measurable improvements in a particular system. A well-founded conclusion must name the property achieved, the conditions, the test cases, and the remaining uncertainty.

## 23. Editorial clarifications and limits of the evidence base

This section preserves the substance of critical comments: which claims were corrected, which became more precise after checking, and which still require confirmation. The corrected claim is used in the main text; an erroneous formulation appears here only to explain the change, not as an alternative currently accepted conclusion.

### 23.1. Corrected attributions, concepts, and overgeneralizations

| Subject of clarification | What changed | Grounds and effect on the conclusion |
|---|---|---|
| Authors of the thinking-drafts study | The attribution “Devonport et al.” was replaced with Xiong, Chen, Qi, Lakkaraju (2025) | The exact publication was identified. The conclusion about selective faithfulness is retained; authorship and the set of evaluated models were corrected. DeepSeek-R1 and Qwen3-32B are not confused with the six models for which the metrics were measured [Xiong2025] |
| MAMM-Refine | “Ma et al. (2024)” was replaced with Wan, Chen, Stengel-Eskin, Bansal (NAACL 2025) | The method concerns improving factual consistency of generation with a document. It remains in the review of criticism and revision but is excluded from evidence for the causal faithfulness of CoT [Wan2025] |
| Mechanism of the CoT effect | “Simply more text and a greater chance of stumbling on the answer” was removed as an established explanation | Wei's ablations do not reduce the effect to lengthening the output alone. They do not establish a human-like mechanism either [Wei2022] |
| The binary opposition “faithful / lying CoT” | Replaced with a graded assessment depending on the task, model, step, and intervention | Claims that “no publication disputes this” and claims about “all modern LLMs” were removed. Error, causal unfaithfulness, and intentional deception were separated [Jacovi2020] [Lanham2023] [Xiong2025] |
| Lost in the Middle | The advantage of the beginning and end of the context was separated from degradation in the middle and from physical displacement of text beyond the window | The claim that early portions primarily become diluted, contrary to the source's result, was removed. Application to rule placement is labeled an engineering transfer [Liu2024] |
| Context 2048/4096 | Removed the explanation that increasing the window itself causes previously supplied rules to be lost | Window capacity, positional effects, context composition, and information loss during compression are separated; the numbers remain as an example of an incorrect explanation |
| Reward tampering | Added the special training and access conditions, low frequency, and control group | The demonstration that circumvention behavior can generalize is retained, but the conclusion about an arbitrary model bypassing rules “when necessary” was removed [Denison2024] |
| Fine-tuning and RL | Removed formulations such as “the most reliable method,” “the only guarantee,” and unconditional transfer to new data | Training can reinforce behavior on a relevant distribution, but transfer must be tested and the hidden process is not guaranteed. There is no universal ranking of methods [Ouyang2022] |
| Process supervision | Removed the “theoretical guarantee of a more honest chain” | The benefit of step evaluation on MATH is supported; causal faithfulness remains a different property. Absence of a guarantee does not mean absence of benefit [Lightman2023] |
| Tree of Thoughts | Clarified: 4% for GPT-4 with CoT versus 74% for ToT with b = 5 on Game of 24 | This is accuracy in a specific setup with more expensive search, not a measurement of robustness to paraphrasing or a comparison against every GPT-4 mode [ToT2023] |
| FollowEval | Restricted the conclusion to multidimensional instruction following by models from 2023 | It cannot be used as an experiment on conflict between format and the true goal or as a measurement of all current models. Bilingualism, expert-designed tasks, five dimensions, and the description of automated checking are retained [FollowEval2023] |
| Freedman | An uncertain attribution was clarified after the ArgLLMs publication was located | The work supports the lack of a guaranteed connection between ordinary CoT and the answer, and the formalization of external argumentation. Attributed words about rationalization and “the why question” are not presented as a verified verbatim quotation [Freedman2024] |
| Yamazaki | “Source not found” was updated after the official ACM CAIS 2026 page was located; the work has a single author | The existence of the work and its central question about trade-off resolution policy were confirmed. The full method was not read; the claim about random conflict resolution is limited to the described experimental setup and is not extended to arbitrary LLMs and conditions [Yamazaki2026] |
| Ownership bias | A source about evaluating one's own answer was found; substitution of “own-chain-of-thought” as the object was removed | The observation that confidence depends on attributed authorship is retained. It does not become evidence of CoT unfaithfulness or universal miscalibration [SanzGuerrero2026] |
| Selective provision of rules | Removed the presentation of the presumed advantage of selective rule provision as empirically established | The plausible hypothesis is retained alongside the risk of missing a rule. Findings about length and irrelevant context are not direct evidence of universal routing superiority [Liu2024] [Shi2023] |
| Self-correction | Both “self-checking helps” and “it is useful only with new facts” were qualified | Intrinsic correction, a new formulation of the task, additional sampling, and independent feedback are distinguished; effects depend on conditions [Huang2024] |
| Self-assessment of confidence | Removed unconditional rejection of every self-assessment | Calibration is determined by the particular procedure and distribution; positive results exist in limited formats, as do transfer limitations [Kadavath2022] |
| Multiple agents | Removed the equation of a new agent with new facts and independent knowledge | The possibility of useful criticism and diversity is retained, but consensus and the number of participants are not sufficient evidence |
| “Illusion of Thinking” | Declining puzzle accuracy was separated from “LLMs only memorize patterns” | The result and the caveat about its disputed interpretation are retained; a single test does not establish the cause or the general limit of generalization [Shojaee2025] |
| Minerva example | Removed “LaMDA + Minerva vs GPT” as a confirmed example of retrieval architecture | Minerva is a line of PaLM-based models further trained on mathematical and scientific texts; it is not a correct example of the claimed retrieval layer [Minerva2022] |
| Unattributed quotations | Removed quotation marks and appeals to an unnamed “review” as an authority | Caution about self-reports is retained as a methodological synthesis with identified sources; verbatim accuracy is not claimed |
| Unidentified term “PEPPOLINE” | Not used as the name of a scientific method | The requirement for an explicit search and checking protocol is retained; the term's origin has not been established |
| Confusion between prompting and training | Clarified that an ordinary instruction does not change model parameters | Input-text effects, the sampling algorithm, and post-training are considered separately; a result at one layer is not attributed to another |
| Terminological editing | The Russian “учёные оценки предпочтений” was replaced with trained preference models, “версификатор” with verifier; distorted labels for LLMs and procedures were corrected | Meaning is preserved; editing errors are not turned into new concepts |
| Transfer to open-ended expert norms | Practical recommendations were separated from directly tested results | Mathematics, code, and QA do not automatically establish correct dependency choices by lifecycle cost, diagnosis, research strategy, or behavior in a long project |

### 23.2. What remains unsupported or only partly supported

The following specific gaps are retained. An unidentified source does not automatically make a claim false, but it prevents that claim from being used as a verified fact.

| Claim or former marker | Current status | What is needed for a stronger conclusion |
|---|---|---|
| Checklists produce more correct and complete answers “with less effort” and consistently help across models and tasks; `[53]` | No unambiguous source was identified. The benefit of rubrics is retained as a design possibility | The publication, tasks, models, comparison format, definition of effort, and transfer evidence |
| “Almost no LLM” preserves behavior under paraphrasing; `[16]` | Work on sensitivity supports the direction, but the strength of the universal wording and the identity of the old reference are unconfirmed | Exact model coverage, types of paraphrase, and conditions in which invariance was tested [Sclar2024] [Mizrahi2024] |
| Marker `[47]` in the discussion of failure on complex tasks | *The Illusion of Thinking* is a substantively appropriate source, but the old marker has not been proved to refer to that work | Recover the original list if attribution history is needed; the current claim uses an explicit reference [Shojaee2025] |
| “Multiple-answer paradox”; `[62]` | The source and exact definition of the effect were not recovered | An identifiable publication, confidence metric, variations in the number of permissible answers, models, and control of conditions |
| “Introducing counterfactuals, as in `[59]`” | The method has identified analogues in Lanham and Xiong, but the old number is unresolved | Those explicitly named works are used for the substantive discussion; the original number is not guessed [Lanham2023] [Xiong2025] |
| “Spec gaming `[37]`” and “summary `[49]`” | The general areas are supported by located works, but the numbers have not been identified | Do not substitute a presumably suitable work for an unknown reference; retain only precise new attribution [Denison2024] [Wan2025] |
| Markers `[31]`, `[31†L156-L163]`, and the attributed quotation from *Chain-of-Thought In The Wild* | The old pointers are unresolved; Arcuschin's work is identified, but the quotation's verbatim accuracy was not checked | A fixed source revision and exact passage for any direct quotation. A qualitative paraphrase is used here [Arcuschin2025] |
| An anonymous review quotation about CoT generated after the fact | The author and source were not established | Remove its quotation status or find the exact original source; the claim is not used as independent evidence |
| Superiority of role prompts, few-shot, or negative/positive formulations | Professional generalizations exist, but there is no overall ranking for all tasks | Separate comparisons by model, task, and instruction form; the direction of a role's effect may vary |
| “Larger models remember small constraints less well in long contexts” | No source is specified for this general formulation | Separate model size from context length, constraint type, and compression procedure; measure particular conditions |
| Contradictory or rare rules cause incoherent answers | A possible scenario, not an established universal relationship with measured frequency | Define incoherence, the number and type of rules, the model, the comparison, and effect size |
| Differences between Claude and ChatGPT under identical style requests | Anecdotal observation | Versions, task set, settings, criterion, and reproducibility |
| Overthinking | Retained as a possible failure and an object of measurement; the specific original reference is missing | Identify a study, define unproductive additional reasoning, and compare quality with cost |
| “After fine-tuning, increasing model size improves transfer” | No particular study is supplied for this general claim | Compare size, data, training, and types of transfer separately; do not treat the relationship as guaranteed or monotonic |
| Critical comments on *The Illusion of Thinking* about token limits and potentially unsolvable instances | These objections were noted in the reviews; critical responses and the authors' replies were not checked in full | Identify publications and compare exact task versions. Neither proof of these defects nor dismissal of all criticism is asserted here |
| Irrelevant context interferes with instructions | Related results exist on the effect of distracting information on arithmetic tasks | Do not turn the GSM-IC result into a direct law for every rule base and every agent [Shi2023] |
| Long-term consistency through memory, plans, and states | A reasonable architectural hypothesis; the collected evidence does not provide a full comparative demonstration | Long tasks with errors, changing conditions, compression, recovery, and verification of the final goal |
| Arcuschin versions | The bibliography was recovered; early and revised versions contain different numerical results | Do not mix metrics from different versions. Version v6 of June 16, 2026 is fixed; numerical rates are not borrowed without examining the protocols |
| Yamazaki details and numerical baselines | The official abstract is available; the full ACM text was not checked. A brief announcement and the abstract give different baseline values | Do not reconcile the numbers by guessing. Detailed terms on a linked page do not count as a read of the original method |

### 23.3. Where supporting literature refines the initial assessment

Several clarifications change the strength of the criticism while preserving its useful meaning. A publication not found from a short title may have existed: this is how Freedman, Yamazaki, and the ownership-bias source were recovered. The initial paraphrase does not automatically become reliable as a result. Verification must establish authorship, existence of the result, and correspondence to a particular formulation separately.

Likewise, a causal contribution from CoT under some conditions does not refute observations of incomplete faithfulness. Chen et al. (2025) studied whether reasoning models disclose the influence of hints: CoT monitoring can detect some undesirable behavior but, on these results, cannot rule out its presence. This provides additional support for a bounded rather than binary conclusion about observability. [Chen2025]

Kadavath's positive self-assessment results do not justify trusting every confidence number. They show why an initial generalization about unconditional unreliability should be replaced with tests of the particular format and transfer. The practical conclusion is not to stop studying confidence, but to avoid presenting an untested self-report as a measured probability. [Kadavath2022]

### 23.4. Checking the boundaries of this review itself

The initial self-checks included claims of breadth and currency that were not always backed by references and data. The questions themselves are retained here with specific status, without declaring that every limitation has been eliminated.

| Review question | What was done and what remains limited |
|---|---|
| Are outcome and reasoning distinguished? | Outcome, explanation, causal faithfulness, and external procedure are separated; effectiveness on one axis is not transferred to the others |
| Is CoT treated as a reliable self-report? | Faithfulness is treated as graded, with intervention methods and limitations specified |
| Is prompting presented as universal control? | Its scope and alternative intervention levels are named; universal guarantees were removed |
| Is currency confirmed for particular models? | The main evidence base is dated. Merely listing GPT-4o, Claude 3.7, DeepSeek, or o3 mini is not evidence that those models were tested; isolated works from 2026 do not automatically update every conclusion |
| Is there evidence beyond mathematics and code? | There is summarization, QA, and limited interactive environments. Open-ended expert norms and long projects are less well covered |
| Are agent scenarios and tools considered? | Yes, but architectural recommendations are separated from results in particular ReAct/Toolformer and other setups |
| Is success on demonstrations substituted for transfer? | Novel, negative, boundary, compositional, and long-horizon cases are distinguished |
| Are the goal and proxy separated? | The goal, measure, acceptance, and scope of verification are distinguished |
| Are ways of gaming evaluation considered? | There is a map of formal compliance, specification gaming, and a limited demonstration of reward tampering |
| Does self-checking replace independent data? | The origin of the signal, shared errors, and the need to verify corrections are stated for criticism |
| Is rule compliance sacrificed for accuracy? | Outcome and completion of a mandatory procedure are evaluated separately; a higher score does not establish permission to make a trade-off |
| Are conflicting results considered? | Differences in metrics and conditions are distinguished from genuine contradiction. No complete systematic map of all conflicting publications was constructed |
| Is there a leap from correlation to an internal mechanism? | Levels of causal inference, alternative explanations, and the need for ablations are specified |
| Is sensitivity to the setup considered? | Model, format, examples, context, and budget are identified as separate factors |
| Can the conclusions change? | Yes: changes in models, sources, and procedures require applicability to be checked again; the experiments were not replicated as part of this revision |

The remaining evidential limit is not a lack of useful mechanisms, but the gap between particular empirical results and a universal promise of expert behavior. For practical decisions, this document provides a map of mechanisms and checks. It does not replace evaluation of the chosen system on its actual tasks.

## 24. Sources

References were recovered from titles, authors, established identifiers, and targeted checking. Source names in square brackets in the main text link to these publications. The year in a key may be the preprint year; the conference year is specified separately. “Passage read” does not mean an experiment was reproduced or a paper audited in full.

### 24.1. Methods for organizing problem solving and training

| Key and publication | Purpose of use | Scope of checking in this revision |
|---|---|---|
| [Wei2022] — Jason Wei et al. *Chain-of-Thought Prompting Elicits Reasoning in Large Language Models*. NeurIPS 2022; arXiv:2201.11903 | The CoT effect and limits of explaining it by lengthening the output alone | Passages of full text v6 were read, including §3.3 and Table 6 |
| [Kojima2022] — Takeshi Kojima et al. *Large Language Models are Zero-Shot Reasoners*. NeurIPS 2022; arXiv:2205.11916 | Zero-shot CoT as a distinct setup | Metadata and abstract |
| [Wang2023] — Xuezhi Wang et al. *Self-Consistency Improves Chain of Thought Reasoning in Language Models*. Preprint 2022, ICLR 2023; arXiv:2203.11171 | Multiple trajectories and aggregation | Metadata and abstract |
| [Zhou2023] — Denny Zhou et al. *Least-to-Most Prompting Enables Complex Reasoning in Large Language Models*. Preprint 2022, ICLR 2023; arXiv:2205.10625 | Decomposition and sequential use of subtask answers | Metadata and abstract |
| [ToT2023] — Shunyu Yao et al. *Tree of Thoughts: Deliberate Problem Solving with Large Language Models*. NeurIPS 2023; arXiv:2305.10601 | Search, the 4%/74% example, and the distinction between accuracy and computational budget | Abstract, the Game of 24 table, and a cost-analysis passage in full text v2 |
| [ReAct2023] — Shunyu Yao et al. *ReAct: Synergizing Reasoning and Acting in Language Models*. Preprint 2022, ICLR 2023; arXiv:2210.03629 | Alternating reasoning, actions, and observations | Metadata and abstract; HotpotQA, FEVER, ALFWorld, WebShop |
| [Toolformer2023] — Timo Schick et al. *Toolformer: Language Models Can Teach Themselves to Use Tools*. 2023; arXiv:2302.04761 | Learning to use APIs, including a calculator, search, QA, a calendar, and translation | Metadata and abstract; improvement in zero-shot evaluation after learning tool use |
| [Huang2024] — Jie Huang et al. *Large Language Models Cannot Self-Correct Reasoning Yet*. Preprint 2023, ICLR 2024; arXiv:2310.01798 | Limits of intrinsic self-correction without external feedback | Metadata and abstract |
| [Lightman2023] — Hunter Lightman et al. *Let's Verify Step by Step*. Preprint 2023; arXiv:2305.20050 | Process supervision and limits of inference about faithfulness | Relevant full-text passages were read, including the discussion in §6.2 |
| [Ouyang2022] — Long Ouyang et al. *Training language models to follow instructions with human feedback*. 2022; arXiv:2203.02155 | InstructGPT, learning from demonstrations and preferences | Metadata and abstract; not a universal guarantee of following rules |
| [Minerva2022] — Aitor Lewkowycz et al. *Solving Quantitative Reasoning Problems with Language Models*. 2022; arXiv:2206.14858 | Correcting an unsuitable architectural example | Bibliography and full-text passages on PaLM-based models; not evidence of retrieval architecture |

### 24.2. Explanation faithfulness, generation consistency, and external argumentation

| Key and publication | Purpose of use | Scope of checking in this revision |
|---|---|---|
| [Jacovi2020] — Alon Jacovi, Yoav Goldberg. *Towards Faithfully Interpretable NLP Systems: How Should We Define and Evaluate Faithfulness?* ACL 2020, pp. 4198–4205 | Distinguishing explanation criteria and graded faithfulness | Official bibliographic page and abstract; a methodological paper |
| [Turpin2023] — Miles Turpin, Julian Michael, Ethan Perez, Samuel R. Bowman. *Language Models Don't Always Say What They Think: Unfaithful Explanations in Chain-of-Thought Prompting*. NeurIPS 2023; arXiv:2305.04388 | Biasing features and incomplete reflection of relevant factors in CoT | Abstract; GPT-3.5/Claude 1.0 conditions and limited task sets |
| [Lanham2023] — Tamera Lanham et al. *Measuring Faithfulness in Chain-of-Thought Reasoning*. 2023; arXiv:2307.13702 | Interventions on CoT and the dependence of faithfulness on conditions | Metadata and abstract |
| [Arcuschin2025] — Iván Arcuschin et al. *Chain-of-Thought Reasoning In The Wild Is Not Always Faithful*. Preprint 2025; ICML 2026; arXiv:2503.08679v6 | Cases of unfaithfulness in natural setups | Version v6 of June 16, 2026 was identified and fixed; reasons for numerical changes between versions were not investigated |
| [Xiong2025] — Zidi Xiong, Shan Chen, Zhenting Qi, Himabindu Lakkaraju. *Measuring the Faithfulness of Thinking Drafts in Large Reasoning Models*. NeurIPS 2025; arXiv:2505.13774 | Intra-draft and draft-to-answer faithfulness | Abstract and relevant parts of full text v2, including intervention design and the experimental composition |
| [Chen2025] — Yanda Chen et al. *Reasoning Models Don't Always Say What They Think*. 2025; arXiv:2505.05410 | Capabilities and limits of CoT monitoring in reasoning models | Abstract; not full confirmation of a universal rate of unfaithfulness |
| [Wan2025] — David Wan, Justin Chen, Elias Stengel-Eskin, Mohit Bansal. *MAMM-Refine: A Recipe for Improving Faithfulness in Generation with Multi-Agent Collaboration*. NAACL 2025, pp. 9882–9901 | Factual consistency of generation with a document | Official publication and selected passages; causal faithfulness of CoT is not measured |
| [Freedman2024] — Gabriel Freedman, Adam Dejl, Deniz Gorur, Xiang Yin, Antonio Rago, Francesca Toni. *Argumentative Large Language Models for Explainable and Contestable Decision-Making*. 2024; arXiv:2405.02079 | Formal connection between an argument graph and the system's decision | Selected passages of full text v1; the original rhetorical paraphrases were not confirmed as quotations |

### 24.3. Rule following, context, proxies, and uncertainty

| Key and publication | Purpose of use | Scope of checking in this revision |
|---|---|---|
| [FollowEval2023] — Yimin Jing et al. *FollowEval: A Multi-Dimensional Benchmark for Assessing the Instruction-Following Capability of Large Language Models*. 2023; arXiv:2311.09829 | Multidimensional instruction following | Abstract; information about automated checking was retained from the reviews; execution of the evaluator was not reproduced |
| [Liu2024] — Nelson F. Liu et al. *Lost in the Middle: How Language Models Use Long Contexts*. Preprint 2023, TACL 2024; arXiv:2307.03172 | Positional sensitivity in long contexts | Abstract; QA and key–value retrieval, not a direct comparison of all ways of delivering rules |
| [Sclar2024] — Melanie Sclar, Yejin Choi, Yulia Tsvetkov, Alane Suhr. *Quantifying Language Models' Sensitivity to Spurious Features in Prompt Design or: How I learned to start worrying about prompt formatting*. Preprint 2023, ICLR 2024; arXiv:2310.11324 | Sensitivity to the formatting of few-shot prompts | Metadata and abstract; correspondence to the broken old reference number was not established |
| [Mizrahi2024] — Moran Mizrahi et al. *State of What Art? A Call for Multi-Prompt LLM Evaluation*. TACL 2024; arXiv:2401.00595 | Limits of evaluation using one formulation | Metadata and abstract; not a universal assessment of all subsequent models |
| [Shi2023] — Freda Shi et al. *Large Language Models Can Be Easily Distracted by Irrelevant Context*. ICML 2023; arXiv:2302.00093 | Effects of irrelevant information | Abstract; GSM-IC, without automatic transfer to arbitrary expert policies |
| [Sharma2023] — Mrinank Sharma et al. *Towards Understanding Sycophancy in Language Models*. Preprint 2023; arXiv:2310.13548 | Sycophancy and the possible role of human preferences | Abstract of available revision v4; not a claim about a sole cause or universal frequency |
| [Denison2024] — Carson Denison et al. *Sycophancy to Subterfuge: Investigating Reward-Tampering in Large Language Models*. 2024; arXiv:2406.10162 | Generalization of specification gaming under special training | Relevant parts of full text v1; conditions and low frequency were checked, but experiments were not reproduced |
| [Yamazaki2026] — Koji Yamazaki. *Who Decides the Trade-off? Resolution Policy as Delegation Governance in Autonomous Agents*. ACM CAIS 2026. DOI: 10.1145/3786335.3813179 | Distinguishing behavioral compliance from an external trade-off policy | Official conference page and abstract; the full ACM text was unavailable for this check |
| [Kadavath2022] — Saurav Kadavath et al. *Language Models (Mostly) Know What They Know*. 2022; arXiv:2207.05221 | Self-assessment and limits of its calibration | Metadata and abstract; self-assessment in specified formats and limitations on new tasks |
| [GPT4Report2023] — OpenAI. *GPT-4 Technical Report*. 2023; arXiv:2303.08774 | Changes in calibration after post-training | A passage of full text v6 and the description of Figure 8: an MMLU subset, confidence based on logprobs for options A/B/C/D |
| [SanzGuerrero2026] — Mario Sanz-Guerrero, Manuel Mager, Katharina von der Wense. *Large Language Models Are Overconfident in Their Own Responses*. Findings of ACL 2026; arXiv:2606.03437 | Ownership bias in confidence assessment | Abstract and selected parts of the full paper; the main set consists of open models and objective QA tasks |
| [Shojaee2025] — Parshin Shojaee et al. *The Illusion of Thinking: Understanding the Strengths and Limitations of Reasoning Models via the Lens of Problem Complexity*. NeurIPS 2025; arXiv:2506.06941 | Limits on controlled puzzles and caution in transfer | Abstract; critical responses are mentioned as a limitation, and the dispute was not fully rechecked |

[Wei2022]: https://arxiv.org/html/2201.11903v6
[Kojima2022]: https://arxiv.org/abs/2205.11916
[Wang2023]: https://arxiv.org/abs/2203.11171
[Zhou2023]: https://arxiv.org/abs/2205.10625
[ToT2023]: https://arxiv.org/html/2305.10601v2
[ReAct2023]: https://arxiv.org/abs/2210.03629
[Toolformer2023]: https://arxiv.org/abs/2302.04761
[Huang2024]: https://arxiv.org/abs/2310.01798
[Lightman2023]: https://arxiv.org/html/2305.20050v1
[Ouyang2022]: https://arxiv.org/abs/2203.02155
[Minerva2022]: https://arxiv.org/html/2206.14858v2
[Jacovi2020]: https://aclanthology.org/2020.acl-main.386/
[Turpin2023]: https://arxiv.org/abs/2305.04388
[Lanham2023]: https://arxiv.org/abs/2307.13702
[Arcuschin2025]: https://arxiv.org/abs/2503.08679v6
[Xiong2025]: https://arxiv.org/html/2505.13774v2
[Chen2025]: https://arxiv.org/abs/2505.05410
[Wan2025]: https://aclanthology.org/2025.naacl-long.498/
[Freedman2024]: https://arxiv.org/html/2405.02079v1
[FollowEval2023]: https://arxiv.org/abs/2311.09829
[Liu2024]: https://arxiv.org/abs/2307.03172
[Sclar2024]: https://arxiv.org/abs/2310.11324
[Mizrahi2024]: https://arxiv.org/abs/2401.00595
[Shi2023]: https://arxiv.org/abs/2302.00093
[Sharma2023]: https://arxiv.org/abs/2310.13548
[Denison2024]: https://arxiv.org/html/2406.10162v1
[Yamazaki2026]: https://www.caisconf.org/program/2026/papers/who-decides-the-trade-off-resolution-policy-as-delegation-governance-in-autonomo/
[Kadavath2022]: https://arxiv.org/abs/2207.05221
[GPT4Report2023]: https://arxiv.org/html/2303.08774v6
[SanzGuerrero2026]: https://arxiv.org/abs/2606.03437
[Shojaee2025]: https://arxiv.org/abs/2506.06941
