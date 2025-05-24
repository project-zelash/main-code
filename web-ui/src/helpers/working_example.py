#!/usr/bin/env python3
"""
Working Browser Example

This script launches a browser window and performs a Google search for
"best Andhra food restaurants in Bangalore"
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
logger = logging.getLogger("browser_example")

# Add project root to path if needed
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Load environment variables
load_dotenv(os.path.join(project_root, '.env'))

# Import required modules from browser_use
from src.browser.custom_browser import CustomBrowser
from src.browser.custom_context import CustomBrowserContextConfig
from src.controller.custom_controller import CustomController
from src.agent.browser_use.browser_use_agent import BrowserUseAgent
from src.webui.webui_manager import WebuiManager
from src.webui.components.browser_use_agent_tab import run_agent_task, handle_stop, handle_clear
import gradio as gr


async def run_browser_search():
    """
    Launch a browser and perform a Google search using the WebUI agent lifecycle and log system.
    """
    print("\033[94mLaunching browser for Andhra restaurant search (WebUI-integrated)...\033[0m")
    
    # Initialize WebUI manager and agent tab components
    webui_manager = WebuiManager()
    webui_manager.init_browser_use_agent()

    # Setup Gradio components and input dict as if from the UI
    from gradio.components import Textbox, Button, Chatbot, HTML, File, Image
    tab_components = {
        "chatbot": Chatbot(value=[], label="Agent Interaction", type="messages"),
        "user_input": Textbox(value="Go to google.com and search for best Andhra food restaurants in Bangalore", label="Your Task"),
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
            mock_components[component] = "Go to google.com and search for best Andhra food restaurants in Bangalore"

    print("\033[94mSubmitting agent task...\033[0m")
    try:
        async for update in run_agent_task(webui_manager, mock_components):
            chat_history = webui_manager.bu_chat_history
            if chat_history:
                latest = chat_history[-1]
                print(f"\033[92m[{latest['role']}\033[0m {latest['content']}")
            await asyncio.sleep(0.05)
        print("\033[92mAgent task completed!\033[0m")
    except Exception as e:
        logger.error(f"Error running agent: {e}", exc_info=True)
        print(f"\033[91mError: {e}\033[0m")
    
    print("\033[94mStopping agent (simulating Stop button)...\033[0m")
    await handle_stop(webui_manager)
    print("\033[92mAgent stopped.\033[0m")
    
    print("\033[94mClearing logs (simulating Clear button)...\033[0m")
    await handle_clear(webui_manager)
    print("\033[92mLogs cleared.\033[0m")


def main():
    """Run the browser example"""
    try:
        # Run the async function
        asyncio.run(run_browser_search())
    
    except KeyboardInterrupt:
        print("\n\033[93mTask interrupted by user\033[0m")
        sys.exit(130)
    
    except Exception as e:
        logger.error(f"Unhandled exception: {e}", exc_info=True)
        print(f"\033[91mFatal error: {e}\033[0m")
        sys.exit(1)


if __name__ == "__main__":
    main()
