from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

class ProjectInitializationRequest(BaseModel):
    project_name: str = Field(..., description="Unique name or ID for the project/task.")
    project_description: str = Field(..., description="Detailed description of what needs to be built.")

class ErrorReportRequest(BaseModel):
    task_id: Optional[str] = Field(None, description="The ID of the task/project this error pertains to. Should match active project if provided.")
    error_message: str = Field(..., description="The error message or description of the issue.")
    component: Optional[str] = Field(None, description="The component that reported the error (e.g., 'backend_agent', 'testing_framework').")
    details: Optional[Dict[str, Any]] = Field(None, description="Any additional details or context about the error.")

