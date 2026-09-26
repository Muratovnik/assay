# Model-specific guidance and upgrade checks

Read when a model/client upgrade changes a routing assumption, or when vendor
advice appears to conflict across available routes. The existing
[benchmark service](benchmark-routing.md) owns acquisition and measurements;
this reference explains its documentation scope. No model ranking, new service,
subscription-price conversion or automatic client migration is introduced.

## Registered model-specific sources

These supplement the generic reasoning, thinking and model-choice documents.
The registry is `scripts/route_evidence/guides.py`; section extraction uses the
publisher's Markdown, exact headings and the existing drift/error handling.

| Guide ID | Documented models | Surface | Selected sections |
| --- | --- | --- | --- |
| `openai-gpt-6` | GPT-6 Astra, Sol, Luna | API | Limitations; Update API and model parameters |
| `openai-gpt-6-astra-skills` | GPT-6 Astra only | Codex | Better skills; Up-to-date AGENTS.md |
| `claude-opus-5-5` | Claude Opus 5.5 only | API/harness | Calibrate effort; Unattended agentic runs |

Sources and section scope were reviewed on 2026-09-22:
[GPT-6 migration](https://developers.openai.com/api/docs/guides/latest-model),
[Astra skills and prompts](https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra),
and [Opus 5.5 prompting](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5-5).
Registration and a successful fixture are not evidence of live source retrieval.
Recheck source availability through the existing online smoke before claiming it
works in an installed environment; errors remain acquisition gaps.

## Read the scope, not just the excerpt

`applies_to` retains the existing client labels. Each extracted document also
carries `applicability` with four fields:

- `models`: exact documented identities. An empty list means no additional
  model filter; exceptions inside the source still apply.
- `surfaces`: documented `api`, `codex` or `claude-code` use. An API surface does
  not establish that a native child tool accepts an option or enforces a limit.
- `conditions`: bounded registry annotations that accompany the excerpt. They
  are not quotations, benchmark observations or extra authority.
- `reviewed_on`: the registry scope-review date, or null for an older unreviewed
  entry. It is not a fetch, release or model-evaluation date.

During context acquisition, guides are filtered by client and the supplied
inventory's exact model identities or confirmed `evidence_names`. Lexical
normalization is allowed; guessing rolling aliases, dated variants or family
membership is not. A Sol/Luna-only inventory does not acquire Astra-only advice.
`routing_status` remains a catalog/cache inspection, not a routing decision.

Each available document's `matched_models` names the matching runtime IDs. This
survives compact responses and advisor projection, so a mixed-model plan cannot
treat an Astra document as evidence about every candidate. Empty means no match;
null means scope or inventory is unknown. Legacy snapshots without applicability
remain explicitly unknown, never silently universal. The registered conditions
and quoted section caveats still apply to matching routes.

Extractor version 2 requires validated scope and invalidates old derived caches.
Changes to registered scope also change the source fingerprint. This does not
migrate local configuration, refresh the native inventory or alter model routes.
The existing TTL refreshes registered URLs only: discovering a new guide or
checking changed model scope on an evergreen page remains a registry-maintenance
step. Unchanged headings cannot prove unchanged meaning. `reviewed_on` does not
advance merely because a fetch succeeded.

## Apply an upgrade without weakening the method

Keep task criteria in neutral skills and observed model differences in dated
source/run evidence. Do not infer that a new model makes test or visual oracles
unnecessary. Investigate actual irrelevant reading, repeated unchanged checks,
wrong rejections or premature stops before changing instructions. Use the
[skill evaluation method](../../skill-evaluation/SKILL.md) and its upgrade controls;
ordinary work receipts can support a narrow change without a paid campaign.

Reconfirm the current host's routes and permissions. Select effort deliberately,
preserve explicit user choices, and keep unknown capabilities and full-chain
cost unknown. A vendor's default or API price is neither a local outcome nor a
subscription-quota measurement. Follow [Codex](codex-routing.md) or
[Claude Code](claude-code-routing.md) for native execution and continuation.
