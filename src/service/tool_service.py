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
        self.config = config or {}
        self.tools = {}
        self.mcp_client = None
        self._initialize_default_tools()
    
    def _initialize_default_tools(self):
        # ...existing code...
        if 'web_search' in self.config:
            web_search_config = self.config['web_search']
            self.tools['web_search'] = WebSearch(
                search_api_key=web_search_config.get('api_key'),
                search_engine_id=web_search_config.get('engine_id')
            )
        if 'browser_use' in self.config:
            self.tools['browser_use'] = BrowserUseTool()
        if 'bash' in self.config:
            bash_config = self.config['bash']
            self.tools['bash'] = BashTool(
                allowed_commands=bash_config.get('allowed_commands'),
                disallowed_commands=bash_config.get('disallowed_commands')
            )
        if 'planning' in self.config:
            self.tools['planning'] = PlanningTool()
        if 'chart' in self.config:
            chart_config = self.config['chart']
            self.tools['chart'] = ChartTool(
                chart_script_path=chart_config.get('script_path')
            )
    
    def register_tool(self, name, tool):
        if not isinstance(tool, BaseTool):
            raise TypeError("Tool must be an instance of BaseTool")
        self.tools[name] = tool
        return tool
    
    def get_tool(self, name):
        return self.tools.get(name)
    
    def get_tools(self, names=None):
        if names is None:
            return self.tools.copy()
        return {name: self.tools[name] for name in names if name in self.tools}
    
    def connect_mcp(self, server_url="ws://localhost:8765"):
        """
        Connect to MCP server for remote tools.
        """
        try:
            self.mcp_client = MCPClient(server_url)
            print(f"[INFO] Connected to MCP server at {server_url}")
            return True
        except Exception as e:
            print(f"Failed to connect to MCP server: {e}")
            self.mcp_client = None
            return False

    def register_remote_tool(self, name, description, args_schema):
        """
        Register a remote tool via MCP.
        """
        if not self.mcp_client:
            raise ValueError("MCP client not connected")
        tool = MCPTool(self.mcp_client, name, description, args_schema)
        return self.register_tool(name, tool)
    
    def update_config(self, new_config):
        self.config.update(new_config)
        self._initialize_default_tools()
        return self.config
    
    def run_bash_command(self, command):
        bash_tool = self.get_tool('bash')
        if bash_tool:
            return bash_tool.run(command)
        raise NotImplementedError("BashTool is not configured in ToolService.")