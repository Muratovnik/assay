# Quality of Software Systems and Engineering Decisions

**English** · [Русский](../../ru/research/foundations/software-engineering.md)

> A research synthesis, not task-execution instructions or normative Assay policy. Source status and verification limits are retained from the original document. [About the corpus and translations](../README.md).

## Scope and status of the conclusions

What distinguishes a well-designed, evolving software system? Which engineering decisions help preserve its usefulness, reliability, and affordable cost of change? How can a justified practice be distinguished from a plausible heuristic, and a measured result from a convenient indicator?

This model centers on a system that continues to perform the work it is needed for and remains manageable as requirements, load, technologies, and team composition change. Quality is considered from the perspectives of the product, its internal structure, operations, and the development process. An elegant code structure, a large number of tests, or frequent releases cannot answer all these questions on their own.

The main framework is: **engineering decision → intermediate system properties → outcomes of use and evolution**. The arrows represent proposed mechanisms and testable relationships. Much of the empirical evidence is correlational or descriptive; the arrows must not automatically be read as proven causality.

The document distinguishes five types of grounds:

- **Definitions and selected quality criteria:** they specify what is assessed but do not themselves establish a practice's benefit.
- **Empirical results:** observations, experiments, repository analyses, and reviews with particular samples and limitations.
- **Practitioner experience:** interviews, company guidance, accounts of operations and incidents.
- **Engineering recommendations:** ways of acting grounded in mechanisms, experience, and available data; a universal effect is usually not established.
- **Unconfirmed claims and hypotheses:** retained for investigation, but not used as proven support.

Source-verification statuses reproduce the review information dated **October 5, 2026**. “Abstract opened” means the abstract was checked, not the full text; “from memory” means the reviewer did not recheck the documentary source; “a related work found” does not confirm every attributed result. No further external verification was performed during consolidation. Bibliographic information, limitations, and unresolved references appear at the end of the document.

The empirical evidence applies primarily to long-lived object-oriented systems, open-source Java/C++ projects, particular industrial teams, and microservice architectures. Transfer to embedded, scientific, short-lived, and timing-critical software requires separate justification.

## 1. An operational definition of system quality

### 1.1. Correctness and functional suitability

A system should provide the functions users need and conform to requirements and specifications. Observable indicators include correctness of important scenarios, functional completeness, and few operational defects and regressions. Defect density, including relative to code size, can help track change over time but does not replace assessment of error severity and user impact.

Correctness of a particular implementation and correctness of the problem formulation are different questions. A formally satisfied requirement still needs to be compared with business logic, the real need, and success criteria.

### 1.2. Reliability, availability, and recovery

Reliability is the ability to perform specified work under agreed conditions, withstand workloads, and respond predictably to failures. It includes fault tolerance, redundancy, recovery from errors, and availability. Observable outcomes include failure frequency, downtime, and recovery time, often denoted MTTR.

Additional functionality can make reliability harder to achieve. Choices must reflect system criticality: predictable behavior and safe error handling may be worth more than another feature. Accumulated defects and hard-to-change code can increase operational risk, but without specific evidence it cannot be claimed that all technical debt inevitably causes incidents.

### 1.3. Security

Security includes protection from unauthorized actions, access control, attack resistance, and detection and timely remediation of vulnerabilities. Vulnerabilities concern security; conflating them with the definition of reliability is incorrect.[^iso25010]

Practical reference points include *fail-safe defaults*, a clear authentication and authorization model, data isolation, justified use of encryption, and auditability. Debt in authentication, logging, or component updates can create risks, but specific effects need separate analysis. The materials establish no empirical connection between “design cleanliness” and security.

### 1.4. Performance and scalability

Performance is assessed through response time, throughput, and CPU, memory, and I/O consumption under actual load. Scalability is the ability to maintain required characteristics as load grows; horizontal scaling is one possible approach where system conditions justify it.

The quality criterion is sufficient performance for the task and predictable change in those characteristics. High speed can conflict with understandability, maintenance cost, and certain security guarantees. Optimization requirements differ between a game engine, a real-time trading system, and an ordinary enterprise application.

### 1.5. Usability

Product quality includes ease of completing user tasks. Correct internal architecture does not automatically provide it. Usability is identified as a quality attribute in the empirical material presented, but it contains no dedicated interface studies or research connecting UX to architectural decisions.

### 1.6. Maintainability and cost of change

*Maintainability* is the ability to understand, correct, and modify a system with acceptable effort and risk. It is observed through time spent understanding a task, locality of changes, rework, verification difficulty, and the cost of releasing a change.

Low cost of change over time is central to the model. Changing one function should not unnecessarily trigger a cascade of changes elsewhere; a new developer should be able to understand the system without excessive reconstruction of hidden context. Microsoft's Engineering Playbook uses clarity, modularity, documentation, and bounded change risk as characteristics of maintainable software; this is practical guidance, not a comparative study of those properties' effectiveness.[^microsoft-playbook]

Short release time and low technical debt are not synonyms: the former is a process outcome, the latter a property of future obligations and costs. They may be related, but one cannot be defined through the other.

### 1.7. Evolvability and extensibility

*Evolvability* is the ability of a system to change throughout its lifecycle while retaining manageable development costs. Extensibility concerns adding capabilities. These concepts are related to maintainability but do not require every imaginable feature to be implemented in advance.

In ISO/IEC 25010 terminology, maintainability includes modularity, reusability, analyzability, modifiability, and testability. *Evolvability* is used in research literature, including work on microservices, and should not be attributed to the standard as a separate characteristic. In the ISO/IEC 25010:2011 model, adaptability belongs to portability and modifiability to maintainability. ISO/IEC 9126 should be identified as the preceding model, replaced by ISO/IEC 25010 in 2011; they must not be presented as simultaneously current editions of one standard. These terminological corrections were checked in the reviews from memory.[^iso25010][^iso9126][^bogner2019]

A practical goal is to avoid “calcification” of the old core: accumulating layers nobody dares change while continually adding features around them. Periodic renewal and removal of obsolete parts may support changeability, but neither the optimal frequency nor the economic effect of refactoring is universally established.

### 1.8. Modularity, cohesion, and locality of change

**Coupling** is dependency between components. **Cohesion** is the consistency of a component's responsibility and contents. The desired combination is justifiably low external coupling and high internal cohesion; an unqualified term such as “high connectedness” is ambiguous between the two meanings.

Meaningful module boundaries, expressive interfaces, and explicit contracts help limit change propagation. Observable indicators include the number of affected components, predictable impact analysis, and the ability to test parts separately. Low cohesion appears as mixed responsibilities; strong external coupling appears as the need for coordinated changes in several places.

Size, complexity, coupling, and cohesion metrics are associated with external quality attributes in a number of object-oriented systems. They are correlational indicators, not universal quality thresholds. The evidence for inheritance, including DIT and NOC, is weaker and more contradictory.[^jabangwe2015]

### 1.9. Understandability and cognitive load

Understandability concerns the effort needed to comprehend code correctly, identify the causes of behavior, and make a safe change. Practical manifestations include onboarding time, code navigation, reconstruction of intent, and maintenance-task performance.

Clear naming, consistent style, and appropriate documentation are reasonable ways to aid understanding. However, LOC, cyclomatic complexity, Cognitive Complexity, and the maintainability index cannot be treated as direct measures of how understandable code is to a person. In Lavazza, Morasca, and Gatto's study, models using one or two structural metrics had an average understandability prediction error of around 30%; a subsequent replication did not confirm correlations on the same code. Sample details and limitations appear in Section 6.[^lavazza2023][^kapitsaki2025]

### 1.10. Testability and quality of checks

Testability is the ability to check important behavior accurately and quickly enough at acceptable cost. What matters is not only available test infrastructure and scenario breadth, but also **oracle quality**: the rule by which a check distinguishes correct behavior from incorrect behavior.

Coverage percentage indicates which code portions executed. It does not itself establish whether important properties were checked or whether tests can detect the relevant error class. TDD, the presence of CI, line coverage, and test-suite effectiveness are different objects; findings about one cannot automatically be transferred to the others.[^nagappan2008][^rafique2013][^inozemtseva2014]

### 1.11. Diagnosability and observability

The system should provide enough information to localize faults: logs, metrics, traces, and relationships between events. Practical examples include connecting records to a transaction or user action, detecting a failure, and determining the component where it arose.

Observability helps test assumptions about system behavior after release. Its value is assessed through diagnosis and recovery, not the volume of logs collected. Emergency restarts and other recovery mechanisms should be considered alongside detection of failure causes, not as sufficient substitutes for diagnosis. The materials establish no universal quantitative effect of these practices.

### 1.12. API quality, compatibility, and portability

Public interfaces and contracts should be understandable, change in a controlled manner, and have an explicit compatibility policy. Backward compatibility within stated commitments, or an incompatible migration described in advance, reduces uncertainty for consumers.

Compatibility and portability to another environment are separate quality aspects. Contract stability is useful, but supporting old versions creates long-term obligations and may slow cleanup. Consumer needs must be balanced against room for evolution.

### 1.13. Technical debt

Technical debt describes decisions and accumulated problems that can make future work more expensive. It may appear as repeated repairs, difficult upgrades, unpredictable change scope, delays, and growing maintenance effort.

Code smells, duplication, and structural violations can reveal potential problems but do not give a complete monetary estimate of debt. Debt cannot be defined solely through analyzer warnings, nor can every unattractive construct be considered economically harmful. Distinguish prevention cost, removal cost, subsequent expenses, and the risk that an area will never need changing.[^cunningham1992][^kruchten2012]

Empirical literature discusses the direction of the relationship between debt and cost, but this body of material establishes no universal function of time, size, or complexity. “Exponential cost growth” remains an unconfirmed hypothesis, not a law.[^besker][^tom2013][^lehman]

### 1.14. Engineering-process outcomes

Lead time, delivery frequency, recovery time, and regression count help observe the process. Reference points include short time from an idea to production; this interval needs its own definition and must not automatically be equated with a particular DORA metric. Frequent changes alongside stable product operation may indicate manageable evolution. No measure replaces the others: quickly releasing defects and rarely releasing reliable but unwanted changes are different problems.

The reviews cite DORA survey data as possible support for a relationship between delivery practices and stability. These are correlational data; the materials identify no specific report editions or findings. Process metrics must not be turned into direct measures of an individual engineer's or architecture's quality.[^dora]

### 1.15. Reconciling criteria

These properties are partly related and sometimes conflict. Low coupling may ease modification, while extra interfaces complicate understanding; compatibility helps consumers but constrains cleanup; more checks cost more to maintain; optimization can reduce readability.

An operational definition of quality requires a desired outcome, its measurement conditions, and an acceptable compromise. Priorities depend on criticality, load, product lifetime, customer expectations, and team capabilities. Reliability and recovery particularly matter in critical systems; security in systems with sensitive data; cost and reversibility of change in rapidly changing products. These examples distinguish priorities without excluding other properties.

## 2. How decisions connect to properties and outcomes

The following table describes mechanisms worth testing in a particular system. It does not equate a professional explanation with a proven effect size.

| Decision or practice | Intermediate property | Expected outcome and limitation |
|---|---|---|
| Define modules around meaningful boundaries and design APIs | More localized dependencies, high cohesion, explicit contracts | Fewer affected components and easier impact analysis; excessive fragmentation adds transitions and interfaces |
| Consolidate genuinely shared logic | One implementation of a shared rule | A fix propagates from one place; false commonality couples scenarios that should evolve independently |
| Temporarily retain local duplicates | No premature shared layer; copies remain visible | Easier understanding of an individual scenario, but coordinated changes must be tracked and other copies not forgotten |
| Refactor and remove obsolete parts | An evolving structure with fewer unnecessary layers | A way to contain complexity; moving code and reducing metrics do not themselves prove fewer defects or cheaper maintenance |
| Build substantive unit, integration, and smoke checks and include them in CI | Fast feedback on important scenarios and regressions | More grounds for safe change; effects depend on oracles, scenarios, requirement stability, and infrastructure cost |
| Apply TDD | Expected behavior checked before implementation, earlier feedback | Fewer prerelease defects in some industrial cases at additional effort; average effects and conditions vary |
| Conduct code review and use static analysis | Suspicious-code detection, discussion of decisions, adherence to conventions | Opportunities to find problems before release and transfer knowledge; interviews about a practice's popularity do not establish its causal effect |
| Use types, contracts, and invariants | Some invalid states and operations represented in the model or detected by checks | Prevention of certain error classes, including at build time; the type system does not replace domain-logic checks |
| Design diagnosis, monitoring, and recovery | Visible state and failure causes, controlled recovery | Opportunities for faster localization and less downtime; actual results need checking |
| Reuse a library, service, or internal component | Less custom implementation but a new external dependency | Possible development and testing savings alongside obligations for versions, integration, and maintenance |
| Preserve replacement boundaries, compatibility, and migration paths | Easier localization, rollback, or gradual replacement of a decision | Lower risk of an expensive revision; extra layers must be justified by the dependency's nature |

