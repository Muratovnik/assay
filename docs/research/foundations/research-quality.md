# Research Quality and the Work of a Strong Researcher

**English** · [Русский](../../ru/research/foundations/research-quality.md)

> A research synthesis, not task-execution instructions or normative Assay policy. Source status and verification limits are retained from the original document. [About the corpus and translations](../README.md).

## Purpose and status of this document

This document addresses the question: what distinguishes high-quality research and a strong researcher in observable, testable terms—from framing a problem and finding data to assessing uncertainty, making a decision, and reporting results.

Its basis is a narrative synthesis of methodological concepts, professional recommendations, and critical comments on their application. The definitions, behavioral model, lifecycle, error catalog, heuristics, evidence matrix, and list of tensions form a working set of reference points. They must not be treated as an empirically validated quality scale or a proven universal research algorithm. The document distinguishes propositions checked against a primary source, attributions from methodological literature that have not undergone that check, and the author's proposals.

The preceding methodological review, dated October 5, 2026, relied on reading the texts and on reviewers' recollection. During preparation of this document, selected definitions, attributions, and statistical statements were additionally checked against available primary sources and official guidance. Sections 21–22 describe the scope of that check and its remaining limitations; it does not amount to external verification of every proposition.

The general framework is oriented primarily toward empirical disciplines with a quantitative tradition. Separate conditions of application are retained for technical, historical, qualitative, and exploratory research. Universal principles help examine an argument, but do not replace subject knowledge and specialized methods.

## 1. What research quality means

### 1.1. Truth, justification, and usefulness

High-quality research answers the question posed, uses suitable data and methods, produces a traceable inference, and calibrates confidence to the strength of its grounds. Its result may be a justified acknowledgment of uncertainty.

Three properties need to be distinguished:

- **The truth of a claim:** whether it corresponds to reality.
- **The quality of its justification:** how far the data, method, and reasoning warrant this particular conclusion and exclude material alternatives.
- **Practical usefulness:** whether the conclusion helps make a decision under specified conditions, given the available actions and consequences of error.

A correct answer can be obtained by chance or through a faulty method. For example, an incorrect analysis may accidentally detect a real association; that does not make the procedure reliable. Conversely, a careful experiment may leave a question unresolved because the effect is small, measurements are noisy, or the data are limited. A lack of certainty does not itself demonstrate poor work.

### 1.2. Observable properties of a high-quality result

| Property | What needs to be assessed | What must not be treated as a sufficient check |
|---|---|---|
| Fit to the question | Whether the conclusion answers the stated question; whether the unit of analysis, context, and scope of the claim match what was studied | Persuasive reasoning about an adjacent problem |
| Construct validity | Whether the measures and procedures represent the concept being studied; whether the move from construct to metric is justified | The convenience of an available metric or its familiar name |
| Internal validity | For a causal conclusion: how well the design and analysis exclude material alternative explanations | The mere presence of correlation, temporal sequence, or a plausible mechanism |
| External validity and generalizability | The other populations, conditions, periods, and systems to which the result may be transferred | Automatically extending a laboratory or local result to any real-world conditions |
| Statistical validity | Whether analysis and interpretation fit the data, design, assumptions, and nature of the question | A single statistical-significance threshold |
| Reliability of data and methods | The quality and precision of measurements, sample size and composition, data completeness, and potential distortions | A large volume of data without checking its provenance and suitability |
| Estimation precision | How narrow the range of plausible values is and whether precision is sufficient for the stated conclusion | A point estimate without uncertainty |
| Robustness | How the substantive conclusion changes under reasonable alternative assumptions, measurements, and analytical decisions | One convenient specification |
| Reproducibility and replicability | Whether calculations can be checked and, where possible, consistent results obtained with new data | Repeating the same error with the same code or formally demanding that a unique event be repeated |
| Calibration of confidence | Whether expressed confidence matches the quality and completeness of its grounds | Categorical language, confident presentation, or the author's reputation |
| Explanatory and predictive power | What the result explains or predicts, which alternatives it discriminates between, and where it stops working | A story equally compatible with every possible outcome |
| Testability | Which observations, recalculations, or alternative methods could expose an error | A claim insulated against every possible refutation |
| Transparency and traceability | Whether the chain from sources and data, through assumptions and analysis, to the conclusion is visible | A bibliography unconnected to specific claims |

Fit between the conclusion and the question is identified separately here. Labeling this entire criterion *face validity* without further definition is incorrect: it conflates the relevance of an answer with the assessment of a measurement instrument.

Quality is a profile of properties. High precision does not eliminate systematic error; good internal validity does not guarantee transferability; a transparent calculation may reproduce a poorly chosen model. Conflicting results also require analysis: they may reflect a methodological defect or genuine heterogeneity in the phenomenon.

## 2. Framing the question and choosing a research design

### 2.1. Task boundaries

Work starts by clarifying the problem: what needs to be learned, for whom, under what conditions, and why the question matters. The researcher specifies the unit of analysis, population or system under study, period, outcomes of interest, inclusion and exclusion criteria, and topic boundaries. An overly broad question has to be decomposed. For example, “Is technology X safe?” requires specifying the kind of harm, conditions of use, affected groups, and comparison alternative.

The usefulness of data depends on its relationship to the question. A collection of readily available but secondary facts does not compensate for missing information about the central uncertainty.

The initial problem should be separated from the proposed explanation of its mechanism: the wording of the question must not presuppose that explanation is true.

### 2.2. Types of question

| Type of question | What needs to be established | Methodological implication |
|---|---|---|
| Descriptive | What exists, how often it occurs, how it is distributed or organized | Suitable observations, measurements, documents, or surveys are needed; when estimating a population, how the data represent it matters |
| Causal | What will change as a result of an intervention and which factors explain the change | A causal-inference design and justification of its assumptions are needed |
| Predictive | What will happen under specified conditions | Evaluation must match the intended prediction context and account for uncertainty |
| Comparative | How objects, states, or alternatives differ | The properties, conditions, and basis of comparability need to be specified in advance |
| Normative | What should count as good, acceptable, or preferable | Criteria and value assumptions must be disclosed; empirical data alone do not automatically supply them |

For causal questions, a randomized controlled experiment is often preferable when feasible and appropriate to the task. Where it is not possible, natural and quasi-experiments and causal-inference methods for observational data are considered. Knowledge of a mechanism strengthens an explanation but does not by itself establish causality. Restricting causal research to mechanisms or natural experiments omits important design options.

### 2.3. PICO and operationalization

For questions about intervention effects, the PICO framework is useful:

- **Population:** the population or group being studied.
- **Intervention:** the intervention; for questions about exposures, *exposure* is specified separately.
- **Comparator:** the alternative or comparison condition, where applicable.
- **Outcomes:** the outcomes of interest.

PICO is associated with the evidence-based medicine tradition and Richardson et al. (1995); it is used, among other places, in Cochrane and GRADE. Its origin should not be attributed to GRADE. Its area of use does not make it a mandatory format for a historical investigation, interview, or software-system analysis. The extent of the attribution check is stated in the bibliography section.

Every key concept must be connected to observable indicators. For example, a study of satisfaction needs to justify why the chosen questions or indicators represent satisfaction itself. An available measure may be a surrogate for a different property. This is the risk of substituting a metric for a construct, not merely a poor choice of name.

### 2.4. Hypotheses before and after seeing the data

The researcher formulates the main hypothesis, competing explanations, and threats to validity. A study of a drug's effect, for example, needs to consider placebo, co-interventions, and other explanations of the observed change.

The problem with HARKing is presenting a hypothesis formulated after inspecting results as if it had been stated in advance. The emergence of new hypotheses during analysis is legitimate and necessary for exploratory work. Confirmatory analysis, alternatives specified in advance, and hypotheses arising from exploration of the data must therefore be distinguished. A preliminary literature review may guide the question, but must not become a way of tailoring the task to a desired answer.

## 3. Searching for evidence

### 3.1. Coverage and diversity

The aim of the search is sufficient coverage of relevant grounds and alternative explanations. Publication count is meaningful only together with informational value, quality, and independence.

