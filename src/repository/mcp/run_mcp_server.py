import asyncio
from src.repository.mcp.mcp_server import MCPServer
from src.service.tool_service import ToolService

def main():
    # Initialize ToolService and get all available tools
    tool_service = ToolService()
    tools = tool_service.get_tools()
    # Start the MCP server with all tools
    server = MCPServer(tools=tools)
    print("[INFO] Starting MCP server on ws://localhost:8765 ...")
    asyncio.run(server.run_server(host="localhost", port=8765))

if __name__ == "__main__":
    main()
