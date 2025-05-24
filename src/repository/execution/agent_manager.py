import threading
from typing import Any, Dict, Optional
from src.repository.agent.backend_agent import BackendAgent
from src.repository.agent.frontend_agent import FrontendAgent
from src.repository.agent.middleware_agent import MiddlewareAgent
from src.repository.agent.design_agent import DesignAgent
from src.service.llm_factory import LLMFactory
from src.service.tool_service import ToolService

class AgentManager:
    def __init__(self, llm_factory: LLMFactory, tool_service: ToolService):
        self.llm_factory = llm_factory
        self.tool_service = tool_service
        self.agents = {}
        self._initialize_agents()

    def _initialize_agents(self):
        if not self.agents:
            llm = self.llm_factory.create_llm("gemini", "gemini-1.5-pro")
            tools = self.tool_service.get_tools()
            # Register all default agents with a consistent structure
            self.register_agent(
                "backend",
                BackendAgent(
                    llm=llm,
                    tools=tools,
                    name="BackendAgent",
                    verbose=True
                ),
                capabilities={"type": "backend"}
            )
            self.register_agent(
                "middleware",
                MiddlewareAgent(
                    llm=llm,
                    tools=tools,
                    name="MiddlewareAgent",
                    verbose=True
                ),
                capabilities={"type": "middleware"}
            )
            self.register_agent(
                "design",
                DesignAgent(
                    llm=llm,
                    tools=tools,
                    name="DesignAgent",
                    verbose=True
                ),
                capabilities={"type": "design"}
            )
            self.register_agent(
                "frontend",
                FrontendAgent(
                    llm=llm,
                    tools=tools,
                    name="FrontendAgent",
                    verbose=True
                ),
                capabilities={"type": "frontend"}
            )

    def register_agent(self, agent_name: str, agent_instance: Any, capabilities: dict = None) -> None:
        self.agents[agent_name] = {
            "instance": agent_instance,
            "capabilities": capabilities or {}
        }

    def submit_task(self, agent_name: str, task: dict, context: dict) -> dict:
        agent_entry = self.agents.get(agent_name)
        if not agent_entry:
            return {"status": "error", "message": f"Agent {agent_name} not registered."}
        agent = agent_entry["instance"]
        task_context = task.get("context") or context
        result = agent.run(task["input"], context=task_context)
        return result

    def list_agents(self) -> list:
        return [
            {"name": name, "capabilities": entry["capabilities"]}
            for name, entry in self.agents.items()
        ]

    def get_agent(self, agent_name: str):
        entry = self.agents.get(agent_name)
        if entry:
            return entry.get("instance")
        return None
