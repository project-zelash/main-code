import asyncio
import websockets
import json

class MCPServer:
    """
    WebSocket server for remote tool execution.
    """
    
    def __init__(self, tools):
        """
        Constructor with available tools.
        
        Args:
            tools: Dictionary of available tools.
        """
        self.tools = tools
        
    async def run_server(self, host="localhost", port=8765):
        """
        Starts the WebSocket server.
        
        Args:
            host: Server host address.
            port: Server port number.
        """
        async with websockets.serve(self.websocket_endpoint, host, port):
            print(f"MCP Server running on {host}:{port}")
            await asyncio.Future()  # Run forever
    
    async def websocket_endpoint(self, websocket):
        """
        Handles WebSocket connections.
        
        Args:
            websocket: WebSocket connection object.
        """
        try:
            async for message in websocket:
                try:
                    request = json.loads(message)
                    tool_name = request.get("tool_name")
                    args = request.get("args", {})
                    
                    if tool_name in self.tools:
                        result = await self.tools[tool_name].run(**args)
                        await websocket.send(json.dumps({"status": "success", "result": result}))
                    else:
                        await websocket.send(json.dumps({"status": "error", "message": f"Tool {tool_name} not found"}))
                except Exception as e:
                    await websocket.send(json.dumps({"status": "error", "message": str(e)}))
        except websockets.exceptions.ConnectionClosed:
            pass
    
    def get_tools(self):
        """
        Returns available tool definitions.
        
        Returns:
            Dictionary of available tools with their schemas.
        """
        return {name: tool.to_dict() for name, tool in self.tools.items()}