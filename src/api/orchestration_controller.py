from fastapi import APIRouter, HTTPException, Body, Depends, Query, status
from typing import Dict, Any, Optional
import datetime

from src.schemas.project_models import ProjectInitializationRequest, ErrorReportRequest
from src.repository.execution.orchestration_engine import OrchestrationEngine
from src.service.llm_factory import LLMFactory
from src.service.tool_service import ToolService

# This is a simplified way to get an engine instance for the example.
# In a real app, you'd manage this instance properly (e.g., singleton, dependency injection).
# For now, we'll create a global instance or a factory function.

# Dummy configurations - replace with your actual configuration loading
DUMMY_CONFIG = {
    "llm_provider": "gemini", # Or your preferred default
    "gemini_api_key": "YOUR_GEMINI_API_KEY", # Ensure this is configured securely
    "anthropic_api_key": "YOUR_ANTHROPIC_API_KEY",
    "openai_api_key": "YOUR_OPENAI_API_KEY",
    "aws_access_key_id": "YOUR_AWS_ACCESS_KEY",
    "aws_secret_access_key": "YOUR_AWS_SECRET_KEY",
    "aws_region_name": "YOUR_AWS_REGION"
}

llm_factory = LLMFactory(config=DUMMY_CONFIG)
tool_service = ToolService(config=DUMMY_CONFIG, llm_factory=llm_factory) # ToolService might need llm_factory

# Global engine instance (consider a more robust dependency injection for production)
# The workspace_path should ideally come from configuration or be dynamically determined.
orchestration_engine_instance = OrchestrationEngine(
    workspace_path="d:\\Asmit\\main-code-zelash\\workspace", # Example path, adjust as needed
    llm_factory=llm_factory,
    tool_service=tool_service
)

def get_orchestration_engine():
    # In a real application, this could fetch a pre-configured instance
    # or initialize one if it doesn't exist.
    return orchestration_engine_instance