A strategy may include:

- keywords, synonyms, subject terms, and examination of the field's taxonomy;
- general scientific databases, such as Web of Science, PubMed, and Scopus, and specialized sources;
- official technical documentation, code repositories, report archives, and preprint servers;
- examining the reference lists of identified works—*backward citation chasing*;
- finding subsequent works that cite the original—*forward citation chasing*;
- gray literature: dissertations, organizational and company reports, unpublished and negative results;
- reasoned language, time, and other restrictions, with an account of what they may exclude.

Search *recall* and *precision* are in tension: an overly narrow query misses important information, while an overly broad one adds noise. No single set of databases or filters suits every topic.

### 3.2. Checking the search strategy itself

The researcher checks whether the picture found was created by the search method. Restricting a search to English-language publications or to work published before 2010, for example, may exclude relevant information. If English-language articles support a conclusion while local reports contradict it, that is a reason to investigate the discrepancy and reconsider coverage.

The search needs to include data that could refute the current account, as well as results inconvenient for the dominant theory. The absence of negative publications may reflect publication bias or access and language limitations. Gray literature is not reliable merely because it exists: its methods and provenance must be evaluated on the same basis as other sources.

A search cannot be considered complete merely because a predetermined number of articles has been found. The stopping rationale concerns the extent to which new data could change a material conclusion or decision; Section 14 examines this in more detail.

## 4. Evaluating sources and matching evidence to claims

### 4.1. The role of a source

“What does this source support here?” is more useful than a universal ranking such as “an article outranks a report, and a report outranks a blog.” Even a reliable source may not support a particular proposition.

| Claim or task | Most direct forms of evidence | Material limitations |
|---|---|---|
| Design intent, a contract, or a system's operating rule | Specification, official documentation | The stated contract may differ from implementation and a particular execution |
| Implementation of an algorithm | Source code, tests, and examination of the relevant version | Code requires an understanding of its context, configuration, and execution conditions |
| Actual system behavior | Logs, observations, reproducible experiments, and tests | An observation concerns a particular version, environment, and scenario |
| Effect of an intervention | Randomized experiment; an appropriate natural or quasi-experiment; justified analysis of observational data | The inference depends on the design, its execution, assumptions, and measurement quality |
| Prevalence and distribution of characteristics | Observational data, representative surveys, and measurements | Selection, missingness, and measurement distortions may limit the conclusion |
| Detailed understanding of one case | Case studies, documents, observations, interviews | Depth of case description does not provide broad generalizability |
| The overall picture across multiple works | A high-quality systematic review, suitable meta-analysis, or transparent narrative synthesis | Inherited errors, heterogeneity, publication bias, and double-counting data remain possible |

A technical investigation should move toward evidence directly relevant to the fact being checked. This refines the principle of using “low-level” sources: code does not replace a specification when the question concerns a contract, and the existence of code does not replace observation of a particular execution. Someone else's description of an algorithm is usually insufficient when its implementation and a check are available.

### 4.2. What to check in the methodology

Assess sample composition and size, design, measurements, how data were obtained, statistical methods, assumptions, transparency of analysis, and disclosure of limitations. Journal prestige, citation count, and author confidence are not independent guarantees.

Randomization helps justify a causal inference but does not automatically remove every risk. A laboratory study can have high internal validity while being only narrowly applicable elsewhere. Observational data may better represent the environment of interest, but external validity does not follow from the name of the design: selection and measurement still require scrutiny. Questionnaires and surveys also require attention to subjective responses and selection bias.

A small sample and a large p-value may mean the data cannot provide a precise answer; they are not universal evidence of poor research. Likewise, a small p-value does not establish an effect's practical importance. Interpretation depends on the task, estimated effect, uncertainty, and design quality.

### 4.3. Primary sources, synthesis, and hierarchies

To establish exactly what was done in a particular study, consult the primary publication, methods, data, and available supplementary material. For the overall picture, a good systematic review may be more useful than an individual primary study. A secondary source does not remove the need to return to the primary one when methodological details determine the conclusion or the retelling is questionable.

Evidence hierarchies can help assess design for causal questions about intervention effects. They are insufficient for evaluating every study and the body of evidence; they should not be transferred to other question types without adaptation. GRADE and Oxford CEBM are different tools for evaluating and organizing evidence and cannot be reduced to universal voting by publications. The specific versions and limits of the tool being applied need to be stated.

Ioannidis (2005), cited here, examines how power, the prior proportion of true hypotheses, and biases affect the probability that published positive findings are true. Under some combinations of these assumptions, the model allows most positive findings to be false. This is a conditional model result, not a census of all publications' quality. The phrase attributed to the author about results failing to meet “good standards of evidence” must not be used as a verbatim quotation. The bibliographic record and checked source are given in Section 22.

## 5. Causal thinking and competing explanations

### 5.1. From association to cause

A correlation between A and B does not by itself show that A causes B. Justifying causality traditionally involves temporal precedence, an association between variables, and the ability to exclude plausible alternatives. This framework helps formulate checks, but listing the three conditions does not replace a research design and analysis of its assumptions.

Threats to consider include common causes—confounders—reverse causality, selection of observations, and other systematic distortions. Even an established sequence in which A preceded B does not exclude a common factor or more complex feedback. An unrepresentative sample limits transferability; selection's effect on causal inference also requires separate examination.

Suitable tools include control groups, randomization, natural and quasi-experiments, *matching*, instrumental variables, and other causal-inference methods. Each requires its own assumptions. A persuasive account of a mechanism and participants' own explanations may be useful evidence, but do not replace checking alternatives.

### 5.2. A discriminating observation

A strong researcher does not stop at listing possible explanations. They determine what results each explanation predicts and choose an observation, experiment, or analysis for which those expectations diverge.

If the same fact is equally expected under every explanation being considered, it has little diagnostic value for choosing between them. The usefulness of the next step concerns its ability to change the alternatives' relative plausibility, not the complexity of the equipment or the amount of data collected.

For example, given two hypotheses about a mechanism, look for conditions in which they predict different results. An experiment need not conclusively leave only one hypothesis: informative evidence can change the degree of support for several explanations while preserving uncertainty.

### 5.3. Approaches to hypothesis testing

| Approach | Useful research stance | Boundary of application |
|---|---|---|
| Falsification, associated with Karl Popper | Seek tests capable of refuting a hypothesis | Account for measurement and test assumptions; conveniently declaring every outcome “confirmation” makes the test empty |
| *Severe testing*, Deborah Mayo | Subject an explanation to a test capable of detecting a material error | This is a particular methodological approach; naming it does not establish the severity of the test performed |
| Bayesian updating | Assess how data change the relative support for hypotheses | The result depends on the model, assumptions, and prior probabilities |
| Analysis of Competing Hypotheses—ACH, Richards J. Heuer | Compare alternatives with evidence, emphasizing inconsistencies and diagnosticity | Simply counting supporting or contradicting items does not replace assessing their strength and dependence |
| Triangulation | Compare results from approaches with different possible sources of error | Converging conclusions strengthen the argument insofar as the checks are independent and concern the same question |

These approaches differ in their foundations and procedures. They share a useful stance: the next step should reduce material uncertainty and test the explanation's weak points. Choosing by expected information gain remains a heuristic until the alternatives, probabilities, possible results, and costs are specified.

Explanations that fit the researcher's expectations particularly well require attention to counterevidence. This is the substantive meaning of testing “convenient stories” more severely.

## 6. Systematic errors and researcher degrees of freedom

### 6.1. Where bias arises

*Confirmation bias* appears in searching for and interpreting facts in favor of the current position. It can combine with motivated reasoning, anchoring on the first idea, *hindsight bias*, selective reporting, and *cherry-picking* convenient results.

“Researcher degrees of freedom” include the choice of metrics, data-exclusion criteria, models, covariates, subgroups, and when to stop analysis. Choosing these decisions to obtain a desired result creates a risk of p-hacking: many trials and analyses are presented as if there had been only one prespecified test. HARKing further distorts the provenance of a hypothesis.

