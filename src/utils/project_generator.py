"""
Project Generator for Automated Workflow System

This module handles generating projects using the existing orchestration engine
with dynamic prompts and provides comprehensive project analysis.
"""

import os
import json
import time
import uuid
import traceback
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import logging

from repository.execution.orchestration_engine import OrchestrationEngine
from service.llm_factory import LLMFactory
from service.tool_service import ToolService
from utils.prompt_manager import PromptManager

logger = logging.getLogger(__name__)

class ProjectGenerator:
    """Handles automated project generation using the orchestration engine."""
    
    def __init__(self, workspace_base_path: str, llm_factory: LLMFactory, tool_service: ToolService):
        """
        Initialize the project generator.
        
        Args:
            workspace_base_path: Base directory for generated projects
            llm_factory: Factory for creating LLM instances
            tool_service: Service for accessing tools
        """
        self.workspace_base_path = Path(workspace_base_path)
        self.llm_factory = llm_factory
        self.tool_service = tool_service
        self.prompt_manager = PromptManager()
        
        # Create base workspace if it doesn't exist
        self.workspace_base_path.mkdir(parents=True, exist_ok=True)
        
        # Generation history
        self.generation_history = []
        
    def generate_project(
        self, 
        prompt: Optional[str] = None,
        prompt_method: str = "interactive",
        prompt_key: Optional[str] = None,
        project_name: Optional[str] = None,
        async_execution: bool = True
    ) -> Dict[str, Any]:
        """
        Generate a complete project using the orchestration engine.
        
        Args:
            prompt: Custom prompt for project generation
            prompt_method: Method to get prompt ("interactive", "preset", "custom", "env")
            prompt_key: Key for preset prompt (if using preset method)
            project_name: Optional custom project name
            async_execution: Whether to run generation asynchronously
            
        Returns:
            Generation result with project details
        """
        try:
            logger.info("🚀 Starting project generation...")
            start_time = time.time()
            
            # Get user prompt
            if prompt:
                user_prompt = prompt
                logger.info(f"Using provided prompt: {user_prompt[:100]}...")
            else:
                user_prompt = self.prompt_manager.get_user_prompt(
                    method=prompt_method,
                    prompt_key=prompt_key,
                    custom_prompt=prompt
                )
            
            # Generate unique project name if not provided
            if not project_name:
                project_name = self._generate_project_name(user_prompt)
            
            # Create project workspace
            project_workspace = self.workspace_base_path / project_name
            project_workspace.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"📁 Project workspace: {project_workspace}")
            
            # Initialize orchestration engine
            orchestration_engine = OrchestrationEngine(
                workspace_path=str(project_workspace),
                llm_factory=self.llm_factory,
                tool_service=self.tool_service
            )
            
            # Run full workflow
            logger.info("⚙️ Running orchestration workflow...")
            result = orchestration_engine.run_full_workflow(
                user_prompt=user_prompt,
                project_name=project_name
            )
            
            end_time = time.time()
            generation_time = end_time - start_time
            
            # Analyze generated project
            logger.info("🔍 Analyzing generated project...")
            project_analysis = self._analyze_generated_project(
                result.get("project_output_directory", str(project_workspace))
            )
            
            # Create generation record
            generation_record = {
                "id": str(uuid.uuid4()),
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "user_prompt": user_prompt,
                "project_name": project_name,
                "project_workspace": str(project_workspace),
                "project_output_directory": result.get("project_output_directory"),
                "generation_time_seconds": round(generation_time, 2),
                "success": result.get("success", False),
                "orchestration_result": result,
                "project_analysis": project_analysis,
                "deployment_ready": project_analysis.get("has_deployment_files", False)
            }
            
            # Save generation history
            self.generation_history.append(generation_record)
            self._save_generation_history()
            
            logger.info(f"✅ Project generation completed in {generation_time:.2f}s")
            
            return generation_record
            
        except Exception as e:
            logger.error(f"❌ Project generation failed: {str(e)}")
            error_record = {
                "id": str(uuid.uuid4()),
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "user_prompt": prompt or "Unknown",
                "project_name": project_name or "Unknown",
                "success": False,
                "error": str(e),
                "traceback": traceback.format_exc()
            }
            self.generation_history.append(error_record)
            return error_record
    
    def _generate_project_name(self, prompt: str) -> str:
        """Generate a unique project name based on the prompt."""
        # Extract keywords from prompt
        words = prompt.lower().split()
        relevant_words = [w for w in words if len(w) > 3 and w.isalpha()][:3]
        
        if relevant_words:
            base_name = "_".join(relevant_words)
        else:
            base_name = "project"
        
        # Add timestamp for uniqueness
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        return f"{base_name}_{timestamp}"
    
    def _analyze_generated_project(self, project_path: str) -> Dict[str, Any]:
        """
        Analyze the generated project structure and files.
        
        Args:
            project_path: Path to the generated project
            
        Returns:
            Analysis results
        """
        try:
            project_path = Path(project_path)
            
            if not project_path.exists():
                return {"error": "Project path does not exist", "files": []}
            
            # Collect all files
            all_files = []
            for root, dirs, files in os.walk(project_path):
                for file in files:
                    file_path = Path(root) / file
                    relative_path = file_path.relative_to(project_path)
                    all_files.append({
                        "path": str(relative_path),
                        "full_path": str(file_path),
                        "size": file_path.stat().st_size if file_path.exists() else 0,
                        "extension": file_path.suffix.lower()
                    })
            
            # Analyze project type
            project_type = self._detect_project_type([f["path"] for f in all_files])
            
            # Analyze file types
            file_extensions = {}
            for file in all_files:
                ext = file["extension"]
                if ext:
                    file_extensions[ext] = file_extensions.get(ext, 0) + 1
            
            # Check for deployment files
            deployment_files = [
                "package.json", "requirements.txt", "Dockerfile", "docker-compose.yml",
                "go.mod", "pom.xml", "build.gradle", "Cargo.toml"
            ]
            has_deployment_files = any(
                any(f["path"].endswith(dep_file) for f in all_files)
                for dep_file in deployment_files
            )
            
            # Check for configuration files
            config_files = [f for f in all_files if any(
                f["path"].endswith(ext) for ext in [".json", ".yaml", ".yml", ".toml", ".ini", ".env"]
            )]
            
            # Check for source code files
            source_files = [f for f in all_files if any(
                f["path"].endswith(ext) for ext in [".py", ".js", ".ts", ".java", ".go", ".rs", ".cpp", ".c"]
            )]
            
            return {
                "total_files": len(all_files),
                "file_extensions": file_extensions,
                "project_type": project_type,
                "has_deployment_files": has_deployment_files,
                "config_files_count": len(config_files),
                "source_files_count": len(source_files),
                "all_files": [f["path"] for f in all_files],
                "deployment_files": [f["path"] for f in all_files if any(
                    f["path"].endswith(dep_file) for dep_file in deployment_files
                )],
                "config_files": [f["path"] for f in config_files],
                "source_files": [f["path"] for f in source_files]
            }
            
        except Exception as e:
            logger.error(f"Error analyzing project: {str(e)}")
            return {"error": str(e), "files": []}
    
    def _detect_project_type(self, files: List[str]) -> str:
        """Detect project type based on file names."""
        file_names = [os.path.basename(f) for f in files]
        
        if "package.json" in file_names:
            return "nodejs"
        elif "requirements.txt" in file_names or any(f.endswith(".py") for f in files):
            return "python"
        elif "go.mod" in file_names:
            return "go"
        elif "pom.xml" in file_names:
            return "java"
        elif "Cargo.toml" in file_names:
            return "rust"
        elif any(f.endswith(".cs") for f in files):
            return "dotnet"
        elif any(f.endswith(".html") for f in files):
            return "web"
        else:
            return "unknown"
    
    def _save_generation_history(self):
        """Save generation history to file."""
        try:
            history_file = self.workspace_base_path / "generation_history.json"
            with open(history_file, 'w') as f:
                json.dump(self.generation_history, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save generation history: {str(e)}")
    
    def load_generation_history(self) -> List[Dict[str, Any]]:
        """Load generation history from file."""
        try:
            history_file = self.workspace_base_path / "generation_history.json"
            if history_file.exists():
                with open(history_file, 'r') as f:
                    self.generation_history = json.load(f)
            return self.generation_history
        except Exception as e:
            logger.error(f"Failed to load generation history: {str(e)}")
            return []
    
    def get_latest_project(self) -> Optional[Dict[str, Any]]:
        """Get the latest successfully generated project."""
        successful_projects = [p for p in self.generation_history if p.get("success")]
        return successful_projects[-1] if successful_projects else None
    
    def list_generated_projects(self) -> List[Dict[str, Any]]:
        """List all generated projects with basic info."""
        return [{
            "id": p.get("id"),
            "project_name": p.get("project_name"),
            "timestamp": p.get("timestamp"),
            "success": p.get("success"),
            "project_type": p.get("project_analysis", {}).get("project_type"),
            "total_files": p.get("project_analysis", {}).get("total_files"),
            "deployment_ready": p.get("deployment_ready")
        } for p in self.generation_history]
    
    def generate_batch_projects(self, prompts: List[str], project_names: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Generate multiple projects in batch.
        
        Args:
            prompts: List of prompts for project generation
            project_names: Optional list of project names
            
        Returns:
            List of generation results
        """
        results = []
        
        for i, prompt in enumerate(prompts):
            project_name = project_names[i] if project_names and i < len(project_names) else None
            
            logger.info(f"🔄 Generating project {i+1}/{len(prompts)}")
            result = self.generate_project(
                prompt=prompt,
                prompt_method="custom",
                project_name=project_name
            )
            results.append(result)
            
            # Add delay between generations to avoid overwhelming the system
            time.sleep(2)
        
        return results

# Convenience functions for easy import
def generate_project_quick(prompt: str, workspace_path: str = "./generated_projects") -> Dict[str, Any]:
    """Quick project generation with minimal setup."""
    from service.llm_factory import LLMFactory
    from service.tool_service import ToolService
    from repository.tools.bash_tool import BashTool
    
    # Setup basic services
    llm_factory = LLMFactory()
    tool_service = ToolService()
    tool_service.register_tool(BashTool())
    
    # Generate project
    generator = ProjectGenerator(workspace_path, llm_factory, tool_service)
    return generator.generate_project(prompt=prompt, prompt_method="custom")

if __name__ == "__main__":
    # Test the project generator
    test_prompt = "Create a simple FastAPI application with user authentication"
    result = generate_project_quick(test_prompt)
    print(f"Generation result: {result}")
