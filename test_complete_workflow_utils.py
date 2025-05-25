#!/usr/bin/env python3
"""
Comprehensive Test Suite for Complete Automation Workflow Utils

This test validates the entire automation workflow system:
1. AutomationWorkflow class functionality
2. DirectPlaywrightTester capabilities
3. End-to-end pipeline: Generate → Deploy → Test → Report
4. Error handling and refinement loops
5. Async workflow management
6. Batch processing
7. History and cleanup operations
"""

import os
import sys
import asyncio
import tempfile
import json
import time
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
import logging

# Add the src directory to the Python path
sys.path.append(str(Path(__file__).parent / "src"))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WorkflowUtilsTestSuite:
    """Comprehensive test suite for automation workflow utilities."""
    
    def __init__(self):
        self.test_results = []
        self.temp_dirs = []
        
    def add_result(self, test_name: str, success: bool, details: str = ""):
        """Add a test result."""
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        })
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details and not success:
            print(f"   Details: {details}")
    
    def cleanup(self):
        """Clean up temporary directories."""
        for temp_dir in self.temp_dirs:
            try:
                import shutil
                shutil.rmtree(temp_dir)
            except:
                pass
    
    async def test_direct_playwright_tester(self):
        """Test the DirectPlaywrightTester class."""
        try:
            from utils.automation_workflow import DirectPlaywrightTester
            
            # Test initialization
            tester = DirectPlaywrightTester(headless=True)
            self.add_result("DirectPlaywrightTester Initialization", True)
            
            # Test with a simple local HTML file
            test_dir = tempfile.mkdtemp()
            self.temp_dirs.append(test_dir)
            
            html_file = Path(test_dir) / "test.html"
            html_file.write_text("""
<!DOCTYPE html>
<html>
<head><title>Test Page</title></head>
<body>
    <h1>Test Application</h1>
    <button id="testBtn">Click Me</button>
    <input type="text" id="testInput" placeholder="Enter text">
    <div id="content">Content loaded</div>
</body>
</html>
            """)
            
            # Start a simple HTTP server for testing
            import http.server
            import socketserver
            import threading
            
            class TestHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
                def __init__(self, *args, **kwargs):
                    super().__init__(*args, directory=test_dir, **kwargs)
            
            # Find an available port
            port = 8899
            for i in range(10):
                try:
                    httpd = socketserver.TCPServer(("", port), TestHTTPRequestHandler)
                    break
                except OSError:
                    port += 1
            else:
                raise Exception("Could not find available port")
            
            # Start server in background
            server_thread = threading.Thread(target=httpd.serve_forever)
            server_thread.daemon = True
            server_thread.start()
            
            try:
                # Test basic browser functionality
                test_url = f"http://localhost:{port}/test.html"
                result = await tester.test_application([test_url])
                
                success = result.get("success", False)
                self.add_result("DirectPlaywrightTester Basic Test", success, 
                              f"Tested URL: {test_url}, Success: {success}")
                
                # Test custom test scenarios
                custom_tests = [
                    "Test button click functionality",
                    "Test form input",
                    "Test page navigation"
                ]
                
                result_with_custom = await tester.test_application([test_url], custom_tests)
                custom_success = result_with_custom.get("success", False)
                self.add_result("DirectPlaywrightTester Custom Tests", custom_success,
                              f"Custom tests executed: {len(custom_tests)}")
                
            finally:
                httpd.shutdown()
                httpd.server_close()
                
        except Exception as e:
            self.add_result("DirectPlaywrightTester Tests", False, str(e))
    
    async def test_automation_workflow_initialization(self):
        """Test AutomationWorkflow class initialization."""
        try:
            # Mock dependencies to avoid requiring actual services
            with patch('service.llm_factory.LLMFactory') as mock_llm_factory, \
                 patch('service.tool_service.ToolService') as mock_tool_service:
                
                mock_llm_factory.return_value = Mock()
                mock_tool_service.return_value = Mock()
                mock_tool_service.return_value.get_tool.return_value = Mock()
                mock_tool_service.return_value.register_tool.return_value = None
                
                from utils.automation_workflow import AutomationWorkflow
                
                # Test basic initialization
                workflow = AutomationWorkflow()
                self.add_result("AutomationWorkflow Initialization", True)
                
                # Test custom workspace path
                temp_workspace = tempfile.mkdtemp()
                self.temp_dirs.append(temp_workspace)
                
                workflow_custom = AutomationWorkflow(workspace_path=temp_workspace)
                self.add_result("AutomationWorkflow Custom Workspace", True)
                
                # Test component accessibility
                components = [
                    ("project_generator", "ProjectGenerator"),
                    ("deployment_manager", "DeploymentManager"), 
                    ("browser_testing_manager", "DirectPlaywrightTester"),
                    ("agent_service", "AgentManager"),
                    ("build_test_manager", "BuildTestManager")
                ]
                
                for component_name, expected_type in components:
                    try:
                        component = getattr(workflow, component_name)
                        self.add_result(f"AutomationWorkflow {expected_type} Component", 
                                      component is not None,
                                      f"Component type: {type(component).__name__}")
                    except AttributeError as e:
                        self.add_result(f"AutomationWorkflow {expected_type} Component", False, str(e))
                
        except Exception as e:
            self.add_result("AutomationWorkflow Initialization", False, str(e))
    
    async def test_workflow_methods(self):
        """Test AutomationWorkflow methods."""
        try:
            with patch('service.llm_factory.LLMFactory') as mock_llm_factory, \
                 patch('service.tool_service.ToolService') as mock_tool_service:
                
                mock_llm_factory.return_value = Mock()
                mock_tool_service.return_value = Mock()
                mock_tool_service.return_value.get_tool.return_value = Mock()
                mock_tool_service.return_value.register_tool.return_value = None
                
                from utils.automation_workflow import AutomationWorkflow
                workflow = AutomationWorkflow()
                
                # Test method existence
                methods_to_test = [
                    "run_complete_workflow",
                    "run_batch_workflows", 
                    "get_workflow_history",
                    "cleanup_all_workflows",
                    "_generate_comprehensive_report",
                    "_setup_refinement_agents",
                    "cleanup_active_deployments"
                ]
                
                for method_name in methods_to_test:
                    has_method = hasattr(workflow, method_name)
                    is_callable = callable(getattr(workflow, method_name, None))
                    self.add_result(f"AutomationWorkflow {method_name} Method", 
                                  has_method and is_callable,
                                  f"Exists: {has_method}, Callable: {is_callable}")
                
        except Exception as e:
            self.add_result("AutomationWorkflow Methods Test", False, str(e))
    
    async def test_mocked_complete_workflow(self):
        """Test complete workflow with mocked components."""
        try:
            with patch('service.llm_factory.LLMFactory') as mock_llm_factory, \
                 patch('service.tool_service.ToolService') as mock_tool_service, \
                 patch('repository.execution.orchestration_engine.OrchestrationEngine') as mock_orchestration:
                
                # Setup mocks
                mock_llm_factory.return_value = Mock()
                mock_tool_service.return_value = Mock()
                mock_tool_service.return_value.get_tool.return_value = Mock()
                mock_tool_service.return_value.register_tool.return_value = None
                
                # Mock successful project generation
                mock_orchestration_instance = Mock()
                mock_orchestration_instance.run_full_workflow.return_value = {
                    "success": True,
                    "project_output_directory": "/tmp/mock_project",
                    "files_created": ["index.html", "package.json"],
                    "message": "Project generated successfully"
                }
                mock_orchestration.return_value = mock_orchestration_instance
                
                from utils.automation_workflow import AutomationWorkflow
                workflow = AutomationWorkflow()
                
                # Test workflow with skipped deployment and testing
                result = await workflow.run_complete_workflow(
                    prompt="Create a test application",
                    prompt_method="custom",
                    skip_deployment=True,
                    skip_testing=True
                )
                
                success = result.get("status") == "completed"
                self.add_result("Complete Workflow (Mocked, Skipped Deploy/Test)", success,
                              f"Status: {result.get('status')}, Workflow ID: {result.get('workflow_id')}")
                
                # Test workflow phases
                phases = result.get("phases", {})
                for phase_name in ["generation", "deployment", "testing", "reporting"]:
                    phase_data = phases.get(phase_name, {})
                    phase_status = phase_data.get("status", "unknown")
                    self.add_result(f"Workflow Phase: {phase_name}", 
                                  phase_status in ["completed", "skipped"],
                                  f"Status: {phase_status}")
                
        except Exception as e:
            self.add_result("Mocked Complete Workflow", False, str(e))
    
    async def test_workflow_error_handling(self):
        """Test workflow error handling scenarios."""
        try:
            with patch('service.llm_factory.LLMFactory') as mock_llm_factory, \
                 patch('service.tool_service.ToolService') as mock_tool_service:
                
                mock_llm_factory.return_value = Mock()
                mock_tool_service.return_value = Mock()
                mock_tool_service.return_value.get_tool.return_value = Mock()
                mock_tool_service.return_value.register_tool.return_value = None
                
                from utils.automation_workflow import AutomationWorkflow
                workflow = AutomationWorkflow()
                
                # Mock project generator to fail
                workflow.project_generator.generate_project = Mock(return_value={
                    "success": False,
                    "error": "Mock generation failure"
                })
                
                result = await workflow.run_complete_workflow(
                    prompt="Test error handling",
                    prompt_method="custom"
                )
                
                # Should handle error gracefully
                has_error = "error" in result or result.get("status") == "failed"
                self.add_result("Workflow Error Handling", has_error,
                              f"Result status: {result.get('status')}")
                
        except Exception as e:
            self.add_result("Workflow Error Handling", False, str(e))
    
    async def test_batch_workflow_capability(self):
        """Test batch workflow processing."""
        try:
            with patch('service.llm_factory.LLMFactory') as mock_llm_factory, \
                 patch('service.tool_service.ToolService') as mock_tool_service:
                
                mock_llm_factory.return_value = Mock()
                mock_tool_service.return_value = Mock()
                mock_tool_service.return_value.get_tool.return_value = Mock()
                mock_tool_service.return_value.register_tool.return_value = None
                
                from utils.automation_workflow import AutomationWorkflow
                workflow = AutomationWorkflow()
                
                # Test batch workflow method existence and basic functionality
                has_batch_method = hasattr(workflow, 'run_batch_workflows')
                self.add_result("Batch Workflow Method Exists", has_batch_method)
                
                if has_batch_method:
                    # Test with empty batch
                    try:
                        results = workflow.run_batch_workflows([])
                        self.add_result("Batch Workflow Empty List", isinstance(results, list))
                    except Exception as e:
                        self.add_result("Batch Workflow Empty List", False, str(e))
                
        except Exception as e:
            self.add_result("Batch Workflow Capability", False, str(e))
    
    async def test_cleanup_operations(self):
        """Test cleanup and maintenance operations."""
        try:
            with patch('service.llm_factory.LLMFactory') as mock_llm_factory, \
                 patch('service.tool_service.ToolService') as mock_tool_service:
                
                mock_llm_factory.return_value = Mock()
                mock_tool_service.return_value = Mock()
                mock_tool_service.return_value.get_tool.return_value = Mock()
                mock_tool_service.return_value.register_tool.return_value = None
                
                from utils.automation_workflow import AutomationWorkflow
                workflow = AutomationWorkflow()
                
                # Test cleanup methods
                cleanup_methods = [
                    "cleanup_active_deployments",
                    "cleanup_all_workflows"
                ]
                
                for method_name in cleanup_methods:
                    try:
                        method = getattr(workflow, method_name)
                        method()  # Call the cleanup method
                        self.add_result(f"Cleanup Method: {method_name}", True)
                    except Exception as e:
                        self.add_result(f"Cleanup Method: {method_name}", False, str(e))
                
                # Test workflow history
                try:
                    history = workflow.get_workflow_history()
                    self.add_result("Workflow History Access", isinstance(history, list))
                except Exception as e:
                    self.add_result("Workflow History Access", False, str(e))
                
        except Exception as e:
            self.add_result("Cleanup Operations", False, str(e))
    
    async def test_refinement_loop_components(self):
        """Test refinement loop setup and components."""
        try:
            with patch('service.llm_factory.LLMFactory') as mock_llm_factory, \
                 patch('service.tool_service.ToolService') as mock_tool_service:
                
                mock_llm_factory.return_value = Mock()
                mock_tool_service.return_value = Mock()
                mock_tool_service.return_value.get_tool.return_value = Mock()
                mock_tool_service.return_value.register_tool.return_value = None
                
                from utils.automation_workflow import AutomationWorkflow
                workflow = AutomationWorkflow()
                
                # Test refinement agent setup
                try:
                    agents = workflow._setup_refinement_agents()
                    is_dict = isinstance(agents, dict)
                    has_agents = len(agents) > 0 if is_dict else False
                    self.add_result("Refinement Agents Setup", is_dict and has_agents,
                                  f"Agents type: {type(agents)}, Count: {len(agents) if is_dict else 'N/A'}")
                except Exception as e:
                    self.add_result("Refinement Agents Setup", False, str(e))
                
                # Test comprehensive report generation
                try:
                    mock_workflow_result = {
                        "workflow_id": "test_123",
                        "status": "completed",
                        "phases": {
                            "generation": {"status": "completed"},
                            "deployment": {"status": "completed"},
                            "testing": {"status": "completed"},
                            "reporting": {"status": "completed"}
                        }
                    }
                    
                    report = workflow._generate_comprehensive_report(mock_workflow_result)
                    is_report_dict = isinstance(report, dict)
                    self.add_result("Comprehensive Report Generation", is_report_dict,
                                  f"Report type: {type(report)}")
                except Exception as e:
                    self.add_result("Comprehensive Report Generation", False, str(e))
                
        except Exception as e:
            self.add_result("Refinement Loop Components", False, str(e))
    
    async def run_all_tests(self):
        """Run all tests in the suite."""
        print("🚀 Starting Comprehensive Automation Workflow Utils Test Suite")
        print("=" * 80)
        
        tests = [
            ("DirectPlaywrightTester Tests", self.test_direct_playwright_tester),
            ("AutomationWorkflow Initialization", self.test_automation_workflow_initialization),
            ("AutomationWorkflow Methods", self.test_workflow_methods),
            ("Mocked Complete Workflow", self.test_mocked_complete_workflow),
            ("Workflow Error Handling", self.test_workflow_error_handling),
            ("Batch Workflow Capability", self.test_batch_workflow_capability),
            ("Cleanup Operations", self.test_cleanup_operations),
            ("Refinement Loop Components", self.test_refinement_loop_components)
        ]
        
        for test_name, test_func in tests:
            print(f"\n📋 {test_name}")
            print("-" * 50)
            try:
                await test_func()
            except Exception as e:
                self.add_result(f"{test_name} (Exception)", False, str(e))
        
        # Summary
        print("\n" + "=" * 80)
        print("📊 COMPREHENSIVE TEST SUMMARY")
        print("=" * 80)
        
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        print("\n📋 Detailed Results:")
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test']}")
            if result["details"] and not result["success"]:
                print(f"    💬 {result['details']}")
        
        # Save detailed report
        report_file = f"test_report_workflow_utils_{int(time.time())}.json"
        with open(report_file, 'w') as f:
            json.dump({
                "summary": {
                    "total_tests": total,
                    "passed": passed,
                    "failed": total - passed,
                    "success_rate": success_rate,
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                },
                "detailed_results": self.test_results
            }, f, indent=2)
        
        print(f"\n💾 Detailed report saved to: {report_file}")
        
        if success_rate >= 80:
            print("\n🎉 EXCELLENT! Automation workflow utils are functioning properly!")
        elif success_rate >= 60:
            print("\n✅ GOOD! Most automation workflow utils are working with some issues.")
        else:
            print("\n⚠️ ATTENTION NEEDED! Several workflow utils components require fixes.")
        
        self.cleanup()
        return success_rate >= 60

async def main():
    """Run the comprehensive test suite."""
    test_suite = WorkflowUtilsTestSuite()
    success = await test_suite.run_all_tests()
    return success

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️ Test suite interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test suite failed with exception: {e}")
        sys.exit(1)
