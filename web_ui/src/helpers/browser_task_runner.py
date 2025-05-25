#!/usr/bin/env python3
"""
Browser Task Runner

This script provides a simple way to run browser agent tasks with a visible browser window.
It directly triggers the core browser agent functionality, similar to what happens when
clicking the 'Submit Task' button in the WebUI, but without requiring the full UI.

Usage:
    python browser_task_runner.py [task]
    
If no task is provided, it will run the default Andhra restaurants search task.
"""

import os
import sys
import asyncio
import logging
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("minimal_trigger")

# Add project root to path if needed
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Load environment variables
dotenv_path = os.path.join(project_root, '.env')
load_dotenv(dotenv_path)

# Import necessary components
from src.utils import llm_provider
from src.browser.custom_browser import CustomBrowser
from src.browser.custom_context import CustomBrowserContextConfig
from src.controller.custom_controller import CustomController
from src.agent.browser_use.browser_use_agent import BrowserUseAgent


async def run_browser_task(task: str):
    """
    Run the browser agent with the specified task
    
    Args:
        task: The task prompt for the browser agent to execute
    """
    print("Initializing browser agent...")
    print(f"Task: {task}")
    
    # Initialize the LLM (Google Gemini)
    llm = llm_provider.get_llm_model(
        provider="google",
        model_name="gemini-2.0-flash",
        temperature=0.7
    )
    
    # Initialize the browser with visible window
    browser = CustomBrowser()
    
    # Create browser context with visible window
    browser_context_config = CustomBrowserContextConfig(
        window_size={"width": 1280, "height": 800},
        headless=False,  # Ensure browser is visible
        slow_mo=100  # Add slight delay for visibility
    )
    
    # Create the browser context
    browser_context = await browser.new_context(config=browser_context_config)
    
    # Initialize the controller
    controller = CustomController()
    controller.browser_context = browser_context
    
    try:
        # Initialize the agent
        agent = BrowserUseAgent(
            task=task,
            llm=llm,
            browser=browser,
            browser_context=browser_context,
            controller=controller,
            use_vision=True,
            max_input_tokens=128000,
            max_actions_per_step=10,
            source="minimal_trigger"
        )
        
        # Run the agent directly, without callback registrations
        print("Starting browser agent to run task...")
        await agent.run(max_steps=20)
        
    except Exception as e:
        logger.error(f"Error running browser agent: {e}", exc_info=True)
        print(f"Error: {e}")
        
    finally:
        # Close the browser
        if browser:
            print("Closing browser...")
            await browser.close()
            print("Browser closed successfully")


def main():
    """Run the browser task runner with optional command-line arguments"""
    try:
        print("===== BROWSER TASK RUNNER =====")
        
        # Check for command-line arguments for custom task
        if len(sys.argv) > 1:
            # Join all arguments to form the task string
            custom_task = " ".join(sys.argv[1:])
            print(f"Running custom task: {custom_task}")
            asyncio.run(run_browser_task(custom_task))
        else:
            # Run the default task
            default_task = "Go to www.google.com and search for 'best Andhra food restaurants in Bangalore'. Visit the first search result and extract information about the restaurant."
            print(f"Running default task: {default_task}")
            asyncio.run(run_browser_task(default_task))
        
        print("===== BROWSER TASK COMPLETED =====")
        
    except KeyboardInterrupt:
        print("\nTask interrupted by user")
        sys.exit(130)
    
    except Exception as e:
        logger.error(f"Unhandled exception: {e}", exc_info=True)
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
