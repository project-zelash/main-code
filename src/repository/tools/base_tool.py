class BaseTool:
    """
    Abstract base class for all tools usable by agents.
    """
    
    def __init__(self, name, description, args_schema):
        """
        Initialize the tool with name, description, and schema.
        
        Args:
            name: String identifier for the tool.
            description: Tool purpose description visible to the LLM.
            args_schema: Dictionary defining expected parameters.
        """
        self.name = name
        self.description = description
        self.args_schema = args_schema
    
    def run(self, **kwargs):
        """
        Abstract method that executes the tool functionality.
        
        Args:
            **kwargs: Arguments passed to the tool.
            
        Returns:
            Result of the tool execution.
        """
        raise NotImplementedError("Subclasses must implement this method")
    
    def to_dict(self):
        """
        Converts tool definition to LLM-compatible format.
        
        Returns:
            Dictionary representation of the tool for LLM API.
        """
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.args_schema
        }