### 6.2. Control practices and their limitations

| Practice | Risk it helps control | What must be preserved in interpretation |
|---|---|---|
| Preregistration of hypotheses and protocol | Hidden tailoring of the question, outcomes, and analysis to the data | Preregistration does not guarantee the quality of the hypothesis, design, or adherence to the plan |
| A *pre-analysis plan* | Unmarked method changes during confirmatory testing | Justified changes are possible, but must be explicitly distinguished from the original plan |
| Blind analysis | The influence of knowing the desired result on analytical decisions | Applicability depends on the task and whether relevant information can actually be concealed |
| A *holdout* sample | Evaluating a hypothesis or model only on the data used to select it | Held-out data must retain their intended evaluation role |
| Independent reproduction and replication | Implementation errors and dependence on one procedure or sample | It is necessary to understand what is repeated and which errors remain shared |
| Many-analysts: several teams analyzing the same task | Hidden analytical assumptions and dependence on the analyst's choices | Diverse analyses do not create new independent input data |
| Adversarial collaboration: proponents of different explanations testing them together | Ignoring inconvenient alternatives and one-sided test design | Genuine independence of judgment matters more than the mere participation of several people |
| Self-checking and critical examination of the protocol | Logical inconsistencies, arithmetic errors, forgotten alternatives | One's own hidden assumptions may remain unnoticed |

These practices target particular risks; none guarantees a true conclusion. General claims about how much preregistration reduces p-hacking or how well a many-analysts approach exposes hidden assumptions need specific studies and conditions. Kerr (1998), Simmons, Nelson & Simonsohn (2011), Silberzahn et al. (2018), and Scheel et al. (2021) are cited as bibliographic leads; Section 22 states the limits of their verification. Registered Reports and preregistration alone must not automatically be treated as the same intervention.

Ordinary collaboration does not itself eliminate groupthink: a group can reinforce a shared error. A useful check requires different perspectives, the right to disagree, and examination of the grounds for criticism.

### 6.3. Openness and protocol discipline

Confirmatory research requires transparency about prespecified decisions. Exploratory work needs room to refine the question, change observation methods, and formulate new hypotheses. Explicitly identifying the provenance of each analysis and the reasons for changes helps reconcile these needs. Prohibiting all protocol changes would obstruct research; secretly tailoring results to the appearance of an initial plan undermines a conclusion's justification.

## 7. Robustness of the result

Robustness checks show how a conclusion depends on reasonable alternative analytical decisions. The researcher can vary operationalization of measures, variable coding, models, outlier handling, inclusion of covariates, selection criteria, and the composition of analyzed subgroups. The influence of important observations and of including or excluding data is assessed separately.

*Multiverse analysis* and *specification curve* can present multiple defensible analytical choices; the materials associate them with Steegen et al. (2016) and Simonsohn, Simmons & Nelson (2020). Their purpose is to reveal dependence on the analyst's decisions. No universal rule is established here that “it is enough for the signal to survive a substantial proportion of specifications.”

If a small, justified change to an assumption changes the direction or substantive meaning of a conclusion, explain that fragility and reduce confidence where it affects the main claim. Merely crossing p = 0.05 with similar estimates must not automatically be equated with a substantive reversal.

Heterogeneity between subgroups may reflect the phenomenon's structure. The researcher therefore examines whether a discrepancy comes from genuine population and condition differences, measurement, selection, or analytical choices. Robustness does not mean an identical effect in every circumstance.

*Sensitivity analysis* varies material assumptions—for example, sampling conditions or a calculation algorithm—and assesses the consequences for the conclusion. Examining a pessimistic scenario is also useful: what happens to the conclusion if a key assumption is wrong or the data are noisier than expected? Such a check strengthens an argument only within the scenarios examined.

## 8. Reproducibility, replication, and triangulation

### 8.1. Distinguishing the concepts

In NASEM's terminology (2019), **computational reproducibility** means obtaining consistent results with the same input data, computational steps, methods, and code. **Replicability** concerns consistency among studies of the same question, each using its own data. Consistency is assessed with uncertainty taken into account; exact numerical equality is not a universal requirement. This is a paraphrase of the definitions, not a verbatim quotation. [NASEM, 2019](https://www.nationalacademies.org/read/25303/chapter/3).

| Check | What is repeated or changed | What it can assess |
|---|---|---|
| Computational reproducibility | Repeating calculations with the original data | Whether the stated result can be obtained through the described computational route |
| Direct replication | New data with methods and conditions as similar as possible | How much the result depends on a particular execution and sample |
| Conceptual replication | Testing the relevant hypothesis through other methods or conditions | Generalization boundaries and consistency across different checks |
| Independent replication | Other researchers perform the check | Whether the result survives reduced dependence on the original team |
| Triangulation | Comparing different kinds of evidence and methods | Whether conclusions converge despite different possible error sources |

Direct or conceptual replication and team independence are different characteristics of a check; they should not be treated as mutually exclusive categories. Different communities have used reproducibility and replicability differently. The reference to reversed usage in ACM before the terminology change in 2020 is retained as a bibliographic qualification requiring separate verification; applying this document only requires making the chosen definitions explicit.

### 8.2. What a repeat check establishes

Successful independent replication strengthens a conclusion's justification. A successful repeat does not guarantee truth, however, and a single failure does not automatically refute the original claim: reasons for disagreement require analysis. Computational reproducibility can reproduce a coding error as well. [NASEM, 2019](https://www.nationalacademies.org/read/25303/chapter/3).

The requirement that “a conclusion is scientifically justified only after successful replication” is too categorical. Unique historical events cannot be reproduced experimentally, and some measurements destroy the object. In those cases, available evidence, methods, calculations, and alternative explanations are checked within the task's possibilities.

Repeating a study of an effect and checking a particular mechanism also differ. Repeating a sound causal experiment can strengthen a causal inference, but may not distinguish the mechanisms compatible with the observed effect. Therefore, “replication usually confirms only correlation” is not used as a general rule.

### 8.3. Independence and shared errors

Agreement between an experiment, field observations, and technical analysis can be more persuasive than a series of identical checks if the methods really have different vulnerabilities. Diverse method names do not guarantee independence, however. Shared data, a team, a measurement instrument, or an unacknowledged assumption can produce a common error.

Five publications based on one dataset do not provide five independent confirmations. A shared team does not automatically imply complete dependence, and new authors do not eliminate a common error source. The provenance of the data and reasons for possible dependence need to be examined.

## 9. Synthesizing evidence

### 9.1. Choosing a form of synthesis

A systematic review has an explicit search strategy, selection criteria, and a procedure for assessing included materials. Meta-analysis statistically combines sufficiently comparable results; pooling may improve precision, but does not remove weaknesses in the input data. Substantial methodological heterogeneity or qualitative material may call for a transparent narrative or qualitative synthesis.

A narrative synthesis of methodological recommendations is appropriate for a normative question about research quality. Requiring such a text to include its own randomized experiment would be mistaken. References to empirical effects, attributed quotations, and numerical estimates nevertheless require checking, and recommendations need their status identified.

### 9.2. Heterogeneity and directness

Compare initial conditions, populations, periods, measurements, designs, effect estimates, and uncertainty. Conflicting results need explanation: do they concern the same question, do the material assumptions match, and might different contexts underlie the discrepancy?

GRADE considers five reasons for downgrading certainty in a body of evidence for a particular outcome:

1. *Risk of bias*.
2. *Inconsistency*.
3. *Indirectness*.
4. *Imprecision*.
5. *Publication bias*.

