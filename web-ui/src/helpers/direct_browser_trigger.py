#!/usr/bin/env python3
"""
Direct Browser Agent Runner

This script directly initializes and runs the browser agent in the same way
that the WebUI does when the Submit Task button is clicked.
"""

import os
import sys
import asyncio
import logging
import time
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("direct_trigger")

# Add project root to path if needed
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Load environment variables
dotenv_path = os.path.join(project_root, '.env')
load_dotenv(dotenv_path)

# Import necessary components for running the agent
from src.utils import llm_provider
from src.browser.custom_browser import CustomBrowser
from src.browser.custom_context import CustomBrowserContextConfig
from src.controller.custom_controller import CustomController
from src.agent.browser_use.browser_use_agent import BrowserUseAgent


async def on_step(state, output, step_num):
    """Callback for each step the agent takes"""
    logger.info(f"Step {step_num} completed")
    print(f"Step {step_num} completed")
    if state and hasattr(state, 'url') and state.url:
        print(f"Current URL: {state.url}")


async def on_done(history):
    """Callback when the agent completes its task"""
    logger.info("Task completed")
    print("Task completed successfully!")


async def on_user_help(query, context):
    """Callback when the agent asks for help"""
    logger.info(f"Agent asked for help: {query}")
    print(f"Agent needs help: {query}")
    return "Continue with the task."


async def run_browser_task():
    """
    Set up and run the browser agent using the WebUI agent lifecycle and log system.
    """
    from src.webui.webui_manager import WebuiManager
    from src.webui.components.browser_use_agent_tab import run_agent_task, handle_stop, handle_clear
    import gradio as gr

    print("Initializing browser agent (WebUI-integrated)...")
    task = "Go to www.google.com and search for 'best Andhra food restaurants in Bangalore'. Visit the first search result and extract information about the restaurant."
    print(f"Task: {task}")

    # Initialize WebUI manager and agent tab components
    webui_manager = WebuiManager()
    webui_manager.init_browser_use_agent()

    # Setup Gradio components and input dict as if from the UI
    from gradio.components import Textbox, Button, Chatbot, HTML, File, Image
    tab_components = {
        "chatbot": Chatbot(value=[], label="Agent Interaction", type="messages"),
        "user_input": Textbox(value=task, label="Your Task"),
        "run_button": Button(value="▶️ Submit Task"),
        "stop_button": Button(value="⏹️ Stop"),
        "pause_resume_button": Button(value="⏸️ Pause"),
        "clear_button": Button(value="🗑️ Clear"),
        "agent_history_file": File(label="Agent History"),
        "recording_gif": Image(label="Recording"),
        "browser_view": HTML(label="Browser View")
    }
    webui_manager.add_components("browser_use_agent", tab_components)
    mock_components = {}
    for name, component in tab_components.items():
        if name == "user_input":
            mock_components[component] = task

    print("Submitting agent task...")
    try:
        async for update in run_agent_task(webui_manager, mock_components):
            chat_history = webui_manager.bu_chat_history
            if chat_history:
                latest = chat_history[-1]
                print(f"[LOG][{latest['role']}] {latest['content']}")
            await asyncio.sleep(0.05)
        print("Agent task completed!")
    except Exception as e:
        logger.error(f"Error running agent: {e}", exc_info=True)
        print(f"Error: {e}")

    print("Stopping agent (simulating Stop button)...")
    await handle_stop(webui_manager)
    print("Agent stopped.")

    print("Clearing logs (simulating Clear button)...")
    await handle_clear(webui_manager)
    print("Logs cleared.")


def main():
    """Run the direct browser agent trigger"""
    try:
        print("===== DIRECT BROWSER AGENT TRIGGER =====")
        print("This script directly triggers the browser agent with a visible window")
        
        # Run the async function
        asyncio.run(run_browser_task())
        
        print("===== BROWSER AGENT COMPLETED =====")
        
    except KeyboardInterrupt:
        print("\nTask interrupted by user")
        sys.exit(130)
    
    except Exception as e:
        logger.error(f"Unhandled exception: {e}", exc_info=True)
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