Some relationships are supported by reviews of metrics and external quality, some by cases, and some remain a professional model. A statistically nonsignificant relationship between metrics and **code-size growth** is not an absence of association with **change cost**; a positive complexity–defect relationship does not prove complexity itself was causal independently of size. The measured object must be preserved whenever a conclusion is transferred.[^jabangwe2015][^shepperd1988][^landman2016]

Growth in duplication, absence of refactoring, quality, and technical debt also differ. GitClear measures code changes through its own proxies; shifts in those proxies do not directly establish more errors, higher maintenance cost, or AI's causal effect.[^gitclear2026]

## 3. Observable behavior of strong engineers

Here, “strong engineer” is a behavioral model, not a career title. The described actions aim to understand the task, reduce uncertainty, and preserve a system's ability to change. Some practices have empirical support; many have only experience, a proposed mechanism, and professional consensus. Repetition of a recommendation across industry does not make confirmations independent.

### 3.1. Establish the problem and context first

Before making a change, the engineer examines code and architecture, commit history, issue reports, diagrams, and current constraints. They determine why the current behavior arose, what has already been tried, and which solutions exist inside the system. Alongside the task wording, they clarify business logic, nonobvious requirements, and success criteria.

The observable result is a change connected to an established problem, with an explainable scope. The expected benefit is fewer unnecessary changes, repeated mistakes, and rework. The cited studies do not separately measure the exact long-term cost effect of studying context.

### 3.2. Compare an existing solution with a custom implementation

When a new need arises, the engineer checks internal components, libraries, frameworks, and services that already address similar tasks. They assess requirement fit, maturity, testing, support, and dependency cost. An existing implementation is a preferred candidate when it fits and its maintenance is acceptable; matching functionality does not create an obligation to add a package.

Custom code is justified by specialized requirements, an awkward external solution model, unacceptable constraints, or dependency cost. Rejecting an existing component must also account for future maintenance, not merely how easy the first version is to write. Blind copying and undocumented assembly of libraries can leave the team unaware of its obligations.

### 3.3. Design boundaries and explicit contracts

The engineer defines component responsibilities, minimizes unnecessary dependencies, and makes implicit agreements visible through APIs, types, invariants, or documentation. When making a change, they assess affected consumers and whether consequences can be localized.

The aim is predictable evolution of system parts. Simply increasing the number of small classes, interfaces, or services does not achieve it: deep hierarchies and extra transitions can make navigation harder, particularly for newcomers.

### 3.4. Introduce an abstraction for a justified need

Several real consumers, repeated logic, a stable shared rule, repeated similar fixes, and identical errors in several places are signals favoring a shared abstraction. Two or more consumers may be used as a practical heuristic, not a scientifically established or mandatory threshold.

A clear shared concept and the need to isolate an expensive technological or architectural choice can also be sufficient grounds. In that case, the benefit must be explained through a concrete contract, change boundary, or replacement risk. A hypothetical capability with neither visible consumers nor a material boundary provides weak grounds for a new layer.

### 3.5. Handle duplication deliberately

If similar areas serve different purposes or may evolve independently, the engineer may retain local implementations. They make duplication visible, leave a comment or TODO where appropriate, and track change consistency. Stable, critical shared logic is a stronger consolidation candidate.

Intentional divergence between copies and a forgotten update to one copy are different situations. Clone data show the risk of unintentionally inconsistent changes; they do not imply that team awareness removes every possible harm from duplication. Codebase size, copy count, and likelihood of repeated fixes remain important conditions.[^juergens2009]

### 3.6. Prepare for likely changes without implementing imaginary features

The engineer distinguishes a specifically expected change from an undefined future wish. They may reduce coupling, leave a clear replacement boundary, or choose a data structure with likely scenarios in mind without implementing those scenarios in advance.

They also distinguish a one-off local fix from a fundamental contract change. System lifetime, change frequency, and the cost of later revision matter. The materials identify no direct studies of exactly how developers anticipate requirements and with what effect.

### 3.7. Make risky changes incremental and reversible

A large task is divided into steps with observable intermediate results. Risky functionality may call for feature flags, controlled rollout, a way to disable it, and a rollback plan. An expensive replacement may call for a prototype, migration, and temporary access to the earlier option.

Reversibility is a selection criterion, not a promise that every change can be undone painlessly. Public APIs, data, platforms, and organizational commitments create inertia. The materials give no universal quantitative estimates of the benefit of “rollback points.”

### 3.8. Use tests as evidence of correctness

The engineer chooses checks that can detect an important error, not merely execute a line. Priority goes to complex areas, critical business scenarios, API boundaries, and security. Unit, integration, and smoke tests, manual checks, and CI are chosen to match the task and risk.

A passing build is useful but insufficient evidence that the product is correct. The oracle's meaning is also checked: does a test reproduce the faulty implementation, and does it test important behavior? Maximum coverage at any cost is not the aim; a large, expensive suite can slow change when requirements are unstable.

### 3.9. Use types and invariants with an understanding of their limits

Type systems and contracts help express valid states and prevent certain error classes before operation. The engineer uses them in data models and APIs, while separately checking business-rule meaning, external data handling, and whole-system behavior.

Strict typing, formal specification, or a chosen framework does not guarantee freedom from all defects. The materials contain no comparative evidence for declaring one language universally best for long-term maintainability.

### 3.10. Build diagnosis into development

The engineer determines in advance how to detect a failure, connect events, and localize its cause. Logs, metrics, traces, and recovery mechanisms accompany functionality. After release, expected behavior is compared with operational data.

This complements testing: some conditions become visible only through actual use. The benefit of observability is an engineering recommendation here; the reduction in downtime depends on the system and is not established by the cited works.

### 3.11. Use analyzers and review to find particular problems

Linters and static analyzers help find suspicious constructs, potential defects, and code smells. Complexity, duplication, maintainability, and old-code-change metrics are useful for tracking trends and identifying areas to examine. The number of “hotspots” with repeated defects can be tracked as another indicator requiring analysis.

The engineer investigates warnings, conducts review, and compares measures with actual difficulties. Neither a maintainability index nor warning count replaces understanding the code. Interviews reporting that teams value review and standards describe practice; estimating how much those practices reduce defects requires separate research.[^bogner2019][^mcintosh2014][^bacchelli2013]

### 3.12. Maintain structure and remove obsolete material

Refactoring clarifies responsibility, improves naming, extracts genuinely shared logic, and removes unnecessary abstractions. “Hot” areas with recurring problems receive attention; important changes come with comments, explanations of intent, and appropriate method annotations.

Attention must extend beyond new code to the old core. Moved-code metrics, *legacy refactoring*, and *long-term update percent* may indicate the character of work on it, but these include GitClear's proprietary measures, not a generally accepted architecture-health scale. Refactoring carries risk and cost; polishing an area soon to be removed may not pay off.[^gitclear2026]

### 3.13. Transfer knowledge and account for team structure

Discussion of decisions, code review, documentation, joint code navigation, and teaching less experienced colleagues reduce dependence on particular people's hidden knowledge. Alignment between team responsibilities and component boundaries should be examined together with architecture; this relationship is discussed in terms of Conway's Law.

Communication problems may accompany debt accumulation, as described in one large microservice case. This does not support the original broad claim about “many surveys” when those surveys are unnamed, nor does it permit automatic transfer to every project.[^borowa2025]

### 3.14. Learn from incidents

After a serious failure, the team examines causes, tests earlier assumptions, and changes practices, tooling, or system structure. Histories of data loss, unavailability, or difficult diagnosis inform subsequent decisions.

The value lies in changed behavior and the ability to prevent or detect a similar problem sooner. Merely holding a postmortem does not prove improvement; the materials provide no quantitative effectiveness estimates for this pattern.

All these actions can backfire when overapplied: endless research delays decisions, early generalization creates complexity, excessive documentation requires maintenance, and continual postponement of improvement entrenches expensive constraints. The practical model requires actions proportionate to risk and expected benefit.

## 4. Conflicting principles and conditions for choosing

Engineering principles are useful reminders of different costs. A choice needs conditions under which one side wins, signals for reconsideration, and the costs of both extremes. System scale, requirement maturity, product lifetime, criticality, team experience, and customer expectations matter more than literal adherence to slogans.

### 4.1. KISS and preparing for extension

A simple solution speeds work today and reduces cognitive load. An excessively rigid structure may obstruct likely extensions. Conversely, a complex universal scheme creates expenses even if the expected need never materializes.

A prototype, small MVP, or unclear requirements gives stronger grounds for keeping implementation simple. Well-supported load growth, new data types, or module connections can justify preparing the relevant boundaries. Repeated similar requests and changes signal a need for generalization. Rapidly changing requirements may, conversely, justify postponing broad abstraction until the shared model becomes clearer.

A working compromise is a simple implementation with a clear path to change. One extreme requires a complete rewrite for a minor extension; the other produces multilayer patterns for a single case.

### 4.2. YAGNI and preparing for likely changes

YAGNI warns against implementing functionality not yet needed. Preparing for change may be different work: a clear boundary, an understandable contract, moderate modularity, or the ability to replace a dependency.

A class hierarchy for an unconfirmed feature has weak grounds. Near-certain support for new data types or an expensive future migration gives stronger grounds for preparing the structure. In long-lived and critical systems, revision cost can justify extra work; in an early product, uncertainty more often makes it risky.

Ignoring YAGNI produces unused capabilities. Turning it into a prohibition on all design can produce expensive rework. Lehman's laws do not prove that delayed preparation causes specifically exponential cost growth.[^lehman]

### 4.3. DRY and the wrong abstraction

Consolidating the same logic reduces the number of places needing coordinated fixes. But superficial code similarity does not guarantee shared semantics. If scenarios should develop differently, premature consolidation creates a fragile shared dependency.

Signals favoring DRY include a stable shared rule, repeated identical defects, and the same changes in several places. Signals against consolidation include different purposes, diverging requirements, and many special conditions inside the shared component. Deliberate temporary duplication leaves room to identify the right commonality later; uncontrolled copying creates a “propagation tax” on fixes.

Two or more consumers are a useful guide, not a mandatory threshold. Retained duplicates and their rationale should be visible; the risk of unintentionally inconsistent change differs from deliberate divergence.[^juergens2009]

### 4.4. Shared abstraction and local code clarity

This tension extends beyond eliminating repetition. A shared model may organize scenarios and hide details while making the reader navigate across layers. Specific code may be easier to understand in place even when longer or partly duplicated.

The choice depends on the shared concept's stability, expected consumers, and which changes should happen together. A useful abstraction clarifies meaning; abstraction for interface count, deep hierarchies, or formal pattern compliance increases navigation cost. A new consumer is not automatic proof that the existing shared layer was chosen correctly.

### 4.5. Reuse and dependency cost

An existing component may save development, testing, and maintenance of a custom implementation. It also creates obligations around versions, compatibility, licenses, SLAs, upgrades, and the end of support.

Assess component maturity and reliability, task fit, the nature of external changes, and the team's ability to maintain the integration. Retaining old versions may entrench vulnerabilities and obstruct upgrades; constantly chasing new ones may make maintenance a continuous migration. A major framework API change may require substantial rework.

One extreme rewrites solved problems without cause. The other adds packages without understanding transitive dependencies or consequences of disappearance. The left-pad incident shows such a failure is possible, not that dependencies are disadvantageous on average or that their count alone determines risk.[^leftpad2016]

### 4.6. Encapsulation and transparency

Hiding details permits module internals to change independently of consumers. However, absent observable states and diagnostic facilities make interactions hard to understand.

A stable external contract and sufficient diagnosis are needed. Physical separation into services does not automatically solve the issue: misaligned team and architecture boundaries can create additional communication and debt problems. This is described in one industrial case, not established for all distributed systems.[^borowa2025]

### 4.7. Stability, backward compatibility, and evolution

Supporting an old API protects existing consumers but requires preserving constraints and old execution paths. Cleanup and removal of obsolete material may ease evolution while breaking integrations and user trust.

Compatibility has particular weight for systems with critical customer obligations, for example in banking or medicine. A young product with a small customer base may allow faster revision. Specific obligations, not merely company age, determine the choice.

Reconsideration signals include the cost of supporting old contracts, availability of a migration, and prevalence of consumers. Preserving everything too long entrenches awkward architecture; removing compatibility too early transfers costs to users.

### 4.8. Small changes and major architectural work

Small changes are easier to check and provide early feedback. But repeated local workarounds can cost more than revising a fundamental contract.

The same change repeated across components, a long-delayed critical-module migration, or a blocking framework version can justify a separate architectural task. A genuinely local change does not justify automatically extending scope to the whole system.

