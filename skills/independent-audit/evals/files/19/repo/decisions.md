# Accepted current constraints
The supported browser platform provides native dialog modality and focus behavior.
SwitchRoot owns keyboard and checked-state behavior; the facade supplies labels
and tokens. Native input is an intentional platform primitive.
The noninteractive help panel has one fixed corner; no dismissal or focus logic.
The selected popup helper emits dynamic inline coordinates, conflicting with the
deployment CSP. Keep a static stylesheet class for this bounded case. Reassess
if an anchored/interactive help popup is requested or that constraint changes.
This exception applies to placement only, not all UI mechanics. No browser-run
receipt is supplied; source responsibility can be checked, runtime is unverified.
