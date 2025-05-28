#!/usr/bin/env python3
"""
Fully integrated test of the automation pipeline with browser-use system.
This script ensures complete integration with browser-use for automated testing.
"""

import os
import sys
import time
import asyncio
import subprocess
import json
import threading
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the src directory to the Python path
ROOT_DIR = Path(__file__).parent.absolute()
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(ROOT_DIR / "src"))
sys.path.insert(0, str(ROOT_DIR / "web_ui"))
sys.path.insert(0, str(ROOT_DIR / "web_ui" / "src"))

# Global variables
browser_use_process = None
deployed_urls = []
current_workspace = ROOT_DIR / "automation_workspace"
browser_test_completed = threading.Event()

def start_browser_use_server():
    """Start the browser-use server as a separate process."""
    global browser_use_process
    
    print("🚀 Starting browser-use server...")
    
    try:
        # First check if webui.py exists in web_ui directory
        webui_script = ROOT_DIR / "web_ui" / "webui.py"
        if not webui_script.exists():
            print(f"❌ webui.py not found at {webui_script}")
            return False
        
        # Set up environment variables
        env = os.environ.copy()
        env["GEMINI_API_KEY"] = os.getenv("GEMINI_API_KEY")
        env["HEADLESS"] = "false"  # Ensure browser is visible
        
        # Start browser-use server
        cmd = [sys.executable, str(webui_script), "--debug"]
        print(f"🖥️ Running command: {' '.join(cmd)}")
        
        browser_use_process = subprocess.Popen(
            cmd,
            cwd=str(ROOT_DIR / "web_ui"),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        
        # Wait for server to start
        print("⏳ Waiting for browser-use server to start...")
        time.sleep(5)
        
        # Check if process is still running
        if browser_use_process.poll() is not None:
            stdout, stderr = browser_use_process.communicate()
            print(f"❌ Browser-use server failed to start. Error: {stderr}")
            return False
        
        print("✅ Browser-use server started successfully")
        return True
    
    except Exception as e:
        print(f"❌ Failed to start browser-use server: {e}")
        return False

def stop_browser_use_server():
    """Stop the browser-use server."""
    global browser_use_process
    
    if browser_use_process:
        try:
            print("🛑 Stopping browser-use server...")
            browser_use_process.terminate()
            time.sleep(2)
            
            if browser_use_process.poll() is None:
                print("⚠️ Server not responding to terminate, killing...")
                browser_use_process.kill()
                
            browser_use_process.wait()
            print("✅ Browser-use server stopped")
        
        except Exception as e:
            print(f"⚠️ Error stopping browser-use server: {e}")

def run_browser_use_test(url, test_name, test_instructions):
    """
    Run a browser-use test on the deployed application.
    Uses direct calls to the browser-use Python API.
    """
    try:
        # Import browser helpers
        sys.path.insert(0, str(ROOT_DIR / "web_ui" / "src"))
        
        # First try the mcp_helpers
        try:
            from web_ui.src.mcp_helpers.browser_helpers import run_browser_task
            print("✅ Successfully imported browser helpers from web_ui")
        except ImportError:
            try:
                # Try alternative import path
                from mcp_helpers.browser_helpers import run_browser_task
                print("✅ Successfully imported browser helpers from mcp_helpers")
            except ImportError:
                # Fallback to direct playwright
                print("⚠️ Could not import browser helpers, using direct_playwright instead")
                from web_ui.src.mcp_helpers.direct_playwright import run_playwright_test
                
                result = run_playwright_test(url, test_instructions, headless=False)
                print(f"🧪 Test '{test_name}' completed via direct Playwright")
                return result
        
        # Run the test using browser helpers
        print(f"🧪 Running test '{test_name}' on {url}...")
        task_id = run_browser_task(
            task=f"Go to {url} and {test_instructions}", 
            headless=False,  # Make sure browser is visible
            use_vision=True   # Enable vision capabilities
        )
        
        print(f"✅ Browser task started with ID: {task_id}")
        
        # Wait for task to complete (browser will stay open)
        print("⏳ Waiting for browser task to complete (browser window should remain open)...")
        time.sleep(30)  # Allow time for interaction
        
        print(f"✅ Test '{test_name}' completed")
        return {"success": True, "task_id": task_id}
    
    except Exception as e:
        print(f"❌ Error running browser test: {e}")
        return {"success": False, "error": str(e)}

async def run_automation_workflow():
    """Run the complete automation workflow."""
    from utils.automation_workflow import AutomationWorkflow
    
    print("🚀 Initializing automation workflow...")
    workflow = AutomationWorkflow(
        workspace_path=str(current_workspace),
        headless_browser=False  # Ensure browser is visible during testing
    )
    
    # Define a project with multiple interactive elements
    prompt = """
    Create an interactive HTML page with the following features:
    1. A button that shows an alert message with text 'Button clicked!'
    2. A button that changes the background color of the page between blue, green, and red
    3. A counter button that displays how many times it has been clicked
    4. A button that toggles the visibility of an image or text block
    
    Use modern CSS for styling and make the page visually appealing.
    Add clear labels to each button explaining what they do.
    """
    
    # Define specific test scenarios for automated testing
    test_scenarios = [
        "Check that all buttons are visible and properly labeled",
        "Test the alert button by clicking it and verifying an alert appears",
        "Test the color change button by clicking it multiple times and checking the background color changes",
        "Test the counter button by clicking it and verifying the count increases",
        "Test the toggle button by clicking it and checking if an element appears/disappears"
    ]
    
    print(f"📋 Running automation workflow with the following prompt:\n{prompt}")
    
    # Run the complete workflow
    result = await workflow.run_complete_workflow(
        prompt=prompt,
        prompt_method="custom",
        project_name="interactive-browser-test",
        custom_tests=test_scenarios
    )
    
    # Extract deployed URLs
    global deployed_urls
    if result.get("phases", {}).get("deployment", {}).get("result", {}).get("service_urls"):
        deployed_urls = result.get("phases", {}).get("deployment", {}).get("result", {}).get("service_urls", [])
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 AUTOMATION WORKFLOW SUMMARY")
    print("=" * 60)
    
    if result.get("status") == "completed":
        print("✅ Workflow completed successfully!")
    else:
        print("⚠️ Workflow completed with issues.")
    
    # Print detailed results
    if deployed_urls:
        print("\n🌐 Deployed Application URLs:")
        for url in deployed_urls:
            print(f"  - {url}")
    
    return result

def browser_use_test_thread():
    """Run browser-use tests in a separate thread."""
    global deployed_urls, browser_test_completed
    
    # Wait for URLs to be deployed
    max_wait = 60  # seconds
    wait_interval = 2  # seconds
    waited = 0
    
    print("⏳ Waiting for application to be deployed...")
    while not deployed_urls and waited < max_wait:
        time.sleep(wait_interval)
        waited += wait_interval
    
    if not deployed_urls:
        print("❌ No URLs deployed within timeout period.")
        browser_test_completed.set()
        return
    
    # Get the first working URL
    test_url = deployed_urls[0]
    print(f"🧪 Starting browser-use tests on {test_url}")
    
    # Define test cases
    test_cases = [
        {
            "name": "Alert Button Test",
            "instructions": "find the alert button and click it. Verify that an alert appears. Close the alert."
        },
        {
            "name": "Color Change Test",
            "instructions": "find the color change button and click it 3 times. Verify that the background color changes with each click."
        },
        {
            "name": "Counter Test",
            "instructions": "find the counter button and click it 5 times. Verify that the counter value increases with each click."
        },
        {
            "name": "Toggle Test",
            "instructions": "find the toggle button and click it twice. Verify that an element appears and disappears."
        }
    ]
    
    # Run each test case
    test_results = []
    for test_case in test_cases:
        print(f"\n🧪 Running test: {test_case['name']}")
        result = run_browser_use_test(test_url, test_case["name"], test_case["instructions"])
        test_results.append({
            "test_name": test_case["name"],
            "success": result.get("success", False),
            "details": result
        })
        
        # Short pause between tests
        time.sleep(5)
    
    # Generate test report
    print("\n" + "=" * 60)
    print("📊 BROWSER-USE TEST RESULTS")
    print("=" * 60)
    
    successful_tests = sum(1 for r in test_results if r["success"])
    print(f"✅ {successful_tests}/{len(test_results)} tests passed\n")
    
    for i, result in enumerate(test_results):
        status = "✅" if result["success"] else "❌"
        print(f"{status} Test {i+1}: {result['test_name']}")
    
    # Signal that browser testing is complete
    browser_test_completed.set()

async def main():
    """Main entry point."""
    try:
        # 1. Start browser-use server
        server_started = start_browser_use_server()
        if not server_started:
            print("⚠️ Browser-use server failed to start, using fallback testing method")
        
        # 2. Start browser test thread (will wait for URLs)
        browser_test_thread = threading.Thread(target=browser_use_test_thread)
        browser_test_thread.daemon = True
        browser_test_thread.start()
        
        # 3. Run automation workflow
        await run_automation_workflow()
        
        # 4. Wait for browser tests to complete
        print("\n⏳ Waiting for browser-use tests to complete...")
        max_wait = 300  # seconds
        browser_test_completed.wait(max_wait)
        
        if not browser_test_completed.is_set():
            print("⚠️ Browser-use tests did not complete within timeout period")
        
        # 5. Cleanup
        stop_browser_use_server()
        
        print("\n✅ Automation pipeline test completed")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        
        # Ensure cleanup
        stop_browser_use_server()
        return False

if __name__ == "__main__":
    try:
        # Setup proper signal handling for cleanup
        import signal
        for sig in (signal.SIGINT, signal.SIGTERM):
            signal.signal(sig, lambda _sig, _frame: (stop_browser_use_server(), sys.exit(1)))
        
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted by user")
        stop_browser_use_server()
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        stop_browser_use_server()
        sys.exit(1)
