from src.repository.execution.agent_flow import AgentFlow
from src.repository.agent.backend_agent import BackendAgent
from src.repository.agent.frontend_agent import FrontendAgent
from src.repository.agent.middleware_agent import MiddlewareAgent
from src.repository.llm.gemini_llm import GeminiLLM
from src.repository.tools.bash_tool import BashTool
from src.repository.tools.planning_tool import PlanningTool
import os
from dotenv import load_dotenv

load_dotenv()

if __name__ == "__main__":
    # Set up Gemini LLM (ensure your GEMINI_API_KEY is in the environment)
    gemini_llm = GeminiLLM(model="gemini-2.0-flash", temperature=0.2)
    tools = [BashTool(), PlanningTool()]

    # Create real agents
    agents = {
        "backend": BackendAgent(
            llm=gemini_llm,
            tools=tools,
            name="BackendAgent",
            verbose=True,
            max_iterations=3
        ),
        "frontend": FrontendAgent(
            llm=gemini_llm,
            tools=tools,
            name="FrontendAgent",
            verbose=True,
            max_iterations=3
        ),
        "middleware": MiddlewareAgent(
            llm=gemini_llm,
            tools=tools,
            name="MiddlewareAgent",
            verbose=True,
            max_iterations=3
        ),
    }

    # Define a realistic task flow
    task_list = [
        {"name": "backend_task", "agent": "backend", "input": "Generate a REST API endpoint for user login in Python using FastAPI.", "priority": 1, "dependencies": []},
        {"name": "middleware_task", "agent": "middleware", "input": "Write middleware logic to validate JWT tokens for the login endpoint.", "priority": 2, "dependencies": ["backend_task"]},
        {"name": "frontend_task", "agent": "frontend", "input": "Create a React login form that calls the backend login API.", "priority": 3, "dependencies": ["middleware_task"]},
    ]

    # Run the agent flow
    flow = AgentFlow(agents, task_list, verbose=True, max_workers=2)
    results = flow.run()
    print("\nRaw results:")
    print(results)
    print("\nUser-facing summary:")
    print(flow.summarize_results(results))
