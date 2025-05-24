import re
import datetime
import uuid
import threading
import time
from typing import Dict, List, Any, Optional
import os
import json

from src.repository.agent.general_agent import GeneralAgent
from src.repository.execution.meta_planner import MetaPlanner
from src.repository.execution.build_environment import BuildEnvironment
from src.repository.execution.testing_framework import TestingFramework
from src.repository.execution.feedback_analyzer import FeedbackAnalyzer
from src.service.llm_factory import LLMFactory
from src.service.tool_service import ToolService
from src.repository.execution.agent_manager import AgentManager

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
        self.project_id = None
        self.project_name = None
        self.project_description = None
        self.execution_plan = None
        self.current_status = "idle"
        self.progress_callbacks = []
        self.project_files = []
        self.service_urls = []
        self.current_iteration = 0
        self.max_iterations = 5
        
        # Thread for background execution
        self.execution_thread = None
        self.execution_stopped = False
        
    def initialize_project(self, project_description: str, project_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Initialize a new project based on the description.
        
        Args:
            project_description: Detailed project description.
            project_name: Optional project name.
            
        Returns:
            Project initialization result.
        """
        # Generate a project ID
        self.project_id = str(uuid.uuid4())
        
        # Set or generate project name
        if project_name:
            self.project_name = project_name
        else:
            # Generate a simple project name based on the first line of the description
            first_line = project_description.split('\n')[0][:30]
            timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M")
            self.project_name = f"{first_line.replace(' ', '-').lower()}-{timestamp}"
        
        # Store project description
        self.project_description = project_description
        
        # Initialize repository
        repo_result = self._initialize_repository()
        
        # Update status
        self.current_status = "initialized"
        
        # Send progress update
        self._update_progress("Project Initialized", 10)
        
        return {
            "project_id": self.project_id,
            "project_name": self.project_name,
            "workspace_path": self.workspace_path,
            "status": self.current_status,
            "repository": repo_result
        }
    
    def _initialize_repository(self) -> Dict[str, Any]:
        """
        Initialize the code repository.
        
        Returns:
            Repository initialization result.
        """
        # Create project directory structure
        project_dir = os.path.join(self.workspace_path, self.project_name)
        os.makedirs(project_dir, exist_ok=True)
        
        # Create basic structure
        os.makedirs(os.path.join(project_dir, "src"), exist_ok=True)
        os.makedirs(os.path.join(project_dir, "docs"), exist_ok=True)
        os.makedirs(os.path.join(project_dir, "tests"), exist_ok=True)
        
        # Create a basic README.md file
        readme_path = os.path.join(project_dir, "README.md")
        with open(readme_path, 'w') as f:
            f.write(f"# {self.project_name}\n\n{self.project_description}\n")
        
        # In a real implementation, this would initialize a git repository
        # and make an initial commit
        
        return {
            "project_dir": project_dir,
            "initialized": True
        }
    
    def plan_project(self) -> Dict[str, Any]:
        """
        Plan the project using the MetaPlanner.
        
        Returns:
            Planning result.
        """
        # Update status
        self.current_status = "planning"
        self._update_progress("Planning Started", 15)
        
        # Decompose project using MetaPlanner
        self.execution_plan = self.meta_planner.decompose_project(self.project_description)
        
        # Extract components from the plan
        components = self.execution_plan.get("components", [])
        
        # Identify layers
        layers = self.meta_planner.identify_layers(components)
        
        # Create tasks
        tasks = self.meta_planner.create_tasks(components)
        
        # Build dependency graph
        dependency_graph = self.meta_planner.build_dependency_graph(tasks)
        
        # Update the execution plan
        self.execution_plan.update({
            "layers": layers,
            "tasks": tasks,
            "dependency_graph": dependency_graph
        })
        
        # Schedule tasks
        scheduled_tasks = self._schedule_tasks(tasks, dependency_graph)
        self.execution_plan["scheduled_tasks"] = scheduled_tasks
        
        # Update status
        self.current_status = "planned"
        self._update_progress("Planning Complete", 20)
        
        return {
            "status": self.current_status,
            "execution_plan": self.execution_plan
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
        Generate code for the project.
        
        Args:
            async_execution: Whether to execute asynchronously.
            
        Returns:
            Code generation result or thread information.
        """
        if async_execution:
            # Start the code generation in a background thread
            self.execution_thread = threading.Thread(target=self._generate_code_thread)
            self.execution_thread.daemon = True
            self.execution_thread.start()
            
            return {
                "status": "started",
                "message": "Code generation started in background",
                "thread_id": self.execution_thread.ident
            }
        else:
            # Run synchronously
            return self._generate_code_execution()
    
    def _generate_code_thread(self):
        """
        Thread function for asynchronous code generation.
        """
        try:
            self._generate_code_execution()
        except Exception as e:
            self.current_status = "error"
            self._update_progress(f"Error: {str(e)}", 0)
    
    def _generate_code_execution(self) -> Dict[str, Any]:
        """
        Execute the code generation workflow.
        
        Returns:
            Code generation result.
        """
        # Check if planning is done
        if not self.execution_plan:
            return {
                "status": "error",
                "message": "Project must be planned before generating code"
            }
            
        # Update status
        self.current_status = "generating"
        self._update_progress("Code Generation Started", 25)
        
        # Initialize agents if not already created
        self._initialize_agents()
        
        # Get tasks by layer
        tasks_by_layer = {
            "backend": [],
            "middleware": [],
            "design": [],
            "frontend": []
        }
        
        for task in self.execution_plan.get("scheduled_tasks", []):
            layer = task.get("layer", "backend")
            tasks_by_layer[layer].append(task)
        
        # Generate code for each layer
        results = {
            "backend": self._generate_layer_code("backend", tasks_by_layer["backend"]),
            "middleware": self._generate_layer_code("middleware", tasks_by_layer["middleware"]),
            "design": self._generate_layer_code("design", tasks_by_layer["design"]),
            "frontend": self._generate_layer_code("frontend", tasks_by_layer["frontend"])
        }
        
        # Commit the changes
        self._commit_changes("Initial code generation")
        
        # Update progress
        self._update_progress("Code Generated", 50)
        
        # Collect all generated files
        self.project_files = self._collect_project_files()
        
        # Build the project
        build_result = self._build_project()
        
        # Handle build result
        if build_result.get("success", False):
            # Start services
            service_result = self._start_services()
            self.service_urls = service_result.get("service_urls", [])
            self._update_progress("Application Running", 70)
            
            # Run tests
            test_result = self._run_tests()
            
            # Analyze results and fix issues if needed
            analysis_result = self._analyze_results(test_result)
            
            if analysis_result.get("issues_found", False):
                # Start refinement loop
                self._update_progress("Issues Found - Starting Refinement", 80)
                refinement_result = self._run_refinement_loop(analysis_result)
                
                # Final assessment
                if refinement_result.get("success", False):
                    self._update_progress("Project Complete", 100)
                    self.current_status = "completed"
                else:
                    self._update_progress("Project Completed with Issues", 95)
                    self.current_status = "completed_with_issues"
            else:
                # No issues found
                self._update_progress("Project Complete", 100)
                self.current_status = "completed"
        else:
            # Build failed
            self._update_progress("Build Failed - Analyzing Issues", 60)
            
            # Classify build issues
            build_issues = self.feedback_analyzer.classify_issues(build_result)
            
            # Generate fix instructions
            fix_tasks = self.meta_planner.generate_fix_instructions(build_issues)
            
            # Run refinement loop for build issues
            self._run_refinement_loop({"issues": build_issues, "fix_tasks": fix_tasks})
        
        return {
            "status": self.current_status,
            "results": results,
            "build_result": build_result,
            "service_urls": self.service_urls,
            "files_generated": len(self.project_files)
        }
    
    def _initialize_agents(self):
        """
        Initialize the specialized agents for each layer.
        """
        if not self.agents:
            # Create a common LLM for all agents
            llm = self.llm_factory.create_llm("gemini", "gemini-1.5-pro")
            
            # Get tools
            tools = self.tool_service.get_tools()
            
            # Backend Agent
            backend_system_prompt = """You are a backend development specialist. 
            Your task is to implement robust, efficient, and secure backend code.
            Focus on API design, database integration, authentication, and business logic.
            Provide detailed comments and follow best practices for the chosen technology stack."""
            
            self.agent_manager.register_agent(
                "backend",
                GeneralAgent(
                    llm=llm,
                    tools=tools,
                    system_prompt=backend_system_prompt,
                    name="BackendAgent",
                    verbose=True
                )
            )
            
            # Middleware Agent
            middleware_system_prompt = """You are a middleware development specialist.
            Your task is to implement communication layers, integrations, and data processing systems.
            Focus on robustness, performance, and scalability.
            Provide detailed comments and follow best practices for the chosen technology stack."""
            
            self.agent_manager.register_agent(
                "middleware",
                GeneralAgent(
                    llm=llm,
                    tools=tools,
                    system_prompt=middleware_system_prompt,
                    name="MiddlewareAgent",
                    verbose=True
                )
            )
            
            # Design Agent
            design_system_prompt = """You are a UI/UX design specialist.
            Your task is to create visually appealing and user-friendly interfaces.
            Focus on layout, colors, typography, and component design.
            Provide detailed comments and follow best practices for the chosen design system."""
            
            self.agent_manager.register_agent(
                "design",
                GeneralAgent(
                    llm=llm,
                    tools=tools,
                    system_prompt=design_system_prompt,
                    name="DesignAgent",
                    verbose=True
                )
            )
            
            # Frontend Agent
            frontend_system_prompt = """You are a frontend development specialist.
            Your task is to implement responsive, accessible, and interactive user interfaces.
            Focus on component architecture, state management, and user experience.
            Provide detailed comments and follow best practices for the chosen technology stack."""
            
            self.agent_manager.register_agent(
                "frontend",
                GeneralAgent(
                    llm=llm,
                    tools=tools,
                    system_prompt=frontend_system_prompt,
                    name="FrontendAgent",
                    verbose=True
                )
            )
    
    def _generate_layer_code(self, layer: str, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate code for a specific layer.
        
        Args:
            layer: Layer name.
            tasks: List of tasks for the layer.
            
        Returns:
            Code generation result.
        """
        if not tasks:
            return {
                "status": "skipped",
                "message": f"No tasks for {layer} layer",
                "files_generated": 0
            }
            
        # Get the appropriate agent
        agent = self.agent_manager.get_agent(layer)
        if not agent:
            return {
                "status": "error",
                "message": f"No agent found for {layer} layer",
                "files_generated": 0
            }
            
        # Process each task
        results = []
        
        for task in tasks:
            # Check if execution should stop
            if self.execution_stopped:
                break
                
            # Build task context
            task_context = self._build_task_context(task)
            
            # Generate code for the task
            prompt = f"""
            Task: {task.get('description', 'Generate code')}
            
            Project description: {self.project_description}
            
            Context:
            {json.dumps(task_context, indent=2)}
            
            Generate the code for this task. Your response should include:
            1. The file path relative to the project root
            2. The complete file content
            3. Any explanation or notes about the implementation
            
            For each file you create, format your response like this:
            
            FILE: path/to/file.ext
            ```
            File content goes here
            ```
            
            You can create multiple files if needed for the task.
            """
            
            # Execute the agent for this task
            response = agent.run(prompt)
            
            # Parse the response to extract files
            files = self._parse_files_from_response(response)
            
            # Write the files
            for file_info in files:
                file_path = os.path.join(self.workspace_path, self.project_name, file_info["path"])
                
                # Create directory if it doesn't exist
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                
                # Write file
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(file_info["content"])
            
            # Add result
            results.append({
                "task": task,
                "files": files,
                "files_generated": len(files)
            })
            
            # Update progress (calculate based on task completion)
            progress_value = 25 + (25 * len(results) / max(len(tasks), 1))
            self._update_progress(f"Generating {layer} code: {len(results)}/{len(tasks)} tasks", progress_value)
            
        return {
            "status": "completed",
            "tasks_completed": len(results),
            "files_generated": sum(r["files_generated"] for r in results),
            "task_results": results
        }
    
    def _build_task_context(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build context information for a task.
        
        Args:
            task: Task information.
            
        Returns:
            Task context.
        """
        # Get task dependencies
        dependencies = task.get("dependencies", [])
        
        # Get related files (e.g., from previous tasks)
        related_files = []
        
        # In a real implementation, this would scan the workspace for relevant files
        # based on the task and its dependencies
        
        return {
            "task_id": task.get("id"),
            "task_type": task.get("type"),
            "layer": task.get("layer"),
            "dependencies": dependencies,
            "related_files": related_files,
            "project_structure": self._get_project_structure()
        }
    
    def _parse_files_from_response(self, response: str) -> List[Dict[str, Any]]:
        """
        Parse files from an agent response.
        
        Args:
            response: Agent response text.
            
        Returns:
            List of file information.
        """
        files = []
        
        # Look for file patterns in the response: FILE: path/to/file followed by content
        file_pattern = r"FILE\s*:\s*([\w\-\./]+)\s*\n```[\w]*\n([\s\S]*?)```"
        matches = re.findall(file_pattern, response)
        
        for match in matches:
            file_path = match[0].strip()
            file_content = match[1]
            
            files.append({
                "path": file_path,
                "content": file_content
            })
            
        return files
    
    def _commit_changes(self, message: str) -> Dict[str, Any]:
        """
        Commit changes to the repository.
        
        Args:
            message: Commit message.
            
        Returns:
            Commit result.
        """
        # In a real implementation, this would commit to git
        # For now, just return a simulated result
        
        return {
            "status": "committed",
            "message": message,
            "timestamp": datetime.datetime.now().isoformat()
        }
    
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
        self._update_progress("Building Project", 55)
        
        # Get project snapshot
        project_files = self._collect_project_files()
        
        # Detect project type
        project_type = self.build_environment.detect_project_type(project_files)
        
        # Generate build files
        build_files_result = self.build_environment.generate_build_files(project_type)
        
        if not build_files_result.get("success", False):
            return {
                "success": False,
                "message": "Failed to generate build files",
                "project_type": project_type,
                "details": build_files_result
            }
            
        # Install dependencies
        dependencies_result = self.build_environment.install_dependencies()
        
        if not dependencies_result.get("success", False):
            return {
                "success": False,
                "message": "Failed to install dependencies",
                "project_type": project_type,
                "details": dependencies_result
            }
            
        # Build the project
        build_result = self.build_environment.build_project()
        
        return {
            "success": build_result.get("success", False),
            "message": build_result.get("message", ""),
            "project_type": project_type,
            "build_files": build_files_result,
            "dependencies": dependencies_result,
            "build": build_result
        }
    
    def _start_services(self) -> Dict[str, Any]:
        """
        Start services for the project.
        
        Returns:
            Service start result.
        """
        return self.build_environment.start_services()
    
    def _run_tests(self) -> Dict[str, Any]:
        """
        Run tests on the project.
        
        Returns:
            Test results.
        """
        self._update_progress("Running Tests", 75)
        
        # Run static analysis
        static_analysis = self.testing_framework.run_static_analysis(self.project_files)
        
        # Generate tests
        generated_tests = self.testing_framework.generate_tests(self.project_files)
        
        # Run unit tests
        unit_tests = self.testing_framework.execute_unit_tests()
        
        # Run browser tests
        browser_tests = self.testing_framework.perform_browser_tests(self.service_urls)
        
        return {
            "static_analysis": static_analysis,
            "generated_tests": generated_tests,
            "unit_tests": unit_tests,
            "browser_tests": browser_tests
        }
    
    def _analyze_results(self, test_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze test results.
        
        Args:
            test_results: Test results.
            
        Returns:
            Analysis result.
        """
        # Collect all issues
        all_issues = []
        
        # Static analysis issues
        if "static_analysis" in test_results:
            all_issues.extend(test_results["static_analysis"].get("issues", []))
            
        # Unit test failures
        if "unit_tests" in test_results:
            unit_test_failures = test_results["unit_tests"].get("failures", [])
            for failure in unit_test_failures:
                all_issues.append({
                    "type": "unit_test",
                    "test": failure.get("test"),
                    "message": failure.get("message"),
                    "severity": "high"
                })
                
        # Browser test failures
        if "browser_tests" in test_results:
            browser_test_failures = test_results["browser_tests"].get("failures", [])
            for failure in browser_test_failures:
                all_issues.append({
                    "type": "browser_test",
                    "test": failure.get("test"),
                    "url": failure.get("url"),
                    "message": failure.get("message"),
                    "severity": "high"
                })
                
        # Classify issues
        classified_issues = self.feedback_analyzer.classify_issues({"issues": all_issues})
        
        # Check if there are issues to fix
        issues_found = len(classified_issues.get("issues", [])) > 0
        
        # If issues found, generate fix tasks
        fix_tasks = None
        if issues_found:
            fix_tasks = self.meta_planner.generate_fix_instructions(classified_issues)
            
        return {
            "issues_found": issues_found,
            "issues": classified_issues,
            "fix_tasks": fix_tasks
        }
    
    def _run_refinement_loop(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run the refinement loop to fix issues.
        
        Args:
            analysis_result: Analysis result.
            
        Returns:
            Refinement result.
        """
        self.current_iteration = 1
        continue_refinement = True
        results = []
        
        while continue_refinement and self.current_iteration <= self.max_iterations and not self.execution_stopped:
            self._update_progress(f"Refinement Iteration {self.current_iteration}/{self.max_iterations}", 80 + (self.current_iteration / self.max_iterations) * 15)
            
            # Group fix tasks by layer
            fix_tasks_by_layer = {
                "backend": [],
                "middleware": [],
                "design": [],
                "frontend": []
            }
            
            for task in analysis_result.get("fix_tasks", []):
                layer = task.get("layer", "backend")
                fix_tasks_by_layer[layer].append(task)
                
            # Execute fix tasks for each layer
            iteration_results = {}
            
            for layer, tasks in fix_tasks_by_layer.items():
                if tasks:
                    iteration_results[layer] = self._generate_layer_code(layer, tasks)
                    
            # Commit changes
            self._commit_changes(f"Refinement iteration {self.current_iteration}")
            
            # Rebuild and restart
            rebuild_result = self.build_environment.rebuild_and_restart()
            
            # If build fails, break the loop
            if not rebuild_result.get("success", False):
                break
                
            # Update service URLs if they changed
            if "service_urls" in rebuild_result:
                self.service_urls = rebuild_result["service_urls"]
                
            # Rerun tests
            test_results = self.testing_framework.rerun_tests()
            
            # Analyze results
            new_analysis = self._analyze_results(test_results)
            
            # Store iteration results
            results.append({
                "iteration": self.current_iteration,
                "fixes": iteration_results,
                "rebuild": rebuild_result,
                "tests": test_results,
                "analysis": new_analysis
            })
            
            # Check if we should continue
            continue_refinement = new_analysis.get("issues_found", False)
            analysis_result = new_analysis
            
            # Increment iteration counter
            self.current_iteration += 1
            
        # Final result
        success = not analysis_result.get("issues_found", False) if analysis_result else True
        
        return {
            "success": success,
            "iterations": self.current_iteration - 1,
            "results": results,
            "final_analysis": analysis_result
        }
    
    def _get_project_structure(self) -> Dict[str, Any]:
        """
        Get the current project structure.
        
        Returns:
            Project structure.
        """
        project_dir = os.path.join(self.workspace_path, self.project_name)
        structure = {"directories": [], "files": []}
        
        if os.path.exists(project_dir):
            for root, dirs, files in os.walk(project_dir):
                rel_path = os.path.relpath(root, project_dir)
                
                if rel_path != ".":
                    structure["directories"].append(rel_path)
                    
                for file in files:
                    file_path = os.path.join(rel_path, file)
                    if rel_path == ".":
                        file_path = file
                    structure["files"].append(file_path)
                    
        return structure
    
    def _update_progress(self, message: str, percentage: float):
        """
        Update progress and notify callbacks.
        
        Args:
            message: Progress message.
            percentage: Progress percentage (0-100).
        """
        progress_info = {
            "project_id": self.project_id,
            "message": message,
            "percentage": percentage,
            "timestamp": datetime.datetime.now().isoformat()
        }
        
        # Notify all callbacks
        for callback in self.progress_callbacks:
            try:
                callback(progress_info)
            except Exception:
                pass
                
    def register_progress_callback(self, callback):
        """
        Register a progress callback function.
        
        Args:
            callback: Function to call with progress updates.
        """
        if callback not in self.progress_callbacks:
            self.progress_callbacks.append(callback)
            
    def unregister_progress_callback(self, callback):
        """
        Unregister a progress callback function.
        
        Args:
            callback: Function to remove from callbacks.
        """
        if callback in self.progress_callbacks:
            self.progress_callbacks.remove(callback)
            
    def stop_execution(self):
        """
        Stop the execution of the engine.
        """
        self.execution_stopped = True
        self._update_progress("Execution stopped", 0)
        
    def get_status(self) -> Dict[str, Any]:
        """
        Get the current status of the engine.
        
        Returns:
            Status information.
        """
        return {
            "project_id": self.project_id,
            "project_name": self.project_name,
            "status": self.current_status,
            "iteration": self.current_iteration,
            "execution_running": self.execution_thread is not None and self.execution_thread.is_alive(),
            "execution_stopped": self.execution_stopped
        }
    
    # --- MCP-LIKE LOGIC INTEGRATED ---
    def mcp_register_agent(self, agent_name: str, agent_instance: Any, capabilities: dict = None) -> None:
        """
        Register an agent with the orchestration engine (MCP server logic).
        Args:
            agent_name: Unique name for the agent.
            agent_instance: The agent object.
            capabilities: Optional dict describing agent capabilities.
        """
        self.agent_manager.register_agent(agent_name, agent_instance, capabilities)

    def mcp_submit_task(self, agent_name: str, task: dict) -> dict:
        """
        Submit a task to a registered agent. The engine routes the task and manages context.
        Args:
            agent_name: Name of the agent to handle the task.
            task: Task dictionary (should include 'input' and optional 'context').
        Returns:
            Result from the agent.
        """
        return self.agent_manager.submit_task(agent_name, task, self.mcp_get_context())

    def mcp_get_context(self) -> dict:
        """
        Retrieve the current shared project context.
        Returns:
            Dictionary representing the shared context.
        """
        return {
            "project_id": self.project_id,
            "project_name": self.project_name,
            "project_description": self.project_description,
            "execution_plan": self.execution_plan,
            "project_files": self.project_files,
            "service_urls": self.service_urls,
            "current_status": self.current_status
        }

    def mcp_update_context(self, context_update: dict) -> None:
        """
        Update the shared project context with new information.
        Args:
            context_update: Dict of context fields to update.
        """
        for k, v in context_update.items():
            if hasattr(self, k):
                setattr(self, k, v)

    def mcp_list_agents(self) -> list:
        """
        List all registered agents and their capabilities.
        Returns:
            List of agent names and capabilities.
        """
        return self.agent_manager.list_agents()