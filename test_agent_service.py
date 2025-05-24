import sys
import os
import pytest

sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from service.agent_service import AgentService
from service.llm_factory import LLMFactory
from service.tool_service import ToolService

def get_basic_agent_config(agent_id):
    return {
        "id": agent_id,
        "llm": {"provider": "openai", "model": "gpt-3.5-turbo"},
        "tools": [],
        "system_prompt": "You are a test agent.",
        "name": f"TestAgent_{agent_id}",
        "verbose": False,
        "max_iterations": 2,
        "memory_enabled": True
    }

@pytest.fixture
def agent_service():
    llm_factory = LLMFactory()
    tool_service = ToolService()
    return AgentService(llm_factory, tool_service)

def test_create_and_get_agent(agent_service):
    agent_config = get_basic_agent_config("test-agent-1")
    agent = agent_service.create_agent("manus", agent_config)
    assert agent is not None
    assert agent_service.get_agent("test-agent-1") is agent

def test_run_query(agent_service):
    agent_config = get_basic_agent_config("test-agent-2")
    agent_service.create_agent("manus", agent_config)
    result = agent_service.run_query("test-agent-2", "Hello, agent!")
    assert isinstance(result, str) or result is not None

def test_delete_agent(agent_service):
    agent_config = get_basic_agent_config("test-agent-3")
    agent_service.create_agent("manus", agent_config)
    assert agent_service.get_agent("test-agent-3") is not None
    deleted = agent_service.delete_agent("test-agent-3")
    assert deleted
    assert agent_service.get_agent("test-agent-3") is None

if __name__ == "__main__":
    pytest.main([__file__])
