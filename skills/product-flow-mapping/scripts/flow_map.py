"""Check and export an evidence-linked product map without network or app writes.

Exit 0: the requested structural operation succeeded (not semantic acceptance).
Exit 1: a checkable map invariant is refuted. Exit 2: invalid/missing input or
required evidence. Exports are create-only; notes live in a separate input file.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import math
from pathlib import Path
import re
import shutil
import struct
import sys
import tempfile
from typing import Any

ID = re.compile(r"^[A-Za-z][A-Za-z0-9_-]{0,79}$")
SHA = re.compile(r"^[a-f0-9]{64}$")
MAX_JSON = 8 * 1024 * 1024
MAX_IMAGE = 24 * 1024 * 1024
MAX_IMAGES = 128 * 1024 * 1024
KINDS = {"goal": "scenarios", "screen": "screens", "state": "states", "action": "actions"}
GROUPS = ("evidence", "screens", "states", "actions", "scenarios", "inventory", "captures")


class MapError(ValueError):
    def __init__(self, message: str, code: int = 2):
        super().__init__(message)
        self.code = code


def require(condition: bool, message: str, code: int = 2) -> None:
    if not condition:
        raise MapError(message, code)


def keys(obj: Any, expected: str, where: str, *, optional: str = "") -> dict[str, Any]:
    require(isinstance(obj, dict), f"{where}: expected an object")
    required = set(expected.split())
    require(required <= set(obj) <= required | set(optional.split()),
            f"{where}: fields must be {expected}; optional: {optional or 'none'}")
    return obj


def text(value: Any, where: str, *, empty: bool = False) -> str:
    require(isinstance(value, str) and (empty or bool(value.strip())), f"{where}: expected text")
    return value


def array(value: Any, where: str, *, nonempty: bool = False) -> list[Any]:
    require(isinstance(value, list) and (not nonempty or bool(value)), f"{where}: expected an array")
    return value


def identifier(value: Any, where: str) -> str:
    require(isinstance(value, str) and bool(ID.fullmatch(value)), f"{where}: invalid ID")
    return value


def no_links(path: Path) -> None:
    # No shell, expansion, symlink traversal or reparse-point destination.
    for item in (path, *path.parents):
        require(not item.is_symlink(), f"linked path is not allowed: {item}")
        if item.exists():
            attrs = getattr(item.lstat(), "st_file_attributes", 0)
            require(not attrs & 1024, f"reparse point is not allowed: {item}")


def read_json(path: Path) -> dict[str, Any]:
    no_links(path)
    require(path.is_file(), f"missing input: {path}")
    require(path.stat().st_size <= MAX_JSON, f"JSON input too large: {path}")

    def unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            require(key not in result, f"duplicate JSON key: {key}")
            result[key] = value
        return result

    def bad_constant(value: str) -> None:
        raise MapError(f"non-finite JSON value: {value}")

    try:
        value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique,
                           parse_constant=bad_constant)
    except (UnicodeError, json.JSONDecodeError) as error:
        raise MapError(f"invalid JSON: {error}") from error
    require(isinstance(value, dict), "map must be a JSON object")
    return value


def image_bytes(root: Path, capture: dict[str, Any]) -> bytes:
    name = text(capture["file"], "capture file")
    require("\\" not in name and ":" not in name and not name.startswith("/"), "unsafe capture path")
    parts = name.split("/")
    require(all(part and part not in {".", ".."} and not part.endswith((".", " "))
                and not re.search(r'[<>"|?*\x00-\x1f]', part)
                and not re.fullmatch(r"(?:CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\..*)?", part, re.I)
                for part in parts), "unsafe capture path")
    path = root.joinpath(*parts)
    require(path.suffix.lower() == ".png", "portable captures must be PNG")
    no_links(path)
    require(path.is_file(), f"missing capture: {name}")
    require(path.stat().st_size <= MAX_IMAGE, f"capture too large: {name}")
    data = path.read_bytes()
    require(len(data) >= 45 and data[:16] == b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
            and data[-12:] == b"\x00\x00\x00\x00IEND\xaeB`\x82", f"invalid PNG envelope: {name}")
    require(struct.unpack(">II", data[16:24]) == (capture["width"], capture["height"]),
            f"capture dimensions disagree: {name}", 1)
    require(hashlib.sha256(data).hexdigest() == capture["sha256"], f"capture hash disagrees: {name}", 1)
    return data


def action_screens(action: dict[str, Any]) -> list[str]:
    """One canonical effect may be exposed on several verified screens."""
    return [action["screen_id"], *action.get("shared_screen_ids", [])]


def check(document: dict[str, Any], root: Path) -> dict[str, Any]:
    keys(document, "schema_version product " + " ".join(GROUPS), "map")
    require(type(document["schema_version"]) is int and document["schema_version"] == 1, "unsupported schema_version")
    product = keys(document["product"], "name revision scope", "product")
    for field, value in product.items():
        text(value, f"product.{field}")
    indexes: dict[str, dict[str, dict[str, Any]]] = {}
    for group in GROUPS:
        records = array(document[group], group, nonempty=group != "captures")
        index: dict[str, dict[str, Any]] = {}
        folded_ids: set[str] = set()
        for record in records:
            require(isinstance(record, dict), f"{group}: expected records")
            rid = identifier(record.get("id"), group)
            require(rid.casefold() not in folded_ids,
                    f"{group}: duplicate ID or case-colliding ID {rid}", 1)
            folded_ids.add(rid.casefold())
            index[rid] = record
        indexes[group] = index
    gaps: list[str] = []

    def reference(value: Any, group: str) -> dict[str, Any]:
        identifier(value, group)
        require(value in indexes[group], f"unknown {group} reference: {value}", 1)
        return indexes[group][value]

    def references(value: Any, group: str, *, nonempty: bool = True) -> list[str]:
        array(value, group, nonempty=nonempty)
        for ref in value:
            reference(ref, group)
        require(len(value) == len(set(value)), f"duplicate {group} reference", 1)
        return value

    for item in document["evidence"]:
        keys(item, "id kind locator revision detail", "evidence")
        require(item["kind"] in {"requirement", "documentation", "code", "runtime", "inference"}, "unknown evidence kind")
        for field in ("locator", "revision", "detail"):
            text(item[field], f"evidence.{field}")
    for item in document["screens"]:
        keys(item, "id title purpose", "screen")
        text(item["title"], "screen.title")
        text(item["purpose"], "screen.purpose")
    for item in document["states"]:
        keys(item, "id screen_id title conditions evidence_ids", "state")
        reference(item["screen_id"], "screens")
        text(item["title"], "state.title")
        text(item["conditions"], "state.conditions")
        references(item["evidence_ids"], "evidence")
    for item in document["actions"]:
        keys(item, "id screen_id kind label role availability effect scope evidence_ids", "action",
             optional="shared_screen_ids")
        array(item.get("shared_screen_ids", []), "action.shared_screen_ids")
        references(action_screens(item), "screens")
        require(item["kind"] in {"control", "system"}, "action kind must be control or system")
        for field in ("label", "role", "availability", "effect", "scope"):
            text(item[field], f"action.{field}")
        references(item["evidence_ids"], "evidence")

    total_bytes = 0
    for item in document["captures"]:
        keys(item, "id state_id file sha256 width height scope source_revision readiness captured_at simulated redaction evidence_ids callouts", "capture")
        state = reference(item["state_id"], "states")
        require(isinstance(item["sha256"], str) and bool(SHA.fullmatch(item["sha256"])), "invalid capture SHA-256")
        require(all(type(item[key]) is int and 0 < item[key] <= 20000 for key in ("width", "height")), "invalid image dimensions")
        for key in ("scope", "source_revision", "readiness", "captured_at"):
            text(item[key], f"capture.{key}")
        require(type(item["simulated"]) is bool, "simulated must be boolean")
        require(item["redaction"] in {"reviewed", "not-reviewed"}, "invalid redaction status")
        references(item["evidence_ids"], "evidence")
        if not item["simulated"]:
            require(any(indexes["evidence"][eid]["kind"] == "runtime" for eid in item["evidence_ids"]),
                    "runtime capture lacks runtime state evidence", 1)
        numbers = set()
        for mark in array(item["callouts"], "callouts"):
            keys(mark, "number action_id box image_sha256", "callout")
            action = reference(mark["action_id"], "actions")
            require(state["screen_id"] in action_screens(action) and action["kind"] == "control", "callout must target a control on its screen", 1)
            require(type(mark["number"]) is int and mark["number"] > 0, "invalid callout number")
            require(mark["number"] not in numbers, "duplicate callout number", 1)
            numbers.add(mark["number"])
            require(mark["image_sha256"] == item["sha256"], "stale callout image binding", 1)
            box = array(mark["box"], "callout.box")
            require(len(box) == 4 and all(type(x) in (int, float) and math.isfinite(x) for x in box), "invalid callout box")
            x, y, w, h = box
            require(x >= 0 and y >= 0 and w > 0 and h > 0 and x + w <= 1 and y + h <= 1, "callout box escapes image", 1)
        total_bytes += len(image_bytes(root, item))
        require(total_bytes <= MAX_IMAGES, "capture collection too large")
        if item["redaction"] != "reviewed":
            gaps.append(f"{item['id']}: redaction review missing")
        if item["source_revision"] != product["revision"]:
            gaps.append(f"{item['id']}: capture revision differs from product revision")

    used: dict[str, set[str]] = {key: set() for key in ("screens", "states", "actions", "captures")}
    for scenario in document["scenarios"]:
        keys(scenario, "id title goal actor prerequisites entry_state_ids terminal_state_ids evidence_ids steps", "scenario")
        for field in ("title", "goal", "actor", "prerequisites"):
            text(scenario[field], f"scenario.{field}")
        entries = references(scenario["entry_state_ids"], "states")
        terminals = references(scenario["terminal_state_ids"], "states")
        references(scenario["evidence_ids"], "evidence")
        steps = array(scenario["steps"], "steps", nonempty=True)
        step_ids: set[str] = set()
        for step in steps:
            keys(step, "id before action_id after condition result layer verification evidence_ids capture_ids", "step")
            sid = identifier(step["id"], "step")
            require(sid.casefold() not in step_ids,
                    f"duplicate step ID or case-colliding ID in {scenario['id']}: {sid}", 1)
            step_ids.add(sid.casefold())
            before = reference(step["before"], "states")
            after = reference(step["after"], "states")
            action = reference(step["action_id"], "actions")
            require(before["screen_id"] in action_screens(action), f"{sid}: action belongs to another screen", 1)
            text(step["condition"], "step.condition")
            text(step["result"], "step.result")
            require(step["layer"] in {"observed", "intended", "proposed"}, "invalid claim layer")
            require(step["verification"] in {"executed", "read", "unverified", "blocked"}, "invalid verification")
            evidence = references(step["evidence_ids"], "evidence")
            kinds = {indexes["evidence"][eid]["kind"] for eid in evidence}
            if step["verification"] == "executed":
                require("runtime" in kinds, f"{sid}: execution claim lacks runtime evidence", 1)
                runtime = [indexes["evidence"][eid] for eid in evidence
                           if indexes["evidence"][eid]["kind"] == "runtime"]
                if not any(source["revision"] == product["revision"] for source in runtime):
                    gaps.append(f"{scenario['id']}/{sid}: runtime evidence revision needs "
                                f"applicability review: {', '.join(source['id'] for source in runtime)}")
            if step["layer"] == "intended":
                require("requirement" in kinds, f"{sid}: intended outcome lacks adopted requirement", 1)
            if step["verification"] in {"blocked", "unverified"} or (step["layer"] == "observed" and step["verification"] != "executed"):
                gaps.append(f"{scenario['id']}/{sid}: {step['layer']}, {step['verification']}")
            captures = references(step["capture_ids"], "captures", nonempty=False)
            for cid in captures:
                require(indexes["captures"][cid]["state_id"] in {step["before"], step["after"]}, f"{sid}: capture depicts neither endpoint", 1)
            if not captures:
                gaps.append(f"{scenario['id']}/{sid}: no capture attached")
            used["captures"].update(captures)
            used["states"].update((step["before"], step["after"]))
            used["screens"].update((before["screen_id"], after["screen_id"]))
            used["actions"].add(step["action_id"])
        reached = set(entries)
        while True:
            expanded = reached | {step["after"] for step in steps if step["before"] in reached}
            if expanded == reached:
                break
            reached = expanded
        require(all(step["before"] in reached for step in steps), f"{scenario['id']}: unreachable step", 1)
        require(set(terminals) <= reached, f"{scenario['id']}: unreachable terminal state", 1)
        leads_to_terminal = set(terminals)
        while True:
            expanded = leads_to_terminal | {step["before"] for step in steps if step["after"] in leads_to_terminal}
            if expanded == leads_to_terminal:
                break
            leads_to_terminal = expanded
        require(all(step["after"] in leads_to_terminal for step in steps), f"{scenario['id']}: branch has no recorded terminal outcome", 1)
        require(set(entries) <= leads_to_terminal,
                f"{scenario['id']}: entry has no recorded terminal outcome", 1)
        if len({step["layer"] for step in steps}) > 1:
            gaps.append(f"{scenario['id']}: mixed claim layers; combined graph reachability "
                        "does not establish an executable current-product path")

    for item in document["inventory"]:
        keys(item, "id kind evidence_ids disposition target_id reason", "inventory")
        require(item["kind"] in KINDS, "invalid inventory kind")
        references(item["evidence_ids"], "evidence")
        require(item["disposition"] in {"mapped", "unresolved", "excluded"}, "invalid inventory disposition")
        text(item["target_id"], "inventory.target_id", empty=True)
        text(item["reason"], "inventory.reason")
        if item["disposition"] == "mapped":
            reference(item["target_id"], KINDS[item["kind"]])
        else:
            require(not item["target_id"], "unmapped inventory cannot pretend to have a target", 1)
            if item["disposition"] == "unresolved":
                gaps.append(f"{item['id']}: unresolved inventory item: {item['reason']}")
    for group, subjects in used.items():
        for orphan in indexes[group].keys() - subjects:
            gaps.append(f"{group}/{orphan}: no scenario use")
    mapped = {(KINDS[item["kind"]], item["target_id"]) for item in document["inventory"] if item["disposition"] == "mapped"}
    for group in KINDS.values():
        for rid in indexes[group]:
            if (group, rid) not in mapped:
                gaps.append(f"{group}/{rid}: not reconciled to the independent inventory")
    return {"structural_status": "consistent", "semantic_coverage": "not certified",
            "inventory_counts": {status: sum(x["disposition"] == status for x in document["inventory"])
                                 for status in ("mapped", "unresolved", "excluded")},
            "recorded_gaps": sorted(set(gaps))}


def reverse_index(document: dict[str, Any]) -> dict[str, dict[str, list[str]]]:
    result: dict[str, dict[str, list[str]]] = {group: {} for group in ("screens", "states", "actions")}
    states = {item["id"]: item for item in document["states"]}
    for scenario in document["scenarios"]:
        for step in scenario["steps"]:
            refs = {"states": (step["before"], step["after"]), "actions": (step["action_id"],),
                    "screens": (states[step["before"]]["screen_id"], states[step["after"]]["screen_id"])}
            for group, ids in refs.items():
                for rid in ids:
                    users = result[group].setdefault(rid, [])
                    if scenario["id"] not in users:
                        users.append(scenario["id"])
    return result


def read_notes(path: Path | None) -> dict[str, str]:
    if path is None:
        return {}
    document = read_json(path)
    for key, value in document.items():
        parts = key.split("/")
        require(len(parts) == 2 and all(ID.fullmatch(p) for p in parts), "note key must be scenario/step")
        text(value, "note", empty=True)
    return document


def capture_file(capture_id: str) -> str:
    # A valid map ID such as CON must not become a Windows device filename.
    return f"captures/capture-{capture_id}.png"


def handoff(document: dict[str, Any], report: dict[str, Any], notes: dict[str, str]) -> dict[str, Any]:
    actions = {item["id"]: item for item in document["actions"]}
    captures = {item["id"]: item for item in document["captures"]}
    pairs = []
    for scenario in document["scenarios"]:
        following: dict[str, list[dict[str, Any]]] = {}
        for step in scenario["steps"]:
            following.setdefault(step["before"], []).append(step)
        for step in scenario["steps"]:
            key = f"{scenario['id']}/{step['id']}"
            pictures = []
            for cid in step["capture_ids"]:
                capture = captures[cid]
                if step["before"] == step["after"]:
                    moment = "UNCHANGED STATE / MOMENT UNSPECIFIED"
                else:
                    moment = "BEFORE" if capture["state_id"] == step["before"] else "AFTER"
                pictures.append({**capture, "file": capture_file(cid), "moment": moment,
                                 "callouts": [{**mark, "label": actions[mark["action_id"]]["label"]}
                                              for mark in capture["callouts"]]})
            continuations = following.get(step["after"], [])
            pairs.append({
                "key": key,
                "left_frame": {"name": key + " description", "goal": scenario["goal"],
                               "actor": scenario["actor"], "prerequisites": scenario["prerequisites"],
                               "step": step, "action": actions[step["action_id"]]},
                "right_frame": {"name": key + " evidence", "captures": pictures,
                                "placeholder": "Not captured" if not pictures else ""},
                "next_step_keys": [f"{scenario['id']}/{item['id']}" for item in continuations
                                   if item["layer"] == step["layer"]],
                "related_step_keys": [f"{scenario['id']}/{item['id']}" for item in continuations
                                      if item["layer"] != step["layer"]],
                "manual_note": notes.get(key, ""),
            })
    used_keys = {pair["key"] for pair in pairs}
    return {
        "schema_version": 1, "product": document["product"], "report": report,
        "canvas_delivery": "not performed", "layout": "description frame beside state capture frame",
        "ownership": "Reconcile stable pair keys. Never overwrite manual notes or delete unmentioned nodes.",
        "pairs": pairs, "reverse_index": reverse_index(document),
        "sources": document["evidence"], "screens": document["screens"],
        "states": document["states"], "actions": document["actions"], "inventory": document["inventory"],
        "scenarios": [{k: v for k, v in item.items() if k != "steps"} for item in document["scenarios"]],
        "unmatched_notes": {k: v for k, v in notes.items() if k not in used_keys},
    }


def render_html(document: dict[str, Any], plan: dict[str, Any]) -> str:
    """Render the reader's full contract; the JSON is not a hidden appendix."""
    def esc(value: Any) -> str:
        return html.escape(str(value), quote=True)

    def link(group: str, rid: str, label: str | None = None) -> str:
        return f'<a href="#{group}-{esc(rid)}">{esc(rid if label is None else label)}</a>'

    def fields(rows: dict[str, Any]) -> str:
        return '<dl>' + ''.join('<dt>' + esc(k) + '</dt><dd>' + esc(v) + '</dd>'
                               for k, v in rows.items()) + '</dl>'

    def sources(ids: list[str]) -> str:
        return '<p>Evidence: ' + ', '.join(link('source', eid) for eid in ids) + '</p>'

    def state_links(ids: list[str]) -> str:
        return ', '.join(link('states', sid, f"{states[sid]['title']} ({sid})") for sid in ids)

    def step_links(keys: list[str]) -> str:
        return ', '.join(link('step', key,
            f"{pair_index[key]['left_frame']['step']['id']}: "
            f"{pair_index[key]['left_frame']['step']['condition']} "
            f"[{pair_index[key]['left_frame']['step']['layer']}]") for key in keys)

    states = {item['id']: item for item in document['states']}
    pair_index = {pair['key']: pair for pair in plan['pairs']}
    css = """
body{font:16px/1.55 system-ui,sans-serif;margin:32px auto;max-width:1500px;padding:0 24px}
h1,h2,h3{line-height:1.2}a{color:inherit}nav{display:flex;gap:18px;flex-wrap:wrap}
.pair{display:grid;grid-template-columns:minmax(280px,1fr) minmax(320px,1.6fr);gap:24px;border-top:1px solid;padding:24px 0}
.pair>*{min-width:0}p,dd,dt,li,code,h1,h2,h3,a,figcaption{overflow-wrap:anywhere}
dl{display:grid;grid-template-columns:110px minmax(0,1fr);gap:8px}dt{font-weight:650}dd{margin:0}
figure{margin:0 0 24px}.capture{position:relative}.capture img{width:100%;height:auto;display:block}
.callout{position:absolute;border:2px solid;border-radius:4px;box-sizing:border-box;color:#111;text-align:center;font-weight:bold}
.callout span{position:absolute;left:-10px;top:-13px;background:white;border:1px solid;border-radius:50%;width:22px;height:22px;line-height:22px}
.missing{padding:60px 24px;border:1px dashed}figcaption,small{font-size:13px}.note{border-left:3px solid;padding-left:12px}
pre{white-space:pre-wrap;overflow-wrap:anywhere}.index-item{border-top:1px solid;padding:16px 0}
@media(max-width:760px){.pair{grid-template-columns:1fr}body{margin:20px auto;padding:0 16px}}
@media print{.pair{break-inside:avoid}}
"""
    parts = ['<!doctype html><html lang="en"><head><meta charset="utf-8">',
             '<meta name="viewport" content="width=device-width, initial-scale=1">',
             '<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; img-src \'self\'; style-src \'unsafe-inline\'">',
             '<title>' + esc(document['product']['name']) + ' — Product map</title>',
             '<style>' + css + '</style></head><body>',
             '<h1>' + esc(document['product']['name']) + '</h1>',
             fields({'Revision': document['product']['revision'], 'Scope': document['product']['scope']}),
             '<p><strong>Evidence-linked documentation, not certified product coverage. Canvas delivery not performed.</strong></p>',
             '<nav>' + ''.join(link('scenario', s['id'], s['title']) for s in document['scenarios'])
             + ' <a href="#index">Reverse index</a> <a href="#gaps">Gaps</a> <a href="#sources">Sources</a></nav>']
    for scenario in document['scenarios']:
        parts += [f'<section id="scenario-{esc(scenario["id"])}"><h2>{esc(scenario["id"])} · {esc(scenario["title"])}</h2>',
                  fields({'Goal': scenario['goal'], 'Actor': scenario['actor'], 'Prerequisites': scenario['prerequisites']}),
                  '<p>Entry states: ' + state_links(scenario['entry_state_ids'])
                  + '<br>Terminal states: ' + state_links(scenario['terminal_state_ids']) + '</p>',
                  sources(scenario['evidence_ids'])]
        for step in scenario['steps']:
            key = f"{scenario['id']}/{step['id']}"
            pair = pair_index[key]
            action = pair['left_frame']['action']
            # '/' is forbidden inside either ID; unlike '-', it cannot collide.
            parts.append(f'<article class="pair" id="step-{esc(key)}"><div><h3>{esc(step["id"])} · {esc(action["label"])}</h3>')
            parts.append(fields({'Condition': step['condition'], 'Kind / role': f"{action['kind']} / {action['role']}",
                'Availability': action['availability'], 'Effect': action['effect'], 'Scope': action['scope'],
                'Result': step['result'], 'Claim': step['layer'], 'Verification': step['verification']}))
            parts += ['<p>Before: ' + state_links([step['before']]) + '<br>After: '
                      + state_links([step['after']]) + '<br>Control/event: ' + link('action', step['action_id']) + '</p>',
                      sources(step['evidence_ids'])]
            if step['after'] in scenario['terminal_state_ids']:
                parts.append('<p>Recorded terminal state; see the result and claim layer above.</p>')
            if pair['next_step_keys']:
                parts.append('<p>Next / alternatives in this claim layer: ' + step_links(pair['next_step_keys']) + '</p>')
            if pair['related_step_keys']:
                parts.append('<p>Different claim layers — related, not confirmed continuations: '
                             + step_links(pair['related_step_keys']) + '</p>')
            if not pair['next_step_keys'] and step['after'] not in scenario['terminal_state_ids']:
                parts.append('<p>No continuation recorded in this claim layer.</p>')
            if pair['manual_note']:
                parts.append('<p class="note">Designer note: ' + esc(pair['manual_note']) + '</p>')
            parts.append('</div><div>')
            if not pair['right_frame']['captures']:
                parts.append('<div class="missing">Not captured. Consult the source and verification status; this is not a screenshot.</div>')
            for capture in pair['right_frame']['captures']:
                title = states[capture['state_id']]['title']
                parts.append('<figure><div class="capture"><img src="' + esc(capture['file'])
                             + '" alt="' + esc(title) + '">')
                for mark in capture['callouts']:
                    x, y, w, h = [v * 100 for v in mark['box']]
                    parts.append(f'<a class="callout" href="#action-{esc(mark["action_id"])}" '
                        f'style="left:{x}%;top:{y}%;width:{w}%;height:{h}%" '
                        f'aria-label="{mark["number"]}: {esc(mark["label"])}"><span>{mark["number"]}</span></a>')
                parts.append('</div><figcaption>' + esc(capture['moment']) + ' · ' + esc(title) + ' · '
                    + ('SIMULATED' if capture['simulated'] else 'runtime capture') + '<br>'
                    + esc(capture['scope']) + ' · ' + esc(capture['source_revision']) + ' · '
                    + esc(capture['captured_at']) + '<br>Readiness: ' + esc(capture['readiness']))
                if capture['callouts']:
                    parts.append('<p>Callouts: ' + '; '.join(str(mark['number']) + ' — '
                        + link('action', mark['action_id'], mark['label']) for mark in capture['callouts']) + '</p>')
                parts += [sources(capture['evidence_ids']), '</figcaption></figure>']
            parts.append('</div></article>')
        parts.append('</section>')
    parts.append('<section id="index"><h2>Reverse index</h2>')
    for group in ('screens', 'states', 'actions'):
        for item in document[group]:
            anchor = 'action' if group == 'actions' else group
            title = item.get('title', item.get('label', item['id']))
            parts.append(f'<section class="index-item" id="{anchor}-{esc(item["id"])}"><h3>{esc(item["id"])} · {esc(title)}</h3>')
            details = {field.replace('_', ' ').capitalize(): value for field, value in item.items()
                       if field not in {'id', 'title', 'label', 'screen_id', 'shared_screen_ids', 'evidence_ids'}}
            parts.append(fields(details))
            if 'screen_id' in item:
                surface_ids = action_screens(item) if group == 'actions' else [item['screen_id']]
                parts.append('<p>Screens: ' + ', '.join(link('screens', sid) for sid in surface_ids) + '</p>')
            users = plan['reverse_index'][group].get(item['id'], [])
            parts.append('<p>Scenarios: ' + (', '.join(link('scenario', sid) for sid in users)
                                           or 'No recorded scenario use — review this gap') + '</p>')
            if 'evidence_ids' in item:
                parts.append(sources(item['evidence_ids']))
            parts.append('</section>')
    parts += ['</section><section id="gaps"><h2>Gaps and inventory dispositions</h2><ul>']
    parts += ['<li>' + esc(gap) + '</li>' for gap in plan['report']['recorded_gaps']]
    parts.append('</ul>')
    for item in document['inventory']:
        parts.append('<p>' + esc(item['id']) + ' · ' + esc(item['kind']) + ' · '
                     + esc(item['disposition']) + ' · ' + esc(item['target_id']) + ': '
                     + esc(item['reason']) + '</p>' + sources(item['evidence_ids']))
    for key, note in plan['unmatched_notes'].items():
        parts.append('<p class="note">Unmatched designer note (preserved) ' + esc(key) + ': ' + esc(note) + '</p>')
    parts.append('</section><section id="sources"><h2>Sources</h2>')
    for source in document['evidence']:
        parts.append(f'<p id="source-{esc(source["id"])}"><strong>{esc(source["id"])} · {esc(source["kind"])}</strong><br>'
                     + esc(source['locator']) + '<br>' + esc(source['revision']) + '<br>' + esc(source['detail']) + '</p>')
    return ''.join(parts) + '</section></body></html>\n'


