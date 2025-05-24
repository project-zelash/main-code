from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any

class ToolSchema(BaseModel):
    """Schema definition for a tool."""
    name: str = Field(..., description="Unique identifier for the tool")
    description: str = Field(..., description="Short description of the tool's purpose")
    parameters: Dict[str, Any] = Field(..., description="JSON Schema for tool parameters")
    required_parameters: List[str] = Field(default=[], description="List of required parameter names")

class ToolConfig(BaseModel):
    """Configuration for creating or updating a tool."""
    id: Optional[str] = Field(None, description="Unique identifier for the tool")
    name: str = Field(..., description="Display name for the tool")
    description: str = Field(..., description="Short description of the tool's purpose")
    schema: ToolSchema = Field(..., description="Schema definition for the tool")
    config: Optional[Dict[str, Any]] = Field(None, description="Additional configuration options")

class CreateToolRequest(BaseModel):
    """Request for creating a new tool."""
    type: str = Field(..., description="Tool type (bash, web_search, browser, etc.)")
    config: ToolConfig = Field(..., description="Tool configuration")

class ToolResponse(BaseModel):
    """Response containing tool information."""
    id: str = Field(..., description="Unique identifier for the tool")
    type: str = Field(..., description="Tool type")
    name: str = Field(..., description="Display name for the tool")
    description: str = Field(..., description="Short description of the tool's purpose")

class ExecuteToolRequest(BaseModel):
    """Request for executing a tool."""
    input: Dict[str, Any] = Field(..., description="Tool input parameters")

class ExecuteToolResponse(BaseModel):
    """Response from a tool execution."""
    tool_id: str = Field(..., description="Tool ID that was executed")
    input: Dict[str, Any] = Field(..., description="Tool input parameters")
    output: Any = Field(..., description="Tool execution result")
    error: Optional[str] = Field(None, description="Error message if execution failed")