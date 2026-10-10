# from mcp.server.fastmcp import FastMCP
from mcp.server.mcpserver import MCPServer
mcp = MCPServer("MATH")

@mcp.tool("add")
def add(a: int, b: int) -> int:
    return a+b


if __name__ == "__main__":
    mcp.run(transport="stdio")
