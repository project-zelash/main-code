import json
from typing import Dict, List, Any, Optional
from src.repository.execution.agent_flow import AgentFlow
from src.repository.agent.general_agent import GeneralAgent
from src.repository.execution.agent_manager import AgentManager
from src.service.llm_factory import LLMFactory
from src.service.tool_service import ToolService


class CodeGenerationCoordinator:
    """
    Coordinates code generation using agent flow and specialized agents.
    """
    
    def __init__(self, llm_factory: LLMFactory, tool_service: ToolService):
        self.llm_factory = llm_factory
        self.tool_service = tool_service
        self.agent_manager = AgentManager(llm_factory, tool_service)
        self.agents: Dict[str, GeneralAgent] = {}
        self.agent_flow: Optional[AgentFlow] = None
        self.agent_flow_tasks: List[Dict[str, Any]] = []
        
    def initialize_agents(self) -> bool:
        """Initialize specialized agents if not already done."""
        if not self.agents:
            try:
                self.agent_manager.initialize_agents()
                # Set self.agents to a dict of agent_name: agent_instance
                self.agents = {name: entry["instance"] for name, entry in self.agent_manager.agents.items()}
                return True
            except Exception as e:
                print(f"Failed to initialize agents: {str(e)}")
                return False
        return True
    
    def create_agent_flow_tasks(self, execution_plan: Dict[str, Any], project_name: str, project_description: str) -> List[Dict[str, Any]]:
        """
        Convert the meta planner's execution plan into AgentFlow-compatible tasks.
        
        Args:
            execution_plan: The execution plan from meta planner
            project_name: Name of the project
            project_description: Description of the project
            
        Returns:
            List of agent flow tasks
        """
        agent_flow_tasks = []
        task_counter = 1
        
        # Get the planned tasks from meta planner
        # Support both 'scheduled_tasks' and 'components' as the task list key
        planned_tasks = execution_plan.get("scheduled_tasks", execution_plan.get("components", []))
        
        # Create a mapping from component IDs to agent flow task names
        component_id_to_task_name = {}
        
        for planned_task in planned_tasks:
            layer = planned_task.get("layer", "backend")
            task_type = planned_task.get("type", "implementation")
            component_name = planned_task.get("name", f"Task {task_counter}")
            description = planned_task.get("description", "No description provided")
            dependencies = planned_task.get("dependencies", [])
            component_id = planned_task.get("id", f"component-{task_counter}")
            
            # Map layer to agent
            agent_mapping = {
                "backend": "backend",
                "middleware": "middleware", 
                "design": "frontend",    # Route design tasks to frontend agent
                "frontend": "frontend"
            }
            
            agent_name = agent_mapping.get(layer, "backend")
            
            # Create task name
            task_name = f"{layer}_{task_type}_{task_counter}"
            
            # Store mapping for dependency resolution
            component_id_to_task_name[component_id] = task_name
            
            task_counter += 1
        
        # Second pass: create tasks with resolved dependencies
        task_counter = 1
        for planned_task in planned_tasks:
            layer = planned_task.get("layer", "backend")
            task_type = planned_task.get("type", "implementation")
            component_name = planned_task.get("name", f"Task {task_counter}")
            description = planned_task.get("description", "No description provided")
            dependencies = planned_task.get("dependencies", [])
            component_id = planned_task.get("id", f"component-{task_counter}")
            
            # Map layer to agent
            agent_mapping = {
                "backend": "backend",
                "middleware": "middleware", 
                "design": "frontend",    # Route design tasks to frontend agent
                "frontend": "frontend"
            }
            
            agent_name = agent_mapping.get(layer, "backend")
            
            # Create task name
            task_name = f"{layer}_{task_type}_{task_counter}"
            
            # Resolve dependencies using the mapping
            resolved_dependencies = []
            for dep_id in dependencies:
                if dep_id in component_id_to_task_name:
                    resolved_dependencies.append(component_id_to_task_name[dep_id])
                else:
                    # Log unresolved dependency but don't fail
                    print(f"Warning: Could not resolve dependency '{dep_id}' for task '{task_name}'")
            
            # Create agent flow task
            agent_task = {
                "name": task_name,
                "agent": agent_name,
                "input": f"""
Project: {project_name}
Task: {component_name}
Description: {description}
Layer: {layer}
Type: {task_type}
Tech Stack: {', '.join(planned_task.get('tech_stack', []))}

Project Description: {project_description}

Generate the necessary code files for this {layer} component. Ensure the code follows best practices and integrates well with other components.
Return the result as a list of dictionaries with 'path' and 'content' keys for each file to be created.
""",
                "priority": planned_task.get("execution_order", task_counter),
                "dependencies": resolved_dependencies  # Use resolved dependencies
            }
            
            agent_flow_tasks.append(agent_task)
            task_counter += 1
        
        self.agent_flow_tasks = agent_flow_tasks
        return agent_flow_tasks

    def _resolve_dependencies(self, dependencies: List[str], all_tasks: List[Dict[str, Any]]) -> List[tuple]:
        """
        Resolve dependencies to task identifiers that match the naming convention.
        
        Args:
            dependencies: List of dependency IDs
            all_tasks: All planned tasks to resolve against
            
        Returns:
            List of tuples (layer, type, order) for dependencies
        """
        resolved = []
        for dep_id in dependencies:
            for task in all_tasks:
                if task.get("id") == dep_id or task.get("component_id") == dep_id:
                    layer = task.get("layer", "backend")
                    task_type = task.get("type", "implementation")
                    order = task.get("execution_order", 1)
                    resolved.append((layer, task_type, order))
                    break
        return resolved

    def execute_agent_flow_generation(self) -> Dict[str, Any]:
        """
        Execute code generation using agent flow.
        
        Returns:
            Generation result dictionary
        """
        try:
            # Initialize agents if not already done
            if not self.initialize_agents():
                return {
                    "success": False,
                    "message": "Failed to initialize agents",
                    "files_generated": 0
                }
            
            # Create and configure agent flow
            self.agent_flow = AgentFlow(
                agents=self.agents,
                task_list=self.agent_flow_tasks,
                verbose=True,
                max_workers=2  # Limit parallel execution for stability
            )
            
            # Execute the agent flow
            flow_results = self.agent_flow.run(max_retries=1)
            
            # Process results
            successful_tasks = sum(1 for result in flow_results.values() if result is not None)
            total_tasks = len(self.agent_flow_tasks)
            
            # Parse and structure results for file saving
            generated_files = self._process_agent_flow_results(flow_results)
            
            return {
                "success": successful_tasks == total_tasks,
                "message": f"Agent flow completed: {successful_tasks}/{total_tasks} tasks successful",
                "files_generated": len(generated_files),
                "generated_files": generated_files,
                "flow_results": flow_results,
                "successful_tasks": successful_tasks,
                "total_tasks": total_tasks
            }
                
        except Exception as e:
            return {
                "success": False,
                "message": f"Error during agent flow execution: {str(e)}",
                "files_generated": 0
            }

    def _process_agent_flow_results(self, flow_results: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Process and parse the results from agent flow execution.
        
        Args:
            flow_results: Results from agent flow execution
            
        Returns:
            List of file dictionaries with 'path' and 'content' keys
        """
        generated_files = []
        
        for task_name, result in flow_results.items():
            if result is None:
                continue
                
            try:
                # Parse the result - assuming agents return structured data with file information
                if isinstance(result, str):
                    # Try to extract file information from string result
                    file_info = self._parse_string_result(task_name, result)
                    if file_info:
                        generated_files.append(file_info)
                elif isinstance(result, dict):
                    # Handle structured result with file information
                    files = self._parse_structured_result(result)
                    generated_files.extend(files)
                elif isinstance(result, list):
                    # Handle list of files
                    for item in result:
                        if isinstance(item, dict) and "path" in item and "content" in item:
                            generated_files.append({
                                "path": item["path"],
                                "content": item["content"]
                            })
                            
            except Exception as e:
                print(f"Error processing result for task {task_name}: {str(e)}")
                
        return generated_files

    def _parse_string_result(self, task_name: str, result: str) -> Optional[Dict[str, str]]:
        """Parse text result from agent to extract file information."""
        # Extract task info to determine appropriate file location
        task_parts = task_name.split("_")
        layer = task_parts[0] if len(task_parts) > 0 else "general"
        task_type = task_parts[1] if len(task_parts) > 1 else "output"
        
        # Determine file extension based on layer
        extension_map = {
            "backend": "py",
            "frontend": "js",
            "design": "css",
            "middleware": "py"
        }
        extension = extension_map.get(layer, "txt")
        
        # Create file path
        file_path = f"src/{layer}/{task_name}.{extension}"
        
        return {
            "path": file_path,
            "content": result
        }

    def _parse_structured_result(self, result: Dict[str, Any]) -> List[Dict[str, str]]:
        """Parse structured result from agent."""
        files = []
        
        if "files" in result:
            for file_info in result["files"]:
                if isinstance(file_info, dict) and "path" in file_info and "content" in file_info:
                    files.append({
                        "path": file_info["path"],
                        "content": file_info["content"]
                    })
        elif "content" in result:
            # Single file result
            file_path = result.get("path", "src/generated_file.py")
            files.append({
                "path": file_path,
                "content": result["content"]
            })
            
        return files

    def build_task_context(self, task: Dict[str, Any], project_name: str, project_description: str, project_files: List[str]) -> Dict[str, Any]:
        """
        Build context information for a task.
        
        Args:
            task: Task information
            project_name: Name of the project
            project_description: Description of the project
            project_files: List of existing project files
            
        Returns:
            Task context
        """
        dependencies = task.get("dependencies", [])
        
        return {
            "task_id": task.get("id"),
            "task_type": task.get("type"),
            "description": task.get("description"),
            "layer": task.get("layer"),
            "dependencies": dependencies,
            "related_files": project_files,
            "project_name": project_name,
            "project_description": project_description
        }

    def get_agent_flow_status(self) -> Dict[str, Any]:
        """Get current agent flow status."""
        return {
            "agents_initialized": len(self.agents) > 0,
            "available_agents": list(self.agents.keys()),
            "agent_flow_tasks_count": len(self.agent_flow_tasks),
            "agent_flow_active": self.agent_flow is not None
        }