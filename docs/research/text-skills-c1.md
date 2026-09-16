# Text skills C1: corrections after the 2026-09-16 pilot

Status: candidate, not behaviorally qualified. The baseline is the supplied
snapshot identified by the pilot as `1e6fb49`; file hashes in the handoff identify
its exact content. This record must be reconciled with the repository's current
revision before merging. Historical answers, keys and scores are not replaced.

C1 distinguishes missing evidence from a contradiction, applies completeness
within the requested scope, chooses install routes from the audience and actual
availability evidence, and requires a concrete reason for an unsolicited prose
change. It also separates final text from audit reporting and source-path link
resolution from target-string preservation. The Russian modality example no
longer turns a possibility into an observed frequency.

Both methods remain standalone. Runtime scripts stay inside the technical skill;
`text_check.py` and its dependency declaration are unchanged. The added tests
exercise the existing check and explicitly demonstrate what it does not prove.
No new humanizer dependency, AI score, context database or editing-agent cascade
was introduced.

The existing source basis and upstream ledger remain authoritative for
provenance. No external code was copied for this revision. Reader-first README,
structural editing and bounded reader testing are retained; blanket bans and
mandatory template sections are not. The refinements are supported by local
pilot failures and valid controls, not upstream stars or numerical self-scores.

The public case collections retain earlier cases and add 22 diagnostic
regressions. The private successor to the pilot has 32 R2 cases with corrected
inputs/rubrics; it is now a known regression set, not heldout. A separate packet
contains 6 E2E specifications. Their inclusion is not execution evidence. C1
requires a new matched-input comparison against frozen C0; optional simple-prompt
comparison and an independently reserved fresh set answer different questions.

Run the new tool suite explicitly unless the owner gate already discovers it:

```text
python -B -m unittest discover -s skills/technical-writing/evals -p "test_*.py"
```

Passing this suite does not prove semantic equivalence, method effectiveness,
client discovery or correct installation. Update this status only from captured
runs and complete artifacts, including failed attempts and limitations.