A large design goal and gradual rollout are compatible. Some work can accompany ordinary development; some should be planned separately according to the roadmap and risk. Postponing an upgrade for years may make the transition painful, but this is a mechanism and practical observation, not a universal quantitative relationship.

### 4.9. Release speed, process rigor, and technical debt

A shortcut may accelerate the next release while creating future costs. Additional design, checks, and review cost time now and may reduce later risks. The Cycle.io vendor blog describes this tradeoff; earlier conceptual sources on technical debt are Cunningham and Kruchten, Nord, Ozkaya.[^cycle][^cunningham1992][^kruchten2012]

Reasonable rigor depends on risk: a critical change requires closer scrutiny; a simple reversible change needs less process. An early product needs speed in testing demand, while a critical system needs a stable foundation. CI automation, allocated refactoring time, separate debt tasks or sprints, and observation of consequences may help manage the balance.

Constant haste entrenches problems; endless polishing may prevent a timely launch. TDD's 15–35% time increase refers to estimates by managers of four teams, not a universal price of quality.[^nagappan2008]

### 4.10. Checks and the cost of test infrastructure

Tests require environments, maintained frameworks, data, execution time, and updates as requirements change. A small or rapidly changing product may not justify the broadest possible set of checks from the start.

A practical approach is to cover critical scenarios, integration, and basic operation, expanding checks as risk and requirement stability grow. This is neither a universal test pyramid nor a justification for omitting necessary checks. The break-even point for different investments in tests and infrastructure across system classes remains unknown.

### 4.11. Coverage percentage and oracle quality

High coverage may coexist with checks of unimportant details. Low coverage may leave dangerous scenarios untested. Oracle quality and scenario selection are needed independently of a percentage target.

A check's meaning is harder to measure automatically than executed lines. Coverage is therefore a convenient proxy but does not independently justify calling a system high-quality. The supplied data do not resolve “100% of all code” versus “80% of the core”; risk and the tests' ability to expose important errors should guide the choice.

### 4.12. Performance and maintainability

Optimized loops, manual buffer management, and complex caching can reduce readability. An excessively slow implementation, however understandable, can violate product requirements.

An optimization signal is a measured bottleneck or a specific hard constraint: a game's frame budget, financial-event processing time, or load. Possible ways to reduce costs include profiling particular areas, isolating “hot” code, retaining an understandable version as a comparison and default, or allowing replacement of an optimized implementation—for example through a plugin for “hot” code. Maintaining two versions also has a cost.

The extremes are a hard-to-debug system pursuing an unimportant gain and refusing to consider performance until the product becomes unusable. Knuth's statement about premature optimization already discussed the critical 3% of code; it does not rule out optimizing measured bottlenecks.[^knuth1974]

### 4.13. Standardization, local suitability, and experimentation

Shared conventions ease cross-project work and knowledge transfer. A particular task may justify departing from the common standard or trying a new approach.

Deviation needs an explainable task benefit and assessment of maintenance consequences. Formal uniformity must not replace a suitable solution; uncoordinated local freedom must not create unjustifiably different ways to do the same thing.

### 4.14. Documentation and its maintenance cost

Documentation helps preserve intent, obligations, and context that code alone cannot easily reconstruct. More text does not guarantee usefulness and requires updates.

Clear code and meaningful tests can be more useful for some tasks than detailed restatements of implementation. Yet they do not always replace an architectural rationale, the reason for a constraint, or a migration plan. No universal minimum documentation volume is established; company guidance may serve as a reference point, not proof of an optimal document count.[^microsoft-playbook]

## 5. Decisions with a high cost of correction

Some choices spread across many system parts and create long-term obligations. Their cost includes not only new code but migration of data, consumers, infrastructure, and the team.

| Category | Why later revision can be expensive |
|---|---|
| Architectural style and module boundaries | Monolith or services, layers, synchronous or asynchronous interaction determine relationships and operating methods; revision affects several components |
| Data and representation | Relational or NoSQL models, table schemas, denormalization, and message formats require migrations and data-integrity checks |
| Public APIs and fundamental contracts | Compatibility affects external consumers and the ecosystem; removing a version or changing operation semantics can break integrations |
| Language, platform, and core frameworks | Replacement affects the codebase, tools, team skills, and operations; changing CI/CD or cloud infrastructure also creates costs |
| External systems and foundational libraries | Third-party APIs, a particular DBMS, and key packages become part of product constraints and lifecycle |
| Security and compliance | Authentication, encryption, data isolation, and access models affect multiple layers; late redesign requires checking the whole boundary |
| Organizational boundaries | Team responsibilities and interactions affect architecture; revision may require code, process, and team-structure changes |
| Diagnosis and observability | Adding logs, metrics, and event collection to an already distributed system can affect many components |
| Test infrastructure and CI/CD | Initially omitting environments and automation reduces startup work, but adding them later in a large project can become a major task |

For critical security areas, the recommendation is to involve specialists and conduct an audit early in design. This is a list of risk categories and professional actions, not a proven universal cost scale. For example, designing security early is consistent with *security by design* and *shift left*, but the materials do not measure the relative cost of fixing vulnerabilities late.

For expensive decisions, the professional model calls for:

1. **Investigating alternatives.** Examine related implementations, technological maturity, community, limitations, operations, and migration availability. Conduct an architectural or design review and prepare a prototype or proof of concept for material uncertainty.
2. **Clarifying the choice boundary.** Where possible, isolate a replaceable technology or policy through a suitable module, contract, or layer. Here, revision risk can justify abstraction even without several current consumers.
3. **Recording the grounds.** Preserve the architectural decision, constraints, and rationale as an ADR or another understandable document; future teams need the reason, not only the outcome.
4. **Planning the transition.** Consider API versioning, schema migrations, tests, intermediate states, and consumer operation. For database replacement, consider backups and temporary access to the old option; for platforms, checking in a parallel environment.
5. **Rolling out with feedback.** Divide the transition into verifiable stages, use canary releases and feature flags where suitable, observe real outcomes, and have a failure-response plan.
6. **Separating the design goal from delivery scale.** An architectural task can be large in purpose and gradual in implementation; local patches cannot indefinitely substitute for a necessary revision.

Canary releases, feature flags, and continuous delivery are widely recommended in practice. The materials contain no systematic study measuring a universal reduction specifically in **correction cost** from these mechanisms. The cited DORA evidence concerns correlational relationships between delivery practices and stability.[^dora]

The organizational dimension requires the same care in attribution. Borowa's case connects insufficient communication and misaligned boundaries with debt. It cannot be credited with proving “frequent service co-evolution” and “extreme difficulty in recreating their boundaries”: those findings are not present in the checked excerpts.[^borowa2025]

## 6. Empirical results, cases, and transfer boundaries

The following sections preserve samples, numerical results, counterevidence, and the actual scope of verification. A systematic review, interview, incident, vendor statistics, and hypothetical example answer different questions; they must not be pooled as equally strong independent confirmations.

### 6.1. Object-oriented metrics: associations with quality and generalization limits

The systematic review by Jabangwe, Börstler, Šmite, and Wohlin combines **99 primary studies** of associations between object-oriented metrics and external quality attributes. It appeared in *Empirical Software Engineering*, 20(3), in **2015**, following online publication in **2014**. In the supplied review, the study count and main results were checked **from the reviewer's memory; the primary source was not opened**. This limitation also applies to the account below.[^jabangwe2015]

According to that assessment, measures of **complexity, cohesion, coupling, and size** are associated with reliability and maintainability. The studies primarily concern **long-lived object-oriented Java and C++ systems**; associations were examined at class level, and external outcomes through defects and change effort. The materials assign moderate confidence to the overall direction of association. These observations support structural metrics as indicators of possible problems, but do not establish a universal causal formula in which reducing a metric by a specified amount yields a specified maintenance saving.

For **DIT and NOC**, which characterize inheritance, the association with quality is described as **weak and contradictory**. Inheritance depth or the number of descendants therefore cannot on their own support confident judgments of defectiveness or maintainability. This does not prove every hierarchy harmless: excessive inheritance may burden a particular system, but neither an exact threshold nor a universal effect size is established.

Study count does not automatically reveal the independence of data, methods, or conclusions. Correlational results at class level cannot be transferred to every language, architecture, or domain without additional checking. Transfer to embedded, scientific, and short-lived systems is particularly uncertain. The practical explanation through locality of change remains useful: clear boundaries should mean fewer affected components. Yet change cost, system-size growth, defect count, and subjective code understanding are different outcomes; evidence about one does not replace measurement of another.

### 6.2. Cyclomatic complexity, code size, and defects

A positive correlation between cyclomatic complexity and defects is described, but a substantial part may be explained by code size: larger fragments offer more opportunities for both branching and errors. The review considers this cautious interpretation supported by the literature and identifies **Shepperd (1988)** and **Landman, Serebrenik, Bouwers, and Vinju (2016)** on the strong relationship between cyclomatic complexity and SLOC.[^shepperd1988][^landman2016]

Cyclomatic complexity is therefore useful as a signal for investigation, but the correlation does not establish its independent causal contribution to defects. Lowering the metric is not a proven reduction in change cost or errors. Code size, the nature of changes, and the applicability of the comparison require separate consideration; these materials yield no universal threshold of “bad complexity.”

**Verification scope:** the literature and direction of association were identified by the reviewer **from memory, without opening the publications**. Exact titles, quantitative coefficients, and data for estimating a distinct effect are absent from the supplied account.

### 6.3. Code understandability: Lavazza's findings and a subsequent replication

Lavazza, Morasca, and Gatto's *An empirical study on software understandability and its dependence on code characteristics* (*Empirical Software Engineering*, 28, **2023**) investigated how well code characteristics predict understandability. Participants were **students** performing maintenance tasks on **methods from open-source projects**; understandability was measured through **time to correct task completion**. The review states that the **abstract**, not the full paper, was opened.[^lavazza2023]

Models using **one or two code metrics** had an average prediction error of **around 30%**. This is the understandability model's error, not the proportion of defective code, percentage of unintelligible programs, or improvement from an engineering practice. The reported result suggests structural metrics are insufficient for a reliable understanding model; **Cognitive Complexity did not substantially improve it**. Cyclomatic or cognitive complexity, size, and similar measures may therefore flag areas for attention, but cannot replace checking how people actually read and modify code.

A replication by **Kapitsaki, Lavazza, Morasca, and Rotoloni, ENASE 2025**, using **the same code**, did not confirm correlations between metrics and understanding. Its abstract was also opened during review. The replication adds counterevidence to the associations' stability, but the shared material means it is not a fully independent check on another codebase.[^kapitsaki2025]

The limits matter. Student tasks on individual methods do not automatically cover an experienced team's work on architecture, a user interface, or a distributed system. Documentation was not measured; transfer to GUI and other activities is unjustified. The supplied details do not include full participant sample size or intervention thresholds for particular metrics. Moderate confidence that structural metrics are insufficient must therefore be distinguished from claiming such metrics never correlate with anything.

The abstract's opening statement that poor understandability obstructs maintenance and is a major cause of development cost is the **motivation**, not a separate experimental result of the study. Semantic tests, documentation, and observation of task performance can provide other information about a system; numerical test coverage is likewise not a direct understandability measure.

### 6.4. Naming and identifiers' share of code

Deißenböck and Pizka's *Concise and consistent naming* (Software Quality Journal, 2006) proposes concise, consistent naming rules. As the review clarifies, its starting estimate is that identifiers account for **around 70% of source-code characters**, counted in **Eclipse**.[^deissenboeck2006]

This figure characterizes identifiers' share in one codebase. It does not mean identifiers occupy 70% of lines, that every software project has the same share, or that good naming reduces cognitive load by 70%. **The work did not measure a quantitative reduction in cognitive load.**

The practical role of concise, consistent naming in code understanding is retained. The character share helps explain the attention paid to naming, but does not numerically predict reading time, newcomer adaptation speed, or errors prevented.

**Verification scope:** the publication's content, measurement unit, and Eclipse example were clarified by the reviewer **from memory, without opening the work**. The mistaken unit and conversion of identifier share into effect size should be treated as corrected wording, not repeated as findings.

### 6.5. Code clones: whether inconsistent changes are intentional

Juergens, Deissenboeck, Hummel, and Wagner's *Do code clones matter?* (ICSE, 2009) examines duplication in industrial and open-source systems. Its key distinction is **intentional versus unintentional inconsistency in clone changes**. According to the supplied review, approximately **every second unintentionally inconsistent change** produced a defect. Intentionally inconsistent changes generally were not defects.[^juergens2009]

This explains why similar-looking fragments cannot be assessed solely through textual similarity. A developer may deliberately change one copy when its purpose or expected behavior differs. Another case is fixing a fragment without knowing an analogous fix is needed elsewhere. The latter creates a risk of missing a coordinated change.

