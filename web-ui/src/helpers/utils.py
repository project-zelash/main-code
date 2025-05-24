"""
Utility functions and examples for the Browser AI Agent

This module provides examples and utility functions to demonstrate how to use 
the helper functions to control the browser agent.
"""

import asyncio
import argparse
import json
import logging
import os
import sys
from typing import Dict, Any, List, Optional

from .agent_control import (
    run_task,
    stop_agent,
    pause_resume_agent,
    get_agent_status,
    retrieve_logs,
    save_logs_to_file
)
from .model_config import (
    set_default_model,
    get_current_model_config,
    ensure_default_google_model,
    update_env_with_model_config
)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


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


def run_example_task() -> None:
    """Run an example task with the default Google Gemini model."""
    print_colored("Running example task with Google Gemini 2.0 Flash...", "cyan")
    
    # First, set the default model to Google Gemini 2.0 Flash
    config = set_default_model()
    print_colored(f"Using model config: {format_json(config)}", "blue")
    
    # Run a simple task
    task_prompt = "Search for 'latest AI news' and summarize the top 3 results"
    print_colored(f"Task prompt: {task_prompt}", "white")
    
    # Run the task
    task_id = run_task(prompt=task_prompt)
    print_colored(f"Task started with ID: {task_id}", "green")
    
    # Monitor the task status
    print_colored("Task is running. Press Ctrl+C to stop.", "yellow")
    try:
        while True:
            status = get_agent_status(task_id)
            if status.get("completed", False):
                print_colored("Task completed!", "green")
                break
            
            print_colored(f"Status: {format_json(status)}", "blue")
            print_colored("Steps taken: " + str(status.get("steps_taken", 0)), "white")
            
            # Wait before checking again
            asyncio.get_event_loop().run_until_complete(asyncio.sleep(5))
    
    except KeyboardInterrupt:
        print_colored("\nStopping task...", "yellow")
        stop_agent(task_id)
    
    # Get and save the logs
    logs = retrieve_logs(task_id)
    log_file = save_logs_to_file(task_id)
    print_colored(f"Logs saved to: {log_file}", "green")


def run_task_from_prompt(prompt: str) -> str:
    """
    Run a task from a prompt using the default Google Gemini model.
    
    Args:
        prompt: Task prompt
        
    Returns:
        Task ID
    """
    # Ensure we're using Google Gemini as default
    config = ensure_default_google_model()
    
    # Run the task
    task_id = run_task(prompt=prompt)
    
    return task_id


def main() -> None:
    """Command-line interface for controlling the browser agent."""
    parser = argparse.ArgumentParser(description="Browser AI Agent Helper Utilities")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Run task command
    run_parser = subparsers.add_parser("run", help="Run a browser agent task")
    run_parser.add_argument("prompt", help="Task prompt")
    
    # Stop task command
    stop_parser = subparsers.add_parser("stop", help="Stop a browser agent task")
    stop_parser.add_argument("--task-id", help="Task ID to stop")
    
    # Get status command
    status_parser = subparsers.add_parser("status", help="Get browser agent status")
    status_parser.add_argument("--task-id", help="Task ID to check")
    
    # Get logs command
    logs_parser = subparsers.add_parser("logs", help="Get browser agent logs")
    logs_parser.add_argument("--task-id", help="Task ID to get logs for")
    logs_parser.add_argument("--save", action="store_true", help="Save logs to file")
    logs_parser.add_argument("--output", help="Output file path")
    
    # Set model command
    model_parser = subparsers.add_parser("set-model", help="Set default model")
    model_parser.add_argument("--provider", default="google", help="LLM provider")
    model_parser.add_argument("--model", default="gemini-2.0-flash", help="Model name")
    model_parser.add_argument("--temperature", type=float, default=0.6, help="Temperature")
    model_parser.add_argument("--api-key", help="API key")
    model_parser.add_argument("--update-env", action="store_true", help="Update .env file")
    
    # Get model command
    get_model_parser = subparsers.add_parser("get-model", help="Get default model")
    
    # Run example command
    example_parser = subparsers.add_parser("example", help="Run example task")
    
    args = parser.parse_args()
    
    if args.command == "run":
        task_id = run_task_from_prompt(args.prompt)
        print_colored(f"Task started with ID: {task_id}", "green")
    
    elif args.command == "stop":
        success = stop_agent(args.task_id)
        if success:
            print_colored("Task stopped successfully", "green")
        else:
            print_colored("Failed to stop task", "red")
    
    elif args.command == "status":
        status = get_agent_status(args.task_id)
        print_colored(format_json(status), "blue")
    
    elif args.command == "logs":
        logs = retrieve_logs(args.task_id)
        if args.save:
            log_file = save_logs_to_file(args.task_id, args.output)
            print_colored(f"Logs saved to: {log_file}", "green")
        else:
            print_colored(format_json(logs), "blue")
    
    elif args.command == "set-model":
        config = set_default_model(
            provider=args.provider,
            model_name=args.model,
            temperature=args.temperature,
            api_key=args.api_key
        )
        print_colored(f"Default model set to: {format_json(config)}", "green")
        
        if args.update_env:
            success = update_env_with_model_config(config)
            if success:
                print_colored("Updated .env file with new configuration", "green")
            else:
                print_colored("Failed to update .env file", "red")
    
    elif args.command == "get-model":
        config = get_current_model_config()
        print_colored(format_json(config), "blue")
    
    elif args.command == "example":
        run_example_task()
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
