import os
import sys
import argparse
from dotenv import load_dotenv
import atexit
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables from .env file at the project root
# Assuming main.py is in src/, so .env is one level up from main.py's directory's parent
# More robustly, ZELASH_PROJECT_ROOT could be set, or we can infer.
project_root = Path(__file__).resolve().parent.parent 
load_dotenv(dotenv_path=project_root / ".env")

# FastAPI imports
import uvicorn
from fastapi import FastAPI

# Application components
from src.api.agent_controller import AgentController
from src.api.tool_controller import ToolController
from src.api.orchestration_controller import OrchestrationController, get_orchestration_engine
from src.service.agent_service import AgentService
from src.service.llm_factory import LLMFactory
from src.service.tool_service import ToolService
from src.repository.deployment.cli import CLI
from src.repository.deployment.web_ui import WebUI

# Import the server manager
from src.utils.browser_automation_server_manager import BrowserAutomationServerManager # Added
from typing import Optional # Added

# Global instance of the server manager
# It will use os.environ if no specific config object is passed, which is fine here.
browser_server_manager: Optional[BrowserAutomationServerManager] = None # Added


def initialize_browser_automation_server_manager(): # Added
    global browser_server_manager # Added
    # Pass os.environ (or a wrapper) if BrowserAutomationServerManager expects a config object
    # For now, assuming BrowserAutomationServerManager can directly use os.environ if no config is passed
    # or uses a default SimpleConfigProvider as implemented.
    # Set ZELASH_PROJECT_ROOT if not already set, for the manager to use
    if "ZELASH_PROJECT_ROOT" not in os.environ:
        os.environ["ZELASH_PROJECT_ROOT"] = str(project_root)
    
    browser_server_manager = BrowserAutomationServerManager() # Instantiated
    if browser_server_manager.enabled: # Added
        logger.info("Browser Automation Server is enabled. Attempting to start...") # Added
        if browser_server_manager.start_server(): # Added
            logger.info("Browser Automation Server started successfully by manager.") # Added
        else: # Added
            logger.error("Browser Automation Server failed to start via manager. Check logs.") # Added
    else: # Added
        logger.info("Browser Automation Server is disabled in configuration. Will not be started.") # Added

def shutdown_browser_automation_server(): # Added
    global browser_server_manager # Added
    if browser_server_manager and browser_server_manager.is_running(): # Added
        logger.info("Attempting to stop Browser Automation Server via manager...") # Added
        browser_server_manager.stop_server() # Added
        logger.info("Browser Automation Server stop command issued via manager.") # Added
    elif browser_server_manager and browser_server_manager.enabled:
        logger.warning("Browser Automation Server was enabled but not running at shutdown. No stop action needed.")
    else:
        logger.info("Browser Automation Server was not running or not enabled. No stop action needed.")

# Register the shutdown function with atexit for all modes
atexit.register(shutdown_browser_automation_server) # Added

def create_app():
    """
    Create and configure the FastAPI application with all services.
    
    Returns:
        Configured FastAPI application.
    """
    # Create FastAPI app
    app = FastAPI(
        title="Zelash AI Framework",
        description="A fully Python-based, AI-powered developer assistant.",
        version="0.1.0"
    )

    # FastAPI event handlers for API mode
    @app.on_event("startup")
    async def startup_event():
        logger.info("FastAPI app startup: Initializing Browser Automation Server Manager...")
        initialize_browser_automation_server_manager() # Use the new manager

    @app.on_event("shutdown")
    async def shutdown_event():
        # atexit will handle the shutdown, but we can log here too.
        logger.info("FastAPI app shutdown: Browser Automation Server will be stopped by atexit handler.")
        # shutdown_browser_automation_server() # atexit handles this
    
    # Initialize services
    llm_config = {
        'gemini': {
            'api_key': os.environ.get('GEMINI_API_KEY'),
            'model': os.environ.get('GEMINI_MODEL', 'gemini-1.5-pro'),
            'temperature': 0.7
        },
        'openai': {
            'api_key': os.environ.get('OPENAI_API_KEY'),
            'model': os.environ.get('OPENAI_MODEL', 'gpt-4o'),
            'temperature': 0.7
        },
        'anthropic': {
            'api_key': os.environ.get('ANTHROPIC_API_KEY'),
            'model': os.environ.get('ANTHROPIC_MODEL', 'claude-3-sonnet'),
            'temperature': 0.7
        },
        'bedrock': {
            'region_name': os.environ.get('AWS_REGION', 'us-east-1'),
            'model': os.environ.get('BEDROCK_MODEL', 'anthropic.claude-v2'),
            'temperature': 0.7
        }
    }
    llm_factory = LLMFactory(config=llm_config)
    
    tool_config = {
        'web_search': {
            'api_key': os.environ.get('GOOGLE_SEARCH_API_KEY'),
            'engine_id': os.environ.get('GOOGLE_SEARCH_ENGINE_ID')
        },
        'browser_use': {},
        'bash': {
            'allowed_commands': ['ls', 'cat', 'echo', 'find', 'grep'],
            'disallowed_commands': ['rm -rf', 'sudo', 'shutdown', 'reboot']
        },
        'planning': {},
        'chart': {
            'script_path': os.path.join(os.path.dirname(__file__), 'chart_generator.js')
        }
    }
    tool_service = ToolService(config=tool_config, llm_factory=llm_factory)
    
    agent_service = AgentService(llm_factory, tool_service)
    
    # Get the OrchestrationEngine instance
    orchestration_engine_instance = get_orchestration_engine()
    
    # Register controllers
    AgentController(app, agent_service)
    ToolController(app, tool_service)
    OrchestrationController(app, orchestration_engine_instance)
    
    return app, agent_service, tool_service, orchestration_engine_instance

