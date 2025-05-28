#!/usr/bin/env python3
"""
Fixed browser integration test for automation pipeline.
This script properly configures the paths and dependencies to run the automation workflow
with browser testing that stays open for proper interaction.
"""

import os
import sys
import asyncio
import time
import subprocess
import signal
from pathlib import Path
from dotenv import load_dotenv

# Add src directory to Python path correctly
current_dir = Path(__file__).parent.absolute()
sys.path.append(str(current_dir / "src"))

# Load environment variables first
load_dotenv()

# Global variables
deployed_urls = []
test_completed = False

async def run_automation_test():
    """Run the complete automation workflow with browser integration."""
    try:
        # Import after setting paths
        from src.utils.automation_workflow import AutomationWorkflow
        
        print("🚀 Initializing AutomationWorkflow...")
        workspace_path = current_dir / "automation_workspace"
        
        # Create workflow with headless_browser set to False to keep window open
        # and a longer testing timeout
        workflow = AutomationWorkflow(
            workspace_path=str(workspace_path), 
            headless_browser=False
        )
        
        # Create a more complex HTML task with multiple interactive buttons
        task = """
        Create an interactive HTML page with the following features:
        1. A button that shows an alert message when clicked
        2. A button that changes the background color of the page (cycling through multiple colors)
        3. A counter button that displays how many times it has been clicked
        4. A button that toggles the visibility of an image or text element
        
        Make sure each button is clearly labeled and has distinctive styling.
        Add visual feedback for each button interaction.
        Ensure the page has a clean, modern design.
        """
        
        # Define specific test scenarios that will be executed by the browser automation
        test_scenarios = [
            "Verify that all buttons are visible and have clear labels",
            "Click the alert button and verify an alert appears with the expected message",
            "Click the color change button multiple times and verify the background color changes",
            "Click the counter button several times and verify the count increases correctly",
            "Click the toggle button and verify an element appears/disappears"
        ]
        
        print(f"📋 Running automation workflow for task: {task}")
        
        # IMPORTANT: Override the default DirectPlaywrightTester to make it keep the browser open longer
        from src.utils.automation_workflow import DirectPlaywrightTester
        
        # Monkey patch the test_application method to keep browser open longer
        original_test_application = DirectPlaywrightTester.test_application
        
        async def patched_test_application(self, service_urls, custom_tests=None):
            print("\n🔄 Using modified test_application method with extended browser session\n")
            result = await original_test_application(self, service_urls, custom_tests)
            
            # Store deployed URLs globally for reference
            global deployed_urls
            deployed_urls = service_urls
            
            # After completing tests, keep browser open for extended interaction
            print("\n✨ EXTENDED BROWSER SESSION - Browser will remain open for 5 minutes")
            print("⭐ You can interact with the application manually during this time")
            print("⭐ This window will remain active while the browser is open")
            print("⭐ The deployed application is available at: " + (service_urls[0] if service_urls else "No URL available"))
            
            # NOTE: For a real production system, you would integrate with the MCP browser
            # helpers here. For this test, we're just keeping the Playwright window open.
            
            # Keep script running to maintain browser window
            try:
                # Wait for user interaction time
                for i in range(30):  # 5 minutes total (30 * 10 seconds)
                    remaining = 300 - (i * 10)
                    print(f"⏳ Browser session active: {remaining} seconds remaining", end="\\r")
                    await asyncio.sleep(10)
            except asyncio.CancelledError:
                print("\n🛑 Browser session terminated early")
                
            # Mark test as completed
            global test_completed
            test_completed = True
            
            print("\n✅ Extended browser session completed")
            return result
        
        # Apply the monkey patch
        DirectPlaywrightTester.test_application = patched_test_application
        
        # Run the complete workflow with our patched test method
        result = await workflow.run_complete_workflow(
            prompt=task,
            prompt_method="custom",
            project_name="interactive-browser-session",
            custom_tests=test_scenarios
        )
        
        print("\n" + "=" * 60)
        print("📊 AUTOMATION WORKFLOW SUMMARY")
        print("=" * 60)
        
        # Print workflow status
        status = result.get("status")
        print(f"Workflow Status: {'✅ SUCCESS' if status == 'completed' else '❌ FAILED'}")
        
        # Print results for each phase
        for phase, data in result.get("phases", {}).items():
            phase_status = data.get("status")
            print(f"\n{phase.upper()} Phase: {'✅ SUCCESS' if phase_status == 'completed' else '❌ FAILED'}")
            
            # Show details for deployment phase
            if phase == "deployment" and phase_status == "completed":
                deployment_result = data.get("result", {})
                service_urls = deployment_result.get("service_urls", [])
                if service_urls:
                    print("  Deployed URLs:")
                    for url in service_urls:
                        print(f"  - {url}")
            
            # Show details for testing phase
            elif phase == "testing" and phase_status == "completed":
                test_result = data.get("result", {})
                print(f"  Tests Run: {len(test_result.get('detailed_results', []))}")
                print(f"  Screenshots: {len(test_result.get('screenshots', []))}")
                
                # Show individual test results
                for i, test in enumerate(test_result.get("detailed_results", [])):
                    success = test.get("success", False)
                    print(f"  Test {i+1}: {'✅ SUCCESS' if success else '❌ FAILED'} - {test.get('url', 'N/A')}")
        
        # Return success status
        return status == "completed"
    
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main entry point"""
    try:
        # Set up signal handlers for graceful termination
        def signal_handler(sig, frame):
            print("\n⏹️ Test interrupted by user")
            sys.exit(1)
        
        for sig in (signal.SIGINT, signal.SIGTERM):
            signal.signal(sig, signal_handler)
        
        # Run the test
        success = await run_automation_test()
        
        # Check if the test was completed
        if not test_completed:
            print("⚠️ Test did not reach completion, browser session may not have opened correctly")
        
        return success
    
    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted by user")
        return False
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        return False

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
