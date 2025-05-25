"""
Smart Deployment Manager for Automated Workflow System

This module handles automatic deployment of any project structure by detecting
project types and deploying them locally with appropriate commands.
"""

import os
import json
import time
import subprocess
import signal
import threading
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import logging
import psutil
import requests
from urllib.parse import urlparse

from repository.tools.bash_tool import BashTool

logger = logging.getLogger(__name__)

class DeploymentManager:
    """Handles automatic deployment of any project structure."""
    
    def __init__(self, bash_tool: Optional[BashTool] = None):
        """
        Initialize the deployment manager.
        
        Args:
            bash_tool: Optional BashTool instance for command execution
        """
        self.bash_tool = bash_tool or BashTool()
        self.active_deployments = {}
        self.deployment_history = []
        
    def deploy_project(self, project_path: str, force_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Automatically deploy a project by detecting its type and running appropriate commands.
        
        Args:
            project_path: Path to the project directory
            force_type: Force a specific project type instead of auto-detection
            
        Returns:
            Deployment result with service URLs and process info
        """
        try:
            project_path = Path(project_path).resolve()
            
            if not project_path.exists():
                return {"success": False, "error": f"Project path does not exist: {project_path}"}
            
            logger.info(f"🚀 Starting deployment for project: {project_path.name}")
            
            # Detect project type
            if force_type:
                project_type = force_type
                logger.info(f"🔧 Using forced project type: {project_type}")
            else:
                project_type = self._detect_project_type(project_path)
                logger.info(f"🔍 Detected project type: {project_type}")
            
            # Get deployment configuration
            deployment_config = self._get_deployment_config(project_type)
            if not deployment_config:
                return {"success": False, "error": f"Unsupported project type: {project_type}"}
            
            # Change to project directory
            original_cwd = os.getcwd()
            os.chdir(project_path)
            
            try:
                # Install dependencies
                if deployment_config.get("install_command"):
                    logger.info(f"📦 Installing dependencies...")
                    install_result = self._execute_command(deployment_config["install_command"])
                    if not install_result["success"]:
                        return {"success": False, "error": f"Failed to install dependencies: {install_result['error']}"}
                
                # Build project if needed
                if deployment_config.get("build_command"):
                    logger.info(f"🔨 Building project...")
                    build_result = self._execute_command(deployment_config["build_command"])
                    if not build_result["success"]:
                        return {"success": False, "error": f"Failed to build project: {build_result['error']}"}
                
                # Start the service
                if deployment_config.get("run_command"):
                    logger.info(f"🌐 Starting service...")
                    service_result = self._start_service(
                        deployment_config["run_command"],
                        project_path,
                        deployment_config.get("expected_ports", [])
                    )
                    
                    if service_result["success"]:
                        # Register active deployment
                        deployment_id = f"{project_path.name}_{int(time.time())}"
                        self.active_deployments[deployment_id] = {
                            "project_path": str(project_path),
                            "project_type": project_type,
                            "process_id": service_result.get("process_id"),
                            "service_urls": service_result.get("service_urls", []),
                            "started_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                            "config": deployment_config
                        }
                        
                        # Add to deployment history
                        self.deployment_history.append({
                            "deployment_id": deployment_id,
                            "project_name": project_path.name,
                            "project_path": str(project_path),
                            "project_type": project_type,
                            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                            "success": True,
                            "service_urls": service_result.get("service_urls", [])
                        })
                        
                        logger.info(f"✅ Deployment successful!")
                        
                        return {
                            "success": True,
                            "deployment_id": deployment_id,
                            "project_type": project_type,
                            "service_urls": service_result.get("service_urls", []),
                            "process_id": service_result.get("process_id"),
                            "config": deployment_config
                        }
                    else:
                        return {"success": False, "error": f"Failed to start service: {service_result['error']}"}
                else:
                    # No run command - might be a static site or build-only project
                    return {
                        "success": True,
                        "deployment_id": f"{project_path.name}_static_{int(time.time())}",
                        "project_type": project_type,
                        "service_urls": [],
                        "message": "Project built successfully (no service to start)"
                    }
                    
            finally:
                os.chdir(original_cwd)
                
        except Exception as e:
            logger.error(f"❌ Deployment failed: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _detect_project_type(self, project_path: Path) -> str:
        """Detect project type based on files in the directory."""
        files = [f.name for f in project_path.iterdir() if f.is_file()]
        
        # Node.js projects
        if "package.json" in files:
            try:
                with open(project_path / "package.json", 'r') as f:
                    package_json = json.load(f)
                    dependencies = package_json.get("dependencies", {})
                    dev_dependencies = package_json.get("devDependencies", {})
                    
                if "next" in dependencies:
                    return "nextjs"
                elif "react" in dependencies and "vite" in dev_dependencies:
                    return "vite-react"
                elif "vue" in dependencies and "vite" in dev_dependencies:
                    return "vite-vue"
                elif "react" in dependencies:
                    return "react"
                elif "vue" in dependencies:
                    return "vue"
                elif "express" in dependencies:
                    return "express"
                else:
                    return "nodejs"
            except:
                return "nodejs"
        
        # Python projects
        elif "requirements.txt" in files or "pyproject.toml" in files:
            if "manage.py" in files:
                return "django"
            elif "app.py" in files or any(f.startswith("main") and f.endswith(".py") for f in files):
                return "flask"
            else:
                return "python"
        
        # Go projects
        elif "go.mod" in files:
            return "go"
        
        # Java projects
        elif "pom.xml" in files:
            return "maven"
        elif "build.gradle" in files:
            return "gradle"
        
        # Rust projects
        elif "Cargo.toml" in files:
            return "rust"
        
        # .NET projects
        elif any(f.endswith(".csproj") or f.endswith(".sln") for f in files):
            return "dotnet"
        
        # Docker projects
        elif "Dockerfile" in files:
            return "docker"
        
        # Static websites
        elif any(f.endswith(".html") for f in files):
            return "static"
        
        else:
            return "unknown"
    
    def _get_deployment_config(self, project_type: str) -> Optional[Dict[str, Any]]:
        """Get deployment configuration for a project type."""
        configs = {
            "nextjs": {
                "install_command": "npm install",
                "build_command": "npm run build",
                "run_command": "npm run start",
                "expected_ports": [3000],
                "health_check_paths": ["/"]
            },
            "vite-react": {
                "install_command": "npm install",
                "build_command": "npm run build",
                "run_command": "npm run preview",
                "expected_ports": [4173, 5173],
                "health_check_paths": ["/"]
            },
            "vite-vue": {
                "install_command": "npm install",
                "build_command": "npm run build", 
                "run_command": "npm run preview",
                "expected_ports": [4173, 5173],
                "health_check_paths": ["/"]
            },
            "react": {
                "install_command": "npm install",
                "run_command": "npm start",
                "expected_ports": [3000],
                "health_check_paths": ["/"]
            },
            "vue": {
                "install_command": "npm install",
                "run_command": "npm run serve",
                "expected_ports": [8080, 3000],
                "health_check_paths": ["/"]
            },
            "express": {
                "install_command": "npm install",
                "run_command": "npm start",
                "expected_ports": [3000, 8000],
                "health_check_paths": ["/", "/api"]
            },
            "nodejs": {
                "install_command": "npm install",
                "run_command": "npm start",
                "expected_ports": [3000, 8000],
                "health_check_paths": ["/"]
            },
            "django": {
                "install_command": "pip install -r requirements.txt",
                "run_command": "python manage.py runserver",
                "expected_ports": [8000],
                "health_check_paths": ["/", "/admin"]
            },
            "flask": {
                "install_command": "pip install -r requirements.txt",
                "run_command": "python app.py",
                "expected_ports": [5000, 8000],
                "health_check_paths": ["/"]
            },
            "python": {
                "install_command": "pip install -r requirements.txt",
                "run_command": "python main.py",
                "expected_ports": [8000, 5000],
                "health_check_paths": ["/"]
            },
            "go": {
                "build_command": "go build -o app .",
                "run_command": "./app",
                "expected_ports": [8080, 3000],
                "health_check_paths": ["/"]
            },
            "maven": {
                "install_command": "mvn clean install",
                "build_command": "mvn package",
                "run_command": "java -jar target/*.jar",
                "expected_ports": [8080],
                "health_check_paths": ["/"]
            },
            "gradle": {
                "install_command": "./gradlew build",
                "run_command": "./gradlew bootRun",
                "expected_ports": [8080],
                "health_check_paths": ["/"]
            },
            "rust": {
                "build_command": "cargo build --release",
                "run_command": "cargo run",
                "expected_ports": [8080, 3000],
                "health_check_paths": ["/"]
            },
            "dotnet": {
                "install_command": "dotnet restore",
                "build_command": "dotnet build",
                "run_command": "dotnet run",
                "expected_ports": [5000, 5001],
                "health_check_paths": ["/"]
            },
            "docker": {
                "build_command": "docker build -t app .",
                "run_command": "docker run -p 3000:3000 app",
                "expected_ports": [3000],
                "health_check_paths": ["/"]
            },
            "static": {
                "run_command": "python -m http.server 8000",
                "expected_ports": [8000],
                "health_check_paths": ["/"]
            }
        }
        
        return configs.get(project_type)
    
    def _execute_command(self, command: str, timeout: int = 300) -> Dict[str, Any]:
        """Execute a command and return the result."""
        try:
            logger.info(f"🔧 Executing: {command}")
            result = self.bash_tool.run(command)
            
            if isinstance(result, str):
                if "error" in result.lower() or "failed" in result.lower():
                    return {"success": False, "error": result}
                else:
                    return {"success": True, "output": result}
            elif isinstance(result, dict):
                return {
                    "success": result.get("return_code", 0) == 0,
                    "output": result.get("stdout", ""),
                    "error": result.get("stderr", "") if result.get("return_code", 0) != 0 else None
                }
            else:
                return {"success": True, "output": str(result)}
                
        except Exception as e:
            logger.error(f"Command execution failed: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _start_service(self, command: str, project_path: Path, expected_ports: List[int]) -> Dict[str, Any]:
        """Start a service and monitor it."""
        try:
            logger.info(f"🌐 Starting service with command: {command}")
            
            # Start process in background
            process = subprocess.Popen(
                command,
                shell=True,
                cwd=project_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid if os.name != 'nt' else None
            )
            
            # Wait a bit for the service to start
            time.sleep(5)
            
            # Check if process is still running
            if process.poll() is not None:
                stdout, stderr = process.communicate()
                return {
                    "success": False,
                    "error": f"Service failed to start. Exit code: {process.returncode}. Error: {stderr.decode()}"
                }
            
            # Detect which ports are actually being used
            service_urls = self._detect_service_urls(expected_ports)
            
            return {
                "success": True,
                "process_id": process.pid,
                "service_urls": service_urls
            }
            
        except Exception as e:
            logger.error(f"Failed to start service: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _detect_service_urls(self, expected_ports: List[int]) -> List[str]:
        """Detect which URLs are serving content."""
        service_urls = []
        
        for port in expected_ports:
            url = f"http://localhost:{port}"
            try:
                response = requests.get(url, timeout=5)
                if response.status_code < 400:
                    service_urls.append(url)
                    logger.info(f"✅ Service responding at {url}")
            except:
                continue
        
        # If no expected ports work, scan common ports
        if not service_urls:
            common_ports = [3000, 8000, 5000, 8080, 4173, 5173]
            for port in common_ports:
                if port not in expected_ports:
                    url = f"http://localhost:{port}"
                    try:
                        response = requests.get(url, timeout=2)
                        if response.status_code < 400:
                            service_urls.append(url)
                            logger.info(f"✅ Service found at {url}")
                            break
                    except:
                        continue
        
        return service_urls
    
    def stop_deployment(self, deployment_id: str) -> Dict[str, Any]:
        """Stop a running deployment."""
        if deployment_id not in self.active_deployments:
            return {"success": False, "error": f"Deployment {deployment_id} not found"}
        
        deployment = self.active_deployments[deployment_id]
        process_id = deployment.get("process_id")
        
        if not process_id:
            return {"success": False, "error": "No process ID found for deployment"}
        
        try:
            # Try to terminate the process gracefully
            if os.name != 'nt':
                os.killpg(os.getpgid(process_id), signal.SIGTERM)
            else:
                process = psutil.Process(process_id)
                process.terminate()
            
            # Wait for termination
            time.sleep(2)
            
            # Force kill if still running
            try:
                if os.name != 'nt':
                    os.killpg(os.getpgid(process_id), signal.SIGKILL)
                else:
                    process = psutil.Process(process_id)
                    process.kill()
            except:
                pass  # Process already terminated
            
            # Remove from active deployments
            del self.active_deployments[deployment_id]
            
            logger.info(f"🛑 Stopped deployment {deployment_id}")
            return {"success": True, "message": f"Deployment {deployment_id} stopped"}
            
        except Exception as e:
            logger.error(f"Failed to stop deployment: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def list_active_deployments(self) -> List[Dict[str, Any]]:
        """List all active deployments."""
        active = []
        
        for deployment_id, deployment in self.active_deployments.items():
            # Check if process is still running
            process_id = deployment.get("process_id")
            is_running = False
            
            if process_id:
                try:
                    process = psutil.Process(process_id)
                    is_running = process.is_running()
                except:
                    is_running = False
            
            if not is_running and process_id:
                # Remove dead deployments
                del self.active_deployments[deployment_id]
                continue
                
            active.append({
                "deployment_id": deployment_id,
                "project_path": deployment["project_path"],
                "project_type": deployment["project_type"],
                "service_urls": deployment["service_urls"],
                "started_at": deployment["started_at"],
                "is_running": is_running
            })
        
        return active
    
    def stop_all_deployments(self) -> Dict[str, Any]:
        """Stop all active deployments."""
        results = []
        
        for deployment_id in list(self.active_deployments.keys()):
            result = self.stop_deployment(deployment_id)
            results.append({"deployment_id": deployment_id, "result": result})
        
        return {"success": True, "stopped_deployments": results}
    
    def get_deployment_status(self, deployment_id: str) -> Dict[str, Any]:
        """Get status of a specific deployment."""
        if deployment_id not in self.active_deployments:
            return {"success": False, "error": f"Deployment {deployment_id} not found"}
        
        deployment = self.active_deployments[deployment_id]
        process_id = deployment.get("process_id")
        
        # Check if process is running
        is_running = False
        if process_id:
            try:
                process = psutil.Process(process_id)
                is_running = process.is_running()
            except:
                is_running = False
        
        # Check if URLs are responding
        responding_urls = []
        for url in deployment.get("service_urls", []):
            try:
                response = requests.get(url, timeout=5)
                if response.status_code < 400:
                    responding_urls.append(url)
            except:
                continue
        
        return {
            "success": True,
            "deployment_id": deployment_id,
            "is_running": is_running,
            "service_urls": deployment.get("service_urls", []),
            "responding_urls": responding_urls,
            "project_type": deployment.get("project_type"),
            "started_at": deployment.get("started_at")
        }

# Convenience functions
def deploy_project_quick(project_path: str, force_type: Optional[str] = None) -> Dict[str, Any]:
    """Quick project deployment with minimal setup."""
    manager = DeploymentManager()
    return manager.deploy_project(project_path, force_type)

def stop_all_services():
    """Stop all running services."""
    manager = DeploymentManager()
    return manager.stop_all_deployments()

if __name__ == "__main__":
    # Test the deployment manager
    manager = DeploymentManager()
    
    # Example usage
    test_project = "./test_project"
    if os.path.exists(test_project):
        result = manager.deploy_project(test_project)
        print(f"Deployment result: {result}")
        
        if result["success"]:
            print(f"Service URLs: {result.get('service_urls', [])}")
            
            # Test status check
            deployment_id = result["deployment_id"]
            status = manager.get_deployment_status(deployment_id)
            print(f"Status: {status}")
    else:
        print("No test project found. Create a test project to try deployment.")
