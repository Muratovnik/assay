"""Make a declared publication derivative of captured comparison evidence.

The private rule file supplies reviewed literal prefixes; the public code and
manifest carry no encoded substitute for those private values. Original records
are copied byte-for-byte to the new output's private directory. No source input
is overwritten and no submitted program, model, or saved checker is executed.
"""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re

from comparison_report import new_plain_directory


FILES = ("comparison-evidence.json", "comparison-grades.json")
MANIFEST = "comparison-publication.json"
HEX_DIGEST = re.compile(r"(?<![0-9a-f])[0-9a-f]{64}(?![0-9a-f])")
KINDS = {"task-identifier-normalization", "home-cache-redaction"}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def load_rules(raw):
    value = json.loads(raw)
    require(value.get("schema_version") == 1, "Unsupported private rule schema")
    rules = value.get("rules")
    require(isinstance(rules, list) and len(rules) == 2, "Exactly two reviewed rules are required")
    require({row.get("kind") for row in rules} == KINDS, "Unexpected normalization categories")
    require(len({row.get("id") for row in rules}) == 2, "Rule IDs must be unique")
    compiled = []
    for row in rules:
        source, published = row.get("source_prefix"), row.get("published_prefix")
        require(isinstance(source, str) and source.startswith("/") and source.endswith("/"),
                "Private source prefixes must be complete absolute directory prefixes")
        require(isinstance(published, str) and published and published != source,
                "A visible publication replacement is required")
        require(isinstance(row.get("expected_occurrences"), int) and row["expected_occurrences"] > 0,
                "Each reviewed rule must declare its expected occurrence count")
        expression = re.escape(source)
        names = row.get("following_name_prefixes")
        if row["kind"] == "task-identifier-normalization":
            require(names == ["trial_", "assessment_"], "Only the captured canonical task-name families are supported")
            require(published == "agent:", "Task identifiers must use the declared nonpath namespace")
            expression += "(?=(?:" + "|".join(map(re.escape, names)) + "))"
        else:
            require(names is None and published == "[PLAYWRIGHT_CACHE]/",
                    "Home-cache redaction must use the declared named placeholder")
        compiled.append((row, re.compile(expression)))
    return compiled


def normalize(text, rules):
    matches = []
    for rule, pattern in rules:
        matches.extend((match.start(), match.end(), rule) for match in pattern.finditer(text))
    matches.sort(key=lambda item: item[0])
    previous = 0
    result, locations = [], []
    for start, end, rule in matches:
        require(start >= previous, "Reviewed prefix replacements overlap")
        result.extend((text[previous:start], rule["published_prefix"]))
        locations.append({
            "kind": rule["kind"], "rule_id": rule["id"],
            "original_byte_offset": len(text[:start].encode("utf-8")),
            "original_utf8_bytes": len(text[start:end].encode("utf-8")),
            "published_utf8_bytes": len(rule["published_prefix"].encode("utf-8")),
            "line": text.count("\n", 0, start) + 1,
            "column": start - text.rfind("\n", 0, start),
        })
        previous = end
    result.append(text[previous:])
    return "".join(result), locations


def publication_data(raw, document, changes):
    return {
        "schema_version": 1,
        "kind": "reviewed-publication-derivative",
        "original_sha256": digest(raw),
        "original_utf8_bytes": len(raw),
        "original_blob_count": len(document["blobs"]),
        "manifest_file": MANIFEST,
        "blob_changes": changes,
    }


