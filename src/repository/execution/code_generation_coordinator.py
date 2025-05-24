import logging
import json
import re
import os
from typing import Dict, List, Any, Optional
from src.repository.execution.agent_flow import AgentFlow
from src.repository.agent.general_agent import GeneralAgent
from src.repository.execution.agent_manager import AgentManager
from src.service.llm_factory import LLMFactory
from src.service.tool_service import ToolService

# Configure logging to be less verbose
logging.getLogger('src.repository.agent.tool_call_agent').setLevel(logging.WARNING)
logging.getLogger('src.repository.execution.agent_flow').setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


class CodeGenerationCoordinator:
    """
    Coordinates code generation using agent flow and specialized agents.
    """
    
    def __init__(self, llm_factory: LLMFactory, tool_service: ToolService, external_projects_dir: str = None):
        self.llm_factory = llm_factory
        self.tool_service = tool_service
        self.agent_manager = AgentManager(llm_factory, tool_service)
        self.agents: Dict[str, GeneralAgent] = {}
        self.agent_flow: Optional[AgentFlow] = None
        self.agent_flow_tasks: List[Dict[str, Any]] = []
        
        # Set up external projects directory
        if external_projects_dir:
            self.external_projects_dir = external_projects_dir
        else:
            # Default: create projects directory outside the main repo
            current_dir = os.path.dirname(os.path.abspath(__file__))
            repo_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
            self.external_projects_dir = os.path.join(os.path.dirname(repo_root), "generated_projects")
        
        self.current_project_path = None
        
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
            # Determine file extension based on layer for the example
            extension_map = {
                "backend": "py",
                "frontend": "js", 
                "design": "css",
                "middleware": "py"
            }

            # Get dynamic extension mapping based on tech stack
            tech_stack = planned_task.get('tech_stack', [])
            if not tech_stack and execution_plan.get('tech_stack'):
                # Fallback to global tech stack if task doesn't have one
                tech_stack = []
                for layer_stack in execution_plan['tech_stack'].values():
                    if isinstance(layer_stack, list):
                        tech_stack.extend(layer_stack)
            
            extension_map = self._get_extension_mapping(project_description, tech_stack)
            
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
Tech Stack: {', '.join(tech_stack)}

Project Description: {project_description}

IMPORTANT: You must return your response as a JSON array of file objects. Each file object must have exactly these keys:
- "path": The relative file path (e.g., "src/backend/models.py", "src/frontend/components/App.{extension_map.get('frontend', 'js')}")
- "content": The complete file content as a string

Example response format:
[
  {{
    "path": "src/{layer}/example.{extension_map.get(layer, 'py')}",
    "content": "// Complete file content here\\nfunction example() {{\\n  return 'Hello World';\\n}}"
  }},
  {{
    "path": "src/{layer}/another_file.{extension_map.get(layer, 'py')}",
    "content": "# Another complete file\\nprint('Generated code')"
  }}
]

