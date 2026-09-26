"""Validate Agent Assets and manage its guarded native client links."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import sys
import tempfile
from collections.abc import Iterable, Iterator, Sequence
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

import tomllib

if __package__:
    from .asset_formats import ContractError, FRONTMATTER, frontmatter, openai_adapter_document
    from .skill_resources import distribution_problems, markdown_problems, validate_plain_tree
else:
    from asset_formats import ContractError, FRONTMATTER, frontmatter, openai_adapter_document
    from skill_resources import distribution_problems, markdown_problems, validate_plain_tree

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = 2
SEMVER = re.compile(
    r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)"
    r"(?:-[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$"
)
ASCII_ID = re.compile(r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$")
ASSET_ID = re.compile(r"^(?:skill|profile)/[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$")
LITERAL_MACHINE_PATH = re.compile(
    r"(?:[A-Za-z]:\\Users\\[^\\/\s]+|/(?:Users|home)/[^/\s]+)"
)
GENERATED_DEFAULTS = {".git", "__pycache__"}
# A pinned publication-gate zipapp is tracked bytes, not source text.
BINARY_SUFFIXES = frozenset({".pyz"})
UNTEXT_DECLARATION = "* -text"
PROFILE_KEYS = {"schema_version", "name", "description", "capabilities", "instructions"}
FORBIDDEN_PROFILE_KEYS = {
    "effort",
    "hooks",
    "host",
    "mcp",
    "mcp_servers",
    "model",
    "permissions",
    "reasoning_effort",
    "runtime",
    "state",
}
PROFILE_CAPABILITIES = {
    "skill-discovery",
    "primary-web-research",
    "read-only-oracle",
    "workspace-read",
    "workspace-search",
}
CLAUDE_PROFILE_TOOLS = {
    "skill-discovery": ("Skill",),
    "workspace-read": ("Read",),
    "workspace-search": ("Grep", "Glob", "ToolSearch"),
    "primary-web-research": ("WebFetch", "WebSearch"),
    "read-only-oracle": ("Bash",),
}
ROOT_LAYOUT = {
    "agents": Path(".agents"),
    "codex": Path(".codex"),
    "claude": Path(".claude"),
}
CLIENTS = ("codex", "claude")
BASE_FILES = (
    "AGENTS.md",
    "CHANGELOG.md",
    "CLAUDE.md",
    "LICENSE",
    "README.md",
    "VERSION",
    "catalog.toml",
)


@dataclass(frozen=True)
class Projection:
    client: str
    root: str
    path: str
    mode: str


@dataclass(frozen=True)
class Asset:
    id: str
    kind: str
    path: str
    name: str
    activation: str
    license: str
    attribution: str
    projections: tuple[Projection, ...]


@dataclass(frozen=True)
class Catalog:
    generated_paths: frozenset[str]
    assets: tuple[Asset, ...]


@dataclass(frozen=True)
class PlannedEntry:
    asset_id: str
    client: str
    mode: str
    source: Path
    target: Path
    fingerprint: str
    data: bytes | None = None


CLAUDE_EXPLICIT_OVERRIDE = "user-invocable-only"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def strict_json_object(path: Path, label: str) -> dict[str, Any]:
    def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ContractError(f"{label}: duplicate JSON key {key!r}")
            result[key] = value
        return result

    try:
        document = json.loads(
            path.read_text(encoding="utf-8", errors="strict"),
            object_pairs_hook=unique_object,
        )
    except ContractError:
        raise
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ContractError(f"{label}: {error}") from error
    if not isinstance(document, dict):
        raise ContractError(f"{label}: expected a JSON object")
    return document


def exact_keys(table: dict[str, Any], expected: set[str], label: str) -> None:
    missing = sorted(expected - table.keys())
    extra = sorted(table.keys() - expected)
    if missing or extra:
        details = []
        if missing:
            details.append(f"missing {', '.join(missing)}")
        if extra:
            details.append(f"unknown {', '.join(extra)}")
        raise ContractError(f"{label}: {'; '.join(details)}")


def relative_path(value: object, label: str) -> str:
    if not isinstance(value, str) or not value or "\\" in value:
        raise ContractError(f"{label}: expected a non-empty POSIX relative path")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise ContractError(f"{label}: path must stay within its root")
    if ".system" in path.parts:
        raise ContractError(f"{label}: .system is owned by Codex and is never managed")
    return path.as_posix()


def string_list(value: object, label: str) -> tuple[str, ...]:
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise ContractError(f"{label}: expected a string array")
    result = tuple(value)
    if len(set(result)) != len(result):
        raise ContractError(f"{label}: duplicate values")
    return result


def load_catalog(root: Path = ROOT) -> Catalog:
    try:
        document = tomllib.loads(
            (root / "catalog.toml").read_bytes().decode("utf-8", "strict")
        )
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError) as error:
        raise ContractError(f"catalog.toml: {error}") from error
    exact_keys(document, {"schema", "source", "assets"}, "catalog.toml")
    if document["schema"] != SCHEMA:
        raise ContractError(f"catalog.toml: schema must be {SCHEMA}")
    source = document["source"]
    if not isinstance(source, dict):
        raise ContractError("catalog.toml source: expected table")
    exact_keys(source, {"generated_paths"}, "catalog.toml source")
    generated_paths = frozenset(
        relative_path(value, "source.generated_paths")
        for value in string_list(source["generated_paths"], "source.generated_paths")
    )
    if not isinstance(document["assets"], list) or not document["assets"]:
        raise ContractError("catalog.toml assets: expected a non-empty array")

    assets: list[Asset] = []
    target_keys: set[tuple[str, str]] = set()
    expected_asset_keys = {
        "activation",
        "attribution",
        "id",
        "kind",
        "license",
        "path",
        "projections",
    }
    for index, table in enumerate(document["assets"]):
        label = f"assets[{index}]"
        if not isinstance(table, dict):
            raise ContractError(f"{label}: expected table")
        exact_keys(table, expected_asset_keys, label)
        asset_id = table["id"]
        if not isinstance(asset_id, str) or not ASSET_ID.fullmatch(asset_id):
            raise ContractError(f"{label}.id: expected skill/<name> or profile/<name>")
        kind, name = asset_id.split("/", 1)
        if table["kind"] != kind:
            raise ContractError(f"{label}.kind: must agree with {asset_id!r}")
        path = relative_path(table["path"], f"{label}.path")
        expected_path = f"skills/{name}" if kind == "skill" else f"profiles/{name}.json"
        if path != expected_path:
            raise ContractError(f"{label}.path: {asset_id} must use {expected_path!r}")
        activation = table["activation"]
        if activation not in {"automatic", "explicit"}:
            raise ContractError(f"{label}.activation: expected automatic or explicit")
        if not isinstance(table["license"], str) or not table["license"].strip():
            raise ContractError(f"{label}.license: required")
        if (
            not isinstance(table["attribution"], str)
            or not table["attribution"].strip()
        ):
            raise ContractError(f"{label}.attribution: required")
        if not isinstance(table["projections"], list):
            raise ContractError(f"{label}.projections: expected array")
        projections: list[Projection] = []
        for projection_index, raw in enumerate(table["projections"]):
            projection_label = f"{label}.projections[{projection_index}]"
            if not isinstance(raw, dict):
                raise ContractError(f"{projection_label}: expected table")
            exact_keys(raw, {"client", "root", "path", "mode"}, projection_label)
            client, root_name, mode = raw["client"], raw["root"], raw["mode"]
            if client not in {"codex", "claude"}:
                raise ContractError(f"{projection_label}.client: unsupported client")
            if root_name not in ROOT_LAYOUT:
                raise ContractError(f"{projection_label}.root: unsupported native root")
            projection_path = relative_path(raw["path"], f"{projection_label}.path")
            expected = (
                ("agents" if client == "codex" else "claude", f"skills/{name}", "link")
                if kind == "skill"
                else (
                    "codex" if client == "codex" else "claude",
                    f"agents/{name}.toml" if client == "codex" else f"agents/{name}.md",
                    "render",
                )
            )
            if (root_name, projection_path, mode) != expected:
                raise ContractError(
                    f"{projection_label}: expected root/path/mode {expected!r}"
                )
            target_key = root_name, projection_path.casefold()
            if target_key in target_keys:
                raise ContractError(f"{projection_label}: projection target collision")
            target_keys.add(target_key)
            projections.append(Projection(client, root_name, projection_path, mode))
        if {projection.client for projection in projections} != {"codex", "claude"}:
            raise ContractError(
                f"{label}.projections: require one Codex and one Claude entry"
            )
        if len(projections) != 2:
            raise ContractError(f"{label}.projections: duplicate client entry")
        assets.append(
            Asset(
                asset_id,
                kind,
                path,
                name,
                activation,
                table["license"],
                table["attribution"],
                tuple(projections),
            )
        )
    if len({asset.id for asset in assets}) != len(assets):
        raise ContractError("catalog.toml: asset IDs must be unique")
    if len({asset.path for asset in assets}) != len(assets):
        raise ContractError("catalog.toml: asset paths must be unique")
    return Catalog(generated_paths, tuple(assets))


def is_reparse(path: Path) -> bool:
    try:
        return bool(path.lstat().st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT)
    except (AttributeError, OSError):
        return False


def generated(relative: Path, catalog: Catalog) -> bool:
    value = relative.as_posix()
    return any(
        value == declared or value.startswith(f"{declared}/")
        for declared in catalog.generated_paths
    )


def source_paths(root: Path, catalog: Catalog) -> tuple[list[Path], list[str]]:
    files: list[Path] = []
    problems: list[str] = []
    if root.is_symlink() or is_reparse(root):
        problems.append("repository root: symlink or reparse point is forbidden")
    for current, directories, names in os.walk(root, followlinks=False):
        parent = Path(current)
        kept: list[str] = []
        for name in sorted(directories):
            path = parent / name
            relative = path.relative_to(root)
            if relative.parts[0] in GENERATED_DEFAULTS or generated(relative, catalog):
                continue
            if path.is_symlink() or is_reparse(path):
                problems.append(f"{relative.as_posix()}: source links are forbidden")
            else:
                kept.append(name)
        directories[:] = kept
        for name in sorted(names):
            path = parent / name
            relative = path.relative_to(root)
            if relative.parts[0] in GENERATED_DEFAULTS or generated(relative, catalog):
                continue
            if path.is_symlink() or is_reparse(path):
                problems.append(f"{relative.as_posix()}: source links are forbidden")
                continue
            try:
                if not stat.S_ISREG(path.lstat().st_mode):
                    problems.append(
                        f"{relative.as_posix()}: non-regular file is forbidden"
                    )
                    continue
            except OSError as error:
                problems.append(f"{relative.as_posix()}: cannot inspect file: {error}")
                continue
            files.append(path)
    return sorted(files), problems


def parse_version(root: Path = ROOT) -> str:
    try:
        text = (root / "VERSION").read_bytes().decode("utf-8", "strict")
    except (OSError, UnicodeDecodeError) as error:
        raise ContractError(f"VERSION: {error}") from error
    if (
        not text.endswith("\n")
        or text.count("\n") != 1
        or not SEMVER.fullmatch(text[:-1])
    ):
        raise ContractError("VERSION: expected one SemVer line with final LF")
    return text[:-1]


def canonical_inventory(root: Path) -> dict[str, tuple[str, str]]:
    result: dict[str, tuple[str, str]] = {}
    skills = root / "skills"
    if skills.is_dir():
        for path in sorted(item for item in skills.iterdir() if item.is_dir()):
            result[f"skills/{path.name}"] = ("skill", path.name)
    profiles = root / "profiles"
    if profiles.is_dir():
        for path in sorted(profiles.glob("*.json")):
            result[path.relative_to(root).as_posix()] = ("profile", path.stem)
    return result


def walk_keys(value: object) -> Iterator[str]:
    if isinstance(value, dict):
        for key, nested in value.items():
            yield str(key)
            yield from walk_keys(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from walk_keys(nested)


def profile_document(data: bytes, asset: Asset) -> dict[str, Any]:
    try:
        document = json.loads(data.decode("utf-8", "strict"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ContractError(f"{asset.path}: invalid profile JSON: {error}") from error
    if not isinstance(document, dict) or set(document) != PROFILE_KEYS:
        raise ContractError(
            f"{asset.path}: expected exactly {', '.join(sorted(PROFILE_KEYS))}"
        )
    forbidden = sorted(
        {key.lower() for key in walk_keys(document)} & FORBIDDEN_PROFILE_KEYS
    )
    if forbidden:
        raise ContractError(
            f"{asset.path}: forbidden runtime fields: {', '.join(forbidden)}"
        )
    if document["schema_version"] != 1 or document["name"] != asset.name:
        raise ContractError(f"{asset.path}: schema_version/name disagree with catalog")
    if (
        not isinstance(document["description"], str)
        or not document["description"].strip()
    ):
        raise ContractError(f"{asset.path}: description is required")
    capabilities = string_list(document["capabilities"], f"{asset.path}.capabilities")
    instructions = string_list(document["instructions"], f"{asset.path}.instructions")
    if not capabilities or any(not value.strip() for value in capabilities):
        raise ContractError(f"{asset.path}: capabilities require non-empty strings")
    if not instructions or any(not value.strip() for value in instructions):
        raise ContractError(f"{asset.path}: instructions require non-empty strings")
    unknown = sorted(set(capabilities) - PROFILE_CAPABILITIES)
    if unknown:
        raise ContractError(f"{asset.path}: unknown capabilities: {', '.join(unknown)}")
    if (
        asset.id == "profile/evidence-reviewer"
        and "read-only-oracle" not in capabilities
    ):
        raise ContractError(
            f"{asset.path}: evidence reviewer must declare read-only-oracle"
        )
    return document


def render_profile(data: bytes, asset: Asset, client: str) -> bytes:
    """Render one neutral profile into a client-native read-only adapter."""
    document = profile_document(data, asset)
    digest = sha256(data)
    description = document["description"].strip()
    instructions = "\n\n".join(value.strip() for value in document["instructions"])
    if client == "codex":
        text = (
            f"# Generated by Agent Assets from {asset.path}.\n"
            f"# source-sha256: {digest}\n"
            f"name = {json.dumps(asset.name, ensure_ascii=False)}\n"
            f"description = {json.dumps(description, ensure_ascii=False)}\n"
            'sandbox_mode = "read-only"\n'
            f"developer_instructions = {json.dumps(instructions, ensure_ascii=False)}\n"
        )
        return text.encode("utf-8")
    if client == "claude":
        tools: list[str] = []
        for capability in document["capabilities"]:
            for tool in CLAUDE_PROFILE_TOOLS[capability]:
                if tool not in tools:
                    tools.append(tool)
        text = (
            "---\n"
            f"name: {asset.name}\n"
            f"description: {json.dumps(description, ensure_ascii=False)}\n"
            f"tools: {', '.join(tools)}\n"
            "permissionMode: plan\n"
            "---\n\n"
            f"<!-- Generated by Agent Assets from {asset.path}. -->\n"
            f"<!-- source-sha256: {digest} -->\n\n"
            f"{instructions}\n"
        )
        return text.encode("utf-8")
    raise ContractError(f"{asset.id}: unsupported profile client {client!r}")


def skill_problems(path: Path, asset: Asset, root: Path) -> list[str]:
    relative = path.relative_to(root).as_posix()
    try:
        metadata = frontmatter(path)
    except (ContractError, UnicodeDecodeError) as error:
        return [f"{relative}: {error}"]
    allowed = {
        "allowed-tools",
        "compatibility",
        "description",
        "license",
        "metadata",
        "name",
    }
    problems: list[str] = []
    unknown = sorted(set(metadata) - allowed)
    if unknown:
        problems.append(f"{relative}: unsupported metadata: {', '.join(unknown)}")
    if metadata.get("name") != asset.name:
        problems.append(f"{relative}: name must equal {asset.name!r}")
    if (
        not isinstance(metadata.get("description"), str)
        or not str(metadata["description"]).strip()
    ):
        problems.append(f"{relative}: description is required")
    name = metadata.get("name")
    if not isinstance(name, str) or not 1 <= len(name) <= 64 or not re.fullmatch(
        r"[a-z0-9]+(?:-[a-z0-9]+)*", name
    ):
        problems.append(f"{relative}: name must be 1-64 lowercase letters, digits or single hyphens")
    description = metadata.get("description")
    if isinstance(description, str) and len(description) > 1024:
        problems.append(f"{relative}: description must not exceed 1024 characters")
    if "compatibility" in metadata:
        compatibility = metadata["compatibility"]
        if not isinstance(compatibility, str) or not compatibility.strip() or len(compatibility) > 500:
            problems.append(f"{relative}: compatibility must be a non-empty string of at most 500 characters")
    if "allowed-tools" in metadata:
        tools = metadata["allowed-tools"]
        if not isinstance(tools, str) or not tools.strip():
            problems.append(f"{relative}: allowed-tools must be a non-empty string")
    if "metadata" in metadata:
        values = metadata["metadata"]
        if not isinstance(values, dict) or any(
            not isinstance(key, str) or not isinstance(value, str)
            for key, value in values.items()
        ):
            problems.append(f"{relative}: metadata must map strings to strings")
    if metadata.get("license") != asset.license:
        problems.append(f"{relative}: license must equal the catalog license")
    return problems


def openai_adapter_problems(path: Path, asset: Asset, root: Path) -> list[str]:
    relative = path.relative_to(root).as_posix()
    try:
        document = openai_adapter_document(path.read_text(encoding="utf-8"))
    except (ContractError, UnicodeDecodeError, OSError) as error:
        return [f"{relative}: {error}"]
    problems: list[str] = []

    def locate(value: Any, prefix: tuple[str, ...] = ()) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                location = (*prefix, key)
                expected = {
                    "default_prompt": ("interface", "default_prompt"),
                    "allow_implicit_invocation": ("policy", "allow_implicit_invocation"),
                }.get(key)
                if expected is not None and location != expected:
                    problems.append(
                        f"{relative}: {key} must be at {'.'.join(expected)}"
                    )
                locate(child, location)
        elif isinstance(value, list):
            for index, child in enumerate(value):
                locate(child, (*prefix, str(index)))

    locate(document)
    interface = document.get("interface")
    prompt = interface.get("default_prompt") if isinstance(interface, dict) else None
    mentions = (
        re.findall(r"\$([a-z][a-z0-9]*(?:[._-][a-z0-9]+)*)", prompt)
        if isinstance(prompt, str) else []
    )
    if mentions.count(asset.name) != 1:
        problems.append(f"{relative}: interface.default_prompt must uniquely name ${asset.name}")
    policy = document.get("policy", {})
    if not isinstance(policy, dict):
        problems.append(f"{relative}: policy must be an object")
    elif set(policy) - {"allow_implicit_invocation"}:
        problems.append(f"{relative}: unsupported policy keys")
    else:
        implicit = policy.get("allow_implicit_invocation", True)
        if type(implicit) is not bool:
            problems.append(f"{relative}: invocation policy must be a true/false boolean")
        elif implicit != (asset.activation == "automatic"):
            problems.append(f"{relative}: invocation policy disagrees with catalog activation")
    return problems


def still_text(directory: Path) -> set[str] | None:
    """Names a byte-exact directory keeps under the ordinary text rules.

    A test fixture that carries CRLF or broken encoding on purpose cannot also
    be UTF-8 with LF, and renaming it to look binary would only hide what it
    is. Git already has the word for this: a directory whose `.gitattributes`
    says `* -text` declares its bytes are not text. Honour that declaration,
    and keep linting the names that same file marks `text` again, so the
    exemption covers the payload and never the prose beside it.

    Returns None when the directory makes no such declaration.
    """
    attributes = directory / ".gitattributes"
    if not attributes.is_file():
        return None
    exempt, kept = False, {".gitattributes"}
    for line in attributes.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        pattern, *tokens = line.split()
        if pattern == "*" and "-text" in tokens:
            exempt = True
        elif "text" in tokens and "/" not in pattern and "*" not in pattern:
            kept.add(pattern)
    return kept if exempt else None


def check(root: Path = ROOT) -> list[str]:
    problems: list[str] = []
    try:
        catalog = load_catalog(root)
    except ContractError as error:
        return [str(error)]
    try:
        parse_version(root)
    except ContractError as error:
        problems.append(str(error))
    files, path_problems = source_paths(root, catalog)
    problems.extend(path_problems)
    known = {path.relative_to(root).as_posix() for path in files}
    for required in BASE_FILES:
        if required not in known:
            problems.append(f"{required}: required source file is missing")
    declarations: dict[Path, set[str] | None] = {}
    for path in files:
        relative = path.relative_to(root).as_posix()
        if path.suffix.lower() in BINARY_SUFFIXES:
            continue
        if path.parent not in declarations:
            declarations[path.parent] = still_text(path.parent)
        kept = declarations[path.parent]
        if kept is not None and path.name not in kept:
            continue
        data = path.read_bytes()
        try:
            text = data.decode("utf-8", "strict")
        except UnicodeDecodeError as error:
            problems.append(f"{relative}: invalid UTF-8 at byte {error.start}")
            continue
        if data and not data.endswith(b"\n"):
            problems.append(f"{relative}: missing final LF")
        if "\r" in text:
            problems.append(f"{relative}: CR characters are forbidden; use LF")
        if relative != "tools/assay.py" and LITERAL_MACHINE_PATH.search(text):
            problems.append(
                f"{relative}: literal machine-specific user path is forbidden"
            )

    inventory = canonical_inventory(root)
    expected = {asset.path: (asset.kind, asset.name) for asset in catalog.assets}
    uncatalogued = sorted(set(inventory) - set(expected))
    stale = sorted(set(expected) - set(inventory))
    mismatch = sorted(
        path
        for path in set(inventory) & set(expected)
        if inventory[path] != expected[path]
    )
    if uncatalogued:
        problems.append(f"catalog.toml: uncatalogued assets: {', '.join(uncatalogued)}")
    if stale:
        problems.append(f"catalog.toml: missing canonical assets: {', '.join(stale)}")
    if mismatch:
        problems.append(f"catalog.toml: kind/name mismatch: {', '.join(mismatch)}")

    for asset in catalog.assets:
        source = root / asset.path
        if asset.kind == "skill":
            definition = source / "SKILL.md"
            if not definition.is_file():
                problems.append(f"{asset.path}: missing SKILL.md")
            else:
                problems.extend(skill_problems(definition, asset, root))
            for markdown in sorted(source.rglob("*.md")):
                problems.extend(markdown_problems(markdown, root))
            adapter = source / "agents" / "openai.yaml"
            if adapter.is_file():
                problems.extend(openai_adapter_problems(adapter, asset, root))
            elif asset.activation == "explicit":
                problems.append(
                    f"{asset.path}: explicit activation requires agents/openai.yaml"
                )
        else:
            if source.is_file():
                try:
                    profile_document(source.read_bytes(), asset)
                except ContractError as error:
                    problems.append(str(error))

    # Validate a full copied collection and every singleton, not only checkout
    # links. Unsafe source trees never enter the copying boundary.
    skill_sources = [root / asset.path for asset in catalog.assets if asset.kind == "skill"]
    if skill_sources and not path_problems and not stale:
        problems.extend(distribution_problems(skill_sources))

    bridge = root / "CLAUDE.md"
    if bridge.is_file() and bridge.read_bytes() != b"@AGENTS.md\n":
        problems.append("CLAUDE.md: expected the one-line @AGENTS.md bridge")
    problems.extend(render_drift(root))
    return sorted(set(problems))


SUMMARY = "Evidence-grounded methods for coding agents"
LONG_SUMMARY = (
    "Skills and agent profiles for implementation, planning, architecture, testing, "
    "audit, research, writing, UI delivery and bounded delegation. Each method "
    "says what it checked, what that establishes and what it does not."
)
HOMEPAGE = "https://github.com/Muratovnik/assay"
AUTHOR = {"name": "Nikolai Muratov", "url": "https://github.com/Muratovnik"}
KEYWORDS = [
    "agent-skills",
    "architecture",
    "audit",
    "code-review",
    "delegation",
    "planning",
    "research",
    "testing",
    "writing",
]
CATEGORY = "Developer Tools"


def json_document(data: dict[str, Any]) -> bytes:
    return (json.dumps(data, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def skill_assets(catalog: Catalog) -> list[Asset]:
    return [asset for asset in catalog.assets if asset.kind == "skill"]


def profile_assets(catalog: Catalog) -> list[Asset]:
    return [asset for asset in catalog.assets if asset.kind == "profile"]


def claude_plugin(version: str, profiles: list[Asset]) -> bytes:
    return json_document(
        {
            "name": "assay",
            "description": f"{SUMMARY}.",
            "version": version,
            "author": AUTHOR,
            "homepage": HOMEPAGE,
            "repository": HOMEPAGE,
            "license": "MIT",
            "keywords": KEYWORDS,
            "skills": "./skills/",
            # A directory is rejected here: the manifest wants each agent file.
            "agents": [
                f"./adapters/claude/agents/{asset.name}.md" for asset in profiles
            ],
        }
    )


def claude_marketplace(version: str) -> bytes:
    return json_document(
        {
            "name": "assay",
            "owner": AUTHOR,
            "metadata": {"description": f"{SUMMARY}.", "version": version},
            "plugins": [
                {
                    "name": "assay",
                    "source": "./",
                    "description": LONG_SUMMARY,
                    "version": version,
                    "author": AUTHOR,
                    "homepage": HOMEPAGE,
                    "repository": HOMEPAGE,
                    "license": "MIT",
                    "category": CATEGORY,
                    "keywords": KEYWORDS,
                }
            ],
        }
    )


def codex_plugin(version: str) -> bytes:
    return json_document(
        {
            "$schema": "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json",
            "name": "assay",
            "version": version,
            "description": f"{SUMMARY}.",
            "author": AUTHOR,
            "skills": "./skills/",
            "interface": {
                "displayName": "Assay",
                "shortDescription": SUMMARY,
                "longDescription": LONG_SUMMARY,
                "developerName": AUTHOR["name"],
                "category": CATEGORY,
                "capabilities": ["Read", "Write"],
                "websiteURL": HOMEPAGE,
                "defaultPrompt": [
                    "Audit this change against what was asked.",
                    "Write tests for this behaviour and say what they would catch.",
                ],
            },
        }
    )


def codex_marketplace() -> bytes:
    return json_document(
        {
            "name": "assay",
            "interface": {"displayName": "Assay"},
            "plugins": [
                {
                    "name": "assay",
                    "source": {"source": "url", "url": "./"},
                    "policy": {
                        "installation": "AVAILABLE",
                        "authentication": "ON_INSTALL",
                    },
                    "category": CATEGORY,
                }
            ],
        }
    )


def cursor_plugin(version: str) -> bytes:
    return json_document(
        {
            "name": "assay",
            "description": f"{SUMMARY}.",
            "version": version,
            "author": AUTHOR,
        }
    )


def gemini_extension(version: str) -> bytes:
    return json_document(
        {
            "name": "assay",
            "version": version,
            "description": f"{SUMMARY}.",
            "contextFileName": "GEMINI.md",
        }
    )


def reminder_hooks() -> bytes:
    # Both clients expose CLAUDE_PLUGIN_ROOT. Resolve it inside Python, not the
    # shell: spaces and shell metacharacters in an install path stay data.
    command = (
        'python -I -B -c "import os, runpy; '
        "runpy.run_path(os.path.join(os.environ['CLAUDE_PLUGIN_ROOT'], "
        "'skills/route-subagents/scripts/skill_reminder.py'), "
        "run_name='__main__')\""
    )
    return json_document({"hooks": {
        "SessionStart": [{
            "matcher": "^(startup|resume|clear|compact|fork)$",
            "hooks": [{"type": "command", "command": command, "timeout": 5}],
        }],
        "PreToolUse": [{
            "matcher": "^(spawn_agent|Agent|Task)$",
            "hooks": [{"type": "command", "command": command, "timeout": 5}],
        }],
    }})


def skills_index(root: Path, catalog: Catalog) -> bytes:
    lines = [
        "<!-- Generated from catalog.toml and skill frontmatter by",
        "     tools/assay.py render; do not edit this file. -->",
        "# Skills",
        "",
        "Each skill is one directory with a `SKILL.md`. A client reads the name and",
        "description for discovery; actual loading depends on the client and task.",
        "Declared automatic activation is eligibility, not a successful-run receipt.",
        "",
        "| Skill | Activation | What it is for |",
        "| --- | --- | --- |",
    ]
    for asset in skill_assets(catalog):
        metadata = frontmatter(root / asset.path / "SKILL.md")
        # YAML block scalars are valid metadata, but a Markdown table cell must
        # stay on one line and must not introduce an extra column.
        description = " ".join(str(metadata.get("description", "")).split())
        summary = description.split(". ")[0].rstrip(".").replace("|", "\\|")
        lines.append(
            f"| [{asset.name}]({asset.name}/SKILL.md) | {asset.activation} | {summary}. |"
        )
    lines += [
        "",
        "The full description, including when the method should **not** run, is in",
        "each skill's frontmatter. Conditional depth lives in its `references/`, and",
        "its `evals/` hold evaluation data that is never read while working a task.",
        "",
    ]
    return "\n".join(lines).encode("utf-8")


def rendered_documents(root: Path = ROOT) -> dict[str, bytes]:
    """Every generated file, keyed by its repository-relative path.

    One source, many clients: the catalog and VERSION decide what each manifest
    says, so a client copy cannot drift from the inventory without the gate
    noticing.
    """
    catalog = load_catalog(root)
    version = parse_version(root)
    documents: dict[str, bytes] = {
        ".claude-plugin/plugin.json": claude_plugin(version, profile_assets(catalog)),
        ".claude-plugin/marketplace.json": claude_marketplace(version),
        ".codex-plugin/plugin.json": codex_plugin(version),
        ".agents/plugins/marketplace.json": codex_marketplace(),
        ".cursor-plugin/plugin.json": cursor_plugin(version),
        "gemini-extension.json": gemini_extension(version),
        "hooks/hooks.json": reminder_hooks(),
        "skills/README.md": skills_index(root, catalog),
    }
    for asset in profile_assets(catalog):
        data = (root / asset.path).read_bytes()
        documents[f"adapters/claude/agents/{asset.name}.md"] = render_profile(
            data, asset, "claude"
        )
        documents[f"adapters/codex/agents/{asset.name}.toml"] = render_profile(
            data, asset, "codex"
        )
    return documents


def render_drift(root: Path = ROOT) -> list[str]:
    problems: list[str] = []
    for relative, expected in rendered_documents(root).items():
        path = root / relative
        if not path.is_file():
            problems.append(f"{relative}: generated file is missing; run render")
        elif path.read_bytes() != expected:
            problems.append(f"{relative}: generated file differs from its source; run render")
    return problems


def write_rendered(root: Path = ROOT) -> list[str]:
    written: list[str] = []
    for relative, expected in rendered_documents(root).items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.is_file() or path.read_bytes() != expected:
            path.write_bytes(expected)
            written.append(relative)
    return written


def tree_fingerprint(path: Path) -> str:
    digest = hashlib.sha256()
    for file_path in sorted(item for item in path.rglob("*") if item.is_file()):
        relative = file_path.relative_to(path).as_posix().encode("utf-8")
        data = file_path.read_bytes()
        digest.update(len(relative).to_bytes(8, "big"))
        digest.update(relative)
        digest.update(len(data).to_bytes(8, "big"))
        digest.update(data)
    return digest.hexdigest()


def lexical_absolute(path: Path) -> Path:
    return Path(os.path.abspath(os.fspath(path)))


def selected_clients(clients: Iterable[str] | None = None) -> frozenset[str]:
    if clients is None:
        return frozenset(CLIENTS)
    chosen = frozenset(clients)
    unknown = sorted(chosen - set(CLIENTS))
    if not chosen or unknown:
        raise ContractError(
            f"unknown client selection: {', '.join(unknown) or 'none'}; "
            f"expected {', '.join(CLIENTS)}"
        )
    return chosen


def native_plan(
    root: Path = ROOT,
    home: Path | None = None,
    clients: Iterable[str] | None = None,
) -> list[PlannedEntry]:
    root = root.resolve(strict=True)
    home = lexical_absolute((home or Path.home()).expanduser())
    chosen = selected_clients(clients)
    # Lifecycle commands cannot rely on the publication gate to reject a
    # redirected source. This does not validate unrelated documentation.
    validate_plain_tree(root / "catalog.toml")
    catalog = load_catalog(root)
    native_skill_targets: dict[str, Path] = {}
    for asset in catalog.assets:
        if asset.kind != "skill":
            continue
        projection = next(item for item in asset.projections if item.client == "codex")
        native_skill_targets[asset.id] = (
            home / ROOT_LAYOUT[projection.root] / projection.path
        )

    entries: list[PlannedEntry] = []
    client_order = {"codex": 0, "claude": 1}
    for asset in sorted(catalog.assets, key=lambda item: item.id):
        source = root / asset.path
        preflight_safe_parent(root, source.parent)
        validate_plain_tree(source)
        source = source.resolve(strict=True)
        for projection in sorted(
            asset.projections, key=lambda item: client_order[item.client]
        ):
            target = lexical_absolute(
                home / ROOT_LAYOUT[projection.root] / projection.path
            )
            try:
                target.relative_to(home)
            except ValueError as error:
                raise ContractError(
                    f"{asset.id}: projection escapes the selected home"
                ) from error
            if projection.mode == "link":
                link_source = (
                    source
                    if projection.client == "codex"
                    else native_skill_targets[asset.id]
                )
                entries.append(
                    PlannedEntry(
                        asset.id,
                        projection.client,
                        "link",
                        lexical_absolute(link_source),
                        target,
                        tree_fingerprint(source),
                    )
                )
            else:
                data = render_profile(source.read_bytes(), asset, projection.client)
                entries.append(
                    PlannedEntry(
                        asset.id,
                        projection.client,
                        "render",
                        source,
                        target,
                        sha256(data),
                        data,
                    )
                )
    return [entry for entry in entries if entry.client in chosen]


def link_chain_problems(
    root: Path, home: Path, clients: frozenset[str], installing: bool
) -> list[str]:
    """A Claude skill link resolves through the Codex one; keep the chain whole."""
    if installing:
        dependent = "claude" in clients and "codex" not in clients
    else:
        dependent = "codex" in clients and "claude" not in clients
    if not dependent:
        return []
    entries = native_plan(root, home)
    codex_links = {
        entry.asset_id: entry
        for entry in entries
        if entry.client == "codex" and entry.mode == "link"
    }
    problems: list[str] = []
    for entry in entries:
        if entry.client != "claude" or entry.mode != "link":
            continue
        codex = codex_links[entry.asset_id]
        if installing and entry_state(codex)[0] != "exact":
            problems.append(
                f"{entry.target} resolves through {codex.target}, which is not "
                "installed; include the codex client"
            )
        elif not installing and lexists(entry.target):
            problems.append(
                f"{entry.target} still resolves through {codex.target}; "
                "remove the claude client first"
            )
    return problems


def lexists(path: Path) -> bool:
    return os.path.lexists(os.fspath(path))


def link_destination(path: Path) -> Path:
    raw = os.readlink(path)
    raw = raw.removeprefix("\\\\?\\")
    destination = Path(raw)
    if not destination.is_absolute():
        destination = path.parent / destination
    return lexical_absolute(destination)


def same_path(left: Path, right: Path) -> bool:
    return os.path.normcase(os.fspath(lexical_absolute(left))) == os.path.normcase(
        os.fspath(lexical_absolute(right))
    )


def entry_state(entry: PlannedEntry) -> tuple[str, str]:
    if not lexists(entry.target):
        return "missing", "target does not exist"
    if entry.mode == "link":
        if not (entry.target.is_symlink() or is_reparse(entry.target)):
            return "foreign", "expected a directory link, found a real filesystem entry"
        try:
            destination = link_destination(entry.target)
        except OSError as error:
            return "foreign", f"cannot read link target: {error}"
        if not same_path(destination, entry.source):
            return "foreign", f"link points to {destination}, expected {entry.source}"
        return "exact", f"link points to {entry.source}"
    if (
        entry.target.is_symlink()
        or is_reparse(entry.target)
        or not entry.target.is_file()
    ):
        return "foreign", "expected a regular rendered adapter"
    try:
        actual = entry.target.read_bytes()
    except OSError as error:
        return "foreign", f"cannot read adapter: {error}"
    if entry.data is None or actual != entry.data:
        return "foreign", f"adapter bytes differ; expected sha256 {entry.fingerprint}"
    return "exact", f"adapter sha256 {entry.fingerprint}"


def activation_prerequisites(
    root: Path = ROOT,
    home: Path | None = None,
    clients: Iterable[str] | None = None,
) -> list[dict[str, str]]:
    if "claude" not in selected_clients(clients):
        return []
    selected_home = lexical_absolute((home or Path.home()).expanduser())
    settings = selected_home / ".claude" / "settings.json"
    catalog = load_catalog(root.resolve(strict=True))
    explicit_claude_skills = sorted(
        (
            asset
            for asset in catalog.assets
            if asset.kind == "skill"
            and asset.activation == "explicit"
            and any(item.client == "claude" for item in asset.projections)
        ),
        key=lambda asset: asset.id,
    )
    if not explicit_claude_skills:
        return []

    state = "exact"
    detail = ""
    document: dict[str, Any] | None = None
    if not lexists(settings):
        state = "missing"
        detail = "Claude user settings do not exist"
    elif settings.is_symlink() or is_reparse(settings) or not settings.is_file():
        state = "foreign"
        detail = "Claude user settings must be a regular JSON file"
    else:
        try:
            document = strict_json_object(settings, str(settings))
        except ContractError as error:
            state = "invalid"
            detail = str(error)

    prerequisites: list[dict[str, str]] = []
    for asset in explicit_claude_skills:
        asset_state = state
        asset_detail = detail
        if document is not None:
            overrides = document.get("skillOverrides")
            actual = overrides.get(asset.name) if isinstance(overrides, dict) else None
            if actual == CLAUDE_EXPLICIT_OVERRIDE:
                asset_state = "exact"
                asset_detail = (
                    f"skillOverrides.{asset.name} is {CLAUDE_EXPLICIT_OVERRIDE!r}"
                )
            else:
                asset_state = "mismatch"
                asset_detail = (
                    f"skillOverrides.{asset.name} is {actual!r}; expected "
                    f"{CLAUDE_EXPLICIT_OVERRIDE!r}"
                )
        prerequisites.append(
            {
                "asset": asset.id,
                "client": "claude",
                "path": str(settings),
                "setting": f"skillOverrides.{asset.name}",
                "expected": CLAUDE_EXPLICIT_OVERRIDE,
                "state": asset_state,
                "detail": asset_detail,
            }
        )
    return prerequisites


def plan_document(
    root: Path = ROOT,
    home: Path | None = None,
    clients: Iterable[str] | None = None,
) -> dict[str, Any]:
    selected_home = lexical_absolute((home or Path.home()).expanduser())
    chosen = selected_clients(clients)
    entries = native_plan(root, selected_home, chosen)
    planned: list[dict[str, Any]] = []
    for entry in entries:
        state, detail = entry_state(entry)
        try:
            preflight_safe_parent(selected_home, entry.target.parent)
            ancestor = "safe"
        except ContractError as error:
            ancestor = str(error)
        planned.append(
            {
                "asset": entry.asset_id,
                "client": entry.client,
                "mode": entry.mode,
                "source": str(entry.source),
                "target": str(entry.target),
                "fingerprint": entry.fingerprint,
                "state": state,
                "detail": detail,
                "ancestor": ancestor,
                "rollback": {
                    "operation": "remove-only-if-exact",
                    "target": str(entry.target),
                    "restore": "restore the separately captured pre-cutover bytes or link",
                },
            }
        )
    return {
        "schema": 2,
        "source_root": str(root.resolve(strict=True)),
        "version": parse_version(root),
        "prerequisites": activation_prerequisites(root, selected_home, chosen),
        "entries": planned,
    }


def format_plan(document: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    for prerequisite in document["prerequisites"]:
        lines.append(
            "PREREQUISITE "
            f"{prerequisite['state'].upper()} {prerequisite['path']} "
            f"{prerequisite['setting']}={prerequisite['expected']}"
        )
        if prerequisite["state"] != "exact":
            lines.append(f"PREREQUISITE REFUSED {prerequisite['detail']}")
    for entry in document["entries"]:
        lines.append(
            f"{entry['mode'].upper()} {entry['state'].upper()} {entry['target']} <- {entry['source']}"
        )
        if entry["ancestor"] != "safe":
            lines.append(f"ANCESTOR REFUSED {entry['ancestor']}")
        lines.append(f"ROLLBACK REMOVE-ONLY-IF-EXACT {entry['rollback']['target']}")
    return lines


def preflight_safe_parent(home: Path, parent: Path) -> None:
    home = lexical_absolute(home)
    parent = lexical_absolute(parent)
    try:
        relative = parent.relative_to(home)
    except ValueError as error:
        raise ContractError(
            f"projection parent escapes selected home: {parent}"
        ) from error
    if not lexists(home):
        raise ContractError(f"selected home must already exist: {home}")
    current = home
    for part in relative.parts:
        if current.is_symlink() or is_reparse(current) or not current.is_dir():
            raise ContractError(
                f"projection ancestor must be a real directory: {current}"
            )
        current = current / part
        if not lexists(current):
            return
    if current.is_symlink() or is_reparse(current) or not current.is_dir():
        raise ContractError(f"projection parent must be a real directory: {current}")


def ensure_safe_parent(home: Path, parent: Path) -> None:
    preflight_safe_parent(home, parent)
    home = lexical_absolute(home)
    parent = lexical_absolute(parent)
    current = home
    for part in parent.relative_to(home).parts:
        current = current / part
        if not lexists(current):
            current.mkdir()
        if current.is_symlink() or is_reparse(current) or not current.is_dir():
            raise ContractError(
                f"projection ancestor must be a real directory: {current}"
            )


def atomic_create(path: Path, data: bytes) -> None:
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(temporary_name)
    identity: tuple[int, int] | None = None
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        temporary_stat = temporary.stat()
        identity = temporary_stat.st_dev, temporary_stat.st_ino
        try:
            os.link(temporary, path)
        except FileExistsError as error:
            raise ContractError(f"target appeared during install: {path}") from error
        temporary.unlink()
    except BaseException as error:
        cleanup_errors: list[str] = []
        if identity is not None and lexists(path):
            try:
                target_stat = path.stat()
                owned = (target_stat.st_dev, target_stat.st_ino) == identity
            except OSError as inspect_error:
                cleanup_errors.append(f"cannot inspect {path}: {inspect_error}")
                owned = False
            if owned:
                try:
                    path.unlink()
                except OSError as cleanup_error:
                    cleanup_errors.append(f"cannot remove {path}: {cleanup_error}")
            elif not cleanup_errors:
                cleanup_errors.append(f"foreign target appeared at {path}")
        if lexists(temporary):
            try:
                temporary.unlink()
            except OSError as cleanup_error:
                cleanup_errors.append(
                    f"cannot remove temporary adapter {temporary}: {cleanup_error}"
                )
        if cleanup_errors:
            raise ContractError(
                "atomic adapter creation rollback was incomplete:\n"
                + "\n".join(cleanup_errors)
            ) from error
        raise


def create_entry(entry: PlannedEntry, home: Path) -> None:
    ensure_safe_parent(home, entry.target.parent)
    if lexists(entry.target):
        raise ContractError(f"target appeared during install: {entry.target}")
    if entry.mode == "link":
        if not entry.source.is_dir():
            raise ContractError(f"link source is unavailable: {entry.source}")
        os.symlink(entry.source, entry.target, target_is_directory=True)
    else:
        if entry.data is None:
            raise ContractError(f"rendered adapter has no bytes: {entry.target}")
        atomic_create(entry.target, entry.data)


def remove_entry(entry: PlannedEntry) -> None:
    if entry.mode == "link":
        if entry.target.is_symlink():
            entry.target.unlink()
        elif is_reparse(entry.target):
            os.rmdir(entry.target)
        else:
            raise ContractError(f"refusing to remove non-link target: {entry.target}")
    else:
        entry.target.unlink()


def install_links(
    root: Path = ROOT,
    home: Path | None = None,
    clients: Iterable[str] | None = None,
) -> list[str]:
    home = lexical_absolute((home or Path.home()).expanduser())
    chosen = selected_clients(clients)
    prerequisites = activation_prerequisites(root, home, chosen)
    unmet = [item for item in prerequisites if item["state"] != "exact"]
    if unmet:
        raise ContractError(
            "native install preflight refused unmet activation prerequisites:\n"
            + "\n".join(
                f"{item['asset']} at {item['path']}: {item['detail']}"
                for item in unmet
            )
        )
    chain = link_chain_problems(root, home, chosen, installing=True)
    if chain:
        raise ContractError(
            "native install preflight refused a broken link chain:\n"
            + "\n".join(chain)
        )
    entries = native_plan(root, home, chosen)
    states = [(entry, *entry_state(entry)) for entry in entries]
    foreign = [(entry, detail) for entry, state, detail in states if state == "foreign"]
    parent_problems: list[str] = []
    for entry in entries:
        try:
            preflight_safe_parent(home, entry.target.parent)
        except ContractError as error:
            parent_problems.append(str(error))
    if foreign or parent_problems:
        details = [f"{entry.target}: {detail}" for entry, detail in foreign]
        details.extend(parent_problems)
        raise ContractError(
            "native install preflight refused foreign targets or ancestors:\n"
            + "\n".join(details)
        )
    initially_missing = {
        entry for entry, state, _detail in states if state == "missing"
    }
    try:
        for entry, state, _detail in states:
            if state == "exact":
                continue
            create_entry(entry, home)
    except BaseException as error:
        rollback_errors: list[str] = []
        for entry in reversed(entries):
            if entry not in initially_missing:
                continue
            state, detail = entry_state(entry)
            if state == "missing":
                continue
            if state != "exact":
                rollback_errors.append(f"{entry.target}: {detail}")
                continue
            try:
                remove_entry(entry)
            except (ContractError, OSError) as rollback_error:
                rollback_errors.append(f"{entry.target}: {rollback_error}")
        if rollback_errors:
            raise ContractError(
                "native install failed and exact rollback was incomplete:\n"
                + "\n".join(rollback_errors)
            ) from error
        raise
    return [
        f"NOOP {entry.target}" if state == "exact" else f"INSTALLED {entry.target}"
        for entry, state, _detail in states
    ]


def uninstall_links(
    root: Path = ROOT,
    home: Path | None = None,
    clients: Iterable[str] | None = None,
) -> list[str]:
    selected_home = lexical_absolute((home or Path.home()).expanduser())
    chosen = selected_clients(clients)
    chain = link_chain_problems(root, selected_home, chosen, installing=False)
    if chain:
        raise ContractError(
            "native uninstall preflight refused a broken link chain:\n"
            + "\n".join(chain)
        )
    entries = native_plan(root, selected_home, chosen)
    states = [(entry, *entry_state(entry)) for entry in entries]
    foreign = [(entry, detail) for entry, state, detail in states if state == "foreign"]
    parent_problems: list[str] = []
    for entry in entries:
        try:
            preflight_safe_parent(selected_home, entry.target.parent)
        except ContractError as error:
            parent_problems.append(str(error))
    if foreign or parent_problems:
        details = [f"{entry.target}: {detail}" for entry, detail in foreign]
        details.extend(parent_problems)
        raise ContractError(
            "native uninstall preflight refused foreign targets or ancestors:\n"
            + "\n".join(details)
        )
    originally_exact = {entry for entry, state, _detail in states if state == "exact"}
    try:
        for entry, state, _detail in reversed(states):
            if state == "exact":
                remove_entry(entry)
    except BaseException as error:
        rollback_errors: list[str] = []
        for entry in entries:
            if entry not in originally_exact:
                continue
            state, detail = entry_state(entry)
            if state == "exact":
                continue
            if state != "missing":
                rollback_errors.append(f"{entry.target}: {detail}")
                continue
            try:
                create_entry(entry, selected_home)
            except (ContractError, OSError) as rollback_error:
                rollback_errors.append(f"{entry.target}: {rollback_error}")
        if rollback_errors:
            raise ContractError(
                "native uninstall failed and exact rollback was incomplete:\n"
                + "\n".join(rollback_errors)
            ) from error
        raise
    return [
        f"MISSING {entry.target}" if state == "missing" else f"REMOVED {entry.target}"
        for entry, state, _detail in states
    ]


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--root", type=Path, default=ROOT, help=argparse.SUPPRESS)
    commands = result.add_subparsers(dest="command", required=True)
    commands.add_parser("check")
    plan = commands.add_parser("plan")
    plan.add_argument("--json", action="store_true")
    install = commands.add_parser("install-links")
    uninstall = commands.add_parser("uninstall-links")
    for command in (plan, install, uninstall):
        command.add_argument("--home", type=Path, default=Path.home())
        command.add_argument(
            "--client",
            dest="clients",
            action="append",
            choices=CLIENTS,
            help="limit to this client's entries; repeat for more (default: all)",
        )
    render = commands.add_parser("render")
    render.add_argument("--check", action="store_true")
    return result


def main(arguments: Sequence[str] | None = None) -> int:
    options = parser().parse_args(arguments)
    root = options.root.resolve()
    try:
        if options.command == "render":
            if options.check:
                drift = render_drift(root)
                if drift:
                    raise ContractError(chr(10).join(drift))
                print("render: PASS")
            else:
                written = write_rendered(root)
                print(chr(10).join(written) if written else "no change")
                print("render: SYNCHRONIZED")
            return 0

        # Removal validates exact owned targets, adapters and safe ancestors.
        # An unrelated source-format or generated-file error must not trap an
        # installation. The lifecycle's preflight and rollback remain mandatory.
        if options.command == "uninstall-links":
            print("\n".join(uninstall_links(root, options.home, options.clients)))
            print("uninstall-links: APPLIED")
            return 0

        problems = check(root)
        if problems:
            raise ContractError("\n".join(problems))
        if options.command == "check":
            print("check: PASS")
        elif options.command == "plan":
            document = plan_document(root, options.home, options.clients)
            if options.json:
                print(canonical_json(document).decode("utf-8"), end="")
            else:
                print("\n".join(format_plan(document)))
                print("plan: PREVIEW")
        elif options.command == "install-links":
            print("\n".join(install_links(root, options.home, options.clients)))
            print("install-links: APPLIED")
    except (ContractError, OSError) as error:
        print(error, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
