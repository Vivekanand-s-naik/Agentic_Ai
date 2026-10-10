from mcp.server.mcpserver import MCPServer

mcp = MCPServer("WEATHER")

@mcp.tool("weather")
def getCurrentWeather(location: str) -> str:
    return f"The weather in {location} is sunny."

if __name__ == "__main__":
    mcp.run(transport="streamable-http", host = "localhost", port = 11435)