The practical conclusion is to account for relationships between copies, shared semantics, and change intent. Awareness of duplication, explicit comments, and tracking related fixes support a deliberate choice. The finding does not guarantee known duplicates are safe, that defect probability is always zero, or that all duplication should immediately be eliminated. “Approximately every second” concerns the studied **unintentionally inconsistent changes**, not all clones or all code changes.

Reducing size or metrics must also be distinguished from improving maintenance. The review describes reduced LOC and cyclomatic complexity after removing repetition as consequences of counting those metrics, not as a separate empirical result of this study. Claims of lower intermodule coupling, cognitive load, or human error need their own grounds; they cannot automatically be attached to clone-inconsistency findings.

**Verification scope:** attribution, the intent distinction, and approximate defect proportion were reconstructed by the reviewer **from memory, without opening the publication**. This also corrects a Wikipedia-based retelling that mistakenly named Wagner as first author and lost the decisive distinction between the two kinds of inconsistency.

### 6.6. TDD in four industrial projects

Nagappan, Maximilien, Bhat, and Williams describe test-driven development in four industrial teams: three at Microsoft and one at IBM. *Realizing quality improvement through test driven development: results and experiences of four industrial teams* (2008) reports **40–90% lower prerelease defect density** than in comparable non-TDD projects. Managers simultaneously estimated a **15–35% increase in development time**.[^nagappan2008]

These results concern a specific practice: writing a test before implementation, then making the code pass it. The quality measure is prerelease defect density; it cannot automatically be extended to all operational errors or long-term maintenance cost. The time measure is **managers' expert estimates**, not an objectively measured effect in a controlled experiment.

The study is a case study: there was no randomization, comparison projects were selected as comparable, and the teams had experienced developers. Broad ranges reflect heterogeneity between cases. The authors limited generalizability; Microsoft and IBM observations from the 2000s do not by themselves establish the same effect in other stacks, embedded software, beginner teams, or small short-term tasks.

The case supports tests as evidence of correctness and early feedback. Test infrastructure helps detect errors and supports later changes, but requires development and maintenance. Rapid requirement change can make that work slow early delivery. TDD data nevertheless do not determine an optimal test count, coverage percentage, or effect of arbitrary test-suite expansion.

**Verification scope:** bibliographic attribution, team composition, and numerical results were checked by the reviewer **from memory, without opening the paper**. This limitation also applies to these clarifications.

### 6.7. TDD meta-analysis: quality and productivity depend on conditions

Rafique and Mišić's *The Effects of Test-Driven Development on External Quality and Productivity: A Meta-Analysis* (IEEE Transactions on Software Engineering, 39(6), 2013) combines **27 studies**. The average result is a **small improvement in external quality**; the average productivity effect is **not statistically significant**. In industrial settings the productivity effect tends to be negative, while quality gains are larger.[^rafique2013]

The 40–90% defect reduction and 15–35% time increase from particular industrial cases are therefore not the meta-analysis's overall effect estimates. Its more restrained average must remain alongside the striking cases. A nonsignificant average productivity effect also does not mean TDD has no speed effect in every team: individual study results differ substantially.

Primary studies are heterogeneous across academic and industrial conditions, tasks, and assessment methods. Academic studies make up **approximately half the sample**; some find no significant effects. They cannot be reduced to a few inconsequential exceptions. Giving industrial observations greater relevance to industrial development is a legitimate contextual choice, but does not remove the other findings.

This meta-analysis is the strongest empirical support in the TDD discussion presented here. It supports a contextual approach: assess external outcomes, costs, and application conditions, and preserve the distinction between quality and productivity. It does not prove all testing always slows development, high coverage guarantees no errors, or TDD necessarily improves architectural design.

**Verification scope:** the work's content, study count, and effects were checked **from memory, without opening the publication**. “Approximately half” for the academic share is an estimate with the same verification limit.

### 6.8. SOLID: reported findings and partially located support

A **2018** work is attributed to Turan and Tanrıöver in which project code was restructured using SOLID and measured again. The account attributes reduced coupling and improved modifiability, flexibility, understandability, and reuse to it. It also reports increased class count and hierarchy depth, potentially making navigation harder and abstractions more costly. **The exact 2018 publication and these findings were not opened and checked.** They remain an account of a claimed case, not confirmed experimental results.[^turan2018]

In a targeted search, the reviewer found a related **2019** Ankara University dissertation, *Solid prensipleri ile bakım için yazılımı yeniden yapılandırma yöntemi*. Its description maps ISO 9126/25010 maintainability subcharacteristics to SOLID; **two large enterprise projects** were refactored and metrics measured with **Visual Studio**. Ö. Tanrıöver's association with Ankara University is consistent with the attribution, but the dissertation has not been established as identical to the cited 2018 publication.[^solid2019]

The design has material limitations: before/after comparison, refactoring by the authors, no control group, and two projects. Even verified structural-metric changes would require caution in inferring general causal effectiveness of SOLID or transferring to other systems. Here the specific results additionally remain unopened.

Substantively, the case illustrates the tradeoff under discussion: object decomposition may localize dependencies, but more classes and hierarchy levels cost understanding effort. It does not justify mandatory application of all SOLID, continually smaller classes, or universal abstractions for their own sake.

**Verification scope:** a **targeted search found a related source**. The 2018 publication and its specific findings remain **not checked by opening**. Independence of the support is low; reliability is assessed as low–moderate given design and incomplete verification.

### 6.9. Evolution of JHotDraw, Rhino, GLE, and FlightGear

Observations across release sequences support the view that long-lived software grows and becomes more complex. Persuasiveness depends on sample and checking method: a visual trend in a few systems, a statistical result across hundreds of releases, and a universal claim about change cost have different evidential strength. Code size, structural complexity, maintainability, and actual effort must especially be distinguished: change in one does not directly measure the others.[^johari2011][^kaur2014][^kaurvig2016]

**Johari & Kaur (2011)** studied two open-source Java systems, JHotDraw and Rhino. They measured object-oriented metrics, including size and complexity, across releases and concluded the observations supported laws of increasing complexity and continuing growth. The supplied account specifies **13 JHotDraw versions, 16 Rhino versions, and a 10-year period**. Metadata and the abstract were opened during review: the work's existence, subject, and general conclusion were confirmed, but these exact counts and duration were **not checked** against the full text. The attributed wording that adding functionality becomes “increasingly difficult” was not checked verbatim either.[^johari2011]

This is a descriptive trend analysis of two medium-sized open-source Java systems with no identified statistical tests. It appeared in ACM SIGSOFT Software Engineering Notes, **36(5)**; the review notes its research-note format and limited editorial selection compared with full peer review. The observed evolution is a useful example but cannot automatically be transferred to every architecture, language, or domain.[^johari2011]

**Kaur, Ratti & Kaur (2014)** studied the open-source C++ systems GLE and FlightGear. The abstract opened during review confirms **10 versions over 8 years** and the authors' conclusion that laws of continuous change, growth, and increasing complexity applied. The supplied description does not clarify how the ten versions were divided between projects. Like the preceding study, it is a descriptive analysis of two systems. It appeared in International Journal of Computer Applications, **93(18)**; the review characterizes the journal as having low selectivity.[^kaur2014]

These works cover different projects and two languages, broadening observational diversity. Their methodological independence is nevertheless **limited**: the 2014 study reproduces Johari & Kaur's method and cites it. Two publications therefore do not mean two fully independent checks. Given small samples, descriptive methods, and publication formats, **moderate confidence** in trends of growth and complexity under the observed conditions is justified. Any claim of no contradictions is valid only for the examples examined.[^johari2011][^kaur2014]

Broader checks give a less uniform picture. The review cites **Kaur & Vig (2016): 11 Java projects, 493 releases**, confirming only **3 of 8 laws**. Associations persuasive on charts may fail statistical tests. **Neamtiu et al. (2013)** is also named as a source of mixed results. Their status must be retained: Kaur & Vig was found by targeted search, but full-text reading is not claimed; no separate checking procedure is described for Neamtiu. These works show the need for counterevidence, but available information is insufficient to reconstruct findings for every law and test condition without the primary sources.[^kaurvig2016][^neamtiu2013]

This corpus's practical limit is long-lived open-source Java and C++ systems. The evidence does not establish transfer to embedded software, scientific or financial computation, critical real-time applications, or short-lived programs. Observing complexity growth also does not determine change effort, optimal refactoring frequency, or a universal cost-growth function.[^johari2011][^kaur2014][^lehman]

### 6.10. How microservice teams maintain evolvability

**Bogner, Fritzsch, Wagner, and Zimmermann (2019)** describe practices for microservice evolvability. Their sample includes **17 interviews, 10 companies, and 14 systems**; it concerns microservice teams **in Germany**. These parameters and the general conclusion were checked **from the reviewer's memory, without opening the publication**, and cannot be equated with full-text verification.[^bogner2019]

Participants reported relying on architectural guidelines, coding standards, and manual code review. Their tool and metric choices emphasized **source-code quality**: static analysis, code style, understandability, and maintenance. Specialized architecture-level tools were rarely mentioned. Manual review and refactoring were regarded as important for quality and team culture.[^bogner2019]

The word **“all”** for the interviewed teams was **not checked**, nor were the exact quotations about preferring code review and standards. The reviewer recalls wording about most teams, but that does not justify replacing one unconfirmed quantifier with another. The reliable formulation is the priority participants described for code quality and manual practices; exact prevalence and quotations require the publication.[^bogner2019]

This is qualitative, **descriptive** evidence. It shows which approaches teams value and use, but does not measure a causal reduction in defects, maintenance cost, or technical debt. It cannot yield a quantitative superiority of manual review over tools or automation over manual checks. Reported importance and an established effect on outcomes are different claims.[^bogner2019]

Support is assessed as **medium** for describing observed practice; transfer to other countries, architectures, or development types remains an assumption. The sample does not rule out teams emphasizing tests or documentation. It provides no systematic comparison with alternative styles, including different refactoring allocations. These alternatives limit generalization without negating the interviews.[^bogner2019]

### 6.11. Communication, team structure, and debt in a large microservice system

**Borowa, Ratkowski & Verdecchia (2025)** studied one industrial project with **more than 100 microservices**, serving **more than 15 thousand locations**. **30 key services** were analyzed in detail. The method combined static analysis using **SonarQube**, a team focus group, and interviews with the lead architect. The abstract and excerpts were opened during review; this is the most extensively checked support among the microservice cases presented here.[^borowa2025]

The study identifies four observations:

- **Simple static analysis is a useful starting point for debt detection.** It quickly locates some problems, but does not cover all important debt causes and forms.
- **Insufficient communication contributes to debt accumulation.** Organizational interaction was important in this system alongside code state.
- **Misalignment between architecture and organizational structure worsens debt.** Team boundaries and responsibilities must be considered when interpreting architectural outcomes.
- **Debt accumulates and is repaid quickly within individual services.** The team perceives it as service-local; *technical debt gamble* describes these rapid cycles, without literally claiming developers behave like gamblers.[^borowa2025]

The case exposes relationships between static indicators, social processes, and architecture. Multiple methods provide several forms of evidence about one system, but **do not create an independent sample of projects**: there is one industrial context and qualitative data from one team. Only thirty of over one hundred services were studied in detail, further bounding scope.[^borowa2025]

The results challenge the expectation that microservice separation alone ensures flexibility and cheap evolution. Yet the authors expressly frame the suggested greater susceptibility to **social debt** cautiously—*“we speculate”*. It is not an established comparative advantage or disadvantage of the architecture. Different outcomes in tightly centralized teams remain an alternative requiring separate data.[^borowa2025]

For this observation, evidence strength is **medium**, with applicability primarily to distributed teams and microservices. The materials give no independent analogous cases. The data support the importance of communication and boundary alignment in the described project but provide no quantitative function for their effect on future cost.[^borowa2025]

### 6.12. GitClear: code-structure changes and limits on conclusions about AI

GitClear's vendor report, *The Maintainability Gap / Write-Only Mode: AI Code Quality in 2026*, published in **June–July 2026**, describes repository changes. The review reports opening **the report page and coverage of it**. The corrected volume is **around 623 million changed lines (*code changes*) over 2023–2026**. Around **two thirds** of the data come from commercial GitClear customer repositories; the rest from large open-source projects.[^gitclear2026]

The following quantitative observations are reported:

| Measure | Result | Time reference and limits of the retelling |
|---|---|---|
| Share of moved code (*moved*), used as a refactoring indicator | **21% → 3.8%** | **2022 → first half of 2026** |
| Copy-paste share (*copy-pasted*) | **9.4% → 15.7%** | Described as part of the same trend; dates of the two points not separately disclosed |
| Block duplication | **+81%** | The review phrases it as **“+81% by 2023”**; the exact temporal wording needs primary-source clarification |

