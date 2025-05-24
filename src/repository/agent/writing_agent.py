from src.repository.agent.general_agent import GeneralAgent

class WritingAgent(GeneralAgent):
    """
    Specialized Manus agent for content generation.
    """
    
    def __init__(self, llm, tools, name="WritingAgent", verbose=False, max_iterations=5, memory_enabled=True):
        """
        Constructor for Writing agent with specialized system prompt.
        
        Args:
            llm: Language model instance used by the agent.
            tools: List of BaseTool instances available to the agent (focused on text refinement).
            name: String identifier for the agent.
            verbose: Boolean flag for detailed logging.
            max_iterations: Maximum tool calling iterations before stopping.
            memory_enabled: Boolean controlling conversation history tracking.
        """
        # Custom system prompt for writing tasks
        writing_system_prompt = """You are a writing specialist focused on generating high-quality content.
        Your goal is to create clear, engaging, and well-structured text tailored to specific audiences and purposes.
        Always consider tone, style, and format appropriate to the content type and intended reader."""
        
        super().__init__(llm, tools, writing_system_prompt, name, verbose, max_iterations, memory_enabled)