def dump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n'


def export(document: dict[str, Any], root: Path, output: Path, notes: dict[str, str]) -> dict[str, Any]:
    report = check(document, root)
    require(all(c['redaction'] == 'reviewed' for c in document['captures']), 'review captures for sensitive data before exporting')
    no_links(output)
    require(not output.exists(), f'output already exists; use a new snapshot directory: {output}')
    require(output.parent.is_dir(), 'output parent must already exist')
    plan = handoff(document, report, notes)
    # Build outside the destination and clean only our own temporary directory.
    scratch = Path(tempfile.mkdtemp(prefix='.flow-map-', dir=output.parent))
    try:
        (scratch / 'captures').mkdir()
        for capture in document['captures']:
            (scratch / capture_file(capture['id'])).write_bytes(image_bytes(root, capture))
        portable = json.loads(dump(document))
        for capture in portable['captures']:
            capture['file'] = capture_file(capture['id'])
        (scratch / 'map.json').write_text(dump(portable), encoding='utf-8')
        (scratch / 'notes.json').write_text(dump(notes), encoding='utf-8')
        (scratch / 'handoff.json').write_text(dump(plan), encoding='utf-8')
        (scratch / 'index.html').write_text(render_html(document, plan), encoding='utf-8')
        # mkdir reserves the destination without overwriting an existing empty dir.
        output.mkdir()
        (output / 'captures').mkdir()
        # Publish index last and exclusively create each file: rename may replace
        # a note another writer created after we reserved the directory.
        files = sorted(path for path in scratch.rglob('*') if path.is_file())
        files.sort(key=lambda path: path == scratch / 'index.html')
        for source in files:
            target = output / source.relative_to(scratch)
            no_links(target)
            with source.open('rb') as reader, target.open('xb') as writer:
                shutil.copyfileobj(reader, writer)
        # On failure the partial destination stays visible; never erase user work.
    finally:
        shutil.rmtree(scratch)
    return {'output': str(output), 'pairs': len(plan['pairs']), **report}


