from src.repository.agent.general_agent import GeneralAgent


class DesignAgent(GeneralAgent):
    """Specialized agent for UX, visual design, and design-system planning."""

    def __init__(self, llm, tools, name="DesignAgent", verbose=False, max_iterations=5, memory_enabled=True):
        design_system_prompt = """You are a senior product design agent for autonomous software builds.
Return practical UI/UX structure, interaction states, accessibility requirements, and visual-system decisions.
When asked to generate files, return only a JSON array of objects with path and content keys."""
        super().__init__(llm, tools, design_system_prompt, name, verbose, max_iterations, memory_enabled)