The main sample period, **2023–2026**, and the *moved* series' initial point, **2022**, must remain distinct. The data show a several-fold reduction in moved-code share and more copying, but cannot be retold as measured deterioration of every software property.

GitClear uses proprietary measures: **moved, copy-pasted, churn, and duplication**. They are **proxies**, not directly measured defects, reliability, change cost, or team productivity. They depend on change classification; moved-code share does not represent all refactoring work. **Long-term update percent**, “forgotten code,” and **legacy refactoring**, used in discussion of old-layer updates, likewise belong to GitClear's methodology and must not be passed off as generally accepted indicators without definition. Formulas and required thresholds are absent from the supplied materials.

The report **has not undergone scientific peer review**, and its vendor has a commercial interest in code-quality analysis. Large observation volume does not remove dependence on customer-base composition and metric definitions. Several press articles about one report also do not create independent samples. Proxy changes may justify investigating future maintenance costs, but relationships with those outcomes were **not measured** in this report.

Attributing duplication growth specifically to AI assistants remains the **vendor's correlational interpretation**. The proportion of AI authorship and its independent contribution are not established in the reported results. Alternative explanations remain possible: **changes in customer-base composition**, **more junior developers**, and **build-tool changes**. The data should therefore remain preliminary observations of change structure with limitations, not proof of AI's causal effect on defects or maintainability. Distinguishing explanations requires studies that measure development outcomes and control accompanying factors; replications, longitudinal observations, and controlled experiments are possible approaches.

### 6.13. Technical debt, cost, and the limits of evolution laws

Technical debt is associated with future change and maintenance effort, but **debt and release delay are not synonyms**. Delay may be a consequence, not the definition of debt. Structural metrics and code smells likewise indicate potential problems rather than directly measuring expenditure or lost working time. The “debt → delays” relationship therefore needs its own evidence; one encyclopedic retelling cannot establish high confidence.[^besker][^tom2013]

As primary directions for checking this, the reviews identify **Besker, Martini & Bosch (2018–2019)**, on the share of development time lost to technical debt, and **Tom, Aurum & Vidgen (2013)**. They are sources to consult; the supplied materials do not describe opening them or verifying their results. A particular lost-time percentage, a full quantitative model, and comparable cost estimates are absent. This corpus cannot therefore be credited with an established “debt interest rate” or exact return on repayment.[^besker][^tom2013]

The reviews clarify that **Lehman's laws do not specify exponential change cost**. In the stated interpretation they concern continuing change, growth, and increasing complexity in E-type systems, including complexity growth without containment work. These are statements about evolution, not a formula for the price of every later change. The clarification itself was made from memory, without a described primary-source opening; specific observational checks were discussed above.[^lehman]

The exponential-cost proposition remains an **unconfirmed hypothesis**, requiring a measured variable and conditions. The review connects it to **Boehm (1976, 1981)** on defect-correction costs across lifecycle phases, and mentions challenges to that curve, including **Beck (1999)** and later reassessments. This attribution is also from memory. Phase-dependent defect-correction cost, codebase complexity growth, and architectural change effort over time are not one measured relationship.[^boehm][^beck1999][^lehman]

Empirical estimates of time lost to debt do not themselves establish an exponential curve. The exact effect on release timing, support cost, and development rate, and the balance between prevention and later removal effort, remain open. This corpus gives no basis for a universal refactoring frequency, one acceptable-debt threshold, or guaranteed gains from a particular coupling reduction. Such conclusions need code observations linked to real changes, effort, and context over long intervals.[^besker][^tom2013][^johari2011][^kaur2014]

### 6.14. Left-pad: one dependency-chain failure

On **March 22, 2016**, the author removed the **11-line** `left-pad` package from npm. It belonged to transitive dependency chains, and its removal broke builds in projects using related tools. npm eventually restored it against the author's wishes.[^leftpad2016]

**Babel and React** are associated with the incident. During review, the reviewer separately confirmed from memory that broken chains affected Babel tooling; React's role was not separately checked. **Facebook, Netflix, and PayPal** were mentioned in contemporary press as users of affected tools. Those mentions must not become claims of independently confirmed production failures at each company.

**“Thousands of projects”** conveys a press-reported order of magnitude, not an exact measured total. Inability to build or deploy concerns the disrupted supply chain; it does not mean every already-running application instance simultaneously stopped serving users.

The case illustrates dependency cost: little borrowed code does not guarantee little system risk. Component support, supply stability, and position in the dependency chain matter when assessing reuse. But **one incident provides no statistical failure-probability estimate**, establishes no safe package count, and does not prove custom implementations are better on average. Many teams successfully use dozens of dependencies; the claim that experienced teams necessarily limit their number is not independently supported here.

**Verification scope:** date, package size, incident mechanism, and restoration were checked by the reviewer **from memory, without opening sources**. Company names and approximate scale refer to contemporary press accounts. Applicability is bounded by a specific npm ecosystem incident in 2016.

### 6.15. Unconfirmed observations and bounded illustrations of evolution

Several stories help explain engineering mechanisms, but their evidential status is much weaker than the studies listed above.

**JabRef, Lucene, and other open-source projects.** Claims of satisfactory maintainability over many years with an active community, and of a correlation between regular duplicate removal/refactoring and fewer errors, could not be tied to a particular study. Nor was an analysis identified in which coupling/cohesion had no statistically significant association with **code-size growth**. That result cannot be treated as established counterevidence to a general modularity–quality relationship without its source; even if verified, it would principally concern size growth. The claims remain **unchecked**, together with the absence of a resolvable bibliographic reference.

**Google and Netflix.** Continuous integration, code review, static analysis, and detailed logging are given as corporate examples of supporting reliability. Specific publications, quantitative effects, and evaluation designs are unnamed. This supports experience and recommendations for large teams, not an independently verified measurement; effects may depend on skills and organization and be difficult to isolate numerically. Netflix chronology is separately corrected: from the reviewer's memory, **Chaos Monkey appeared around 2010–2011 during cloud migration**, years after streaming launched. It was part of subsequent architectural evolution. Its specific effect on high availability remains an illustration, not an established causal relationship.[^google-netflix]

**A hypothetical banking system.** In the illustration of a system developed over decades, poorly designed APIs cause nonlocal changes as requirements grow. By the end of the described lifecycle, wrappers around old services and a microservice facade preserve existing interfaces while slowing evolution and freezing some capabilities. The mechanism shows compatibility cost: continued operation can constrain flexibility. The bank has no identifying details or documented source, so the story is not a confirmed case.

**A hypothetical migration after prolonged deferral.** Unupdated components and accumulated old layers can make a one-function repair depend on major rework. The illustration describes repayment of accumulated debt through prolonged crisis releases even in a previously successful project. Neither project nor measurements are identified; the story yields no universal rate of cost growth. In particular, **exponential cost growth** remains only an **unconfirmed hypothesis**.

A successful migration or use of microservices does not prove an architecture universally effective. Canary rollouts, feature flags, parallel testing, and rollback plans remain practically justified ways of limiting change consequences; the supplied materials contain no systematic study measuring correction-cost reduction from these individual practices.

## 7. An integrated evidence matrix

Assessment concerns a particular conclusion, not author prestige or mention count. A large sample does not eliminate measurement error; multiple methods in one project do not make it multiple independent cases; a metric's popularity does not prove validity. Primary-source verification status is stated separately from research-design quality.

| Claim | Support and data type | Justified assessment | Main boundaries and contrary evidence |
|---|---|---|---|
| Structural OO metrics are associated with external quality attributes | Jabangwe: systematic review of 99 studies | Moderate for correlation direction; information checked from memory | Mainly Java/C++, class level; causal change savings and universal thresholds not established |
| Inheritance predicts quality | DIT/NOC in the same review | Weak and contradictory associations | A system cannot be assessed solely by hierarchy depth or descendant count |
| Structural metrics adequately describe understandability | Lavazza 2023 and 2025 replication | Data support the limits of such models; abstracts opened | Around 30% error, no substantial Cognitive Complexity improvement; replication does not confirm correlations; students and individual methods |
| Cyclomatic complexity independently explains defects | Shepperd; Landman and colleagues | Limited support; information from memory | Strong code-size association makes the independent effect hard to isolate |
| Long-lived software grows and becomes more complex without containment | Johari & Kaur; Kaur, Ratti & Kaur | Moderate under observed conditions | Two systems each, descriptive methods, limited independence; Kaur & Vig and Neamtiu give mixed findings |
| Shares of moves, copies, and duplicates changed | GitClear 2026 | Reported proxies corroborated through an opened page | Vendor method; defects, costs, and AI's causal effect were not measured |
| Technical debt increases cost and delays | Encyclopedic retellings; Besker and Tom proposed | Universal strength and effect size not assessed through primary studies | Wikipedia provides no independent confirmation; debt cost is not a complexity metric |
| TDD reduces prerelease defects | Nagappan: four industrial teams | Substantive but limited support; checked from memory | 40–90% relative to selected projects, no randomization; managers estimated +15–35% time |
| TDD improves quality and affects productivity | Rafique & Mišić: meta-analysis of 27 works | Strongest support on this topic; content checked from memory | Small average quality gain; no significant average productivity effect, more often lower in industry; approximately half the studies academic |
| High coverage guarantees effective tests | Reviews identify Inozemtseva & Holmes | Guarantee unjustified; work named as additional support | Coverage, oracle quality, infrastructure, and TDD differ; no universal coverage → missed-defects curve |
| Duplication always increases defects | Juergens and colleagues, code clones | Contextual empirical support; checked from memory | Unintentional inconsistency is critical; deliberately different changes generally were not defects |
| Consistent naming has a numerically known effect on understanding | Deißenböck & Pizka | Practical recommendation without a measured load reduction | 70% is identifiers' character share in Eclipse, not improvement size |
| SOLID necessarily improves maintainability | Claimed 2018 publication; related 2019 dissertation | Low–moderate support; specific findings unopened | Two projects, before/after, no control, author-performed refactoring; metrics are not long-term outcomes |
| Teams rely on code quality, review, and standards | Bogner: 17 interviews, 10 companies, 14 systems | Medium for practice description; checked from memory | Germany and microservices; “all” not checked; interviews do not prove causal defect reduction |
| Communication and organizational boundaries relate to debt | Borowa: analysis and qualitative data from one project | Medium for the case; abstract and excerpts opened | 30 detailed services out of 100+, one team; architectural-style superiority not measured |
| Reuse saves time and creates a dependency | left-pad incident; professional cost assessment | Specific failure mechanism; weak statistical support | One npm case; many teams use dependencies successfully; no formal risk model |
| Canary releases and feature flags reduce correction cost | Practical recommendations; DORA as possible support | Recommendation; exact effect size not established | No named systematic study specifically of correction cost |
| Modularity and documentation aid maintenance | Microsoft Engineering Playbook, corporate experience | Practitioner opinion, not experimental estimation | No minimum documentation volume established; excessive process also costs resources |
| KISS, YAGNI, DRY, and common patterns provide a universal selection rule | Expert reasoning and selected observations | Contextual heuristics | No common thresholds; wrong abstraction, excessive simplicity, and excessive rigor have their own failure modes |

Section 11 gives bibliography and status for each basis. Unidentified Su et al. is not used in the matrix for a quantitative conclusion about metric prevalence. Its numbers and associated unsupported claims remain in Section 10.

## 8. Popular beliefs that need applicability boundaries

### 8.1. “Always follow SOLID, DRY, KISS, or YAGNI”

These principles help identify particular costs, but do not replace situational analysis. There is no basis for making every principle mandatory for every system. Low external coupling can help; additional Dependency Inversion or another layer may merely burden a project. DRY needs shared semantics, KISS needs the solution's full cost considered, and YAGNI needs unconfirmed functionality distinguished from necessary structure.

A limited SOLID study can exist without universal proof of effectiveness. Claiming no studies exist would exceed the grounds available. The same applies to DDD, FDD, and other approaches: popularity and professional consensus do not replace independent effect checks.

### 8.2. “Clean code solves every problem”

Understandability helps, but aesthetic judgments are vague and not equivalent to maintenance cost. A bounded temporary solution with a clear purpose may be preferable to prolonged polishing of code soon to be deleted. Successful systems with imperfect architecture show beauty is neither a sufficient nor the only criterion; they do not conversely show structure is useless.

### 8.3. “A design pattern is a solution in itself”

Factory, Strategy, and other patterns describe recurring ways to organize code. Their names do not justify their necessity. When an ordinary function expresses the task clearly, extra objects and layers can make it harder to read. Benefit depends on the particular responsibility, variability, and change boundary.

### 8.4. “Many tests or 100% coverage guarantee quality”

Test count and executed lines do not replace oracle quality. Important scenarios, detection of material errors, and acceptable maintenance cost are needed. TDD data must not become a guarantee for every test suite, nor may infrequent mentions of a metric in literature prove the practice itself useless.

