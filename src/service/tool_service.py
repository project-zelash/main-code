from src.repository.tools.base_tool import BaseTool
from src.repository.tools.web_search import WebSearch
from src.repository.tools.browser_use import BrowserUseTool
from src.repository.tools.bash_tool import BashTool
from src.repository.tools.planning_tool import PlanningTool
from src.repository.tools.chart_tool import ChartTool
from src.repository.tools.mcp_tool import MCPTool
from src.repository.mcp.mcp_client import MCPClient

class ToolService:
    """
    Service for managing tool instances and configurations.
    """
    
    def __init__(self, config=None):
        """
        Initialize the tool service.
        
        Args:
            config: Configuration for tool settings.
        """
        self.config = config or {}
        self.tools = {}
        self.mcp_client = None
        self._initialize_default_tools()
    
    def _initialize_default_tools(self):
        """
        Initialize default tools based on configuration.
        """
        # Web Search
        if 'web_search' in self.config:
            web_search_config = self.config['web_search']
            self.tools['web_search'] = WebSearch(
                search_api_key=web_search_config.get('api_key'),
                search_engine_id=web_search_config.get('engine_id')
            )
        
        # Browser Use
        if 'browser_use' in self.config:
            self.tools['browser_use'] = BrowserUseTool()
        
        # Bash Tool
        if 'bash' in self.config:
            bash_config = self.config['bash']
            self.tools['bash'] = BashTool(
                allowed_commands=bash_config.get('allowed_commands'),
                disallowed_commands=bash_config.get('disallowed_commands')
            )
        
        # Planning Tool
        if 'planning' in self.config:
            self.tools['planning'] = PlanningTool()
        
        # Chart Tool
        if 'chart' in self.config:
            chart_config = self.config['chart']
            self.tools['chart'] = ChartTool(
                chart_script_path=chart_config.get('script_path')
            )
    
    def register_tool(self, name, tool):
        """
        Register a new tool instance.
        
        Args:
            name: Tool name.
            tool: Tool instance.
            
        Returns:
            The registered tool.
        """
        if not isinstance(tool, BaseTool):
            raise TypeError("Tool must be an instance of BaseTool")
            
        self.tools[name] = tool
        return tool
    
    def get_tool(self, name):
        """
        Get a tool by name.
        
        Args:
            name: Tool name.
            
        Returns:
            Tool instance or None if not found.
        """
        return self.tools.get(name)
    
    def get_tools(self, names=None):
        """
        Get multiple tools by name.
        
        Args:
            names: List of tool names. If None, returns all tools.
            
        Returns:
            Dictionary of tool instances.
        """
        if names is None:
            return self.tools.copy()
            
        return {name: self.tools[name] for name in names if name in self.tools}
    
    def connect_mcp(self, server_url):
        """
        Connect to MCP server for remote tools.
        
        Args:
            server_url: MCP server URL.
            
        Returns:
            Success status.
        """
        try:
            self.mcp_client = MCPClient(server_url)
            # This would be async in actual implementation
            # await self.mcp_client.connect()
            return True
        except Exception as e:
            print(f"Failed to connect to MCP server: {e}")
            return False
    
    def register_remote_tool(self, name, description, args_schema):
        """
        Register a remote tool via MCP.
        
        Args:
            name: Tool name.
            description: Tool description.
            args_schema: Tool arguments schema.
            
        Returns:
            The registered remote tool.
        """
        if not self.mcp_client:
            raise ValueError("MCP client not connected")
            
        tool = MCPTool(self.mcp_client, name, description, args_schema)
        return self.register_tool(name, tool)
    
    def update_config(self, new_config):
        """
        Update tool configurations.
        
        Args:
            new_config: New configuration to merge with existing.
            
        Returns:
            Updated configuration.
        """
        self.config.update(new_config)
        self._initialize_default_tools()
        return self.config