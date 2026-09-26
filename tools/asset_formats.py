"""Safe YAML syntax shared by skill metadata and native adapters.

Format parsing lives here; catalog agreement and field policy belong to the
caller. No import of the installer, and no change to PyYAML's global loader.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

FRONTMATTER = re.compile(r"\A---\r?\n(?P<body>.*?)\r?\n---(?:\r?\n|\Z)", re.DOTALL)


class ContractError(ValueError):
    """A user-facing contract violation."""


def yaml_mapping(text: str, *, label: str) -> dict[str, Any]:
    """Read YAML with unique string keys and explicit true/false booleans.

    Aliases and merge keys are deliberately unsupported in Assay metadata.
    SafeLoader handles YAML syntax, including quoted and multiline scalars.
    """
    try:
        import yaml
    except ImportError as error:
        raise ContractError(
            "YAML validation requires PyYAML; run "
            "python -m pip install -r requirements-tools.txt in your environment"
        ) from error

    class MetadataLoader(yaml.SafeLoader):
        def compose_node(self, parent: Any, index: Any) -> Any:
            if self.check_event(yaml.AliasEvent):
                raise ContractError(f"{label} YAML aliases are not supported")
            return super().compose_node(parent, index)

        def construct_mapping(self, node: Any, deep: bool = False) -> dict[str, Any]:
            if not isinstance(node, yaml.MappingNode):
                raise ContractError(f"{label} YAML requires a mapping")
            result: dict[str, Any] = {}
            for key_node, value_node in node.value:
                key = self.construct_object(key_node, deep=deep)
                if not isinstance(key, str):
                    raise ContractError(f"{label} YAML keys must be strings")
                if key in result:
                    raise ContractError(f"duplicate YAML key {key!r}")
                result[key] = self.construct_object(value_node, deep=deep)
            return result

    MetadataLoader.yaml_implicit_resolvers = {
        key: [(tag, pattern) for tag, pattern in values
              if tag != "tag:yaml.org,2002:bool"]
        for key, values in yaml.SafeLoader.yaml_implicit_resolvers.items()
    }
    MetadataLoader.add_implicit_resolver(
        "tag:yaml.org,2002:bool", re.compile(r"^(?:true|false)$"), list("tf")
    )
    try:
        document = yaml.load(text, Loader=MetadataLoader)
    except yaml.YAMLError as error:
        raise ContractError(f"invalid {label} YAML: {error}") from error
    if not isinstance(document, dict):
        raise ContractError(f"{label} YAML must be an object")
    return document


def frontmatter(path: Path) -> dict[str, object]:
    match = FRONTMATTER.match(path.read_text(encoding="utf-8", errors="strict"))
    if not match:
        raise ContractError("missing YAML frontmatter")
    return yaml_mapping(match.group("body") + "\n", label="frontmatter")


def openai_adapter_document(text: str) -> dict[str, Any]:
    return yaml_mapping(text, label="adapter")