class OrchestrationController:
    def __init__(self, app, engine: OrchestrationEngine):
        self.router = APIRouter(prefix="/api/orchestration", tags=["Orchestration"])
        self.engine = engine

        @self.router.post("/project/initialize_and_plan", 
                         response_model=Dict[str, Any],
                         summary="Initialize and Plan New Project",
                         description="Initializes a new project with a description and name, then creates an execution plan. If another project is active, it will return an error unless the active project is in a terminal state (idle, completed, error).")
        async def initialize_and_plan_project(
            request: ProjectInitializationRequest = Body(...),
            current_engine: OrchestrationEngine = Depends(get_orchestration_engine)
        ):
            """
            Initializes and plans a new project based on the provided description.
            This corresponds to the conceptual /orchestrate endpoint and immediately plans.
            """
            try:
                if current_engine.project_id and current_engine.current_status not in ["idle", "completed", "error", "completed_with_issues", "error_reported"]:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT, 
                        detail=f"Project '{current_engine.project_name}' is currently active (status: '{current_engine.current_status}'). Stop or wait for completion before starting a new one."
                    )

                current_engine.stop_execution() # Ensure any previous run is fully stopped.
                # Reset key engine states for a new project if one was previously active
                if current_engine.project_id:
                    current_engine.project_id = None
                    current_engine.project_name = None
                    current_engine.project_description = None
                    current_engine.execution_plan = None
                    current_engine.project_files = []
                    current_engine.service_urls = []
                    current_engine.current_iteration = 0
                    current_engine.externally_reported_errors = []
                    current_engine.current_status = "idle" # Explicitly reset status
                
                init_result = current_engine.initialize_project(
                    project_description=request.project_description,
                    project_name=request.project_name
                )
                if not init_result or not init_result.get("project_id"):
                    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Project initialization failed: {init_result.get('message', 'Unknown error')}")

                plan_result = current_engine.plan_project()
                if not plan_result or not plan_result.get("execution_plan"):
                    # Rollback or log initialization if planning fails immediately after
                    current_engine.current_status = "initialization_failed_planning"
                    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Project planning failed: {plan_result.get('message', 'Unknown error')}")
                
                final_status = current_engine.get_status()
                return {
                    "message": "Project initialized and planned successfully. Ready for code generation.",
                    "project_name": final_status.get("project_name"),
                    "project_id": final_status.get("project_id"),
                    "current_status_details": final_status
                }
            except HTTPException as http_exc:
                raise http_exc
            except Exception as e:
                print(f"Unhandled error in initialize_and_plan_project: {str(e)}")
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Orchestration error: {str(e)}")

        @self.router.post("/project/generate_code", 
                         response_model=Dict[str, Any],
                         summary="Generate Project Code",
                         description="Starts the asynchronous code generation process for the currently planned project. Project must be in 'planned' state.")
        async def generate_project_code(
            current_engine: OrchestrationEngine = Depends(get_orchestration_engine)
        ):
            """
            Starts the code generation process for the currently planned project.
            This is an asynchronous operation.
            """
            try:
                if not current_engine.project_id or current_engine.current_status != "planned":
                    detail_msg = f"Project '{current_engine.project_name or 'Unknown'}' must be initialized and in 'planned' state before generating code. Current status: '{current_engine.current_status}'."
                    if not current_engine.project_id:
                        detail_msg = "No project has been initialized and planned. Please call /project/initialize_and_plan first."
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=detail_msg
                    )
                
                # Start code generation (asynchronously by default in OrchestrationEngine)
                generation_response = current_engine.generate_code(async_execution=True)
                return generation_response
            except HTTPException as http_exc:
                raise http_exc
            except Exception as e:
                print(f"Unhandled error in generate_project_code: {str(e)}")
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Code generation initiation error: {str(e)}")

        @self.router.post("/report_error", 
                         response_model=Dict[str, Any],
                         summary="Report External Error",
                         description="Allows external components to report errors. The OrchestrationEngine logs the error and may use it for remediation.")
        async def report_error(
            request: ErrorReportRequest = Body(...),
            current_engine: OrchestrationEngine = Depends(get_orchestration_engine)
        ):
            """
            Allows components to report errors. The OrchestrationEngine will
            log the error. The engine's internal mechanisms (e.g., refinement loops)
            are responsible for acting on errors. This endpoint informs the engine.
            """
            try:
                if not current_engine.project_id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Cannot report error: No project is currently active in the Orchestration Engine."
                    )
                report_result = current_engine.report_external_error(request.model_dump())
                return report_result
            except HTTPException as http_exc:
                raise http_exc
            except Exception as e:
                print(f"Unhandled error in report_error: {str(e)}")
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error reporting failed: {str(e)}")

        @self.router.get("/project/status", 
                        response_model=Dict[str, Any],
                        summary="Get Project Status",
                        description="Returns the current status of the active project managed by the OrchestrationEngine.")
        async def get_project_status(
            current_engine: OrchestrationEngine = Depends(get_orchestration_engine)
        ):
            """
            Returns the current status of the active project being managed by the OrchestrationEngine.
            """
            try:
                if not current_engine.project_id:
                    return {
                        "message": "No project is currently active or initialized.",
                        "status": "idle",
                        "project_id": None,
                        "project_name": None,
                        "last_updated": datetime.datetime.now().isoformat()
                    }
                
                status_data = current_engine.get_status()
                return status_data
            except Exception as e:
                print(f"Unhandled error in get_project_status: {str(e)}")
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to get project status: {str(e)}")

        @self.router.post("/project/stop_execution", 
                         response_model=Dict[str, str],
                         summary="Stop Project Execution",
                         description="Requests the OrchestrationEngine to stop any ongoing background tasks for the current project.")
        async def stop_project_execution(
            current_engine: OrchestrationEngine = Depends(get_orchestration_engine)
        ):
            """
            Stops any ongoing execution in the OrchestrationEngine.
            """
            try:
                if not current_engine.project_id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="No project is currently active to stop."
                    )
                current_engine.stop_execution()
                return {"message": f"Execution stop requested for project '{current_engine.project_name}'. Current status after request: {current_engine.get_status().get('status')}"}
            except Exception as e:
                print(f"Unhandled error in stop_project_execution: {str(e)}")
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to stop execution: {str(e)}")

        app.include_router(self.router)

