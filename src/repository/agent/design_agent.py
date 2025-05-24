from src.repository.agent.general_agent import GeneralAgent

class DesignAgent(GeneralAgent):
    """
    Specialized agent for UI/UX design tasks.
    """
    def __init__(self, llm, tools, name="DesignAgent", verbose=False, max_iterations=5, memory_enabled=True):
        design_system_prompt = """You are a UI/UX design specialist.\nYour task is to create visually appealing and user-friendly interfaces.\nFocus on layout, colors, typography, and component design.\nProvide detailed comments and follow best practices for the chosen design system."""
        super().__init__(llm, tools, design_system_prompt, name, verbose, max_iterations, memory_enabled)
