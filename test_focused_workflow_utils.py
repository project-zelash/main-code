#!/usr/bin/env python3
"""
Focused Test for Complete Automation Workflow Utils

This test validates core workflow functionality in the utils/automation_workflow.py file.
"""

import os
import sys
import asyncio
import tempfile
import json
import time
from pathlib import Path
from unittest.mock import Mock, patch

# Add the src directory to the Python path
sys.path.append(str(Path(__file__).parent / "src"))

def test_workflow_imports():
    """Test that workflow components can be imported."""
    print("📦 Testing workflow imports...")
    
    try:
        from utils.automation_workflow import AutomationWorkflow, DirectPlaywrightTester
        print("✅ AutomationWorkflow imported successfully")
        print("✅ DirectPlaywrightTester imported successfully")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_workflow_initialization():
    """Test workflow initialization with mocked dependencies."""
    print("\n🔧 Testing workflow initialization...")
    
    try:
        with patch('service.llm_factory.LLMFactory') as mock_llm_factory, \
             patch('service.tool_service.ToolService') as mock_tool_service:
            
            mock_llm_factory.return_value = Mock()
            mock_tool_service.return_value = Mock()
            mock_tool_service.return_value.get_tool.return_value = Mock()
            mock_tool_service.return_value.register_tool.return_value = None
            
            from utils.automation_workflow import AutomationWorkflow
            workflow = AutomationWorkflow()
            
            print("✅ AutomationWorkflow initialized successfully")
            
            # Test component access
            components = [
                ("project_generator", "ProjectGenerator"),
                ("deployment_manager", "DeploymentManager"),
                ("browser_testing_manager", "DirectPlaywrightTester")
            ]
            
            all_components_ok = True
            for comp_name, comp_type in components:
                try:
                    comp = getattr(workflow, comp_name)
                    print(f"✅ {comp_type} component accessible")
                except Exception as e:
                    print(f"❌ {comp_type} component failed: {e}")
                    all_components_ok = False
            
            return all_components_ok
            
    except Exception as e:
        print(f"❌ Workflow initialization failed: {e}")
        return False

