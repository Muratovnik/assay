#!/usr/bin/env python3
"""Official stdio MCP adapter. No protocol implementation or agent launcher."""
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
        """Comparative benchmark data for choosing routes, not enforced routing.

        Supply the complete host model/effort inventory once, not a preferred
        subset. Preserve unmeasured routes; only hard constraints exclude.
        Host inventory must be confirmed, not guessed. Measured model/effort
        rows are cohort-specific; API dollars and tokens are not subscription
        quota. Source errors do not prove that measurements do not exist.
        Offline results are diagnostic only.
        """
        try:
            return await service.get_routing_context(task_types, available=available,
                                                     constraints=constraints, details=details)
        except EvidenceError as exc:
            raise ToolError(str(exc)) from exc

    @server.tool()
    async def routing_status() -> dict[str, Any]:
        """Inspect configuration, protocol and capability gaps; no network requests.

        Configuration is not proof of hook installation, agent discovery or an
        observed model. Unsupported hosts report the enforcement gap explicitly.
        """
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
