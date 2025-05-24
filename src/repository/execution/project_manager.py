import os
import uuid
import datetime
from typing import Dict, List, Any, Optional
from src.service.tool_service import ToolService


class ProjectManager:
    """
    Manages project initialization, repository setup, and file operations.
    """
    
    def __init__(self, workspace_path: str, tool_service: ToolService):
        self.workspace_path = workspace_path
        self.tool_service = tool_service
        self.project_id: Optional[str] = None
        self.project_name: Optional[str] = None
        self.project_description: Optional[str] = None
        self.project_files: List[str] = []
        
    def initialize_project(self, project_description: str, project_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Initialize a new project with description and optional name.
        
        Args:
            project_description: Description of the project
            project_name: Optional project name, will be generated if not provided
            
        Returns:
            Result dictionary with success status and project information
        """
        try:
            # Generate project ID and name
            self.project_id = str(uuid.uuid4())
            
            if project_name:
                # Sanitize provided name
                self.project_name = self._sanitize_project_name(project_name)
            else:
                # Generate name from description
                self.project_name = self._generate_project_name(project_description)
            
            self.project_description = project_description
            
            # Initialize repository
            repo_result = self._initialize_repository()
            if not repo_result.get("success"):
                return repo_result
            
            return {
                "success": True,
                "project_id": self.project_id,
                "project_name": self.project_name,
                "message": f"Project '{self.project_name}' initialized successfully"
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to initialize project: {str(e)}"
            }
    
    def _sanitize_project_name(self, name: str) -> str:
        """Sanitize project name for filesystem compatibility."""
        import re
        # Remove/replace invalid characters and limit length
        sanitized = re.sub(r'[<>:"/\\|?*]', '_', name.strip())
        sanitized = re.sub(r'\s+', '_', sanitized)
        return sanitized[:50].lower()
    
    def _generate_project_name(self, description: str) -> str:
        """Generate project name from description."""
        import re
        # Extract key words and create a name
        words = re.findall(r'\b\w+\b', description.lower())
        key_words = [w for w in words if len(w) > 3 and w not in ['with', 'using', 'that', 'this', 'will', 'can', 'has']]
        
        if key_words:
            name = '_'.join(key_words[:3])
        else:
            name = f"project_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        return name[:50]
    
    def _initialize_repository(self) -> Dict[str, Any]:
        """
        Initialize the code repository (directory structure, basic files).
        """
        try:
            if not self.project_name:
                return {"success": False, "message": "Project name not set"}
            
            project_dir = os.path.join(self.workspace_path, self.project_name)
            
            # Create project directory structure
            directories = [
                project_dir,
                os.path.join(project_dir, "src"),
                os.path.join(project_dir, "src", "backend"),
                os.path.join(project_dir, "src", "frontend"),
                os.path.join(project_dir, "src", "middleware"),
                os.path.join(project_dir, "tests"),
                os.path.join(project_dir, "docs"),
                os.path.join(project_dir, "config")
            ]
            
            for directory in directories:
                os.makedirs(directory, exist_ok=True)
            
            # Create basic files
            self._create_basic_files(project_dir)
            
            # Initialize git repository
            self._initialize_git(project_dir)
            
            # Update project files list
            self.project_files = self._collect_project_files()
            
            return {"success": True, "message": "Repository initialized successfully"}
            
        except Exception as e:
            return {"success": False, "message": f"Repository initialization failed: {str(e)}"}
    
    def _create_basic_files(self, project_dir: str):
        """Create basic project files."""
        # README.md
        readme_content = f"""# {self.project_name}

{self.project_description}

## Project Structure

```
{self.project_name}/
├── src/
│   ├── backend/
│   ├── frontend/
│   └── middleware/
├── tests/
├── docs/
└── config/
```

## Getting Started

[Instructions will be added during development]
"""
        with open(os.path.join(project_dir, "README.md"), 'w', encoding='utf-8') as f:
            f.write(readme_content)
        
        # .gitignore
        gitignore_content = """# Dependencies
node_modules/
__pycache__/
*.pyc
*.pyo
*.pyd

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Build outputs
dist/
build/
*.egg-info/

# Environment
.env
.env.local
"""
        with open(os.path.join(project_dir, ".gitignore"), 'w', encoding='utf-8') as f:
            f.write(gitignore_content)
    
    def _initialize_git(self, project_dir: str):
        """Initialize git repository."""
        init_command = f'cd "{project_dir}" && git init'
        self.tool_service.run_bash_command(init_command)
        
        # Initial commit
        add_command = f'cd "{project_dir}" && git add .'
        self.tool_service.run_bash_command(add_command)
        
        commit_command = f'cd "{project_dir}" && git commit -m "Initial project setup"'
        self.tool_service.run_bash_command(commit_command)
    
    def save_code_to_file(self, relative_file_path: str, content: str) -> str:
        """
        Save generated code to a file, relative to the project root.
        
        Args:
            relative_file_path: Relative path to the file within the project
            content: File content
            
        Returns:
            Absolute saved file path
        """
        if not self.project_name:
            raise ValueError("Project name is not set. Cannot save file.")
            
        project_root_dir = os.path.join(self.workspace_path, self.project_name)
        
        # Security check for path traversal
        if os.path.isabs(relative_file_path) or relative_file_path.startswith((".."+os.sep, os.sep)):
            raise ValueError(f"Invalid relative_file_path: {relative_file_path}")

        absolute_file_path = os.path.join(project_root_dir, relative_file_path)
        
        # Ensure the path is within project directory
        if not os.path.abspath(absolute_file_path).startswith(os.path.abspath(project_root_dir)):
            raise ValueError(f"File path attempts to escape project directory")

        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(absolute_file_path), exist_ok=True)
        
        # Write file
        with open(absolute_file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Add to project files list
        if relative_file_path not in self.project_files:
            self.project_files.append(relative_file_path)
            self.project_files.sort()

        return absolute_file_path
    
    def commit_changes(self, message: str) -> bool:
        """
        Commit changes to the repository using Git.
        
        Args:
            message: Commit message
            
        Returns:
            True if successful, False otherwise
        """
        if not self.project_name:
            return False

        project_dir = os.path.join(self.workspace_path, self.project_name)
        
        add_command = f'cd "{project_dir}" && git add .'
        add_result = self.tool_service.run_bash_command(add_command)
        
        if add_result.get('exit_code', 1) != 0:
            return False

        commit_command = f'cd "{project_dir}" && git commit -m "{message}"'
        commit_result = self.tool_service.run_bash_command(commit_command)

        return commit_result.get('exit_code', 1) == 0
    
    def _collect_project_files(self) -> List[str]:
        """
        Collect all files in the project.
        
        Returns:
            List of relative file paths
        """
        if not self.project_name:
            return []
            
        project_dir = os.path.join(self.workspace_path, self.project_name)
        files = []
        
        for root, _, filenames in os.walk(project_dir):
            for filename in filenames:
                rel_path = os.path.relpath(os.path.join(root, filename), project_dir)
                files.append(rel_path)
                
        return files
    
    def get_project_structure(self, max_depth: int = 3) -> Dict[str, Any]:
        """
        Get the directory structure of the project.

        Args:
            max_depth: Maximum depth to traverse

        Returns:
            Directory structure
        """
        if not self.project_name:
            return {"error": "Project not initialized"}
            
        project_dir = os.path.join(self.workspace_path, self.project_name)
        structure = {}
        
        if not os.path.exists(project_dir):
            return {"error": "Project directory does not exist"}

        for root, dirs, files in os.walk(project_dir, topdown=True):
            depth = root.replace(project_dir, '').count(os.sep)
            if depth >= max_depth:
                dirs[:] = []

            relative_root = os.path.relpath(root, project_dir)
            if relative_root == ".":
                current_level = structure
            else:
                parts = relative_root.split(os.sep)
                current_level = structure
                for part in parts:
                    if part not in current_level:
                        current_level[part] = {}
                    current_level = current_level[part]
            
            for d in dirs:
                if depth + 1 < max_depth:
                    current_level[d] = {}
                else:
                    current_level[d] = "directory"

            for f_name in files:
                current_level[f_name] = "file"
        
        return structure
    
    def get_project_info(self) -> Dict[str, Any]:
        """Get current project information."""
        return {
            "project_id": self.project_id,
            "project_name": self.project_name,
            "project_description": self.project_description,
            "project_files_count": len(self.project_files),
            "project_files": self.project_files.copy()
        }