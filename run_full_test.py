#!/usr/bin/env python3
"""
Full automation pipeline test script that properly loads environment variables.
"""

import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Add the src directory to the Python path
sys.path.append(str(Path(__file__).parent / "src"))

# First load .env file to get API keys
load_dotenv()

# Import after loading environment variables
from utils.automation_workflow import AutomationWorkflow

async def main():
    print("🚀 Starting complete automation pipeline test...")
    
    # Print loaded API key (partially masked for security)
    gemini_key = os.getenv("GEMINI_API_KEY", "")
    if gemini_key:
        masked_key = gemini_key[:4] + "..." + gemini_key[-4:] if len(gemini_key) > 8 else "..."
        print(f"✅ Loaded GEMINI_API_KEY: {masked_key}")
    else:
        print("❌ GEMINI_API_KEY not found in environment")
        return False
    
    # Initialize workflow
    workflow = AutomationWorkflow(
        workspace_path="./automation_workspace", 
        headless_browser=False  # Show browser for testing
    )
    
    # Define project prompt and test scenarios
    prompt = "Create a simple HTML page with multiple interactive buttons that perform different actions when clicked"
    test_scenarios = [
        "Test that all buttons are clickable",
        "Test that each button performs its expected action",
        "Test that the page is responsive"
    ]
    
    # Run the complete workflow
    print(f"📋 Running automation workflow for task: {prompt}")
    result = await workflow.run_complete_workflow(
        prompt=prompt,
        prompt_method="custom",
        project_name="interactive-buttons-test",
        custom_tests=test_scenarios
    )
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 AUTOMATION WORKFLOW SUMMARY")
    print("=" * 60)
    
    # Analyze result
    workflow_success = result.get("status") == "completed"
    print(f"Workflow Status: {'✅ SUCCESS' if workflow_success else '❌ FAILED'}")
    
    # Print detailed results for each phase
    for phase, data in result.get("phases", {}).items():
        status = data.get("status", "unknown")
        success = status == "completed"
        print(f"\n{phase.upper()} Phase: {'✅ SUCCESS' if success else '❌ FAILED'}")
        
        # Show specific details for each phase
        if phase == "deployment" and success:
            service_urls = data.get("result", {}).get("service_urls", [])
            if service_urls:
                print(f"  Deployed URLs:")
                for url in service_urls:
                    print(f"  - {url}")
        
        elif phase == "testing" and success:
            test_results = data.get("result", {})
            print(f"  Tests Run: {test_results.get('tested_urls', [])}")
            print(f"  Success Rate: {test_results.get('test_report', {}).get('summary', {}).get('overall_success_rate', 0):.1f}%")
            print(f"  Screenshots: {test_results.get('screenshots', [])}")
    
    return workflow_success

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
