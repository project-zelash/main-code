#!/usr/bin/env python3
"""
Simple test for the automation pipeline with a minimal example
"""

import os
import sys
import asyncio
import json
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file first thing
load_dotenv()

# Add the src directory to the Python path
sys.path.append(str(Path(__file__).parent / "src"))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_simple_workflow():
    """Test the automation workflow with a simple HTML page."""
    try:
        from utils.automation_workflow import AutomationWorkflow
        
        print("🚀 Initializing AutomationWorkflow...")
        workspace_path = Path("./test_workspace")
        workflow = AutomationWorkflow(workspace_path=str(workspace_path), headless_browser=False)
        
        # Simple task: Create a basic HTML page with a button
        task = "Create a simple HTML page with a button that shows an alert when clicked"
        
        print(f"📋 Running automation workflow for task: {task}")
        # Properly await the async function
        result = await workflow.run_complete_workflow(
            prompt=task,
            prompt_method="custom",
            project_name="simple-html-test"
        )
        
        print("\n" + "=" * 60)
        print("📊 WORKFLOW RESULT SUMMARY")
        print("=" * 60)
        
        if result.get("success", False):
            print("✅ Workflow completed successfully!")
        else:
            print("❌ Workflow failed!")
            
        # Print detailed results
        print("\n📋 Detailed Results:")
        print(json.dumps(result, indent=2))
        
        return result.get("success", False)
        
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run the simple workflow test."""
    success = await test_simple_workflow()
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
