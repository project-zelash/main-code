#!/usr/bin/env python3
"""
Main entry point for the Complete Automation Workflow System.

This script provides an easy-to-use interface for the Generate → Deploy → Test → Report pipeline.

Usage:
    python automation_main.py --help
    python automation_main.py generate-deploy-test --prompt "Create a React todo app"
    python automation_main.py batch-workflow --config batch_config.json
    python automation_main.py list-workflows
    python automation_main.py cleanup --workflow-id abc123
"""

import argparse
import asyncio
import json
import sys
import os
from pathlib import Path
from typing import Dict, List, Optional

# Add the src directory to the Python path
sys.path.append(str(Path(__file__).parent / "src"))

from utils.automation_workflow import AutomationWorkflow
from utils.project_generator import ProjectGenerator
from utils.deployment_manager import DeploymentManager
from utils.browser_testing_manager import BrowserTestingManager


class AutomationCLI:
    """Command-line interface for the automation workflow system."""
    
    def __init__(self):
        self.workflow = None
        self._initialize_workflow()
    
    def _initialize_workflow(self):
        """Initialize the automation workflow."""
        try:
            self.workflow = AutomationWorkflow()
            print("✅ Automation workflow system initialized successfully")
        except Exception as e:
            print(f"❌ Failed to initialize automation workflow: {e}")
            sys.exit(1)
    
    def generate_deploy_test(self, prompt: str, project_type: Optional[str] = None, 
                                 test_scenarios: Optional[List[str]] = None) -> Dict:
        """Run the complete generate → deploy → test pipeline."""
        print(f"🚀 Starting complete automation pipeline for: {prompt}")
        
        try:
            result = self.workflow.run_complete_workflow(
                prompt=prompt,
                force_project_type=project_type,
                custom_tests=test_scenarios or []
            )
            
            # Print summary
            print("\n" + "="*60)
            print("📊 AUTOMATION WORKFLOW SUMMARY")
            print("="*60)
            print(f"Status: {'✅ SUCCESS' if result['success'] else '❌ FAILED'}")
            print(f"Workflow ID: {result['workflow_id']}")
            print(f"Generated Project: {result.get('project_path', 'N/A')}")
            print(f"Deployment URL: {result.get('deployment_url', 'N/A')}")
            print(f"Test Results: {result.get('test_summary', {}).get('total_tests', 0)} tests")
            
            if result.get('test_summary'):
                test_summary = result['test_summary']
                print(f"  - Passed: {test_summary.get('passed', 0)}")
                print(f"  - Failed: {test_summary.get('failed', 0)}")
                print(f"  - Score: {test_summary.get('overall_score', 0):.1f}%")
            
            print(f"Report Location: {result.get('report_path', 'N/A')}")
            print("="*60)
            
            return result
            
        except Exception as e:
            print(f"❌ Workflow failed: {e}")
            return {"success": False, "error": str(e)}
    
    def batch_workflow(self, config_path: str) -> List[Dict]:
        """Run batch workflows from configuration file."""
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            print(f"🔄 Starting batch workflow with {len(config.get('workflows', []))} items")
            
            results = self.workflow.run_batch_workflows(config['workflows'])
            
            # Print batch summary
            print("\n" + "="*60)
            print("📊 BATCH WORKFLOW SUMMARY")
            print("="*60)
            successful = sum(1 for r in results if r.get('success', False))
            print(f"Total Workflows: {len(results)}")
            print(f"Successful: {successful}")
            print(f"Failed: {len(results) - successful}")
            print("="*60)
            
            return results
            
        except Exception as e:
            print(f"❌ Batch workflow failed: {e}")
            return []
    
    def list_workflows(self) -> None:
        """List all workflow history."""
        try:
            history = self.workflow.get_workflow_history()
            
            if not history:
                print("📋 No workflows found in history")
                return
            
            print(f"📋 Found {len(history)} workflows in history")
            print("\n" + "="*60)
            
            for workflow in history:
                print(f"ID: {workflow['workflow_id']}")
                print(f"Prompt: {workflow['prompt'][:50]}...")
                print(f"Status: {'✅ SUCCESS' if workflow['success'] else '❌ FAILED'}")
                print(f"Created: {workflow['timestamp']}")
                if workflow.get('deployment_url'):
                    print(f"URL: {workflow['deployment_url']}")
                print("-" * 40)
                
        except Exception as e:
            print(f"❌ Failed to list workflows: {e}")
    
    def cleanup_workflow(self, workflow_id: str) -> None:
        """Clean up a specific workflow."""
        try:
            success = self.workflow.cleanup_workflow(workflow_id)
            if success:
                print(f"✅ Successfully cleaned up workflow: {workflow_id}")
            else:
                print(f"❌ Failed to cleanup workflow: {workflow_id}")
        except Exception as e:
            print(f"❌ Cleanup failed: {e}")
    
    def cleanup_all(self) -> None:
        """Clean up all workflows."""
        try:
            count = self.workflow.cleanup_all_workflows()
            print(f"✅ Successfully cleaned up {count} workflows")
        except Exception as e:
            print(f"❌ Cleanup all failed: {e}")
    
    def create_example_config(self, output_path: str = "batch_config.json") -> None:
        """Create an example batch configuration file."""
        example_config = {
            "workflows": [
                {
                    "prompt": "Create a React todo app with TypeScript",
                    "project_type": "react",
                    "test_scenarios": [
                        "Test adding a new todo item",
                        "Test marking todo as complete",
                        "Test deleting a todo item"
                    ]
                },
                {
                    "prompt": "Create a simple Python Flask API for user management",
                    "project_type": "flask",
                    "test_scenarios": [
                        "Test API endpoints are accessible",
                        "Test user creation endpoint",
                        "Test user listing endpoint"
                    ]
                },
                {
                    "prompt": "Create a Next.js landing page with dark mode",
                    "project_type": "nextjs",
                    "test_scenarios": [
                        "Test page loads correctly",
                        "Test dark mode toggle",
                        "Test responsive design"
                    ]
                }
            ]
        }
        
        with open(output_path, 'w') as f:
            json.dump(example_config, f, indent=2)
        
        print(f"✅ Created example batch configuration: {output_path}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Complete Automation Workflow System - Generate → Deploy → Test → Report",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Generate-Deploy-Test command
    gen_parser = subparsers.add_parser(
        'generate-deploy-test', 
        help='Run complete workflow for a single project'
    )
    gen_parser.add_argument('--prompt', required=True, help='Project generation prompt')
    gen_parser.add_argument('--project-type', help='Specific project type (optional)')
    gen_parser.add_argument(
        '--test-scenarios', 
        nargs='*', 
        help='Custom test scenarios'
    )
    
    # Batch workflow command
    batch_parser = subparsers.add_parser(
        'batch-workflow', 
        help='Run batch workflows from configuration file'
    )
    batch_parser.add_argument('--config', required=True, help='Path to batch configuration JSON file')
    
    # List workflows command
    subparsers.add_parser('list-workflows', help='List all workflow history')
    
    # Cleanup commands
    cleanup_parser = subparsers.add_parser('cleanup', help='Clean up workflows')
    cleanup_parser.add_argument('--workflow-id', help='Specific workflow ID to clean up')
    cleanup_parser.add_argument('--all', action='store_true', help='Clean up all workflows')
    
    # Create example config
    config_parser = subparsers.add_parser(
        'create-example-config', 
        help='Create example batch configuration file'
    )
    config_parser.add_argument(
        '--output', 
        default='batch_config.json', 
        help='Output path for example config'
    )
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Initialize CLI
    cli = AutomationCLI()
    
    # Handle commands
    if args.command == 'generate-deploy-test':
        result = cli.generate_deploy_test(
            prompt=args.prompt,
            project_type=args.project_type,
            test_scenarios=args.test_scenarios
        )
        sys.exit(0 if result.get('success') else 1)
    
    elif args.command == 'batch-workflow':
        results = cli.batch_workflow(args.config)
        successful = sum(1 for r in results if r.get('success'))
        sys.exit(0 if successful == len(results) else 1)
    
    elif args.command == 'list-workflows':
        cli.list_workflows()
    
    elif args.command == 'cleanup':
        if args.all:
            cli.cleanup_all()
        elif args.workflow_id:
            cli.cleanup_workflow(args.workflow_id)
        else:
            print("❌ Please specify either --workflow-id or --all")
            sys.exit(1)
    
    elif args.command == 'create-example-config':
        cli.create_example_config(args.output)


if __name__ == "__main__":
    main()
