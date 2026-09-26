# Optional portable map and offline handoff

Use for a large handoff that needs stable links, reproducible export or change
comparison. It is not required for a bounded text answer and does not replace
source investigation, a browser, designer judgment or a canvas adapter.

The bundled `scripts/flow_map.py` uses Python 3.11+ standard library only. It never
connects to the network, executes application code, follows evidence URLs or
writes a Figma file. The input schema is intentionally small and closed; unknown
fields and versions fail instead of being silently ignored.

## Commands

Run from the Assay checkout; use a new, authorized output directory whose parent
already exists. Input/output paths below are examples, not required project paths.

```sh
python -B skills/product-flow-mapping/scripts/flow_map.py check path/to/map.json
python -B skills/product-flow-mapping/scripts/flow_map.py check path/to/map.json --require-no-gaps
python -B skills/product-flow-mapping/scripts/flow_map.py export path/to/map.json --notes path/to/notes.json --output path/to/new-handoff
python -B skills/product-flow-mapping/scripts/flow_map.py diff path/to/previous/map.json path/to/current/map.json
```

Exit 0 means the requested structural operation succeeded, not that the map is
complete or behavior verified. Exit 1 means a checkable invariant is refuted
(dangling references, wrong state/action links, stale image binding). Exit 2 means
missing/invalid input, missing required evidence, or recorded gaps under
`--require-no-gaps`. A source-only map can pass ordinary structural validation
while reporting missing captures and unexecuted observations. Empty inputs fail.

`export` creates `index.html`, `map.json`, `handoff.json`, `notes.json` and reviewed
PNG copies under `captures/`. Image bytes are preserved after the recorded
redaction review; the exporter does not redact or strip metadata itself. Open `index.html` locally. It includes paired steps,
branches, source references, capture provenance, gaps and the reverse index. No
remote assets or executable user HTML are embedded. `handoff.json` describes
editable frame pairs and stable keys for an adapter; it is not a Figma API script.
It explicitly records `canvas_delivery: not performed`.

Exports are create-only snapshots. An existing destination is refused, even when
empty. Files are exclusively created and the HTML index is published last; a
concurrent file is not overwritten. A write failure can leave a partial new snapshot, which is reported as a
failure rather than deleted under a reader. The user-owned notes input is never
modified; unmatched notes are retained and displayed. Regenerate into a new
snapshot and reconcile canvas nodes by stable keys, preserving manual regions.
The exporter does not perform live Figma reconciliation or certify its success.
`handoff.json` retains complete action records, even without scenario use, and
resolves callout labels. HTML exposes screen purposes, state conditions, action
effects/roles, entry/terminal states and evidence rather than hiding these in JSON.

## Schema version 1

All listed fields are required unless explicitly optional below. Arrays are nonempty except captures, step
`capture_ids`, capture `callouts` and optional action `shared_screen_ids`. Use an empty string only for an unmapped
inventory `target_id` or an intentionally empty note. IDs are ASCII letters
followed by letters, digits, underscore or hyphen (up to 80 characters). IDs are
unique ignoring case within their collection; step IDs are unique ignoring case
within a scenario. Generated images use `captures/capture-<ID>.png`, so a legal
ID such as `CON` does not produce a Windows reserved device filename. HTML step
anchors use the slash-delimited scenario/step key, not ambiguous hyphen joining.

