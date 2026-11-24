# AI usage

## Tools I used, and for what

Codex drafted the retrieval, tool wrappers and triage loop. I used the supplied scripted model, pytest and the in-memory MCP client to check message ordering, tool behavior and citation enforcement.

## Whether my assistant produced MCP v1 code, and how I noticed

Codex used the starter's `from mcp.server import MCPServer` import from the beginning. I checked the three registered names and called a tool with the installed MCP 2.2.0 client.

## One hostile model move I thought of that the spec does not mention

A scripted model can return well-formed final JSON with a summary that is too large for the analyst note. I tried a 601-character summary. The schema rejected it, the loop recorded a failed final step and asked for valid JSON, and three repeated oversized replies led to `needs_human` with `invalid_output`.
