"""Independent compatibility checks for the minimal native projection plan."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

import assay as aa
import tomllib

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_ASSETS = {
    "profile/evidence-reviewer",
    "profile/official-docs-researcher",
    "skill/independent-audit",
    "skill/operations-ui-delivery",
    "skill/route-subagents",
    "skill/skill-design",
    "skill/evidence-research",
    "skill/test-writing",
    "skill/test-audit",
    "skill/code-maintenance",
    "skill/technical-writing",
}


def assert_inventory(catalog: aa.Catalog) -> None:
    actual = {asset.id for asset in catalog.assets}
    if actual != EXPECTED_ASSETS:
        raise aa.ContractError(
            f"compatibility fixture: expected {sorted(EXPECTED_ASSETS)}, got {sorted(actual)}"
        )


def assert_native_plan(catalog: aa.Catalog) -> None:
    with tempfile.TemporaryDirectory(prefix="assay-compat-") as directory:
        home = Path(directory)
        if aa.activation_prerequisites(ROOT, home):
            raise aa.ContractError("compatibility fixture: retired activation prerequisite returned")
        entries = aa.native_plan(ROOT, home)
        targets = {entry.target for entry in entries}
        expected_targets = {
            home / ".agents/skills/route-subagents",
            home / ".claude/skills/route-subagents",
            home / ".agents/skills/operations-ui-delivery",
            home / ".claude/skills/operations-ui-delivery",
            home / ".agents/skills/independent-audit",
            home / ".claude/skills/independent-audit",
            home / ".agents/skills/skill-design",
            home / ".claude/skills/skill-design",
            home / ".agents/skills/evidence-research",
            home / ".claude/skills/evidence-research",
            home / ".agents/skills/test-writing",
            home / ".claude/skills/test-writing",
            home / ".agents/skills/test-audit",
            home / ".claude/skills/test-audit",
            home / ".agents/skills/code-maintenance",
            home / ".claude/skills/code-maintenance",
            home / ".agents/skills/technical-writing",
            home / ".claude/skills/technical-writing",
            home / ".codex/agents/evidence-reviewer.toml",
            home / ".claude/agents/evidence-reviewer.md",
            home / ".codex/agents/official-docs-researcher.toml",
            home / ".claude/agents/official-docs-researcher.md",
        }
        if targets != expected_targets:
            raise aa.ContractError(
                f"compatibility fixture: native targets drifted: {sorted(map(str, targets))}"
            )
        claude_skill = next(
            entry
            for entry in entries
            if entry.asset_id == "skill/route-subagents" and entry.client == "claude"
        )
        if claude_skill.source != home / ".agents/skills/route-subagents":
            raise aa.ContractError(
                "compatibility fixture: Claude must link through native skills"
            )
        operations = next(
            entry
            for entry in entries
            if entry.asset_id == "skill/operations-ui-delivery"
            and entry.client == "claude"
        )
        if operations.source != home / ".agents/skills/operations-ui-delivery":
            raise aa.ContractError(
                "compatibility fixture: operations UI delivery must use native skills"
            )
        skill_design = next(
            entry
            for entry in entries
            if entry.asset_id == "skill/skill-design" and entry.client == "claude"
        )
        if skill_design.source != home / ".agents/skills/skill-design":
            raise aa.ContractError(
                "compatibility fixture: skill design must use native skills"
            )
        if next(
            asset for asset in catalog.assets if asset.id == "skill/skill-design"
        ).activation != "automatic":
            raise aa.ContractError(
                "compatibility fixture: skill design must retain automatic discovery"
            )
        if any(".codex/skills" in entry.target.as_posix() for entry in entries):
            raise aa.ContractError(
                "compatibility fixture: deprecated Codex skill root returned"
            )

        for name in ("test-writing", "test-audit", "evidence-research", "code-maintenance"):
            asset_id = f"skill/{name}"
            asset = next(item for item in catalog.assets if item.id == asset_id)
            if asset.activation != "automatic":
                raise aa.ContractError(
                    f"compatibility fixture: {name} must allow automatic discovery"
                )
            for client, expected_source in (
                ("codex", ROOT / "skills" / name),
                ("claude", home / ".agents/skills" / name),
            ):
                entry = next(
                    item for item in entries
                    if item.asset_id == asset_id and item.client == client
                )
                if entry.source != expected_source or entry.mode != "link":
                    raise aa.ContractError(
                        f"compatibility fixture: {name} lost its native {client} link"
                    )

        evidence = next(
            asset for asset in catalog.assets if asset.id == "profile/evidence-reviewer"
        )
        source = (ROOT / evidence.path).read_bytes()
        codex = aa.render_profile(source, evidence, "codex").decode("utf-8", "strict")
        claude = aa.render_profile(source, evidence, "claude").decode("utf-8", "strict")
        codex_document = tomllib.loads(codex)
        if codex_document.get("sandbox_mode") != "read-only":
            raise aa.ContractError(
                "compatibility fixture: Codex reviewer lost read-only sandbox"
            )
        header = claude.split("\n---\n", 1)[0]
        if "tools: Read, Grep, Glob, ToolSearch, Bash" not in header:
            raise aa.ContractError(
                "compatibility fixture: Claude reviewer cannot run its oracle"
            )
        if "permissionMode: plan" not in header:
            raise aa.ContractError(
                "compatibility fixture: Claude reviewer lost plan mode"
            )
        profile = json.loads(source.decode("utf-8", "strict"))
        if "read-only-oracle" not in profile["capabilities"]:
            raise aa.ContractError(
                "compatibility fixture: reviewer oracle capability is absent"
            )


def main() -> int:
    try:
        problems = aa.check(ROOT)
        if problems:
            raise aa.ContractError("\n".join(problems))
        catalog = aa.load_catalog(ROOT)
        assert_inventory(catalog)
        assert_native_plan(catalog)
    except (aa.ContractError, OSError) as error:
        print(f"compatibility fixture: FAIL: {error}", file=sys.stderr)
        return 1
    print("compatibility fixture: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
