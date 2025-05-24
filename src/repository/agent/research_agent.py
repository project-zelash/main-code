from src.repository.agent.general_agent import GeneralAgent

class ResearchAgent(GeneralAgent):
    """
    Specialized Manus agent focused on information gathering.
    """
    
    def __init__(self, llm, tools, name="ResearchAgent", verbose=False, max_iterations=5, memory_enabled=True):
        """
        Constructor for Research agent with specialized system prompt.
        
        Args:
            llm: Language model instance used by the agent.
            tools: List of BaseTool instances available to the agent (focused on information gathering).
            name: String identifier for the agent.
            verbose: Boolean flag for detailed logging.
            max_iterations: Maximum tool calling iterations before stopping.
            memory_enabled: Boolean controlling conversation history tracking.
        """
        # Custom system prompt for research tasks
        research_system_prompt = """You are a research specialist focused on gathering accurate information. 
        Your goal is to find relevant, reliable information from various sources including web searches, 
        browsing, and processing data. Always cite your sources and provide context for your findings."""
        
        super().__init__(llm, tools, research_system_prompt, name, verbose, max_iterations, memory_enabled)