def transform(source, rules, original_bytes):
    documents = {name: json.loads(raw) for name, raw in original_bytes.items()}
    evidence, grades = (documents[name] for name in FILES)
    require("publication" not in evidence and "publication" not in grades,
            "Publication derivatives cannot be used as private originals")
    require(grades["evidence_sha256"] == digest(original_bytes[FILES[0]]),
            "Original grades do not bind the original evidence")
    original_blobs = {}
    for document in documents.values():
        require(isinstance(document["blobs"], dict) and document["blobs"], "Missing original blobs")
        for sha, content in document["blobs"].items():
            require(isinstance(content, str) and digest(content.encode("utf-8")) == sha,
                    "Original retained blob does not match its digest")
            require(sha not in original_blobs or original_blobs[sha] == content,
                    "Conflicting original blob bytes")
            original_blobs[sha] = content

    # Preserve opaque original measurements. Only materialized publication bytes
    # receive separate published_* sizes; no observed output size is rewritten.
    normalized = {sha: normalize(content, rules) for sha, content in original_blobs.items()}
    dependencies = {
        sha: {match.group() for match in HEX_DIGEST.finditer(content)} & original_blobs.keys()
        for sha, content in original_blobs.items()
    }
    changed = {sha for sha, (content, _) in normalized.items() if content != original_blobs[sha]}
    while True:
        additions = {sha for sha, refs in dependencies.items() if sha not in changed and refs & changed}
        if not additions:
            break
        changed.update(additions)

    published_blobs, mapping, visiting, locations = {}, {}, set(), {}

    def rebuild(sha):
        if sha in mapping:
            return mapping[sha]
        if sha not in changed:
            mapping[sha] = sha
            published_blobs[sha] = original_blobs[sha]
            return sha
        require(sha not in visiting, "A changed content-addressed blob has a cyclic dependency")
        visiting.add(sha)
        for dependency in sorted(dependencies[sha] & changed):
            rebuild(dependency)
        content, local_changes = normalized[sha]
        local_changes = list(local_changes)
        for match in HEX_DIGEST.finditer(original_blobs[sha]):
            old_reference = match.group()
            new_reference = mapping.get(old_reference, old_reference)
            if old_reference != new_reference:
                local_changes.append({
                    "kind": "digest-rebind",
                    "original_byte_offset": len(original_blobs[sha][:match.start()].encode("utf-8")),
                    "original_sha256": old_reference,
                    "published_sha256": new_reference,
                })
        content = HEX_DIGEST.sub(lambda match: mapping.get(match.group(), match.group()), content)
        new_sha = digest(content.encode("utf-8"))
        require(new_sha != sha, "Declared changed blob remained byte-identical")
        require(new_sha not in original_blobs, "Publication blob collides with another original identity")
        require(new_sha not in published_blobs or published_blobs[new_sha] == content,
                "Publication digest collision")
        published_blobs[new_sha], mapping[sha], locations[sha] = content, new_sha, local_changes
        visiting.remove(sha)
        return new_sha

    for sha in sorted(original_blobs):
        rebuild(sha)

    blob_changes = []
    for old_sha in sorted(changed):
        new_sha = mapping[old_sha]
        blob_changes.append({
            "original_sha256": old_sha, "published_sha256": new_sha,
            "original_utf8_bytes": len(original_blobs[old_sha].encode("utf-8")),
            "published_utf8_bytes": len(published_blobs[new_sha].encode("utf-8")),
            "categories": sorted({row["kind"] for row in locations[old_sha]}),
            "locations": locations[old_sha],
        })
    changed_by_original = {row["original_sha256"]: row for row in blob_changes}
    changed_by_published = {row["published_sha256"]: row for row in blob_changes}
    metadata_changes = []

    def rewrite(value, path):
        if isinstance(value, dict):
            return {key: rewrite(item, path + "." + key) for key, item in value.items()}
        if isinstance(value, list):
            return [rewrite(item, f"{path}[{i}]") for i, item in enumerate(value)]
        if not isinstance(value, str):
            return value
        result, changed_locations = normalize(value, rules)
        for match in HEX_DIGEST.finditer(value):
            old = match.group()
            new = mapping.get(old, old)
            if old != new:
                changed_locations.append({"kind": "digest-rebind", "original_sha256": old,
                                          "published_sha256": new,
                                          "original_byte_offset": len(value[:match.start()].encode("utf-8"))})
        result = HEX_DIGEST.sub(lambda match: mapping.get(match.group(), match.group()), result)
        if result != value:
            metadata_changes.append({
                "path": path, "original_sha256": digest(value.encode("utf-8")),
                "published_sha256": digest(result.encode("utf-8")),
                "original_utf8_bytes": len(value.encode("utf-8")),
                "published_utf8_bytes": len(result.encode("utf-8")),
                "locations": changed_locations,
            })
        return result

    public_documents = {}
    for name, document in documents.items():
        public = rewrite({key: value for key, value in document.items() if key != "blobs"}, name)
        public["blobs"] = {
            mapping[sha]: published_blobs[mapping[sha]] for sha in sorted(document["blobs"], key=lambda sha: mapping[sha])
        }
        own_changes = [changed_by_original[sha] for sha in sorted(set(document["blobs"]) & changed)]
        public["publication"] = publication_data(original_bytes[name], document, own_changes)
        public_documents[name] = public

    public_evidence, public_grades = (public_documents[name] for name in FILES)
    affected_runs = []
    for original, public in zip(evidence["runs"], public_evidence["runs"], strict=True):
        require(original["run_id"] == public["run_id"], "Run identity changed")
        require(original["source_files"] == public["source_files"], "A task source blob changed")
        for metric in ("output_utf8_bytes", "answer_utf8_bytes"):
            require(original.get(metric) == public.get(metric), "An observed byte metric changed")
        original_sizes = {
            name: changed_by_published[sha]["original_utf8_bytes"] if sha in changed_by_published
            else len(published_blobs[sha].encode("utf-8"))
            for name, sha in public["output_files"].items()
        }
        require(sum(original_sizes.values()) == original["output_utf8_bytes"], "Original output byte total differs")
        require(original_sizes.get("answer.md", 0) == original["answer_utf8_bytes"], "Original answer byte total differs")
        if original["output_files"] != public["output_files"]:
            public["published_output_utf8_bytes"] = sum(
                len(published_blobs[sha].encode("utf-8")) for sha in public["output_files"].values())
            public["published_answer_utf8_bytes"] = len(
                published_blobs[public["output_files"]["answer.md"]].encode("utf-8")) if "answer.md" in public["output_files"] else 0
            affected_runs.append(original["run_id"])

    for field in ("runs", "adjudications", "assessment_summary", "scope_sensitivity",
                  "calibration_scope_note", "adjudication_policy", "measurement_boundary"):
        require(grades[field] == public_grades[field], "A grading result or interpretation changed: " + field)
    require(evidence["deterministic_receipts"] == public_evidence["deterministic_receipts"],
            "A deterministic measurement receipt identity changed")
    raw_assessments = {row["assessment_id"]: row["output_sha256"]
                       for row in grades["assessment_provenance"]["assessments"]}
    require(raw_assessments == {row["assessment_id"]: row["output_sha256"]
                                for row in public_grades["assessment_provenance"]["assessments"]},
            "An original assessment output changed")

    preserved_inputs = {}
    for filename in ("comparison-plan.json", "comparison-cases.json", "comparison-rubric.json",
                     "comparison-case-metadata.json", "comparison-protocol.md"):
        payload = (source / filename).read_bytes()
        preserved_inputs[filename] = {"sha256": digest(payload), "utf8_bytes": len(payload)}
        require(not any(sha.encode("ascii") in payload for sha in changed),
                "An immutable task/design record depends on a changed blob")
    require(preserved_inputs["comparison-plan.json"]["sha256"] == evidence["plan_sha256"],
            "Frozen plan identity differs")
    require(preserved_inputs["comparison-rubric.json"]["sha256"] == grades["rubric_sha256"],
            "Frozen rubric identity differs")

    public_bytes = {FILES[0]: encoded(public_evidence)}
    public_grades["evidence_sha256"] = digest(public_bytes[FILES[0]])
    public_bytes[FILES[1]] = encoded(public_grades)
    occurrences = Counter(row["rule_id"] for _, rows in normalized.values() for row in rows)
    occurrences.update(row["rule_id"] for item in metadata_changes for row in item["locations"] if "rule_id" in row)
    public_rules = []
    for rule, _ in rules:
        require(occurrences[rule["id"]] == rule["expected_occurrences"],
                "Reviewed prefix occurrence count changed: " + rule["id"])
        public_rules.append({
            "id": rule["id"], "kind": rule["kind"],
            "source_prefix_sha256": digest(rule["source_prefix"].encode("utf-8")),
            "source_prefix_utf8_bytes": len(rule["source_prefix"].encode("utf-8")),
            "published_prefix": rule["published_prefix"],
            "following_name_prefixes": rule.get("following_name_prefixes"),
            "occurrences": occurrences[rule["id"]],
        })
    manifest = {
        "schema_version": 1,
        "kind": "reviewed-publication-derivative",
        "files": {name: {
            "original_sha256": digest(original_bytes[name]), "published_sha256": digest(public_bytes[name]),
            "original_utf8_bytes": len(original_bytes[name]), "published_utf8_bytes": len(public_bytes[name]),
        } for name in FILES},
        "rules": public_rules,
        "blob_changes": blob_changes,
        "metadata_changes": metadata_changes,
        "file_digest_rebindings": [{"path": FILES[1] + ".evidence_sha256",
            "original_sha256": digest(original_bytes[FILES[0]]), "published_sha256": digest(public_bytes[FILES[0]])}],
        "preserved_inputs": preserved_inputs,
        "preservation_checks": {
            "original_blob_count": len(original_blobs), "changed_blob_count": len(changed),
            "unchanged_blob_count": len(original_blobs) - len(changed),
            "changed_by_file": {name: len(document["publication"]["blob_changes"])
                                for name, document in public_documents.items()},
            "affected_output_run_ids": affected_runs,
            "original_observed_byte_metrics_preserved": True,
            "source_file_inventories_preserved": True,
            "deterministic_receipt_identities_preserved": True,
            "assessment_output_sha256": raw_assessments,
            "final_grading_and_adjudication_values_preserved": True,
        },
        "interpretation": {
            "originals": "Byte-identical original records are retained privately under the declared original digests.",
            "publication": "This is a reviewed derivative. Changed blobs and their dependent inventories are separately identified.",
            "measurements": "output_utf8_bytes and answer_utf8_bytes describe original captured outputs. The published_* fields describe changed publication outputs.",
            "recorded_implementation": "Three captured coordinator-source copies normalize task identifiers. They are publication derivatives, not claims of byte-identical executable originals.",
            "verification_limit": "Public hashes verify the published derivative and bind the original commitments. Verifying the transformation against original bytes also requires the private original records and reviewed literal-prefix rule file.",
        },
        "transformer_sha256": digest(Path(__file__).read_bytes()),
    }
    public_bytes[MANIFEST] = encoded(manifest)

    # Recheck the complete public surface, including the manifest. Publication
    # records never retain the literal private prefixes as an encoded payload.
    for filename, payload in public_bytes.items():
        text = payload.decode("utf-8")
        for rule, pattern in rules:
            require(not pattern.search(text), "Unnormalized reviewed prefix remains in " + filename)
    require(sum(len(doc["blobs"]) for doc in documents.values()) ==
            sum(len(doc["blobs"]) for doc in public_documents.values()), "Blob inventory cardinality changed")
    return public_bytes, manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-directory", type=Path, required=True)
    parser.add_argument("--rules", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--expected-evidence-sha256", required=True)
    parser.add_argument("--expected-grades-sha256", required=True)
    args = parser.parse_args()
    require(not args.output.exists(), "Output must be a new directory")
    originals = {name: (args.source_directory / name).read_bytes() for name in FILES}
    for name, expected in zip(FILES, (args.expected_evidence_sha256, args.expected_grades_sha256), strict=True):
        require(digest(originals[name]) == expected, "Pinned original file digest differs: " + name)
    rule_bytes = args.rules.read_bytes()
    rules = load_rules(rule_bytes)
    public_bytes, manifest = transform(args.source_directory, rules, originals)
    new_plain_directory(args.output)
    private = args.output / "private"
    public = args.output / "public"
    private.mkdir()
    public.mkdir()
    for name, payload in originals.items():
        (private / name).write_bytes(payload)
        require((private / name).read_bytes() == payload, "Private original copy differs")
    (private / "publication-rules.json").write_bytes(rule_bytes)
    for name, payload in public_bytes.items():
        (public / name).write_bytes(payload)
    print(json.dumps({"output": str(args.output), "files": manifest["files"],
                      "rules": {row["id"]: row["occurrences"] for row in manifest["rules"]},
                      "preservation_checks": manifest["preservation_checks"]}, indent=2))


if __name__ == "__main__":
    main()
