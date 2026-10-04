# Collect feedback candidates from ordinary work

Use this when user corrections should leave a local record for later review,
without running another model or a benchmark campaign. A candidate means
**a correction signal was observed**, not that the agent, skill or user is wrong.
The same working model can annotate it using the conversation it already has.

Capture is off by default. It never reads transcripts, attachments, repository
files or tool outputs to infer a failure; it does not change skills, create evals,
call a service or schedule another model turn. The hook notice and any annotation
tool call still consume time and context in the existing turn.

## Enable capture and find the first record

You need Python 3.11+ and the existing `hooks/requirements.txt` dependencies in
the interpreter used by the hook. The full plugin or a full checkout must contain
`hooks/runtime` and `skills/route-subagents/scripts`: a skills-only installation
does not supply this runtime. See [hook setup](hooks.md) first.

Create an owner-controlled JSON configuration outside a tracked repository and
set `ASSAY_HOOK_CONFIG` to its absolute path in the environment starting the
client. Choose an absolute private data directory. For example:

```json
{
  "state_dir": "/absolute/private-assay-data",
  "feedback_capture": "metadata"
}
```

On Windows, use an actual Windows absolute path, for example
`C:/private-assay-data`, not the POSIX placeholder above. Existing
`disabled_rules`, `disabled_skills` and `record_events` options can remain in the
same file. Without an explicit `state_dir`, full plugins can use their existing
`PLUGIN_DATA` / `CLAUDE_PLUGIN_DATA` location. Cursor and Gemini setup should use
an explicit directory so the native hook and later inspection agree.

| Mode | What is retained |
| --- | --- |
| `off` | No feedback records or notices. This is the default. |
| `metadata` | Client, native session/delivery IDs when available, hashed scope, timestamps, signal class, installed Assay version and categorical annotations. No prompt excerpt or free-text annotation. |
| `content` | The metadata plus the first 4,096 characters of the correcting prompt and permitted short annotations/review reasons. Truncation is explicit. |

**Before enabling `content`:** excerpts are verbatim, not automatically sanitized.
They may contain private code, credentials or personal data. No full transcript is
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

These are command adapters, not a claim that every historical client version,
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
In metadata mode send only `category` and `basis`. Their allowed values are:

- `category`: `reported_mismatch`, `changed_requirement`, `preference`,
  `disagreement`, `uncertain`.
- `basis`: `prior_requirement`, `new_requirement`, `unknown`.

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
python -I -B hooks/runtime/feedback_cli.py review CANDIDATE_ID --state-dir /absolute/private-assay-data --status confirmed --reason "Checked against the earlier requirement and actual artifact."
python -I -B hooks/runtime/feedback_cli.py review CANDIDATE_ID --state-dir /absolute/private-assay-data --status dismissed --reason "The requirement changed after the original work."
python -I -B hooks/runtime/feedback_cli.py review CANDIDATE_ID --state-dir /absolute/private-assay-data --status duplicate --duplicate-of OTHER_ID --reason "Same underlying incident."
python -I -B hooks/runtime/feedback_cli.py export --state-dir /absolute/private-assay-data
python -I -B hooks/runtime/feedback_cli.py delete CANDIDATE_ID --state-dir /absolute/private-assay-data
```

`candidate` is also an allowed review status for reopening a judgment. Duplicate
review links two retained records; it does not merge their source observations.
Free-text review requires content consent; metadata records can still be annotated
categorically or deleted. `export` emits JSONL to stdout, with no network transfer
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
capture does not remove old files, OS backups or exports. To stop capture set
`feedback_capture` to `off`; remove only the optional native entries you added,
not the existing Claude/Codex plugin handler or foreign hooks. Delete selected
records explicitly. The isolated feedback directory can be retired by its owner
when no collector is using it; do not remove the routing data directory by mistake.

## Check the implementation without calling a model

From a contributor checkout with `requirements-tools.txt` installed:

```text
python -B -m unittest tools.test_feedback_capture
python -B tools/check.py --all
```

Fixtures exercise native JSON envelopes, positive/negative prompt cases,
idempotency, real SQLite reopen/concurrency, source preservation, consent modes,
expiry/capacity, CLI operation and isolation from existing hook results. These
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
