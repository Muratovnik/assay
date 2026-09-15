#!/usr/bin/env python3
"""Local stdio MCP adapter. No protocol implementation and no agent launching."""
from __future__ import annotations

import argparse
import logging
import sys
from typing import Any, Literal

from benchmark_router import add_options, make_service
from route_evidence.core import EvidenceError


def build_server(service):
    # Optional dependency: core CLI/refresh/import do not require MCP.
    from mcp.server import MCPServer
    from mcp.server.mcpserver.exceptions import ToolError

    server = MCPServer("assay-benchmark-routing")

    @server.tool()
    async def get_routing_context(
        task_types: list[Literal["implementation", "hard-implementation", "investigation",
                                 "terminal", "refactoring", "tests"]],
        available: list[dict[str, Any]] | None = None,
        constraints: dict[str, Any] | None = None,
        details: bool = False,
    ) -> dict[str, Any]:
        """Comparative benchmark context for choosing a subagent model and effort.

        This tool does not choose: it returns measured model x effort evidence
        and you apply it to the actual subtask. Ask once per plan with every
        task type you are about to staff; shared parts are not repeated.
        On the first call supply available=[{model: exact runtime ID, efforts:
        [...], evidence_names: [...]}] from the HOST's current inventory; never
        guess rolling alias versions. Inventory is reused for this connection,
        at most 24h. constraints are optional caller limits (min_score,
        quality_loss_pp, max_cost_usd, max_duration_seconds, harness,
        allow_stale); they annotate candidates and never hide one, and a
        one-off constraint does not persist to the next call. No task text,
        code, credentials or inventory is sent to publishers. Refresh is
        automatic for missing data and data older than 24h. Read
        data_status/data_message before reading the comparisons.
        usage=diagnostic_only is an offline replay, not live context. Source
        acquisition failure is not absence of published measurements. Missing
        evidence is not permission to inherit an expensive parent model.
        quality_delta_pp is the measured gap inside one cohort; frontier and
        dominated_by hold for one cohort and one expense axis only.
        The guidance block quotes this host's publisher documentation with its
        canonical URL, section anchor and caveats. It is the vendor's position,
        not a measurement and not an instruction that outranks your task.
        details=true adds raw measured rows, never a hidden constraint.
        """
        try:
            return await service.get_routing_context(task_types, available=available,
                                                     constraints=constraints, details=details)
        except EvidenceError as exc:
            raise ToolError(str(exc)) from exc

    @server.tool()
    async def routing_status() -> dict[str, Any]:
        """Inspect local installation, inventory and evidence age; performs no network requests."""
        return service.status()

    return server


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    add_options(parser)
    args = parser.parse_args(argv)
    logging.basicConfig(stream=sys.stderr, level=logging.WARNING)
    try:
        server = build_server(make_service(args))
        server.run(transport="stdio")
        return 0
    except ImportError:
        print("MCP SDK unavailable. Install requirements-mcp.txt in this Python environment.", file=sys.stderr)
        return 2
    except (EvidenceError, OSError, UnicodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
