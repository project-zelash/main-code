#!/usr/bin/env python3
"""
Test automation pipeline with interactive browser window
"""

import os
import sys
import asyncio
import time
import subprocess
import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

# Add src directory to path
sys.path.append(str(Path(__file__).parent / "src"))

async def test_automation_with_browser():
    """Run the test automation pipeline with browser window interaction"""
    try:
        from utils.automation_workflow import AutomationWorkflow
        
        print("🚀 Initializing AutomationWorkflow...")
        workspace_path = Path("./test_workspace")
        
        # Create workflow with headless_browser set to False to keep window open
        workflow = AutomationWorkflow(workspace_path=str(workspace_path), headless_browser=False)
        
        # Create a more complex HTML task with multiple interactive buttons
        task = """
        Create a simple HTML page with the following interactive buttons:
        1. A button that shows an alert message when clicked
        2. A button that changes the background color of the page
        3. A button that counts the number of times it has been clicked
        4. A button that toggles the visibility of an image
        
        Each button should have a clear label and visual feedback when interacted with.
        """
        
        # Define specific test scenarios for browser automation
        test_scenarios = [
            "Verify that all buttons are visible on the page",
            "Test that the alert button shows a message when clicked",
            "Test that the color change button changes the background color when clicked",
            "Test that the counter button increases its count when clicked multiple times",
            "Test that the toggle button correctly shows and hides an element"
        ]
        
        print(f"📋 Running automation workflow for task: {task}")
        
        # Run workflow with longer test timeout
        result = await workflow.run_complete_workflow(
            prompt=task,
            prompt_method="custom",
            project_name="interactive-buttons",
            custom_tests=test_scenarios
        )
        
        print("\n" + "=" * 60)
        print("📊 WORKFLOW RESULT SUMMARY")
        print("=" * 60)
        
        if result.get("success", False):
            print("✅ Workflow completed successfully!")
        else:
            print("❌ Workflow failed!")
            
        # Print detailed results including the deployed URLs
        print("\n📋 Detailed Results:")
        
        # Get deployment information
        deployment_result = result.get("phases", {}).get("deployment", {}).get("result", {})
        service_urls = deployment_result.get("service_urls", [])
        
        if service_urls:
            print("\n🌐 Deployed Application URLs:")
            for url in service_urls:
                print(f"  - {url}")
            
            # Display instructions for manual testing
            print("\n🧪 Manual Testing Instructions:")
            print("  1. The browser window should be open showing the application")
            print("  2. Try clicking each button to verify functionality")
            print("  3. The browser window will remain open for 60 seconds for testing")
            
            # Keep script running to maintain browser window
            print("\n⏳ Keeping browser window open for manual testing...")
            await asyncio.sleep(60)
            
            print("\n✅ Test completed - browser window will close now")
        
        # Print testing results
        testing_result = result.get("phases", {}).get("testing", {}).get("result", {})
        if testing_result:
            print("\n📷 Screenshots:")
            for screenshot in testing_result.get("screenshots", []):
                print(f"  - {screenshot}")
        
        return result.get("success", False)
        
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main entry point"""
    success = await test_automation_with_browser()
    return success

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
