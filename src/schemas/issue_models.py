'''
Defines Pydantic models for issue tracking and error reporting.
'''
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
import uuid

class DetailedIssue(BaseModel):
    issue_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    source_component: str  # e.g., "OrchestrationEngine", "TestingFramework.UnitTests", "FeedbackAnalyzer", "BuildProcess", "StaticAnalysisTool.LinterName", "Agent.BackendAgent"
    phase: str  # e.g., "CodeGeneration", "Build", "UnitTest", "IntegrationTest", "StaticAnalysis", "RefinementAnalysis", "Deployment"
    layer_affected: Optional[str] = None  # e.g., "backend", "middleware", "frontend", "design", "cross-cutting"
    severity: str  # "critical", "high", "medium", "low", "informational"
    type: str  # e.g., "SyntaxError", "RuntimeError", "LogicError", "CompatibilityIssue", "SecurityVulnerability", "PerformanceBottleneck", "BuildFailure", "TestFailure", "LintingViolation", "CodeQualitySuggestion"
    message: str  # Concise error message
    description: Optional[str] = None  # More detailed explanation of the issue and its context
    file_path: Optional[str] = None  # Relative path to the primary affected file
    line_number: Optional[int] = None
    column_number: Optional[int] = None
    function_name: Optional[str] = None  # If applicable
    class_name: Optional[str] = None  # If applicable
    code_snippet_context: Optional[str] = None  # A few lines of code around the error
    stack_trace: Optional[str] = None
    expected_behavior: Optional[str] = None
    actual_behavior: Optional[str] = None
    reproduction_steps: Optional[List[str]] = None
    related_issue_ids: Optional[List[str]] = None  # For tracking recurring or related issues
    analysis_by_llm: Optional[Dict[str, Any]] = None  # To store FeedbackAnalyzer's output: cause, fix_suggestion, etc.
    status: str = "new"  # "new", "analyzed", "fix_proposed", "fix_attempted", "resolved", "ignored"
    additional_data: Optional[Dict[str, Any]] = None  # For any other relevant structured data
