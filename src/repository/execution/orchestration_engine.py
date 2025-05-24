import re
import datetime
import uuid
import threading
import time
from typing import Dict, List, Any, Optional, Callable
import os
import json
import traceback

from src.repository.agent.general_agent import GeneralAgent
from src.repository.execution.meta_planner import MetaPlanner
from src.repository.execution.build_environment import BuildEnvironment
from src.repository.execution.testing_framework import TestingFramework
from src.repository.execution.feedback_analyzer import FeedbackAnalyzer
from src.repository.execution.agent_flow import AgentFlow
from src.service.llm_factory import LLMFactory
from src.service.tool_service import ToolService
from src.repository.execution.agent_manager import AgentManager
from src.schemas.issue_models import DetailedIssue
from src.repository.execution.project_manager import ProjectManager
from src.repository.execution.code_generation_coordinator import CodeGenerationCoordinator
from src.repository.execution.build_test_manager import BuildTestManager
from src.repository.execution.progress_issue_tracker import ProgressIssueTracker

class OrchestrationEngine:
    """
    Central component that orchestrates the project synthesis workflow.
    Coordinates agents, planning, building, testing, and feedback through agent flow.
    """
    
    def __init__(self, workspace_path: str, llm_factory: LLMFactory, tool_service: ToolService):
        """
        Initialize the orchestration engine.
        
        Args:
            workspace_path: Path to the project workspace directory.
            llm_factory: Factory for creating LLM instances.
            tool_service: Service for accessing and managing tools.
        """
        self.project_manager = ProjectManager(workspace_path, tool_service)
        self.codegen = CodeGenerationCoordinator(llm_factory, tool_service)
        self.build_test = BuildTestManager(tool_service, None, None, workspace_path)  # Pass actual testing_framework/feedback_analyzer if needed
        self.progress_tracker = ProgressIssueTracker()
        self.workspace_path = workspace_path
        self.llm_factory = llm_factory
        self.tool_service = tool_service
        from src.repository.execution.meta_planner import MetaPlanner
        self.meta_planner = MetaPlanner(llm_factory)
        
    def process_user_request(self, user_prompt: str, project_name: Optional[str] = None, async_execution: bool = True) -> Dict[str, Any]:
        """
        Complete workflow: elaborate prompt -> initialize -> plan -> execute via agent flow.
        
        Args:
            user_prompt: Raw user input
            project_name: Optional project name
            async_execution: Whether to run code generation asynchronously
            
        Returns:
            Result dictionary with project information and status
        """
        self.progress_tracker.update_progress("Elaborating user request...", 5)
        # You would call your LLM here for prompt elaboration
        project_description = user_prompt  # Replace with actual elaboration logic
        self.progress_tracker.update_progress("Initializing project...", 10)
        init_result = self.project_manager.initialize_project(project_description, project_name)
        if not init_result.get("success"):
            return init_result
        self.progress_tracker.update_progress("Planning project...", 15)
        # ...call meta planner here if needed...
        # ...call codegen, build_test, etc. as needed...
        return {"success": True, "message": "Workflow completed (stub)"}

    def run_full_workflow(self, user_prompt, project_name=None):
        """
        Full workflow: elaborate prompt -> meta plan -> agent flow codegen.
        """
        self.progress_tracker.update_progress("Elaborating user prompt...", 5)
        # TODO: Replace with actual LLM-based elaboration if needed
        project_description = user_prompt

        self.progress_tracker.update_progress("Initializing project...", 10)
        init_result = self.project_manager.initialize_project(project_description, project_name)
        if not init_result.get("success"):
            return init_result

        # Set up external project directory before generating code
        try:
            project_output_dir = self.codegen.set_project_output_directory(self.project_manager.project_name)
            print(f"🎯 Project will be generated at: {project_output_dir}")
        except Exception as e:
            return {
                "success": False, 
                "message": f"Failed to create project directory: {str(e)}"
            }

        self.progress_tracker.update_progress("Planning project...", 20)
        plan = self.meta_planner.decompose_project(project_description)
        if not plan or not isinstance(plan, dict):
            return {"success": False, "message": "Meta planning failed."}

        self.progress_tracker.update_progress("Creating and running agent flow tasks...", 30)
        agent_flow_tasks = self.codegen.create_agent_flow_tasks(
            plan,
            self.project_manager.project_name,
            self.project_manager.project_description
        )
        codegen_result = self.codegen.execute_agent_flow_generation(self.project_manager.project_name)

        return {
            "success": codegen_result.get("success", False),
            "project_name": self.project_manager.project_name,
            "project_output_directory": project_output_dir,
            "plan": plan,
            "agent_flow_tasks": agent_flow_tasks,
            "codegen_result": codegen_result
        }

    # Add more high-level coordination methods as needed
