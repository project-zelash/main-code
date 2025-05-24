from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any, Union

class LLMConfig(BaseModel):
    """Configuration for language models."""
    provider: str = Field(..., description="LLM provider name (openai, anthropic, etc.)")
    model: str = Field(..., description="Model name (gpt-4, claude, etc.)")
    api_key: Optional[str] = Field(None, description="API key for the provider")
    temperature: float = Field(0.7, description="Temperature for generation")
    max_tokens: Optional[int] = Field(None, description="Maximum tokens in response")
    extra_params: Optional[Dict[str, Any]] = Field(None, description="Additional parameters")

class AgentConfig(BaseModel):
    """Configuration for creating or updating an agent."""
    id: Optional[str] = Field(None, description="Unique identifier for the agent")
    name: str = Field(..., description="Display name for the agent")
    llm: LLMConfig = Field(..., description="Language model configuration")
    system_prompt: Optional[str] = Field(None, description="System instructions for the agent")
    tools: List[str] = Field(default=[], description="List of tool names available to the agent")
    verbose: bool = Field(False, description="Enable detailed logging")
    max_iterations: int = Field(5, description="Maximum tool calling iterations")
    memory_enabled: bool = Field(True, description="Enable conversation history")

class AgentSchema(BaseModel):
    """Schema definition for an agent."""
    name: str = Field(..., description="Unique identifier for the agent")
    type: str = Field(..., description="Type of agent (e.g., analysis, research, writing)")
    description: str = Field(..., description="Short description of the agent's purpose")
    capabilities: List[str] = Field(default=[], description="List of agent capabilities")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Optional configuration parameters")

class CreateAgentRequest(BaseModel):
    """Request for creating a new agent."""
    type: str = Field(..., description="Agent type (analysis, research, writing, etc.)")
    name: str = Field(..., description="Display name for the agent")
    description: str = Field(..., description="Short description of the agent's purpose")
    config: Optional[Dict[str, Any]] = Field(None, description="Additional configuration options")

class AgentResponse(BaseModel):
    """Response containing agent information."""
    id: str = Field(..., description="Unique identifier for the agent")
    type: str = Field(..., description="Agent type")
    name: str = Field(..., description="Display name for the agent")
    description: str = Field(..., description="Short description of the agent's purpose")
    status: str = Field(..., description="Current status of the agent")

class ExecuteAgentRequest(BaseModel):
    """Request for executing an agent."""
    input: Dict[str, Any] = Field(..., description="Agent input parameters")
    tools: Optional[List[str]] = Field(None, description="List of tool IDs the agent can use")
    memory_id: Optional[str] = Field(None, description="Memory ID for persistent context")

class ExecuteAgentResponse(BaseModel):
    """Response from an agent execution."""
    agent_id: str = Field(..., description="Agent ID that was executed")
    input: Dict[str, Any] = Field(..., description="Agent input parameters")
    output: Any = Field(..., description="Agent execution result")
    tool_calls: List[Dict[str, Any]] = Field(default=[], description="Tool calls made by the agent")
    error: Optional[str] = Field(None, description="Error message if execution failed")

class QueryRequest(BaseModel):
    """Request for querying an agent."""
    query: str = Field(..., description="User query to process")

class ToolCallRecord(BaseModel):
    """Record of a tool call made by an agent."""
    tool: str = Field(..., description="Tool name")
    input: Dict[str, Any] = Field(..., description="Tool input arguments")
    output: Any = Field(..., description="Tool output result")

class QueryResponse(BaseModel):
    """Response from an agent query."""
    agent_id: str = Field(..., description="Agent ID that processed the query")
    query: str = Field(..., description="Original user query")
    response: str = Field(..., description="Agent's response")
    tool_calls: List[ToolCallRecord] = Field(default=[], description="Record of tool calls made")