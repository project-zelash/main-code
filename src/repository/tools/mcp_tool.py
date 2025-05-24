from src.repository.tools.base_tool import BaseTool

class MCPTool(BaseTool):
    """
    Remote tool proxy using Model Control Protocol.
    """
    
    def __init__(self, client, name, description, args_schema):
        """
        Constructor for remote tool.
        
        Args:
            client: MCPClient instance for communication.
            name: String identifier for the tool.
            description: Tool purpose description visible to the LLM.
            args_schema: Dictionary defining expected parameters.
        """
        super().__init__(name, description, args_schema)
        self.client = client
    
    def run(self, **kwargs):
        """
        Forwards requests to remote tool via MCP client.
        
        Args:
            **kwargs: Arguments passed to the remote tool.
            
        Returns:
            Result from the remote tool execution.
        """
        # Implementation will forward the request to the remote tool via MCP client
        # and return the result
        return self.client.call_tool(self.name, **kwargs)