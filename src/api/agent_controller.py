from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, List, Optional, Any, Union
import uuid

from src.service.agent_service import AgentService
from src.service.llm_factory import LLMFactory
from src.service.tool_service import ToolService
from src.schemas.agent import (
    AgentConfig, CreateAgentRequest, AgentResponse, 
    QueryRequest, QueryResponse, LLMConfig
)

# API Controller
class AgentController:
    """
    API controller for agent management and execution.
    """
    
    def __init__(self, app: FastAPI, agent_service: AgentService):
        """
        Initialize the controller with FastAPI app and services.
        
        Args:
            app: FastAPI application instance.
            agent_service: Agent service instance.
        """
        self.app = app
        self.agent_service = agent_service
        self._register_routes()
    
    def _register_routes(self):
        """
        Register API routes.
        """
        # Create a new agent
        @self.app.post("/api/agents", response_model=AgentResponse)
        async def create_agent(request: CreateAgentRequest):
            try:
                config = request.config
                if config is None:
                    config = AgentConfig(
                        id=str(uuid.uuid4()),
                        name=request.name,
                        llm=LLMConfig(provider="gemini", model="gemini-2.0-flash"),
                        tools=[],
                    )
                # Generate unique ID if not provided
                if not config.id:
                    config.id = str(uuid.uuid4())
                
                # Create agent
                agent = self.agent_service.create_agent(request.type, config.model_dump())
                
                return {
                    "id": config.id,
                    "type": request.type,
                    "name": agent.name,
                    "description": request.description,
                    "status": "ready",
                    "tools": list(config.tools)
                }
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        # Get all agents
        @self.app.get("/api/agents", response_model=List[AgentResponse])
        async def get_agents():
            try:
                result = []
                for agent_id, agent in self.agent_service.agents.items():
                    result.append({
                        "id": agent_id,
                        "type": agent.__class__.__name__.replace("Agent", "").lower(),
                        "name": agent.name,
                        "description": getattr(agent, "system_prompt", "")[:160],
                        "status": "ready",
                        "tools": [tool.name for tool in agent.tools]
                    })
                return result
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        # Get agent by ID
        @self.app.get("/api/agents/{agent_id}", response_model=AgentResponse)
        async def get_agent(agent_id: str):
            agent = self.agent_service.get_agent(agent_id)
            if not agent:
                raise HTTPException(status_code=404, detail=f"Agent with ID {agent_id} not found")
                
            return {
                "id": agent_id,
                "type": agent.__class__.__name__.replace("Agent", "").lower(),
                "name": agent.name,
                "description": getattr(agent, "system_prompt", "")[:160],
                "status": "ready",
                "tools": [tool.name for tool in agent.tools]
            }
        
        # Delete agent
        @self.app.delete("/api/agents/{agent_id}")
        async def delete_agent(agent_id: str):
            success = self.agent_service.delete_agent(agent_id)
            if not success:
                raise HTTPException(status_code=404, detail=f"Agent with ID {agent_id} not found")
                
            return {"success": True}
        
        # Run query on agent
        @self.app.post("/api/agents/{agent_id}/query", response_model=QueryResponse)
        async def run_query(agent_id: str, request: QueryRequest):
            try:
                agent = self.agent_service.get_agent(agent_id)
                if not agent:
                    raise HTTPException(status_code=404, detail=f"Agent with ID {agent_id} not found")
                    
                response = self.agent_service.run_query(agent_id, request.query)
                
                # In a real implementation, we would extract tool calls from agent's history
                tool_calls = []
                
                return {
                    "agent_id": agent_id,
                    "query": request.query,
                    "response": response,
                    "tool_calls": tool_calls
                }
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
    
    @staticmethod
    def create_app():
        """
        Create and configure FastAPI application.
        
        Returns:
            Configured FastAPI application.
        """
        app = FastAPI(title="Zelash API", description="AI Agent Framework API", version="1.0.0")
        
        # Configure CORS
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        return app
