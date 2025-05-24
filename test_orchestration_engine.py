import pytest
from src.repository.execution.orchestration_engine import OrchestrationEngine
from src.service.llm_factory import LLMFactory
from src.service.tool_service import ToolService

class DummyLLMFactory(LLMFactory):
    def create_llm(self, *args, **kwargs):
        class DummyLLM:
            def chat(self, messages):
                return {"content": messages[-1]["content"]}
        return DummyLLM()

def get_test_tool_service():
    config = {
        "bash": {
            "allowed_commands": ["*"],
            "disallowed_commands": []
        },
        "web_search": {
            "search_api_key": None,
            "search_engine_id": None
        },
        "browser_use": {},
        "planning": {},
        "chart": {"chart_script_path": None}
    }
    return ToolService(config)

def test_run_full_workflow_basic(tmp_path):
    workspace = str(tmp_path)
    llm_factory = DummyLLMFactory()
    tool_service = get_test_tool_service()
    engine = OrchestrationEngine(workspace, llm_factory, tool_service)
    user_prompt = "Build a simple to-do app with backend and frontend."
    result = engine.run_full_workflow(user_prompt, project_name="todo_app")
    assert result["success"] is True or result["success"] is False  # Should return a bool
    assert "project_name" in result
    assert "plan" in result
    assert "agent_flow_tasks" in result
    assert "codegen_result" in result

def test_run_full_workflow_failure(tmp_path):
    workspace = str(tmp_path)
    llm_factory = DummyLLMFactory()
    tool_service = get_test_tool_service()
    engine = OrchestrationEngine(workspace, llm_factory, tool_service)
    # Simulate a failure by passing an empty prompt
    result = engine.run_full_workflow("", project_name="fail_app")
    assert "success" in result
    # Should still return a result dict even if planning fails