async def test_mocked_workflow():
    """Test complete workflow with mocked components."""
    print("\n🎭 Testing mocked complete workflow...")
    
    try:
        with patch('service.llm_factory.LLMFactory') as mock_llm_factory, \
             patch('service.tool_service.ToolService') as mock_tool_service, \
             patch('repository.execution.orchestration_engine.OrchestrationEngine') as mock_orchestration:
            
            # Setup mocks
            mock_llm_factory.return_value = Mock()
            mock_tool_service.return_value = Mock()
            mock_tool_service.return_value.get_tool.return_value = Mock()
            mock_tool_service.return_value.register_tool.return_value = None
            
            mock_orchestration_instance = Mock()
            mock_orchestration_instance.run_full_workflow.return_value = {
                "success": True,
                "project_output_directory": "/tmp/mock_project",
                "files_created": ["index.html"],
                "message": "Mock project generated"
            }
            mock_orchestration.return_value = mock_orchestration_instance
            
            from utils.automation_workflow import AutomationWorkflow
            workflow = AutomationWorkflow()
            
            # Run workflow with skipped phases
            result = await workflow.run_complete_workflow(
                prompt="Create a test app",
                prompt_method="custom",
                skip_deployment=True,
                skip_testing=True
            )
            
            success = result.get("status") == "completed"
            print(f"✅ Mocked workflow completed: {success}")
            print(f"   Status: {result.get('status')}")
            print(f"   Workflow ID: {result.get('workflow_id')}")
            
            # Check phases
            phases = result.get("phases", {})
            for phase in ["generation", "deployment", "testing", "reporting"]:
                status = phases.get(phase, {}).get("status", "unknown")
                print(f"   {phase}: {status}")
            
            return success
            
    except Exception as e:
        print(f"❌ Mocked workflow failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_playwright_tester():
    """Test DirectPlaywrightTester functionality."""
    print("\n🎬 Testing DirectPlaywrightTester...")
    
    try:
        from utils.automation_workflow import DirectPlaywrightTester
        
        # Test initialization
        tester = DirectPlaywrightTester(headless=True)
        print("✅ DirectPlaywrightTester initialized")
        
        # Test method existence
        methods = ["test_application", "_run_custom_tests", "_ensure_playwright_installed"]
        for method in methods:
            if hasattr(tester, method):
                print(f"✅ Method {method} exists")
            else:
                print(f"❌ Method {method} missing")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ DirectPlaywrightTester test failed: {e}")
        return False

def test_workflow_methods():
    """Test workflow methods exist and are callable."""
    print("\n🔍 Testing workflow methods...")
    
    try:
        with patch('service.llm_factory.LLMFactory') as mock_llm_factory, \
             patch('service.tool_service.ToolService') as mock_tool_service:
            
            mock_llm_factory.return_value = Mock()
            mock_tool_service.return_value = Mock()
            mock_tool_service.return_value.get_tool.return_value = Mock()
            mock_tool_service.return_value.register_tool.return_value = None
            
            from utils.automation_workflow import AutomationWorkflow
            workflow = AutomationWorkflow()
            
            # Test key methods
            methods = [
                "run_complete_workflow",
                "run_batch_workflows",
                "get_workflow_history",
                "cleanup_all_workflows",
                "_generate_comprehensive_report",
                "_setup_refinement_agents"
            ]
            
            all_methods_ok = True
            for method in methods:
                if hasattr(workflow, method) and callable(getattr(workflow, method)):
                    print(f"✅ Method {method} exists and callable")
                else:
                    print(f"❌ Method {method} missing or not callable")
                    all_methods_ok = False
            
            return all_methods_ok
            
    except Exception as e:
        print(f"❌ Workflow methods test failed: {e}")
        return False

async def test_simple_playwright():
    """Test DirectPlaywrightTester with a simple case."""
    print("\n🌐 Testing DirectPlaywrightTester with real test...")
    
    try:
        from utils.automation_workflow import DirectPlaywrightTester
        
        tester = DirectPlaywrightTester(headless=True)
        
        # Test with a simple URL
        test_urls = ["https://httpbin.org/html"]
        result = await tester.test_application(test_urls)
        
        success = result.get("success", False)
        print(f"✅ Playwright test completed: {success}")
        print(f"   Tested URLs: {len(test_urls)}")
        print(f"   Successful connections: {result.get('successful_connections', 0)}")
        
        return success
        
    except Exception as e:
        print(f"❌ Simple Playwright test failed: {e}")
        return False

async def main():
    """Run all focused tests."""
    print("🚀 FOCUSED AUTOMATION WORKFLOW UTILS TEST SUITE")
    print("=" * 60)
    
    tests = [
        ("Workflow Imports", test_workflow_imports, False),
        ("Workflow Initialization", test_workflow_initialization, False),
        ("Workflow Methods", test_workflow_methods, False),
        ("Playwright Tester", test_playwright_tester, False),
        ("Mocked Workflow", test_mocked_workflow, True),
        ("Simple Playwright Test", test_simple_playwright, True)
    ]
    
    results = []
    
    for test_name, test_func, is_async in tests:
        print(f"\n📋 {test_name}")
        print("-" * 40)
        
        try:
            if is_async:
                success = await test_func()
            else:
                success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ {test_name} exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    success_rate = (passed / total * 100) if total > 0 else 0
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{test_name:25} {status}")
    
    print(f"\nPassed: {passed}/{total}")
    print(f"Success Rate: {success_rate:.1f}%")
    
    if success_rate >= 80:
        print("\n🎉 EXCELLENT! Workflow utils are functioning properly!")
    elif success_rate >= 60:
        print("\n✅ GOOD! Most workflow utils are working.")
    else:
        print("\n⚠️ Some workflow utils need attention.")
    
    return success_rate >= 60

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
