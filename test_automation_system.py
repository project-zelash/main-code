#!/usr/bin/env python3
"""
Simple test of the automation workflow system with mocked components.
This test demonstrates the workflow without requiring actual API keys.
"""

import os
import sys
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch

# Add the src directory to the Python path
sys.path.append(str(Path(__file__).parent / "src"))

def test_workflow_components():
    """Test individual workflow components."""
    print("🧪 Testing individual workflow components...")
    
    try:
        # Test imports
        from utils.automation_workflow import AutomationWorkflow
        from utils.project_generator import ProjectGenerator
        from utils.deployment_manager import SmartDeploymentManager
        from utils.browser_testing_manager import BrowserTestingManager
        
        print("✅ All imports successful")
        
        # Test initialization with mocked dependencies
        with patch('service.llm_factory.LLMFactory') as mock_llm_factory, \
             patch('service.tool_service.ToolService') as mock_tool_service:
            
            # Mock the LLM factory
            mock_llm_factory.return_value = Mock()
            
            # Mock the tool service
            mock_tool_service.return_value = Mock()
            mock_tool_service.return_value.get_tool.return_value = Mock()
            mock_tool_service.return_value.register_tool.return_value = None
            
            workflow = AutomationWorkflow()
            print("✅ AutomationWorkflow initialization successful with mocks")
            
            # Test project generator
            project_gen = workflow.project_generator
            print("✅ ProjectGenerator component accessible")
            
            # Test deployment manager  
            deploy_mgr = workflow.deployment_manager
            print("✅ DeploymentManager component accessible")
            
            # Test browser testing manager
            browser_mgr = workflow.browser_testing_manager
            print("✅ BrowserTestingManager component accessible")
            
        return True
        
    except Exception as e:
        print(f"❌ Component test failed: {e}")
        return False

def test_mock_workflow():
    """Test a complete workflow with mocked LLM responses."""
    print("\n🎭 Testing complete workflow with mocked responses...")
    
    try:
        with patch('service.llm_factory.LLMFactory') as mock_llm_factory, \
             patch('service.tool_service.ToolService') as mock_tool_service, \
             patch('repository.execution.orchestration_engine.OrchestrationEngine') as mock_orchestration:
            
            # Mock the LLM factory
            mock_llm_factory.return_value = Mock()
            
            # Mock the tool service
            mock_tool_service.return_value = Mock()
            mock_tool_service.return_value.get_tool.return_value = Mock()
            mock_tool_service.return_value.register_tool.return_value = None
            
            # Mock the orchestration engine with a successful project generation
            mock_orchestration_instance = Mock()
            mock_orchestration_instance.run_full_workflow.return_value = {
                "success": True,
                "project_output_directory": "/tmp/test_project",
                "files_created": ["index.html", "style.css"],
                "message": "Project generated successfully"
            }
            mock_orchestration.return_value = mock_orchestration_instance
            
            # Create test project files
            test_project_dir = tempfile.mkdtemp()
            index_html = Path(test_project_dir) / "index.html"
            index_html.write_text("""
<!DOCTYPE html>
<html>
<head><title>Hello World</title></head>
<body><h1>Hello World!</h1></body>
</html>
            """)
            
            # Mock the project generation to return our test directory
            mock_orchestration_instance.run_full_workflow.return_value["project_output_directory"] = test_project_dir
            
            # Initialize workflow
            from utils.automation_workflow import AutomationWorkflow
            workflow = AutomationWorkflow()
            
            # Run a test workflow with mocked components
            result = workflow.run_complete_workflow(
                prompt="Create a simple HTML hello world page",
                prompt_method="custom",
                skip_deployment=True,  # Skip deployment for this test
                skip_testing=True      # Skip testing for this test
            )
            
            print(f"✅ Mock workflow completed")
            print(f"   Status: {result.get('status')}")
            print(f"   Workflow ID: {result.get('workflow_id')}")
            print(f"   Phases completed: {result.get('phases', {}).keys()}")
            
            # Check if generation phase completed
            gen_phase = result.get('phases', {}).get('generation', {})
            if gen_phase.get('status') == 'completed':
                print("✅ Generation phase completed successfully")
            else:
                print(f"❌ Generation phase failed: {gen_phase}")
                
            return result.get('status') == 'completed'
            
    except Exception as e:
        print(f"❌ Mock workflow test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_cli_interface():
    """Test the CLI interface."""
    print("\n💻 Testing CLI interface...")
    
    try:
        import subprocess
        import tempfile
        
        # Test help command
        result = subprocess.run([
            sys.executable, 'automation_main.py', '--help'
        ], capture_output=True, text=True, cwd=Path(__file__).parent)
        
        if result.returncode == 0 and 'Complete Automation Workflow System' in result.stdout:
            print("✅ CLI help command works")
        else:
            print(f"❌ CLI help failed: {result.stderr}")
            return False
            
        # Test create-example-config
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "test_config.json"
            
            result = subprocess.run([
                sys.executable, 'automation_main.py', 
                'create-example-config', '--output', str(config_path)
            ], capture_output=True, text=True, cwd=Path(__file__).parent)
            
            if result.returncode == 0 and config_path.exists():
                print("✅ CLI create-example-config works")
                
                # Check config content
                with open(config_path) as f:
                    config = json.load(f)
                    if 'workflows' in config and len(config['workflows']) > 0:
                        print("✅ Generated config has valid structure")
                    else:
                        print("❌ Generated config has invalid structure")
                        return False
            else:
                print(f"❌ CLI create-example-config failed: {result.stderr}")
                return False
                
        return True
        
    except Exception as e:
        print(f"❌ CLI test failed: {e}")
        return False

def test_file_structure():
    """Test that all required files exist."""
    print("\n📁 Testing file structure...")
    
    required_files = [
        "automation_main.py",
        "src/utils/automation_workflow.py",
        "src/utils/project_generator.py", 
        "src/utils/deployment_manager.py",
        "src/utils/browser_testing_manager.py",
        "src/service/llm_factory.py",
        "src/service/tool_service.py",
        "README_AUTOMATION.md",
        "examples/batch_config_simple.json"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Missing files: {missing_files}")
        return False
    else:
        print("✅ All required files exist")
        return True

def main():
    """Run all tests."""
    print("🚀 Starting Automation Workflow System Tests")
    print("=" * 60)
    
    tests = [
        ("File Structure", test_file_structure),
        ("Component Imports", test_workflow_components),
        ("Mock Workflow", test_mock_workflow),
        ("CLI Interface", test_cli_interface)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        print("-" * 40)
        success = test_func()
        results.append((test_name, success))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{test_name:20} {status}")
    
    print(f"\nPassed: {passed}/{total}")
    print(f"Success Rate: {passed/total*100:.1f}%")
    
    if passed == total:
        print("\n🎉 All tests passed! The automation workflow system is ready to use.")
        print("\n🔧 Next steps:")
        print("   1. Set up your LLM API keys (GEMINI_API_KEY, OPENAI_API_KEY, etc.)")
        print("   2. Run: python3 automation_main.py --help")
        print("   3. Try: python3 automation_main.py create-example-config")
        print("   4. Run: python3 automation_main.py generate-deploy-test --prompt 'Your idea'")
    else:
        print(f"\n❌ {total-passed} tests failed. Please review the errors above.")
        
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