Indirectness concerns, for example, a mismatch between the population or intervention studied and the question of interest; broad uncertainty in an estimate concerns imprecision. Heterogeneity in results cannot be assigned entirely to these two domains: inconsistency is considered separately. GRADE also provides conditions for upgrading certainty. [Cochrane Handbook, Chapter 14](https://www.cochrane.org/authors/handbooks-and-manuals/handbook/current/chapter-14).

This system helps structure assessment, but cannot be applied as a universal ranking of technical documents, historical evidence, and qualitative interviews.

### 9.3. Provenance and double-counting

Synthesis needs an “evidence genealogy”: which publications use the same data, which retell others, and which add an independent check. One epidemiological database may support several articles; each text cannot therefore be counted as an independent confirmation of the same effect.

Several publications from one study, including fragmentation called *salami publication*, require attention to overlapping data and analyses. Multiple articles do not automatically determine the degree of dependence or misconduct; synthesis must avoid double-counting and describe each work's contribution precisely.

Simple voting—“how many sources are for and against”—does not work. Account for methodological quality, directness of evidence, effect size and uncertainty, dependence between sources, and possible reasons for disagreement. A design hierarchy does not replace this work.

## 10. Uncertainty and confidence calibration

### 10.1. Different states of knowledge

Confidence statements should reflect the grounds for the conclusion. Rather than only “proven / unproven,” it is useful to distinguish several states:

| State | Meaning | What needs to be communicated |
|---|---|---|
| Established within stated limits | The claim has survived material checks and has strong cumulative support | Conditions, scope, and remaining limitations |
| Strongly supported | The data are persuasive, but important questions or needs for further checks remain | What prevents a stronger conclusion |
| Plausible | There are grounds for the explanation, but alternatives remain material | Strong alternatives and the data that discriminate between them |
| Uncertain | Available results do not permit a stable choice | Which kinds of uncertainty and data deficiencies prevent it |
| Not supported by available data | Current materials do not provide sufficient grounds to accept the claim | How lack of support differs from refutation |
| Conflicting or evidence against | Data disagree or substantially contradict the hypothesis | Which results conflict and possible reasons |
| Unknown | Data are absent or too weak for a substantive assessment | What needs to be learned first |

This is a working verbal framework, not a validated measurement scale. “Established” does not mean absolute infallibility. Absence of data, weak support, and counterevidence must not be collapsed into one state.

Quantitative assessment can use intervals and probabilities within the chosen statistical approach; qualitative assessment can use explicitly justified confidence categories. GRADE's levels—high, moderate, low, and very low certainty in a body of evidence—have their own definitions and do not automatically coincide with the verbal framework above. [Cochrane Handbook, Chapter 14](https://www.cochrane.org/authors/handbooks-and-manuals/handbook/current/chapter-14).

### 10.2. Statistical and practical significance

A p-value helps assess the incompatibility of data with a specified statistical model under its assumptions. It does not by itself determine the probability that a hypothesis is true, the size of an effect, or its practical importance. Conclusions and decisions must not rest solely on crossing p < 0.05. [ASA, 2016](https://www.amstat.org/asa/files/pdfs/p-valuestatement.pdf).

A small, practically unimportant effect can be statistically significant in a large sample; a practically important effect may remain uncertain with limited data or imprecise measurements. An effect estimate, uncertainty, and the context of consequences are therefore needed. “p < 0.05 says nothing about the effect” is too imprecise; the correct limitation concerns interpreting a p-value on its own and conflating it with the effect's size or usefulness.

### 10.3. Absence of evidence and evidence of absence

An unsuccessful search or a statistically nonsignificant result does not establish the absence of an effect. Distinguish:

- an effect was not detected, and data sensitivity may be insufficient;
- the data rule out effects of a specified, substantively important size under stated conditions;
- the question remains open because of data quality, ambiguity, or insufficiency.

“The data unambiguously indicate absence” needs qualification. Equivalence analysis can assess whether an effect is small enough relative to justified bounds of practical significance; it does not generally prove an exact zero under every condition. A negative conclusion should disclose those bounds, sensitivity, and assumptions. [Lakens, 2017](https://pubmed.ncbi.nlm.nih.gov/28736600/?dopt=Abstract). The classic attribution for “absence of evidence is not evidence of absence” is Altman & Bland (1995); Section 22 states its bibliographic status.

### 10.4. What calibration means

Confidence should be compared with actual accuracy across a series of judgments for which the outcome can be checked. For example, among a sufficiently large number of comparable claims assigned 90% probability, good calibration implies approximately 90% correct answers. A single correct or incorrect answer cannot assess a researcher's calibration.

The rounded statements “about 20% errors at 100% confidence” and “70–85% correct answers” are mathematically compatible, but meaningful only when tied to a particular experiment.

Table 1 of Fischhoff, Slovic & Lichtenstein (1977) gives the following results for responses assigned a probability of correctness of 1.00:

| Question format | Correct answers among those rated certainly correct |
|---|---:|
| Open-ended question | 83.1% |
| Judging the truth of a single statement | 71.7% |
| Choosing between two answers, confidence scale from 0.50 to 1.00 | 81.8% |
| Two alternatives, rating the specified alternative on a scale from 0.00 to 1.00 | 80.7% |

These were general-knowledge questions; participants were recruited as paid volunteers through an advertisement in a student newspaper. Formats included open-ended questions, not just binary choices. [Fischhoff, Slovic & Lichtenstein, 1977, Table 1](https://nuovoeutile.it/wp-content/uploads/2014/10/Knowing-with-certainty.pdf).

The table illustrates overconfidence under particular conditions. It does not establish a universal human, scientist, or subject-expert error rate. Comments about dependence on question difficulty—the *hard–easy effect*—and possible attenuation among experts in their own field are retained as matters requiring separate clarification from the relevant literature; they cannot be inferred from this table alone.

## 11. Expertise, metacognition, and observable behavior

### 11.1. Expert errors

Experience does not guarantee freedom from error. Risks considered include overconfidence, fixation on a theory, premature closure, confirmation bias, disciplinary blind spots, and groupthink.

The **Einstellung effect** describes fixation on a familiar solution that obstructs recognition of another, possibly simpler one. The term is associated with Luchins (1942); calling it the “Einstein effect” is incorrect.

Subject experience may help recognize structures in data, choose methods, detect weak arguments, and find a useful next step. Yet the generalization that “an experienced scientist chooses methods better but is subject to the dominance of beliefs” needs specification of domain, task type, and feedback. References to Ericsson's literature and expert forecasting in Tetlock (2005) are directions for investigation, not sufficient grounds for a universal law.

Expertise includes subject knowledge and accumulated patterns, breadth of awareness, the ability to evaluate arguments, and willingness to revise direction. A familiar pattern must remain open to examination, especially when a new task differs from earlier ones.

### 11.2. Metacognition

The researcher tracks the boundaries of their knowledge: what they understand, where they make assumptions, which uncertainty is currently most important, and whether the chosen approach can reduce it. When necessary, they involve a specialist—for example in statistics, mathematics, or the subject—and change method when the current line of work is not approaching an answer.

Useful forms of this work include comparing stated confidence with verifiable outcomes, discussion with colleagues, and a **premortem**: examining in advance why the research might turn out to be wrong or useless. This document establishes no universal effect size for these techniques.

The mentioned “50%—yes/no technique” is insufficiently described to identify it with a specific method. Its general intention is retained: pose questions with checkable outcomes, record confidence, and compare it with results. A possible connection to calibration training in Lichtenstein & Fischhoff (1980) remains tentative.

### 11.3. A behavioral model of a strong researcher

| Observable behavior | How it appears in the work |
|---|---|
| Precise framing | Clarifies the question, unit of analysis, constructs, criteria, and scope |
| Testing alternatives | Formulates competing explanations and seeks observations that separate their predictions |
| Critical treatment of convenient results | Checks whether confirmation arose from search, selection, or analysis choices |
| Openness to data | Considers conflicting sources and interpretations and revises position when sufficiently warranted |
| Traceability | Records sources, methods, assumptions, and reasons for changing the conclusion |
| Proportionate confidence | Marks provisionality and limitations, avoids false precision and tailoring statements to audience expectations |
| Metacognition | Identifies competence gaps and involves appropriate independent expertise |
| Choice of next step | Favors data capable of resolving the central uncertainty and revises the plan when the picture changes |

Personal emotions or value judgments must not substitute for justification. However, the requirement “do not display personal emotions or moral judgments” is not established as a research-quality criterion. Normative questions particularly require disclosure of value assumptions; professional restraint alone does not establish a conclusion's truth.

## 12. Criticism and independent checking

Self-checking can detect arithmetic errors, logical inconsistencies, and omitted alternatives. Its limit is one's own unrecognized assumptions. An independent reviewer adds another perspective, but peer review does not guarantee detection of every data, methodological, or interpretive defect.

Independently repeating calculations and obtaining new data can test what reading a report cannot. The choice among review, reproduction, replication, and an additional experiment should depend on the particular risk of error.

Many-analysts studies, red teams, and adversarial collaboration allow one question to be examined from different analytical and theoretical positions. At the same time:

- several analysts may work with the same flawed database;
- agreement among reviewers may reflect a shared assumption;
- a critical team may find a vulnerability, but its criticism still needs justification;
- calling these practices “new” is relative: adversarial collaboration has been discussed since at least the 2000s, according to a retained bibliographic qualification not separately checked here.

### An empirical example and its interpretive limits

Open Science Collaboration (2015) conducted 100 replications of studies from three psychology journals. The frequently cited “about 36%” refers to one criterion: 35 of 97 originally positive effects, or 36.1%, reached p < 0.05 in the original direction on replication; the 95% confidence interval for this proportion was 26.6–46.2%. The originally positive set included four results with p slightly above 0.05 that the original authors interpreted as positive. [Open Science Collaboration, 2015, section assessing the replication effect against the null hypothesis](https://gwern.net/doc/statistics/bias/2015-opensciencecollaboration.pdf).

This is a bounded measure for the selected body of work, not the proportion of true publications, a universal error rate for psychology, or a measure of all science. It shows why “successful replication” needs an explicit criterion and why uncertainty requires examination. Camerer et al. (2018) is retained as an additional bibliographic lead; its results were not separately checked in this document.

The claim that “most errors pass through peer review” is not justified by the supplied materials: it requires a definition of error, a sample, and a counting method. The substantively supported limitation is the absence of a guarantee, not an error-miss rate established here.

## 13. Research types and transfer of methods

| Type of work | Typical data and methods | What particularly needs checking | Limit on transferring general rules |
|---|---|---|---|
| Experimental | Controlled conditions, randomization, outcome measurement | Execution of the design, alternative explanations, measurement quality, and transferability | Control of conditions does not automatically make results applicable elsewhere |
| Observational | Cohort, cross-sectional, retrospective data; statistical models, matching, natural experiments where conditions permit | Confounding, selection, data provenance, assumptions behind adjustments | Statistical control does not turn any collection of observations into a reliable causal experiment |
| Synthesis of existing work | Systematic review, meta-analysis, narrative or qualitative synthesis | Search, selection, bias risk, heterogeneity, and source dependence | Reliability is bounded by the quality and completeness of available grounds |
| Technical investigation | Documentation, code, logs, tests, experiments with software, networks, or protocols | Fit between source and claim role, version, environment, reproducibility of behavior and failure causes | Clinical design hierarchies do not provide a ready-made assessment of technical evidence |
| Historical and investigative | Archives, documents, testimony, and indirect data; source criticism and critical textual analysis | Provenance and dependence of evidence, context, factual consistency, alternative causal chains | Inability to repeat an event requires different checks; statistical criteria do not apply to every conclusion |
| Exploratory and qualitative | Observation, in-depth interviews, scenario analysis, gradual refinement of concepts and hypotheses | Justification of interpretations, transparency of choices and changes in approach, inferential limits | Requiring all hypotheses to be fixed in advance or applying a laboratory statistical scheme may not fit the task |

Exploration characterizes the aim and stage of work; qualitative methods are not limited to early hypothesis generation. The table shows typical emphases, not mutually exclusive classes: one study may combine several approaches.

General principles—fit between question and method, critical evaluation of evidence, testing alternatives, transparency, and calibration—transfer widely. Subject-specific methods, such as conducting an RCT, analyzing natural experiments, CRISPR techniques, or historical verification of documents, require specialized preparation. Even statistics is appropriate only insofar as it fits the task. General methodology can expose a weak link in an argument, but cannot replace domain competence.

## 14. Research, decisions, and when to stop

### 14.1. What is known and what to do

A research conclusion addresses what is established or plausible. A practical recommendation also incorporates goals, acceptable risk, error costs, deadlines, and available actions.

When consequences are asymmetric, it may be reasonable to act before uncertainty is resolved. For example, “the data are insufficient, but given the possible harm we choose A” expresses a decision under a particular risk attitude. It does not warrant retelling the result as “the research proved A is better.”

Consider false-positive and false-negative decisions, reversibility, the option of deferral, and consequences of delay. An urgent, hard-to-reverse situation may call for a fallback or cautious alternative, but that choice needs its own justification. Urgency does not itself increase confidence in a scientific conclusion.

### 14.2. Four stopping rationales

| Rationale | What it means | What must remain visible |
|---|---|---|
| Information is sufficient for the current decision | Material alternatives have been considered and available new information is unlikely to change the choice | Sufficiency is for a particular decision, not final completion of knowledge |
| New data are currently unreachable | Access, resources, funding, a feasible experiment, or suitable measurement are unavailable | Forced stopping does not remove uncertainty |
| Further search is not worthwhile | The expected benefit of clarification is small relative to its cost and delay | The benefit and cost assessment needs grounds |
| Remaining uncertainty cannot be resolved with available means | Current methods or properties of the task prevent resolution | Distinguish limits of today's capabilities from proven impossibility in principle |

This typology is the author's working construct. It preserves the distinction between “enough for the decision,” “unobtainable,” and “not worth pursuing,” but does not itself supply a computable stopping criterion.

### 14.3. The value of additional information

Value of Information—VOI—connects continued research to the expected benefit of new information for choosing an action. Decision-analysis literature associates this idea, among others, with Raiffa & Schlaifer (1961). This document uses its qualitative meaning: what possible new data could change the decision, and whether that possibility justifies the cost.

A search cannot be declared unhelpful merely because the last few sources repeated what was already known. Repetition may reflect a narrow strategy. Stopping requires attention to unresolved competing hypotheses and gaps that could materially affect the answer.

No universal practical procedure for calculating VOI for arbitrary research searches is established here. Claims that “additional information is unlikely to change the conclusion” and “marginal returns are near zero” require task-specific justification. When error consequences are serious, an additional independent check may retain high value even after substantial work.

### 14.4. Heuristics for choosing the next step

| Situation | Reasonable direction | Limitation |
|---|---|---|
| Material competing hypotheses remain | Find data or an experiment for which their predictions diverge | Another general confirmation may contribute little |
| Controlling a factor is critical to causal inference but a direct experiment is impossible | Consider a natural or quasi-experiment and suitable observational causal-analysis methods | Their assumptions need justification; an analogue alone does not ensure control |
| Direct data are absent | Seek indirect evidence, analogues, and opportunities for triangulation | Indirectness must weaken the conclusion where transfer is unjustified |
| The conclusion depends on a study's method or context details | Consult the primary source, data, and supplementary material | A secondary retelling may lose material conditions |
| Many direct studies have accumulated | Conduct a suitable synthesis | Results cannot be added without checking comparability and dependence |
| The result depends on one sample or methodology | Consider independent replication or an alternative method | Choose a check targeting the particular vulnerability |
| The conclusion has serious consequences | Add independent checks of material assumptions and results | One team may miss its shared blind spots |
| New information is unlikely to change the decision and costs are substantial | Stop or suspend the search, recording residual uncertainty | Low usefulness must be justified, not declared from source count |

Heuristics depend on the task, time and resource constraints, acceptable risk, and method availability. They do not supply an automatic answer until it is specified how to recognize the situation in the left column.

## 15. Reporting quality and communicating conclusions

A justified result can be distorted in presentation. Reporting quality requires preserving the connection between a claim and the data, conditions, and assumptions on which it rests.

Typical distortions include:

- **Suppressing uncertainty:** a preliminary result becomes a categorical conclusion.
- **Strengthening causal language:** an observed association is retold as an established effect.
- **Selectivity:** supporting results remain visible while contradictory ones disappear or change meaning in the retelling.
- **Mismatch between the main text and the summary:** decisive limitations disappear from an abstract, presentation, or short communication.
- **Visual distortion:** scale, axis range, or an incorrect label creates an impression inconsistent with the data. A nonzero scale origin is not judged outside its task; the problem is misleading communication of quantities.
- **Citation distortion:** secondary accounts, media, or repeated citation attribute a stronger claim to a source than it made.
- **Unreliable quotation:** a paraphrase is put in quotation marks and presented as exact wording.
- **False precision and promotional presentation:** certainty or importance is inflated without additional grounds.

When shortening, preserve the population or system, observation conditions, time and data context, inferential boundaries, degree of uncertainty, material contradictions, and unresolved questions. Simpler language is acceptable; changing the strength or subject of a claim requires grounds.

Transparency also means accurate attribution: readers should be able to tell observation from interpretation, recommendation, and assumption. “Sources: methodological manuals and current thinking” does not provide that traceability.

## 16. An integrated model of research

### 16.1. Six dimensions of quality

The proposed model brings together six dimensions discussed above:

| Dimension | Content |
|---|---|
| Question quality | A clear problem, method fit, defined constructs and boundaries, alternatives, and the risk of framing the question toward a desired answer |
| Evidence quality | Suitable data type, measurement and design quality, control of relevant systematic errors, transparent provenance and processing |
| Inference quality | Traceable reasoning, testing material alternatives, causal or other interpretation appropriate to the question, robustness |
| Synthesis quality | Systematic search and comparison, assessment of heterogeneity, directness, and dependence, no double-counting |
| Quality of uncertainty handling | Proportionate confidence, interpretable intervals or categories, distinguishing absence of data, lack of support, and evidence of absence |
| Reporting quality | Complete and accurate presentation, preserved conditions and contradictions, checkable attribution, no strengthening through shortening |

These dimensions can structure criticism. The document establishes no weights, universal thresholds, or validity of a total score; converting the model into an assessment scale would require separate work.

### 16.2. Lifecycle

| Stage | Main work | Question for checking the transition |
|---|---|---|
| 1. Problem boundaries | Define purpose, context, unit of analysis, and scope | Is this the right problem? |
| 2. Questions and hypotheses | Clarify concepts, measurements, main and alternative explanations, and suitable design | Do methods fit the question; what could change the initial position? |
| 3. Data search | Use suitable sources, terminology, citation tracing, and counterevidence searches | Does the strategy create a one-sided picture? |
| 4. Selection and assessment | Check provenance, methodology, and each piece of evidence's role | Does the source support the specific claim, and how directly? |
| 5. Comparing hypotheses | Assess diagnosticity of observations, confounders, and alternative interpretations | Which explanations do the data actually distinguish? |
| 6. Synthesis | Bring together comparable results, explain heterogeneity, and account for dependence | Does double-counting or averaging different questions create false agreement? |
| 7. Robustness checks | Examine justified alternative analyses, subsamples, and key assumptions | Which decisions determine the substantive conclusion? |
| 8. Uncertainty assessment | State support, limitations, and areas of ignorance | Does confidence match the grounds? |
| 9. Deciding to finish | Consider the usefulness of new data, access, cost, and consequences of delay | Why is the available work now sufficient, or further work impossible or not worthwhile? |
| 10. Reporting | Communicate the conclusion, grounds, conditions, contradictions, and limitations | Has meaning survived presentation and shortening? |

The cycle permits returns. New data may require changing a hypothesis, refining a metric, reconsidering selection, or broadening the search. Validity, assumptions, and systematic errors are checked throughout. Initial framing and hypothesis formulation are separated for clarity; in practice they may constitute one stage.

### 16.3. An evidence matrix

The following card can be used for each material claim:

> **Claim:** what exactly is accepted or tested.  
> **Evidence type:** experiment, observation, document, technical test, expert judgment, or a combination of methods.  
> **Main sources:** publications, reports, documents, data, and available identifiers.  
> **Methodological quality:** design, measurements, sample, assumptions, and material bias risks.  
> **Replication and robustness:** repeat checks, alternative analyses, and their results.  
> **Counterevidence:** negative or conflicting results and ways of explaining them.  
> **Applicability:** population, system, conditions, period, and transfer boundaries.  
> **Confidence in the conclusion:** support level with explicit justification.  
> **Limitations:** what is unaccounted for, unknown, or in need of further checking.

Source dependence should be reflected in provenance or limitations. This matrix is the author's organizational tool. No complete example of its use on an independent subject-specific task is shown here, and whether this particular template improves research outcomes has not been tested. Filling every field does not make its contents justified.

## 17. A catalog of research errors

| Error | Observable manifestation | Direction of control |
|---|---|---|
| Incorrect question framing | A different problem, an overly broad topic, or a question tailored to a desired answer is studied | Reconsider purpose, scope, and the required kind of inference |
| Construct substitution | An available metric is treated as the property of interest without justification | Check operationalization and alternative measurements |
| Confirmation bias | Search and interpretation systematically favor the initial position | Seek counterevidence and discriminating observations |
| Motivated reasoning | The desired outcome changes standards for accepting and rejecting arguments | Explicit criteria, independent examination, and comparison of alternatives |
| Anchoring and Einstellung | The first idea or a familiar method narrows the alternatives | Reconsider framing and methods; involve another perspective |
| Hindsight bias | An outcome is presented as expected after it becomes known | Preserve initial hypotheses, plans, and confidence estimates |
| *Premature closure* | The first plausible explanation is accepted without checking material alternatives | Examine what else could have produced the observations |
| Restricted search | Important databases, terms, languages, periods, negative results, or gray literature are missed | Assess coverage and revise the strategy |
| Selective data and reporting | Only convenient metrics, observations, and conclusions are retained | Transparent selection and a complete account of material results |
| HARKing | A post-analysis hypothesis is presented as prespecified | Separate confirmatory and exploratory work |
| P-hacking and hidden analytical tailoring | Models, exclusions, and tests are selected until desired significance appears | An analysis plan, disclosure of alternatives, and robustness checks |
| Causal overgeneralization | Correlation, temporal sequence, or a mechanism story is declared sufficient causal proof | A suitable design and analysis of its assumptions |
| Unaccounted confounding and selection | Common causes, feedback, or the selection process alter interpretation | Analyze alternative causes and how the sample was formed |
| Dependent sources | Repeated publications or retellings count as independent confirmations | Track provenance, data overlap, and shared assumptions |
| Ignoring contradictions | An inconvenient result is excluded without substantive grounds | Check methods, context, heterogeneity, and alternatives |
| Excessive transfer | A local result is extended to unsupported populations, systems, or periods | Explicit applicability boundaries and assessment of indirectness |
| Substituting absence for uncertainty | An undetected or statistically nonsignificant effect is declared absent | Assess sensitivity, precision, and substantively meaningful bounds |
| Overconfidence | Claims exceed the data; uncertainty and limitations are concealed | Calibration and traceable assessment of support strength |
| Groupthink and blind spots | Team agreement suppresses checks of shared assumptions | Independent judgment, alternative approaches, and justified criticism |
| Endless low-value search | Minor confirmations accumulate instead of resolving the central uncertainty | Assess the next step's value and stopping rationale |
| Distortion in presentation | A conclusion is strengthened in an abstract, presentation, chart, or retelling | Compare statements with data, conditions, and primary sources |

One practice may reduce several risks, and one error may require several checks. The catalog describes typical failures, but establishes neither their frequencies nor guaranteed effectiveness of the proposed controls.

## 18. Tensions between useful principles

| Tension | What must be reconciled |
|---|---|
| Breadth and depth | Coverage of different explanations and domains versus detailed checking of the most important grounds |
| Speed and thoroughness | A timely answer versus completeness of checking and error probability |
| Research and decision | Continuing to refine knowledge versus acting under current uncertainty |
| Openness and protocol discipline | Freedom to change direction versus protection from hidden tailoring |
| Primary data and synthesis | New data with a controlled design versus using existing work and risking inherited errors |
| Simplicity and realism | An understandable model and overfitting control versus capturing material complexity and avoiding omitted factors |
| Exhaustive search and diminishing returns | Accounting for all information versus stopping in time when new data have little value |
| Skepticism and resolve | Attention to limitations versus the ability to state a conclusion or recommendation |

Neither side is universally correct. The choice depends on question type, consequences of error, resources, data properties, and research stage. Simplicity does not itself ensure accuracy, and depth of checking does not justify any delay.

## 19. Common misconceptions

| Simplified view | Qualification |
|---|---|
| More sources mean a more reliable conclusion | Relevant diversity, quality, and independence are needed; many retellings of one weak basis create no new evidence |
| A primary source is always more reliable than a secondary one | It is necessary for the details of a particular study; a high-quality synthesis may be more useful than one experiment for the overall picture |
| Peer review guarantees quality | Review can expose errors but does not guarantee detection of all defects; a miss rate is not established here |
| Statistical significance means importance | A p-value alone determines neither effect size nor decision relevance |
| A nonsignificant result means no effect | A negative conclusion needs sufficient sensitivity and an appropriate assessment of the absence of a practically important effect |
| Successful replication proves a mechanism | A repeat can strengthen the inference about an effect; discriminating mechanisms requires suitable tests |
| Scientific justification is possible only after replication | Repeatability depends on the subject; unique events are investigated by other checkable means |
| Scientific consensus proves truth | Consensus can be indirect evidence; its strength depends on the quality, independence, and completeness of its grounds. Shared error and groupthink remain possible |
| Evidence hierarchies are useless | They can be useful bounded tools, but do not replace assessment of the particular question, study, and body of data |
| No references means no testable claims | These are different deficiencies: an empirical statement can be testable in meaning even if the author provides no basis for checking it |

Consensus should neither be made a guarantee nor assigned no evidential value. At the same time, the possibility that a historical majority was wrong is not an argument for any dissenter: an alternative position also needs grounds.

## 20. Open methodological questions

The following questions are retained as directions for future work. The list reflects the author's assessment of difficulties; it does not establish that solutions are entirely absent or that these problems have universally accepted top priority.

1. **Joint synthesis of qualitative and quantitative results.** How can different kinds of inference be compared, context retained, and the strength of complex qualitative arguments assessed without false numerical precision?
2. **Comparing incompatible methods.** How can results using different constructs, assumptions, and verification standards be combined without erasing important distinctions?
3. **Stopping research.** How can search sufficiency and the scope of remaining uncertainty be formalized without making completion arbitrary?
4. **Working with scarce resources.** How should data collection, synthesis, replication, and action be prioritized under tight time and funding constraints?
5. **Assessing expert judgments.** How can competence and calibration be evaluated reliably, team judgments coordinated, and useful disagreement preserved?
6. **Publication bias.** How can it be detected and reduced across disciplines, including small fields with few studies?
7. **Complex dynamic systems.** How can robustness, reproducibility, and transferability be assessed in social systems and networks, ecology, climatology, and other changing environments?
8. **Completeness of an answer.** How can work be finished with a usable conclusion while retaining material detail, limitations, and unresolved alternatives?

## 21. Limits of justification and adopted methodological corrections

### 21.1. What can count as the result of this work

Types of validity, the distinction between truth and justification, testing alternatives, control of analytical decisions, robustness, source independence, and proportionate confidence form a coherent methodological framework. It can be used as a basis for examining research and organizing checks.

Consistency with established concepts does not prove the framework is complete, that all practices are equally useful, or that applying the whole model guarantees a better result. The heuristics, behavioral model, verbal categories, stopping typology, and evidence matrix remain professional recommendations and the author's synthesis. Evaluating them as a single tool requires criteria, application examples, and separate testing.

### 21.2. What remains limited or unchecked

| Proposition | Current status and limitation |
|---|---|
| Citation support for the entire framework | The supplied texts lacked URLs and a complete bibliography. Sources were reconstructed and checked for selected key propositions; for the rest, authors, years, and topics are retained without pretending to have fully verified them |
| Describing the text as entirely devoid of empirical or testable claims | That assessment is too strong: statements about overconfidence, review, and the effects of research practices are testable in meaning. The deficiency is incomplete attribution and support, not inherent untestability |
| Quantitative effects of preregistration and other protective practices | Specific effect sizes, conditions, and cross-domain transfer are not established here. Mentioning Registered Reports does not prove the effect of every kind of preregistration |
| Expertise and overconfidence | Universal claims about experts' advantages and errors require a domain and task; a general-knowledge experiment does not supply that check |
| Hard–easy effect and differences between experts and nonexperts | Retained as lines of investigation from the methodological discussion; no separate empirical assessment was conducted |
| Approximate chronology of PICO and GRADE | The estimate “PICO predates GRADE by about a decade” was not checked separately. Richardson et al. 1995 is used to correct attribution without claiming established historical priority |
| The “50%—yes/no technique” | The specific technique could not be identified from the insufficient description; the general principle of comparing probabilities with outcomes is retained |
| Practical VOI assessment | The concept is used qualitatively; no universal procedure for calculating the next research step's usefulness is supplied |
| Conditions such as “new data are unlikely to change the conclusion” | These are heuristic criteria. Measurement methods and task-specific thresholds remain open |
| Evidence matrix and quality scales | Working constructs without demonstrated independent application, validated weights, or evidence of effectiveness here |
| Many analysts and adversarial collaboration as “new practices” | Relative novelty is not established; substantive value must be discussed separately from an approach's age |
| Technical, historical, and qualitative research | General principles and distinctions between evidence types are given; detailed specialized protocols are not included |
| Completeness of the error catalog and open questions | The lists aid orientation but do not claim an empirically confirmed exhaustive taxonomy |

### 21.3. Corrections that affect meaning

The following limitations of wording must survive use of this document:

- A successful-replication requirement is replaced with a conditional strengthening of justification, considering repeatability and reasons for disagreement.
- Nonverbatim quotations attributed to NASEM and Ioannidis are presented as attributed paraphrases. Ioannidis's model argument is not turned into an empirical count of false publications.
- PICO is connected to the tradition of structuring clinical questions and Richardson et al. (1995); the framework's origin is not attributed to GRADE.
- All five GRADE downgrading domains are retained; inconsistency, indirectness, and imprecision are not conflated.
- Simple source voting is rejected; the usefulness of hierarchies is bounded by question type and does not replace evaluating specific grounds.
- Causal inference is connected to appropriate designs and assumptions; mechanisms, randomization, and observational design are not declared automatic guarantees.
- Statistical significance is distinguished from effect size and practical importance; lack of significance is distinguished from evidence of absence.
- Overconfidence and successful-replication proportions retain specific conditions and counting criteria. Original approximations of “about 20%,” “70–85%,” and “about 36%” are not used as universal measures.
- The Russian rendering of Einstellung is corrected to “эффект установки.” The terms holdout, pre-analysis plan, many-analysts, groupthink, triangulation, construct validity, p-hacking, and publication bias are given recognizable forms.
- Fit between the answer and the question is separated from an unsupported use of the label face validity.
- Post-observation hypothesis formation is distinguished from HARKing; exploratory flexibility is compatible with transparent analysis provenance.
- Consensus remains possible indirect evidence, while the requirement not to express emotion is treated as an unsupported norm excluded from quality criteria.

Two damaged sentences were reconstructed from context: the warning about “convenient stories” is rendered as a requirement to test them against counterevidence; the fragment about multiple publications is rendered as a warning about dependence and double-counting results from one study. This is editorial reconstruction supported by adjacent propositions, not recovered verbatim author wording. Typos and draft notes were not retained as substantive claims.

## 22. Sources and bibliographic leads

### 22.1. Sources used for additional checking

Verification is limited to the excerpts and tasks specified below. Access to an abstract or bibliographic record is not labeled as reading the full text. The listed information was checked during preparation of the document on October 6, 2026; DOIs are persistent identifiers, and available copies are locations used for substantive checks.

| Source | Link | What was checked |
|---|---|---|
| National Academies of Sciences, Engineering, and Medicine. **Reproducibility and Replicability in Science**. 2019 | [Publication, Summary section](https://www.nationalacademies.org/read/25303/chapter/3); [DOI: 10.17226/25303](https://doi.org/10.17226/25303) | Definitions of reproducibility and replicability; limits on interpreting successful and unsuccessful repeats; reproducibility of a calculation error |
| Richardson W. S., Wilson M. C., Nishikawa J., Hayward R. S. **The well-built clinical question: a key to evidence-based decisions**. ACP Journal Club. 1995;123(3):A12–A13 | [PubMed bibliographic record](https://pubmed.ncbi.nlm.nih.gov/7582737/?dopt=Abstract); [DOI: 10.7326/ACPJC-1995-123-3-A12](https://doi.org/10.7326/ACPJC-1995-123-3-A12) | Bibliography checked. The four-part structure was checked against an available indexed excerpt of a copy of the original; the publisher's full text was not read. Historical priority was not established |
| Cochrane Handbook for Systematic Reviews of Interventions. **Chapter 14: Completing ‘Summary of findings’ tables and grading the certainty of the evidence** | [Official chapter](https://www.cochrane.org/authors/handbooks-and-manuals/handbook/current/chapter-14) | Five GRADE domains, certainty categories, and outcome-specific assessment of a body of evidence. The page states a chapter update in August 2023 and Handbook version 6.5, 2024 |
| Ioannidis J. P. A. **Why Most Published Research Findings Are False**. PLOS Medicine. 2005;2(8):e124 | [Publisher's original](https://journals.plos.org/plosmedicine/article?id=10.1371/journal.pmed.0020124); [DOI: 10.1371/journal.pmed.0020124](https://doi.org/10.1371/journal.pmed.0020124) | The model-based argument and dependence of positive findings' credibility on power, prior plausibility, and bias |
| Fischhoff B., Slovic P., Lichtenstein S. **Knowing with Certainty: The Appropriateness of Extreme Confidence**. Journal of Experimental Psychology: Human Perception and Performance. 1977;3(4):552–564 | [Copy of the original journal article](https://nuovoeutile.it/wp-content/uploads/2014/10/Knowing-with-certainty.pdf); [DOI: 10.1037/0096-1523.3.4.552](https://doi.org/10.1037/0096-1523.3.4.552) | Table 1 visually checked against PDF p. 554; task formats and participant recruitment description checked. Section 10's numbers concern this experiment |
| Lichtenstein S., Fischhoff B., Phillips L. D. **Calibration of probabilities: The state of the art to 1980**. In: Judgment under Uncertainty. 1982, pp. 306–334 | [Publisher's chapter page](https://www.cambridge.org/core/books/abs/judgment-under-uncertainty/calibration-of-probabilities-the-state-of-the-art-to-1980/9F0C9EC2997AEEB6DDDB304C2F935A16); [DOI: 10.1017/CBO9780511809477.023](https://doi.org/10.1017/CBO9780511809477.023) | Bibliography and the available introductory definition of calibration; the full chapter was not checked. The numerical example relies on the 1977 article |
| Open Science Collaboration. **Estimating the reproducibility of psychological science**. Science. 2015;349(6251):aac4716 | [Bibliographic record and abstract](https://pubmed.ncbi.nlm.nih.gov/26315443/); [Copy of the original article](https://gwern.net/doc/statistics/bias/2015-opensciencecollaboration.pdf); [DOI: 10.1126/science.aac4716](https://doi.org/10.1126/science.aac4716) | Criterion, numerator, denominator, and uncertainty of the 36.1% estimate; corresponding section on p. aac4716-4. Not used to estimate the proportion of true publications |
| American Statistical Association. **Statement on Statistical Significance and P-Values**. 2016 | [Official statement with six principles](https://www.amstat.org/asa/files/pdfs/p-valuestatement.pdf); [DOI of the main publication: 10.1080/00031305.2016.1154108](https://doi.org/10.1080/00031305.2016.1154108) | Officially published principles of p-value interpretation checked. Added to refine statistical statements |
| Lakens D. **Equivalence Tests: A Practical Primer for t Tests, Correlations, and Meta-Analyses**. Social Psychological and Personality Science. 2017;8(4):355–362 | [PubMed abstract and bibliography](https://pubmed.ncbi.nlm.nih.gov/28736600/?dopt=Abstract); [DOI: 10.1177/1948550617697177](https://doi.org/10.1177/1948550617697177) | The abstract was used to check the connection between equivalence and bounds of the smallest effect of interest, and the distinction from an ordinary nonsignificant result. Full text not read; added to correct an absolute negative conclusion |

The question structure was substantively checked using an indexed excerpt from a [copy of Richardson et al. at QMUL](https://qmplus.qmul.ac.uk/pluginfile.php/290559/mod_resource/content/1/The%20well-built%20question.pdf); direct access to the full file requires authorization. The relevant passage allows a comparison where applicable. This document does not assert that four filled fields are mandatory for every research task.

### 22.2. Retained attributions without a separate primary-source check

The table retains all other named works, authors, and systems. Incomplete bibliographic details remain incomplete: no titles, outlets, or DOIs have been guessed. These entries can guide further searches, but do not provide verified support for any wording in the document.

| Author, work, or system | Topic associated with the attribution | Record limitation |
|---|---|---|
| Shadish, Cook & Campbell, 2002 | Causal-inference criteria and design | Specific primary-source sections not checked |
| John Stuart Mill | Historical connection of causal criteria to Mill's method | No particular work or location specified |
| Richards J. Heuer, 1999 | Analysis of Competing Hypotheses | Detailed procedure and application effectiveness not separately checked here |
| Karl Popper | Falsification | No particular work, edition, or pages specified |
| Deborah Mayo, 2018 | Severe testing | No exact location supporting the paraphrase specified |
| Steegen et al., 2016 | Multiverse analysis | Primary text and result boundaries not separately checked |
| Simonsohn, Simmons & Nelson, 2020 | Specification curve | Primary text not separately checked |
| Kerr, 1998 | HARKing | Attribution retained; primary source not separately checked |
| Simmons, Nelson & Simonsohn, 2011 | Researcher degrees of freedom and false-positive conclusions | Specific results and effect sizes not established here |
| Silberzahn et al., 2018 | Many-analysts studies | One attribution does not support a universal estimate of independent analysts' usefulness |
| Scheel et al., 2021 | Registered Reports and selective reporting | Connection to a particular form of preregistration and effect strength require checking |
| Luchins, 1942 | Einstellung effect, “эффект установки” | Historical attribution retained without separately opening the work |
| Lichtenstein & Fischhoff, 1980 | Calibration training | Connection to the unspecified “50%—yes/no technique” is tentative |
| Camerer et al., 2018 | Replication projects | Mentioned as an additional lead; measures and conditions not checked |
| Ericsson | Expertise and its domain limits | No year or specific work stated |
| Tetlock, 2005 | Expert forecasting | Transfer to all research expertise is not justified |
| Raiffa & Schlaifer, 1961 | Value of information and decision analysis | Practical VOI procedure for research searches not reconstructed here |
| Altman & Bland, 1995 | Distinguishing absence of evidence from evidence of absence | Attribution retained; exact primary-source wording not checked |
| Oxford Centre for Evidence-Based Medicine—Oxford CEBM | Levels of evidence | Specific scale version not stated; the system is not equated with GRADE |
| ACM, terminology before 2020 | Differences in usage of reproducibility and replicability between communities | History of terminology changes not separately checked |

GRADE and Cochrane are retained in the main text as systems and guidance; the checked Cochrane chapter is included in subsection 22.1. Web of Science, PubMed, Scopus, preprint servers, archives, and code repositories are mentioned as search infrastructure; listing them is not evidence for methodological propositions.

### 22.3. Using the references

For further work, return to the primary source when a decision depends on an exact method, definition, or effect size. An author's name in a table does not justify calling a claim verified. The general model's usefulness lies in its structure of questions and checks; confidence in each proposition must remain connected to its own grounds.