Generate the necessary code files for this {layer} component. Ensure the code follows best practices and integrates well with other components.
Return ONLY the JSON array - no explanations, no markdown formatting, just the raw JSON.
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

    def execute_agent_flow_generation(self, project_name: str = None) -> Dict[str, Any]:
        """
        Execute code generation using agent flow.
        
        Args:
            project_name: Optional project name for directory setup
            
        Returns:
            Generation result dictionary
        """
        try:
            # Set up project directory if project name is provided and not already set
            if project_name and not self.current_project_path:
                self.set_project_output_directory(project_name)
            
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
            
            # Write generated files to filesystem using bash tool
            files_written = self._write_files_to_filesystem(generated_files)
            
            return {
                "success": successful_tasks == total_tasks,
                "message": f"Agent flow completed: {successful_tasks}/{total_tasks} tasks successful, {files_written} files written",
                "files_generated": len(generated_files),
                "files_written": files_written,
                "generated_files": generated_files,
                "flow_results": flow_results,
                "successful_tasks": successful_tasks,
                "total_tasks": total_tasks,
                "project_output_directory": self.current_project_path
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
                print(f"⚠️  Task {task_name} returned no result")
                continue
                
            try:
                # Use the improved parsing method
                files = self._parse_agent_result(str(result))
                
                if files:
                    generated_files.extend(files)
                    print(f"📄 Parsed {len(files)} files from task {task_name}")
                else:
                    print(f"⚠️  No valid files found in result for task {task_name}")
                    
            except Exception as e:
                print(f"❌ Error processing result for task {task_name}: {str(e)}")
                
        return generated_files

    def _clean_json_response(self, response: str) -> str:
        """
        Clean agent response to extract pure JSON, removing markdown formatting.
        """
        if not response:
            return ""
            
        # Remove markdown code blocks
        response = re.sub(r'```json\s*', '', response)
        response = re.sub(r'```\s*$', '', response)
        response = response.strip()
        
        # Find JSON array start and end
        start_idx = response.find('[')
        end_idx = response.rfind(']')
        
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            return response[start_idx:end_idx + 1]
        
        return response
    
    def _parse_agent_json_response(self, response: str) -> List[Dict[str, str]]:
        """
        Parse agent response to extract file objects.
        """
        try:
            cleaned_response = self._clean_json_response(response)
            if not cleaned_response:
                return []
                
            parsed = json.loads(cleaned_response)
            if isinstance(parsed, list):
                return parsed
            elif isinstance(parsed, dict):
                return [parsed]
            else:
                logger.warning(f"Unexpected JSON structure: {type(parsed)}")
                return []
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.debug(f"Raw response: {response[:500]}...")
            return []
        except Exception as e:
            logger.error(f"Unexpected error parsing response: {e}")
            return []

    def set_project_output_directory(self, project_name: str) -> str:
        """
        Create and set the output directory for the current project.
        
        Args:
            project_name: Name of the project to create
            
        Returns:
            Path to the created project directory
        """
        try:
            # Create the external projects directory if it doesn't exist
            os.makedirs(self.external_projects_dir, exist_ok=True)
            
            # Create project-specific directory
            project_dir = os.path.join(self.external_projects_dir, project_name)
            os.makedirs(project_dir, exist_ok=True)
            
            self.current_project_path = project_dir
            
            print(f"📁 Created project directory: {project_dir}")
            return project_dir
            
        except Exception as e:
            logger.error(f"Failed to create project directory: {e}")
            raise

    def _write_file_safely(self, file_path: str, content: str) -> bool:
        """
        Write file content safely to the external project directory.
        """
        try:
            if not self.current_project_path:
                logger.error("No project directory set. Call set_project_output_directory first.")
                return False
            
            # Construct full path relative to project directory
            full_path = os.path.join(self.current_project_path, file_path)
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            # Write file content directly
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"✅ Successfully wrote file: {full_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to write file {file_path}: {e}")
            return False

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
    
    def _write_files_to_filesystem(self, generated_files: List[Dict[str, str]]) -> int:
        """
        Write generated files to the filesystem using direct Python file operations.
        
        Args:
            generated_files: List of file dictionaries with 'path' and 'content' keys
            
        Returns:
            Number of files successfully written
        """
        if not generated_files:
            print("No files to write.")
            return 0
            
        files_written = 0
        
        for file_info in generated_files:
            try:
                file_path = file_info.get("path", "")
                content = file_info.get("content", "")
                
                if not file_path or not content:
                    print(f"⚠️  Skipping file with missing path or content")
                    continue
                
                # Use the safe file writing method
                if self._write_file_safely(file_path, content):
                    files_written += 1
                    print(f"✅ Successfully wrote: {file_path}")
                else:
                    print(f"❌ Failed to write: {file_path}")
                    
            except Exception as e:
                print(f"❌ Error writing {file_info.get('path', 'unknown')}: {str(e)}")
                
        return files_written

    def _get_extension_mapping(self, project_description: str, tech_stack: List[str]) -> Dict[str, str]:
        """
        Dynamically determine file extensions based on project description and tech stack.
        
        Args:
            project_description: Description of the project
            tech_stack: List of technologies being used
            
        Returns:
            Dictionary mapping layers to appropriate file extensions
        """
        extension_map = {
            "backend": "py",      # Default fallback
            "frontend": "js",     # Default fallback  
            "design": "css",      # Default fallback
            "middleware": "py"    # Default fallback
        }
        
        # Convert to lowercase for easier matching
        tech_stack_lower = [tech.lower() for tech in tech_stack]
        description_lower = project_description.lower()
        
        # Backend language detection
        if any(tech in tech_stack_lower for tech in ["python", "fastapi", "flask", "django", "uvicorn"]):
            extension_map["backend"] = "py"
            extension_map["middleware"] = "py"
        elif any(tech in tech_stack_lower for tech in ["node", "nodejs", "express", "nestjs"]):
            extension_map["backend"] = "js"
            extension_map["middleware"] = "js"
        elif any(tech in tech_stack_lower for tech in ["typescript", "ts-node"]):
            extension_map["backend"] = "ts"
            extension_map["middleware"] = "ts"
        elif any(tech in tech_stack_lower for tech in ["java", "spring", "springboot"]):
            extension_map["backend"] = "java"
            extension_map["middleware"] = "java"
        elif any(tech in tech_stack_lower for tech in ["c#", "csharp", "dotnet", ".net", "asp.net"]):
            extension_map["backend"] = "cs"
            extension_map["middleware"] = "cs"
        elif any(tech in tech_stack_lower for tech in ["go", "golang", "gin", "fiber"]):
            extension_map["backend"] = "go"
            extension_map["middleware"] = "go"
        elif any(tech in tech_stack_lower for tech in ["php", "laravel", "symfony"]):
            extension_map["backend"] = "php"
            extension_map["middleware"] = "php"
        elif any(tech in tech_stack_lower for tech in ["ruby", "rails", "sinatra"]):
            extension_map["backend"] = "rb"
            extension_map["middleware"] = "rb"
        
        # Frontend language detection
        if any(tech in tech_stack_lower for tech in ["react", "next", "nextjs"]):
            if any(tech in tech_stack_lower for tech in ["typescript", "ts"]):
                extension_map["frontend"] = "tsx"
            else:
                extension_map["frontend"] = "jsx"
        elif any(tech in tech_stack_lower for tech in ["vue", "vuejs", "nuxt"]):
            extension_map["frontend"] = "vue"
        elif any(tech in tech_stack_lower for tech in ["angular", "ng"]):
            extension_map["frontend"] = "ts"
        elif any(tech in tech_stack_lower for tech in ["svelte", "sveltekit"]):
            extension_map["frontend"] = "svelte"
        elif any(tech in tech_stack_lower for tech in ["typescript", "ts"]):
            extension_map["frontend"] = "ts"
        elif any(tech in tech_stack_lower for tech in ["javascript", "js", "vanilla"]):
            extension_map["frontend"] = "js"
        elif any(tech in tech_stack_lower for tech in ["html", "css", "static"]):
            extension_map["frontend"] = "html"
            
        # Design/styling detection
        if any(tech in tech_stack_lower for tech in ["scss", "sass"]):
            extension_map["design"] = "scss"
        elif any(tech in tech_stack_lower for tech in ["less"]):
            extension_map["design"] = "less"
        elif any(tech in tech_stack_lower for tech in ["stylus"]):
            extension_map["design"] = "styl"
        elif any(tech in tech_stack_lower for tech in ["tailwind", "tailwindcss"]):
            extension_map["design"] = "css"  # Tailwind still uses CSS files
        
        # Special case handling based on project description
        if "mobile" in description_lower:
            if any(tech in tech_stack_lower for tech in ["react native", "expo"]):
                extension_map["frontend"] = "tsx" if "typescript" in tech_stack_lower else "jsx"
            elif any(tech in tech_stack_lower for tech in ["flutter", "dart"]):
                extension_map["frontend"] = "dart"
            elif any(tech in tech_stack_lower for tech in ["kotlin", "android"]):
                extension_map["frontend"] = "kt"
            elif any(tech in tech_stack_lower for tech in ["swift", "ios"]):
                extension_map["frontend"] = "swift"
                
        return extension_map

    def _parse_agent_result(self, result: str) -> List[Dict[str, str]]:
        """
        Parse agent result to extract file information.
        Handles various formats including markdown-wrapped JSON.
        """
        if not result or not result.strip():
            return []
        
        try:
            # Clean the result - remove markdown formatting
            cleaned_result = result.strip()
            
            # Remove markdown code blocks if present
            if cleaned_result.startswith('```'):
                # Find the first and last ```
                lines = cleaned_result.split('\n')
                start_idx = 0
                end_idx = len(lines)
                
                # Find start of JSON (skip ```json or ```markdown)
                for i, line in enumerate(lines):
                    if line.strip().startswith('```'):
                        start_idx = i + 1
                        break
                
                # Find end of JSON (find closing ```)
                for i in range(len(lines) - 1, -1, -1):
                    if lines[i].strip() == '```':
                        end_idx = i
                        break
                
                # Extract just the JSON part
                if start_idx < end_idx:
                    cleaned_result = '\n'.join(lines[start_idx:end_idx])
            
            # Try to parse as JSON
            parsed = json.loads(cleaned_result)
            
            # Handle different response formats
            if isinstance(parsed, list):
                # Direct list of file objects
                files = []
                for item in parsed:
                    if isinstance(item, dict) and "path" in item and "content" in item:
                        files.append({
                            "path": item["path"],
                            "content": item["content"]
                        })
                return files
            
            elif isinstance(parsed, dict):
                # Single file object or structured response
                if "path" in parsed and "content" in parsed:
                    return [{"path": parsed["path"], "content": parsed["content"]}]
                elif "files" in parsed:
                    return parsed["files"]
                elif "code" in parsed:
                    # Handle structured code response
                    return [{"path": parsed.get("path", "generated_file.txt"), "content": parsed["code"]}]
            
            return []
            
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON, attempting string parsing: {e}")
            # Fallback to string parsing for non-JSON responses
            return [self._parse_string_result("unknown_task", result)]
        except Exception as e:
            logger.error(f"Error parsing agent result: {e}")
            return []
    
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
    
    def _extract_json_from_response(self, response: str) -> List[Dict[str, str]]:
        """Extract JSON array from agent response, handling markdown formatting."""
        try:
            # Remove markdown code blocks and clean up the response
            cleaned_response = response.strip()
            
            # Remove ```json and ``` markers
            if cleaned_response.startswith('```json'):
                cleaned_response = cleaned_response[7:]  # Remove ```json
            if cleaned_response.startswith('```'):
                cleaned_response = cleaned_response[3:]   # Remove ```
            if cleaned_response.endswith('```'):
                cleaned_response = cleaned_response[:-3]  # Remove trailing ```
            
            # Clean up any remaining backticks and whitespace
            cleaned_response = cleaned_response.strip('`').strip()
            
            # Find JSON array in the response
            json_start = cleaned_response.find('[')
            json_end = cleaned_response.rfind(']') + 1
            
            if json_start != -1 and json_end > json_start:
                json_str = cleaned_response[json_start:json_end]
                parsed_json = json.loads(json_str)
                
                if isinstance(parsed_json, list):
                    # Validate each file object has required keys
                    validated_files = []
                    for file_obj in parsed_json:
                        if isinstance(file_obj, dict) and 'path' in file_obj and 'content' in file_obj:
                            validated_files.append({
                                'path': str(file_obj['path']),
                                'content': str(file_obj['content'])
                            })
                        else:
                            logger.warning(f"Invalid file object structure: {file_obj}")
                    
                    return validated_files
                else:
                    logger.error(f"Parsed JSON is not a list: {type(parsed_json)}")
                    return []
            else:
                logger.error("No valid JSON array found in response")
                return []
                
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            logger.debug(f"Problematic response: {response[:500]}...")
            return []
        except Exception as e:
            logger.error(f"Unexpected error parsing JSON: {e}")
            return []