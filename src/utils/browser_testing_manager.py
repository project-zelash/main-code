"""
Browser Testing Automation for Automated Workflow System

This module handles automated browser testing of deployed applications using
the MCP browser-use system and AI agents for comprehensive testing.
"""

import os
import json
import time
import asyncio
import subprocess
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import logging
import requests
from urllib.parse import urlparse, urljoin

# Import MCP browser helpers if available
try:
    from web_ui.src.mcp_helpers.browser_helpers import run_browser_task
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    logging.warning("MCP browser helpers not available. Some features will be disabled.")

# Direct Playwright automation as fallback
try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    logging.warning("Playwright not available. Browser automation will be limited.")

logger = logging.getLogger(__name__)

class BrowserTestingManager:
    """Handles automated browser testing of web applications."""
    
    def __init__(self, use_mcp: bool = True, headless: bool = False):
        """
        Initialize the browser testing manager.
        
        Args:
            use_mcp: Whether to use MCP browser-use system
            headless: Whether to run browsers in headless mode
        """
        self.use_mcp = use_mcp and MCP_AVAILABLE
        self.headless = headless
        self.test_results = []
        self.active_sessions = {}
        
        if not self.use_mcp and not PLAYWRIGHT_AVAILABLE:
            raise ImportError("Neither MCP browser-use nor Playwright is available")
    
    async def test_application(
        self, 
        service_urls: List[str], 
        test_scenarios: Optional[List[Dict[str, Any]]] = None,
        custom_tests: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Run comprehensive testing on deployed applications.
        
        Args:
            service_urls: List of URLs to test
            test_scenarios: Custom test scenarios
            custom_tests: List of custom test descriptions
            
        Returns:
            Comprehensive test results
        """
        try:
            logger.info(f"🧪 Starting browser testing for {len(service_urls)} URLs")
            
            all_results = []
            
            for url in service_urls:
                logger.info(f"🌐 Testing URL: {url}")
                
                # Basic connectivity test
                connectivity_result = self._test_connectivity(url)
                
                if not connectivity_result["success"]:
                    all_results.append({
                        "url": url,
                        "connectivity": connectivity_result,
                        "ui_tests": {"success": False, "error": "URL not accessible"},
                        "functionality_tests": {"success": False, "error": "URL not accessible"}
                    })
                    continue
                
                # UI and functionality tests
                if self.use_mcp:
                    ui_results = self._run_mcp_ui_tests(url, test_scenarios, custom_tests)
                else:
                    ui_results = await self._run_playwright_ui_tests(url, test_scenarios, custom_tests)
                
                functionality_results = self._run_functionality_tests(url)
                
                all_results.append({
                    "url": url,
                    "connectivity": connectivity_result,
                    "ui_tests": ui_results,
                    "functionality_tests": functionality_results,
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                })
            
            # Generate comprehensive report
            test_report = self._generate_test_report(all_results)
            
            # Save test results
            self.test_results.append({
                "test_id": f"test_{int(time.time())}",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "urls_tested": service_urls,
                "results": all_results,
                "report": test_report
            })
            
            logger.info(f"✅ Browser testing completed")
            
            return {
                "success": True,
                "test_report": test_report,
                "detailed_results": all_results,
                "summary": {
                    "total_urls": len(service_urls),
                    "successful_tests": len([r for r in all_results if r["connectivity"]["success"]]),
                    "failed_tests": len([r for r in all_results if not r["connectivity"]["success"]])
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Browser testing failed: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _test_connectivity(self, url: str) -> Dict[str, Any]:
        """Test basic connectivity to a URL."""
        try:
            logger.info(f"🔗 Testing connectivity to {url}")
            
            response = requests.get(url, timeout=10)
            
            return {
                "success": True,
                "status_code": response.status_code,
                "response_time": response.elapsed.total_seconds(),
                "content_length": len(response.content),
                "content_type": response.headers.get("content-type", "unknown")
            }
            
        except Exception as e:
            logger.error(f"Connectivity test failed for {url}: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _run_mcp_ui_tests(
        self, 
        url: str, 
        test_scenarios: Optional[List[Dict[str, Any]]] = None,
        custom_tests: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Run UI tests using MCP browser-use system."""
        try:
            logger.info(f"🤖 Running MCP UI tests for {url}")
            
            # Default test scenarios if none provided
            if not test_scenarios and not custom_tests:
                test_scenarios = self._get_default_test_scenarios(url)
            
            results = []
            
            # Run default scenarios
            if test_scenarios:
                for scenario in test_scenarios:
                    result = self._run_mcp_scenario(url, scenario)
                    results.append(result)
            
            # Run custom tests
            if custom_tests:
                for test_description in custom_tests:
                    task = f"Go to {url} and {test_description}"
                    result = self._run_mcp_task(task)
                    results.append({
                        "test_name": test_description,
                        "result": result
                    })
            
            return {
                "success": True,
                "test_results": results,
                "total_tests": len(results),
                "passed_tests": len([r for r in results if r.get("success", False)])
            }
            
        except Exception as e:
            logger.error(f"MCP UI tests failed: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _run_mcp_scenario(self, url: str, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """Run a specific test scenario using MCP."""
        try:
            scenario_name = scenario.get("name", "unnamed_test")
            task_description = scenario.get("task", "")
            
            # Build full task description
            full_task = f"Go to {url} and {task_description}"
            
            logger.info(f"🎯 Running scenario: {scenario_name}")
            
            # Run the task using MCP browser agent
            result = self._run_mcp_task(full_task)
            
            return {
                "test_name": scenario_name,
                "task": task_description,
                "success": "error" not in result.lower() and "failed" not in result.lower(),
                "result": result
            }
            
        except Exception as e:
            logger.error(f"MCP scenario failed: {str(e)}")
            return {
                "test_name": scenario.get("name", "unknown"),
                "success": False,
                "error": str(e)
            }
    
    def _run_mcp_task(self, task: str) -> str:
        """Run a single task using MCP browser agent."""
        try:
            if not MCP_AVAILABLE:
                return "MCP browser system not available"
            
            # Use the MCP browser helper
            result = run_browser_task(
                task=task,
                headless=self.headless,
                use_vision=True
            )
            
            return result
            
        except Exception as e:
            logger.error(f"MCP task failed: {str(e)}")
            return f"Error: {str(e)}"
    
    async def _run_playwright_ui_tests(
        self, 
        url: str, 
        test_scenarios: Optional[List[Dict[str, Any]]] = None,
        custom_tests: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Run UI tests using direct Playwright automation."""
        try:
            logger.info(f"🎭 Running Playwright UI tests for {url}")
            
            if not PLAYWRIGHT_AVAILABLE:
                return {"success": False, "error": "Playwright not available"}
            
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=self.headless)
                context = await browser.new_context()
                page = await context.new_page()
                
                results = []
                
                try:
                    # Navigate to the URL
                    await page.goto(url, wait_until="networkidle")
                    
                    # Take screenshot
                    screenshot_path = f"screenshot_{int(time.time())}.png"
                    await page.screenshot(path=screenshot_path)
                    
                    # Basic UI tests
                    basic_tests = await self._run_basic_playwright_tests(page)
                    results.extend(basic_tests)
                    
                    # Custom scenarios if provided
                    if test_scenarios:
                        for scenario in test_scenarios:
                            result = await self._run_playwright_scenario(page, scenario)
                            results.append(result)
                    
                    return {
                        "success": True,
                        "test_results": results,
                        "screenshot": screenshot_path,
                        "total_tests": len(results),
                        "passed_tests": len([r for r in results if r.get("success", False)])
                    }
                    
                finally:
                    await browser.close()
                    
        except Exception as e:
            logger.error(f"Playwright UI tests failed: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def _run_basic_playwright_tests(self, page) -> List[Dict[str, Any]]:
        """Run basic Playwright tests on a page."""
        tests = []
        
        try:
            # Test page title
            title = await page.title()
            tests.append({
                "test_name": "page_title",
                "success": bool(title and title.strip()),
                "result": f"Title: {title}"
            })
            
            # Test for common elements
            elements_to_check = [
                ("h1", "main heading"),
                ("nav", "navigation"),
                ("button", "buttons"),
                ("form", "forms"),
                ("img", "images")
            ]
            
            for selector, description in elements_to_check:
                element = await page.query_selector(selector)
                tests.append({
                    "test_name": f"has_{description.replace(' ', '_')}",
                    "success": element is not None,
                    "result": f"Found {description}" if element else f"No {description} found"
                })
            
            # Test for console errors
            console_errors = []
            page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
            
            # Wait a bit to collect console messages
            await page.wait_for_timeout(2000)
            
            tests.append({
                "test_name": "no_console_errors",
                "success": len(console_errors) == 0,
                "result": f"Console errors: {console_errors}" if console_errors else "No console errors"
            })
            
        except Exception as e:
            tests.append({
                "test_name": "basic_tests_error",
                "success": False,
                "error": str(e)
            })
        
        return tests
    
    async def _run_playwright_scenario(self, page, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """Run a specific scenario using Playwright."""
        try:
            scenario_name = scenario.get("name", "unnamed_test")
            actions = scenario.get("actions", [])
            
            for action in actions:
                action_type = action.get("type")
                
                if action_type == "click":
                    selector = action.get("selector")
                    await page.click(selector)
                elif action_type == "fill":
                    selector = action.get("selector")
                    text = action.get("text")
                    await page.fill(selector, text)
                elif action_type == "wait":
                    timeout = action.get("timeout", 1000)
                    await page.wait_for_timeout(timeout)
                # Add more action types as needed
            
            return {
                "test_name": scenario_name,
                "success": True,
                "result": "Scenario completed successfully"
            }
            
        except Exception as e:
            return {
                "test_name": scenario.get("name", "unknown"),
                "success": False,
                "error": str(e)
            }
    
    def _run_functionality_tests(self, url: str) -> Dict[str, Any]:
        """Run functionality tests on the application."""
        try:
            logger.info(f"⚙️ Running functionality tests for {url}")
            
            tests = []
            
            # Test different endpoints if it's an API
            if self._is_api_endpoint(url):
                api_tests = self._test_api_endpoints(url)
                tests.extend(api_tests)
            else:
                # Test common web app functionality
                web_tests = self._test_web_functionality(url)
                tests.extend(web_tests)
            
            return {
                "success": True,
                "test_results": tests,
                "total_tests": len(tests),
                "passed_tests": len([t for t in tests if t.get("success", False)])
            }
            
        except Exception as e:
            logger.error(f"Functionality tests failed: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _is_api_endpoint(self, url: str) -> bool:
        """Check if URL appears to be an API endpoint."""
        try:
            response = requests.get(url, timeout=5)
            content_type = response.headers.get("content-type", "").lower()
            
            return (
                "application/json" in content_type or
                "api" in url.lower() or
                response.headers.get("x-api-version") is not None
            )
        except:
            return False
    
    def _test_api_endpoints(self, base_url: str) -> List[Dict[str, Any]]:
        """Test common API endpoints."""
        tests = []
        
        # Common API endpoints to test
        endpoints = [
            "/health",
            "/status", 
            "/api/health",
            "/api/v1/health",
            "/docs",
            "/api/docs",
            "/swagger",
            "/openapi.json"
        ]
        
        for endpoint in endpoints:
            try:
                url = urljoin(base_url, endpoint)
                response = requests.get(url, timeout=5)
                
                tests.append({
                    "test_name": f"endpoint_{endpoint.replace('/', '_').strip('_')}",
                    "success": response.status_code < 400,
                    "status_code": response.status_code,
                    "url": url
                })
                
            except Exception as e:
                tests.append({
                    "test_name": f"endpoint_{endpoint.replace('/', '_').strip('_')}",
                    "success": False,
                    "error": str(e),
                    "url": urljoin(base_url, endpoint)
                })
        
        return tests
    
    def _test_web_functionality(self, url: str) -> List[Dict[str, Any]]:
        """Test common web application functionality."""
        tests = []
        
        try:
            # Test main page load time
            start_time = time.time()
            response = requests.get(url, timeout=10)
            load_time = time.time() - start_time
            
            tests.append({
                "test_name": "page_load_time",
                "success": load_time < 5.0,  # Consider 5 seconds as acceptable
                "load_time": load_time,
                "result": f"Page loaded in {load_time:.2f} seconds"
            })
            
            # Test for common static assets
            content = response.text.lower()
            
            assets_tests = [
                ("css", "stylesheet" in content or ".css" in content),
                ("javascript", "script" in content or ".js" in content),
                ("images", "img" in content or ".png" in content or ".jpg" in content)
            ]
            
            for asset_type, has_asset in assets_tests:
                tests.append({
                    "test_name": f"has_{asset_type}",
                    "success": has_asset,
                    "result": f"Found {asset_type}" if has_asset else f"No {asset_type} found"
                })
            
            # Test for responsive design indicators
            responsive_indicators = [
                "viewport",
                "media",
                "responsive",
                "mobile"
            ]
            
            has_responsive = any(indicator in content for indicator in responsive_indicators)
            tests.append({
                "test_name": "responsive_design",
                "success": has_responsive,
                "result": "Responsive design indicators found" if has_responsive else "No responsive design indicators"
            })
            
        except Exception as e:
            tests.append({
                "test_name": "web_functionality_error",
                "success": False,
                "error": str(e)
            })
        
        return tests
    
    def _get_default_test_scenarios(self, url: str) -> List[Dict[str, Any]]:
        """Get default test scenarios based on the application type."""
        
        # Basic scenarios that work for most web applications
        scenarios = [
            {
                "name": "navigation_test",
                "task": "navigate around the website, click on any navigation links or buttons you find, and report what you discover"
            },
            {
                "name": "form_interaction",
                "task": "look for any forms on the page and try to interact with them (but don't submit anything sensitive)"
            },
            {
                "name": "ui_elements_check", 
                "task": "check all the UI elements on the page - buttons, links, images, and report if anything seems broken or missing"
            },
            {
                "name": "responsive_test",
                "task": "test if the website works well by resizing the browser window to different sizes"
            }
        ]
        
        return scenarios
    
    def _generate_test_report(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate a comprehensive test report."""
        total_urls = len(results)
        successful_urls = len([r for r in results if r["connectivity"]["success"]])
        
        report = {
            "summary": {
                "total_urls_tested": total_urls,
                "successful_connections": successful_urls,
                "failed_connections": total_urls - successful_urls,
                "overall_success_rate": (successful_urls / total_urls * 100) if total_urls > 0 else 0
            },
            "detailed_results": [],
            "recommendations": []
        }
        
        for result in results:
            url_report = {
                "url": result["url"],
                "accessible": result["connectivity"]["success"],
                "response_time": result["connectivity"].get("response_time"),
                "ui_tests_passed": result["ui_tests"].get("passed_tests", 0),
                "ui_tests_total": result["ui_tests"].get("total_tests", 0),
                "functionality_tests_passed": result["functionality_tests"].get("passed_tests", 0),
                "functionality_tests_total": result["functionality_tests"].get("total_tests", 0)
            }
            
            report["detailed_results"].append(url_report)
            
            # Generate recommendations
            if not result["connectivity"]["success"]:
                report["recommendations"].append(f"Fix connectivity issues for {result['url']}")
            
            if result["ui_tests"].get("passed_tests", 0) < result["ui_tests"].get("total_tests", 1):
                report["recommendations"].append(f"Investigate UI issues for {result['url']}")
        
        return report
    
    def get_test_history(self) -> List[Dict[str, Any]]:
        """Get the history of all test runs."""
        return self.test_results
    
    def generate_comprehensive_test_suite(self, url: str, app_type: str = "web") -> List[str]:
        """Generate a comprehensive test suite based on application type."""
        
        base_tests = [
            "verify that the main page loads correctly and all elements are visible",
            "test all navigation links and ensure they work properly",
            "check that all images load correctly and have appropriate alt text",
            "verify that the page is responsive and works on different screen sizes"
        ]
        
        if app_type == "api":
            api_tests = [
                "test the API documentation if available",
                "verify that the API returns proper error codes for invalid requests",
                "check if the API has rate limiting or authentication"
            ]
            return base_tests + api_tests
        
        elif app_type == "ecommerce":
            ecommerce_tests = [
                "test the product search functionality",
                "verify that product pages display correctly",
                "test the shopping cart functionality (without making purchases)",
                "check the checkout process flow (stop before payment)"
            ]
            return base_tests + ecommerce_tests
        
        elif app_type == "blog":
            blog_tests = [
                "test the blog post listing and pagination",
                "verify that individual blog posts display correctly",
                "test the search functionality if available",
                "check the comment section (if enabled)"
            ]
            return base_tests + blog_tests
        
        elif app_type == "dashboard":
            dashboard_tests = [
                "test all dashboard widgets and charts",
                "verify that data filtering works correctly",
                "test any data export functionality",
                "check that user settings can be accessed"
            ]
            return base_tests + dashboard_tests
        
        else:
            return base_tests

    async def run_comprehensive_tests(
        self, 
        service_urls: List[str], 
        test_scenarios: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Run comprehensive tests - wrapper method for backward compatibility.
        
        Args:
            service_urls: List of URLs to test
            test_scenarios: List of test scenario descriptions
            
        Returns:
            Comprehensive test results
        """
        # Convert string test scenarios to dict format
        scenarios_dict = None
        if test_scenarios:
            scenarios_dict = [
                {"name": f"test_{i}", "task": scenario}
                for i, scenario in enumerate(test_scenarios)
            ]
        
        return await self.test_application(
            service_urls=service_urls,
            test_scenarios=scenarios_dict,
            custom_tests=test_scenarios
        )

# Convenience functions
def test_application_quick(service_urls: List[str], headless: bool = True) -> Dict[str, Any]:
    """Quick application testing with minimal setup."""
    manager = BrowserTestingManager(headless=headless)
    return manager.test_application(service_urls)

async def test_with_playwright(url: str, headless: bool = True) -> Dict[str, Any]:
    """Test application using Playwright directly."""
    manager = BrowserTestingManager(use_mcp=False, headless=headless)
    return await manager._run_playwright_ui_tests(url)

if __name__ == "__main__":
    # Test the browser testing manager
    test_urls = ["http://localhost:3000", "http://localhost:8000"]
    
    manager = BrowserTestingManager()
    result = manager.test_application(test_urls)
    
    print("Test Results:")
    print(json.dumps(result, indent=2))
