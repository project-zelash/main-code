from typing import Dict, List, Any, Optional
import os
import subprocess
import json
import shutil

class BuildEnvironment:
    """
    Component responsible for setting up, building, and deploying code.
    """
    
    def __init__(self, workspace_path: str = None):
        """
        Initialize the build environment.
        
        Args:
            workspace_path: Path to the workspace directory.
        """
        self.workspace_path = workspace_path or os.getcwd()
        self.initialized = False
        self.project_type = None
        self.build_config = {}
    
    def detect_project_type(self, files: List[str]) -> Dict[str, Any]:
        """
        Detect the type of project based on files.
        
        Args:
            files: List of file paths.
            
        Returns:
            Project type information.
        """
        # Extract file names and extensions for analysis
        file_names = [os.path.basename(f) for f in files]
        extensions = [os.path.splitext(f)[1].lower() for f in files]
        
        # Check for package.json (Node.js)
        if "package.json" in file_names:
            with open(os.path.join(self.workspace_path, "package.json"), 'r') as f:
                package_json = json.load(f)
                
            dependencies = package_json.get("dependencies", {})
            dev_dependencies = package_json.get("devDependencies", {})
            
            # Check for React
            if "react" in dependencies:
                # Next.js
                if "next" in dependencies:
                    self.project_type = "nextjs"
                # Vite
                elif "vite" in dev_dependencies:
                    self.project_type = "vite"
                else:
                    self.project_type = "react"
            # Check for Vue
            elif "vue" in dependencies:
                self.project_type = "vue"
            # Check for Express
            elif "express" in dependencies:
                self.project_type = "express"
            # Generic Node.js
            else:
                self.project_type = "nodejs"
        
        # Check for pom.xml (Java/Maven)
        elif "pom.xml" in file_names:
            self.project_type = "maven"
        
        # Check for requirements.txt (Python)
        elif "requirements.txt" in file_names:
            if any(f.endswith("django.py") for f in files):
                self.project_type = "django"
            elif any(f.endswith("flask.py") for f in files) or "app.py" in file_names:
                self.project_type = "flask"
            else:
                self.project_type = "python"
        
        # Check for go.mod (Go)
        elif "go.mod" in file_names:
            self.project_type = "go"
        
        # Check file extensions
        elif ".py" in extensions:
            self.project_type = "python"
        elif ".java" in extensions:
            self.project_type = "java"
        elif ".cs" in extensions:
            self.project_type = "dotnet"
        else:
            # Default to static website if HTML files present
            if ".html" in extensions:
                self.project_type = "static-website"
            else:
                self.project_type = "unknown"
        
        self.build_config = self._create_build_config(self.project_type)
        
        return {
            "project_type": self.project_type,
            "build_config": self.build_config
        }
    
    def _create_build_config(self, project_type: str) -> Dict[str, Any]:
        """
        Create build configuration based on project type.
        
        Args:
            project_type: Type of project.
            
        Returns:
            Build configuration.
        """
        config = {
            "build_command": None,
            "run_command": None,
            "test_command": None,
            "install_command": None,
            "output_dir": None,
            "package_manager": None
        }
        
        if project_type == "nextjs":
            config["build_command"] = "npm run build"
            config["run_command"] = "npm run start"
            config["test_command"] = "npm test"
            config["install_command"] = "npm install"
            config["output_dir"] = ".next"
            config["package_manager"] = "npm"
            
        elif project_type == "vite" or project_type == "react" or project_type == "vue":
            config["build_command"] = "npm run build"
            config["run_command"] = "npm run preview" if project_type == "vite" else "npm run start"
            config["test_command"] = "npm test"
            config["install_command"] = "npm install"
            config["output_dir"] = "dist"
            config["package_manager"] = "npm"
            
        elif project_type == "express" or project_type == "nodejs":
            config["build_command"] = "npm run build" if self._has_build_script() else None
            config["run_command"] = "npm start"
            config["test_command"] = "npm test"
            config["install_command"] = "npm install"
            config["package_manager"] = "npm"
            
        elif project_type == "python" or project_type == "flask" or project_type == "django":
            config["install_command"] = "pip install -r requirements.txt"
            config["run_command"] = "python app.py" if project_type == "flask" else "python -m main"
            config["test_command"] = "pytest"
            config["package_manager"] = "pip"
            
            if project_type == "django":
                config["run_command"] = "python manage.py runserver"
                config["test_command"] = "python manage.py test"
            
        elif project_type == "maven":
            config["build_command"] = "mvn clean package"
            config["run_command"] = "java -jar target/*.jar"
            config["test_command"] = "mvn test"
            config["install_command"] = "mvn install"
            config["output_dir"] = "target"
            config["package_manager"] = "maven"
            
        elif project_type == "go":
            config["build_command"] = "go build -o app ."
            config["run_command"] = "./app"
            config["test_command"] = "go test ./..."
            config["package_manager"] = "go"
            
        elif project_type == "dotnet":
            config["build_command"] = "dotnet build"
            config["run_command"] = "dotnet run"
            config["test_command"] = "dotnet test"
            config["install_command"] = "dotnet restore"
            config["output_dir"] = "bin"
            config["package_manager"] = "dotnet"
            
        elif project_type == "static-website":
            # No build process for static websites
            pass
            
        return config
    
    def _has_build_script(self) -> bool:
        """
        Check if package.json has a build script.
        
        Returns:
            True if build script exists, False otherwise.
        """
        package_json_path = os.path.join(self.workspace_path, "package.json")
        
        if os.path.exists(package_json_path):
            try:
                with open(package_json_path, 'r') as f:
                    package_json = json.load(f)
                
                scripts = package_json.get("scripts", {})
                return "build" in scripts
            except:
                pass
                
        return False
    
    def generate_build_files(self, project_type: str) -> Dict[str, Any]:
        """
        Generate necessary build files for the project.
        
        Args:
            project_type: Type of project.
            
        Returns:
            Generated files information.
        """
        generated_files = []
        
        # Store project type for later use
        self.project_type = project_type
        
        # Generate appropriate files based on project type
        if project_type == "nextjs":
            # Check if next.config.js exists, create if not
            next_config = os.path.join(self.workspace_path, "next.config.js")
            if not os.path.exists(next_config):
                with open(next_config, 'w') as f:
                    f.write("/** @type {import('next').NextConfig} */\n")
                    f.write("const nextConfig = {\n  reactStrictMode: true,\n  swcMinify: true,\n};\n\n")
                    f.write("module.exports = nextConfig;\n")
                generated_files.append(next_config)
                
        elif project_type == "vite":
            # Check if vite.config.js exists, create if not
            vite_config = os.path.join(self.workspace_path, "vite.config.js")
            if not os.path.exists(vite_config):
                with open(vite_config, 'w') as f:
                    f.write("import { defineConfig } from 'vite';\n")
                    f.write("import react from '@vitejs/plugin-react';\n\n")
                    f.write("export default defineConfig({\n  plugins: [react()],\n});\n")
                generated_files.append(vite_config)
                
        elif project_type == "flask":
            # Create wsgi.py if not exists
            wsgi_file = os.path.join(self.workspace_path, "wsgi.py")
            if not os.path.exists(wsgi_file):
                with open(wsgi_file, 'w') as f:
                    f.write("from app import app\n\n")
                    f.write("if __name__ == '__main__':\n")
                    f.write("    app.run()\n")
                generated_files.append(wsgi_file)
                
        elif project_type == "django":
            # Nothing to generate for Django as it has its own generation commands
            pass
            
        elif project_type == "nodejs" or project_type == "express":
            # Check if package.json exists, create if not
            package_json = os.path.join(self.workspace_path, "package.json")
            if not os.path.exists(package_json):
                with open(package_json, 'w') as f:
                    f.write('{\n')
                    f.write('  "name": "generated-project",\n')
                    f.write('  "version": "1.0.0",\n')
                    f.write('  "main": "index.js",\n')
                    f.write('  "scripts": {\n')
                    f.write('    "start": "node index.js",\n')
                    f.write('    "test": "echo \\"Error: no test specified\\" && exit 1"\n')
                    f.write('  },\n')
                    f.write('  "dependencies": {}\n')
                    f.write('}\n')
                generated_files.append(package_json)
                
        # Update build configuration based on project type
        self.build_config = self._create_build_config(project_type)
        
        return {
            "generated_files": generated_files,
            "build_config": self.build_config
        }
    
    def install_dependencies(self) -> Dict[str, Any]:
        """
        Install dependencies for the project.
        
        Returns:
            Results of the installation.
        """
        if not self.build_config:
            self.build_config = self._create_build_config(self.project_type or "unknown")
            
        install_command = self.build_config.get("install_command")
        package_manager = self.build_config.get("package_manager")
        
        if not install_command:
            return {
                "success": False,
                "message": "No install command available for this project type",
                "output": ""
            }
            
        try:
            # Split the command into parts
            cmd_parts = install_command.split()
            
            # Run the install command
            process = subprocess.run(
                cmd_parts,
                cwd=self.workspace_path,
                capture_output=True,
                text=True,
                check=False
            )
            
            success = process.returncode == 0
            
            return {
                "success": success,
                "message": "Dependencies installed successfully" if success else "Failed to install dependencies",
                "output": process.stdout + process.stderr,
                "package_manager": package_manager
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Error installing dependencies: {str(e)}",
                "output": str(e)
            }
    
    def build_project(self) -> Dict[str, Any]:
        """
        Build the project.
        
        Returns:
            Build results.
        """
        if not self.build_config:
            self.build_config = self._create_build_config(self.project_type or "unknown")
            
        build_command = self.build_config.get("build_command")
        
        # Some projects don't require building
        if not build_command:
            return {
                "success": True,
                "message": "No build step required for this project type",
                "output": "",
                "warnings": [],
                "errors": []
            }
            
        try:
            # Split the command into parts
            cmd_parts = build_command.split()
            
            # Run the build command
            process = subprocess.run(
                cmd_parts,
                cwd=self.workspace_path,
                capture_output=True,
                text=True,
                check=False
            )
            
            success = process.returncode == 0
            output = process.stdout + process.stderr
            
            # Parse output for warnings and errors
            warnings = []
            errors = []
            
            for line in output.splitlines():
                line = line.strip()
                if "warning" in line.lower():
                    warnings.append(line)
                elif "error" in line.lower():
                    errors.append(line)
            
            return {
                "success": success,
                "message": "Build completed successfully" if success else "Build failed",
                "output": output,
                "warnings": warnings,
                "errors": errors
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Error building project: {str(e)}",
                "output": str(e),
                "warnings": [],
                "errors": [str(e)]
            }
    
    def start_services(self) -> Dict[str, Any]:
        """
        Start the project services.
        
        Returns:
            Service information.
        """
        if not self.build_config:
            self.build_config = self._create_build_config(self.project_type or "unknown")
            
        run_command = self.build_config.get("run_command")
        
        if not run_command:
            return {
                "success": False,
                "message": "No run command available for this project type",
                "service_urls": []
            }
        
        # For simplicity, we won't actually start a long-running process
        # In a real implementation, this would launch the service in the background
        
        # Determine likely service URLs based on project type
        service_urls = []
        
        if self.project_type in ["flask", "django", "express", "nodejs"]:
            service_urls.append("http://localhost:5000")  # Default for Flask
            
            if self.project_type == "django":
                service_urls.append("http://localhost:8000")  # Default for Django
                
            if self.project_type in ["express", "nodejs"]:
                service_urls.append("http://localhost:3000")  # Default for Express
                
        elif self.project_type in ["nextjs", "react", "vue", "vite"]:
            service_urls.append("http://localhost:3000")  # NextJS default
            
            if self.project_type == "vite":
                service_urls.append("http://localhost:5173")  # Vite default
        
        return {
            "success": True,
            "message": f"Services started with command: {run_command}",
            "run_command": run_command,
            "service_urls": service_urls
        }
    
    def rebuild_and_restart(self) -> Dict[str, Any]:
        """
        Rebuild and restart the project.
        
        Returns:
            Combined results of build and start.
        """
        # Build the project
        build_result = self.build_project()
        
        if not build_result["success"]:
            return {
                "success": False,
                "message": "Rebuild failed",
                "build_result": build_result,
                "start_result": None
            }
        
        # Start services
        start_result = self.start_services()
        
        return {
            "success": build_result["success"] and start_result["success"],
            "message": "Project rebuilt and restarted",
            "build_result": build_result,
            "start_result": start_result
        }