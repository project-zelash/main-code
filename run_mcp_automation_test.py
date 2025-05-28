#!/usr/bin/env python3
"""
Enhanced automation pipeline test script with proper MCP server integration.
This script ensures:
1. MCP server is running before testing
2. Browser window stays open for interactive testing
3. Detailed test reports are generated
"""

import os
import sys
import asyncio
import time
import subprocess
import signal
from pathlib import Path
from dotenv import load_dotenv

# Add necessary paths
REPO_ROOT = Path(__file__).parent.absolute()

# Ensure proper import paths
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT / "web_ui"))
sys.path.insert(0, str(REPO_ROOT / "web_ui" / "src"))

# First load .env file to get API keys
load_dotenv()

# Import after setting up paths
from utils.automation_workflow import AutomationWorkflow
from web_ui.src.mcp_helpers.browser_helpers import run_browser_task, stop_browser_task, get_browser_logs

# Global variables to track subprocesses
mcp_server_process = None

async def start_mcp_server():
    """Start the MCP server as a separate process."""
    global mcp_server_process
    
    print("🚀 Starting MCP server...")
    
    # Set environment variables
    env = os.environ.copy()
    env["MCP_LLM_GOOGLE_API_KEY"] = os.getenv("GEMINI_API_KEY")
    env["MCP_LLM_PROVIDER"] = "google"
    env["MCP_LLM_MODEL_NAME"] = "gemini-2.0-flash"
    env["MCP_LLM_TEMPERATURE"] = "0.4"
    
    # Configure browser settings
    env["MCP_BROWSER_HEADLESS"] = "false"  # Ensure browser is visible
    env["MCP_BROWSER_WINDOW_WIDTH"] = "1280"
    env["MCP_BROWSER_WINDOW_HEIGHT"] = "720"
    env["MCP_BROWSER_DISABLE_SECURITY"] = "false"
    
    # Configure agent tool settings
    env["MCP_AGENT_TOOL_USE_VISION"] = "true"
    env["MCP_AGENT_TOOL_MAX_STEPS"] = "100"
    env["MCP_AGENT_TOOL_MAX_ACTIONS_PER_STEP"] = "5"
    env["MCP_AGENT_TOOL_TOOL_CALLING_METHOD"] = "auto"
    
    # Configure server settings
    env["MCP_SERVER_LOGGING_LEVEL"] = "INFO"
    env["MCP_SERVER_PORT"] = "8765"  # Default MCP port
    
    # Start the MCP server from the integrations directory
    mcp_path = REPO_ROOT / "integrations" / "mcp-browser-use"
    
    try:
        # Check if path exists
        if not mcp_path.exists():
            print(f"⚠️ MCP path not found at {mcp_path}")
            print("Trying alternative path...")
            mcp_path = REPO_ROOT / "integrations" / "browser-use"
            
            if not mcp_path.exists():
                raise FileNotFoundError(f"MCP server directory not found")
        
        # Start server process
        cmd = ["python", "-m", "mcp_server_browser_use.server"]
        
        # Check if the module exists in the expected location
        server_file = mcp_path / "src" / "mcp_server_browser_use" / "server.py"
        if server_file.exists():
            print(f"✅ Found MCP server at: {server_file}")
            server_dir = server_file.parent.parent
        else:
            # Try to find the server file in the repo
            print("⚠️ Server file not found in expected location, searching...")
            cmd = ["python", "webui.py", "--mcp"]
            server_dir = REPO_ROOT / "web_ui"
            
        print(f"🖥️ Starting MCP server with command: {cmd} in directory: {server_dir}")
        
        mcp_server_process = subprocess.Popen(
            cmd,
            cwd=str(server_dir),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        
        # Wait for server to start
        print("⏳ Waiting for MCP server to start...")
        await asyncio.sleep(5)
        
        # Check if server started successfully
        if mcp_server_process.poll() is not None:
            # Server exited prematurely
            stdout, stderr = mcp_server_process.communicate()
            print(f"❌ MCP server failed to start: {stderr}")
            return False
        
        print("✅ MCP server started successfully")
        return True
    
    except Exception as e:
        print(f"❌ Failed to start MCP server: {e}")
        return False

async def run_automation_with_mcp():
    """Run the complete automation pipeline with MCP integration."""
    
    # 1. Start MCP server
    server_started = await start_mcp_server()
    if not server_started:
        print("⚠️ Continuing without MCP server...")
    
    # 2. Initialize workflow
    print("🔄 Initializing AutomationWorkflow...")
    workflow = AutomationWorkflow(
        workspace_path="./automation_workspace", 
        headless_browser=False  # Ensure browser is visible
    )
    
    # 3. Define project prompt and test scenarios
    prompt = "Create an interactive HTML page with multiple buttons that each perform different actions: change colors, show alerts, toggle text visibility, and count clicks"
    test_scenarios = [
        "Test that all buttons are clearly visible on the page",
        "Test that the color change button works correctly",
        "Test that the alert button shows an alert message",
        "Test that the toggle text button shows and hides text",
        "Test that the counter button increments a number correctly"
    ]
    
    # 4. Run the workflow
    print(f"📋 Running automation workflow for task: {prompt}")
    result = await workflow.run_complete_workflow(
        prompt=prompt,
        prompt_method="custom",
        project_name="interactive-buttons-demo",
        custom_tests=test_scenarios
    )
    
    # 5. Extract and display the deployed URLs
    deployed_urls = []
    if result.get("phases", {}).get("deployment", {}).get("status") == "completed":
        deployed_urls = result.get("phases", {}).get("deployment", {}).get("result", {}).get("service_urls", [])
        
        if deployed_urls:
            print("\n" + "=" * 60)
            print("🌐 DEPLOYED APPLICATIONS")
            print("=" * 60)
            for i, url in enumerate(deployed_urls):
                print(f"{i+1}. {url}")
    
    # 6. Run interactive browser testing with MCP
    if deployed_urls and server_started:
        print("\n" + "=" * 60)
        print("🧪 STARTING INTERACTIVE BROWSER TESTING")
        print("=" * 60)
        
        test_url = deployed_urls[0]  # Use first URL
        print(f"Testing URL: {test_url}")
        
        # Use MCP browser helpers to run interactive tests
        task_description = f"""
        Navigate to {test_url} and perform the following tests:
        1. Verify all buttons are visible
        2. Click each button and observe its behavior
        3. For the counter button, click it multiple times and verify the count increases
        4. For the color change button, verify the colors change
        5. For the alert button, verify an alert appears
        """
        
        task_id = run_browser_task(task_description, headless=False, use_vision=True)
        print(f"🔍 Interactive testing started with task ID: {task_id}")
        print("✨ Browser window should remain open for interactive testing")
        print("⏳ Interactive testing will continue for 2 minutes...")
        
        # Wait for interactive testing (keeping browser open)
        for i in range(12):
            print(f"⏳ Test in progress... {i*10}/120 seconds")
            await asyncio.sleep(10)
            
            # Get and display logs
            logs = get_browser_logs()
            if logs and len(logs) > 0:
                print(f"📝 Latest log: {logs[-1].get('content', 'No content')[:100]}...")
        
        # 7. Stop browser task
        print("🛑 Stopping interactive testing...")
        stop_browser_task()
    
    # 8. Print comprehensive summary
    print("\n" + "=" * 60)
    print("📊 AUTOMATION WORKFLOW SUMMARY")
    print("=" * 60)
    
    # Show overall status
    workflow_status = result.get("status", "unknown")
    print(f"Workflow Status: {'✅ SUCCESS' if workflow_status == 'completed' else '❌ FAILED'}")
    
    # Show details for each phase
    for phase, data in result.get("phases", {}).items():
        phase_status = data.get("status", "unknown")
        print(f"\n{phase.upper()} Phase: {'✅ SUCCESS' if phase_status == 'completed' else '❌ FAILED'}")
        
        # Show specific details for each phase
        if phase == "testing" and phase_status == "completed":
            test_results = data.get("result", {})
            print(f"  Tests Run: {test_results.get('tested_urls', [])}")
            print(f"  Screenshots: {test_results.get('screenshots', [])}")
            
            # Show test details
            detailed_results = test_results.get("detailed_results", [])
            if detailed_results:
                print("  Test Details:")
                for i, test in enumerate(detailed_results):
                    print(f"    Test {i+1}: {test.get('url')}")
                    print(f"      Success: {'✅' if test.get('success') else '❌'}")
                    print(f"      Page Title: {test.get('page_title')}")
                    print(f"      Screenshot: {test.get('screenshot_path')}")
    
    return workflow_status == "completed"

def cleanup():
    """Cleanup all processes."""
    global mcp_server_process
    
    print("🧹 Cleaning up processes...")
    
    # Stop MCP server
    if mcp_server_process:
        try:
            mcp_server_process.terminate()
            time.sleep(1)
            if mcp_server_process.poll() is None:
                mcp_server_process.kill()
            print("✅ MCP server stopped")
        except Exception as e:
            print(f"⚠️ Error stopping MCP server: {e}")

async def main():
    """Main entry point."""
    try:
        print("🚀 Starting enhanced automation pipeline test with MCP integration...")
        
        # Run the enhanced automation workflow
        success = await run_automation_with_mcp()
        
        # Always perform cleanup before exiting
        cleanup()
        
        print(f"\n{'✅ Test completed successfully!' if success else '❌ Test completed with issues.'}")
        return success
    
    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted by user")
        cleanup()
        return False
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        cleanup()
        return False

if __name__ == "__main__":
    # Handle proper cleanup on exit signals
    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, lambda _sig, _frame: cleanup())
        
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