### 8.5. “Refactoring always pays off”

Refactoring may sustain structure and lower future cost, but takes time and risks regressions. Its value depends on the likelihood of later changes, the area's condition, and its remaining life. Releasing a feature first and addressing an accumulated problem afterward may be justified. No optimal universal refactoring frequency is established, and moving lines alone does not measure its result.

### 8.6. “Microservices, cloud, or a particular architecture guarantee flexibility”

Microservices offer ways to separate and scale, while adding networking, orchestration, deployment, coordination, and transaction complexity. A modular monolith may be easier to maintain for a small system. One unsuccessful case does not establish general unsuitability; one successful case does not establish general suitability.

A logically verified counterexample can refute a strictly universal guarantee. Borowa's case, however, is not a direct comparative measurement of all “flexibility,” nor does it prove the monolith causally superior. Its result is particular debt and communication observations; the social-debt proposition retains its hypothetical status.[^borowa2025]

### 8.7. “Always reuse” or “avoid dependencies”

Both formulations ignore lifecycle cost. An existing component may save substantial work while creating update and supply obligations. A custom implementation removes a particular external dependency but leaves its own defects, support, and evolution. No safe package count can be derived from left-pad.

### 8.8. “Static analyzers and automated tests will handle everything”

Tools provide particular kinds of signal. They do not automatically assess the validity of a need, all domain-rule meanings, architecture suitability, or communication quality. Interviews report an ongoing role for manual review and architectural principles, but supply no universal quantitative comparison of manual and automated approaches.[^bogner2019]

### 8.9. “Strict types and invariants guarantee no errors”

Types and checks prevent some invalid operations. They do not replace a correct domain model or system-behavior checks. Popularity of statically typed technology in large companies cannot be generalized to all tasks without comparing comparable systems.

### 8.10. “Premature optimization means not thinking about performance”

The advice concerns unjustified optimization and does not exclude a measured bottleneck. Knuth's context already qualifies critical areas. Speed requirements may shape architecture from the start; the materials contain no universal empirical prohibition on early optimization.[^knuth1974]

### 8.11. “More documentation is better”

Documentation is useful when it preserves necessary knowledge and stays current. Page count does not measure usefulness. Code, tests, diagrams, and decision records provide different information; no universal ratio among them is established.

### 8.12. “A senior necessarily knows the right answer”

Career matrices describe expected responsibility, autonomy, and mentoring. A title does not itself confirm decision quality. The materials include no particular matrices or studies connecting them to code quality, so even a claim that no empirical relationship exists must remain bounded by the search performed. This model concerns observable decisions and consequences.

## 9. Unknowns and directions for further investigation

Unknowns bound the conclusions and explain why one engineering metric or a set of slogans is insufficient. The research task is to connect system properties to observed outcomes without losing context and alternative explanations.

### 9.1. How to measure maintainability and evolvability

LOC, cyclomatic complexity, coupling, and the number of code smells do not provide a complete assessment of system health. No generally accepted thresholds have been established beyond which a particular project necessarily requires intervention. Long-term observations of changes, effort, and outcomes in real systems are needed to test which indicators predict the subsequent cost of development.

The question also concerns the ROI of architectural investments: to what extent does reducing coupling or adding a boundary actually reduce future work rather than merely improve an internal metric? Effort spent on understanding, implementation, verification, release, and remediation should be measured separately when such data are available.

### 9.2. When abstraction pays off

There is no verified universal rule to “introduce a shared component after X repetitions.” It is unclear how the stability of shared meaning, the number of consumers, the frequency of coordinated changes, and the probability of diverging requirements affect the outcome.

Repository analysis and controlled experiments could compare the history of identical changes with the outcomes of early and late generalization. Until then, multiple consumers and recurring fixes remain heuristics. A clear shared concept and an expensive future replacement need their own justification, but are not ruled out by a lack of repetition.

### 9.3. The actual cost of technical debt

Prevention costs, removal costs, subsequent time losses, incident risks, and the probability that an area will change must be distinguished. The existence of losses does not answer how many resources should be spent now or when repayment will pay off.

Quantitative relationships with lead time, support, product growth, and business outcomes remain open. A universal refactoring frequency, a single debt threshold, and an exponential form of cost growth have not been established. Comparable data on real tasks and time are needed, rather than repository proxies alone.[^besker][^tom2013]

### 9.4. When microservices are more advantageous than a modular monolith

No rule has been derived for the relationship between team size, tasks, load, independent-release requirements, and operational complexity. Different cases use different success criteria, and architectural changes are often accompanied by changes in teams and processes.

Boundary benefits, network and orchestration costs, coordination, transaction handling, and migration costs need separate assessment. A single observation about debt cannot replace that comparison.

### 9.5. How to measure understanding and cognitive load

Methods are needed to assess correct code understanding, task completion speed, onboarding, and navigation in large systems. Nesting depth, the exposed API surface, size, and Cognitive Complexity can be candidate indicators, but their validity needs testing.

Results involving students and individual methods do not fully answer the question for experienced developers, architecture, or interfaces. Code reading and task performance can be studied; DORA process indicators are not themselves direct measures of cognitive load.[^lavazza2023][^kapitsaki2025]

### 9.6. How much testing, and which kinds, are sufficient

No universal **test coverage → defects that escape into production** curve has been established. Oracle quality, scenario coverage, types of checks, environment costs, execution time, and test maintenance need to be distinguished.

Meta-analyses and commercial data could clarify the effects of different strategies, including under rapidly changing requirements. Until then, choosing between hypothetical 100% coverage and 80% coverage of a critical core cannot rest on percentages alone. A universal break-even point for TDD or additional infrastructure for each project type is also unknown.[^rafique2013][^inozemtseva2014]

### 9.7. How to separate technical and organizational factors

Team structure, communication, deadlines, motivation, accumulated knowledge, and culture may affect both the choice of practices and the quality of outcomes. Good architecture can therefore be a consequence of a strong team rather than an independent cause of all observed advantages.

Research is needed that separates product and process effects: longitudinal observations, interviews, ethnographic and sociological methods, experiments, and team comparisons. The materials do not provide a sufficient assessment of the independent long-term effects of code review, pair programming, Scrum, XP, or other agile practices. Descriptions of participants' priorities and actual reductions in defects must remain different kinds of conclusions.

### 9.8. How far findings transfer across domains and stacks

Most of the empirical evidence presented concerns open-source and object-oriented systems and web services. Transfer to embedded software, scientific and financial computing, real-time applications, small programs, and short-lived prototypes is unclear.

Languages and technologies require comparisons of analogous systems with comparable requirements and teams. The preferences of companies on Google's scale do not prove that their chosen stack is universally suitable. Without such comparisons, effects of scale and organization can easily be mistaken for language effects.

### 9.9. How to assess dependencies in advance

An incident demonstrates a possible failure mechanism, not its probability. It is unknown how to combine component maturity, support, transitive dependencies, change frequency, licensing, and the cost of an in-house alternative into a testable decision model.

Research is needed not only on adoption but also on exiting a dependency, updating, replacement, and maintaining old versions. An individual simple package and a foundational framework create different obligations; the number of dependencies without their structure is insufficient.

### 9.10. How to preserve reversibility under unforeseen requirements

There are ways to limit the consequences of a particular choice, but no universal pattern guarantees inexpensive rework after a sharp change in conditions. Replacement boundaries, migrations, compatibility preservation, and approaches to data handling need investigation.

A substantial question is when flexibility introduced in advance actually reduces future costs and when it becomes unused complexity. Preserving options is a useful criterion, but its cost and effect must be assessed for particular decisions.

### 9.11. How much documentation and formalism are needed

A minimum sufficient set of documents has not been established for different lifetimes, team sizes, and requirements. Data are needed on which information helps maintenance, how quickly it becomes outdated, and when code or tests can replace a textual explanation.

The same applies to multistage reviews, formal checks, and standards: comparable outcomes are needed, not merely the existence of a process. Rigor should be proportional to risk, but no universal numerical calibration has been derived.

### 9.12. How new tools change earlier conclusions

IDEs, Copilot, GPT, other AI assistants, and new analyzers may change the nature of work and code changes. Preliminary observations about duplication do not establish a causal deterioration due to AI. The user population, the share of AI authorship, tool changes, and the difference between new code and maintenance of existing code need to be considered.

Independent replications, longitudinal repository analysis, and controlled experiments, including randomized ones, are useful. They should measure defects, effort, understanding, development costs, and other outcomes, rather than only the amount of generated or copied code.[^gitclear2026]

### 9.13. How to test the model of engineering behavior itself

Most recommendations draw on a combination of partial empirical evidence and practical experience. Causal conclusions require tests in real teams and large codebases, alongside controlled experiments in educational or pilot settings with explicit transfer limits.

Comparing experiments, surveys, cases, analyses of large repository corpora with metadata, and longitudinal observations helps reveal different aspects of the problem. Agreement strengthens an argument only when the methods and data genuinely provide independent grounds. Negative results, failed transfers, and competing explanations must remain visible alongside supporting evidence.

## 10. Corrected, disputed, and unsupported claims

This section preserves substantive claims that cannot be relied on in their earlier form and explains exactly what changed. An incorrect figure or an overstrong conclusion does not disappear from the history of the argument, but is separated from the current model. Textual flaws, transliteration variants, and repeated wording have been standardized.

### 10.1. Clarifying quantities, units, and attribution

| Wording requiring correction | What is retained after checking, and why |
|---|---|
| “GitClear: 600M industry commits” | Approximately **623 million changed lines / code changes** in 2023–2026; about two thirds came from customer repositories. Commits and changed lines have different scales; substituting the unit exaggerated the impression of the sample |
| “Fewer moves, more duplicates: code quality is declining” | A trend in the **moved / copy-pasted / churn / duplication** proxies is supported. Defects, cost, and reliability were not measured in this evidence; conclusions about them need an additional link |
| “Increasing duplication with AI” as an established cause | A preliminary correlational interpretation is retained. The customer-base composition, the number of junior developers, and build tools remain alternative explanations |
| “30% error” without a definition | About 30% is the mean error in predicting understandability with models using one or two metrics, not the percentage of defects or incomprehensible code |
| Lavazza's opening statement about maintenance costs described as an experimental finding | This is motivation in the *Context* section. The measured result concerns the insufficiency of structural metrics for predicting understandability |
| “Naming reduces cognitive load by 70% of the code”; “70% of lines are identifiers” | Identifiers accounted for about 70% of the **characters** in Eclipse code; a quantitative reduction in cognitive load was not measured |
| “Wagner et al.: duplicates known to the team do not increase errors” | The work is clarified as **Juergens, Deissenboeck, Hummel & Wagner (2009)**. The distinction between intentional and unintentional inconsistency is retained; roughly every second change of the latter kind led to a defect. This does not guarantee the safety of any known duplicates |
| “Removing duplicates reduces LOC, cyclomatic complexity, coupling, cognitive load, and human error” as one experimental result | Changes in size and metrics must be separated from empirical effects. A Wikipedia summary does not establish all outcomes with a single finding; dependence on the extraction method and measurement scope also needs checking |
| “Netflix used Chaos Engineering from the beginning” | According to the reviewer's recollection, Chaos Monkey appeared around **2010–2011** during cloud migration; this was subsequent evolution, not the streaming service's original design |
| “TDD increased time by 15–35%” as an objective measurement | These are **managers' estimates** from four teams; the 40–90% reduction in pre-release defect density concerns matched comparable projects without randomization |
| “Academic TDD experiments with no effect are a few small exceptions” | Academic studies accounted for **approximately half** of the meta-analysis; their role cannot be reduced to incidental exceptions |
| “Turan & Tanrıöver 2018” as a fully verified experiment | The 2018 publication and its results were not opened. A **related 2019 dissertation** concerning two projects was found; the sources have not been established as identical |
| “Lehman's laws prove exponential cost growth” | The laws do not specify this function. Exponential growth is retained as an unsupported hypothesis; the historical Boehm/Beck discussion concerns defect-fixing costs across phases, not all architectural changes |
| “Technical debt means minimal release delays” | A possible cause and an outcome are separated: debt, lead time, and release frequency are different quantities |
| “Evolvability is an ISO/IEC 25010 characteristic” | Evolvability is retained as a research term; the standard's maintainability is described through modularity, reusability, analyzability, modifiability, and testability |
| “Reliability is the absence of failures and vulnerabilities”; “adaptability is modifiability” | Vulnerabilities are assigned to security; in ISO/IEC 25010:2011, adaptability belongs to portability and modifiability to maintainability |
| ISO/IEC 9126 and 25010 presented as simultaneously current models | 9126 is retained as the historical predecessor; its replacement by 25010 is dated to 2011 according to the review |
| Debt in Borowa “accumulates through gambling” | *Technical debt gamble* is rendered as rapid cycles of debt accumulation and repayment within services, without a psychological interpretation of gambling |
| The familiar statement about premature optimization lacks its author and context | Knuth, 1974, *Structured Programming with go to Statements*, is identified, including the qualification about the critical **3%** of code; this is historical context, not a prescribed optimization percentage |

