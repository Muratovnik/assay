# Record feedback cases from ordinary work

Use this when a user correction, or an example of acceptable behavior, should
leave a local record for later review without running another model or a
benchmark campaign. A record means **a case was observed and kept**, not that the
agent, skill or user is wrong. The same working model can annotate it using the
conversation it already has.

A case is recorded by an explicit decision: the user says "record this as a
case", or the agent offers it after classifying a correction. Automatic capture
from correction phrases is a separate, optional trigger that is off by default.
Nothing here reads transcripts, attachments, repository files or tool outputs to
infer a failure; it does not change skills, create evals, call a service or
schedule another model turn. Annotation still consumes time and context.

You need Python 3.11+ and the existing `hooks/requirements.txt` dependencies. The
full plugin or a full checkout must contain `hooks/runtime` and
`skills/route-subagents/scripts`: a skills-only installation does not supply this
runtime. See [hook setup](hooks.md) for the hook path.

## Storage mode and trigger

Two owner-controlled options in the `ASSAY_HOOK_CONFIG` JSON file decide what is
kept and what creates a record. Keep that file outside a tracked repository and
choose an absolute private data directory:

```json
{
  "state_dir": "/absolute/private-assay-data",
  "feedback_capture": "metadata",
  "feedback_trigger": "explicit"
}
```

On Windows, use an actual Windows absolute path, for example
`C:/private-assay-data`, not the POSIX placeholder above. Existing
`disabled_rules`, `disabled_skills` and `record_events` options can remain in the
same file. Without an explicit `state_dir`, full plugins can use their existing
`PLUGIN_DATA` / `CLAUDE_PLUGIN_DATA` location for hook capture; explicit commands
take `--state-dir` or `--config`.

| `feedback_capture` | What is retained |
| --- | --- |
| `off` | No records of any kind. |
| `metadata` | The default. Kind, client, session ID when supplied or native, hashed scope, timestamps, signal class, Assay version, method context, short codes and identifiers. No prompt excerpt and no free text. |
| `content` | The metadata plus a correction excerpt of up to 4,096 characters and permitted short annotation/review text. Truncation is explicit. |

| `feedback_trigger` | What creates a record |
| --- | --- |
| `explicit` | The default. Only the `record` command. The prompt hook does not classify messages. |
| `hook` | Also the bounded correction grammar in the existing prompt hook. |

Deciding to record a case never switches on `content`: storing free text is a
separate owner decision about permitted content and location.

## Record a case explicitly

```text
python -I -B hooks/runtime/feedback_cli.py record --state-dir /absolute/private-assay-data --input case.json
```

`--config` reads the storage mode and data directory from an owner configuration
file instead. The JSON object accepts:

| Field | Meaning |
| --- | --- |
| `kind` | Required: `correction` or `allowed_behavior`. |
| `criterion` | `{"code": "...", "ref": "..."}`: a short code from the owner's requirement list and a reference to the owning task or decision. Required for `allowed_behavior`: an allowed example is defined by the criterion it meets, never by an absence of complaints. |
| `client`, `session_id` | Optional: `claude`, `codex`, `gemini`, `cursor` or `unknown`, and the client session in which a person can find the transcript. |
| `methods_reported` | Optional catalogue-relative paths such as `skills/code-change/SKILL.md` that the agent reports having read; stored as `self_reported`. |
| `revision` | Optional commit or digest of the method copy, stored as `caller_supplied`. |
| `related` | Optional ID of a retained record, for example the correction an allowed example answers. |
| `trace_refs` | Optional identifiers of available traces: receipts, commits, task items. No spaces or absolute paths. |
| `excerpt` | The original correction text; accepted only when the storage mode is `content`. |

Example of an allowed example linked to a reviewed correction:

```json
{
  "kind": "allowed_behavior",
  "criterion": {"code": "R8", "ref": "TASK-17"},
  "related": "CORRECTION_ID",
  "methods_reported": ["skills/code-change/SKILL.md"]
}
```

## What a record can and cannot identify

Each record stores the release `VERSION`, the hint-rule fingerprint and, for
reported methods, SHA-256 digests of those files as present in the recorder's own
installation (`recorder_root_bytes`). These are pointers, not proof:

- `VERSION` does not identify exact method bytes.
- The rule fingerprint covers hint rules and `SKILL.md` bytes, not `references/`.
  A change to a reference alone can leave version and fingerprint unchanged.
- The digests describe this installation's files at record time; the agent may
  have read another installed copy. A caller-supplied revision is labelled as such.
- `methods_reported` is the agent's own report, not a trace of reading.

