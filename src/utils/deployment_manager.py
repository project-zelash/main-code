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
import socket
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import logging
import psutil
import requests
from urllib.parse import urlparse

from src.repository.tools.bash_tool import BashTool

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
        """Detect project type based on files in the directory, prioritizing native runtime over deployment tech."""
        files = [f.name for f in project_path.iterdir() if f.is_file()]
        
        # Also check subdirectories for HTML files (common in generated projects)
        all_files = []
        subdirs = []
        for root, dirs, files_in_dir in os.walk(project_path):
            for file in files_in_dir:
                all_files.append(file)
            for dir_name in dirs:
                subdirs.append(dir_name)
        
        logger.info(f"🔍 PROJECT TYPE DETECTION: Found files: {files}")
        logger.info(f"🔍 PROJECT TYPE DETECTION: Found all files (including subdirs): {all_files}")
        logger.info(f"🔍 PROJECT TYPE DETECTION: Found subdirectories: {subdirs}")
        
        # PRIORITY 1: Check for complex multi-service projects (app/, src/, api/, web/ structure)
        if any(subdir in subdirs for subdir in ['app', 'src']):
            app_dir = project_path / "app"
            if app_dir.exists():
                app_subdirs = [d.name for d in app_dir.iterdir() if d.is_dir()]
                app_files = []
                for root, dirs, files_in_dir in os.walk(app_dir):
                    app_files.extend(files_in_dir)
                
                logger.info(f"🔍 PROJECT TYPE DETECTION: App directory structure - subdirs: {app_subdirs}, files: {app_files}")
                
                # Check for React/Node.js in app/web/ directory FIRST (prioritize frontend)
                web_dir = app_dir / "web"
                if web_dir.exists():
                    web_files = [f.name for f in web_dir.iterdir() if f.is_file()]
                    logger.info(f"🔍 PROJECT TYPE DETECTION: Web directory files: {web_files}")
                    
                    if "package.json" in web_files:
                        logger.info("🔍 PROJECT TYPE DETECTION: Detected as fullstack-app (React frontend + backend)")
                        return "fullstack-app"
                    elif any(f.endswith(".html") for f in web_files):
                        logger.info("🔍 PROJECT TYPE DETECTION: Detected as static (HTML files in app/web)")
                        return "static"
                
                # Check for Flask/FastAPI in app/api/ directory
                api_dir = app_dir / "api"
                if api_dir.exists():
                    api_files = [f.name for f in api_dir.iterdir() if f.is_file()]
                    logger.info(f"🔍 PROJECT TYPE DETECTION: API directory files: {api_files}")
                    
                    # Check for Python API
                    python_dir = api_dir / "python"
                    if python_dir.exists():
                        python_files = [f.name for f in python_dir.iterdir() if f.is_file()]
                        if "app.py" in python_files or "main.py" in python_files:
                            logger.info("🔍 PROJECT TYPE DETECTION: Detected as flask-api (app/api/python structure)")
                            return "flask-api"
                    
                    # Check for Node.js API
                    nodejs_dir = api_dir / "nodejs"
                    if nodejs_dir.exists():
                        nodejs_files = [f.name for f in nodejs_dir.iterdir() if f.is_file()]
                        if "index.js" in nodejs_files or "app.js" in nodejs_files:
                            logger.info("🔍 PROJECT TYPE DETECTION: Detected as express (app/api/nodejs structure)")
                            return "express"
        
        # PRIORITY 2: Node.js projects (check package.json)
        if "package.json" in files:
            try:
                with open(project_path / "package.json", 'r') as f:
                    package_json = json.load(f)
                    dependencies = package_json.get("dependencies", {})
                    dev_dependencies = package_json.get("devDependencies", {})
                    
                if "next" in dependencies:
                    logger.info("🔍 PROJECT TYPE DETECTION: Detected as nextjs")
                    return "nextjs"
                elif "react" in dependencies and "vite" in dev_dependencies:
                    logger.info("🔍 PROJECT TYPE DETECTION: Detected as vite-react")
                    return "vite-react"
                elif "vue" in dependencies and "vite" in dev_dependencies:
                    logger.info("🔍 PROJECT TYPE DETECTION: Detected as vite-vue")
                    return "vite-vue"
                elif "react" in dependencies:
                    logger.info("🔍 PROJECT TYPE DETECTION: Detected as react")
                    return "react"
                elif "vue" in dependencies:
                    logger.info("🔍 PROJECT TYPE DETECTION: Detected as vue")
                    return "vue"
                elif "express" in dependencies:
                    logger.info("🔍 PROJECT TYPE DETECTION: Detected as express")
                    return "express"
                else:
                    logger.info("🔍 PROJECT TYPE DETECTION: Detected as nodejs")
                    return "nodejs"
            except:
                logger.info("🔍 PROJECT TYPE DETECTION: Failed to parse package.json, defaulting to nodejs")
                return "nodejs"
        
        # PRIORITY 3: Python projects
        elif "requirements.txt" in files or "pyproject.toml" in files:
            if "manage.py" in files:
                logger.info("🔍 PROJECT TYPE DETECTION: Detected as django")
                return "django"
            elif "app.py" in files or any(f.startswith("main") and f.endswith(".py") for f in files):
                logger.info("🔍 PROJECT TYPE DETECTION: Detected as flask")
                return "flask"
            else:
                logger.info("🔍 PROJECT TYPE DETECTION: Detected as python")
                return "python"
        
        # PRIORITY 4: Other native runtimes
        elif "go.mod" in files:
            logger.info("🔍 PROJECT TYPE DETECTION: Detected as go")
            return "go"
        elif "pom.xml" in files:
            logger.info("🔍 PROJECT TYPE DETECTION: Detected as maven")
            return "maven"
        elif "build.gradle" in files:
            logger.info("🔍 PROJECT TYPE DETECTION: Detected as gradle")
            return "gradle"
        elif "Cargo.toml" in files:
            logger.info("🔍 PROJECT TYPE DETECTION: Detected as rust")
            return "rust"
        elif any(f.endswith(".csproj") or f.endswith(".sln") for f in files):
            logger.info("🔍 PROJECT TYPE DETECTION: Detected as dotnet")
            return "dotnet"
        
        # PRIORITY 5: Static websites - check both root files and all files
        elif any(f.endswith(".html") for f in files) or any(f.endswith(".html") for f in all_files):
            logger.info("🔍 PROJECT TYPE DETECTION: Detected as static (HTML files found)")
            return "static"
        
        # LAST RESORT: Docker (only if no native runtime detected)
        elif "Dockerfile" in files:
            logger.warning("🔍 PROJECT TYPE DETECTION: Only Dockerfile found, no native runtime detected")
            logger.warning("🔍 PROJECT TYPE DETECTION: Docker deployment should come AFTER localhost testing")
            logger.warning("🔍 PROJECT TYPE DETECTION: Treating as unknown project type")
            return "unknown"
        
        else:
            logger.warning(f"🔍 PROJECT TYPE DETECTION: Could not determine project type. Files found: {files}")
            logger.warning(f"🔍 PROJECT TYPE DETECTION: All files found: {all_files}")
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
            "static": {
                "run_command": "python -m http.server {port}",
                "expected_ports": [3000, 8080, 9000, 3001, 8081, 4000, 5001, 7000],
                "health_check_paths": ["/", "/index.html"]
            },
            "flask-api": {
                "install_command": "pip install -r requirements.txt",
                "run_command": "cd app/api/python && python app.py",
                "expected_ports": [5000, 8000],
                "health_check_paths": ["/", "/api", "/health"]
            },
            "fullstack-app": {
                "install_command": "pip install -r requirements.txt",
                "run_command": "cd app/api/python && python app.py",
                "expected_ports": [5000, 8000, 3000],
                "health_check_paths": ["/", "/api", "/health"]
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
    
    def _find_available_port(self, start_port: int = 3000) -> int:
        """Find an available port starting from the given port, with Windows-friendly alternatives."""
        # Windows-friendly port ranges that typically don't require admin privileges
        windows_safe_ports = [3000, 8080, 9000, 3001, 8081, 4000, 5001, 7000, 9001, 3002, 8082, 4001]
        
        # First try the requested port
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', start_port))
                logger.info(f"🔍 PORT ALLOCATION: Found available port {start_port}")
                return start_port
        except OSError as e:
            logger.warning(f"⚠️ PORT ALLOCATION: Port {start_port} unavailable: {e}")
        
        # Try Windows-safe ports first
        for port in windows_safe_ports:
            if port != start_port:  # Skip if we already tried it
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                        s.bind(('localhost', port))
                        logger.info(f"🔍 PORT ALLOCATION: Found available Windows-safe port {port}")
                        return port
                except OSError:
                    continue
        
        # Fallback to scanning a range
        port = max(start_port, 3000)  # Start from at least 3000
        while port < 65535:
            # Skip common restricted ports on Windows
            if port in [8000, 80, 443, 135, 445, 1433, 3389]:
                port += 1
                continue
                
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('localhost', port))
                    logger.info(f"🔍 PORT ALLOCATION: Found available port {port}")
                    return port
            except OSError:
                port += 1
        
        logger.warning(f"⚠️ PORT ALLOCATION: Could not find any available port, returning {start_port}")
        return start_port  # Return original port as fallback
    
    def _start_service(self, command: str, project_path: Path, expected_ports: List[int]) -> Dict[str, Any]:
        """Start a service and monitor it."""
        try:
            logger.info(f"🌐 Starting service with command template: {command}")
            
            # Check if any expected ports are in use and find alternatives
            available_port = None
            for port in expected_ports:
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                        s.bind(('localhost', port))
                        available_port = port
                        logger.info(f"🔍 PORT CHECK: Port {port} is available")
                        break
                except OSError:
                    logger.warning(f"⚠️ PORT CHECK: Port {port} is already in use")
                    continue
            
            # If no expected ports are available, find an alternative
            if available_port is None:
                available_port = self._find_available_port(expected_ports[0] if expected_ports else 3000)
                logger.info(f"🔍 PORT ALLOCATION: Using alternative port {available_port}")
            
            # Substitute the port placeholder in the command
            final_command = command.replace("{port}", str(available_port))
            logger.info(f"🌐 Final command with port substitution: {final_command}")
            
            # Set the PORT environment variable to ensure the service uses the available port
            env = os.environ.copy()
            env['PORT'] = str(available_port)
            
            # Start process in background with the PORT environment variable
            process = subprocess.Popen(
                final_command,  # Use the command with port substituted
                shell=True,
                cwd=project_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                preexec_fn=os.setsid if os.name != 'nt' else None
            )
            
            logger.info(f"🌐 SERVICE STARTUP: Process started with PID {process.pid} on port {available_port}")
            
            # Wait longer for service to start (React apps can be slow)
            initial_wait = 10
            logger.info(f"🌐 SERVICE STARTUP: Waiting {initial_wait}s for initial startup...")
            time.sleep(initial_wait)
            
            # Check if process is still running
            if process.poll() is not None:
                stdout, stderr = process.communicate()
                logger.error(f"❌ SERVICE STARTUP: Process exited early with code {process.returncode}")
                logger.error(f"❌ SERVICE STARTUP: STDOUT: {stdout.decode()}")
                logger.error(f"❌ SERVICE STARTUP: STDERR: {stderr.decode()}")
                return {
                    "success": False,
                    "error": f"Service failed to start. Exit code: {process.returncode}. Error: {stderr.decode()}"
                }
            
            logger.info("✅ SERVICE STARTUP: Process is still running, attempting to detect service URLs...")
            
            # Try to detect service URLs with retries, including the allocated port
            service_urls = []
            max_retries = 6  # Total wait time: 10s initial + (5s * 6) = 40s
            ports_to_check = [available_port] + [p for p in expected_ports if p != available_port]
            
            for attempt in range(max_retries):
                logger.info(f"🔍 SERVICE STARTUP: Detection attempt {attempt + 1}/{max_retries}")
                service_urls = self._detect_service_urls(ports_to_check)
                
                if service_urls:
                    logger.info(f"✅ SERVICE STARTUP: Successfully detected service URLs: {service_urls}")
                    break
                
                if attempt < max_retries - 1:  # Don't wait after the last attempt
                    logger.info(f"⏳ SERVICE STARTUP: No URLs detected yet, waiting 5s before retry...")
                    time.sleep(5)
                    
                    # Check if process is still running
                    if process.poll() is not None:
                        stdout, stderr = process.communicate()
                        logger.error(f"❌ SERVICE STARTUP: Process died during startup")
                        return {
                            "success": False,
                            "error": f"Service process died during startup. Exit code: {process.returncode}"
                        }
            
            if not service_urls:
                logger.warning("⚠️ SERVICE STARTUP: No service URLs detected after all attempts, but process is running")
                logger.warning("⚠️ SERVICE STARTUP: This may indicate the service is starting on an unexpected port or isn't ready yet")
            
            return {
                "success": True,
                "process_id": process.pid,
                "service_urls": service_urls
            }
            
        except Exception as e:
            logger.error(f"❌ SERVICE STARTUP: Failed to start service: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _detect_service_urls(self, expected_ports: List[int]) -> List[str]:
        """Detect which URLs are serving content."""
        service_urls = []
        
        logger.info(f"🔍 SERVICE URL DETECTION: Checking expected ports: {expected_ports}")
        
        # First try expected ports
        for port in expected_ports:
            url = f"http://localhost:{port}"
            logger.info(f"🔍 SERVICE URL DETECTION: Testing {url}...")
            try:
                response = requests.get(url, timeout=5)
                logger.info(f"🔍 SERVICE URL DETECTION: {url} responded with status {response.status_code}")
                if response.status_code < 400:
                    service_urls.append(url)
                    logger.info(f"✅ SERVICE URL DETECTION: Service responding at {url}")
                else:
                    logger.warning(f"⚠️ SERVICE URL DETECTION: {url} responded but with error status {response.status_code}")
            except requests.exceptions.ConnectionError:
                logger.debug(f"❌ SERVICE URL DETECTION: Connection refused at {url}")
            except requests.exceptions.Timeout:
                logger.debug(f"❌ SERVICE URL DETECTION: Timeout at {url}")
            except Exception as e:
                logger.debug(f"❌ SERVICE URL DETECTION: Error testing {url}: {str(e)}")
        
        logger.info(f"🔍 SERVICE URL DETECTION: Found {len(service_urls)} responding services on expected ports")
        
        # If no service URLs found, try common ports
        if not service_urls:
            logger.info("🔍 SERVICE URL DETECTION: No services found on expected ports, scanning common ports...")
            common_ports = [3000, 8000, 5000, 8080, 4173, 5173, 9000, 4000]
            
            for port in common_ports:
                if port not in expected_ports:
                    url = f"http://localhost:{port}"
                    logger.debug(f"🔍 SERVICE URL DETECTION: Testing common port {url}...")
                    try:
                        response = requests.get(url, timeout=3)
                        if response.status_code < 400:
                            service_urls.append(url)
                            logger.info(f"✅ SERVICE URL DETECTION: Service found at {url}")
                            break  # Found one, that's enough for now
                    except:
                        continue
            
            if service_urls:
                logger.info(f"✅ SERVICE URL DETECTION: Found service on common port: {service_urls}")
            else:
                logger.warning("⚠️ SERVICE URL DETECTION: No responding services found on any common ports")
        
        logger.info(f"🔍 SERVICE URL DETECTION: Final result: {service_urls}")
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
