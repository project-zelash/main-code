"""
Browser-Use MCP Helper Functions

This module provides helper functions to use the browser-use MCP server
for browser automation tasks, similar to the previous helper functions
but with the advantages of the MCP implementation.
"""

import os
import sys
import json
import subprocess
import asyncio
import logging
from typing import Dict, Any, List, Optional, Union
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Add the MCP browser-use to the Python path
REPO_ROOT = Path(__file__).parents[3]  # main-code directory
MCP_PATH = REPO_ROOT / "integrations" / "mcp-browser-use"
BROWSER_USE_PATH = REPO_ROOT / "integrations" / "browser-use"

sys.path.append(str(MCP_PATH))
sys.path.append(str(BROWSER_USE_PATH))

# Store task state
_TASK_STATE = {
    "current_task": None,
    "current_process": None,
    "logs": [],
}

def run_browser_task(
    task: str, 
    headless: bool = False,
    use_vision: bool = True,
) -> str:
    """
    Run a browser task using the MCP browser-use implementation.
    
    Args:
        task: The natural language task to perform
        headless: Whether to run the browser in headless mode
        use_vision: Whether to enable vision capabilities
        
    Returns:
        The task ID (can be used to reference this task later)
    """
    # Clear previous logs
    _TASK_STATE["logs"] = []
    
    # Add initial task to logs
    _TASK_STATE["logs"].append({
        "role": "system",
        "content": f"Starting task: {task}"
    })
    
    # Set environment variables
    env = os.environ.copy()
    env["MCP_BROWSER_HEADLESS"] = str(headless).lower()
    env["MCP_AGENT_TOOL_USE_VISION"] = str(use_vision).lower()
    
    # Set Google Gemini API key directly
    env["MCP_LLM_GOOGLE_API_KEY"] = "AIzaSyDHT_4-rbBQkDD2igDxnxmu-j5LfH1MJ8I"
    env["MCP_LLM_PROVIDER"] = "google"
    env["MCP_LLM_MODEL_NAME"] = "gemini-2.0-flash"
    env["MCP_LLM_TEMPERATURE"] = "0.4"
    
    # Configure browser settings
    env["MCP_BROWSER_HEADLESS"] = str(headless).lower()
    env["MCP_BROWSER_WINDOW_WIDTH"] = "1280"
    env["MCP_BROWSER_WINDOW_HEIGHT"] = "720"
    env["MCP_BROWSER_DISABLE_SECURITY"] = "false"
    
    # Configure agent tool settings
    env["MCP_AGENT_TOOL_USE_VISION"] = str(use_vision).lower()
    env["MCP_AGENT_TOOL_MAX_STEPS"] = "100"
    env["MCP_AGENT_TOOL_MAX_ACTIONS_PER_STEP"] = "5"
    env["MCP_AGENT_TOOL_TOOL_CALLING_METHOD"] = "auto"
    
    # Configure paths
    deep_research_dir = REPO_ROOT / "tmp" / "deep_research"
    deep_research_dir.mkdir(parents=True, exist_ok=True)
    env["MCP_RESEARCH_TOOL_SAVE_DIR"] = str(deep_research_dir)
    
    # Configure server settings
    env["MCP_SERVER_LOGGING_LEVEL"] = "INFO"
    env["MCP_SERVER_ANONYMIZED_TELEMETRY"] = "true"
    
    # Construct the command
    cmd = [
        "python", "-m", "mcp_server_browser_use.cli", 
        "run-browser-agent", task
    ]
    
    # Run the command
    try:
        # Create a unique task ID
        import uuid
        task_id = str(uuid.uuid4())
        
        # Run the command asynchronously
        process = subprocess.Popen(
            cmd,
            cwd=str(MCP_PATH / "src"),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        
        # Store the task and process
        _TASK_STATE["current_task"] = task_id
        _TASK_STATE["current_process"] = process
        
        # Add log entry
        _TASK_STATE["logs"].append({
            "role": "system",
            "content": f"Task started with ID: {task_id}"
        })
        
        return task_id
        
    except Exception as e:
        logger.error(f"Error running browser task: {e}")
        # Add error to logs
        _TASK_STATE["logs"].append({
            "role": "system",
            "content": f"Error: {str(e)}"
        })
        return f"Error: {str(e)}"


def run_deep_research(
    research_task: str,
    max_parallel_browsers: int = 3,
    save_dir: str = None,
) -> str:
    """
    Run a deep research task using the MCP browser-use implementation.
    
    Args:
        research_task: The research topic or question
        max_parallel_browsers: Maximum number of parallel browsers to use
        save_dir: Directory to save research output
        
    Returns:
        The task ID (can be used to reference this task later)
    """
    # Clear previous logs
    _TASK_STATE["logs"] = []
    
    # Add initial task to logs
    _TASK_STATE["logs"].append({
        "role": "system",
        "content": f"Starting research: {research_task}"
    })
    
    # Set environment variables
    env = os.environ.copy()
    env["MCP_RESEARCH_TOOL_MAX_PARALLEL_BROWSERS"] = str(max_parallel_browsers)
    
    if save_dir:
        save_path = Path(save_dir)
        save_path.mkdir(parents=True, exist_ok=True)
        env["MCP_RESEARCH_TOOL_SAVE_DIR"] = str(save_path)
    else:
        # Create a default save directory
        save_path = REPO_ROOT / "tmp" / "deep_research"
        save_path.mkdir(parents=True, exist_ok=True)
        env["MCP_RESEARCH_TOOL_SAVE_DIR"] = str(save_path)
    
    # Set Google Gemini API key directly
    env["MCP_LLM_GOOGLE_API_KEY"] = "AIzaSyDHT_4-rbBQkDD2igDxnxmu-j5LfH1MJ8I"
    env["MCP_LLM_PROVIDER"] = "google"
    env["MCP_LLM_MODEL_NAME"] = "gemini-2.0-flash"
    env["MCP_LLM_TEMPERATURE"] = "0.4"
    
    # Configure browser settings
    env["MCP_BROWSER_HEADLESS"] = "false"
    env["MCP_BROWSER_WINDOW_WIDTH"] = "1280"
    env["MCP_BROWSER_WINDOW_HEIGHT"] = "720"
    env["MCP_BROWSER_DISABLE_SECURITY"] = "false"
    
    # Configure agent tool settings
    env["MCP_AGENT_TOOL_USE_VISION"] = "true"
    env["MCP_AGENT_TOOL_MAX_STEPS"] = "100"
    env["MCP_AGENT_TOOL_MAX_ACTIONS_PER_STEP"] = "5"
    env["MCP_AGENT_TOOL_TOOL_CALLING_METHOD"] = "auto"
    
    # Configure server settings
    env["MCP_SERVER_LOGGING_LEVEL"] = "INFO"
    env["MCP_SERVER_ANONYMIZED_TELEMETRY"] = "true"
    
    # Construct the command
    cmd = [
        "python", "-m", "mcp_server_browser_use.cli", 
        "run-deep-research", research_task,
        "--max-parallel-browsers", str(max_parallel_browsers)
    ]
    
    # Run the command
    try:
        # Create a unique task ID
        import uuid
        task_id = str(uuid.uuid4())
        
        # Run the command asynchronously
        process = subprocess.Popen(
            cmd,
            cwd=str(MCP_PATH / "src"),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        
        # Store the task and process
        _TASK_STATE["current_task"] = task_id
        _TASK_STATE["current_process"] = process
        
        # Add log entry
        _TASK_STATE["logs"].append({
            "role": "system",
            "content": f"Research task started with ID: {task_id}"
        })
        
        return task_id
        
    except Exception as e:
        logger.error(f"Error running research task: {e}")
        # Add error to logs
        _TASK_STATE["logs"].append({
            "role": "system",
            "content": f"Error: {str(e)}"
        })
        return f"Error: {str(e)}"


def stop_browser_task() -> bool:
    """
    Stop the currently running browser task.
    
    Returns:
        True if the task was stopped successfully, False otherwise
    """
    if not _TASK_STATE["current_process"]:
        logger.warning("No browser task is running.")
        return False
    
    try:
        # Terminate the process
        _TASK_STATE["current_process"].terminate()
        
        # Give it a moment to clean up
        import time
        time.sleep(1)
        
        # Add log entry
        _TASK_STATE["logs"].append({
            "role": "system",
            "content": "Task stopped by user"
        })
        
        return True
    except Exception as e:
        logger.error(f"Error stopping browser task: {e}")
        # Add error to logs
        _TASK_STATE["logs"].append({
            "role": "system",
            "content": f"Error stopping task: {str(e)}"
        })
        return False


def get_browser_logs() -> List[Dict[str, str]]:
    """
    Get the logs from the browser task.
    
    Returns:
        A list of log entries
    """
    # If a process is running, try to capture its current output
    if _TASK_STATE["current_process"]:
        try:
            # Check if there's any output to read
            if _TASK_STATE["current_process"].stdout:
                # Read any available output without blocking
                import select
                if select.select([_TASK_STATE["current_process"].stdout], [], [], 0)[0]:
                    output = _TASK_STATE["current_process"].stdout.read()
                    if output:
                        _TASK_STATE["logs"].append({
                            "role": "system",
                            "content": output
                        })
        except Exception as e:
            logger.error(f"Error reading process output: {e}")
    
    return _TASK_STATE["logs"]


if __name__ == "__main__":
    # Example usage
    task_id = run_browser_task("Go to google.com and search for 'browser-use MCP'")
    print(f"Task started with ID: {task_id}")
    
    # Wait a bit
    import time
    time.sleep(30)
    
    # Stop the task
    stop_browser_task()
    
    # Get the logs
    logs = get_browser_logs()
    print(f"Got {len(logs)} log entries")