def compare(previous: dict[str, Any], current: dict[str, Any]) -> dict[str, Any]:
    changes = {}
    changed_ids: dict[str, set[str]] = {}
    for group in GROUPS:
        before = {x['id']: x for x in previous[group]}
        after = {x['id']: x for x in current[group]}
        changed = sorted(key for key in before.keys() & after.keys() if before[key] != after[key])
        changes[group] = {'added': sorted(after.keys() - before.keys()), 'changed': changed,
                          'retired_candidates': sorted(before.keys() - after.keys())}
        changed_ids[group] = set(changed) | (before.keys() ^ after.keys())
    affected = set(changed_ids['scenarios'])
    product_changed = previous['product'] != current['product']
    coverage_review = product_changed or bool(changed_ids['inventory'])
    for document in (previous, current):
        consumers = reverse_index(document)
        for item in document['inventory']:
            if (item['id'] in changed_ids['inventory']
                    or set(item['evidence_ids']) & changed_ids['evidence']):
                coverage_review = True
                if item['disposition'] == 'mapped':
                    group = KINDS[item['kind']]
                    if group == 'scenarios':
                        affected.add(item['target_id'])
                    else:
                        affected.update(consumers[group].get(item['target_id'], []))
        states = {x['id']: x for x in document['states']}
        actions = {x['id']: x for x in document['actions']}
        captures = {x['id']: x for x in document['captures']}
        for scenario in document['scenarios']:
            relevant = product_changed or bool(set(scenario['evidence_ids']) & changed_ids['evidence'])
            for step in scenario['steps']:
                st = {step['before'], step['after']}
                relevant |= bool(st & changed_ids['states'] or step['action_id'] in changed_ids['actions']
                                 or set(step['capture_ids']) & changed_ids['captures']
                                 or set(step['evidence_ids']) & changed_ids['evidence'])
                for sid in st:
                    relevant |= states[sid]['screen_id'] in changed_ids['screens'] or bool(set(states[sid]['evidence_ids']) & changed_ids['evidence'])
                relevant |= bool(set(actions[step['action_id']]['evidence_ids']) & changed_ids['evidence'])
                relevant |= any(set(captures[cid]['evidence_ids']) & changed_ids['evidence'] for cid in step['capture_ids'])
            if relevant:
                affected.add(scenario['id'])
    return {'product_changed': product_changed, 'coverage_review_required': coverage_review,
            'changes': changes, 'affected_scenarios': sorted(affected),
            'canvas_writes': 'none; reconcile target IDs, annotations and manual notes before writing'}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    validate = sub.add_parser('check')
    validate.add_argument('map', type=Path)
    validate.add_argument('--require-no-gaps', action='store_true', help='exit 2 for recorded evidence/coverage gaps; does not certify completeness')
    bundle = sub.add_parser('export')
    bundle.add_argument('map', type=Path)
    bundle.add_argument('--output', required=True, type=Path)
    bundle.add_argument('--notes', type=Path)
    diff = sub.add_parser('diff')
    diff.add_argument('previous', type=Path)
    diff.add_argument('current', type=Path)
    args = parser.parse_args()
    try:
        if args.command == 'diff':
            previous, current = read_json(args.previous), read_json(args.current)
            check(previous, args.previous.parent)
            check(current, args.current.parent)
            result = compare(previous, current)
        else:
            document = read_json(args.map)
            if args.command == 'export':
                result = export(document, args.map.parent, args.output, read_notes(args.notes))
            else:
                result = check(document, args.map.parent)
                if args.require_no_gaps and result['recorded_gaps']:
                    print(dump(result), end='')
                    return 2
        print(dump(result), end='')
        return 0
    except MapError as error:
        print(dump({'error': str(error), 'exit_code': error.code}), file=sys.stderr, end='')
        return error.code
    except (OSError, ValueError, TypeError, KeyError, RecursionError) as error:
        print(dump({'error': str(error), 'exit_code': 2}), file=sys.stderr, end='')
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
