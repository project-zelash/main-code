import sys
import argparse

# FastAPI imports
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Application components
from src.api.agent_controller import AgentController
from src.api.tool_controller import ToolController
from src.api.orchestration_controller import OrchestrationController
from src.config import settings
from src.service.agent_service import AgentService
from src.service.llm_factory import LLMFactory
from src.service.tool_service import ToolService

def create_app():
    """
    Create and configure the FastAPI application with all services.
    
    Returns:
        Configured FastAPI application.
    """
    # Create FastAPI app
    app = FastAPI(
        title="Zelash AI Framework",
        description="Autonomous project synthesis API and build pipeline.",
        version="1.0.0"
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Initialize services
    llm_factory = LLMFactory(config=settings.llm_config())
    tool_service = ToolService(config=settings.tool_config(), llm_factory=llm_factory)
    
    agent_service = AgentService(llm_factory, tool_service)
    
    # Register controllers
    AgentController(app, agent_service)
    ToolController(app, tool_service)
    orchestration_controller = OrchestrationController(app, llm_factory, tool_service)
    
    return app, agent_service, tool_service, orchestration_controller

def main():
    """
    Main entry point for the application.
    """
    parser = argparse.ArgumentParser(description="Zelash AI Framework")
    parser.add_argument("--mode", choices=["api", "cli", "web"], default="api",
                       help="Mode to run: API server, CLI, or Web UI")
    parser.add_argument("--host", default=settings.host, help="Host for API server")
    parser.add_argument("--port", type=int, default=settings.port, help="Port for API server")
    parser.add_argument("--cli-args", nargs="*", help="Arguments to pass to CLI mode")
    parser.add_argument("--share", action="store_true", help="Share Web UI with public link")
    
    args = parser.parse_args()
    
    if args.mode == "api":
        # Run FastAPI server
        app, _, _, _ = create_app()
        uvicorn.run(app, host=args.host, port=args.port)
    
    elif args.mode == "cli":
        # Run CLI mode
        from src.repository.deployment.cli import CLI
        cli = CLI()
        sys.exit(cli.run(args.cli_args))
    
    elif args.mode == "web":
        # Run Web UI mode
        from src.repository.deployment.web_ui import WebUI
        _, agent_service, tool_service, _ = create_app()
        web_ui = WebUI()
        web_ui.load_tools(tool_service.tools)
        web_ui.launch_ui(share=args.share)

if __name__ == "__main__":
    main()
