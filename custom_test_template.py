#!/usr/bin/env python3
"""
Custom Test Case Template
Copy this file and modify for your specific test needs.
"""

import os
import sys
import json
import time
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from utils.automation_workflow import AutomationWorkflow

class MyCustomTest:
    """Your custom test class."""
    
    def __init__(self):
        self.workflow = AutomationWorkflow()
        self.results = []
    
    def test_my_project(self):
        """Test case 1: Your specific project."""
        
        print("🧪 Running Custom Test Case 1")
        
        # Define your project requirements
        prompt = """
        Create a modern e-commerce product page with:
        1. Product image gallery with zoom functionality
        2. Add to cart button with quantity selector
        3. Product details tabs (Description, Reviews, Specifications)
        4. Related products section
        5. Responsive design for mobile/desktop
        6. Clean, professional styling
        """
        
        # Run the workflow
        result = self.workflow.run_complete_workflow(
            prompt=prompt,
            project_name="ecommerce_product_page",
            skip_deployment=False,  # Set True to skip deployment
            skip_testing=False      # Set True to skip browser testing
        )
        
        # Evaluate results
        success = result["status"] == "completed"
        
        if success:
            print("✅ Test Case 1 PASSED")
            project_path = result["phases"]["generation"]["result"]["project_path"]
            service_url = result["phases"]["deployment"]["result"].get("service_url", "N/A")
            print(f"📁 Project: {project_path}")
            print(f"🌐 URL: {service_url}")
        else:
            print("❌ Test Case 1 FAILED")
            print(f"Error: {result.get('error')}")
        
        self.results.append({
            "test_name": "ecommerce_product_page",
            "success": success,
            "result": result
        })
        
        return result
    
    def test_batch_projects(self):
        """Test case 2: Multiple projects in batch."""
        
        print("🧪 Running Batch Test Case")
        
        # Define multiple test projects
        test_prompts = [
            "Create a simple weather app that shows current weather",
            "Build a basic task management app with add/delete functionality", 
            "Create a portfolio landing page with contact form"
        ]
        
        # Run batch workflow
        batch_results = self.workflow.run_batch_workflows(
            prompts=test_prompts,
            project_names=["weather_app", "task_manager", "portfolio_site"]
        )
        
        # Evaluate batch results
        successful = sum(1 for r in batch_results if r["status"] == "completed")
        total = len(batch_results)
        
        print(f"📊 Batch Results: {successful}/{total} successful")
        
        self.results.append({
            "test_name": "batch_test",
            "success": successful == total,
            "results": batch_results
        })
        
        return batch_results
    
    def test_specific_framework(self):
        """Test case 3: Framework-specific test."""
        
        print("🧪 Running Framework-Specific Test")
        
        # Test React specifically
        prompt = """
        Create a React dashboard with:
        - Navigation sidebar
        - Multiple chart components (bar, line, pie)
        - Data table with filtering
        - Dark/light theme toggle
        - Responsive layout
        """
        
        result = self.workflow.run_complete_workflow(
            prompt=prompt,
            project_name="react_dashboard",
            force_project_type="react"  # Force React framework
        )
        
        success = result["status"] == "completed"
        print(f"React Test: {'✅ PASSED' if success else '❌ FAILED'}")
        
        self.results.append({
            "test_name": "react_dashboard",
            "success": success,
            "result": result
        })
        
        return result
    
    def run_all_tests(self):
        """Run all test cases."""
        
        print("🚀 Starting Custom Test Suite")
        print("=" * 60)
        
        # Set your API key
        if not os.getenv("GEMINI_API_KEY"):
            print("❌ Error: Please set GEMINI_API_KEY environment variable")
            return False
        
        try:
            # Run individual tests
            self.test_my_project()
            self.test_batch_projects()
            self.test_specific_framework()
            
            # Generate summary
            self.generate_summary()
            
            # Return overall success
            return all(r["success"] for r in self.results)
            
        except Exception as e:
            print(f"❌ Test suite failed: {e}")
            return False
    
    def generate_summary(self):
        """Generate test summary report."""
        
        print("\n" + "=" * 60)
        print("📊 CUSTOM TEST SUITE SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for r in self.results if r["success"])
        total = len(self.results)
        
        print(f"Overall Result: {'✅ PASS' if passed == total else '❌ FAIL'}")
        print(f"Tests Passed: {passed}/{total}")
        
        for result in self.results:
            status = "✅ PASS" if result["success"] else "❌ FAIL"
            print(f"  {result['test_name']}: {status}")
        
        # Save detailed results
        timestamp = int(time.time())
        report_file = f"custom_test_report_{timestamp}.json"
        
        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        print(f"\n💾 Detailed report saved: {report_file}")

def main():
    """Main entry point."""
    
    # Create and run custom tests
    test_suite = MyCustomTest()
    success = test_suite.run_all_tests()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
