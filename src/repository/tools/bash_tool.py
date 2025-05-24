from src.repository.tools.base_tool import BaseTool
import subprocess
import os
import shlex
import logging

logger = logging.getLogger(__name__)

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
        # Default security: block dangerous commands
        self.disallowed_commands = disallowed_commands or [
            "rm -rf", "sudo", "shutdown", "reboot", "format", "mkfs", 
            "dd if=", ":(){ :|:& };:", "chmod 777", "chown", "passwd",
            "userdel", "useradd", "su -", "curl", "wget"
        ]
    
    def run(self, command):
        """
        Executes shell command and returns output.
        
        Args:
            command: Shell command string to execute.
            
        Returns:
            Output from the command execution.
        """
        # Security check
        if not self._is_command_allowed(command):
            return {
                "error": f"Command not allowed for security reasons: {command}",
                "stdout": "",
                "stderr": "",
                "return_code": -1
            }
        
        try:
            logger.info(f"🖥️ Executing command: {command}")
            
            # Use shell=True for Windows compatibility, but be careful with input
            # On Windows, we need shell=True to execute commands properly
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30,  # 30 second timeout
                cwd=os.getcwd()
            )
            
            output = {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode,
                "command": command
            }
            
            if result.returncode == 0:
                logger.info(f"✅ Command completed successfully")
                return f"Command executed successfully:\n{result.stdout}" if result.stdout else "Command completed with no output"
            else:
                logger.warning(f"⚠️ Command failed with return code {result.returncode}")
                error_msg = f"Command failed (exit code {result.returncode})"
                if result.stderr:
                    error_msg += f"\nError: {result.stderr}"
                if result.stdout:
                    error_msg += f"\nOutput: {result.stdout}"
                return error_msg
            
        except subprocess.TimeoutExpired:
            error_msg = f"Command timed out after 30 seconds: {command}"
            logger.error(f"⏰ {error_msg}")
            return error_msg
        except subprocess.CalledProcessError as e:
            error_msg = f"Command failed: {e}"
            logger.error(f"🚨 {error_msg}")
            return error_msg
        except Exception as e:
            error_msg = f"Error executing command: {str(e)}"
            logger.error(f"🚨 {error_msg}")
            return error_msg
    
    def _is_command_allowed(self, command):
        """
        Checks command against security rules.
        
        Args:
            command: Shell command string to check.
            
        Returns:
            Boolean indicating if command is allowed.
        """
        command_lower = command.lower().strip()
        
        # If allowed_commands is specified, check if command starts with any allowed pattern
        if self.allowed_commands:
            for allowed in self.allowed_commands:
                if command_lower.startswith(allowed.lower()):
                    return True
            return False
        
        # Check against disallowed patterns
        for disallowed in self.disallowed_commands:
            if disallowed.lower() in command_lower:
                logger.warning(f"🚫 Blocked command containing '{disallowed}': {command}")
                return False
        
        # Updated security checks - allow some safe patterns
        safe_patterns = [
            "$(pwd)", "$(date)", "$(whoami)", "%cd%"  # Safe command substitutions
        ]
        
        # Check if command contains safe patterns first
        for safe_pattern in safe_patterns:
            if safe_pattern in command:
                return True
        
        # Then check suspicious patterns (excluding the safe ones)
        suspicious_patterns = [
            "&gt;", "eval", "exec", "import os", "import subprocess",
            "__import__", "open(", "file(", "input(", "raw_input("
        ]
        
        for pattern in suspicious_patterns:
            if pattern in command_lower:
                logger.warning(f"🚫 Blocked command with suspicious pattern '{pattern}': {command}")
                return False
        
        return True