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
                "run_command": "cd app/web && python -m http.server {port}",
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
            
            # Special handling for Python HTTP server and static file projects
            is_python_http_server = "python -m http.server" in final_command
            if is_python_http_server:
                logger.info("🔧 STATIC DEPLOYMENT: Detected Python HTTP server for static files")
                
                # Ensure we have the correct working directory for static files
                static_dir = None
                if "cd app/web" in final_command:
                    static_dir = project_path / "app" / "web"
                elif "cd web" in final_command:
                    static_dir = project_path / "web"
                else:
                    static_dir = project_path
                
                # Verify static files exist
                if static_dir and static_dir.exists():
                    html_files = list(static_dir.glob("*.html"))
                    if not html_files:
                        logger.info("🔧 STATIC DEPLOYMENT: No HTML files found, creating default index.html")
                        self._create_default_index_html(static_dir, available_port)
                    else:
                        logger.info(f"🔧 STATIC DEPLOYMENT: Found {len(html_files)} HTML files in {static_dir}")
                else:
                    logger.warning(f"⚠️ STATIC DEPLOYMENT: Static directory not found: {static_dir}")
                    # Create the directory and default file
                    if static_dir:
                        static_dir.mkdir(parents=True, exist_ok=True)
                        self._create_default_index_html(static_dir, available_port)
            
            # Set the PORT environment variable to ensure the service uses the available port
            env = os.environ.copy()
            env['PORT'] = str(available_port)
            
            # Start process in background with proper error handling
            try:
                process = subprocess.Popen(
                    final_command,
                    shell=True,
                    cwd=project_path,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    env=env,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0,
                    preexec_fn=None if os.name == 'nt' else os.setsid
                )
                
                logger.info(f"🌐 SERVICE STARTUP: Process started with PID {process.pid} on port {available_port}")
                
                # Give the process a moment to start
                time.sleep(2)
                
                # Check if process died immediately
                if process.poll() is not None:
                    stdout, stderr = process.communicate()
                    stdout_str = stdout.decode('utf-8', errors='ignore') if stdout else ""
                    stderr_str = stderr.decode('utf-8', errors='ignore') if stderr else ""
                    
                    logger.error(f"❌ SERVICE STARTUP: Process exited immediately with code {process.returncode}")
                    logger.error(f"❌ SERVICE STARTUP: STDOUT: {stdout_str}")
                    logger.error(f"❌ SERVICE STARTUP: STDERR: {stderr_str}")
                    
                    return {
                        "success": False,
                        "error": f"Service failed to start. Exit code: {process.returncode}. Error: {stderr_str or 'Unknown error'}"
                    }
                
                # Wait for service to start properly - longer wait for Python HTTP server
                initial_wait = 8 if is_python_http_server else 5
                logger.info(f"🌐 SERVICE STARTUP: Waiting {initial_wait}s for service to bind to port...")
                time.sleep(initial_wait)
                
                # Verify the process is still running after initial wait
                if process.poll() is not None:
                    stdout, stderr = process.communicate()
                    stdout_str = stdout.decode('utf-8', errors='ignore') if stdout else ""
                    stderr_str = stderr.decode('utf-8', errors='ignore') if stderr else ""
                    
                    logger.error(f"❌ SERVICE STARTUP: Process died during startup with code {process.returncode}")
                    logger.error(f"❌ SERVICE STARTUP: STDOUT: {stdout_str}")
                    logger.error(f"❌ SERVICE STARTUP: STDERR: {stderr_str}")
                    
                    return {
                        "success": False,
                        "error": f"Service process died during startup. Exit code: {process.returncode}. Error: {stderr_str or 'Process died unexpectedly'}"
                    }
                
                logger.info("✅ SERVICE STARTUP: Process is running, attempting direct port verification...")
                
                # Direct port verification before URL detection - gentler for Python HTTP server
                port_listening = False
                max_attempts = 15 if is_python_http_server else 10
                for attempt in range(max_attempts):
                    try:
                        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as test_socket:
                            test_socket.settimeout(2)
                            result = test_socket.connect_ex(('localhost', available_port))
                            if result == 0:
                                port_listening = True
                                logger.info(f"✅ SERVICE STARTUP: Port {available_port} is now accepting connections")
                                break
                    except Exception as e:
                        logger.debug(f"Port check attempt {attempt + 1}: {e}")
                    
                    time.sleep(0.5)
                
                # Try to detect service URLs with special handling for Python HTTP server
                ports_to_check = [available_port] + [p for p in expected_ports if p != available_port]
                logger.info(f"🔍 SERVICE STARTUP: URL detection for {'Python HTTP server' if is_python_http_server else 'service'}")
                
                if is_python_http_server:
                    service_urls = self._detect_python_http_server_urls(ports_to_check)
                else:
                    service_urls = self._detect_service_urls(ports_to_check)
                
                if service_urls:
                    logger.info(f"✅ SERVICE STARTUP: Successfully detected service URLs: {service_urls}")
                else:
                    logger.warning(f"⚠️ SERVICE STARTUP: No service URLs detected")
                
                # If URL detection failed but port is listening, create URL manually
                if not service_urls and port_listening:
                    service_urls = [f"http://localhost:{available_port}"]
                    logger.info(f"🔧 SERVICE STARTUP: Port is listening but URL detection failed, manually created URL: {service_urls}")
                
                if not service_urls:
                    logger.warning("⚠️ SERVICE STARTUP: No service URLs detected and port not listening")
                    logger.warning("⚠️ SERVICE STARTUP: Service may be starting very slowly or having issues")
                
                return {
                    "success": True,
                    "process_id": process.pid,
                    "service_urls": service_urls,
                    "port_listening": port_listening
                }
                
            except subprocess.SubprocessError as e:
                logger.error(f"❌ SERVICE STARTUP: Failed to start subprocess: {str(e)}")
                return {"success": False, "error": f"Failed to start subprocess: {str(e)}"}
            
        except Exception as e:
            logger.error(f"❌ SERVICE STARTUP: Failed to start service: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _detect_python_http_server_urls(self, expected_ports: List[int]) -> List[str]:
        """Special URL detection for Python HTTP server with gentler connection handling."""
        service_urls = []
        
        logger.info(f"🔍 PYTHON HTTP SERVER: Gentle URL detection for ports: {expected_ports}")
        
        # Give Python HTTP server more time to fully initialize
        logger.info(f"🔍 PYTHON HTTP SERVER: Waiting 5 seconds for full initialization...")
        time.sleep(5)
        
        for port in expected_ports:
            url = f"http://localhost:{port}"
            logger.info(f"🔍 PYTHON HTTP SERVER: Testing {url}...")
            
            # Use gentler approach with fewer attempts and longer delays
            success = False
            for attempt in range(3):  # Only 3 attempts to avoid overwhelming the server
                try:
                    # First check if port is listening
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as test_socket:
                        test_socket.settimeout(5)  # Longer timeout
                        result = test_socket.connect_ex(('localhost', port))
                        if result != 0:
                            logger.info(f"🔍 PYTHON HTTP SERVER: Port {port} not listening (attempt {attempt + 1})")
                            time.sleep(3)  # Longer wait between attempts
                            continue
                    
                    # Port is listening, try the most basic HTTP request first
                    try:
                        import urllib.request
                        import urllib.error
                        
                        logger.info(f"🔍 PYTHON HTTP SERVER: Trying basic urllib request for {url}")
                        
                        # Use urllib with very simple request
                        req = urllib.request.Request(
                            url, 
                            headers={
                                'User-Agent': 'Python-urllib/3.0',
                                'Accept': 'text/html,*/*',
                                'Connection': 'close'
                            }
                        )
                        
                        with urllib.request.urlopen(req, timeout=8) as response:
                            status_code = response.getcode()
                            logger.info(f"🔍 PYTHON HTTP SERVER: {url} responded with status {status_code}")
                            
                            if status_code < 400:
                                service_urls.append(url)
                                logger.info(f"✅ PYTHON HTTP SERVER: Service responding at {url}")
                                success = True
                                break
                            else:
                                logger.warning(f"⚠️ PYTHON HTTP SERVER: {url} returned status {status_code}")
                                
                    except urllib.error.URLError as e:
                        error_msg = str(e).lower()
                        if "connection refused" in error_msg:
                            logger.info(f"🔧 PYTHON HTTP SERVER: {url} - Connection refused, server may not be ready")
                        else:
                            logger.info(f"🔧 PYTHON HTTP SERVER: {url} - URL error: {str(e)}")
                    except Exception as e:
                        logger.info(f"🔧 PYTHON HTTP SERVER: {url} - Request error: {str(e)}")
                        
                        # Fallback: if port is listening, assume it's working
                        try:
                            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as fallback_socket:
                                fallback_socket.settimeout(2)
                                if fallback_socket.connect_ex(('localhost', port)) == 0:
                                    logger.info(f"🔧 PYTHON HTTP SERVER: Port {port} is listening, assuming service is working")
                                    service_urls.append(url)
                                    success = True
                                    break
                        except Exception:
                            pass
                        
                except Exception as socket_error:
                    logger.info(f"❌ PYTHON HTTP SERVER: Socket error for port {port} (attempt {attempt + 1}): {str(socket_error)}")
                
                if attempt < 2:  # Don't wait after the last attempt
                    wait_time = 4 + attempt * 2  # 4, 6 seconds
                    logger.info(f"🔍 PYTHON HTTP SERVER: Waiting {wait_time}s before next attempt...")
                    time.sleep(wait_time)
            
            if not success:
                logger.warning(f"⚠️ PYTHON HTTP SERVER: {url} failed all gentle connection attempts")
                
                # Final check - if port is listening at all, add the URL
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as final_check:
                        final_check.settimeout(1)
                        if final_check.connect_ex(('localhost', port)) == 0:
                            logger.info(f"🔧 PYTHON HTTP SERVER: Port {port} is listening, adding URL as working")
                            service_urls.append(url)
                except Exception:
                    logger.warning(f"⚠️ PYTHON HTTP SERVER: Port {port} appears to be completely unresponsive")
        
        logger.info(f"🔍 PYTHON HTTP SERVER: Final detection result: {service_urls}")
        return service_urls

    def _detect_service_urls(self, expected_ports: List[int]) -> List[str]:
        """Detect service URLs by testing HTTP connections."""
        service_urls = []
        
        logger.info(f"🔍 URL DETECTION: Testing ports: {expected_ports}")
        
        for port in expected_ports:
            url = f"http://localhost:{port}"
            logger.info(f"🔍 URL DETECTION: Testing {url}...")
            
            success = False
            for attempt in range(5):
                try:
                    # First check if port is listening
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as test_socket:
                        test_socket.settimeout(3)
                        result = test_socket.connect_ex(('localhost', port))
                        if result != 0:
                            logger.info(f"🔍 URL DETECTION: Port {port} not listening (attempt {attempt + 1})")
                            time.sleep(2)
                            continue
                    
                    # Port is listening, try HTTP request
                    try:
                        response = requests.get(url, timeout=5, headers={'User-Agent': 'DeploymentManager/1.0'})
                        status_code = response.status_code
                        logger.info(f"🔍 URL DETECTION: {url} responded with status {status_code}")
                        
                        if status_code < 400:
                            service_urls.append(url)
                            logger.info(f"✅ URL DETECTION: Service responding at {url}")
                            success = True
                            break
                        else:
                            logger.warning(f"⚠️ URL DETECTION: {url} returned status {status_code}")
                            
                    except requests.exceptions.RequestException as e:
                        error_msg = str(e).lower()
                        if "connection refused" in error_msg:
                            logger.info(f"🔧 URL DETECTION: {url} - Connection refused, server may not be ready")
                        else:
                            logger.info(f"🔧 URL DETECTION: {url} - Request error: {str(e)}")
                        
                        # Fallback: if port is listening, assume it's working
                        try:
                            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as fallback_socket:
                                fallback_socket.settimeout(2)
                                if fallback_socket.connect_ex(('localhost', port)) == 0:
                                    logger.info(f"🔧 URL DETECTION: Port {port} is listening, assuming service is working")
                                    service_urls.append(url)
                                    success = True
                                    break
                        except Exception:
                            pass
                        
                except Exception as socket_error:
                    logger.info(f"❌ URL DETECTION: Socket error for port {port} (attempt {attempt + 1}): {str(socket_error)}")
                
                if attempt < 4:  # Don't wait after the last attempt
                    wait_time = 2 + attempt  # 2, 3, 4, 5 seconds
                    logger.info(f"🔍 URL DETECTION: Waiting {wait_time}s before next attempt...")
                    time.sleep(wait_time)
            
            if not success:
                logger.warning(f"⚠️ URL DETECTION: {url} failed all connection attempts")
        
        logger.info(f"🔍 URL DETECTION: Final result: {service_urls}")
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
    
    def _create_default_index_html(self, project_path: Path, port: int) -> bool:
        """Create a default index.html if no web content exists."""
        try:
            # Create a simple but functional index.html without Unicode characters
            default_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Generated Project</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 40px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }}
        .container {{
            max-width: 800px;
            margin: 0 auto;
            background: white;
            padding: 40px;
            border-radius: 12px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            text-align: center;
            margin-bottom: 30px;
            font-size: 2.5em;
        }}
        .status {{
            background: #d4edda;
            color: #155724;
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid #28a745;
            margin: 20px 0;
            font-weight: bold;
        }}
        .info-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }}
        .info-card {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            border: 1px solid #e9ecef;
        }}
        .info-card h3 {{
            color: #495057;
            margin: 0 0 10px 0;
            font-size: 1.1em;
        }}
        .file-list {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
        }}
        .file-list ul {{
            margin: 10px 0;
            padding-left: 20px;
        }}
        .file-list li {{
            margin: 5px 0;
            color: #6c757d;
        }}
        .footer {{
            text-align: center;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #e9ecef;
            color: #6c757d;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Project Generated Successfully</h1>
        
        <div class="status">
            Server is running successfully on port {port}
        </div>
        
        <div class="info-grid">
            <div class="info-card">
                <h3>Server Status</h3>
                <p>Active and responding</p>
            </div>
            <div class="info-card">
                <h3>Port</h3>
                <p>{port}</p>
            </div>
            <div class="info-card">
                <h3>Protocol</h3>
                <p>HTTP</p>
            </div>
            <div class="info-card">
                <h3>Access URL</h3>
                <p>http://localhost:{port}</p>
            </div>
        </div>
        
        <div class="file-list">
            <h3>Project Structure</h3>
            <p>This project was generated by the AI automation system and includes:</p>
            <ul>
                <li>Frontend components and styles</li>
                <li>Backend API endpoints</li>
                <li>Configuration files</li>
                <li>Documentation</li>
            </ul>
        </div>
        
        <div class="footer">
            <p>Generated by AI Automation Workflow System</p>
            <p>Visit <strong>http://localhost:{port}</strong> to access this project</p>
        </div>
    </div>
    
    <script>
        console.log('Project page loaded successfully');
        console.log('Server running on port {port}');
        
        // Add some interactivity
        document.addEventListener('DOMContentLoaded', function() {{
            console.log('DOM content loaded - page ready for browser testing');
            
            // Add a simple animation
            const container = document.querySelector('.container');
            container.style.opacity = '0';
            container.style.transform = 'translateY(20px)';
            
            setTimeout(() => {{
                container.style.transition = 'all 0.6s ease';
                container.style.opacity = '1';
                container.style.transform = 'translateY(0)';
            }}, 100);
        }});
    </script>
</body>
</html>"""

            # Write the HTML file with proper encoding
            index_path = project_path / "index.html"
            with open(index_path, 'w', encoding='utf-8') as f:
                f.write(default_html)
            
            print(f"✅ Created default index.html at: {index_path}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to create default index.html: {e}")
            return False

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
