#!/usr/bin/env python3
"""
End-to-End Test Suite for Complete Automation Workflow System
Tests the full pipeline: Generate → Deploy → Test → Report
"""

import os
import sys
import json
import time
import subprocess
import requests
from pathlib import Path
import logging
from typing import Dict, Any, List

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EndToEndTestSuite:
    """Complete end-to-end test suite for the automation workflow system."""
    
    def __init__(self):
        self.test_results = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "tests": {},
            "overall_success": False,
            "errors": [],
            "generated_projects": [],
            "deployed_services": []
        }
        
        # Test project prompt
        self.test_prompt = """Create a modern personal portfolio landing page website with the following features:

1. Hero section with name, title, and call-to-action button
2. About section with bio and skills
3. Projects section with 3 sample project cards (clickable)
4. Contact section with a working contact form
5. Navigation menu that smoothly scrolls to sections
6. Modern CSS styling with hover effects
7. Responsive design for mobile and desktop
8. Use vanilla HTML, CSS, and JavaScript (no frameworks)
9. Include interactive elements like button clicks and form submission
10. Make it visually appealing with gradients, shadows, and animations

The website should be fully functional as a single HTML file with embedded CSS and JavaScript."""

    def run_test_suite(self) -> Dict[str, Any]:
        """Run the complete end-to-end test suite."""
        logger.info("🚀 Starting End-to-End Test Suite")
        logger.info("=" * 80)
        
        try:
            # Test 1: System Status Check
            self.test_system_status()
            
            # Test 2: Project Generation
            self.test_project_generation()
            
            # Test 3: Project Deployment  
            self.test_project_deployment()
            
            # Test 4: Website Functionality Testing
            self.test_website_functionality()
            
            # Test 5: Cleanup
            self.test_cleanup()
            
            self.test_results["overall_success"] = all(
                test.get("success", False) for test in self.test_results["tests"].values()
            )
            
        except Exception as e:
            logger.error(f"❌ Test suite failed with error: {e}")
            self.test_results["errors"].append(str(e))
            self.test_results["overall_success"] = False
        
        self.generate_test_report()
        return self.test_results
    
    def test_system_status(self):
        """Test 1: Verify system status and components."""
        logger.info("📋 Test 1: System Status Check")
        test_result = {"name": "System Status", "success": False, "details": {}}
        
        try:
            # Import and test core components
            from utils.automation_workflow import AutomationWorkflow
            from utils.project_generator import ProjectGenerator
            from utils.deployment_manager import DeploymentManager
            from utils.browser_testing_manager import BrowserTestingManager
            
            test_result["details"]["imports"] = "✅ All core components imported successfully"
            
            # Check CLI availability
            cli_path = Path("automation_main.py")
            if cli_path.exists():
                test_result["details"]["cli"] = "✅ CLI interface available"
            else:
                test_result["details"]["cli"] = "❌ CLI interface missing"
                
            # Check API key
            api_key = os.getenv("GEMINI_API_KEY")
            if api_key:
                test_result["details"]["api_key"] = "✅ API key configured"
            else:
                test_result["details"]["api_key"] = "❌ API key missing"
                self.test_results["errors"].append("GEMINI_API_KEY not set")
                
            test_result["success"] = all("✅" in detail for detail in test_result["details"].values())
            logger.info(f"✅ System Status: {'PASS' if test_result['success'] else 'FAIL'}")
            
        except Exception as e:
            test_result["details"]["error"] = str(e)
            test_result["success"] = False
            logger.error(f"❌ System Status Test Failed: {e}")
        
        self.test_results["tests"]["system_status"] = test_result
    
    def test_project_generation(self):
        """Test 2: Generate a test project using the automation system."""
        logger.info("📋 Test 2: Project Generation")
        test_result = {"name": "Project Generation", "success": False, "details": {}}
        
        try:
            # Run project generation via CLI
            cmd = [
                "python", "automation_main.py", "generate-deploy-test",
                "--prompt", self.test_prompt
            ]
            
            logger.info("🤖 Running project generation...")
            start_time = time.time()
            
            # Set API key for the subprocess
            env = os.environ.copy()
            env["GEMINI_API_KEY"] = os.getenv("GEMINI_API_KEY", "")
            
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=180,  # 3 minutes timeout
                env=env
            )
            
            generation_time = time.time() - start_time
            
            test_result["details"]["command"] = " ".join(cmd)
            test_result["details"]["generation_time"] = f"{generation_time:.2f} seconds"
            test_result["details"]["exit_code"] = result.returncode
            test_result["details"]["stdout"] = result.stdout[-1000:]  # Last 1000 chars
            test_result["details"]["stderr"] = result.stderr[-500:] if result.stderr else ""
            
            # Check for generated project
            workspace_path = Path("automation_workspace/projects")
            if workspace_path.exists():
                projects = list(workspace_path.glob("**/"))
                latest_project = max(projects, key=lambda p: p.stat().st_mtime, default=None)
                
                if latest_project:
                    test_result["details"]["project_path"] = str(latest_project)
                    self.test_results["generated_projects"].append(str(latest_project))
                    
                    # Check for HTML files
                    html_files = list(latest_project.rglob("*.html"))
                    if html_files:
                        test_result["details"]["html_files"] = len(html_files)
                        test_result["success"] = True
                        logger.info(f"✅ Project Generated: {latest_project.name}")
                        logger.info(f"📁 Found {len(html_files)} HTML files")
                    else:
                        test_result["details"]["error"] = "No HTML files found in generated project"
                else:
                    test_result["details"]["error"] = "No project directory found"
            else:
                test_result["details"]["error"] = "Workspace directory not found"
                
        except subprocess.TimeoutExpired:
            test_result["details"]["error"] = "Project generation timed out"
            logger.error("⏰ Project generation timed out")
        except Exception as e:
            test_result["details"]["error"] = str(e)
            logger.error(f"❌ Project Generation Failed: {e}")
        
        self.test_results["tests"]["project_generation"] = test_result
        
    def test_project_deployment(self):
        """Test 3: Deploy the generated project and verify it's accessible."""
        logger.info("📋 Test 3: Project Deployment")
        test_result = {"name": "Project Deployment", "success": False, "details": {}}
        
        try:
            if not self.test_results["generated_projects"]:
                test_result["details"]["error"] = "No projects to deploy"
                self.test_results["tests"]["project_deployment"] = test_result
                return
            
            project_path = self.test_results["generated_projects"][-1]  # Latest project
            
            # Use deployment manager directly
            from utils.deployment_manager import DeploymentManager
            
            deployment_manager = DeploymentManager()
            logger.info(f"🚀 Deploying project: {project_path}")
            
            # Look for the actual project files in external directory
            external_project_dir = None
            if "automation_workspace/projects" in project_path:
                # Find corresponding external directory
                project_name = Path(project_path).name
                external_path = Path(f"/Users/saivishwasgooty/Documents/Projects/Hackathon/generated_projects/{project_name}")
                if external_path.exists():
                    external_project_dir = str(external_path)
                    
            deploy_path = external_project_dir or project_path
            deployment_result = deployment_manager.deploy_project(deploy_path)
            
            test_result["details"]["deployment_result"] = deployment_result
            test_result["details"]["project_path"] = deploy_path
            
            if deployment_result.get("success"):
                service_url = deployment_result.get("service_url")
                if service_url:
                    test_result["details"]["service_url"] = service_url
                    self.test_results["deployed_services"].append(service_url)
                    
                    # Test if service is accessible
                    time.sleep(2)  # Wait for service to start
                    try:
                        response = requests.get(service_url, timeout=10)
                        if response.status_code == 200:
                            test_result["details"]["http_status"] = response.status_code
                            test_result["details"]["content_length"] = len(response.text)
                            test_result["success"] = True
                            logger.info(f"✅ Service deployed and accessible at: {service_url}")
                        else:
                            test_result["details"]["http_status"] = response.status_code
                            test_result["details"]["error"] = f"HTTP {response.status_code}"
                    except requests.RequestException as e:
                        test_result["details"]["error"] = f"Service not accessible: {e}"
                else:
                    test_result["details"]["error"] = "No service URL returned"
            else:
                test_result["details"]["error"] = deployment_result.get("error", "Deployment failed")
                
        except Exception as e:
            test_result["details"]["error"] = str(e)
            logger.error(f"❌ Deployment Test Failed: {e}")
        
        self.test_results["tests"]["project_deployment"] = test_result
    
    def test_website_functionality(self):
        """Test 4: Test website functionality and interactive elements."""
        logger.info("📋 Test 4: Website Functionality Testing")
        test_result = {"name": "Website Functionality", "success": False, "details": {}}
        
        try:
            if not self.test_results["deployed_services"]:
                test_result["details"]["error"] = "No deployed services to test"
                self.test_results["tests"]["website_functionality"] = test_result
                return
            
            service_url = self.test_results["deployed_services"][-1]
            logger.info(f"🧪 Testing website functionality at: {service_url}")
            
            # Test basic HTTP response
            response = requests.get(service_url, timeout=10)
            test_result["details"]["http_status"] = response.status_code
            test_result["details"]["content_length"] = len(response.text)
            
            # Test HTML content
            html_content = response.text.lower()
            
            # Check for expected elements
            checks = {
                "html_structure": "<html" in html_content and "</html>" in html_content,
                "css_styling": "style" in html_content or ".css" in html_content,
                "javascript": "script" in html_content or "function" in html_content,
                "navigation": "nav" in html_content or "menu" in html_content,
                "interactive_elements": "button" in html_content or "onclick" in html_content,
                "form_elements": "form" in html_content or "input" in html_content,
                "responsive_design": "viewport" in html_content or "@media" in html_content
            }
            
            test_result["details"]["content_checks"] = checks
            test_result["details"]["passed_checks"] = sum(checks.values())
            test_result["details"]["total_checks"] = len(checks)
            
            # Test for portfolio-specific content
            portfolio_checks = {
                "hero_section": any(word in html_content for word in ["hero", "banner", "main"]),
                "about_section": "about" in html_content,
                "projects_section": "project" in html_content,
                "contact_section": "contact" in html_content
            }
            
            test_result["details"]["portfolio_checks"] = portfolio_checks
            test_result["details"]["portfolio_score"] = sum(portfolio_checks.values())
            
            # Success if most checks pass
            total_score = test_result["details"]["passed_checks"] + test_result["details"]["portfolio_score"]
            max_score = test_result["details"]["total_checks"] + len(portfolio_checks)
            
            test_result["details"]["overall_score"] = f"{total_score}/{max_score}"
            test_result["success"] = total_score >= (max_score * 0.7)  # 70% pass rate
            
            if test_result["success"]:
                logger.info(f"✅ Website Functionality Test PASSED ({total_score}/{max_score})")
            else:
                logger.info(f"⚠️ Website Functionality Test PARTIAL ({total_score}/{max_score})")
                
        except Exception as e:
            test_result["details"]["error"] = str(e)
            logger.error(f"❌ Website Functionality Test Failed: {e}")
        
        self.test_results["tests"]["website_functionality"] = test_result
    
    def test_cleanup(self):
        """Test 5: Cleanup test resources."""
        logger.info("📋 Test 5: Cleanup")
        test_result = {"name": "Cleanup", "success": False, "details": {}}
        
        try:
            # Stop deployed services
            if self.test_results["deployed_services"]:
                from utils.deployment_manager import DeploymentManager
                deployment_manager = DeploymentManager()
                
                stopped_services = []
                for service_url in self.test_results["deployed_services"]:
                    try:
                        cleanup_result = deployment_manager.stop_all_deployments()
                        stopped_services.append(service_url)
                    except Exception as e:
                        logger.warning(f"⚠️ Could not stop service {service_url}: {e}")
                
                test_result["details"]["stopped_services"] = stopped_services
            
            test_result["details"]["cleanup_completed"] = True
            test_result["success"] = True
            logger.info("✅ Cleanup completed")
            
        except Exception as e:
            test_result["details"]["error"] = str(e)
            logger.error(f"❌ Cleanup Failed: {e}")
        
        self.test_results["tests"]["cleanup"] = test_result
    
    def generate_test_report(self):
        """Generate comprehensive test report."""
        logger.info("\n" + "=" * 80)
        logger.info("📊 END-TO-END TEST REPORT")
        logger.info("=" * 80)
        
        # Summary
        total_tests = len(self.test_results["tests"])
        passed_tests = sum(1 for test in self.test_results["tests"].values() if test.get("success"))
        
        logger.info(f"Overall Result: {'✅ PASS' if self.test_results['overall_success'] else '❌ FAIL'}")
        logger.info(f"Tests Passed: {passed_tests}/{total_tests}")
        logger.info(f"Generated Projects: {len(self.test_results['generated_projects'])}")
        logger.info(f"Deployed Services: {len(self.test_results['deployed_services'])}")
        
        # Detailed results
        for test_name, test_data in self.test_results["tests"].items():
            status = "✅ PASS" if test_data.get("success") else "❌ FAIL"
            logger.info(f"\n{test_data['name']}: {status}")
            
            for key, value in test_data.get("details", {}).items():
                if key != "error":
                    logger.info(f"  {key}: {value}")
            
            if "error" in test_data.get("details", {}):
                logger.error(f"  Error: {test_data['details']['error']}")
        
        # Save report to file
        report_file = f"test_report_e2e_{int(time.time())}.json"
        with open(report_file, 'w') as f:
            json.dump(self.test_results, f, indent=2)
        
        logger.info(f"\n💾 Detailed report saved to: {report_file}")
        logger.info("=" * 80)


def main():
    """Main entry point for the end-to-end test suite."""
    print("🧪 COMPLETE AUTOMATION WORKFLOW - END-TO-END TEST SUITE")
    print("Testing: Generate → Deploy → Test → Report Pipeline")
    print("=" * 80)
    
    # Check for API key
    if not os.getenv("GEMINI_API_KEY"):
        print("❌ Error: GEMINI_API_KEY environment variable not set")
        print("Please set your API key: export GEMINI_API_KEY='your_key_here'")
        return 1
    
    # Run test suite
    test_suite = EndToEndTestSuite()
    results = test_suite.run_test_suite()
    
    return 0 if results["overall_success"] else 1

if __name__ == "__main__":
    sys.exit(main())
