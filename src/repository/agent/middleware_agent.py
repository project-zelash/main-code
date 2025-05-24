from src.repository.agent.general_agent import GeneralAgent

class MiddlewareAgent(GeneralAgent):
    """
    Specialized agent for middleware development tasks.
    """
    def __init__(self, llm, tools, name="MiddlewareAgent", verbose=False, max_iterations=5, memory_enabled=True):
        middleware_system_prompt = """You are a middleware development specialist.\nYour task is to implement communication layers, integrations, and data processing systems.\nFocus on robustness, performance, and scalability.\nProvide detailed comments and follow best practices for the chosen technology stack."""
        super().__init__(llm, tools, middleware_system_prompt, name, verbose, max_iterations, memory_enabled)
