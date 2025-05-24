from fastapi import FastAPI, HTTPException
from typing import Dict, List, Optional, Any

from src.service.tool_service import ToolService
from src.schemas.tool import (
    ToolConfigUpdate, ToolRegistration, 
    ToolResponse, MCPConnection
)

# API Controller
class ToolController:
    """
    API controller for tool management.
    """
    
    def __init__(self, app: FastAPI, tool_service: ToolService):
        """
        Initialize the controller with FastAPI app and tool service.
        
        Args:
            app: FastAPI application instance.
            tool_service: Tool service instance.
        """
        self.app = app
        self.tool_service = tool_service
        self._register_routes()
    
    def _register_routes(self):
        """
        Register API routes.
        """
        # Get all available tools
        @self.app.get("/api/tools", response_model=List[ToolResponse])
        async def get_tools():
            try:
                result = []
                for name, tool in self.tool_service.tools.items():
                    result.append({
                        "name": tool.name,
                        "description": tool.description,
                        "schema": tool.args_schema
                    })
                return result
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        # Get tool by name
        @self.app.get("/api/tools/{name}", response_model=ToolResponse)
        async def get_tool(name: str):
            tool = self.tool_service.get_tool(name)
            if not tool:
                raise HTTPException(status_code=404, detail=f"Tool '{name}' not found")
                
            return {
                "name": tool.name,
                "description": tool.description,
                "schema": tool.args_schema
            }
        
        # Update tool configuration
        @self.app.patch("/api/tools/config", response_model=Dict[str, Any])
        async def update_tool_config(request: ToolConfigUpdate):
            try:
                updated_config = self.tool_service.update_config(request.config)
                return {"config": updated_config}
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        # Connect to MCP server
        @self.app.post("/api/tools/mcp/connect")
        async def connect_mcp(request: MCPConnection):
            try:
                success = self.tool_service.connect_mcp(request.server_url)
                if not success:
                    raise HTTPException(status_code=500, detail="Failed to connect to MCP server")
                return {"connected": True, "server_url": request.server_url}
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        # Register remote tool
        @self.app.post("/api/tools/mcp/register", response_model=ToolResponse)
        async def register_remote_tool(request: ToolRegistration):
            try:
                if not self.tool_service.mcp_client:
                    raise HTTPException(status_code=400, detail="MCP client not connected")
                    
                tool = self.tool_service.register_remote_tool(
                    request.name,
                    request.description,
                    request.args_schema
                )
                
                return {
                    "name": tool.name,
                    "description": tool.description,
                    "schema": tool.args_schema
                }
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))