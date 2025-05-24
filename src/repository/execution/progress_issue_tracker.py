import datetime
import traceback
from typing import Dict, List, Any, Optional, Callable
from src.schemas.issue_models import DetailedIssue


class ProgressIssueTracker:
    """Handles progress tracking and issue management for the orchestration engine."""
    
    def __init__(self):
        self.progress_log: List[Dict[str, Any]] = []
        self.progress_callbacks: List[Callable[[str, int, str], None]] = []
        self.detailed_issue_log: List[DetailedIssue] = []
        self.internal_errors: List[Dict[str, Any]] = []
        self.externally_reported_errors: List[Dict[str, Any]] = []
        
    def update_progress(self, message: str, percentage: int = -1):
        """
        Update progress with a message and optional percentage.
        
        Args:
            message: Progress message
            percentage: Completion percentage (-1 for no specific percentage)
        """
        timestamp = datetime.datetime.now().isoformat()
        progress_entry = {
            "message": message,
            "percentage": percentage,
            "timestamp": timestamp
        }
        
        self.progress_log.append(progress_entry)
        
        # Call all registered callbacks
        for callback in self.progress_callbacks:
            try:
                callback(message, percentage, timestamp)
            except Exception as e:
                print(f"Error in progress callback: {e}")
    
    def log_issue(self, issue_data: Dict[str, Any]) -> DetailedIssue:
        """
        Log a detailed issue.
        
        Args:
            issue_data: Issue information
            
        Returns:
            Created DetailedIssue object
        """
        try:
            detailed_issue = DetailedIssue(**issue_data)
            self.detailed_issue_log.append(detailed_issue)
            return detailed_issue
        except Exception as e:
            # If we can't create a DetailedIssue, log it as an internal error
            self.log_internal_error("log_issue", f"Failed to create DetailedIssue: {str(e)}", e, {"issue_data": issue_data})
            # Return a minimal valid DetailedIssue
            minimal_issue = DetailedIssue(
                project_id=issue_data.get("project_id", "unknown"),
                source_component="IssueLogger",
                phase="IssueLogging",
                severity="critical",
                type="IssueLoggingError",
                message=f"Failed to log issue: {str(e)}"
            )
            self.detailed_issue_log.append(minimal_issue)
            return minimal_issue
    
    def log_internal_error(self, step: str, message: str, exception_obj: Optional[Exception] = None, details: Optional[Any] = None):
        """
        Log an internal error for debugging purposes.
        
        Args:
            step: The step where the error occurred
            message: Error message
            exception_obj: Optional exception object
            details: Optional additional details
        """
        error_entry = {
            "step": step,
            "message": message,
            "timestamp": datetime.datetime.now().isoformat(),
            "exception": str(exception_obj) if exception_obj else None,
            "exception_type": type(exception_obj).__name__ if exception_obj else None,
            "stack_trace": traceback.format_exc() if exception_obj else None,
            "details": details
        }
        self.internal_errors.append(error_entry)
        print(f"Internal Error in {step}: {message}")
    
    def get_detailed_issues(self, severity_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get detailed issues with optional severity filtering.
        
        Args:
            severity_filter: Optional severity level to filter by
            
        Returns:
            List of detailed issues as dictionaries
        """
        issues = self.detailed_issue_log
        
        if severity_filter:
            issues = [issue for issue in issues if issue.severity == severity_filter]
            
        return [issue.model_dump() for issue in issues]
    
    def report_external_error(self, error_data: Dict[str, Any], project_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Report an error from external sources (e.g., user feedback, monitoring).
        
        Args:
            error_data: Error information
            project_id: Project ID for the issue
            
        Returns:
            Result dictionary
        """
        try:
            # Log as a detailed issue
            issue_data = {
                "project_id": project_id or "unknown_project",
                "source_component": error_data.get("source", "ExternalReport"),
                "phase": "ExternalFeedback",
                "severity": error_data.get("severity", "medium"),
                "type": error_data.get("type", "ExternalError"),
                "message": error_data.get("message", "External error reported"),
                "description": error_data.get("description"),
                "file_path": error_data.get("file_path"),
                "additional_data": error_data
            }
            
            logged_issue = self.log_issue(issue_data)
            
            # Also add to externally reported errors for backwards compatibility
            self.externally_reported_errors.append({
                "timestamp": datetime.datetime.now().isoformat(),
                "error_data": error_data,
                "issue_id": logged_issue.issue_id
            })
            
            self.update_progress(f"External error reported: {error_data.get('message', 'No message')}", -1)
            
            return {
                "success": True,
                "message": "Error reported successfully",
                "issue_id": logged_issue.issue_id
            }
            
        except Exception as e:
            error_message = f"Failed to report external error: {str(e)}"
            self.log_internal_error("report_external_error", error_message, e)
            return {"success": False, "message": error_message}
    
    def add_progress_callback(self, callback: Callable[[str, int, str], None]):
        """
        Add a progress callback function.
        
        Args:
            callback: Function that takes (message, percentage, timestamp)
        """
        self.progress_callbacks.append(callback)

    def remove_progress_callback(self, callback: Callable[[str, int, str], None]):
        """
        Remove a progress callback function.
        
        Args:
            callback: Function to remove
        """
        if callback in self.progress_callbacks:
            self.progress_callbacks.remove(callback)
    
    def get_status_info(self) -> Dict[str, Any]:
        """
        Get status information related to progress and issues.
        
        Returns:
            Dictionary with counts and recent progress
        """
        return {
            "progress_log": self.progress_log[-10:] if self.progress_log else [],  # Last 10 entries
            "detailed_issues_count": len(self.detailed_issue_log),
            "internal_errors_count": len(self.internal_errors),
            "external_errors_count": len(self.externally_reported_errors)
        }