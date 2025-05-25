#!/usr/bin/env python3
"""
Amazon Headphones Search - WebUI Integration

This script demonstrates how to programmatically trigger the same components
that get activated when clicking buttons on the web interface.
It uses the proper WebUI integration to search for headphones on Amazon.
"""

import os
import sys
import asyncio
import logging
import json
from typing import Dict, Any, Optional

# Import Gradio components for proper typing
try:
    import gradio as gr
    from gradio.components import Component, Textbox, Button, Chatbot, HTML, File, Image
except ImportError:
    # If running without Gradio installed, define placeholder classes for type checking
    class Component: pass
    class Textbox(Component): pass
    class Button(Component): pass
    class Chatbot(Component): pass
    class HTML(Component): pass
    class File(Component): pass
    class Image(Component): pass

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("amazon_search_webui")

# Add project root to path if needed
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Import necessary components from the web_ui structure
from src.webui.webui_manager import WebuiManager
from src.webui.components.browser_use_agent_tab import run_agent_task
from src.utils import llm_provider
from src.browser.custom_browser import CustomBrowser
from src.browser.custom_context import CustomBrowserContextConfig
from src.controller.custom_controller import CustomController
from src.agent.browser_use.browser_use_agent import BrowserUseAgent


def print_colored(text: str, color: str = 'white') -> None:
    """
    Print colored text to the console
    
    Args:
        text: The text to print
        color: Color name (red, green, blue, etc.)
    """
    color_codes = {
        "black": "\033[30m",
        "red": "\033[31m",
        "green": "\033[32m",
        "yellow": "\033[33m",
        "blue": "\033[34m",
        "magenta": "\033[35m",
        "cyan": "\033[36m",
        "white": "\033[37m",
        "reset": "\033[0m"
    }
    color_code = color_codes.get(color.lower(), color_codes["white"])
    reset_code = color_codes["reset"]
    print(f"{color_code}{text}{reset_code}")


async def print_agent_updates(update_dict: Dict[Any, Any]) -> None:
    """Print updates from the agent to the console"""
    if not update_dict:
        return
    
    # Extract chat history updates if present
    for comp, value in update_dict.items():
        # Check for chatbot updates (the component where agent responses appear)
        if hasattr(comp, "label") and comp.label == "Agent Interaction":
            if hasattr(value, "value"):
                chat_history = value.value
                if chat_history and len(chat_history) > 0:
                    # Print the latest message
                    latest_msg = chat_history[-1]
                    if isinstance(latest_msg, dict):
                        role = latest_msg.get("role", "")
                        content = latest_msg.get("content", "")
                        
                        if role == "assistant":
                            print_colored(f"Agent: {content}", "green")
                        elif role == "user":
                            print_colored(f"User: {content}", "cyan")
        
        # Print button state changes for debugging
        if hasattr(comp, "value") and isinstance(comp, Button):
            print_colored(f"Button state: {comp.value}", "yellow")
            
        # Print any browser screenshots or view updates
        if comp.label == "Browser View" and hasattr(value, "value"):
            print_colored("Browser view updated", "blue")


async def run_amazon_search() -> None:
    """
    Run the Amazon headphones search by triggering the same components
    that get activated when using the web interface
    """
    print_colored("=== AMAZON HEADPHONES SEARCH (WebUI Integration) ===", "magenta")
    
    # Initialize the WebUI manager (same as what happens when the UI starts)
    webui_manager = WebuiManager()
    
    # Initialize the browser use agent components
    webui_manager.init_browser_use_agent()
    
    # Create a simple structure to initialize the tab components for browser agent
    from gradio.components import Component, Textbox, Button, Chatbot, HTML, File, Image
    
    # Initialize browser use agent tab components
    tab_components = {
        "chatbot": Chatbot(value=[], label="Agent Interaction"),
        "user_input": Textbox(value="Go to www.amazon.com and search for headphones", label="Your Task"),
        "run_button": Button(value="▶️ Submit Task"),
        "stop_button": Button(value="⏹️ Stop"),
        "pause_resume_button": Button(value="⏸️ Pause"),
        "clear_button": Button(value="🗑️ Clear"),
        "agent_history_file": File(label="Agent History"),
        "recording_gif": Image(label="Recording"),
        "browser_view": HTML(label="Browser View")
    }
    
    # Add components to the webui_manager
    webui_manager.add_components("browser_use_agent", tab_components)
    
    # Create a dictionary that maps components to their values (as expected by run_agent_task)
    mock_components = {}
    for name, component in tab_components.items():
        if name == "user_input":
            mock_components[component] = "Go to www.amazon.com and search for headphones"
    
    # Run the agent task (this is what happens when the Submit button is clicked)
    print_colored("Starting browser agent with task: Go to www.amazon.com and search for headphones", "blue")
    
    try:
        # Run the agent task asynchronously and process updates
        async for update in run_agent_task(webui_manager, mock_components):
            # Print updates from the agent
            await print_agent_updates(update)
            await asyncio.sleep(0.1)  # Small delay to prevent flooding the console
        
        print_colored("Task completed successfully!", "green")
        
    except Exception as e:
        logger.error(f"Error running Amazon search: {e}", exc_info=True)
        print_colored(f"Error: {e}", "red")
    
    finally:
        # Clean up resources
        if hasattr(webui_manager, 'bu_browser') and webui_manager.bu_browser:
            print_colored("Closing browser...", "blue")
            await webui_manager.bu_browser.close()
            print_colored("Browser closed successfully", "green")


async def main() -> None:
    """Main entry point for the script"""
    try:
        await run_amazon_search()
    except KeyboardInterrupt:
        print_colored("\nScript interrupted by user", "yellow")
    except Exception as e:
        logger.error(f"Unhandled exception: {e}", exc_info=True)
        print_colored(f"Fatal error: {e}", "red")


if __name__ == "__main__":
    # Set up the event loop and run the main function
    print_colored("This script integrates with the web_ui components to search for headphones on Amazon", "cyan")
    print_colored("It triggers the same objects that get activated when clicking buttons on the interface", "cyan")
    asyncio.run(main())
