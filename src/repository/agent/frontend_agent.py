from src.repository.agent.general_agent import GeneralAgent

class FrontendAgent(GeneralAgent):
    """
    Specialized agent for frontend development tasks.
    """
    def __init__(self, llm, tools, name="FrontendAgent", verbose=False, max_iterations=5, memory_enabled=True):
        frontend_system_prompt = """You are a frontend development and UI/UX design specialist.
Your task is to implement responsive, accessible, and interactive user interfaces with excellent design principles.
Focus on:
- Component architecture and state management
- User experience and interface design
- Visual design including layout, colors, typography, and styling
- Accessibility and responsive design
- Modern frontend frameworks and design systems
Provide detailed comments and follow best practices for both development and design aspects of the chosen technology stack."""
        super().__init__(llm, tools, frontend_system_prompt, name, verbose, max_iterations, memory_enabled)