The detailed limits of these corrections are given in Section 6 and the bibliography: some came from opened abstracts or pages, others from reviewers' memory. GitClear's **+81% “by 2023”** and the dates of the **9.4% → 15.7%** endpoints require clarification of their temporal reference; it has not been reconstructed by assumption.

### 10.2. An unidentified quantitative source

The reference **Su et al. (2026)** was credited with a review of **284 publications**, use of structural metrics in **92.3%** of architectural-decomposition studies, a share of documentation and testability metrics **below 5%**, and test metrics at **1–2%**. These claims supported a “very high” reliability rating, applicability to any architecture, and an argument about how extensively testing has been studied.[^su2026]

The reviewer's targeted search using the stated parameters did not identify the publication. This does not prove it does not exist: the details may be incomplete or the work unindexed. Until identification, the figures **284; 92.3%; <5%; 1–2%** are retained only as unverified information and do not form part of the evidence base.

Even if verified, these figures would describe how frequently metrics were used in the selected literature. Frequency does not establish a metric's validity, its causal influence on maintenance cost, or the uselessness of an infrequently studied practice. Structural metrics' relationship with external quality needs other evidence—for example, Jabangwe's review; the effect of checks needs studies of particular types of testing.

### 10.3. Overrated confidence and causal transitions

| Strong wording | Current interpretation and the affected conclusion |
|---|---|
| “Technical debt → delays: high reliability, many independent examples,” based on Wikipedia | An encyclopedia article is a secondary account. Independence and strength are unassessed until primary studies are consulted; a universal cost estimate remains open |
| “Two studies on Lehman are independent, reliability is high, no contradictions in the examined examples” | The methodology is partly shared, samples are small, and analysis is descriptive. Confidence is moderate for the relevant trends; Kaur & Vig and Neamtiu add counterevidence |
| “Moderate reliability” for the relationship between metrics and modifiability based only on the SOLID case and Deissenböck 2009 | This pair has low independence and low-to-moderate reliability; one study is unidentified. Jabangwe's review is stronger evidence, although checked from memory in the review |
| “Engineering patterns are confirmed by repeated occurrence in industry; confidence is moderately high” | Repetition of an opinion is not independent empirical evidence. Confidence is contextual and predominantly moderate; there is specific support concerning TDD, clones, metrics, and dependency risks |
| “The role of test infrastructure: no direct studies exist; evidence on coverage's direct effect is not provided” | Missing selected sources indicate incomplete searching, not the absence of all literature. TDD cases and a meta-analysis are retained; universal data on coverage, infrastructure, and break-even points remain lacking |
| “Testing reduces defects and slows development: high reliability” | Individual industrial findings, the average meta-analytic effect, and other kinds of testing must be distinguished. A “high” rating does not transfer to every testing process or project |
| “Teams value review; this directly reduces defects and debt” | Bogner describes reported practices. Causal effects require other evidence; the reviews suggest McIntosh and Bacchelli & Bird |
| The insufficiency of tools alone described as “empirically known” | Interview participants report review's importance. These data contain no quantitative comparative finding about replacing manual approaches with automated ones |
| “Borowa shows frequent co-evolution and the extreme difficulty of rebuilding service boundaries” | This is an authorial extrapolation, not a verified finding of the study. The case concerns debt perceived as isolated and rapid cycles of its accumulation and repayment |
| The idea that “microservices solve flexibility problems” described as refuted by Borowa's case | It challenges an automatic guarantee and shows the role of context. A direct comparison of flexibility as a whole or a causal conclusion about architectural superiority is absent; the authors label social debt as speculation |
| “Systematic studies show that canaries and flags substantially reduce remediation costs” | Professional recommendations exist; no specific systematic study of this cost is identified. DORA concerns broader correlations between delivery practices and stability |
| The Microsoft guide and Cycle.io blog included on a common evidence scale with studies | The Playbook is practitioners' opinion from one company; Cycle.io is a vendor blog. Their role is explaining approaches and recommendations, with the source type separately identified |
| Early security design is recommended without data on the cost of late fixes | Early audit and design are retained as recommendations. The relative cost of vulnerability fixes across phases was not measured in the material |

Both the proposed mechanisms and the limited support for them are preserved in the synthesis. This applies to the arrows “decision → property → outcome”: localized changes plausibly explain the benefits of modularity, but correlational evidence does not establish its independent causal effect in every system.

### 10.4. Claims lacking a source or sufficient verification

| Retained content | Status and clarification needed |
|---|---|
| JabRef, Lucene, and other projects preserved maintainability through their community, duplicate cleanup, and refactoring; error rates fell | No study is named or identified. This is neither a verified case nor a confirmed correlation |
| In one large analysis, coupling/cohesion had no statistically significant relationship with code-size growth | The source is unidentified; marker **`[15]`** is unresolved. Do not use it as established counterevidence; the subject is size growth, not automatically change cost |
| “Many surveys” link missing documentation and excessive coupling to poor communication or insufficient knowledge | The surveys are unnamed. This direction is discussed in one Borowa case, which does not establish the claimed multiplicity of surveys |
| In situ studies show that projects with good tests break less often and detect regressions faster | No sources are named. Inozemtseva & Holmes are suggested as a direction for investigation: the review attributes a weak relationship between coverage and test effectiveness to their 2014 work, but does not describe opening it. This is not a recovered citation for the in situ claim |
| Studies show how developers anticipate changes and increase flexibility in advance | No study is identified; this is retained as a plausible recommendation without an attributed measured effect |
| “Long-term update percent,” “old-code update coefficient,” “forgotten code” | These are linked to GitClear indicators, including legacy refactoring; their formula, thresholds, and validity as a general indicator are undisclosed |
| Google/Netflix practices show independent effects of static analysis, CI, and review | No specific publications or quantitative estimates are named; the corporate examples retain illustrative status |
| 13 JHotDraw versions, 16 Rhino versions, and a 10-year span | These details occur in the description but were not checked by opening Johari & Kaur's full text. The abstract supports the subject and broad conclusion, not every exact figure |
| Johari quotations about adding features becoming “increasingly difficult,” and Bogner quotations about a preference for review | Exact wording is unverified; the main account retains a paraphrase rather than the appearance of a verified direct quotation |
| “All teams” rely on architectural principles and manual review | The quantifier is unverified. Recalling “most” does not justify silently substituting another exact claim |
| “Abstraction without a real need merely adds unnecessary layers of understanding” as a research quotation | No source is specified; this is retained as a heuristic explanation of the cost of a wrong abstraction |
| Frequent package adoption causes “shadow management” of versions and debt | No specific source; the mechanism of additional obligations is retained, while the universal empirical formulation is removed |
| “Experienced teams therefore limit the number of third-party packages” | No data establish the prevalence of this behavior. The recommendation to assess dependencies is retained, without a universal quantity rule |
| Deissenböck (2009): deterioration first appears in coupled components; architecture “rusts” across every attribute | The exact work is unidentified; the author has several publications on quality from 2007–2009. This is not verified empirical support |
| Many tools record continuous growth in cyclomatic complexity and duplication without review | Sources are unnamed. GitClear and evolution studies may guide further checking, but do not automatically support the entire claim |
| The Microsoft Engineering Playbook's maintainability definition contains the listed characteristics verbatim | The guide exists; the exact wording is unverified. A substantive paraphrase is used as practitioners' opinion |
| Regular reviews and static analysis reduce the number of release defects | Sources are absent from the corresponding claim. The reviews name McIntosh et al. 2014 and Bacchelli & Bird 2013; particular findings require consulting them |
| Team metrics are used as indirect indicators of process quality without named empirical support | DORA is suggested as possible support; no report or study is identified, and causality is not established |
| Senior career matrices are empirically unrelated to code quality | Neither matrices nor studies are named; absence of a relationship cannot be treated as an established negative result |
| “Continuous quality control (see [94])” proves prevention of architectural degradation | Marker **`[94]`** is unresolved and is not used in the evidential references |
| “Bank X successfully fixed the situation” and “a failed migration” as real documented cases | No identifiable projects or sources exist in the materials. These stories are retained as hypothetical illustrations of compatibility, flexibility, and deferred rework |

## 11. Bibliography and source status

The details below distinguish an identified publication from a direction for searching. Links are constructed only for DOI and arXiv identifiers supplied in the materials. For other works, URLs, DOIs, titles, and missing years have not been reconstructed by guessing. “From memory” does not mean a work is unreliable; it limits how reliably its findings have been reproduced here.

### 11.1. Sources for the empirical discussion

- Object-oriented metrics and external quality: **Jabangwe, Börstler, Šmite & Wohlin (2015; online 2014)**.[^jabangwe2015]
- Code understandability: **Lavazza, Morasca & Gatto (2023)**; replication by **Kapitsaki, Lavazza, Morasca & Rotoloni (2025)**.[^lavazza2023][^kapitsaki2025]
- Cyclomatic complexity and size: **Shepperd (1988)**; **Landman, Serebrenik, Bouwers & Vinju (2016)**.[^shepperd1988][^landman2016]
- Repository proxies: **GitClear, 2026**.[^gitclear2026]
- Evolution of open systems: **Johari & Kaur (2011)**; **Kaur, Ratti & Kaur (2014)**; further tests by **Kaur & Vig (2016)** and **Neamtiu et al. (2013)**.[^johari2011][^kaur2014][^kaurvig2016][^neamtiu2013]
- Microservice-team practices: **Bogner, Fritzsch, Wagner & Zimmermann (2019)**.[^bogner2019]
- Debt in a large microservice system: **Borowa, Ratkowski & Verdecchia (2025)**.[^borowa2025]
- TDD: **Nagappan, Maximilien, Bhat & Williams (2008)**; meta-analysis by **Rafique & Mišić (2013)**.[^nagappan2008][^rafique2013]
- Code clones: **Juergens, Deissenboeck, Hummel & Wagner (2009)**.[^juergens2009]
- Naming: **Deißenböck & Pizka (2006)**.[^deissenboeck2006]
- SOLID: the claimed publication by **Turan & Tanrıöver (2018)** and the separately found related **Ankara University dissertation (2019)**.[^turan2018][^solid2019]
- Dependency risk: **the left-pad incident, March 22, 2016**.[^leftpad2016]

### 11.2. Standards, concepts, and practitioners' experience

- Quality models **ISO/IEC 25010** and the historical **ISO/IEC 9126**.[^iso25010][^iso9126]
- **Lehman's laws**; the historical discussion of defect-fixing costs in **Boehm (1976, 1981)** and **Beck (1999)**.[^lehman][^boehm][^beck1999]
- Technical debt: **Cunningham (1992)**; **Kruchten, Nord & Ozkaya (2012)**.[^cunningham1992][^kruchten2012]
- Optimization: **Knuth (1974)**.[^knuth1974]
- Corporate guidance and reports: **Microsoft Engineering Playbook**, **Cycle.io**, unnamed **Google/Netflix** publications, and material by **Martin Fowler**.[^microsoft-playbook][^cycle][^google-netflix][^fowler]
- Delivery and stability indicators: **DORA**, without a specific report identified.[^dora]
- Encyclopedic accounts: **Wikipedia**, without a resolved chain of primary sources.[^wikipedia]

### 11.3. Further directions and unidentified works

- The empirical cost of debt: **Besker, Martini & Bosch (2018–2019)**; **Tom, Aurum & Vidgen (2013)**.[^besker][^tom2013]
- Test effectiveness and coverage: **Inozemtseva & Holmes (2014)**.[^inozemtseva2014]
- Code review: **McIntosh et al. (2014)**; **Bacchelli & Bird (2013)**.[^mcintosh2014][^bacchelli2013]
- Unidentified references: **Su et al. (2026)**; **Deissenböck (2009)**; numeric markers **`[15]`** and **`[94]`**; unnamed works on JabRef/Lucene, anticipating changes, test quality in situ, and communication surveys.[^su2026][^deissenboeck2009]

## 12. Conclusions of the model

Good engineering preserves a system's ability to perform the required tasks and change with acceptable effort and risk. Its assessment requires product properties, operational outcomes, and actual maintenance work together. No internal indicator covers them all.

Modularity, clear contracts, meaningful checks, diagnostics, appropriate refactoring, and knowledge transfer provide useful ways to manage uncertainty. Their benefits depend on fit to the particular task: an additional layer, test, or process must be justified by a need and its consequences. Excessive use of the same practice can create costs of its own.

