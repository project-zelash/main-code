from src.repository.agent.general_agent import GeneralAgent

class AnalysisAgent(GeneralAgent):
    """
    Specialized Manus agent for data analysis and insights.
    """
    
    def __init__(self, llm, tools, name="AnalysisAgent", verbose=False, max_iterations=5, memory_enabled=True):
        """
        Constructor for Analysis agent with specialized system prompt.
        
        Args:
            llm: Language model instance used by the agent.
            tools: List of BaseTool instances available to the agent (focused on analysis and visualization).
            name: String identifier for the agent.
            verbose: Boolean flag for detailed logging.
            max_iterations: Maximum tool calling iterations before stopping.
            memory_enabled: Boolean controlling conversation history tracking.
        """
        # Custom system prompt for analysis tasks
        analysis_system_prompt = """You are a data analysis specialist focused on interpreting information and extracting insights.
        Your goal is to process, analyze, and visualize data to uncover patterns, trends, and meaningful conclusions.
        Always provide clear explanations of your analytical methods and the significance of your findings."""
        
        super().__init__(llm, tools, analysis_system_prompt, name, verbose, max_iterations, memory_enabled)