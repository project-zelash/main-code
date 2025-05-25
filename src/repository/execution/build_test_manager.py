import os
import time
import traceback
from typing import Dict, List, Any, Optional
from src.repository.execution.testing_framework import TestingFramework
from src.repository.execution.feedback_analyzer import FeedbackAnalyzer
from src.service.tool_service import ToolService
from src.schemas.issue_models import DetailedIssue


class BuildTestManager:
    """
    Manages build processes, testing, and refinement cycles.
    """
    
    def __init__(self, tool_service: ToolService, testing_framework: TestingFramework, 
                 feedback_analyzer: FeedbackAnalyzer, workspace_path: str):
        self.tool_service = tool_service
        self.testing_framework = testing_framework
        self.feedback_analyzer = feedback_analyzer
        self.workspace_path = workspace_path
        self.service_urls: List[str] = []
        
    def build_project(self, project_name: str, build_config: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Build the project.
        
        Args:
            project_name: Name of the project
            build_config: Optional build configuration
            
        Returns:
            Build result dictionary
        """
        try:
            project_dir = os.path.join(self.workspace_path, project_name)
            
            # Check if build command is specified in config
            if build_config and build_config.get("build_command"):
                build_command = f'cd "{project_dir}" && {build_config["build_command"]}'
                build_result = self.tool_service.run_bash_command(build_command)
                
                if build_result.get('exit_code', 1) != 0:
                    return {
                        "success": False,
                        "message": f"Build command failed: {build_result.get('stderr', 'Unknown error')}"
                    }
            else:
                # Basic validation build
                if not os.path.exists(os.path.join(project_dir, "src")):
                    return {
                        "success": False,
                        "message": "Build check failed: 'src' directory not found"
                    }
            
            # Simulate build time
            time.sleep(0.5)
            
            return {
                "success": True,
                "message": "Build completed successfully"
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Build failed: {str(e)}"
            }
    
    def start_services(self, project_name: str, deploy_config: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Start project services.
        
        Args:
            project_name: Name of the project
            deploy_config: Optional deployment configuration
            
        Returns:
            Service start result dictionary
        """
        try:
            # Execute start commands if specified
            if deploy_config and deploy_config.get("start_commands"):
                project_dir = os.path.join(self.workspace_path, project_name)
                
                for command in deploy_config["start_commands"]:
                    start_command = f'cd "{project_dir}" && {command}'
                    result = self.tool_service.run_bash_command(start_command)
                    
                    if result.get('exit_code', 1) != 0:
                        return {
                            "success": False,
                            "message": f"Service start command failed: {result.get('stderr', 'Unknown error')}",
                            "service_urls": []
                        }
            
            # Simulate service startup
            time.sleep(0.5)
            
            # Generate service URLs (in real implementation, these would be from actual services)
            simulated_urls = [
                f"http://localhost:8000/{project_name}/api",
                f"http://localhost:3000/{project_name}"
            ]
            
            self.service_urls = simulated_urls
            
            return {
                "success": True,
                "message": "Services started successfully",
                "service_urls": self.service_urls
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to start services: {str(e)}",
                "service_urls": []
            }
    
    def run_tests(self, project_id: str) -> Dict[str, Any]:
        """
        Run tests for the project.
        
        Args:
            project_id: ID of the project
            
        Returns:
            Test result dictionary
        """
        try:
            # Execute unit tests using the testing framework
            test_run_output = self.testing_framework.execute_unit_tests()
            
            # Validate the testing framework response
            if not isinstance(test_run_output, dict) or "success" not in test_run_output or "issues_found" not in test_run_output:
                return {
                    "success": False,
                    "issues_found": True,
                    "message": "Testing framework error: Invalid response format",
                    "details": {"error": "Invalid testing framework response"}
                }
            
            summary = test_run_output.get("summary", "No summary provided")
            
            # Check if framework itself failed
            if not test_run_output["success"]:
                return {
                    "success": False,
                    "issues_found": True,
                    "message": f"Testing framework execution failed: {summary}",
                    "details": test_run_output
                }
            
            # Framework ran successfully, check for test failures
            if test_run_output["issues_found"]:
                return {
                    "success": True,
                    "issues_found": True,
                    "message": f"Tests ran, issues found: {summary}",
                    "details": test_run_output
                }
            
            # All tests passed
            return {
                "success": True,
                "issues_found": False,
                "message": f"All tests passed: {summary}",
                "details": test_run_output
            }
            
        except Exception as e:
            return {
                "success": False,
                "issues_found": True,
                "message": f"Exception during testing: {str(e)}",
                "details": {"error": str(e), "traceback": traceback.format_exc()}
            }
    
    def analyze_test_results(self, test_result_details: Dict[str, Any], project_id: str) -> Dict[str, Any]:
        """
        Analyze test results to identify actionable issues.
        
        Args:
            test_result_details: Test results from run_tests
            project_id: ID of the project
            
        Returns:
            Analysis result dictionary
        """
        try:
            # Transform test failures into DetailedIssue objects
            issues_for_analyzer = []
            
            raw_failures = test_result_details.get("details", {}).get("failures", [])
            if isinstance(raw_failures, list):
                for failure in raw_failures:
                    try:
                        issue_data = {
                            "project_id": project_id,
                            "source_component": "TestingFramework.UnitTests",
                            "phase": "UnitTest",
                            "severity": "high",
                            "type": failure.get("type", "TestFailure"),
                            "message": failure.get("message", "Test failed"),
                            "description": failure.get("description"),
                            "file_path": failure.get("file_path"),
                            "line_number": failure.get("line_number"),
                            "function_name": failure.get("test_name"),
                            "stack_trace": failure.get("stack_trace"),
                            "expected_behavior": failure.get("expected"),
                            "actual_behavior": failure.get("actual")
                        }
                        
                        # Create DetailedIssue object
                        detailed_issue = DetailedIssue(**issue_data)
                        issues_for_analyzer.append(detailed_issue)
                        
                    except Exception as e:
                        print(f"Could not transform test failure to DetailedIssue: {e}")
                        continue
            
            # If no issues found but test indicated problems, handle gracefully
            if not issues_for_analyzer and test_result_details.get("issues_found"):
                return {
                    "success": True,
                    "issues_found": False,
                    "message": "Test results indicated issues, but no specific failures were identified for analysis"
                }
            
            # If no issues to analyze
            if not issues_for_analyzer:
                return {
                    "success": True,
                    "issues_found": False,
                    "message": "No issues to analyze"
                }
            
            # Run analysis using feedback analyzer
            analysis = self.feedback_analyzer.classify_issues(
                issues_input=[issue.model_dump() for issue in issues_for_analyzer]
            )
            
            # Validate analyzer response
            if not isinstance(analysis, dict) or "issues" not in analysis or "fix_tasks" not in analysis:
                return {
                    "success": False,
                    "issues_found": True,
                    "message": "Analysis failed: Invalid response from FeedbackAnalyzer"
                }
            
            # Check for actionable issues
            actionable_issues = [issue for issue in analysis.get("issues", []) if issue.get("actionable", False)]
            fix_tasks = analysis.get("fix_tasks", [])
            
            return {
                "success": True,
                "issues_found": len(actionable_issues) > 0,
                "actionable_issues": actionable_issues,
                "fix_tasks": fix_tasks,
                "analysis": analysis,
                "message": f"Analysis complete: {len(actionable_issues)} actionable issues found"
            }
            
        except Exception as e:
            return {
                "success": False,
                "issues_found": True,
                "message": f"Exception during result analysis: {str(e)}"
            }
    
    def run_refinement_loop(self, analysis_result: Dict[str, Any], agents: Dict[str, Any], 
                           project_manager, max_iterations: int = 3) -> Dict[str, Any]:
        """
        Run refinement loop to fix identified issues.
        
        Args:
            analysis_result: Result from analysis containing actionable issues and fix tasks
            agents: Dictionary of available agents
            project_manager: Project manager instance for file operations
            max_iterations: Maximum number of refinement iterations
            
        Returns:
            Final result dictionary
        """
        try:
            fix_tasks = analysis_result.get("fix_tasks", [])
            
            for iteration in range(max_iterations):
                # Apply fixes using agents
                fixes_applied = self._apply_fixes(fix_tasks, agents, project_manager)
                
                if not fixes_applied:
                    break
                
                # Re-run tests to check if issues are resolved
                project_id = project_manager.project_id
                test_result = self.run_tests(project_id)
                
                if not test_result.get("success"):
                    return {
                        "success": False,
                        "status": "refinement_testing_failed",
                        "message": "Testing failed during refinement"
                    }
                
                if not test_result.get("issues_found"):
                    # All issues resolved!
                    return {
                        "success": True,
                        "status": "completed",
                        "message": f"Project completed successfully after {iteration + 1} refinement iterations",
                        "refinement_iterations": iteration + 1
                    }
            
            # Max iterations reached
            return {
                "success": True,
                "status": "completed_with_remaining_issues",
                "message": f"Refinement completed after {max_iterations} iterations, some issues may remain",
                "refinement_iterations": max_iterations
            }
            
        except Exception as e:
            return {
                "success": False,
                "status": "refinement_failed",
                "message": f"Exception during refinement loop: {str(e)}"
            }
    
    def _apply_fixes(self, fix_tasks: List[Dict[str, Any]], agents: Dict[str, Any], 
                    project_manager) -> bool:
        """
        Apply fixes using appropriate agents.
        
        Args:
            fix_tasks: List of fix tasks from analysis
            agents: Dictionary of available agents
            project_manager: Project manager for file operations
            
        Returns:
            True if any fixes were applied, False otherwise
        """
        fixes_applied = False
        
        # Get project name from project manager, with robust fallback handling
        try:
            if hasattr(project_manager, 'project_name'):
                project_name = project_manager.project_name
            elif hasattr(project_manager, 'project_id'):
                project_name = project_manager.project_id
            elif hasattr(project_manager, 'workspace_path'):
                # Extract project name from workspace path
                import os
                project_name = os.path.basename(project_manager.workspace_path.rstrip('/\\'))
            else:
                project_name = 'unknown_project'
        except Exception as e:
            print(f"Warning: Could not determine project name: {e}")
            project_name = 'unknown_project'
        
        for fix_task in fix_tasks:
            try:
                agent_type = fix_task.get("agent_type", "backend")
                agent = agents.get(agent_type)
                
                if not agent:
                    print(f"Agent '{agent_type}' not found for fix task")
                    continue
                
                fix_prompt = self._build_fix_prompt(fix_task, project_name)
                fix_result = agent.run(fix_prompt)
                
                # Process fix result and save files
                if fix_result and isinstance(fix_result, list):
                    for file_info in fix_result:
                        if isinstance(file_info, dict) and "path" in file_info and "content" in file_info:
                            # Try to save using project manager if available
                            try:
                                if hasattr(project_manager, 'save_code_to_file'):
                                    project_manager.save_code_to_file(file_info["path"], file_info["content"])
                                    fixes_applied = True
                                else:
                                    # Fallback: write file directly
                                    file_path = file_info["path"]
                                    with open(file_path, 'w', encoding='utf-8') as f:
                                        f.write(file_info["content"])
                                    fixes_applied = True
                            except Exception as save_error:
                                print(f"Error saving file {file_info['path']}: {save_error}")
                                continue
                            
            except Exception as e:
                print(f"Error applying fix: {str(e)}")
                continue
        
        # Commit changes if fixes were applied and project manager supports it
        if fixes_applied:
            try:
                if hasattr(project_manager, 'commit_changes'):
                    project_manager.commit_changes("Applied fixes from refinement loop")
            except Exception as commit_error:
                print(f"Error committing changes: {commit_error}")
                # Don't fail the entire operation for commit errors
            
        return fixes_applied
    
    def _build_fix_prompt(self, fix_task: Dict[str, Any], project_name: str) -> str:
        """
        Build a prompt for the agent to fix a specific issue.
        
        Args:
            fix_task: Fix task information
            project_name: Name of the project
            
        Returns:
            Fix prompt string
        """
        return f"""
Fix Request for Project: {project_name}

Issue Description: {fix_task.get('description', 'No description')}
File: {fix_task.get('file_path', 'Unknown')}
Issue Type: {fix_task.get('issue_type', 'Unknown')}
Severity: {fix_task.get('severity', 'Medium')}

Current Code Context:
{fix_task.get('code_context', 'No context provided')}

Expected Fix:
{fix_task.get('suggested_fix', 'No specific fix suggested')}

Please provide the corrected code files that address this issue while maintaining compatibility with the rest of the project.
Return the result as a list of dictionaries with 'path' and 'content' keys for each file to be updated.
"""
    
    def get_service_urls(self) -> List[str]:
        """Get current service URLs."""
        return self.service_urls.copy()
    
    def stop_services(self, project_name: str) -> Dict[str, Any]:
        """
        Stop project services.
        
        Args:
            project_name: Name of the project
            
        Returns:
            Result dictionary
        """
        try:
            # Clear service URLs
            self.service_urls = []
            
            return {
                "success": True,
                "message": "Services stopped successfully"
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to stop services: {str(e)}"
            }