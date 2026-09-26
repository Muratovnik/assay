# Prepare a behavior handoff for a redesign

Use [product-flow-mapping](../../skills/product-flow-mapping/SKILL.md) with the
existing product and the requested audience/format. For example:

> Reconstruct the current Routevane user journeys for a designer. Inspect the
> documentation, routes, controls and available runtime without changing the
> app. Relate each task and action to its screen/state, result, alternatives and
> evidence. In the authorized Figma destination, use adjacent editable description
> and screenshot frames, plus an overview and reverse index. Keep existing
> behavior, adopted intent and redesign proposals separate. Do not send rules to
> real devices or expose subscription secrets; mark unavailable runtime/canvas
> evidence explicitly.

A repository URL alone supplies no running application or target Figma file.
The method can prepare a source-backed map while those observations are missing;
it must not claim verified behavior or a completed canvas transfer.

## Try the portable example locally

From the Assay checkout, choose a new output directory. This example is synthetic,
not a Routevane walkthrough; missing captures are intentionally visible.

```sh
python -B skills/product-flow-mapping/scripts/flow_map.py check skills/product-flow-mapping/examples/source-only-map.json
python -B skills/product-flow-mapping/scripts/flow_map.py export skills/product-flow-mapping/examples/source-only-map.json --notes skills/product-flow-mapping/examples/notes.json --output ./flow-map-example
```

Open `flow-map-example/index.html`. The output also contains `map.json`, a portable
`handoff.json`, separate notes and any supplied sanitized captures. Existing output
directories are refused. Use another snapshot directory for a repeat export and
retain your notes input; never store owner notes only inside generated HTML.

For a real capture, use the established application/browser fixture, record the
state, build and readiness, sanitize it, and add its PNG hash/dimensions and
callouts to the map. See the [portable schema and commands](../../skills/product-flow-mapping/references/portable-map.md).
The optional tool checks declared provenance and references, not the truth of an
observation or the full decoding/usability of an image.

## Routevane first slice

A useful first slice from the product documentation is lists/categories ->
profile -> output formats/forecast -> build -> obtain the result, plus a failed
refresh that preserves the previous published output. Treat this as a starting
scope from the [Routevane README](https://github.com/Muratovnik/routevane/blob/main/README.md),
not an executed or exhaustive inventory. Check its current source/build before
attributing live behavior. Building a result, downloading it and sending it to a
device are different actions. Use only permitted disposable resources for the
last one; blocked execution should remain blocked, not silently simulated.
