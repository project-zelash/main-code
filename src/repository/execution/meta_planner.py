from typing import Dict, List, Any, Optional
import json
import uuid
import re

from src.service.llm_factory import LLMFactory

class MetaPlanner:
    """
    Meta-planner responsible for decomposing projects into tasks and planning execution.
    """
    
    def __init__(self, llm_factory: LLMFactory):
        """
        Initialize the meta-planner.
        
        Args:
            llm_factory: Factory for creating LLM instances.
        """
        self.llm_factory = llm_factory
        self.llm = self.llm_factory.create_llm("gemini")
    
    def decompose_project(self, description: str) -> Dict[str, Any]:
        """
        Decompose a project description into components and structures.
        
        Args:
            description: Project description.
            
        Returns:
            Decomposition result with components and architecture.
        """
        prompt = f"""
        You are an expert system architect. Decompose the following project description into a structured
        architectural plan with clear components.
        
        Project Description:
        {description}
        
        Please organize your response as a JSON object with the following structure:
        {{
            "components": [
                {{
                    "id": "unique-id",
                    "name": "Component Name",
                    "description": "Component Description",
                    "layer": "backend|middleware|design|frontend",
                    "dependencies": ["id-of-dependency-1", "id-of-dependency-2"],
                    "tech_stack": ["technology-1", "technology-2"]
                }}
            ],
            "architecture": {{
                "description": "Overall architecture description",
                "pattern": "Name of architecture pattern (e.g., MVC, Microservices)"
            }},
            "tech_stack": {{
                "backend": ["technology-1", "technology-2"],
                "middleware": ["technology-1", "technology-2"],
                "frontend": ["technology-1", "technology-2"],
                "database": ["technology-1", "technology-2"],
                "deployment": ["technology-1", "technology-2"]
            }}
        }}
        
        Be comprehensive and ensure all necessary components for a functional application are included.
        Make reasonable assumptions about the technology stack based on the description.
        """
        
        # Call LLM to decompose the project
        response = self.llm.chat([{"role": "user", "content": prompt}])
        
        # Extract JSON from response
        content = response.get("content", "")
        
        # Clean up content to extract valid JSON
        try:
            # Try to parse directly
            decomposition = json.loads(content)
        except json.JSONDecodeError:
            # Use regex to extract JSON object
            matches = re.search(r'```(?:json)?\s*({[\s\S]*?})\s*```', content)
            if matches:
                try:
                    decomposition = json.loads(matches.group(1))
                except json.JSONDecodeError:
                    # Fallback to a basic structure
                    decomposition = {
                        "components": [],
                        "architecture": {
                            "description": "Failed to parse architecture from LLM response",
                            "pattern": "Unknown"
                        },
                        "tech_stack": {
                            "backend": [],
                            "middleware": [],
                            "frontend": [],
                            "database": [],
                            "deployment": []
                        }
                    }
            else:
                # Create a fallback decomposition
                decomposition = {
                    "components": [],
                    "architecture": {
                        "description": "Failed to parse architecture from LLM response",
                        "pattern": "Unknown"
                    },
                    "tech_stack": {
                        "backend": [],
                        "middleware": [],
                        "frontend": [],
                        "database": [],
                        "deployment": []
                    }
                }
        
        # Generate IDs for components if not present
        for component in decomposition.get("components", []):
            if "id" not in component:
                component["id"] = str(uuid.uuid4())
        
        return decomposition
    
    def identify_layers(self, components: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Group components by layers.
        
        Args:
            components: List of components.
            
        Returns:
            Components grouped by layer.
        """
        layers = {
            "backend": [],
            "middleware": [],
            "frontend": []
        }
        
        for component in components:
            layer = component.get("layer", "backend")
            # Map all design tasks to frontend
            if layer == "design":
                layers["frontend"].append(component)
            elif layer in layers:
                layers[layer].append(component)
            else:
                layers["backend"].append(component)
        
        return layers
    
    def create_tasks(self, components: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Create tasks from components.
        
        Args:
            components: List of components.
            
        Returns:
            List of tasks.
        """
        tasks = []
        
        for component in components:
            component_id = component.get("id")
            component_name = component.get("name", "Unnamed Component")
            component_desc = component.get("description", "")
            component_layer = component.get("layer", "backend")
            component_deps = component.get("dependencies", [])
            component_tech = component.get("tech_stack", [])
            
            # Map design layer to frontend agent
            agent_name = "frontend" if component_layer == "design" else component_layer
            
            # Create a main task for the component
            main_task = {
                "id": f"task-{component_id}",
                "type": "implementation",
                "component_id": component_id,
                "name": f"Implement {component_name}",
                "description": f"Implement the {component_name} component. {component_desc}",
                "layer": component_layer,
                "agent": agent_name,
                "dependencies": component_deps,
                "tech_stack": component_tech
            }
            tasks.append(main_task)
            
            # Create a test task for the component
            test_task = {
                "id": f"test-{component_id}",
                "type": "testing",
                "component_id": component_id,
                "name": f"Test {component_name}",
                "description": f"Create tests for the {component_name} component.",
                "layer": component_layer,
                "dependencies": [main_task["id"]],
                "tech_stack": component_tech
            }
            tasks.append(test_task)
            
            # Create documentation task for the component
            doc_task = {
                "id": f"doc-{component_id}",
                "type": "documentation",
                "component_id": component_id,
                "name": f"Document {component_name}",
                "description": f"Create documentation for the {component_name} component.",
                "layer": component_layer,
                "dependencies": [main_task["id"]],
                "tech_stack": component_tech
            }
            tasks.append(doc_task)
        
        return tasks
    
    def build_dependency_graph(self, tasks: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """
        Build a dependency graph of tasks.
        
        Args:
            tasks: List of tasks.
            
        Returns:
            Task dependency graph.
        """
        # Create a mapping of task IDs to dependencies
        graph = {}
        
        for task in tasks:
            task_id = task.get("id")
            deps = task.get("dependencies", [])
            graph[task_id] = deps
        
        return graph
    
    def generate_fix_instructions(self, issues: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate instructions to fix identified issues.
        
        Args:
            issues: Dictionary of issues.
            
        Returns:
            List of fix tasks.
        """
        # Extract relevant information from issues
        issue_list = issues.get("issues", [])
        if not issue_list:
            return []
        
        prompt = f"""
        You are an expert software engineer. Analyze the following issues found in a project and generate
        specific fix instructions for each issue. Group them by component and layer.
        
        Issues:
        {json.dumps(issue_list, indent=2)}
        
        Please organize your response as a JSON array of fix tasks with the following structure:
        [
            {{
                "id": "fix-task-id",
                "name": "Fix task name",
                "description": "Detailed description of how to fix the issue",
                "layer": "backend|middleware|design|frontend",
                "component_id": "affected-component-id",
                "issue_id": "related-issue-id",
                "severity": "high|medium|low",
                "suggested_solution": "Specific code or solution suggestion"
            }}
        ]
        
        Be specific and clear with your fix instructions. If possible, provide sample code fragments.
        """
        
        # Call LLM to generate fix instructions
        response = self.llm.chat([{"role": "user", "content": prompt}])
        
        # Extract JSON from response
        content = response.get("content", "")
        
        # Clean up content to extract valid JSON
        try:
            # Try to parse directly
            fix_tasks = json.loads(content)
        except json.JSONDecodeError:
            # Use regex to extract JSON array
            matches = re.search(r'```(?:json)?\s*(\[[\s\S]*?\])\s*```', content)
            if matches:
                try:
                    fix_tasks = json.loads(matches.group(1))
                except json.JSONDecodeError:
                    # Create a basic fix task as fallback
                    fix_tasks = self._generate_fallback_fixes(issue_list)
            else:
                # Create fallback tasks
                fix_tasks = self._generate_fallback_fixes(issue_list)
        
        # Ensure each task has an ID
        for task in fix_tasks:
            if "id" not in task:
                task["id"] = f"fix-{uuid.uuid4()}"
        
        return fix_tasks
    
    def _generate_fallback_fixes(self, issues: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate fallback fix tasks when LLM parsing fails.
        
        Args:
            issues: List of issues.
            
        Returns:
            List of generic fix tasks.
        """
        fix_tasks = []
        
        for i, issue in enumerate(issues):
            issue_type = issue.get("type", "unknown")
            message = issue.get("message", "Unknown issue")
            component = issue.get("component", "Unknown component")
            layer = issue.get("layer", "backend")
            
            fix_tasks.append({
                "id": f"fix-{i+1}",
                "name": f"Fix {issue_type} issue in {component}",
                "description": f"Address the following issue: {message}",
                "layer": layer,
                "component_id": "unknown",
                "issue_id": i+1,
                "severity": issue.get("severity", "medium"),
                "suggested_solution": "Investigate and fix the reported issue."
            })
        
        return fix_tasks