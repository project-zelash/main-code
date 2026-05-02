import threading
from typing import Any, Dict, Optional
from src.repository.agent.backend_agent import BackendAgent
from src.repository.agent.frontend_agent import FrontendAgent
from src.repository.agent.middleware_agent import MiddlewareAgent
from src.repository.agent.design_agent import DesignAgent
from src.repository.agent.research_agent import ResearchAgent
from src.repository.agent.analysis_agent import AnalysisAgent
from src.repository.agent.writing_agent import WritingAgent
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
            llm = self.llm_factory.create_default_llm()
            tools = list(self.tool_service.get_tools().values())  # Ensure this is a list of tool instances
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
                "frontend",
                FrontendAgent(
                    llm=llm,
                    tools=tools,
                    name="FrontendAgent",
                    verbose=True
                ),
                capabilities={"type": "frontend"}
            )
            self.register_agent("design", DesignAgent(llm=llm, tools=tools, verbose=True), capabilities={"type": "design"})
            self.register_agent("research", ResearchAgent(llm=llm, tools=tools, verbose=True), capabilities={"type": "research"})
            self.register_agent("analysis", AnalysisAgent(llm=llm, tools=tools, verbose=True), capabilities={"type": "analysis"})
            self.register_agent("writing", WritingAgent(llm=llm, tools=tools, verbose=True), capabilities={"type": "writing"})

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
        try:
            result = agent.run(task["input"], context=task_context)
            return {
                "status": "completed",
                "agent": agent_name,
                "task_id": task.get("id") or task.get("name"),
                "output": result,
            }
        except Exception as exc:
            return {
                "status": "failed",
                "agent": agent_name,
                "task_id": task.get("id") or task.get("name"),
                "error": str(exc),
            }

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

    def initialize_agents(self):
        return self._initialize_agents()
