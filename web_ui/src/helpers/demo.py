#!/usr/bin/env python3
"""
Demo Script for Browser Agent Helper Functions

This script demonstrates how to use the helper functions to configure the Google Gemini model
and interact with the Browser Agent through a simple API.
"""

import os
import sys
import json
import logging
from typing import Dict, Any

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("demo")

# Add the project root to the path if needed
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import helper functions
from src.helpers.model_config import (
    set_default_model, 
    get_current_model_config,
    update_env_with_model_config
)

def print_colored(text: str, color: str = 'white') -> None:
    """Print colored text to the console."""
    colors = {
        'red': '\033[91m',
        'green': '\033[92m',
        'yellow': '\033[93m',
        'blue': '\033[94m',
        'magenta': '\033[95m',
        'cyan': '\033[96m',
        'white': '\033[97m',
        'reset': '\033[0m'
    }
    print(f"{colors.get(color, colors['white'])}{text}{colors['reset']}")

def format_json(obj: Any) -> str:
    """Format an object as a JSON string."""
    return json.dumps(obj, indent=2)

def demo_model_config():
    """Demonstrate the model configuration functions."""
    print_colored("===== DEMONSTRATING MODEL CONFIGURATION =====", "magenta")
    
    # 1. Show default model config
    print_colored("Current default model configuration:", "cyan")
    config = get_current_model_config()
    print_colored(format_json(config), "blue")
    
    # 2. Set Google Gemini as the default model
    print_colored("\nSetting Google Gemini 2.0 Flash as the default model...", "cyan")
    new_config = set_default_model(
        provider="google",
        model_name="gemini-2.0-flash",
        temperature=0.7,
        use_vision=True
    )
    print_colored("New default model configuration:", "cyan")
    print_colored(format_json(new_config), "green")
    
    # 3. Update the .env file with the new configuration
    print_colored("\nUpdating .env file with the new configuration...", "cyan")
    success = update_env_with_model_config(new_config)
    if success:
        print_colored("✓ Successfully updated .env file", "green")
    else:
        print_colored("✗ Failed to update .env file", "red")
    
    # 4. Show that the configuration persists
    print_colored("\nVerifying that the configuration persists...", "cyan")
    current_config = get_current_model_config()
    print_colored(format_json(current_config), "blue")
    
    print_colored("\n✓ Model configuration demo completed", "green")

def explain_agent_usage():
    """Explain how to use the agent functions."""
    print_colored("===== HOW TO USE THE BROWSER AGENT =====", "magenta")
    
    print_colored("\nTo run a browser agent task with Google Gemini 2.0 Flash:", "cyan")
    
    code_example = """
# Import the helper functions
from src.helpers import run_task, retrieve_logs, get_agent_status

# Run a task with Google Gemini 2.0 Flash as the default model
task_id = run_task(
    prompt="Go to www.google.com and search for 'best Andhra food restaurants in Bangalore'",
    llm_config={
        "provider": "google",
        "model_name": "gemini-2.0-flash",
        "temperature": 0.7
    }
)

# Check the status of the task
status = get_agent_status(task_id)
print(f"Task status: {status}")

# Retrieve the logs once the task is complete
if status.get("completed", False):
    logs = retrieve_logs(task_id)
    print(f"Found {len(logs)} log entries")
    
    # Get the last log entry (the result)
    if logs:
        last_entry = logs[-1]
        print(f"Final result: {last_entry}")
"""
    print_colored(code_example, "yellow")
    
    print_colored("\nNote on running the actual browser:", "cyan")
    print_colored("""
The Browser Agent requires a properly configured browser environment with the necessary dependencies.
To run the actual browser agent, you need:

1. Required dependencies (browser-use package, playwright)
2. A compatible browser installation
3. API keys for the LLM provider (Google API key for Gemini)

For simplicity, this demo only shows how to configure the model settings and 
provides the API to use the agent. To run the full browser-based tasks, use:

./browser_agent_cli.py run "Your task prompt here"
""", "white")

def main():
    """Main demo function."""
    print_colored("Starting Browser Agent Helper Functions Demo...", "blue")
    
    # Demo the model configuration
    demo_model_config()
    
    # Explain how to use the agent
    explain_agent_usage()
    
    print_colored("\nDemo completed successfully!", "green")
    print_colored("To use the Browser Agent with Google Gemini 2.0 Flash as the default model:", "cyan")
    print_colored("1. Run tasks: ./browser_agent_cli.py run \"Your task prompt\"", "white")
    print_colored("2. Check status: ./browser_agent_cli.py status", "white")
    print_colored("3. Get logs: ./browser_agent_cli.py logs --save", "white")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print_colored("\nDemo interrupted by user", "yellow")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Error in demo: {e}", exc_info=True)
        print_colored(f"Error: {e}", "red")
        sys.exit(1)
