\
import os
import subprocess
import time
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class SimpleConfigProvider:
    def __init__(self, source_dict=None):
        self.source = source_dict if source_dict is not None else os.environ

    def get(self, key, default=None):
        return self.source.get(key, default)

class BrowserAutomationServerManager:
    def __init__(self, zelash_config: Optional[Any] = None): # Modified signature
        """
        Initializes the BrowserAutomationServerManager.

        Args:
            zelash_config: (Optional) A configuration object/dict-like accessor for Zelash settings.
                           If None, os.environ will be used directly.
                           Expected keys include:
                           - ZELASH_PROJECT_ROOT (str): Absolute path to the Zelash project root.
                           - ZELASH_BROWSER_AUTOMATION_ENABLED (str: "true"/"false")
                           - ZELASH_BROWSER_AUTOMATION_SERVER_DIR (str): Path to mcp-browser-use server code (relative to project root or absolute).
                           - ZELASH_BROWSER_AUTOMATION_SERVER_HOST (str)
                           - ZELASH_BROWSER_AUTOMATION_SERVER_PORT (int)
                           - ZELASH_BROWSER_AUTOMATION_UV_PATH (str): Path to 'uv' executable.
                           - ZELASH_MCP_BROWSER_FASTAPI_APP (str): FastAPI app string, e.g., "mcp_server_browser_use.main:app" or "mcp_server_browser_use.server:app".
                           - ZELASH_BROWSER_AUTOMATION_SERVER_LOG_FILE (str, optional): Path for server's log file.
                           - ZELASH_BROWSER_AUTOMATION_LOG_LEVEL (str, optional): Logging level for the server.
                           - ZELASH_BROWSER_AUTOMATION_STARTUP_TIMEOUT (int, optional): Max time to wait for server process to be considered started.
                           - ZELASH_BROWSER_AUTOMATION_POST_LAUNCH_DELAY (int, optional): Seconds to wait after launching server before considering it started (replaces health check).
                           - And various ZELASH_MCP_... variables for pass-through configuration.
        """
        # If zelash_config is None or not a dict-like, wrap os.environ
        if not hasattr(zelash_config, 'get'):
            self.config = SimpleConfigProvider(os.environ)
            logger.info("BrowserAutomationServerManager initialized using os.environ for configuration.")
        else:
            self.config = zelash_config
            logger.info("BrowserAutomationServerManager initialized with provided configuration object.")

        self.process = None

        self.project_root = Path(self.config.get("ZELASH_PROJECT_ROOT", Path(__file__).resolve().parent.parent.parent))
        
        server_dir_config = self.config.get("ZELASH_BROWSER_AUTOMATION_SERVER_DIR", "integrations/mcp-browser-use")
        self.server_dir = Path(server_dir_config)
        if not self.server_dir.is_absolute():
            self.server_dir = (self.project_root / self.server_dir).resolve()

        self.host = self.config.get("ZELASH_BROWSER_AUTOMATION_SERVER_HOST", "127.0.0.1")
        self.port = int(self.config.get("ZELASH_BROWSER_AUTOMATION_SERVER_PORT", 8777))
        self.uv_executable = self.config.get("ZELASH_BROWSER_AUTOMATION_UV_PATH", "uv")
        self.enabled = str(self.config.get("ZELASH_BROWSER_AUTOMATION_ENABLED", "false")).lower() == "true"
        # Try mcp_server_browser_use.main:app or mcp_server_browser_use.server:app
        # The script entry point is mcp_server_browser_use.server:main, which likely runs an 'app' instance.
        self.fastapi_app_module = self.config.get("ZELASH_MCP_BROWSER_FASTAPI_APP", "mcp_server_browser_use.server:app") 
        self.post_launch_delay = int(self.config.get("ZELASH_BROWSER_AUTOMATION_POST_LAUNCH_DELAY", 10)) # seconds

    def _resolve_path_config(self, config_key, create_dirs=True):
        path_str = self.config.get(config_key)
        if not path_str:
            return None
        
        path_obj = Path(path_str)
        if not path_obj.is_absolute():
            path_obj = (self.project_root / path_obj).resolve()
        
        if create_dirs:
            # Ensure parent directory exists for files, or the dir itself if it's a directory path
            target_dir = path_obj if config_key.endswith("_DIR") or config_key.endswith("_PATH") else path_obj.parent
            try:
                target_dir.mkdir(parents=True, exist_ok=True)
            except OSError as e:
                logger.warning(f"Could not create directory {target_dir} for {config_key}: {e}")
        return str(path_obj)

    def _prepare_env(self):
        env = os.environ.copy()
        
        log_file = self._resolve_path_config("ZELASH_BROWSER_AUTOMATION_SERVER_LOG_FILE", create_dirs=True)
        if log_file:
            env["MCP_SERVER_LOG_FILE"] = log_file
        # Default to INFO if not specified, as DEBUG can be very verbose for the browser server
        env["MCP_SERVER_LOGGING_LEVEL"] = self.config.get("ZELASH_BROWSER_AUTOMATION_LOG_LEVEL", "INFO")

        mcp_vars_map = {
            "MCP_LLM_PROVIDER": "ZELASH_MCP_LLM_PROVIDER",
            "MCP_LLM_MODEL_NAME": "ZELASH_MCP_LLM_MODEL_NAME",
            "MCP_LLM_API_KEY": "ZELASH_MCP_LLM_API_KEY",
            "MCP_LLM_GOOGLE_API_KEY": "ZELASH_MCP_LLM_GOOGLE_API_KEY",
            "MCP_LLM_OPENAI_API_KEY": "ZELASH_MCP_LLM_OPENAI_API_KEY",
            "MCP_LLM_ANTHROPIC_API_KEY": "ZELASH_MCP_LLM_ANTHROPIC_API_KEY",
            # Add other LLM provider keys as needed
            "MCP_BROWSER_HEADLESS": ("ZELASH_MCP_BROWSER_HEADLESS", "true"), # Default to true
            "MCP_BROWSER_KEEP_OPEN": ("ZELASH_MCP_BROWSER_KEEP_OPEN", "true"), # Default to true
            "MCP_RESEARCH_TOOL_SAVE_DIR": "ZELASH_MCP_RESEARCH_TOOL_SAVE_DIR",
            "MCP_AGENT_TOOL_HISTORY_PATH": "ZELASH_MCP_AGENT_TOOL_HISTORY_PATH",
            "MCP_PATHS_DOWNLOADS": "ZELASH_MCP_PATHS_DOWNLOADS",
        }

        for mcp_key, zelash_key_info in mcp_vars_map.items():
            default_value = None
            if isinstance(zelash_key_info, tuple):
                zelash_key, default_value = zelash_key_info
            else:
                zelash_key = zelash_key_info

            value = self.config.get(zelash_key)
            if value is not None:
                if "_DIR" in mcp_key or "_PATH" in mcp_key: # These are path configurations
                    resolved_path = self._resolve_path_config(zelash_key, create_dirs=True)
                    if resolved_path:
                         env[mcp_key] = resolved_path
                elif isinstance(value, bool): # Handle boolean to string conversion
                    env[mcp_key] = str(value).lower()
                else:
                    env[mcp_key] = str(value)
            elif default_value is not None: # Apply default if Zelash config not set
                if "_DIR" in mcp_key or "_PATH" in mcp_key: # These are path configurations
                     # This case might be tricky if default_value is a relative path string
                     # For simplicity, assume default_value for paths are not used or are absolute
                     pass # Or handle default path resolution if necessary
                else:
                    env[mcp_key] = str(default_value).lower() if isinstance(default_value, bool) else str(default_value)
        return env

    def start_server(self):
        if not self.enabled:
            logger.info("Browser Automation Server is disabled in configuration.")
            return False
            
        if self.is_running():
            logger.info("Browser Automation Server is already running.")
            return True

        if not self.server_dir.is_dir() or not (self.server_dir / "pyproject.toml").exists():
             logger.error(f"mcp-browser-use server directory not found or invalid: {self.server_dir}")
             logger.error("Ensure ZELASH_BROWSER_AUTOMATION_SERVER_DIR is set correctly and points to a valid mcp-browser-use project.")
             return False

        if not self.fastapi_app_module:
            logger.error("ZELASH_MCP_BROWSER_FASTAPI_APP is not configured. Cannot determine FastAPI app for Uvicorn.")
            return False

        env = self._prepare_env()
        
        # Command to run the server using 'uv run uvicorn ...'
        # This assumes 'mcp_server_browser_use' is installed in the environment 'uv' manages for self.server_dir
        # or that 'uv run python -m uvicorn ...' can find it if the CWD is server_dir.
        # The mcp-browser-use server is designed to be run as a module.
        command = [
            self.uv_executable, "run", "python", "-m", "uvicorn",
            self.fastapi_app_module,
            "--host", self.host,
            "--port", str(self.port)
            # Add --reload if desired for development, from config
        ]
        if str(self.config.get("ZELASH_BROWSER_AUTOMATION_SERVER_RELOAD", "false")).lower() == "true":
            command.append("--reload")

        logger.info(f"Starting Browser Automation Server: {' '.join(command)}")
        logger.info(f"Server CWD: {self.server_dir}")
        # Avoid logging sensitive keys directly, show only a few safe ones
        log_env_subset = {k: v for k, v in env.items() if k.startswith("MCP_") and "API_KEY" not in k}
        logger.info(f"Server ENV (subset): {log_env_subset}")
        
        try:
            self.process = subprocess.Popen(
                command,
                cwd=self.server_dir,
                env=env,
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE
                # Consider redirecting stdout/stderr to files if ZELASH_BROWSER_AUTOMATION_SERVER_LOG_FILE is not used by the app itself
                # or if more detailed startup logs are needed directly from Zelash.
            )
        except FileNotFoundError:
            logger.error(f"Failed to start server: '{self.uv_executable}' not found. Ensure it's in PATH or ZELASH_BROWSER_AUTOMATION_UV_PATH is correct.")
            self.process = None
            return False
        except Exception as e:
            logger.error(f"Failed to start server: {e}", exc_info=True)
            self.process = None
            return False

        # Simplified startup check: Wait for a configured delay then check process status.
        logger.info(f"Waiting {self.post_launch_delay} seconds for server to initialize...")
        time.sleep(self.post_launch_delay)

        if self.is_process_running():
            logger.info(f"Browser Automation Server process is running after delay. Assuming successful start at {self.get_server_url()}.")
            # Optionally, could log snippets of stdout/stderr here if available without blocking
            # For example, by reading non-blocking from self.process.stdout
            return True
        else:
            logger.error("Server process terminated unexpectedly during or shortly after startup.")
            stdout, stderr = self.process.communicate() if self.process else (None, None) # Capture remaining output
            logger.error(f"Server stdout: {stdout.decode(errors='ignore') if stdout else 'N/A'}")
            logger.error(f"Server stderr: {stderr.decode(errors='ignore') if stderr else 'N/A'}")
            self.process = None # Ensure process handle is cleared
            return False


    def is_process_running(self):
        return self.process is not None and self.process.poll() is None

    def is_running(self):
        # Simplified check: only verifies if the process is alive.
        # A more robust check might involve a lightweight MCP ping if available and desired.
        return self.is_process_running()

    def stop_server(self):
        if self.process and self.is_process_running(): # Check if process exists and is running
            logger.info("Stopping Browser Automation Server...")
            self.process.terminate()
            try:
                stdout, stderr = self.process.communicate(timeout=10) # Wait for graceful termination
                logger.info("Browser Automation Server terminated.")
                if stdout: logger.debug(f"Server stdout on shutdown: {stdout.decode(errors='ignore')}")
                if stderr: logger.debug(f"Server stderr on shutdown: {stderr.decode(errors='ignore')}")
            except subprocess.TimeoutExpired:
                logger.warning("Server did not terminate gracefully, killing.")
                self.process.kill()
                stdout, stderr = self.process.communicate() # Wait for kill
                logger.info("Browser Automation Server killed.")
                if stdout: logger.debug(f"Server stdout on kill: {stdout.decode(errors='ignore')}")
                if stderr: logger.debug(f"Server stderr on kill: {stderr.decode(errors='ignore')}")
            except Exception as e:
                logger.error(f"Error during server shutdown: {e}", exc_info=True)
            self.process = None
        elif self.process and not self.is_process_running(): # Process existed but already stopped
            logger.info("Browser Automation Server process was found but already stopped.")
            self.process = None
        else: # No process or already cleared
            logger.info("Browser Automation Server is not running or process handle already cleared.")
            
    def get_server_url(self):
        return f"http://{self.host}:{self.port}"

    def get_mcp_api_key_for_client(self):
        # This is for the CLIENT to use if the server is protected by an API key.
        # mcp-browser-use server itself doesn't seem to have an incoming API key auth layer by default.
        return self.config.get("ZELASH_MCP_SERVER_API_KEY_FOR_CLIENT")
