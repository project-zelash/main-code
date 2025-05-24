import os
import sys
import argparse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

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
    
    if args.mode == "api":
        # Run FastAPI server
        app, _, _, _ = create_app()
        uvicorn.run(app, host=args.host, port=args.port)
    
    elif args.mode == "cli":
        # Run CLI mode
        cli = CLI()
        sys.exit(cli.run(args.cli_args))
    
    elif args.mode == "web":
        # Run Web UI mode
        _, agent_service, tool_service, _ = create_app()
        web_ui = WebUI()
        web_ui.load_tools(tool_service.tools)
        web_ui.launch_ui(share=args.share)

if __name__ == "__main__":
    main()