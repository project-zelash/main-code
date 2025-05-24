from src.repository.agent.general_agent import GeneralAgent

class BackendAgent(GeneralAgent):
    """
    Specialized agent for backend development tasks.
    """
    def __init__(self, llm, tools, name="BackendAgent", verbose=False, max_iterations=5, memory_enabled=True):
        backend_system_prompt = """You are a backend development specialist.\nYour task is to implement robust, efficient, and secure backend code.\nFocus on API design, database integration, authentication, and business logic.\nProvide detailed comments and follow best practices for the chosen technology stack."""
        super().__init__(llm, tools, backend_system_prompt, name, verbose, max_iterations, memory_enabled)
