import re
import datetime
import uuid
import threading
import time
from typing import Dict, List, Any, Optional, Callable # Added Callable
import os
import json
import traceback # For stack traces, if desired

from src.repository.agent.general_agent import GeneralAgent
from src.repository.execution.meta_planner import MetaPlanner
from src.repository.execution.build_environment import BuildEnvironment
from src.repository.execution.testing_framework import TestingFramework
from src.repository.execution.feedback_analyzer import FeedbackAnalyzer
from src.service.llm_factory import LLMFactory
from src.service.tool_service import ToolService
from src.repository.execution.agent_manager import AgentManager
from src.schemas.issue_models import DetailedIssue # Added import

class OrchestrationEngine:
    """
    Central component that orchestrates the project synthesis workflow.
    Coordinates agents, planning, building, testing, and feedback.
    """
    
    def __init__(self, workspace_path: str, llm_factory: LLMFactory, tool_service: ToolService):
        """
        Initialize the orchestration engine.
        
        Args:
            workspace_path: Path to the project workspace directory.
            llm_factory: Factory for creating LLM instances.
            tool_service: Service for accessing and managing tools.
        """
        self.workspace_path = workspace_path
        self.llm_factory = llm_factory
        self.tool_service = tool_service
        
        # Create components
        self.meta_planner = MetaPlanner(llm_factory)
        self.build_environment = BuildEnvironment(workspace_path)
        self.testing_framework = TestingFramework(workspace_path, llm_factory)
        self.feedback_analyzer = FeedbackAnalyzer(llm_factory)
        self.agent_manager = AgentManager(llm_factory, tool_service)
        
        # Initialize state
        self.project_id: Optional[str] = None
        self.project_name: Optional[str] = None
        self.project_description: Optional[str] = None
        self.execution_plan: Optional[Dict[str, Any]] = None
        self.current_status: str = "idle"
        self.progress_callbacks: List[Callable[[str, int, str], None]] = [] # Callback signature updated
        self.project_files: List[str] = []
        self.service_urls: List[str] = []
        self.current_iteration: int = 0
        self.max_iterations: int = 5 
        self.externally_reported_errors: List[Dict[str, Any]] = [] 
        self.agents: Dict[str, GeneralAgent] = {} # Type hint for clarity

        # Enhanced progress and error logging
        self.progress_log: List[Dict[str, Any]] = [] 
        self.internal_errors: List[Dict[str, Any]] = [] # Will be deprecated or used for truly internal engine issues not fitting DetailedIssue
        self.detailed_issue_log: List[DetailedIssue] = [] # New centralized issue log

        # Thread for background execution
        self.execution_thread: Optional[threading.Thread] = None
        self.execution_stopped: bool = False
        
    def _log_issue(self, issue_data: Dict[str, Any]) -> DetailedIssue:
        """
        Logs a detailed issue to the centralized issue log.
        Validates data against DetailedIssue schema, assigns ID and timestamp if needed.
        """
        # Ensure project_id is present, fallback to current engine's project_id if available
        if 'project_id' not in issue_data and self.project_id:
            issue_data['project_id'] = self.project_id
        elif 'project_id' not in issue_data:
            # If no project_id in data and engine has no project_id (e.g. pre-init error)
            # Pydantic will raise validation error if project_id is mandatory and not provided.
            # Or, we can assign a placeholder or handle as a truly "internal" unassociated error.
            # For now, let Pydantic handle it based on schema definition.
            pass

        try:
            # Add default timestamp if not present
            if 'timestamp' not in issue_data:
                issue_data['timestamp'] = datetime.datetime.now(datetime.timezone.utc) # Use timezone-aware UTC

            # Pydantic will handle issue_id generation if not provided, via default_factory
            detailed_issue = DetailedIssue(**issue_data)
            self.detailed_issue_log.append(detailed_issue)
            
            # Optional: print to console for immediate visibility, similar to _log_internal_error
            print(f"DETAILED ISSUE logged: ID={detailed_issue.issue_id}, Source='{detailed_issue.source_component}', Type='{detailed_issue.type}', Message='{detailed_issue.message}'")
            
            return detailed_issue
        except Exception as e: # Catch Pydantic validation errors or other issues
            # Fallback to old internal error logging if DetailedIssue creation fails
            error_message = f"Failed to log DetailedIssue: {str(e)}. Original data: {issue_data}"
            self._log_internal_error("log_detailed_issue_failure", error_message, e, details=issue_data)
            # Depending on policy, we might want to raise this or return a dummy/error object
            # For now, we've logged it via the old mechanism.
            # To fulfill the return type, we could raise or return a specially marked DetailedIssue if possible,
            # but that complicates the caller's error handling.
            # Raising an exception might be cleaner if logging is critical.
            raise ValueError(f"Failed to create DetailedIssue: {error_message}") from e

    def _log_internal_error(self, step: str, message: str, exception_obj: Optional[Exception] = None, details: Optional[Any] = None):
        """Logs an internal error encountered by the engine."""
        timestamp = datetime.datetime.now().isoformat()
        error_entry = {
            "timestamp": timestamp,
            "step": step,
            "message": message,
            "exception_type": str(type(exception_obj).__name__) if exception_obj else None,
            "exception_message": str(exception_obj) if exception_obj else None,
            # "stack_trace": traceback.format_exc() if exception_obj else None, # Potentially too verbose for API status
            "details": details
        }
        # self.internal_errors.append(error_entry) # Deprecate direct append
        # Keep only the last N internal errors if desired, e.g., last 20
        # if len(self.internal_errors) > 20:
        #     self.internal_errors = self.internal_errors[-20:]
        
        # Log through the new system
        issue_data = {
            "project_id": self.project_id if self.project_id else "unknown_project",
            "source_component": "OrchestrationEngine.Internal",
            "phase": step, # Use 'step' as 'phase' for internal errors
            "severity": "high", # Assume internal errors are at least high severity
            "type": "InternalEngineError",
            "message": message,
            "description": f"Exception: {str(exception_obj)}" if exception_obj else None,
            "stack_trace": traceback.format_exc() if exception_obj else None,
            "additional_data": details
        }
        try:
            self._log_issue(issue_data)
        except ValueError as log_e:
            # If _log_issue itself fails, print to console as a last resort
            print(f"CRITICAL: Failed to log internal error via _log_issue and old mechanism. Error: {log_e}")
            print(f"Original internal error: Step='{step}', Message='{message}', Exception='{exception_obj}'")
            # Optionally, append to a very raw failsafe log if this path is hit
            self.internal_errors.append(error_entry) # Fallback to old list if new system fails
            if len(self.internal_errors) > 20:
                 self.internal_errors = self.internal_errors[-20:]


        # Also print to console for immediate developer visibility
        print(f"INTERNAL ENGINE ERROR logged at {timestamp} during '{step}': {message}" + (f" | Exception: {str(exception_obj)}" if exception_obj else ""))

    def _update_progress(self, message: str, percentage: int):
        """Updates progress and logs it."""
        timestamp = datetime.datetime.now().isoformat()
        # Clamp percentage between 0 and 100, or allow -1 for non-percentage updates
        if percentage != -1:
            clamped_percentage = max(0, min(100, percentage))
        else:
            clamped_percentage = -1 # Keep -1 as is

        log_entry = {"timestamp": timestamp, "message": message, "percentage": clamped_percentage}
        self.progress_log.append(log_entry)
        
        # Keep only the last N progress messages, e.g., last 50
        if len(self.progress_log) > 50:
            self.progress_log = self.progress_log[-50:]

        for callback in self.progress_callbacks:
            try:
                callback(message, clamped_percentage, timestamp) # Pass timestamp
            except Exception as e:
                # Log error in callback execution but don't let it stop the engine
                self._log_internal_error("progress_callback", f"Error in progress callback: {str(e)}", e)
    
    def initialize_project(self, project_description: str, project_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Initialize a new project based on the description.
        Resets most of the engine state for the new project.
        """
        # Reset state for a new project
        self.project_id = str(uuid.uuid4())
        self.project_name = project_name if project_name else f"project-{self.project_id[:8]}"
        self.project_description = project_description
        self.execution_plan = None
        self.current_status = "initializing" # Initial status
        self.project_files = []
        self.service_urls = []
        self.current_iteration = 0
        self.externally_reported_errors = []
        self.internal_errors = [] # Clear previous internal errors for the new project
        self.progress_log = []    # Clear previous progress log for the new project
        self.detailed_issue_log = [] # Clear detailed issues for the new project
        self.execution_stopped = False # Ensure execution_stopped is reset

        self._update_progress(f"Initializing project: {self.project_name}", 5)
        
        try:
            repo_result = self._initialize_repository()
            if not repo_result.get("success"):
                message = f"Failed to initialize repository: {repo_result.get('message')}"
                self._log_internal_error("initialize_project", message)
                self.current_status = "initialization_failed"
                return {"success": False, "project_id": self.project_id, "project_name": self.project_name, "message": message, "status": self.current_status}

            self.current_status = "initialized"
            self._update_progress("Project Initialized", 10)
            
            return {
                "success": True,
                "project_id": self.project_id,
                "project_name": self.project_name,
                "workspace_path": os.path.join(self.workspace_path, self.project_name), # Actual project path
                "status": self.current_status,
                "message": "Project initialized successfully."
            }
        except Exception as e:
            message = f"Critical error during project initialization: {str(e)}"
            self._log_internal_error("initialize_project", message, e)
            self.current_status = "initialization_failed_exception"
            return {"success": False, "project_id": self.project_id, "project_name": self.project_name, "message": message, "status": self.current_status}

    def _initialize_repository(self) -> Dict[str, Any]:
        """
        Initialize the code repository (directory structure, basic files).
        Returns a dictionary with 'success' and 'message'.
        """
        try:
            project_dir = os.path.join(self.workspace_path, self.project_name)
            if not os.path.exists(self.workspace_path):
                 os.makedirs(self.workspace_path, exist_ok=True) # Ensure base workspace exists
            if os.path.exists(project_dir):
                # Potentially add logic here to handle existing directories (e.g., clear, backup, or error)
                # For now, we'll overwrite, but this could be a point of failure or data loss.
                # Consider adding a timestamp or unique ID to project_dir if overwriting is not desired.
                pass # Allow re-initialization for now.
            
            os.makedirs(project_dir, exist_ok=True)
            os.makedirs(os.path.join(project_dir, "src"), exist_ok=True)
            os.makedirs(os.path.join(project_dir, "docs"), exist_ok=True)
            os.makedirs(os.path.join(project_dir, "tests"), exist_ok=True)
            
            readme_path = os.path.join(project_dir, "README.md")
            with open(readme_path, 'w') as f:
                f.write(f"# {self.project_name}\\n\\n{self.project_description}\\n")
            
            # Git initialization could go here
            # self.tool_service.run_bash_command(f"cd {project_dir} && git init && git add . && git commit -m 'Initial commit'")
            
            return {"success": True, "message": "Repository initialized.", "project_dir": project_dir}
        except Exception as e:
            return {"success": False, "message": f"Repository initialization error: {str(e)}"}
    
    def plan_project(self) -> Dict[str, Any]:
        """
        Plan the project using the MetaPlanner.
        Returns a dictionary with 'success', 'status', 'message', and 'execution_plan'.
        """
        if not self.project_id or self.current_status not in ["initialized", "error_reported", "planning_failed"]: # Allow retry if planning failed
            message = "Project must be initialized (or planning failed previously) before planning."
            # Not logging as internal error here as it's a state check, API layer should handle this.
            return {"success": False, "status": self.current_status, "message": message, "execution_plan": None}

        self.current_status = "planning"
        self._update_progress("Planning Started", 15)
        
        try:
            # Assuming MetaPlanner methods are robust or handle their own errors internally
            self.execution_plan = self.meta_planner.decompose_project(self.project_description)
            if not self.execution_plan or not isinstance(self.execution_plan, dict):
                raise ValueError("MetaPlanner.decompose_project returned invalid data.")

            components = self.execution_plan.get("components", [])
            layers = self.meta_planner.identify_layers(components)
            tasks = self.meta_planner.create_tasks(components)
            dependency_graph = self.meta_planner.build_dependency_graph(tasks)
            
            self.execution_plan.update({
                "layers": layers,
                "tasks": tasks,
                "dependency_graph": dependency_graph
            })
            
            scheduled_tasks = self._schedule_tasks(tasks, dependency_graph)
            self.execution_plan["scheduled_tasks"] = scheduled_tasks
            
            self.current_status = "planned"
            self._update_progress("Planning Complete", 20)
            
            return {"success": True, "status": self.current_status, "message": "Project planned successfully.", "execution_plan_summary": self._summarize_plan(self.execution_plan)}
        except Exception as e:
            error_message = f"Error during project planning: {str(e)}"
            self._log_internal_error("plan_project", error_message, e)
            self.current_status = "planning_failed"
            self._update_progress(error_message, 15) 
            return {"success": False, "status": self.current_status, "message": error_message, "execution_plan_summary": None}

    def _summarize_plan(self, plan: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if not plan:
            return None
        return {
            "has_plan": True,
            "component_count": len(plan.get("components", [])),
            "task_count": len(plan.get("tasks", [])),
            "layer_count": len(plan.get("layers", [])),
            "scheduled_task_count": len(plan.get("scheduled_tasks", [])),
        }

    def _schedule_tasks(self, tasks: List[Dict[str, Any]], dependency_graph: Dict[str, List[str]]) -> List[Dict[str, Any]]:
        """
        Schedule tasks based on dependencies.
        
        Args:
            tasks: List of tasks.
            dependency_graph: Task dependency graph.
            
        Returns:
            Scheduled tasks with execution order.
        """
        # Group tasks by layer
        tasks_by_layer = {
            "backend": [],
            "middleware": [],
            "design": [],
            "frontend": []
        }
        
        for task in tasks:
            layer = task.get("layer", "backend")
            tasks_by_layer[layer].append(task)
        
        # For each layer, sort tasks by dependencies
        scheduled_tasks = []
        
        # Add backend tasks first
        scheduled_tasks.extend([
            {**task, "execution_order": len(scheduled_tasks) + i + 1} 
            for i, task in enumerate(tasks_by_layer["backend"])
        ])
        
        # Add middleware tasks
        scheduled_tasks.extend([
            {**task, "execution_order": len(scheduled_tasks) + i + 1} 
            for i, task in enumerate(tasks_by_layer["middleware"])
        ])
        
        # Add design tasks
        scheduled_tasks.extend([
            {**task, "execution_order": len(scheduled_tasks) + i + 1} 
            for i, task in enumerate(tasks_by_layer["design"])
        ])
        
        # Add frontend tasks
        scheduled_tasks.extend([
            {**task, "execution_order": len(scheduled_tasks) + i + 1} 
            for i, task in enumerate(tasks_by_layer["frontend"])
        ])
        
        return scheduled_tasks
    
    def generate_code(self, async_execution: bool = True) -> Dict[str, Any]:
        """
        Generate code for the project. Can be run sync or async.
        Returns a dictionary indicating status or thread info.
        """
        if self.current_status != "planned":
            message = f"Project must be in 'planned' state to generate code. Current status: {self.current_status}"
            # Not an internal engine error, but a state precondition for the API.
            return {"success": False, "status": "error_state_precondition", "message": message}

        if async_execution:
            if self.execution_thread and self.execution_thread.is_alive():
                return {"success": False, "status": "already_running", "message": "Code generation is already running in the background."}
            
            self.execution_stopped = False # Ensure it's reset before starting a new thread
            self.execution_thread = threading.Thread(target=self._generate_code_thread_wrapper) # Use a wrapper
            self.execution_thread.daemon = True # Allow main program to exit even if thread is running
            self.execution_thread.start()
            
            self.current_status = "generation_started_async" # Update status immediately for async
            return {
                "success": True,
                "status": self.current_status,
                "message": "Code generation started in background.",
                "thread_id": self.execution_thread.ident
            }
        else:
            self.execution_stopped = False # Reset for synchronous run
            return self._generate_code_execution() # Directly call and return its result

    def _generate_code_thread_wrapper(self):
        """Wrapper for the thread to ensure status updates on completion/error."""
        # Result not directly used here, but _generate_code_execution updates engine state
        result = self._generate_code_execution()
        # Status (completed, failed, etc.) is set by _generate_code_execution
        if not result.get("success"):
            # Error should have been logged by _generate_code_execution
            print(f"Async code generation finished with error: {result.get('message')}")
        else:
            print(f"Async code generation finished with status: {self.current_status}")


    def _generate_code_execution(self) -> Dict[str, Any]:
        """
        Synchronous execution of the code generation workflow.
        Returns a comprehensive result dictionary.
        """
        # Redundant check if called from generate_code, but good for direct calls or safety
        if self.current_status != "planned" and self.current_status != "generation_started_async": 
             message = f"Project must be in 'planned' or 'generation_started_async' state. Current: {self.current_status}"
             # Not logging as internal, this is a state check.
             return {"success": False, "status": self.current_status, "message": message}
            
        self.current_status = "generating" # Main status for the active generation phase
        self._update_progress("Code Generation Process Started", 25)
        
        final_result = {"success": False, "message": "Code generation did not complete."} # Default
        try:
            self._initialize_agents() # Should be idempotent or safe to call multiple times
            
            tasks_by_layer = {layer: [] for layer in ["backend", "middleware", "design", "frontend"]}
            for task in self.execution_plan.get("scheduled_tasks", []):
                tasks_by_layer.setdefault(task.get("layer", "backend"), []).append(task)

            layer_generation_results = {}
            generation_order = ["backend", "middleware", "design", "frontend"]
            base_progress = 25

            for i, layer_name in enumerate(generation_order):
                if self.execution_stopped:
                    self.current_status = "stopped"
                    self._update_progress("Execution stopped by request during code generation.", base_progress)
                    final_result = {"success": False, "status": "stopped", "message": "Execution was stopped during layer generation."}
                    return final_result # Exit early

                self._update_progress(f"Generating code for {layer_name} layer...", base_progress + i * 6) # Approx 6% per layer block
                layer_result = self._generate_layer_code(layer_name, tasks_by_layer.get(layer_name, []))
                layer_generation_results[layer_name] = layer_result
                
                if not layer_result.get("success"):
                    # Error already logged by _generate_layer_code
                    self.current_status = f"{layer_name}_generation_failed" # Specific status
                    self._update_progress(f"Failed to generate code for {layer_name} layer. Reason: {layer_result.get('message', 'Unknown')}", base_progress + i * 6)
                    final_result = {"success": False, "status": self.current_status, "message": f"Failed at {layer_name} layer: {layer_result.get('message')}", "details": layer_generation_results}
                    return final_result # Exit early

            if self.execution_stopped: # Check again after loop
                self.current_status = "stopped"
                self._update_progress("Execution stopped by request after layer generation loop.", base_progress + len(generation_order) * 6)
                return {"success": False, "status": "stopped", "message": "Execution was stopped."}

            self._update_progress("All layer code generation completed.", 50)
            self._commit_changes("Post-layer code generation")
            self.project_files = self._collect_project_files() # Update file list

            # --- Build, Test, Refine Cycle ---
            current_progress = 50
            build_result = self._build_project()
            current_progress = 65
            if not build_result.get("success"):
                # Error logged in _build_project, status updated there
                # No need to log again here, _build_project should use _log_issue
                return {"success": False, "status": self.current_status, "message": f"Build failed: {build_result.get('message')}", "details": {"build": build_result}}

            service_result = self._start_services()
            current_progress = 70
            if not service_result.get("success"):
                # Error logged, status updated
                # No need to log again here, _start_services should use _log_issue
                return {"success": False, "status": self.current_status, "message": f"Service start failed: {service_result.get('message')}", "details": {"services": service_result}}
            self.service_urls = service_result.get("service_urls", [])
            
            test_result = self._run_tests()
            current_progress = 80
            # _run_tests returns success=True if tests ran, issues_found indicates test failures
            # success=False from _run_tests means the testing framework itself failed
            if not test_result.get("success"): # Framework error
                # _run_tests should have logged this via _log_issue
                return {"success": False, "status": self.current_status, "message": f"Testing phase failed: {test_result.get('message')}", "details": {"testing": test_result}}

            if test_result.get("issues_found"):
                self._update_progress("Test issues found, proceeding to analysis and refinement.", current_progress)
                analysis_result = self._analyze_results(test_result) # Pass the full test_result
                current_progress = 85
                if not analysis_result.get("success"): # Analysis process error
                     # _analyze_results should have logged this
                     return {"success": False, "status": self.current_status, "message": f"Result analysis failed: {analysis_result.get('message')}", "details": {"analysis": analysis_result}}

                if analysis_result.get("issues_found"): # Should be true if test_result.issues_found was true
                    refinement_result = self._run_refinement_loop(analysis_result)
                    # Status (completed, failed, etc.) is set by _run_refinement_loop
                    final_result = refinement_result # This will have success:True/False and final status
                else: # Analysis found no actionable issues despite test_result.issues_found (should be rare)
                    self._log_issue({ # Log this inconsistency
                        "project_id": self.project_id,
                        "source_component": "OrchestrationEngine.CodeGeneration",
                        "phase": "PostTestAnalysis",
                        "severity": "medium",
                        "type": "LogicError",
                        "message": "Analysis reported no issues, but tests indicated issues. Contradiction.",
                        "additional_data": analysis_result
                    })
                    self.current_status = "completed_with_unverified_test_issues"
                    final_result = {"success": True, "status": self.current_status, "message": "Tests reported issues, but analysis found no actionable items. Manual review suggested."}
            else: # Tests passed, no issues found
                self.current_status = "completed"
                self._update_progress("Project Completed: All tests passed.", 100)
                final_result = {"success": True, "status": self.current_status, "message": "Project generated and tested successfully."}
            
            return final_result

        except Exception as e:
            error_message = f"Unhandled critical error during code generation process: {str(e)}"
            self._log_internal_error("_generate_code_execution", error_message, e)
            self.current_status = "generation_failed_uncaught_exception" # More specific
            self._update_progress(error_message, 0) # Reset progress or indicate critical failure
            return {"success": False, "status": self.current_status, "message": error_message}
    
    def _initialize_agents(self):
        """Initializes specialized agents if not already done. Idempotent."""
        if not self.agents: # Only initialize if agents dict is empty
            try:
                # Using a single LLM instance for all agents for simplicity here
                # In a more complex setup, each agent could have a differently configured LLM
                common_llm = self.llm_factory.create_llm(provider="gemini", model_name="gemini-1.5-pro") # Example
                available_tools = self.tool_service.get_tools() # Assuming this returns a list of tool instances

                agent_configs = {
                    "backend": "You are a backend development specialist...",
                    "middleware": "You are a middleware development specialist...",
                    "design": "You are a UI/UX design specialist...",
                    "frontend": "You are a frontend development specialist..."
                }
                for agent_name, system_prompt in agent_configs.items():
                    if agent_name not in self.agents: # Double check, though outer if should cover
                        self.agents[agent_name] = GeneralAgent(
                            llm=common_llm,
                            tools=available_tools, # Provide tools
                            system_prompt=system_prompt,
                            name=f"{agent_name.capitalize()}Agent",
                            verbose=True # Or configure verbosity
                        )
                self._update_progress("Specialized agents initialized.", -1) # -1 for no specific percentage
            except Exception as e:
                self._log_internal_error("_initialize_agents", f"Failed to initialize agents: {str(e)}", e)
                self.current_status = "agent_initialization_failed"
                # This is a critical failure for code generation.
                # Consider how to propagate this error to stop generation if it occurs mid-process.
                raise # Re-raise to stop the process if agents can't be initialized.
    
    def _generate_layer_code(self, layer: str, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generates code for a specific layer.
        Returns a dict with 'success', 'status', 'message', 'files_generated'.
        """
        if not tasks:
            return {"success": True, "status": "skipped", "message": f"No tasks for {layer} layer.", "files_generated": 0}
            
        agent = self.agents.get(layer) # Get pre-initialized agent
        if not agent:
            message = f"Agent for layer '{layer}' not initialized or found."
            self._log_internal_error(f"_generate_layer_code ({layer})", message)
            return {"success": False, "status": "error_agent_missing", "message": message, "files_generated": 0}
            
        files_generated_this_layer = 0
        layer_task_results = []

        try:
            for task_idx, task in enumerate(tasks):
                if self.execution_stopped:
                    return {"success": False, "status": "stopped", "message": f"Execution stopped during {layer} task processing."}

                self._update_progress(f"Processing task {task_idx+1}/{len(tasks)} for {layer}: {task.get('description','Unnamed task')[:40]}...", -1)
                
                task_context = self._build_task_context(task) # Assuming this is robust
                # Construct a more detailed prompt if necessary
                prompt = f"Project: {self.project_name}\\nLayer: {layer}\\nTask: {task.get('description')}\\nDetails: {json.dumps(task_context, indent=2)}\\nGenerate necessary code files."

                # --- Agent Interaction ---
                # This is highly dependent on how GeneralAgent.run() is implemented
                # and what it returns. Assuming it returns a list of file dicts or throws an error.
                # Example: agent_response = [{"path": "src/file.py", "content": "print('hello')"}]
                agent_response_files = agent.run(prompt) # This needs to be robust

                if not isinstance(agent_response_files, list): # Expecting a list of file dicts
                    raise ValueError(f"Agent for {layer} returned unexpected response type: {type(agent_response_files)}. Expected list of file dicts.")

                for file_info in agent_response_files:
                    if self.execution_stopped: break
                    if not isinstance(file_info, dict) or "path" not in file_info or "content" not in file_info:
                        self._log_internal_error(f"_generate_layer_code ({layer})", f"Malformed file info from agent: {file_info}", details=task)
                        continue # Skip malformed file entry

                    try:
                        actual_file_path = self._save_code_to_file(file_info["path"], file_info["content"])
                        layer_task_results.append({"file_path": actual_file_path, "task_description": task.get('description'), "status": "created"})
                        files_generated_this_layer += 1
                    except Exception as e_save: # Catch error during saving a specific file
                        self._log_internal_error(f"_generate_layer_code ({layer})", f"Failed to save file {file_info['path']}: {str(e_save)}", e_save, details=task)
                        # Decide if one file failing should fail the whole layer. For now, log and continue.
                        layer_task_results.append({"file_path": file_info["path"], "task_description": task.get('description'), "status": "save_failed", "error": str(e_save)})


            if self.execution_stopped:
                 return {"success": False, "status": "stopped", "message": f"Execution stopped during {layer} code generation."} # No files_generated here as it's incomplete

            return {"success": True, "status": "completed", "message": f"{layer} code generated successfully.", "files_generated": files_generated_this_layer, "details": layer_task_results}
        
        except Exception as e: # Catch errors from agent.run() or other unexpected issues
            error_message = f"Critical error generating code for {layer} layer task: {str(e)}"
            self._log_internal_error(f"_generate_layer_code ({layer})", error_message, e)
            return {"success": False, "status": f"{layer}_task_processing_failed", "message": error_message, "files_generated": files_generated_this_layer}

    def _build_task_context(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build context information for a task.
        
        Args:
            task: Task information.
            
        Returns:
            Task context.
        """
        project_dir = os.path.join(self.workspace_path, self.project_name)
        dependencies = task.get("dependencies", [])
        
        # For related_files, we can start by listing all files in the src directory
        # or all currently known project files. A more sophisticated approach would
        # trace files generated by dependent tasks.
        related_files = []
        src_dir = os.path.join(project_dir, "src")
        if os.path.exists(src_dir):
            for root, _, filenames in os.walk(src_dir):
                for filename in filenames:
                    related_files.append(os.path.relpath(os.path.join(root, filename), project_dir))
        
        # If no files in src, fall back to all project files collected so far
        if not related_files:
            related_files = self.project_files[:]

        return {
            "task_id": task.get("id"),
            "task_type": task.get("type"),
            "description": task.get("description"),
            "layer": task.get("layer"),
            "dependencies": dependencies,
            "related_files": related_files, # Files potentially relevant to the task
            "current_project_structure": self._get_project_structure(), # Overall structure
            "project_description": self.project_description
        }

    def _get_project_structure(self, max_depth: int = 3) -> Dict[str, Any]:
        """
        Get the directory structure of the project.

        Args:
            max_depth: Maximum depth to traverse.

        Returns:
            Directory structure.
        """
        project_dir = os.path.join(self.workspace_path, self.project_name)
        structure = {}
        if not os.path.exists(project_dir):
            return {"error": "Project directory does not exist."}

        for root, dirs, files in os.walk(project_dir, topdown=True):
            # Calculate current depth
            depth = root.replace(project_dir, '').count(os.sep)
            if depth >= max_depth:
                dirs[:] = [] # Don't go deeper

            # Get relative path from project_dir
            relative_root = os.path.relpath(root, project_dir)
            if relative_root == ".": # Root of the project
                current_level = structure
            else:
                parts = relative_root.split(os.sep)
                current_level = structure
                for part in parts:
                    current_level = current_level.setdefault(part, {})
            
            for d in dirs:
                if depth + 1 < max_depth: # Only add dir if not exceeding depth
                     current_level.setdefault(d, {})
                else: # Mark that there's more but not showing
                    current_level.setdefault(d, {"...": "max_depth_reached"})

            for f_name in files:
                current_level[f_name] = "file"
        
        return structure
    
    def _save_code_to_file(self, relative_file_path: str, content: str) -> str:
        """
        Save generated code to a file, relative to the project root.
        
        Args:
            relative_file_path: Relative path to the file within the project.
            content: File content.
            
        Returns:
            Absolute saved file path.
        """
        if not self.project_name:
            raise ValueError("Project name is not set. Cannot save file.")
            
        project_root_dir = os.path.join(self.workspace_path, self.project_name)
        # Sanitize relative_file_path to prevent escaping the project directory
        # os.path.normpath helps resolve ".." but we should ensure it doesn't go above project_root_dir
        # A simple way is to ensure it doesn't start with ".." or an absolute path indicator
        if os.path.isabs(relative_file_path) or relative_file_path.startswith((".."+os.sep, os.sep)):
            raise ValueError(f"Invalid relative_file_path: {relative_file_path}. Must be relative and within project.")

        absolute_file_path = os.path.join(project_root_dir, relative_file_path)
        
        # Ensure the path is truly within the project_root_dir after joining
        if not os.path.abspath(absolute_file_path).startswith(os.path.abspath(project_root_dir)):
            raise ValueError(f"File path {absolute_file_path} attempts to escape project directory {project_root_dir}.")

        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(absolute_file_path), exist_ok=True)
        
        # Write file
        with open(absolute_file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        self._update_progress(f"File saved: {relative_file_path}", -1)
        # Add to project_files if not already there (using relative path)
        if relative_file_path not in self.project_files:
            self.project_files.append(relative_file_path)
            self.project_files.sort() # Keep it sorted for consistency

        return absolute_file_path
    
    def _commit_changes(self, message: str):
        """
        Commit changes to the repository using Git.
        
        Args:
            message: Commit message.
        """
        if not self.project_name:
            self._log_internal_error("_commit_changes", "Project name not set, cannot commit.")
            return

        project_dir = os.path.join(self.workspace_path, self.project_name)

        # Check if it's a git repository
        is_git_repo_check_command = f"cd \"{project_dir}\" && git rev-parse --is-inside-work-tree"
        # Use a simplified way to check command success if tool_service doesn't directly return it
        # This part depends on the exact return signature of tool_service.run_bash_command
        # Assuming it returns a dict like {"success": bool, "output": str, "error": str}
        
        # For now, let's assume tool_service.run_bash_command returns a tuple (success_bool, output_str)
        # or a dict. We need to adapt to its actual API.
        # Let's assume a dict: {'stdout': '...', 'stderr': '...', 'exit_code': 0}
        
        # Initialize git if not already initialized (idempotent)
        # This should ideally be part of _initialize_repository
        init_command = f'cd "{project_dir}" && git init'
        init_result = self.tool_service.run_bash_command(init_command)
        if init_result.get('exit_code', 1) != 0 and "Reinitialized existing Git repository" not in init_result.get('stdout', '') and "Initialised empty Git repository" not in init_result.get('stdout', ''): # Check for non-zero exit code
            self._log_issue({
                "project_id": self.project_id,
                "source_component": "OrchestrationEngine.GitService",
                "phase": "VersionControl",
                "severity": "warning", 
                "type": "GitOperationError",
                "message": f"Git init failed or project directory not found.",
                "additional_data": {"command": init_command, "stdout": init_result.get('stdout',''), "stderr": init_result.get('stderr','')}
            })

        add_command = f'cd "{project_dir}" && git add .'
        add_result = self.tool_service.run_bash_command(add_command)
        
        if add_result.get('exit_code', 1) != 0:
            self._log_internal_error("_commit_changes", f"git add . failed. Output: {add_result.get('stdout','')}, Error: {add_result.get('stderr','')}", details={"command": add_command})
            self._update_progress(f"Git add failed: {add_result.get('stderr','')}", -1)
            return # Stop if add fails

        commit_command = f'cd "{project_dir}" && git commit -m "{message}"'
        commit_result = self.tool_service.run_bash_command(commit_command)

        if commit_result.get('exit_code', 1) == 0:
            self._update_progress(f"Changes committed: {message}", -1)
        else:
            # Handle cases like "nothing to commit" which might not be an error (exit code 1 for git commit sometimes)
            if "nothing to commit" in commit_result.get('stdout','').lower() or "no changes added to commit" in commit_result.get('stdout','').lower():
                self._update_progress(f"No changes to commit: {message}", -1)
            else:
                # self._log_internal_error("_commit_changes", f"git commit failed. Output: {commit_result.get('stdout','')} Error: {commit_result.get('stderr','')}", details={"command": commit_command, "message": message}) # Replaced
                self._log_issue({
                    "project_id": self.project_id,
                    "source_component": "OrchestrationEngine.GitService",
                    "phase": "VersionControl",
                    "severity": "warning",
                    "type": "GitOperationError",
                    "message": f"git commit failed.",
                    "additional_data": {"command": commit_command, "commit_message": message, "stdout": commit_result.get('stdout',''), "stderr": commit_result.get('stderr','')}
                })
                self._update_progress(f"Git commit failed: {commit_result.get('stderr','')}", -1)

    def _collect_project_files(self) -> List[str]:
        """
        Collect all files in the project.
        
        Returns:
            List of file paths.
        """
        project_dir = os.path.join(self.workspace_path, self.project_name)
        files = []
        
        for root, _, filenames in os.walk(project_dir):
            for filename in filenames:
                rel_path = os.path.relpath(os.path.join(root, filename), project_dir)
                files.append(rel_path)
                
        return files
    
    def _build_project(self) -> Dict[str, Any]:
        """
        Build the project.
        
        Returns:
            Build result.
        """
        self.current_status = "building"
        self._update_progress("Building Project...", 60)
        try:
            project_dir = os.path.join(self.workspace_path, self.project_name)
            # Simulate build: e.g., run a build script if defined in execution_plan
            # build_command = self.execution_plan.get("build_config", {}).get("build_command")
            # if build_command:
            #     success, output = self.tool_service.run_bash_command(f"cd {project_dir} && {build_command}")
            #     if not success:
            #         raise Exception(f"Build command failed: {output}")
            # else: # Simple check if no build command
            if not os.path.exists(os.path.join(project_dir, "src")): # Basic check
                 # raise FileNotFoundError("Build check failed: 'src' directory not found.")
                 self._log_issue({
                     "project_id": self.project_id,
                     "source_component": "OrchestrationEngine.BuildProcess",
                     "phase": "Build",
                     "severity": "critical",
                     "type": "BuildFailure",
                     "message": "Build check failed: 'src' directory not found.",
                     "file_path": "src" # Or project_dir if more appropriate
                 })
                 self.current_status = "build_failed"
                 self._update_progress("Build failed: 'src' directory not found.", 60)
                 return {"success": False, "message": "Build failed: 'src' directory not found."}
            
            time.sleep(0.5) # Simulate build
            self._update_progress("Build Successful", 65)
            return {"success": True, "message": "Build completed successfully."}
        except Exception as e:
            error_message = f"Build failed: {str(e)}"
            # self._log_internal_error("_build_project", error_message, e) # Replaced by _log_issue
            self._log_issue({
                "project_id": self.project_id,
                "source_component": "OrchestrationEngine.BuildProcess",
                "phase": "Build",
                "severity": "critical",
                "type": "BuildFailure",
                "message": error_message,
                "description": f"Exception: {str(e)}",
                "stack_trace": traceback.format_exc()
            })
            self.current_status = "build_failed" # Set specific status
            self._update_progress(error_message, 60) # Update progress with error
            return {"success": False, "message": error_message}

    def _start_services(self) -> Dict[str, Any]:
        self.current_status = "starting_services"
        self._update_progress("Starting Services...", 68)
        try:
            # service_commands = self.execution_plan.get("deploy_config", {}).get("start_commands", [])
            # For now, simulate
            time.sleep(0.5)
            simulated_urls = [f"http://localhost:8000/{self.project_name}/api"]
            self.service_urls = simulated_urls # Update engine state
            self._update_progress("Services Started", 70)
            return {"success": True, "message": "Services started successfully.", "service_urls": self.service_urls}
        except Exception as e:
            error_message = f"Failed to start services: {str(e)}"
            # self._log_internal_error("_start_services", error_message, e) # Replaced
            self._log_issue({
                "project_id": self.project_id,
                "source_component": "OrchestrationEngine.ServiceDeployment",
                "phase": "Deployment", # Or "ServiceStart"
                "severity": "critical",
                "type": "RuntimeError", # Or "DeploymentFailure"
                "message": error_message,
                "description": f"Exception: {str(e)}",
                "stack_trace": traceback.format_exc()
            })
            self.current_status = "services_start_failed"
            self._update_progress(error_message, 68)
            return {"success": False, "message": error_message, "service_urls": []}

    def _run_tests(self) -> Dict[str, Any]:
        self.current_status = "testing"
        self._update_progress("Running Tests...", 75)
        try:
            # Assuming testing_framework.execute_unit_tests() is robust
            # and returns a dict like: {"success": <bool_framework_ok>, "issues_found": <bool_tests_failed>, "summary": "...", "details": [...]}
            test_run_output = self.testing_framework.execute_unit_tests() 

            if not isinstance(test_run_output, dict) or "success" not in test_run_output or "issues_found" not in test_run_output:
                # raise ValueError("Test framework returned an invalid response format.")
                self._log_issue({
                    "project_id": self.project_id,
                    "source_component": "OrchestrationEngine.TestingFrameworkInterface",
                    "phase": "TestExecution",
                    "severity": "critical",
                    "type": "ContractViolation", # Or "InternalError"
                    "message": "Test framework returned an invalid response format.",
                    "additional_data": {"response": test_run_output}
                })
                self.current_status = "testing_framework_error"
                self._update_progress("Testing framework error: Invalid response.", 75)
                return {"success": False, "issues_found": True, "message": "Test framework error: Invalid response."}


            summary = test_run_output.get("summary", "No summary provided.")
            if not test_run_output["success"]: # Framework itself failed
                message = f"Testing framework execution failed: {summary}"
                # self._log_internal_error("_run_tests", message, details=test_run_output) # Replaced
                self._log_issue({
                    "project_id": self.project_id,
                    "source_component": "TestingFramework", # Source is the framework itself
                    "phase": "TestExecution",
                    "severity": "critical",
                    "type": "TestFrameworkFailure",
                    "message": message,
                    "additional_data": test_run_output
                })
                self.current_status = "testing_framework_error"
                self._update_progress(message, 75)
                return {"success": False, "issues_found": True, "message": message, "details": test_run_output}
            
            if test_run_output["issues_found"]:
                self.current_status = "tests_completed_with_failures"
                self._update_progress(f"Tests Completed: Issues found. Summary: {summary}", 78)
                # Success is True because the test process ran, but issues_found is True for refinement
                return {"success": True, "issues_found": True, "message": f"Tests ran, issues found: {summary}", "details": test_run_output}
            
            # Tests ran successfully and all passed
            self.current_status = "tests_passed"
            self._update_progress(f"All Tests Passed Successfully. Summary: {summary}", 80)
            return {"success": True, "issues_found": False, "message": f"All tests passed: {summary}", "details": test_run_output}

        except Exception as e:
            error_message = f"Exception during testing phase: {str(e)}"
            # self._log_internal_error("_run_tests", error_message, e) # Replaced
            self._log_issue({
                "project_id": self.project_id,
                "source_component": "OrchestrationEngine.TestRunner",
                "phase": "TestExecution",
                "severity": "critical",
                "type": "TestExecutionError",
                "message": error_message,
                "description": f"Exception: {str(e)}",
                "stack_trace": traceback.format_exc()
            })
            self.current_status = "testing_exception"
            self._update_progress(error_message, 75)
            # If an exception occurs, assume tests effectively failed or couldn't run
            return {"success": False, "issues_found": True, "message": error_message}


    def _analyze_results(self, test_result_details: Dict[str, Any]) -> Dict[str, Any]:
        """Analyzes test results (if issues were found) to prepare for refinement."""
        self.current_status = "analyzing_test_results"
        self._update_progress("Analyzing Test Results...", 82)
        
        try: # ADDED try statement
            # The input `test_result_details` is the raw output from `_run_tests`.
            # We need to transform its `details` (which should contain test failures)
            # into a list of `DetailedIssue` objects before passing to `feedback_analyzer`.

            issues_for_analyzer: List[DetailedIssue] = []
            
            # Example transformation (highly dependent on `testing_framework` output structure):
            # This assumes `test_result_details['details']['failures']` is a list of failure dicts
            raw_failures = test_result_details.get("details", {}).get("failures", [])
            if isinstance(raw_failures, list):
                for failure in raw_failures:
                    try:
                        issue_data = {
                            "project_id": self.project_id,
                            "source_component": "TestingFramework.UnitTests", # Or determine from failure data
                            "phase": "UnitTest", # Or determine from failure data
                            "severity": "high", # Default, could be parsed from failure
                            "type": failure.get("type", "TestFailure"),
                            "message": failure.get("message", "Test failed"),
                            "description": failure.get("description"),
                            "file_path": failure.get("file_path"),
                            "line_number": failure.get("line_number"),
                            "function_name": failure.get("test_name"), # Or function_name
                            "stack_trace": failure.get("stack_trace"),
                            "expected_behavior": failure.get("expected"),
                            "actual_behavior": failure.get("actual")
                            # Add other fields if available from test output
                        }
                        # Log it to the main log first
                        logged_issue = self._log_issue(issue_data)
                        issues_for_analyzer.append(logged_issue)
                    except ValueError as e: # Catch if _log_issue fails for a specific failure
                        print(f"Could not transform or log test failure as DetailedIssue: {e}. Failure data: {failure}")
                        # Optionally log this transformation problem itself as another issue
                        self._log_issue({
                            "project_id": self.project_id,
                            "source_component": "OrchestrationEngine.ResultAnalyzer",
                            "phase": "AnalysisPreparation",
                            "severity": "medium",
                            "type": "DataTransformationError",
                            "message": f"Failed to transform test failure to DetailedIssue: {e}",
                            "additional_data": {"raw_failure": failure}
                        })
                    except Exception as e_gen: # Catch any other unexpected error during transformation
                        print(f"Unexpected error transforming test failure: {e_gen}. Failure data: {failure}")
                        self._log_issue({
                            "project_id": self.project_id,
                            "source_component": "OrchestrationEngine.ResultAnalyzer",
                            "phase": "AnalysisPreparation",
                            "severity": "high",
                            "type": "UnexpectedError",
                            "message": f"Unexpected error transforming test failure: {e_gen}",
                            "additional_data": {"raw_failure": failure}
                        })


            # If `test_result_details` itself represents a framework failure (not just test failures),
            # we might need to create a `DetailedIssue` for that framework error as well, if not already logged by _run_tests.
            # For now, we assume _run_tests already logged critical framework failures.
            # We primarily focus on transforming actual test failures here.

            if not issues_for_analyzer and test_result_details.get("issues_found"):
                # This means _run_tests reported issues, but we couldn't transform them into DetailedIssue.
                # This situation should be logged.
                self._log_issue({
                    "project_id": self.project_id,
                    "source_component": "OrchestrationEngine.ResultAnalyzer",
                    "phase": "AnalysisPreparation",
                    "severity": "warning", # Or "error" depending on how critical this is
                    "type": "MissingTransformedIssues",
                    "message": "Test results indicated issues, but no specific failures were transformed for analysis.",
                    "additional_data": {"test_result_details": test_result_details}
                })
                # We might still proceed to feedback_analyzer if it can handle an empty list,
                # or return early indicating an issue with analysis preparation.
                # For now, let's allow feedback_analyzer to be called with an empty list if that's the case.

            # Current implementation: Pass issues derived from the current test run.
            # Future: Pass relevant subset of `self.detailed_issue_log`.
            # For now, we use `issues_for_analyzer` which are fresh from the current test run.
            
            if not issues_for_analyzer and not test_result_details.get("issues_found"):
                 # This case means _run_tests reported no issues, so no analysis needed.
                 self._update_progress("No test issues to analyze.", 85)
                 return {"success": True, "issues_found": False, "message": "No issues to analyze."}


            analysis = self.feedback_analyzer.classify_issues(
                issues_input=[issue.model_dump() for issue in issues_for_analyzer] # Pass as list of dicts
            )
            
            if not isinstance(analysis, dict) or "issues" not in analysis or "fix_tasks" not in analysis:
                 # raise ValueError("FeedbackAnalyzer.classify_issues returned an invalid response format.")
                 self._log_issue({
                    "project_id": self.project_id,
                    "source_component": "FeedbackAnalyzerInterface",
                    "phase": "ResultAnalysis",
                    "severity": "critical",
                    "type": "ContractViolation",
                    "message": "FeedbackAnalyzer.classify_issues returned an invalid response format.",
                    "additional_data": {"response": analysis}
                 })
                 self.current_status = "analysis_failed"
                 self._update_progress("Analysis failed: Invalid response from FeedbackAnalyzer.", 82)
                 return {"success": False, "issues_found": True, "message": "Analysis failed: Invalid response format."} # Assume issues if analysis fails

            # The `analysis['issues']` should be a list of *enriched* DetailedIssue objects (as dicts).
            # We need to update our main `self.detailed_issue_log` with these enriched versions.
            enriched_issue_dicts = analysis.get("issues", [])
            for enriched_dict in enriched_issue_dicts:
                issue_id_to_update = enriched_dict.get("issue_id")
                if issue_id_to_update:
                    for i, existing_issue in enumerate(self.detailed_issue_log):
                        if existing_issue.issue_id == issue_id_to_update:
                            try:
                                # Update existing issue with enriched data.
                                # Pydantic model_copy(update=...) is good for this.
                                updated_fields = {k: v for k, v in enriched_dict.items() if v is not None}
                                self.detailed_issue_log[i] = existing_issue.model_copy(update=updated_fields)
                                break 
                            except Exception as e_update:
                                print(f"Failed to update issue {issue_id_to_update} with enriched data: {e_update}")
                                self._log_issue({
                                    "project_id": self.project_id,
                                    "source_component": "OrchestrationEngine.ResultAnalyzer",
                                    "phase": "AnalysisUpdate",
                                    "severity": "warning",
                                    "type": "IssueUpdateFailed",
                                    "message": f"Failed to update issue {issue_id_to_update} with enriched data from FeedbackAnalyzer.",
                                    "additional_data": {"issue_id": issue_id_to_update, "error": str(e_update)}
                                })
            
            self._update_progress("Test Result Analysis Complete", 85)
            # issues_found should reflect if the analysis actually identified actionable issues
            # This is based on the enriched issues from the analyzer.
            final_issues_found = any(enriched_issue.get("status") != "resolved" and enriched_issue.get("status") != "ignored" for enriched_issue in enriched_issue_dicts)

            return {"success": True, "issues_found": final_issues_found, "analysis": analysis, "message": "Analysis complete."}
        except Exception as e:
            error_message = f"Error during test result analysis: {str(e)}"
            # self._log_internal_error("_analyze_results", error_message, e) # Replaced
            self._log_issue({
                "project_id": self.project_id,
                "source_component": "OrchestrationEngine.ResultAnalyzer",
                "phase": "ResultAnalysis",
                "severity": "critical",
                "type": "AnalysisExecutionError",
                "message": error_message,
                "description": f"Exception: {str(e)}",
                "stack_trace": traceback.format_exc()
            })
            self.current_status = "analysis_failed"
            self._update_progress(error_message, 82)
            return {"success": False, "issues_found": True, "message": error_message} # Assume issues if analysis fails

    def _run_refinement_loop(self, analysis_output: Dict[str, Any]) -> Dict[str, Any]:
        """Runs the refinement loop: refine code, build, test, analyze."""
        self.current_status = "refinement_loop_started"
        self._update_progress("Starting Refinement Loop", 88)
        
        current_analysis = analysis_output # The first analysis result
        
        for i in range(self.max_iterations):
            self.current_iteration = i + 1
            iteration_progress_start = 88 + int((i / self.max_iterations) * 10) # Rough progress
            self._update_progress(f"Refinement Iteration {self.current_iteration}/{self.max_iterations}", iteration_progress_start)

            if self.execution_stopped:
                self.current_status = "stopped"
                return {"success": False, "status": "stopped", "message": "Execution stopped during refinement loop."}

            # 1. Refine Code
            refinement_step_result = self._refine_code(
                current_analysis.get("analysis", {}).get("issues", []),
                current_analysis.get("analysis", {}).get("fix_tasks", [])
            )
            if not refinement_step_result.get("success"):
                self.current_status = f"refinement_iteration_{self.current_iteration}_code_refine_failed"
                # Error logged in _refine_code
                return {"success": False, "status": self.current_status, "message": f"Code refinement failed in iteration {self.current_iteration}: {refinement_step_result.get('message')}"}

            self._commit_changes(f"Code refinement iteration {self.current_iteration}")

            # 2. Build
            build_result = self._build_project()
            if not build_result.get("success"):
                self.current_status = f"refinement_iteration_{self.current_iteration}_build_failed"
                # Error logged in _build_project
                # Consider if we should try to analyze this build error and feed it back. For now, fail the iteration.
                return {"success": False, "status": self.current_status, "message": f"Build failed after refinement iteration {self.current_iteration}: {build_result.get('message')}"}
            
            # 3. Test
            test_result = self._run_tests()
            if not test_result.get("success"): # Test framework error
                self.current_status = f"refinement_iteration_{self.current_iteration}_testing_framework_error"
                return {"success": False, "status": self.current_status, "message": f"Testing framework failed after refinement iteration {self.current_iteration}: {test_result.get('message')}"}

            if not test_result.get("issues_found"): # All tests passed!
                self.current_status = "completed" # Issues resolved
                self._update_progress(f"Refinement Successful: All issues resolved after {self.current_iteration} iterations.", 100)
                return {"success": True, "status": self.current_status, "message": "Refinement completed, all issues resolved."}
            
            # Tests ran but still have issues, re-analyze for the next iteration
            self._update_progress(f"Iteration {self.current_iteration} tests completed with issues. Re-analyzing.", iteration_progress_start + 5)
            current_analysis = self._analyze_results(test_result) # Use the 'details' from test_result
            if not current_analysis.get("success"): # Analysis process itself failed
                self.current_status = f"refinement_iteration_{self.current_iteration}_analysis_failed"
                return {"success": False, "status": self.current_status, "message": f"Result analysis failed in refinement iteration {self.current_iteration}: {current_analysis.get('message')}"}
            
            if not current_analysis.get("issues_found"): # Analysis found no more actionable issues, but tests still failing (contradiction)
                 self._log_issue({ # Log this contradiction for investigation
                    "project_id": self.project_id,
                    "source_component": "OrchestrationEngine.RefinementLoop",
                    "phase": f"RefinementIteration_{self.current_iteration}",
                    "severity": "high",
                    "type": "ContradictoryAnalysis",
                    "message": "Analysis found no actionable issues, but tests still report failures.",
                    "additional_data": {
                        "test_result": test_result,
                        "analysis_result": current_analysis
                    }
                 })
                 self.current_status = "completed_with_unresolved_conflicting_analysis"
                 self._update_progress("Refinement loop ended: Analysis found no further actionable issues, but tests may still indicate problems.", 98)
                 return {"success": True, "status": self.current_status, "message": "Refinement ended due to conflicting test/analysis results."}


        if self.execution_stopped:
            self.current_status = "stopped"
            return {"success": False, "status": "stopped", "message": "Execution stopped during refinement (max iterations check)."}

        # Max iterations reached
        self.current_status = "completed_with_issues_max_iterations"
        self._update_progress("Max refinement iterations reached. Issues may persist.", 99)
        return {"success": False, "status": self.current_status, "message": "Max refinement iterations reached. Some issues might persist."}

    def _refine_code(self, issues: List[Dict[str, Any]], fix_tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Simulates refining code based on issues and fix_tasks.
        In a real system, this would involve targeted agent calls.
        Returns dict with 'success' and 'message'.
        """
        self._update_progress(f"Refining code for {len(issues)} issues and {len(fix_tasks)} fix tasks.", -1)
        try:
            if not issues and not fix_tasks:
                return {"success": True, "message": "No specific issues or fix tasks provided for refinement, assuming minor adjustments or re-evaluation."}

            # Simulate agent calls for each fix_task or issue
            # For example:
            # for task in fix_tasks:
            #     agent = self.agents.get(task.get("target_layer", "backend")) # Or a specialized "fixer" agent
            #     if agent:
            #         # Pass task details, relevant code snippets, error messages to agent
            #         # agent.run_fix_task(task_details=task, issue_context=issues)
            #         pass 
            time.sleep(1) # Simulate work
            
            self._update_progress("Code refinement attempt for current iteration completed.", -1)
            return {"success": True, "message": "Code refinement iteration completed (simulated)." }
        except Exception as e:
            error_message = f"Error during code refinement step: {str(e)}"
            self._log_internal_error("_refine_code", error_message, e)
            return {"success": False, "message": error_message}

    def register_progress_callback(self, callback: Callable[[str, int, str], None]): # Updated signature
        """Register a callback function for progress updates."""
        if callback not in self.progress_callbacks:
            self.progress_callbacks.append(callback)

    def get_status(self) -> Dict[str, Any]:
        """Get the current detailed status of the project and engine."""
        plan_summary = self._summarize_plan(self.execution_plan)
        
        return {
            "project_id": self.project_id,
            "project_name": self.project_name,
            "status": self.current_status,
            "current_iteration": self.current_iteration, # For refinement loop
            "execution_plan_summary": plan_summary,
            "project_files_count": len(self.project_files),
            "service_urls": self.service_urls,
            "externally_reported_errors_count": len(self.externally_reported_errors),
            "last_externally_reported_error": self.externally_reported_errors[-1] if self.externally_reported_errors else None,
            "internal_errors_count": len(self.internal_errors),
            "last_internal_error": self.internal_errors[-1] if self.internal_errors else None,
            "progress_log_summary": self.progress_log[-10:] if self.progress_log else [], # Last 10 progress messages
            "is_execution_active": self.execution_thread.is_alive() if self.execution_thread else False,
            "last_updated": datetime.datetime.now().isoformat()
        }
        
    def report_external_error(self, error_report: Dict[str, Any]) -> Dict[str, Any]:
        """
        Logs an error reported by an external component.
        Returns confirmation and suggested action.
        """
        timestamp = datetime.datetime.now().isoformat()
        component_name = error_report.get("component", "Unknown Component")
        error_message = error_report.get("error_message", "No error message provided.")
        
        logged_error = {
            "timestamp": timestamp,
            "project_id": self.project_id, 
            "reported_task_id": error_report.get("task_id"), # Could be None
            "component": component_name,
            "error_message": error_message,
            "details": error_report.get("details"),
            "status": "logged_external" # More specific status for this error entry
        }
        # self.externally_reported_errors.append(logged_error) # Deprecate direct append
        # if len(self.externally_reported_errors) > 20: # Limit stored external errors
        #     self.externally_reported_errors = self.externally_reported_errors[-20:]

        # Log through the new system
        issue_data_for_log = {
            "project_id": self.project_id if self.project_id else "unknown_project",
            "source_component": f"External.{component_name}",
            "phase": error_report.get("phase", "ExternalReport"), # Get phase from report or default
            "severity": error_report.get("severity", "high"), # Get severity or default
            "type": error_report.get("type", "ExternalError"), # Get type or default
            "message": error_message,
            "description": error_report.get("description"),
            "file_path": error_report.get("file_path"),
            "line_number": error_report.get("line_number"),
            "additional_data": error_report.get("details")
        }
        try:
            self._log_issue(issue_data_for_log)
        except ValueError as log_e:
             print(f"CRITICAL: Failed to log external error via _log_issue. Error: {log_e}")
             # Fallback to old list if new system fails for external errors too
             self.externally_reported_errors.append(logged_error)
             if len(self.externally_reported_errors) > 20:
                self.externally_reported_errors = self.externally_reported_errors[-20:]


        # Potentially change engine's main status based on external error
        # Only change if not in a more critical error state already
        if self.current_status not in ["error", "initialization_failed", "planning_failed", "generation_failed_uncaught_exception", "build_failed", "services_start_failed", "testing_framework_error", "analysis_failed", "refinement_loop_failed_exception"]:
            if "critical" in error_message.lower() or (self.current_status in ["idle", "completed", "planned", "initialized"]):
                 self.current_status = "error_reported_external" # Specific status

        self._update_progress(f"External error logged from {component_name}: '{error_message[:100]}...'", -1) 

        suggested_action = f"Error from {component_name} logged. Engine status: {self.current_status}. Monitor project status and logs. Remediation may occur in the next cycle if applicable."
        
        return {
            "message": "Error reported and logged successfully.",
            "logged_error_timestamp": timestamp,
            "logged_error_component": component_name,
            "engine_status_after_report": self.current_status,
            "suggested_action": suggested_action
        }

    def stop_execution(self):
        """Request to stop any ongoing background execution gracefully."""
        if self.execution_thread and self.execution_thread.is_alive():
            self._update_progress("Stop execution requested.", -1)
            self.execution_stopped = True # Signal for loops to break
            # Note: Thread join with timeout could be added here if immediate confirmation of stop is needed,
            # but it can make the stop request blocking. For now, it's a signal.
            # self.execution_thread.join(timeout=5.0) # Example: wait up to 5s
            # if self.execution_thread.is_alive():
            #     self._log_internal_error("stop_execution", "Thread did not stop in time after signal.")
            #     return {"status": "error", "message": "Failed to stop execution thread in time."}
            # self.current_status = "stopped" # Status will be updated by the thread itself when it exits
            return {"status": "stopping_initiated", "message": "Stop signal sent to execution thread. Monitor status."}
        else:
            self.execution_stopped = False # Clear flag if no thread running
            # If no thread is running, but status indicates an active phase, reset it.
            if self.current_status not in ["idle", "completed", "planned", "initialized", "error_reported_external"] and not self.current_status.startswith("completed_with_"):
                self.current_status = "stopped_idle" # Or a more appropriate idle/aborted state
            return {"status": "not_running", "message": "No execution thread is currently active."}

    def reset_engine(self) -> Dict[str, Any]:
        """Resets the engine to its initial idle state, clearing current project data."""
        self.stop_execution() # Attempt to stop anything running

        self.project_id = None
        self.project_name = None
        self.project_description = None
        self.execution_plan = None
        self.current_status = "idle"
        self.project_files = []
        self.service_urls = []
        self.current_iteration = 0
        self.externally_reported_errors = []
        self.internal_errors = []
        self.progress_log = []
        self.execution_stopped = False
        # self.agents = {} # Optionally clear/re-init agents, or keep them if they are stateless

        self._update_progress("Orchestration Engine has been reset to idle state.", 0)
        return {"success": True, "message": "Engine reset to idle state.", "status": self.current_status}

# Make sure datetime is imported if not already at the top of the file
import datetime