def main():
    """
    Main entry point for the application.
    """
    parser = argparse.ArgumentParser(description="Zelash AI Framework")
    parser.add_argument("--mode", choices=["api", "cli", "web"], default="api",
                       help="Mode to run: API server, CLI, or Web UI")
    parser.add_argument("--host", default="0.0.0.0", help="Host for API server")
    parser.add_argument("--port", type=int, default=8000, help="Port for API server")
    parser.add_argument("--cli-args", nargs="*", help="Arguments to pass to CLI mode")
    parser.add_argument("--share", action="store_true", help="Share Web UI with public link")
    
    args = parser.parse_args()

    # Initialize and start the browser automation server manager early 
    # if not in API mode (where FastAPI startup handles it).
    # For CLI and Web modes, we start it here and rely on atexit for shutdown.
    if args.mode != "api":
        logger.info(f"{args.mode.upper()} mode: Initializing Browser Automation Server Manager...")
        initialize_browser_automation_server_manager()
    
    if args.mode == "api":
        # Run FastAPI server
        # Browser server is started by FastAPI startup event
        app, _, _, _ = create_app()
        uvicorn.run(app, host=args.host, port=args.port)
    
    elif args.mode == "cli":
        # Run CLI mode
        # Browser server started above, atexit handles shutdown
        cli = CLI()
        # Ensure sys.exit is called to trigger atexit handlers properly
        try:
            exit_code = cli.run(args.cli_args)
            if exit_code is None: # Handle cases where cli.run might not return an int
                exit_code = 0 
        except SystemExit as e:
            exit_code = e.code if e.code is not None else 0
        except Exception as e:
            logger.error(f"Unhandled exception in CLI mode: {e}", exc_info=True)
            exit_code = 1
        finally:
            sys.exit(exit_code)
    
    elif args.mode == "web":
        # Run Web UI mode
        # Browser server started above, atexit handles shutdown
        # Create app context but don't run uvicorn; web_ui.run handles its own server if any.
        _, agent_service, tool_service, orchestration_engine_instance = create_app()
        web_ui = WebUI()
        # WebUI().run() might block, ensure atexit is robust
        # If WebUI().run() is a blocking call that doesn't allow atexit to run cleanly on Ctrl+C,
        # we might need to handle signals for graceful shutdown.
        # For now, assume it exits cleanly or atexit is sufficient.
        try:
            web_ui.run(agent_service=agent_service, tool_service=tool_service, orchestration_engine=orchestration_engine_instance, share=args.share)
            exit_code = 0
        except KeyboardInterrupt:
            logger.info("Web UI interrupted. Exiting...")
            exit_code = 0
        except SystemExit as e: # Catch sys.exit from underlying Gradio/WebUI
            exit_code = e.code if e.code is not None else 0
        except Exception as e:
            logger.error(f"Unhandled exception in Web UI mode: {e}", exc_info=True)
            exit_code = 1
        finally:
            # atexit will handle server shutdown
            sys.exit(exit_code)

if __name__ == "__main__":
    main()