#!/usr/bin/env python3
"""
Test script for the Browser-Use MCP helper functions.

This script demonstrates how to use the helper functions to run browser tasks
using the MCP implementation.
"""

import os
import sys
import time
from pathlib import Path

# Add the parent directory to the path
current_dir = Path(__file__).parent
sys.path.append(str(current_dir.parent))

# Import the helper functions
from mcp_helpers import run_browser_task, stop_browser_task, get_browser_logs, run_deep_research

# Define the task - same as before
TASK = (
    "Go to www.google.com and search for '100 best songs of all time'. "
    "Then return the result page of the first URL. "
    "Go into the first URL and then return me the page content."
)

# Define a research task
RESEARCH_TASK = (
    "What are the top 5 most popular programming languages in 2024 "
    "and what are their main advantages?"
)

def print_header(message):
    """Print a formatted header."""
    print("\n" + "=" * 80)
    print(f" {message} ".center(80, "="))
    print("=" * 80 + "\n")

def test_browser_task():
    """Test the run_browser_task and stop_browser_task functions."""
    print_header("RUNNING BROWSER TASK")
    print(f"Task: {TASK}")
    
    # Run the browser task
    task_id = run_browser_task(TASK, headless=False, use_vision=True)
    print(f"Task started with ID: {task_id}")
    
    # Let it run for a bit (30 seconds)
    print("\nLetting the task run for 30 seconds...\n")
    for i in range(30, 0, -1):
        print(f"Stopping in {i} seconds...", end="\r")
        time.sleep(1)
    print("\n")
    
    # Stop the task
    print_header("STOPPING THE BROWSER TASK")
    success = stop_browser_task()
    if success:
        print("Task stopped successfully")
    else:
        print("Failed to stop task")
    
    # Get the logs
    print_header("BROWSER LOGS")
    logs = get_browser_logs()
    print(f"Retrieved {len(logs)} log entries")
    
    # Print the logs
    for i, entry in enumerate(logs, 1):
        role = entry.get("role", "unknown")
        content = entry.get("content", "")
        if isinstance(content, str) and len(content) > 100:
            content = content[:97] + "..."
        print(f"{i}. [{role}] {content}")

def test_deep_research():
    """Test the run_deep_research function."""
    print_header("RUNNING DEEP RESEARCH")
    print(f"Research Task: {RESEARCH_TASK}")
    
    # Create a directory for research output
    research_dir = os.path.join(os.path.dirname(__file__), "research_output")
    os.makedirs(research_dir, exist_ok=True)
    
    # Run the deep research task
    task_id = run_deep_research(
        RESEARCH_TASK,
        max_parallel_browsers=2,
        save_dir=research_dir
    )
    print(f"Research task started with ID: {task_id}")
    
    # Let it run (this can take a while)
    print("\nThe research task is running in the background.")
    print("This can take several minutes to complete.")
    print("You can check the logs and the research_output directory for results.")
    
    # Wait for user input to continue
    input("\nPress Enter to continue...\n")
    
    # Stop the task
    print_header("STOPPING THE RESEARCH TASK")
    success = stop_browser_task()
    if success:
        print("Research task stopped successfully")
    else:
        print("Failed to stop research task")
    
    # Get the logs
    print_header("RESEARCH LOGS")
    logs = get_browser_logs()
    print(f"Retrieved {len(logs)} log entries")
    
    # Print the logs
    for i, entry in enumerate(logs, 1):
        role = entry.get("role", "unknown")
        content = entry.get("content", "")
        if isinstance(content, str) and len(content) > 100:
            content = content[:97] + "..."
        print(f"{i}. [{role}] {content}")

def main():
    """Main function to run the tests."""
    print_header("MCP BROWSER HELPER FUNCTIONS TEST")
    
    # Test options
    print("1. Test Browser Task")
    print("2. Test Deep Research")
    print("3. Run Both Tests")
    
    # Automatically select option 1 for testing
    print("\nAutomatically selecting option 1: Test Browser Task")
    choice = "1"
    
    if choice == "1":
        test_browser_task()
    elif choice == "2":
        test_deep_research()
    elif choice == "3":
        test_browser_task()
        test_deep_research()
    else:
        print("Invalid choice. Exiting...")
        return
    
    print_header("TEST COMPLETED")
    print("You can now use these helper functions in your own code!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"Error during test: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
