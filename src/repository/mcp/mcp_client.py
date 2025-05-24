import asyncio
import websockets
import json

class MCPClient:
    """
    Client for connecting to MCP server and using remote tools.
    """
    
    def __init__(self, server_url="ws://localhost:8765"):
        """
        Constructor with server address.
        
        Args:
            server_url: URL of the MCP server.
        """
        self.server_url = server_url
        self.websocket = None
    
    async def connect(self):
        """
        Establishes connection to server.
        
        Returns:
            Boolean indicating success of connection.
        """
        try:
            self.websocket = await websockets.connect(self.server_url)
            return True
        except Exception as e:
            print(f"Failed to connect to MCP server: {e}")
            return False
    
    async def call_tool(self, tool_name, **kwargs):
        """
        Executes remote tool.
        
        Args:
            tool_name: Name of the remote tool to call.
            **kwargs: Arguments for the remote tool.
            
        Returns:
            Result from the remote tool execution.
        """
        if not self.websocket:
            success = await self.connect()
            if not success:
                return {"error": "Not connected to MCP server"}
        
        request = json.dumps({
            "tool_name": tool_name,
            "args": kwargs
        })
        
        try:
            await self.websocket.send(request)
            response = await self.websocket.recv()
            return json.loads(response)
        except Exception as e:
            return {"error": f"Failed to call remote tool: {e}"}
    
    async def close(self):
        """
        Closes the connection.
        """
        if self.websocket:
            await self.websocket.close()
            self.websocket = None