| Collection | Record fields |
| --- | --- |
| `product` (one object) | `name`, `revision`, `scope` |
| `evidence` | `id`, `kind`, `locator`, `revision`, `detail` |
| `screens` | `id`, `title`, `purpose` |
| `states` | `id`, `screen_id`, `title`, `conditions`, `evidence_ids` |
| `actions` | `id`, `screen_id`, `kind`, `label`, `role`, `availability`, `effect`, `scope`, `evidence_ids` |
| `scenarios` | `id`, `title`, `goal`, `actor`, `prerequisites`, `entry_state_ids`, `terminal_state_ids`, `evidence_ids`, `steps` |
| Scenario step | `id`, `before`, `action_id`, `after`, `condition`, `result`, `layer`, `verification`, `evidence_ids`, `capture_ids` |
| `inventory` | `id`, `kind`, `evidence_ids`, `disposition`, `target_id`, `reason` |
| `captures` | `id`, `state_id`, `file`, `sha256`, `width`, `height`, `scope`, `source_revision`, `readiness`, `captured_at`, `simulated`, `redaction`, `evidence_ids`, `callouts` |
| Capture callout | `number`, `action_id`, `box`, `image_sha256` |

The root also contains integer `schema_version: 1`. See the complete
[source-only example](../examples/source-only-map.json), which is synthetic,
contains no screenshots and makes no claim about Routevane runtime behavior.

An action may additionally declare `shared_screen_ids`: other screens exposing
the same canonical control/event. The primary `screen_id` and additional screens
must be distinct, valid screen IDs. Both steps and callouts may use those surfaces.
Do not use this to merge context-dependent effects merely because labels match.
Existing single-screen maps remain valid without the optional field.

Evidence `kind`: requirement, documentation, code, runtime or inference. An action
`kind` is control or system. A step's `layer` is observed, intended or proposed;
`verification` is executed, read, unverified or blocked. An executed claim needs
a runtime source; an intended outcome needs an adopted requirement source.
This checks the declared provenance, not the truthfulness of that source. An
executed step supported only by other runtime revisions records an applicability
gap. Requirement/documentation revisions are not forced to equal the product
build. Every declared entry must lead to a recorded terminal. Mixed-layer graphs
remain representable but record a gap: their combined reachability is not proof
of an executable current-product path. In the handoff, `next_step_keys` stay
within one claim layer; `related_step_keys` carry cross-layer relations instead.

Inventory `kind` is goal, screen, state or action; its target is respectively a
scenario, screen, state or action. `disposition` is mapped, unresolved or excluded.
The last two use an empty target and a meaningful reason. Independently discovered
items must not be generated solely from the map to manufacture a clean inventory.

Capture paths are relative to the map, confined to that folder, without symlinks,
reparse points or platform-ambiguous names. Only PNG is accepted by this optional
exporter; other media can stay in ordinary prose/adapter handoff. Width and height
are positive integers up to 20,000. The exporter checks envelope, dimensions and
SHA-256, not full PNG decoding; visual inspection is still required. The limits
are resource guards, not UX thresholds: 8 MiB JSON, 24 MiB per image, 128 MiB total.
`simulated` is boolean. A non-simulated capture needs runtime state evidence;
this alone still does not prove an action was executed. `redaction` is reviewed or not-reviewed; export refuses
unreviewed images. This flag is not an automatic secret scan or publication consent.

Callout `box` is normalized `[x, y, width, height]` inside the image. Its action
must be a control on the depicted screen; `image_sha256` must match that capture.
Replacing the image requires new coordinates or explicit revalidation. A capture
attached to a step must show one of its endpoints. Same-screen actions retain
separate steps and are labeled UNCHANGED STATE / MOMENT UNSPECIFIED; neither
a temporal BEFORE claim nor an after-screen is invented. Conditions are text, not a formally proven state-machine guard.

`notes.json` is an object from `scenarioID/stepID` to text. Keep it outside
regenerated map content. `diff` returns changed records, affected scenarios and
retirement candidates, never deletion commands. Inventory changes, changes to evidence used only by inventory items and product
scope/revision changes also set `coverage_review_required`, even when scenario
records themselves are unchanged. Mapped inventory changes propagate to the
known consuming scenarios; excluded/unresolved changes remain coverage review
work rather than being discarded. Shared source/action changes
propagate to consuming scenarios. The caller still verifies semantic dependencies,
current canvas identity and annotation placement before any write.