Unknown values stay `unknown`; nothing is reconstructed from current files later.
The source records an evidence level: `command_input_unattested` for hook
capture and `caller_report_unattested` for explicit records.

## Optional correction hook

Set `feedback_trigger` to `hook` and keep `feedback_capture` at `metadata` unless
content has been approved. Claude/Codex full plugins already invoke the collector
from their existing `UserPromptSubmit` handler.

**Before enabling `content`:** excerpts, explicit or captured, are verbatim, not
automatically sanitized.
They may contain private code, credentials or personal data, whose storage stays
subject to the data owner's legal obligations. No full transcript is
read or copied, but that does not make a single prompt safe to share. Use a private
owner-controlled directory with appropriate filesystem access; review and sanitize
anything you export before putting it in a repository. There is no outbound upload.

For an already installed Claude/Codex full plugin, update/enable/trust its normal
hooks and restart as required by that client. Do **not** register a second feedback
hook: the existing `UserPromptSubmit` command already invokes the collector.
`doctor` reports configuration, not filesystem permission, native execution or
model compliance:

```text
python -I -B hooks/runtime/cli.py doctor --client claude
python -I -B hooks/runtime/cli.py doctor --client codex
```

On a later actual correction such as `You missed the required static analysis.`,
the collector records a candidate and returns a short notice to the working model.
The parser considers the first top-level request paragraph, excludes Markdown
quotes/code/lists/headings, and recognizes bounded English/Russian repair phrases.
It does not analyze sentiment generally, and can miss implicit corrections or
messages over 16,384 characters. False positives remain candidates for review.

Inspect the store from the checkout or installed plugin root:

```text
python -I -B hooks/runtime/feedback_cli.py list --state-dir /absolute/private-assay-data
python -I -B hooks/runtime/feedback_cli.py show CANDIDATE_ID --state-dir /absolute/private-assay-data
```

Replace `CANDIDATE_ID` with a returned ID. `list` prints a compact JSON inventory;
`show` prints the source observation separately from annotations and review.
The argument is the parent directory from configuration, **not** its `feedback`
child. Missing native execution or an inaccessible directory produces no receipt
that the client ran the hook. Inspect the client's own diagnostics as well.

## Native client boundaries

Hook capture requires `feedback_trigger: hook`; with the default explicit trigger
these adapters record nothing. They are command adapters, not a claim that every historical client version,
cloud surface or managed policy supports them. Contracts were checked against
the primary documentation linked below on 2026-10-05; native enablement and model
compliance still need observation in the intended client.

| Client | Capture event | Model notice | Deduplication |
| --- | --- | --- | --- |
| Claude Code | `UserPromptSubmit` | `hookSpecificOutput.additionalContext` with the native event name | No invented turn ID; identical prompts are separate candidates. |
| Codex | `UserPromptSubmit` | The documented native `hookSpecificOutput` envelope | Native `turn_id`, scoped by session, working directory and agent/transcript identity. |
| Gemini CLI | `BeforeAgent` | `hookSpecificOutput.additionalContext` | No timestamp/text-based invented delivery ID; identical prompts are separate candidates. |
| Cursor | `beforeSubmitPrompt` | `additional_context` at the next successful `postToolUse` in the same generation | Native `generation_id` plus conversation/workspace scope. |

Cursor's documented prompt-hook output does not provide context injection. Its
prompt hook therefore only records; its tool hook emits the notice once, for that
exact generation, within 24 hours. A tool-free turn leaves an unannotated candidate.
There is no `stop` follow-up, forced tool call or hidden model invocation. Other
generations cannot consume the notice. Native hook output is not proof the model
read or obeyed it.

Claude/Gemini duplicate deliveries without stable native IDs cannot be reliably
suppressed; do not enable duplicate registrations to compensate. Codex without
both an agent ID and transcript identity abstains from stateful collection rather
than merge indistinguishable workers. Transcript paths contribute to a scope hash
but are never opened or stored verbatim.

### Cursor registration

The existing Assay skills install does not register Cursor feedback hooks. From a
full checkout, add these entries to the appropriate native `.cursor/hooks.json`,
preserving all unrelated entries. Replace the absolute path placeholders. These
are configuration fragments, not an instruction to overwrite an existing file.

```json
{
  "version": 1,
  "hooks": {
    "beforeSubmitPrompt": [
      {
        "command": "python -I -B /absolute/assay/hooks/runtime/feedback_cli.py event --client cursor --config /absolute/private/assay-hooks.json"
      }
    ],
    "postToolUse": [
      {
        "command": "python -I -B /absolute/assay/hooks/runtime/feedback_cli.py event --client cursor --config /absolute/private/assay-hooks.json"
      }
    ]
  }
}
```

