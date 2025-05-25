#!/usr/bin/env python3
"""
Final verification and status report for the Complete Automation Workflow System.
"""

import os
import sys
import json
from pathlib import Path

# Add the src directory to the Python path
sys.path.append(str(Path(__file__).parent / "src"))

def check_system_status():
    """Check the status of all system components."""
    print("🔍 COMPLETE AUTOMATION WORKFLOW SYSTEM - STATUS CHECK")
    print("=" * 80)
    
    status = {
        "components": {},
        "files": {},
        "dependencies": {},
        "overall": "unknown"
    }
    
    # Check core files
    core_files = {
        "Main CLI": "automation_main.py",
        "AutomationWorkflow": "src/utils/automation_workflow.py", 
        "ProjectGenerator": "src/utils/project_generator.py",
        "DeploymentManager": "src/utils/deployment_manager.py",
        "BrowserTestingManager": "src/utils/browser_testing_manager.py",
        "Documentation": "README_AUTOMATION.md",
        "Demo Script": "demo.sh",
        "Simple Config": "examples/batch_config_simple.json",
        "Integration Tests": "tests/test_integration.py"
    }
    
    print("\n📁 CORE FILES:")
    print("-" * 40)
    for name, path in core_files.items():
        exists = Path(path).exists()
        status["files"][name] = exists
        emoji = "✅" if exists else "❌"
        print(f"{emoji} {name:20} {path}")
    
    # Check imports
    print("\n🔧 COMPONENT IMPORTS:")
    print("-" * 40)
    
    try:
        from utils.automation_workflow import AutomationWorkflow
        print("✅ AutomationWorkflow imported successfully")
        status["components"]["AutomationWorkflow"] = True
    except Exception as e:
        print(f"❌ AutomationWorkflow import failed: {e}")
        status["components"]["AutomationWorkflow"] = False
    
    try:
        from utils.project_generator import ProjectGenerator
        print("✅ ProjectGenerator imported successfully")
        status["components"]["ProjectGenerator"] = True
    except Exception as e:
        print(f"❌ ProjectGenerator import failed: {e}")
        status["components"]["ProjectGenerator"] = False
    
    try:
        from utils.deployment_manager import DeploymentManager
        print("✅ DeploymentManager imported successfully")
        status["components"]["DeploymentManager"] = True
    except Exception as e:
        print(f"❌ DeploymentManager import failed: {e}")
        status["components"]["DeploymentManager"] = False
    
    try:
        from utils.browser_testing_manager import BrowserTestingManager
        print("✅ BrowserTestingManager imported successfully")
        status["components"]["BrowserTestingManager"] = True
    except Exception as e:
        print(f"❌ BrowserTestingManager import failed: {e}")
        status["components"]["BrowserTestingManager"] = False
    
    # Check existing components
    print("\n🔌 EXISTING COMPONENTS:")
    print("-" * 40)
    
    try:
        from service.llm_factory import LLMFactory
        print("✅ LLMFactory (existing) imported successfully")
        status["components"]["LLMFactory"] = True
    except Exception as e:
        print(f"❌ LLMFactory import failed: {e}")
        status["components"]["LLMFactory"] = False
    
    try:
        from service.tool_service import ToolService
        print("✅ ToolService (existing) imported successfully")
        status["components"]["ToolService"] = True
    except Exception as e:
        print(f"❌ ToolService import failed: {e}")
        status["components"]["ToolService"] = False
    
    try:
        from repository.execution.orchestration_engine import OrchestrationEngine
        print("✅ OrchestrationEngine (existing) imported successfully")
        status["components"]["OrchestrationEngine"] = True
    except Exception as e:
        print(f"❌ OrchestrationEngine import failed: {e}")
        status["components"]["OrchestrationEngine"] = False
    
    # Check CLI functionality
    print("\n🖥️  CLI FUNCTIONALITY:")
    print("-" * 40)
    
    try:
        if Path("automation_main.py").exists():
            print("✅ CLI entry point exists")
            # Test CLI import
            import automation_main
            print("✅ CLI module imports successfully")
            status["components"]["CLI"] = True
        else:
            print("❌ CLI entry point missing")
            status["components"]["CLI"] = False
    except Exception as e:
        print(f"❌ CLI import failed: {e}")
        status["components"]["CLI"] = False
    
    # Check example configurations
    print("\n📋 EXAMPLE CONFIGURATIONS:")
    print("-" * 40)
    
    config_files = [
        "examples/batch_config_simple.json",
        "examples/batch_config_comprehensive.json",
        "config/automation_config.json"
    ]
    
    for config_file in config_files:
        if Path(config_file).exists():
            try:
                with open(config_file, 'r') as f:
                    json.load(f)
                print(f"✅ {config_file} - Valid JSON")
                status["files"][config_file] = True
            except json.JSONDecodeError:
                print(f"❌ {config_file} - Invalid JSON")
                status["files"][config_file] = False
        else:
            print(f"❌ {config_file} - Missing")
            status["files"][config_file] = False
    
    # Overall status
    print("\n📊 OVERALL STATUS:")
    print("-" * 40)
    
    all_components = all(status["components"].values())
    critical_files = all([
        status["files"].get("Main CLI", False),
        status["files"].get("AutomationWorkflow", False),
        status["files"].get("ProjectGenerator", False),
        status["files"].get("DeploymentManager", False),
        status["files"].get("BrowserTestingManager", False)
    ])
    
    if all_components and critical_files:
        status["overall"] = "operational"
        print("✅ System is FULLY OPERATIONAL")
        print("🚀 Ready for automated workflow execution!")
    elif critical_files:
        status["overall"] = "partial"
        print("⚠️  System is PARTIALLY OPERATIONAL")
        print("💡 Some components may have import issues but core files exist")
    else:
        status["overall"] = "broken"
        print("❌ System has CRITICAL ISSUES")
        print("🔧 Missing core files or major import failures")
    
    # Next steps
    print("\n🎯 NEXT STEPS:")
    print("-" * 40)
    
    if status["overall"] == "operational":
        print("1. Set up your API keys in environment variables:")
        print("   export OPENAI_API_KEY='your_key_here'")
        print("   export ANTHROPIC_API_KEY='your_key_here'")
        print("")
        print("2. Run a simple test:")
        print("   python automation_main.py generate 'Create a simple React calculator app'")
        print("")
        print("3. Try the complete workflow:")
        print("   python automation_main.py workflow 'Create a todo app' --deploy --test")
        print("")
        print("4. Run batch processing:")
        print("   python automation_main.py batch examples/batch_config_simple.json")
        
    elif status["overall"] == "partial":
        print("1. Check Python path and dependencies")
        print("2. Verify all required modules are available")
        print("3. Run individual component tests")
        print("4. Check for missing environment variables")
        
    else:
        print("1. Verify all core files are present")
        print("2. Check file permissions")
        print("3. Review import paths and dependencies")
        print("4. Consider regenerating missing components")
    
    print("\n" + "=" * 80)
    return status

def main():
    """Main entry point."""
    try:
        status = check_system_status()
        
        # Save status to file
        with open("system_status_report.json", "w") as f:
            json.dump(status, f, indent=2)
        
        print(f"\n💾 Status report saved to: system_status_report.json")
        
        return 0 if status["overall"] == "operational" else 1
        
    except Exception as e:
        print(f"\n❌ Status check failed with error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
