# Current architecture

Use when a decision or assessment depends on an existing system. Reconstruct the
relevant part before proposing a replacement; missing access does not establish
a greenfield project. Do not turn documentation into an unrequested redesign.

## Establish what is actually known

Start from the brief, owner decisions, manifests, framework entry points and
representative code. Identify the examined revision or artifact and relevant
dirty changes. Expand only along dependencies and consumers material to scope.

Keep four evidence kinds visible in working notes: observed in source or execution,
stated in documentation, inferred with a reason, and unknown with the discriminating
check. A repeated pattern is evidence of practice, not automatically an adopted
rule. Conflicting docs and code remain a question to resolve rather than permission
to pick the convenient account.

## Map owners, not every file

For each material responsibility identify its owner, canonical inputs, consumers,
public interface, dependency direction, mutation authority and lifecycle. Distinguish
editable sources from generated projections, caches, installed state and history.
Similar bytes are not necessarily independently authoritative copies.

Read past public names: follow imports, aliases, re-exports, calls, registrations
and the native/library operation behind a facade. Include supported external
consumers and dynamic discovery when relevant. Zero textual imports do not establish
inactivity; do not broaden a search beyond authorized roots to manufacture certainty.

Connect the physical layout with logical responsibilities, execution/deployment
units and trust boundaries. Name which view is needed; do not require every C4
level or a diagram. A directory named `services` does not establish a deployment
boundary, nesting does not prove ownership, and a protocol interface such as MCP
does not by itself make an independently operated service.

## Trace consequential scenarios

Choose representative operations, changes and failures that can affect the decision.
For each, trace entry/discovery, configuration, calls, state changes and the observable
result. Identify the source of truth, who can mutate it, and how errors, cancellation,
retries or disposal are handled where applicable. Check lifetime distinctions such
as instance, request, process and shared persistent state.

For a change scenario, identify affected owners and contracts, required coordination
and how a violation would be detected. Examine a nearby valid alternative before
calling a relationship harmful. A source walkthrough is useful evidence of structure,
not proof that execution or clean installation succeeded.

## Return a scoped map

Report the material owners and flows with source locations, the applicable contract,
coverage and remaining unknowns. Reuse an existing architecture document when it is
sufficient. An exhaustive file census, automatic pattern confidence score or a new
canonical registry is not required. Preserve the difference between the current
system and a subsequent target proposal.