The native Cursor schema uses arrays of commands directly. It is not Claude's
nested hook-group schema. Do not register both a translated Claude feedback hook
and these native entries. Project/user/cloud availability and trust follow Cursor's
own documentation; a local user's configuration is not installed into cloud VMs.

### Gemini CLI registration

Merge the following fragment into the intended native Gemini `settings.json`:

```json
{
  "hooks": {
    "BeforeAgent": [
      {
        "hooks": [
          {
            "name": "assay-feedback",
            "type": "command",
            "command": "python -I -B /absolute/assay/hooks/runtime/feedback_cli.py event --client gemini --config /absolute/private/assay-hooks.json"
          }
        ]
      }
    ]
  }
}
```

Use `BeforeAgent`, not Claude/Codex's `UserPromptSubmit`. No `AfterAgent` retry
handler is needed. Paths containing spaces need quoting for the client's actual
command shell; Windows paths can use forward slashes in JSON. Verify the chosen
Python interpreter and command through native diagnostics instead of assuming
that a shell example for another OS was executed.

The standalone `feedback_cli.py event --client claude|codex` adapter also accepts
those clients' native prompt payloads for an explicitly managed, non-plugin setup.
Use their documented command-hook registration syntax. Never add it alongside the
full plugin's existing event handler. This is an alternative installation path,
not a second automatic settings installer.

## Annotation is not confirmation

The notice asks the current model to compare the correction with the earlier
request and actual work. It must distinguish a reported mismatch, a new
requirement, a preference, disagreement and insufficient context. Missing earlier
requirements remain unknown. The source excerpt is an observation; the model's
summaries and suspected cause are interpretations, not ground truth.

An annotation is a JSON object on stdin, or an explicitly supplied UTF-8 JSON file:

```json
{
  "category": "reported_mismatch",
  "basis": "prior_requirement",
  "task": "Prepare the development environment.",
  "observed": "Static analysis was not configured.",
  "expected": "Include the agreed pre-release checks.",
  "evidence": "The earlier request explicitly named pre-release checks.",
  "hypothesis": "The setup inventory may have omitted a quality capability; the cause is not established."
}
```

This is an illustrative **content-mode** annotation, not a captured real case.
In metadata mode send only codes and identifiers. Their allowed values are:

- `category`: `reported_mismatch`, `changed_requirement`, `preference`,
  `disagreement`, `uncertain`.
- `basis`: `prior_requirement`, `new_requirement`, `unknown`.
- `layer` (optional cause hypothesis): `absent`, `not_loaded`,
  `loaded_not_applied`, `check_missed`, `unknown`. Without a trace showing what
  was loaded and applied, use `unknown`; the agent's own report does not
  establish the layer.
- `trace_refs` (optional): up to eight identifiers of available traces.

A correction annotation requires `category` and `basis`. An `allowed_behavior`
record takes no category or layer; annotate it only with trace references or,
in content mode, text.

Text fields are optional and limited to 1,500 characters each. A maximum of four
distinct annotations is retained per candidate; identical annotations are
idempotent. An annotation cannot change source, capture mode, expiry or review
status. Neither disagreement nor agreement in the conversation automatically
confirms a failure.

```text
python -I -B hooks/runtime/feedback_cli.py annotate CANDIDATE_ID --state-dir /absolute/private-assay-data --input annotation.json
```

The notice includes the resolved script/data location because a model's shell may
not inherit plugin-only environment variables. A sandbox or read-only restriction
can still prevent annotation. Do not bypass it: the hook's existing candidate can
remain unannotated. Do not interrupt the task or ask the user to fill in a form for
every signal.

## Review, export and remove

Review is an explicit later action, not part of automatic capture. The local CLI
is not an authentication boundary against a process running as the same OS user;
its review provenance is `explicit_local_review_unattested`, not authenticated
human approval. Only annotation is requested of the working model.

```text
python -I -B hooks/runtime/feedback_cli.py review CANDIDATE_ID --state-dir /absolute/private-assay-data --status confirmed --basis-ref TASK-12 --layer not_loaded
python -I -B hooks/runtime/feedback_cli.py review CANDIDATE_ID --state-dir /absolute/private-assay-data --status dismissed --reason-code new_requirement
python -I -B hooks/runtime/feedback_cli.py review CANDIDATE_ID --state-dir /absolute/private-assay-data --status duplicate --duplicate-of OTHER_ID --reason-code same_incident
python -I -B hooks/runtime/feedback_cli.py review CANDIDATE_ID --state-dir /absolute/private-assay-data --status candidate --reason-code new_evidence
python -I -B hooks/runtime/feedback_cli.py export --state-dir /absolute/private-assay-data
python -I -B hooks/runtime/feedback_cli.py delete CANDIDATE_ID --state-dir /absolute/private-assay-data
```

