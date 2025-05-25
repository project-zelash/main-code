#!/usr/bin/env python3
"""
End-to-end test of DirectPlaywrightTester with simple HTML project
This test validates that the browser testing works correctly
"""

import os
import sys
import time
import asyncio
from pathlib import Path

# Add the src directory to Python path
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

from utils.deployment_manager import DeploymentManager
from utils.automation_workflow import DirectPlaywrightTester

async def test_html_project_end_to_end():
    """Test the complete workflow with our simple HTML project"""
    print("=" * 60)
    print("🧪 TESTING DIRECTPLAYWRIGHTTESTER WITH SIMPLE HTML PROJECT")
    print("=" * 60)
    
    # Project path
    project_path = Path("automation_workspace/test_projects/simple_html_test")
    
    if not project_path.exists():
        print(f"❌ Project path does not exist: {project_path}")
        return False
    
    print(f"📁 Testing project: {project_path.absolute()}")
    
    # Initialize deployment manager
    deployment_manager = DeploymentManager()
    
    try:
        print("\n🚀 Step 1: Deploy the HTML project...")
        
        # Deploy the project (should serve the HTML file)
        deployment_result = deployment_manager.deploy_project(str(project_path))
        
        if not deployment_result.get("success"):
            print(f"❌ Deployment failed: {deployment_result.get('error', 'Unknown error')}")
            return False
            
        service_urls = deployment_result.get("service_urls", [])
        if not service_urls:
            print("❌ No service URLs returned from deployment")
            return False
            
        print(f"✅ Service deployed successfully at: {service_urls}")
        
        # Wait for the build/deployment to fully complete
        print("⏳ Waiting 20 seconds for build and deployment to fully complete...")
        print("   This ensures the service is completely ready before testing begins.")
        
        # Show countdown to indicate we're actually waiting
        for i in range(20, 0, -1):
            print(f"   ⏰ {i} seconds remaining...", end="\r")
            time.sleep(1)
        print("   ✅ Wait complete - proceeding with tests")
        
        print("\n🌐 Step 2: Test browser interaction...")
        
        # Initialize DirectPlaywrightTester
        tester = DirectPlaywrightTester(headless=True)
        
        # Test the service URLs using the correct API
        print(f"\n🎯 Testing URLs: {service_urls}")
        
        # Custom tests for our HTML application
        custom_tests = [
            "Click the Generate Quote button and verify a quote appears",
            "Test the calculator by entering numbers and clicking calculate",
            "Click the Blue button to change background color"
        ]
        
        test_result = await tester.test_application(service_urls, custom_tests)
        
        print("\n📊 Test Results:")
        print(f"✅ Success: {test_result.get('success', False)}")
        print(f"📈 Successful connections: {test_result.get('successful_connections', 0)}")
        print(f"❌ Failed connections: {test_result.get('failed_connections', 0)}")
        
        # Show detailed results
        for detail in test_result.get('detailed_results', []):
            url = detail.get('url', 'Unknown URL')
            success = detail.get('success', False)
            error = detail.get('error', 'No error')
            title = detail.get('page_title', 'No title')
            
            print(f"\n🔍 URL: {url}")
            print(f"   Status: {'✅ PASS' if success else '❌ FAIL'}")
            if not success:
                print(f"   Error: {error}")
            else:
                print(f"   Title: {title}")
                print(f"   Response time: {detail.get('response_time', 0):.2f}s")
        
        # Show screenshot info
        screenshots = test_result.get('screenshots', [])
        if screenshots:
            print(f"\n📸 Screenshots saved: {len(screenshots)}")
            for screenshot in screenshots:
                print(f"   {screenshot}")
        
        print("\n🧹 Step 3: Cleanup...")
        deployment_manager.cleanup()
        
        # Final results
        print("\n" + "=" * 60)
        if test_result.get('success') and test_result.get('successful_connections', 0) > 0:
            print("🎉 ALL TESTS PASSED! DirectPlaywrightTester is working correctly!")
            print("✅ Browser testing is functioning properly")
        else:
            print("❌ Some tests failed. Check the output above for details.")
        print("=" * 60)
        
        return test_result.get('success', False) and test_result.get('successful_connections', 0) > 0
        
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        
        # Ensure cleanup
        try:
            deployment_manager.cleanup()
        except:
            pass
            
        return False

def main():
    """Run the end-to-end test"""
    try:
        # Run the async test
        result = asyncio.run(test_html_project_end_to_end())
        
        if result:
            print("\n🎯 CONCLUSION: DirectPlaywrightTester is working perfectly!")
            print("Browser testing capabilities are fully functional.")
            sys.exit(0)
        else:
            print("\n❌ CONCLUSION: Tests failed. Further investigation needed.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()