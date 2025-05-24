import os
import sys
import dotenv
from src.repository.execution.orchestration_engine import OrchestrationEngine
from src.service.llm_factory import LLMFactory
from src.service.tool_service import ToolService
from src.repository.tools.bash_tool import BashTool
from src.utils.prompt_manager import get_user_prompt, get_prompt_from_args

def get_manual_tool_service():
    from src.service.tool_service import ToolService
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

def print_failed_task_details(codegen_result, agent_flow_tasks):
    print("\n=== Failed Tasks Details ===")
    flow_results = codegen_result.get('flow_results', {})
    task_map = {task['name']: task for task in agent_flow_tasks}
    for task_name, result in flow_results.items():
        if not result or (isinstance(result, dict) and 'error_type' in result) or (isinstance(result, str) and not result.strip()):
            print(f"Task: {task_name}")
            task_info = task_map.get(task_name)
            if task_info:
                print(f"  Agent: {task_info.get('agent')}")
                input_str = task_info.get('input', '')
                print(f"  Input: {input_str[:300]}{'...' if len(input_str) > 300 else ''}")
            if result is None:
                print("  Result: None (no error info captured, agent may have returned None)\n")
            elif isinstance(result, dict):
                for k, v in result.items():
                    print(f"  {k}: {v if isinstance(v, str) and len(v) < 500 else str(v)[:500] + '...'}")
                print()
            elif isinstance(result, str) and not result.strip():
                print("  Result: '' (empty string returned by agent)\n")
            else:
                print(f"  Result: {result}\n")

def main():
    dotenv.load_dotenv()
    if "GEMINI_API_KEY" not in os.environ:
        print("ERROR: GEMINI_API_KEY environment variable is not set. Please set it in your .env file.")
        return

    # Ensure your API key is set in the environment, e.g.:
    # os.environ["OPENAI_API_KEY"] = "sk-..."
    workspace = "./manual_test_workspace"
    os.makedirs(workspace, exist_ok=True)

    llm_factory = LLMFactory()
    tool_service = get_manual_tool_service()
    engine = OrchestrationEngine(workspace, llm_factory, tool_service)

    # Get user prompt dynamically instead of hardcoding
    # You can change the method here:
    # - "interactive": Ask user for input
    # - "preset": Use a preset (e.g., get_user_prompt("preset", prompt_key="todo_app"))
    # - "custom": Pass custom prompt (e.g., get_user_prompt("custom", custom_prompt="Your prompt"))
    # - "env": Use ORCHESTRATION_PROMPT environment variable
    
    # For command line usage: python manual_orchestration_workflow_check.py "Your prompt here"
    user_prompt = get_prompt_from_args() if len(sys.argv) > 1 else get_user_prompt("interactive")
    
    print("Running full orchestration workflow...")
    result = engine.run_full_workflow(user_prompt, project_name="manual_todo_app")

    print("\n=== Orchestration Workflow Result ===")
    for k, v in result.items():
        v_str = str(v)
        print(f"{k}: {v_str if len(v_str) < 500 else v_str[:500] + '...'}")
    # Print detailed error info for failed tasks
    if 'codegen_result' in result:
        print_failed_task_details(result['codegen_result'], result.get('agent_flow_tasks', []))
        # Print succeeded and failed tasks
        all_tasks = [task['name'] for task in result.get('agent_flow_tasks', [])]
        flow_results = result['codegen_result'].get('flow_results', {})
        completed_tasks = [name for name, res in flow_results.items() if res and not (isinstance(res, dict) and 'error_type' in res)]
        failed_tasks = [name for name in all_tasks if name not in completed_tasks]
        print("\n=== Succeeded Tasks ===")
        for name in completed_tasks:
            print(name)
        print("\n=== Failed Tasks ===")
        for name in failed_tasks:
            print(name)

if __name__ == "__main__":
    main()
