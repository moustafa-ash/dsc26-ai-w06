"""MCP server exposing Hisn's three tools. You write this file (mcp 2.2.0, the v2 SDK)."""
from __future__ import annotations

import json

from mcp.server import MCPServer
from mcp_types import CallToolResult, TextContent

from hisn import tools

server = MCPServer("hisn-triage")


def _result(value: dict | list[dict]) -> CallToolResult:
    # MCP structured content must be an object. Preserve the exact value in the text block.
    structured = value if isinstance(value, dict) else {"result": value}
    return CallToolResult(
        content=[TextContent(type="text", text=json.dumps(value, ensure_ascii=False))],
        structured_content=structured,
    )


@server.tool()
def lookup_asset(host: str) -> CallToolResult:
    """Look up the owner and criticality of a host."""
    return _result(tools.lookup_asset(host))


@server.tool()
def search_runbooks(query: str, k: int = 3) -> CallToolResult:
    """Find runbooks that apply to an alert."""
    return _result(tools.search_runbooks(query, k))


@server.tool()
def related_alerts(rule_id: str, agent: str, around: str, window_minutes: int = 60) -> CallToolResult:
    """Count matching earlier alerts for a host and rule."""
    return _result(tools.related_alerts(rule_id, agent, around, window_minutes))


if __name__ == "__main__":
    server.run()  # stdio transport by default