The strength of the empirical base varies. Systematic reviews of metrics and TDD, observations of evolution, interviews, individual incidents, and vendor statistics support different parts of the model. They do not establish a single causal formula for quality. Checking the sample, measurement target, independence, and alternative explanations matters as much as having a citation.

The working position is to state the expected outcome, choose a proportionate solution, observe its consequences, and revise assumptions when new evidence appears. Multiple consumers are a signal for abstraction, not a mandatory condition; exponential cost growth is an unsupported hypothesis; a statistical finding applies to the practice and conditions studied. Preserving these boundaries makes the model suitable for further refinement in particular projects.

---

[^jabangwe2015]: **Jabangwe, R.; Börstler, J.; Šmite, D.; Wohlin, C.** *Empirical evidence on the link between object-oriented measures and external quality attributes: a systematic literature review*. Empirical Software Engineering, **20(3), 2015**, online **2014**. The review checked the **99**-study count and findings **from memory**, without opening the work. Context: predominantly Java/C++, class-level correlations, defects, and change effort; inheritance shows weak and conflicting relationships. The DOI and full bibliographic page range are not provided.

[^lavazza2023]: **Lavazza; Morasca; Gatto.** *An empirical study on software understandability and its dependence on code characteristics*. Empirical Software Engineering, **28, 2023**. **Abstract opened**. The description mentions the University of Insubria; participants were students, tasks involved maintenance of open-source methods, and the measure was correct-completion time. Models using one or two metrics had about **30%** error; Cognitive Complexity did not substantially improve the result. The full text, sample size, and DOI are not provided.

[^kapitsaki2025]: **Kapitsaki; Lavazza; Morasca; Rotoloni. ENASE, 2025.** Replication of the understandability study using the same code. **Abstract opened**; correlations between metrics and understanding were not confirmed. The full title and identifier are unspecified.

[^shepperd1988]: **Shepperd, 1988.** Mentioned as support from the literature for a cautious discussion of cyclomatic complexity and size. The finding was cited **from memory**; the exact publication, coefficients, and sample are not supplied in the materials.

[^landman2016]: **Landman; Serebrenik; Bouwers; Vinju, 2016.** A work on the strong relationship between cyclomatic complexity and SLOC. Mentioned **from memory**; its full title, identifier, and numerical findings are absent.

[^gitclear2026]: **GitClear.** *The Maintainability Gap / Write-Only Mode: AI Code Quality in 2026*, **June–July 2026**. **The report page and publications about it were opened**. The clarified volume is about **623 million changed lines / code changes**, 2023–2026; roughly two thirds of the data came from customer repositories. A separate moved series begins in 2022. This is a vendor report without scholarly peer review; defect and cost outcomes were not measured. The URL was not retained in the materials.

[^johari2011]: **Johari; Kaur.** *Effect of software evolution on software metrics: an open source case study*. ACM SIGSOFT Software Engineering Notes, **36(5), 2011**. [DOI: 10.1145/2020976.2020987](https://doi.org/10.1145/2020976.2020987). **Metadata and abstract opened**. The subject and general result were confirmed; **13/16 versions and 10 years** were not checked against the full text. The review notes the descriptive design and research-note format, which are not equivalent to a full experimental test.

[^kaur2014]: **Kaur; Ratti; Kaur.** *Applicability of Lehman Laws on Open Source Evolution: A Case study*. International Journal of Computer Applications, **93(18), 2014**. **Abstract opened**: GLE and FlightGear, **10 versions over 8 years**. The method draws on Johari & Kaur; independence is limited. The characterization of the outlet as having low selectivity comes from the review; no separate assessment of its editorial procedure was performed.

[^kaurvig2016]: **Kaur; Vig, 2016.** Statistical testing of evolution laws: **11 Java projects, 493 releases, 3 of 8 laws supported**. The work was **found in the reviewer's targeted search**; opening the full text is not claimed. The title, identifier, and findings for each law are not provided.

[^neamtiu2013]: **Neamtiu et al., 2013.** Identified as a source of mixed findings on the applicability of evolution laws. The review does not describe full bibliographic details or a separate verification scope; detailed findings have not been reconstructed here.

[^bogner2019]: **Bogner; Fritzsch; Wagner; Zimmermann.** *Assuring the Evolvability of Microservices: Insights into Industry Practices and Challenges*. **ICSME, 2019**. Checked **from memory**, without opening. Sample: **17 interviews, 10 companies, 14 systems**, microservice teams in Germany. Participants' priorities are described; a causal effect on defects was not measured. Exact quotations and the quantifier “all” are unverified.

[^borowa2025]: **Borowa; Ratkowski; Verdecchia.** *The Technical Debt Gamble: A Case Study on Technical Debt in a Large-Scale Industrial Microservice Architecture*. Journal of Systems and Software, **230, 2025**; [arXiv:2506.16214](https://arxiv.org/abs/2506.16214). **Abstract and passages opened**. **100+** services, **>15 thousand** locations; detailed analysis of **30** services, SonarQube, a focus group, and an architect interview. One project; the authors discuss social debt as speculation.

[^nagappan2008]: **Nagappan; Maximilien; Bhat; Williams.** *Realizing quality improvement through test driven development: results and experiences of four industrial teams*. Empirical Software Engineering, **13(3), 2008**. Checked **from memory**. Three Microsoft teams and one IBM team; a **40–90%** reduction in pre-release defect density, and a **15–35%** increase in time according to managers' estimates. A nonrandomized case study, comparison with matched projects, and experienced teams.

[^rafique2013]: **Rafique; Mišić.** *The Effects of Test-Driven Development on External Quality and Productivity: A Meta-Analysis*. IEEE Transactions on Software Engineering, **39(6), 2013**. Checked **from memory**. **27 studies**, a small positive average effect on external quality, and a statistically nonsignificant average effect on productivity; industrial settings more often showed a negative productivity effect alongside a larger quality gain. Approximately half the studies were academic; conditions were heterogeneous.

[^juergens2009]: **Juergens; Deissenboeck; Hummel; Wagner.** *Do code clones matter?* **ICSE, 2009**. Checked **from memory**. Industrial and open systems; the distinction between intentional and unintentional inconsistency. Approximately every second unintentionally inconsistent change led to a defect. The full sample and exact coefficients are not presented in the materials.

[^deissenboeck2006]: **Deißenböck; Pizka.** *Concise and consistent naming*. Software Quality Journal, **2006**. Clarified **from memory**: identifiers account for approximately **70% of characters** in Eclipse code. Rules for concise and consistent naming were proposed; a quantitative reduction in cognitive load was not measured.

[^turan2018]: **Turan; Tanrıöver, 2018.** The exact title and identifier of the claimed work have not been established. Attributed effects—reduced coupling, greater modifiability, and increased class counts/hierarchy depth—were **not verified by opening the publication**. The discovered 2019 work cannot be treated as the same publication without further details.

[^solid2019]: *Solid prensipleri ile bakım için yazılımı yeniden yapılandırma yöntemi*. **Dissertation, Ankara University, 2019**. **Found through targeted search** as a related work. The description maps SOLID to ISO 9126/25010 subcharacteristics, refactors two large enterprise projects, and uses Visual Studio metrics. A before/after design without a control group; specific results were not opened. Ö. Tanrıöver's university affiliation is consistent with the attribution but does not establish that the sources are identical.

[^leftpad2016]: **The left-pad incident, npm, March 22, 2016.** According to the reviewer's memory: an **11-line** package was removed, breaking transitive build chains, including through Babel; npm restored it by bypassing the author. React is mentioned without separate verification; Facebook, Netflix, and PayPal are press reports about users of affected tools. “Thousands of projects” is an approximate order of magnitude from the press, not a measured total. No specific postmortem or URL is named.

[^iso25010]: **ISO/IEC 25010**, **2011/2023** models mentioned during review. Terminological clarifications were made **from memory**, without opening the standard. For the 2011 model, adaptability/portability and modifiability/maintainability are explicitly distinguished; vulnerabilities are assigned to security. Evolvability is not attributed to the standard as its term. The full contents of the editions were not verified.

[^iso9126]: **ISO/IEC 9126.** A historical quality model, described in the review as replaced by ISO/IEC 25010 in **2011**. Clarified **from memory**; it is also retained as the model used in the description of the SOLID work.

[^lehman]: **Lehman's laws of software evolution.** No specific publication is given. The laws and the scope of E-type systems were described in the reviews **from memory**. They address continuing change, growth, and increasing complexity, but do not specify an exponential cost function for any change. Results of particular empirical tests are listed separately.

[^boehm]: **Boehm, 1976 and 1981.** Named as historical sources discussing growth in defect-fixing costs across lifecycle phases. Attribution is **from memory**; titles, original data, and methodology are not provided. This is a different subject from the cost of any architectural change over time.

[^beck1999]: **Beck, 1999.** Mentioned in connection with challenging earlier conceptions of the cost-of-change curve. No title or specific passage is given, and verification through opening is not claimed. Subsequent reassessments are also mentioned without bibliographic details.

[^cunningham1992]: **Cunningham, 1992.** Identified as a primary conceptual source on technical debt. The review lacks full bibliographic details and a verification procedure; no numerical effect size is attributed.

[^kruchten2012]: **Kruchten; Nord; Ozkaya, 2012.** Identified as primary literature on technical debt rather than relying solely on a vendor blog. The title and verified findings are not supplied in the materials.

[^knuth1974]: **Knuth, 1974.** *Structured Programming with go to Statements*. Attribution **from memory**: “premature optimization is the root of all evil (or at least most of it) in programming”. The same work discusses the critical **3%** of code where optimization is justified. This is the quotation's context, not an empirically established norm for the share of code to optimize.

[^microsoft-playbook]: **Microsoft Engineering Playbook.** A practical guide; the review notes the existence of a public repository, but the exact wording of the maintainability definition was not checked. Clarity, modularity, documentation, and limiting change risk are mentioned. This is practitioners' opinion from one company, without formal comparative evidence of effect.

[^cycle]: **Cycle.io.** A vendor blog used to explain the trade-off between release speed and future debt costs. No specific publication or URL is given; the source is not independent empirical confirmation.

[^google-netflix]: **Google / Netflix: corporate practices and the history of Chaos Monkey.** Specific blogs, independent assessments, and quantitative effects are unnamed. Chaos Monkey's appearance around **2010–2011** during cloud migration was clarified **from memory**. The causal connection to high availability remains illustrative.

[^fowler]: **Martin Fowler.** Mentioned in connection with testing practices and quality, without a publication title, date, or URL. Not independent support for numerical conclusions about TDD or test infrastructure.

[^dora]: **DORA: delivery and stability reports.** Named in the reviews as possible support for lead time, delivery frequency, recovery, and relationships between continuous-delivery practices and stability. Specific editions and effects are not provided. The data are characterized as **survey-based and correlational**, not evidence of a causal effect of a particular practice.

[^wikipedia]: **Wikipedia.** Unnamed articles on technical debt, duplication, and metrics. Secondary accounts; the full reference chain to primary works has not been recovered. The number of mentions does not establish independence or high credibility. Attribution of the code-clone result is clarified separately with Juergens and colleagues.

[^besker]: **Besker; Martini; Bosch, 2018–2019.** Named as primary works on the share of development time lost to technical debt. The reviews do not describe opening and checking specific findings; numerical shares and work titles are not supplied. This is a direction for checking, not a reconstructed quantitative cost model.

[^tom2013]: **Tom; Aurum; Vidgen, 2013.** Named as primary support for investigating technical debt. Full bibliographic details and verification scope are unspecified; particular measured effects are not reproduced here.

[^inozemtseva2014]: **Inozemtseva; Holmes, 2014.** The reviews identify a work on the weak relationship between coverage and test effectiveness and suggest it as a direction for filling search gaps. The full title, sample, and separate opening procedure are not given. It must not substitute for the unnamed in situ studies of test quality.

[^mcintosh2014]: **McIntosh et al., 2014.** Named as additional evidence on code-review coverage and participation and post-release defects. Findings are not detailed, and their verification procedure is undescribed; the work does not turn Bogner's descriptive interviews into a causal experiment.

[^bacchelli2013]: **Bacchelli; Bird, 2013.** Suggested as a direction for checking claims about code review. The materials lack the title, numerical findings, and opening procedure.

[^su2026]: **Su et al., 2026.** An unidentified supposed review of **284 publications**; the attributed shares **92.3%**, **<5%**, and **1–2%** are unconfirmed. The reviewer's targeted search using numbers and subject matter produced no result. Existence is not ruled out; until bibliographic details are supplied, the quantitative conclusions and “very high” rating are not accepted.

[^deissenboeck2009]: **Deissenböck, 2009.** The exact work is unidentified; several publications by the author from **2007–2009** on quality models are mentioned. Claims that deterioration first manifests in coupled components and that architecture “rusts” are not connected to a verified source. Do not confuse this with the identified title of the 2006 consistent-naming work.