| Status | Review code | Required |
| --- | --- | --- |
| `confirmed` | — | `--basis-ref`: identifier of the evidence the confirmation rests on |
| `dismissed` | `not_a_correction`, `new_requirement`, `preference`, `insufficient_evidence`, `out_of_scope`, `other` | a code; in content mode a code or `--reason` |
| `duplicate` | `same_incident` | a code or reason, and `--duplicate-of` a retained record |
| `candidate` | `reopened`, `new_evidence` | a code or reason |

A metadata record is reviewed with codes only, so a false candidate can be kept
as dismissed instead of deleted, and free text cannot enter through a review.
`--reason` is accepted only in content mode. `--layer` records the reviewer's
cause hypothesis. Each review is appended to a history of up to eight entries
and `review` shows the latest; the source observation is never rewritten. A full
history is an explicit error, not silent replacement: export the record or delete
it by owner decision. Duplicate review links two retained records; it does not
merge their source observations. `export` emits JSONL to stdout, with no network transfer
and no implicit file creation. Shell redirection has the shell's ordinary overwrite
semantics. Never pipe an unsanitized export into an eval corpus or public commit.
There is no automatic clustering, promotion, replay or Assay modification.

Records use the existing transactional SQLite implementation in
`<state_dir>/feedback/routing-v2.sqlite3`, isolated from routing receipts and hook
reminder state. The filename belongs to that existing store format; the directory
separates its ownership and lifetime. There is a 512-candidate cap and a 90-day
logical lifetime from capture; annotations do not extend it. At capacity, new
capture fails with a fixed diagnostic rather than silently evicting old evidence.
Inspect/export/delete explicitly to make room.

Expired records are removed on the next store transaction, including inspection;
this is not a background cleanup service or a secure-erasure guarantee. Disabling
capture does not remove old files, OS backups or exports. To stop automatic
capture set `feedback_trigger` to `explicit`; to stop all recording set
`feedback_capture` to `off`. Remove only the optional native entries you added,
not the existing Claude/Codex plugin handler or foreign hooks. Delete selected
records explicitly. The isolated feedback directory can be retired by its owner
when no collector is using it; do not remove the routing data directory by mistake.

## Upgrade, compatibility and rollback

Records written by the first collector version (schema 1) remain readable. Fields
they never stored read as `unknown`, their kind reads as `correction` because that
version only kept correction-grammar candidates, and review history starts with
the last review that survived. Nothing is rewritten in bulk; a record is upgraded
only when it is annotated or reviewed. New fields are additive and keep every key
the first version read, so an older collector can still list and inspect them.

Before switching an operational installation, copy the `<state_dir>/feedback`
directory outside the managed roots and stop clients that write to it. Do not run
old and new writers against the same directory at the same time. To roll back to
the first collector version, set `feedback_capture` to `off` and remove the
`feedback_trigger` key before restoring the earlier code: that version rejects
the unknown key and treats `metadata` as enabling automatic capture. Keep the
newer records; deleting the directory is a separate owner decision.

## Check the implementation without calling a model

From a contributor checkout with `requirements-tools.txt` installed:

```text
python -B -m unittest tools.test_feedback_capture
python -B tools/check.py --all
```

Fixtures exercise native JSON envelopes, positive/negative prompt cases,
idempotency, real SQLite reopen/concurrency, source preservation, consent modes,
the separate trigger, explicit records and their boundaries, coded metadata
review and its history, reading first-version records, expiry/capacity, CLI
operation, absence of network access and isolation from existing hook results. These
checks do not measure classifier recall on real conversations, native installation,
model adherence or improved engineering outcomes. A saved command input is labelled
`command_input_unattested`; it is not a verified client execution receipt.

## Primary client contracts

- [Claude Code hooks](https://code.claude.com/docs/en/hooks): prompt input,
  additional context and native command lifecycle.
- [Codex hooks](https://developers.openai.com/codex/hooks): native turn identity,
  prompt context, plugin trust and command-hook support.
- [Cursor hooks](https://cursor.com/docs/hooks): conversation/generation identity,
  `beforeSubmitPrompt` output and `postToolUse.additional_context`.
- [Gemini CLI hooks reference](https://geminicli.com/docs/hooks/reference/): common
  input, `BeforeAgent`, and its distinct settings/output contract.
