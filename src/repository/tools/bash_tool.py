from src.repository.tools.base_tool import BaseTool

class BashTool(BaseTool):
    """
    Tool for executing shell commands.
    """
    
    def __init__(self, allowed_commands=None, disallowed_commands=None):
        """
        Constructor with security settings.
        
        Args:
            allowed_commands: List of allowed commands or patterns.
            disallowed_commands: List of blocked commands or patterns.
        """
        name = "bash"
        description = "Execute shell commands and return their output"
        args_schema = {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "Shell command string to execute"
                }
            },
            "required": ["command"]
        }
        
        super().__init__(name, description, args_schema)
        self.allowed_commands = allowed_commands or []
        self.disallowed_commands = disallowed_commands or ["rm -rf", "sudo", "shutdown", "reboot"]
    
    def run(self, command):
        """
        Executes shell command and returns output.
        
        Args:
            command: Shell command string to execute.
            
        Returns:
            Output from the command execution.
        """
        # Implementation will check if command is allowed, execute it safely, and return output
        if not self._is_command_allowed(command):
            return {"error": "Command not allowed for security reasons."}
        pass
    
    def _is_command_allowed(self, command):
        """
        Checks command against security rules.
        
        Args:
            command: Shell command string to check.
            
        Returns:
            Boolean indicating if command is allowed.
        """
        # Implementation will check command against allowed and disallowed patterns
        pass