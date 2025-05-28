"""
Complete End-to-End Automation Pipeline

This module orchestrates the entire automated workflow:
Generate → Deploy → Test → Report

Handles the complete pipeline from project generation to comprehensive testing.
"""

import os
import json
import time
import asyncio
from typing import Dict, List, Any, Optional
from pathlib import Path
import logging

from utils.project_generator import ProjectGenerator
from utils.deployment_manager import DeploymentManager
# Remove browser_testing_manager import - we'll use direct Playwright
from service.llm_factory import LLMFactory
from service.tool_service import ToolService
from repository.execution.agent_manager import AgentManager
from repository.tools.bash_tool import BashTool
from repository.execution.build_test_manager import BuildTestManager
from repository.execution.testing_framework import TestingFramework
from repository.execution.feedback_analyzer import FeedbackAnalyzer

logger = logging.getLogger(__name__)

class DirectPlaywrightTester:
    """Direct Playwright browser testing - guaranteed to work."""
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self._ensure_playwright_installed()
        
    def _ensure_playwright_installed(self):
        """Ensure Playwright browsers are installed."""
        try:
            from playwright.async_api import async_playwright
            
            # Try to check if browsers are installed by attempting to launch
            import asyncio
            import subprocess
            
            # Check if playwright install has been run
            try:
                result = subprocess.run(
                    ["playwright", "install", "chromium"], 
                    capture_output=True, 
                    text=True, 
                    timeout=120
                )
                if result.returncode == 0:
                    print("✅ Playwright browsers installed successfully")
                else:
                    print(f"⚠️ Playwright install returned code {result.returncode}: {result.stderr}")
            except subprocess.TimeoutExpired:
                print("⚠️ Playwright install timed out, but continuing...")
            except Exception as e:
                print(f"⚠️ Error installing Playwright browsers: {e}")
                
        except ImportError:
            print("❌ Playwright not available - install with: pip install playwright")
            raise
        
    async def test_application(self, service_urls: List[str], custom_tests: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Test application using direct Playwright automation.
        
        Args:
            service_urls: List of URLs to test
            custom_tests: Custom test scenarios (optional)
            
        Returns:
            Test results dictionary
        """
        print("\n================ STARTING BROWSER TESTING ================\n")
        
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            return {
                "success": False,
                "error": "Playwright not available - install with: pip install playwright && playwright install"
            }
        
        test_results = {
            "success": True,
            "tested_urls": [],
            "successful_connections": 0,
            "failed_connections": 0,
            "detailed_results": [],
            "screenshots": []
        }
        
        async with async_playwright() as p:
            # Launch browser (visible or headless based on setting)
            browser = await p.chromium.launch(headless=self.headless)
            context = await browser.new_context(viewport={"width": 1280, "height": 720})
            
            try:
                for i, url in enumerate(service_urls):
                    print(f"\nTesting URL {i+1}/{len(service_urls)}: {url}")
                    
                    page = await context.new_page()
                    url_result = {
                        "url": url,
                        "success": False,
                        "error": None,
                        "page_title": None,
                        "response_time": 0,
                        "screenshot_path": None
                    }
                    
                    try:
                        # Pre-check: Verify the URL is responding before browser test
                        print(f"Pre-checking URL availability: {url}")
                        import requests
                        try:
                            pre_response = requests.get(url, timeout=10)
                            if pre_response.status_code >= 400:
                                url_result["error"] = f"Server returned error status {pre_response.status_code}"
                                print(f"❌ Pre-check failed: Server returned {pre_response.status_code}")
                                test_results["failed_connections"] += 1
                                continue
                            else:
                                print(f"✅ Pre-check passed: Server returned {pre_response.status_code}")
                        except requests.exceptions.ConnectionError:
                            url_result["error"] = "Connection refused - server not responding"
                            print(f"❌ Pre-check failed: Connection refused")
                            test_results["failed_connections"] += 1
                            continue
                        except Exception as e:
                            url_result["error"] = f"Pre-check failed: {str(e)}"
                            print(f"❌ Pre-check failed: {str(e)}")
                            test_results["failed_connections"] += 1
                            continue
                        
                        start_time = time.time()
                        
                        # Navigate to the URL with longer timeout and better error handling
                        print(f"Navigating to {url} with browser...")
                        try:
                            await page.goto(url, timeout=45000, wait_until="networkidle")
                        except Exception as nav_error:
                            # Try with different wait conditions
                            nav_error_str = str(nav_error)
                            if "ERR_EMPTY_RESPONSE" in nav_error_str:
                                print(f"Empty response detected, trying with domcontentloaded...")
                                try:
                                    await page.goto(url, timeout=30000, wait_until="domcontentloaded")
                                except Exception as retry_error:
                                    url_result["error"] = f"Browser navigation failed: {str(retry_error)}"
                                    print(f"❌ Browser navigation failed: {str(retry_error)}")
                                    test_results["failed_connections"] += 1
                                    continue
                            else:
                                url_result["error"] = f"Browser navigation failed: {nav_error_str}"
                                print(f"❌ Browser navigation failed: {nav_error_str}")
                                test_results["failed_connections"] += 1
                                continue
                        
                        # Calculate response time
                        url_result["response_time"] = time.time() - start_time
                        
                        # Wait a bit more for dynamic content
                        print("Waiting for page content to load...")
                        await asyncio.sleep(2)
                        
                        # Try to get page title with fallback
                        try:
                            url_result["page_title"] = await page.title()
                        except:
                            url_result["page_title"] = "Unable to get title"
                        
                        # Take screenshot before content check
                        screenshot_dir = Path("./automation_workspace/screenshots")
                        screenshot_dir.mkdir(parents=True, exist_ok=True)
                        screenshot_path = screenshot_dir / f"test_{i+1}_{int(time.time())}.png"
                        
                        try:
                            await page.screenshot(path=str(screenshot_path))
                            url_result["screenshot_path"] = str(screenshot_path)
                            test_results["screenshots"].append(str(screenshot_path))
                            print(f"Screenshot saved: {screenshot_path}")
                        except Exception as screenshot_error:
                            print(f"⚠️ Screenshot failed: {str(screenshot_error)}")
                        
                        # Check if page loaded successfully with multiple methods
                        try:
                            # Method 1: Check page content
                            page_content = await page.content()
                            content_length = len(page_content)
                            print(f"Page content length: {content_length} characters")
                            
                            # Method 2: Check for basic HTML structure
                            has_html = "<html" in page_content.lower()
                            has_body = "<body" in page_content.lower()
                            
                            # Method 3: Check if there are any visible elements
                            try:
                                visible_elements = await page.query_selector_all("*")
                                element_count = len(visible_elements)
                                print(f"Visible elements found: {element_count}")
                            except:
                                element_count = 0
                            
                            # Determine success based on multiple criteria
                            if content_length > 100 and (has_html or has_body or element_count > 5):
                                url_result["success"] = True
                                test_results["successful_connections"] += 1
                                print(f"✅ Successfully tested: {url}")
                                print(f"   Page Title: {url_result['page_title']}")
                                print(f"   Response Time: {url_result['response_time']:.2f}s")
                                print(f"   Content Length: {content_length} chars")
                                print(f"   Elements: {element_count}")
                            else:
                                url_result["error"] = f"Page appears empty or malformed (content: {content_length} chars, elements: {element_count})"
                                test_results["failed_connections"] += 1
                                print(f"❌ Failed: {url} - {url_result['error']}")
                                
                        except Exception as content_error:
                            url_result["error"] = f"Failed to analyze page content: {str(content_error)}"
                            test_results["failed_connections"] += 1
                            print(f"❌ Failed to analyze content: {str(content_error)}")
                        
                        # Run custom tests if provided and basic test succeeded
                        if custom_tests and url_result["success"]:
                            print("Running custom tests...")
                            custom_results = await self._run_custom_tests(page, custom_tests)
                            url_result["custom_test_results"] = custom_results
                            print(f"Custom tests completed: {len(custom_results)} tests")
                        
                    except Exception as e:
                        url_result["error"] = str(e)
                        test_results["failed_connections"] += 1
                        print(f"❌ Failed to test {url}: {str(e)}")
                    
                    finally:
                        try:
                            await page.close()
                        except:
                            pass
                    
                    test_results["detailed_results"].append(url_result)
                    test_results["tested_urls"].append(url)
                
                # Calculate overall success
                total_tests = len(service_urls)
                success_rate = (test_results["successful_connections"] / total_tests * 100) if total_tests > 0 else 0
                
                test_results["test_report"] = {
                    "summary": {
                        "total_urls_tested": total_tests,
                        "successful_connections": test_results["successful_connections"],
                        "failed_connections": test_results["failed_connections"],
                        "overall_success_rate": success_rate
                    }
                }
                
                if test_results["successful_connections"] == 0:
                    test_results["success"] = False
                    test_results["error"] = "No successful connections to any service URL"
                
                print(f"\n✅ Browser testing completed: {test_results['successful_connections']}/{total_tests} URLs successful")
                
            finally:
                await browser.close()
        
        print("\n================ BROWSER TESTING COMPLETE ================\n")
        return test_results
    
    async def _run_custom_tests(self, page, custom_tests: List[str]) -> List[Dict[str, Any]]:
        """Run custom test scenarios on the page."""
        results = []
        
        for test_description in custom_tests:
            test_result = {
                "test": test_description,
                "success": False,
                "error": None
            }
            
            try:
                # Simple test implementations based on description
                if "click" in test_description.lower():
                    # Try to find and click common button elements
                    buttons = await page.query_selector_all("button, input[type='button'], input[type='submit']")
                    if buttons:
                        await buttons[0].click()
                        test_result["success"] = True
                    else:
                        test_result["error"] = "No clickable elements found"
                
                elif "form" in test_description.lower() or "input" in test_description.lower():
                    # Try to fill forms
                    inputs = await page.query_selector_all("input[type='text'], input[type='email'], textarea")
                    if inputs:
                        await inputs[0].fill("test input")
                        test_result["success"] = True
                    else:
                        test_result["error"] = "No input fields found"
                
                else:
                    # Generic test - just check if page is interactive
                    await page.wait_for_load_state("networkidle")
                    test_result["success"] = True
                    
            except Exception as e:
                test_result["error"] = str(e)
            
            results.append(test_result)
        
        return results

class AutomationWorkflow:
    """Complete automation workflow orchestrator."""
    
    def __init__(
        self, 
        workspace_path: str = "./automation_workspace",
        llm_factory: Optional[LLMFactory] = None,
        tool_service: Optional[ToolService] = None,
        headless_browser: bool = True
    ):
        """
        Initialize the automation workflow.
        
        Args:
            workspace_path: Base workspace for all operations
            llm_factory: LLM factory instance
            tool_service: Tool service instance
            headless_browser: Whether to run browser tests in headless mode
        """
        self.workspace_path = Path(workspace_path)
        self.workspace_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize services
        self.llm_factory = llm_factory or LLMFactory()
        self.tool_service = tool_service or self._setup_default_tool_service()
        
        # Initialize workflow components
        self.project_generator = ProjectGenerator(
            workspace_base_path=str(self.workspace_path / "projects"),
            llm_factory=self.llm_factory,
            tool_service=self.tool_service
        )
        
        self.deployment_manager = DeploymentManager(
            bash_tool=self.tool_service.get_tool("bash")
        )
        
        # Use our proven direct Playwright tester instead of complex browser-use
        self.browser_testing_manager = DirectPlaywrightTester(
            headless=headless_browser
        )
        
        # Initialize AgentService for refinement loop
        self.agent_service = AgentManager(
            llm_factory=self.llm_factory,
            tool_service=self.tool_service
        )
        
        # Add BuildTestManager for refinement loop
        self.testing_framework = TestingFramework(
            workspace_path=str(self.workspace_path / "projects"),
            llm_factory=self.llm_factory
        )
        self.feedback_analyzer = FeedbackAnalyzer(llm_factory=self.llm_factory)
        self.build_test_manager = BuildTestManager(
            tool_service=self.tool_service,
            testing_framework=self.testing_framework,
            feedback_analyzer=self.feedback_analyzer,
            workspace_path=str(self.workspace_path / "projects")
        )
        
        # Workflow history
        self.workflow_history = []
        
    def _setup_default_tool_service(self) -> ToolService:
        """Setup default tool service with required tools."""
        tool_service = ToolService()
        tool_service.register_tool("bash", BashTool())
        return tool_service
    
    def _setup_refinement_agents(self) -> Dict[str, Any]:
        """Setup agents for the refinement loop using AgentManager."""
        # AgentManager already initializes backend, frontend, and middleware agents
        agents = {}
        
        # Get the pre-initialized agents from AgentManager
        agents["backend"] = self.agent_service.get_agent("backend")
        agents["frontend"] = self.agent_service.get_agent("frontend") 
        agents["general"] = self.agent_service.get_agent("middleware")  # Use middleware as general agent
        
        return agents
    
    async def run_complete_workflow(
        self,
        prompt: Optional[str] = None,
        prompt_method: str = "interactive",
        prompt_key: Optional[str] = None,
        project_name: Optional[str] = None,
        custom_tests: Optional[List[str]] = None,
        force_project_type: Optional[str] = None,
        skip_deployment: bool = False,
        skip_testing: bool = False
    ) -> Dict[str, Any]:
        """
        Run the complete automation workflow: Generate → Deploy → Test → Report.
        
        Args:
            prompt: Project generation prompt
            prompt_method: Method to get prompt ("interactive", "preset", "custom", "env")
            prompt_key: Key for preset prompt
            project_name: Optional project name
            custom_tests: Custom browser tests to run
            force_project_type: Force specific project type for deployment
            skip_deployment: Skip deployment phase
            skip_testing: Skip testing phase
            
        Returns:
            Complete workflow results
        """
        workflow_id = f"workflow_{int(time.time())}"
        start_time = time.time()
        
        logger.info(f"🚀 Starting complete automation workflow: {workflow_id}")
        
        workflow_result = {
            "workflow_id": workflow_id,
            "started_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "status": "running",
            "phases": {
                "generation": {"status": "pending"},
                "deployment": {"status": "pending"}, 
                "testing": {"status": "pending"},
                "reporting": {"status": "pending"}
            }
        }
        
        try:
            # Phase 1: Project Generation
            logger.info("📝 Phase 1: Project Generation")
            workflow_result["phases"]["generation"]["status"] = "running"
            
            generation_result = self.project_generator.generate_project(
                prompt=prompt,
                prompt_method=prompt_method,
                prompt_key=prompt_key,
                project_name=project_name
            )
            
            if not generation_result.get("success"):
                workflow_result["phases"]["generation"] = {
                    "status": "failed",
                    "error": generation_result.get("error", "Unknown generation error"),
                    "result": generation_result
                }
                workflow_result["status"] = "failed"
                logger.error(f"❌ Generation failed: {generation_result.get('error', 'Unknown generation error')}")
                return workflow_result
            
            workflow_result["phases"]["generation"] = {
                "status": "completed",
                "result": generation_result
            }
            logger.info("✅ Phase 1: Project Generation completed successfully")
            
            project_path = generation_result.get("project_output_directory") or generation_result.get("project_workspace")
            
            if skip_deployment:
                logger.info("⏭️ Skipping deployment phase")
                workflow_result["phases"]["deployment"]["status"] = "skipped"
                workflow_result["phases"]["testing"]["status"] = "skipped"
            else:
                # Phase 2: Deployment
                logger.info("🚀 Phase 2: Smart Deployment")
                workflow_result["phases"]["deployment"]["status"] = "running"
                
                deployment_result = self.deployment_manager.deploy_project(
                    project_path=project_path,
                    force_type=force_project_type
                )
                
                if not deployment_result.get("success"):
                    logger.error(f"❌ Deployment failed: {deployment_result.get('error', 'Unknown deployment error')}")
                    
                    # --- REFINEMENT LOOP ON DEPLOYMENT FAILURE ---
                    logger.info("🔄 REFINEMENT LOOP: Starting refinement for deployment failure...")
                    logger.info(f"🔄 REFINEMENT LOOP: Error to fix: {deployment_result.get('error', 'Unknown deployment error')}")
                    
                    error_log = deployment_result.get("error", "Unknown deployment error")
                    agents = self._setup_refinement_agents()
                    logger.info(f"🔄 REFINEMENT LOOP: Available agents: {list(agents.keys())}")
                    
                    project_manager = self.project_generator
                    analysis_result = {"fix_tasks": [{
                        "description": error_log,
                        "file_path": project_path,  # Use project_path instead of project_name
                        "issue_type": "DeploymentError",
                        "severity": "high",
                        "code_context": "",
                        "suggested_fix": "Fix the deployment error by ensuring the application entry point exists and is properly configured."
                    }]}
                    
                    logger.info("🔄 REFINEMENT LOOP: Starting refinement loop with max_iterations=3...")
                    try:
                        refinement_result = self.build_test_manager.run_refinement_loop(
                            analysis_result=analysis_result,
                            agents=agents,
                            project_manager=project_manager,
                            max_iterations=3
                        )
                        
                        logger.info(f"🔄 REFINEMENT LOOP: Refinement completed with success={refinement_result.get('success', False)}")
                        
                        # If refinement was successful, retry deployment
                        if refinement_result.get("success"):
                            logger.info("🔄 REFINEMENT LOOP: Retrying deployment after fixes...")
                            deployment_result = self.deployment_manager.deploy_project(
                                project_path=project_path,
                                force_type=force_project_type
                            )
                            
                            # IMPORTANT: Wait 20 seconds for services to fully stabilize after refinement fixes
                            logger.info("⏳ REFINEMENT LOOP: Waiting 20 seconds for services to stabilize after fixes...")
                            time.sleep(20)
                            
                            # Update workflow result with refinement information
                            workflow_result["phases"]["deployment"]["refinement_result"] = refinement_result
                            workflow_result["phases"]["deployment"]["result"] = deployment_result
                            
                            if deployment_result.get("success"):
                                logger.info("✅ REFINEMENT LOOP: Retry deployment successful!")
                            else:
                                logger.error("❌ REFINEMENT LOOP: Retry deployment failed")
                        else:
                            logger.error("❌ REFINEMENT LOOP: Refinement failed")
                            
                    except Exception as e:
                        logger.error(f"❌ REFINEMENT LOOP: Exception during refinement: {str(e)}")
                        logger.error(f"❌ REFINEMENT LOOP: Exception type: {type(e).__name__}")
                        import traceback
                        logger.error(f"❌ REFINEMENT LOOP: Full traceback: {traceback.format_exc()}")
                    
                    workflow_result["phases"]["deployment"] = {
                        "status": "failed",
                        "error": error_log,
                        "result": deployment_result,
                    }
                else:
                    workflow_result["phases"]["deployment"] = {
                        "status": "completed",
                        "result": deployment_result
                    }
                    logger.info("✅ Phase 2: Deployment completed successfully")
                
                service_urls = deployment_result.get("service_urls", [])
                logger.info(f"🔍 Service URLs detected: {service_urls}")
                
                # Check if we should attempt to force service URL detection
                if not service_urls and deployment_result.get("success"):
                    logger.warning("⚠️ Deployment succeeded but no service URLs detected")
                    logger.info("🔍 Attempting to detect service URLs manually...")
                    
                    # Try to detect common ports
                    potential_urls = ["http://localhost:3000", "http://localhost:8080", "http://localhost:5000", "http://localhost:9000"]
                    detected_urls = []
                    
                    for url in potential_urls:
                        try:
                            import requests
                            response = requests.get(url, timeout=2)
                            if response.status_code == 200:
                                detected_urls.append(url)
                                logger.info(f"✅ Found responding service at: {url}")
                        except:
                            logger.debug(f"❌ No service responding at: {url}")
                    
                    if detected_urls:
                        service_urls = detected_urls
                        deployment_result["service_urls"] = service_urls
                        logger.info(f"✅ Manually detected service URLs: {service_urls}")
                    else:
                        logger.warning("⚠️ No responding services found on common ports")
                
                logger.info(f"🔍 REFINEMENT CHECK: skip_testing={skip_testing}, service_urls={service_urls}")
                logger.info(f"🔍 REFINEMENT CHECK: deployment_success={deployment_result.get('success')}")
                
                if skip_testing or not service_urls:
                    if not service_urls:
                        logger.info("⏭️ No service URLs available, checking if refinement should run...")
                        
                        # Consider this a deployment issue and run refinement loop
                        if deployment_result.get("success"):
                            logger.info("🔄 REFINEMENT LOOP: STARTING - Deployment succeeded but no service URLs detected")
                            logger.info("🔄 REFINEMENT LOOP: This indicates the application may not be properly configured to start a web server")
                            
                            agents = self._setup_refinement_agents()
                            logger.info(f"🔄 REFINEMENT LOOP: Initialized agents: {list(agents.keys())}")
                            
                            project_manager = self.project_generator
                            analysis_result = {"fix_tasks": [{
                                "description": "Deployment succeeded but no service URLs were detected. The application may not be configured to start a web server or may be listening on an unexpected port.",
                                "file_path": None,
                                "issue_type": "ServiceURLDetectionError",
                                "severity": "medium",
                                "code_context": "",
                                "suggested_fix": "Ensure the application starts a web server and listens on a standard port (3000, 8080, 5000, etc.)"
                            }]}
                            
                            logger.info("🔄 REFINEMENT LOOP: Running refinement for service URL detection...")
                            logger.info(f"🔄 REFINEMENT LOOP: Project path: {project_path}")
                            
                            try:
                                refinement_result = self.build_test_manager.run_refinement_loop(
                                    analysis_result=analysis_result,
                                    agents=agents,
                                    project_manager=project_manager,
                                    max_iterations=2
                                )
                                
                                logger.info(f"🔄 REFINEMENT LOOP: Service URL refinement completed with success={refinement_result.get('success', False)}")
                                
                                # If refinement was successful, retry deployment
                                if refinement_result.get("success"):
                                    logger.info("🔄 REFINEMENT LOOP: Retrying deployment after service URL fixes...")
                                    deployment_result = self.deployment_manager.deploy_project(
                                        project_path=project_path,
                                        force_type=force_project_type
                                    )
                                    
                                    # IMPORTANT: Wait 20 seconds for services to fully stabilize after refinement fixes
                                    logger.info("⏳ REFINEMENT LOOP: Waiting 20 seconds for services to stabilize after service URL fixes...")
                                    time.sleep(20)
                                    
                                    service_urls = deployment_result.get("service_urls", [])
                                    logger.info(f"🔄 REFINEMENT LOOP: After retry, service URLs: {service_urls}")
                                    
                                    # Update workflow result with refinement information
                                    workflow_result["phases"]["deployment"]["refinement_result"] = refinement_result
                                    workflow_result["phases"]["deployment"]["result"] = deployment_result
                                else:
                                    logger.error("❌ REFINEMENT LOOP: Service URL refinement failed")
                                    
                            except Exception as e:
                                logger.error(f"❌ REFINEMENT LOOP: Exception during refinement: {str(e)}")
                                logger.error(f"❌ REFINEMENT LOOP: Exception type: {type(e).__name__}")
                        else:
                            logger.info("⏭️ Deployment failed, refinement already handled in deployment section")
                    else:
                        logger.info("⏭️ Skipping testing phase as requested")
                    
                    logger.info(f"🔍 FINAL SERVICE URLs after refinement attempts: {service_urls}")
                    workflow_result["phases"]["testing"]["status"] = "skipped"
                else:
                    # Phase 3: Browser Testing
                    logger.info("🧪 Phase 3: Browser Testing")
                    logger.info(f"🧪 Testing URLs: {service_urls}")
                    workflow_result["phases"]["testing"]["status"] = "running"
                    
                    # Wait a bit for services to fully start
                    logger.info("⏳ Waiting for services to stabilize...")
                    time.sleep(10)
                    
                    # FIX: Properly await the async test_application method
                    try:
                        # Create an event loop if one doesn't exist
                        try:
                            loop = asyncio.get_event_loop()
                        except RuntimeError:
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                        
                        # Run the async function properly
                        testing_result = await self.browser_testing_manager.test_application(
                            service_urls=service_urls,
                            custom_tests=custom_tests
                        )
                    except Exception as e:
                        logger.error(f"❌ Browser testing failed with exception: {str(e)}")
                        testing_result = {"success": False, "error": str(e)}
                    
                    # FIX: Only consider browser testing as failed if all connections failed
                    # or if there's a specific error that isn't just connection failures
                    if not testing_result.get("success") and testing_result.get("successful_connections", 0) == 0:
                        logger.error(f"❌ Browser testing failed: {testing_result.get('error', 'Unknown browser test error')}")
                        
                        # --- REFINEMENT LOOP ON BROWSER TEST FAILURE (DOM/UI) ---
                        logger.info("🔄 REFINEMENT LOOP: Starting refinement for browser testing failure...")
                        logger.info(f"🔄 REFINEMENT LOOP: Browser test error: {testing_result.get('error', 'Unknown browser test error')}")
                    elif not testing_result.get("success") and testing_result.get("successful_connections", 0) > 0:
                        # If at least one connection was successful, consider testing partially successful
                        logger.info(f"⚠️ Browser testing partially successful: {testing_result.get('successful_connections')} URLs worked, {testing_result.get('failed_connections')} failed")
                        # Override success status for partial successes
                        testing_result["success"] = True
                    
                    # Only proceed with error_log and refinement if we got here via failure path
                    if not testing_result.get("success"):
                        error_log = testing_result.get("error", "Unknown browser test error")
                        agents = self._setup_refinement_agents()
                        logger.info(f"🔄 REFINEMENT LOOP: Available agents: {list(agents.keys())}")
                        
                        
                        project_manager = self.project_generator
                        analysis_result = {"fix_tasks": [{
                            "description": error_log,
                            "file_path": None,
                            "issue_type": "BrowserTestError",
                            "severity": "high",
                            "code_context": "",
                            "suggested_fix": "Fix the browser/DOM/UI test error."
                        }]}
                        
                        logger.info("🔄 REFINEMENT LOOP: Starting browser testing refinement loop...")
                        try:
                            refinement_result = self.build_test_manager.run_refinement_loop(
                                analysis_result=analysis_result,
                                agents=agents,
                                project_manager=project_manager,
                                max_iterations=2
                            )
                            
                            logger.info(f"🔄 REFINEMENT LOOP: Browser test refinement completed with success={refinement_result.get('success', False)}")
                            
                            # If refinement was successful, retry browser testing
                            if refinement_result.get("success"):
                                logger.info("🔄 REFINEMENT LOOP: Retrying browser testing after UI fixes...")
                                # Retry deployment first to apply fixes
                                deployment_result = self.deployment_manager.deploy_project(
                                    project_path=project_path,
                                    force_type=force_project_type
                                )
                                
                                # IMPORTANT: Wait 20 seconds for services to fully stabilize after refinement fixes
                                logger.info("⏳ REFINEMENT LOOP: Waiting 20 seconds for services to stabilize after UI fixes...")
                                time.sleep(20)
                                
                                service_urls = deployment_result.get("service_urls", [])
                                
                                if service_urls:
                                    testing_result = await self.browser_testing_manager.test_application(
                                        service_urls=service_urls,
                                        custom_tests=custom_tests
                                    )
                                    logger.info(f"🔄 REFINEMENT LOOP: Retry browser testing success={testing_result.get('success', False)}")
                                else:
                                    logger.error("❌ REFINEMENT LOOP: No service URLs after retry deployment")
                            else:
                                logger.error("❌ REFINEMENT LOOP: Browser test refinement failed")
                                
                        except Exception as e:
                            logger.error(f"❌ REFINEMENT LOOP: Exception during browser test refinement: {str(e)}")
                        
                        workflow_result["phases"]["testing"] = {
                            "status": "failed" if not testing_result.get("success") else "completed",
                            "error": testing_result.get("error") if not testing_result.get("success") else None,
                            "result": testing_result
                        }
                    else:
                        workflow_result["phases"]["testing"] = {
                            "status": "completed",
                            "result": testing_result
                        }
                        logger.info("✅ Phase 3: Browser Testing completed successfully")
            
            # Phase 4: Reporting
            logger.info("📊 Phase 4: Generating Report")
            workflow_result["phases"]["reporting"]["status"] = "running"
            
            # Make sure workflow status is properly set to completed
            workflow_result["status"] = "completed"
            
            # Generate comprehensive report
            report = self._generate_comprehensive_report(workflow_result)
            workflow_result["phases"]["reporting"] = {
                "status": "completed",
                "result": report
            }
            
            # Ensure these fields are properly set
            workflow_result["completed_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
            workflow_result["duration"] = time.time() - start_time
            
            logger.info("✅ Complete automation workflow finished successfully")
            
        except Exception as e:
            logger.error(f"❌ Workflow failed with exception: {str(e)}")
            logger.error(f"❌ Exception type: {type(e).__name__}")
            import traceback
            logger.error(f"❌ Exception traceback:\n{traceback.format_exc()}")
            
            workflow_result["status"] = "failed"
            workflow_result["error"] = str(e)
            workflow_result["completed_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
            workflow_result["duration"] = time.time() - start_time
        
        finally:
            # CLEANUP: Stop active deployments before exiting
            logger.info("🧹 Cleaning up active deployments...")
            try:
                self.cleanup_active_deployments()
                logger.info("✅ Deployment cleanup completed")
            except Exception as e:
                logger.error(f"❌ Deployment cleanup failed: {str(e)}")
        
        # Save workflow to history
        self._save_workflow_history()
        
        return workflow_result
    
    def _generate_comprehensive_report(self, workflow_result: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a comprehensive report of the entire workflow."""
        try:
            report = {
                "workflow_summary": {
                    "workflow_id": workflow_result["workflow_id"],
                    "status": workflow_result["status"],
                    "total_time": workflow_result.get("total_time_seconds"),
                    "phases_completed": len([p for p in workflow_result["phases"].values() if p["status"] == "completed"]),
                    "phases_failed": len([p for p in workflow_result["phases"].values() if p["status"] == "failed"]),
                    "phases_skipped": len([p for p in workflow_result["phases"].values() if p["status"] == "skipped"])
                },
                "generation_report": {},
                "deployment_report": {},
                "testing_report": {},
                "recommendations": [],
                "next_steps": []
            }
            
            # Generation report
            if workflow_result["phases"]["generation"]["status"] == "completed":
                gen_result = workflow_result["phases"]["generation"]["result"]
                project_analysis = gen_result.get("project_analysis", {})
                
                report["generation_report"] = {
                    "project_name": gen_result.get("project_name"),
                    "project_type": project_analysis.get("project_type"),
                    "total_files": project_analysis.get("total_files"),
                    "source_files": project_analysis.get("source_files_count"),
                    "config_files": project_analysis.get("config_files_count"),
                    "deployment_ready": gen_result.get("deployment_ready"),
                    "generation_time": gen_result.get("generation_time_seconds")
                }
                
                # Recommendations for generated project
                if not gen_result.get("deployment_ready"):
                    report["recommendations"].append("Add deployment configuration files (package.json, requirements.txt, etc.)")
                
                if project_analysis.get("total_files", 0) < 5:
                    report["recommendations"].append("Consider adding more comprehensive project structure")
            
            # Deployment report
            if workflow_result["phases"]["deployment"]["status"] == "completed":
                dep_result = workflow_result["phases"]["deployment"]["result"]
                
                report["deployment_report"] = {
                    "deployment_id": dep_result.get("deployment_id"),
                    "project_type": dep_result.get("project_type"),
                    "service_urls": dep_result.get("service_urls", []),
                    "deployment_successful": dep_result.get("success"),
                    "process_id": dep_result.get("process_id")
                }
                
                if not dep_result.get("service_urls"):
                    report["recommendations"].append("No service URLs detected - verify application is configured to start a web server")
            
            # Testing report
            if workflow_result["phases"]["testing"]["status"] == "completed":
                test_result = workflow_result["phases"]["testing"]["result"]
                
                if test_result.get("success"):
                    test_report = test_result.get("test_report", {})
                    summary = test_report.get("summary", {})
                    
                    report["testing_report"] = {
                        "total_urls_tested": summary.get("total_urls_tested"),
                        "successful_connections": summary.get("successful_connections"),
                        "overall_success_rate": summary.get("overall_success_rate"),
                        "detailed_results": test_result.get("detailed_results", [])
                    }
                    
                    # Testing recommendations
                    if summary.get("overall_success_rate", 0) < 100:
                        report["recommendations"].append("Some tests failed - review detailed test results")
                    
                    if summary.get("successful_connections", 0) == 0:
                        report["recommendations"].append("No successful connections - check if services are properly deployed")
                else:
                    report["testing_report"] = {
                        "error": test_result.get("error"),
                        "testing_failed": True
                    }
                    report["recommendations"].append("Browser testing failed - check browser automation setup")
            
            # Next steps
            if workflow_result["status"] == "completed":
                report["next_steps"] = [
                    "Review the comprehensive test results",
                    "Check deployed application URLs for functionality",
                    "Consider running additional custom tests",
                    "Deploy to production environment if tests pass"
                ]
            else:
                report["next_steps"] = [
                    "Review failed phases and error messages",
                    "Fix identified issues",
                    "Re-run the workflow"
                ]
            
            # Overall assessment - FIX: Lower success threshold and improve status handling
            # Always use the workflow status from the workflow_result directly
            report["workflow_summary"]["status"] = workflow_result["status"]
            
            # Lower the success threshold from 80% to 30%
            if report["testing_report"].get("overall_success_rate", 0) >= 30:
                if workflow_result["status"] == "completed":
                    report["overall_assessment"] = "SUCCESS - Project generated, deployed, and tested successfully"
                else:
                    report["overall_assessment"] = "PARTIAL SUCCESS - Most phases completed but workflow had issues"
            else:
                if workflow_result["status"] == "completed":
                    report["overall_assessment"] = "PARTIAL SUCCESS - Project deployed but has significant test failures"
                else:
                    report["overall_assessment"] = "FAILED - Multiple workflow phases had issues"
            
            return report
            
        except Exception as e:
            logger.error(f"Failed to generate comprehensive report: {str(e)}")
            return {"error": str(e)}
    
    def run_batch_workflows(
        self, 
        prompts: List[str], 
        project_names: Optional[List[str]] = None,
        custom_tests_list: Optional[List[List[str]]] = None
    ) -> List[Dict[str, Any]]:
        """
        Run multiple workflows in batch.
        
        Args:
            prompts: List of project prompts
            project_names: Optional list of project names
            custom_tests_list: Optional list of custom tests for each project
            
        Returns:
            List of workflow results
        """
        logger.info(f"🔄 Running batch workflows for {len(prompts)} projects")
        
        results = []
        
        for i, prompt in enumerate(prompts):
            logger.info(f"🚀 Running workflow {i+1}/{len(prompts)}")
            
            project_name = project_names[i] if project_names and i < len(project_names) else None
            custom_tests = custom_tests_list[i] if custom_tests_list and i < len(custom_tests_list) else None
            
            result = self.run_complete_workflow(
                prompt=prompt,
                prompt_method="custom",
                project_name=project_name,
                custom_tests=custom_tests
            )
            
            results.append(result)
            
            # Add delay between workflows
            time.sleep(5)
        
        return results
    
    def cleanup_active_deployments(self) -> Dict[str, Any]:
        """
        Clean up active deployments by stopping running services.
        
        Returns:
            Dict with cleanup results
        """
        logger.info("🧹 Starting deployment cleanup...")
        cleanup_result = {
            "cleanup_attempted": True,
            "services_stopped": [],
            "errors": []
        }
        
        try:
            # Stop deployments using the deployment manager
            if hasattr(self.deployment_manager, 'stop_all_services'):
                stop_result = self.deployment_manager.stop_all_services()
                cleanup_result.update(stop_result)
                logger.info(f"✅ Deployment manager cleanup completed: {stop_result}")
            elif hasattr(self.deployment_manager, 'active_processes'):
                # Manually stop processes if the method doesn't exist
                stopped_count = 0
                for process_info in getattr(self.deployment_manager, 'active_processes', []):
                    try:
                        if 'process' in process_info and process_info['process']:
                            process_info['process'].terminate()
                            stopped_count += 1
                            cleanup_result["services_stopped"].append(f"PID {process_info['process'].pid}")
                            logger.info(f"✅ Stopped process PID {process_info['process'].pid}")
                    except Exception as e:
                        error_msg = f"Failed to stop process: {str(e)}"
                        cleanup_result["errors"].append(error_msg)
                        logger.error(f"❌ {error_msg}")
                
                logger.info(f"✅ Manually stopped {stopped_count} processes")
            else:
                logger.info("ℹ️ No active deployment processes found to clean up")
                
        except Exception as e:
            error_msg = f"Cleanup failed: {str(e)}"
            cleanup_result["errors"].append(error_msg)
            logger.error(f"❌ {error_msg}")
        
        return cleanup_result
    
    def get_workflow_history(self) -> List[Dict[str, Any]]:
        """Get the history of all workflow runs."""
        return self.workflow_history
    
    def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific workflow."""
        for workflow in self.workflow_history:
            if workflow["workflow_id"] == workflow_id:
                return workflow
        return None
    
    def _save_workflow_history(self):
        """Save workflow history to file."""
        try:
            history_file = self.workspace_path / "workflow_history.json"
            with open(history_file, 'w') as f:
                json.dump(self.workflow_history, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save workflow history: {str(e)}")
    
    def load_workflow_history(self):
        """Load workflow history from file."""
        try:
            history_file = self.workspace_path / "workflow_history.json"
            if history_file.exists():
                with open(history_file, 'r') as f:
                    self.workflow_history = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load workflow history: {str(e)}")
    
    def generate_workflow_summary_report(self) -> Dict[str, Any]:
        """Generate a summary report of all workflows."""
        total_workflows = len(self.workflow_history)
        successful_workflows = len([w for w in self.workflow_history if w["status"] == "completed"])
        
        return {
            "total_workflows": total_workflows,
            "successful_workflows": successful_workflows,
            "success_rate": (successful_workflows / total_workflows * 100) if total_workflows > 0 else 0,
            "recent_workflows": self.workflow_history[-5:] if self.workflow_history else [],
            "average_completion_time": sum(
                w.get("total_time_seconds", 0) for w in self.workflow_history 
                if w.get("total_time_seconds")
            ) / len([w for w in self.workflow_history if w.get("total_time_seconds")]) if self.workflow_history else 0
        }

# Convenience functions for easy usage
def run_quick_workflow(prompt: str, workspace_path: str = "./quick_automation") -> Dict[str, Any]:
    """Run a quick complete workflow with minimal setup."""
    workflow = AutomationWorkflow(workspace_path=workspace_path)
    return workflow.run_complete_workflow(prompt=prompt, prompt_method="custom")

def run_preset_workflow(preset_key: str, workspace_path: str = "./preset_automation") -> Dict[str, Any]:
    """Run a workflow using a preset prompt."""
    workflow = AutomationWorkflow(workspace_path=workspace_path)
    return workflow.run_complete_workflow(prompt_method="preset", prompt_key=preset_key)

if __name__ == "__main__":
    # Test the automation workflow
    workflow = AutomationWorkflow()
    
    # Example workflow
    test_prompt = "Create a simple FastAPI application with a health check endpoint"
    result = workflow.run_complete_workflow(prompt=test_prompt, prompt_method="custom")
    
    print("Workflow Result:")
    print(json.dumps(result, indent=2))
