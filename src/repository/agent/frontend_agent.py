from src.repository.agent.general_agent import GeneralAgent

class FrontendAgent(GeneralAgent):
    """
    Specialized agent for frontend development tasks.
    """
    def __init__(self, llm, tools, name="FrontendAgent", verbose=False, max_iterations=5, memory_enabled=True):
        frontend_system_prompt = """You are a frontend development specialist.\nYour task is to implement responsive, accessible, and interactive user interfaces.\nFocus on component architecture, state management, and user experience.\nProvide detailed comments and follow best practices for the chosen technology stack."""
        super().__init__(llm, tools, frontend_system_prompt, name, verbose, max_iterations, memory_enabled)
