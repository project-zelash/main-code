from src.service.agent_service import AgentService
from src.service.llm_factory import LLMFactory
from src.service.tool_service import ToolService

llm_factory = LLMFactory()
tool_service = ToolService()
agent_service = AgentService(llm_factory, tool_service)

agent_config = {
    "id": "manual-test-agent",
    "llm": {"provider": "gemini", "model": "gemini-2.0-flash", "temperature": 0.7},
    "tools": [],
    "system_prompt": "You are a test agent.",
    "name": "ManualTestAgent",
    "verbose": True,
    "max_iterations": 2
}

# Create agent
agent = agent_service.create_agent("manus", agent_config)
print("Agent created:", agent)

# Run a query
result = agent_service.run_query("manual-test-agent", "Say hello!")
print("Agent response:", result)

# Delete agent
deleted = agent_service.delete_agent("manual-test-agent")
print("Agent deleted:", deleted)
