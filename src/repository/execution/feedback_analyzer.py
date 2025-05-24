from typing import Dict, List, Any, Optional
import json

from src.service.llm_factory import LLMFactory

class FeedbackAnalyzer:
    """
    Component responsible for analyzing test results, classifying issues, and tracking progress.
    """
    
    def __init__(self, llm_factory: LLMFactory):
        """
        Initialize the feedback analyzer.
        
        Args:
            llm_factory: Factory for creating LLM instances.
        """
        self.llm_factory = llm_factory
        self.llm = llm_factory.create_llm("gemini", "gemini-1.5-pro", temperature=0.3)
        self.previous_results = None
    
    def classify_issues(self, test_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Analyze test results and classify issues.
        
        Args:
            test_results: Results from tests (can include build results, static analysis, unit tests, etc.)
            
        Returns:
            List of classified issues.
        """
        # Convert test results to a standardized format
        formatted_results = self._format_test_results(test_results)
        
        # Create a prompt for issue classification
        prompt = self._create_classification_prompt(formatted_results)
        
        # Run LLM to classify issues
        messages = [
            {"role": "system", "content": "You are an expert software engineer specializing in debugging and issue analysis."},
            {"role": "user", "content": prompt}
        ]
        
        response = self.llm.chat(messages)
        
        # Extract and process the classification
        classified_issues = self._extract_classified_issues(response.get("content", ""))
        
        # Store results for future progress comparison
        self.previous_results = test_results
        
        return classified_issues
    
    def _format_test_results(self, test_results: Dict[str, Any]) -> str:
        """
        Format test results for LLM analysis.
        
        Args:
            test_results: Raw test results.
            
        Returns:
            Formatted test results as a string.
        """
        formatted = []
        
        # Handle build results
        if "build" in test_results:
            build = test_results["build"]
            status = build.get("status", "unknown")
            formatted.append(f"Build Status: {status}")
            
            if "errors" in build:
                formatted.append("Build Errors:")
                for error in build["errors"]:
                    formatted.append(f"- {error}")
            
            if "warnings" in build:
                formatted.append("Build Warnings:")
                for warning in build["warnings"]:
                    formatted.append(f"- {warning}")
        
        # Handle static analysis
        if "static_analysis" in test_results:
            static = test_results["static_analysis"]
            formatted.append("\nStatic Analysis Results:")
            
            for issue in static.get("issues", []):
                severity = issue.get("severity", "error")
                message = issue.get("message", "Unknown issue")
                file = issue.get("file", "unknown")
                line = issue.get("line", "?")
                
                formatted.append(f"- [{severity.upper()}] {file}:{line} - {message}")
        
        # Handle unit tests
        if "unit_tests" in test_results:
            unit = test_results["unit_tests"]
            total = unit.get("total", 0)
            passed = unit.get("passed", 0)
            failed = unit.get("failed", 0)
            
            formatted.append(f"\nUnit Tests: {passed}/{total} passed, {failed} failed")
            
            if "failures" in unit:
                formatted.append("Failed Tests:")
                for failure in unit["failures"]:
                    test_name = failure.get("test", "Unknown test")
                    message = failure.get("message", "Unknown failure")
                    formatted.append(f"- {test_name}: {message}")
        
        # Handle browser tests
        if "browser_tests" in test_results:
            browser = test_results["browser_tests"]
            total = browser.get("total", 0)
            passed = browser.get("passed", 0)
            failed = browser.get("failed", 0)
            
            formatted.append(f"\nBrowser Tests: {passed}/{total} passed, {failed} failed")
            
            if "failures" in browser:
                formatted.append("Failed Browser Tests:")
                for failure in browser["failures"]:
                    test_name = failure.get("test", "Unknown test")
                    message = failure.get("message", "Unknown failure")
                    formatted.append(f"- {test_name}: {message}")
        
        return "\n".join(formatted)
    
    def _create_classification_prompt(self, formatted_results: str) -> str:
        """
        Create a prompt for issue classification.
        
        Args:
            formatted_results: Formatted test results.
            
        Returns:
            Classification prompt.
        """
        return f"""
        Analyze these test results and classify all issues found:
        
        {formatted_results}
        
        For each issue, provide:
        1. The type of issue (build error, runtime error, logical error, security issue, etc.)
        2. The severity (critical, high, medium, low)
        3. The affected component or layer
        4. A clear description of the problem
        5. The most likely cause
        6. A suggested approach to fix it
        
        Return your analysis as a JSON array with this structure:
        [
            {{
                "type": "string",
                "severity": "critical|high|medium|low",
                "component": "string",
                "layer": "backend|middleware|design|frontend",
                "message": "string",
                "cause": "string",
                "fix_approach": "string"
            }}
        ]
        
        Output ONLY valid JSON without any explanations or markdown.
        """
    
    def _extract_classified_issues(self, response: str) -> List[Dict[str, Any]]:
        """
        Extract classified issues from LLM response.
        
        Args:
            response: LLM response text.
            
        Returns:
            List of classified issues.
        """
        try:
            # Find where the JSON array starts and ends
            json_start = response.find('[')
            json_end = response.rfind(']') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                return json.loads(json_str)
            else:
                # Return empty list if no JSON found
                return []
                
        except (ValueError, json.JSONDecodeError) as e:
            # Return error as a single issue if parsing fails
            return [{
                "type": "parsing_error",
                "severity": "low",
                "component": "feedback_analyzer",
                "layer": "backend",
                "message": f"Failed to parse LLM response: {str(e)}",
                "cause": "LLM returned malformed JSON",
                "fix_approach": "Retry analysis with more explicit JSON formatting instructions"
            }]
    
    def extract_error_context(self, issues: List[Dict[str, Any]], project_files: Dict[str, str]) -> Dict[str, Any]:
        """
        Extract additional context for issues from project files.
        
        Args:
            issues: Classified issues.
            project_files: Dictionary mapping file paths to content.
            
        Returns:
            Issues with added context.
        """
        enriched_issues = []
        
        for issue in issues:
            enriched = issue.copy()
            
            # Try to find relevant file context if a component is specified
            component = issue.get("component", "")
            
            # Find files that might be related to this component
            related_files = []
            for path, content in project_files.items():
                if component.lower() in path.lower():
                    # Extract a snippet around the error if possible
                    error_message = issue.get("message", "")
                    snippet = self._extract_snippet(content, error_message)
                    
                    related_files.append({
                        "path": path,
                        "snippet": snippet,
                        "relevance": "high" if snippet else "medium"
                    })
            
            enriched["context"] = {
                "related_files": related_files[:3]  # Limit to 3 most relevant files
            }
            
            enriched_issues.append(enriched)
        
        return {
            "issues": enriched_issues,
            "context_stats": {
                "files_analyzed": len(project_files),
                "issues_enriched": len(enriched_issues)
            }
        }
    
    def _extract_snippet(self, content: str, error_message: str, context_lines: int = 3) -> Dict[str, Any]:
        """
        Extract a code snippet around an error in a file.
        
        Args:
            content: File content.
            error_message: Error message to search for.
            context_lines: Number of lines of context to include.
            
        Returns:
            Dictionary with line number and code snippet.
        """
        if not error_message or len(error_message) < 5:
            return {}
            
        lines = content.split('\n')
        
        # Search for a line containing part of the error message
        best_match = None
        best_score = 0
        
        for i, line in enumerate(lines):
            # Simple matching algorithm - count overlapping words
            error_words = set(error_message.lower().split())
            line_words = set(line.lower().split())
            overlap = len(error_words.intersection(line_words))
            
            if overlap > best_score:
                best_score = overlap
                best_match = i
        
        # If we found a reasonable match, extract the snippet
        if best_match is not None and best_score >= 2:
            start_line = max(0, best_match - context_lines)
            end_line = min(len(lines), best_match + context_lines + 1)
            
            snippet_lines = lines[start_line:end_line]
            
            return {
                "line_number": best_match + 1,  # 1-based line number
                "code": "\n".join(snippet_lines),
                "highlight_line": best_match - start_line + 1  # Relative line in snippet
            }
        
        return {}
    
    def evaluate_progress(self, current_results: Dict[str, Any], previous_results: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Evaluate progress by comparing current results with previous results.
        
        Args:
            current_results: Current test results.
            previous_results: Previous test results (or None).
            
        Returns:
            Progress evaluation.
        """
        # Use stored previous results if not explicitly provided
        if previous_results is None and self.previous_results is not None:
            previous_results = self.previous_results
            
        if previous_results is None:
            # If no previous results, just count current issues
            current_issues = self._count_issues(current_results)
            
            return {
                "is_first_iteration": True,
                "current_issues": current_issues,
                "progress_metrics": {
                    "total_issues": current_issues["total"]
                },
                "conclusion": "First evaluation" if current_issues["total"] > 0 else "No issues found"
            }
        
        # Count issues in both current and previous results
        current_issues = self._count_issues(current_results)
        previous_issues = self._count_issues(previous_results)
        
        # Calculate differences
        total_diff = previous_issues["total"] - current_issues["total"]
        critical_diff = previous_issues["by_severity"].get("critical", 0) - current_issues["by_severity"].get("critical", 0)
        high_diff = previous_issues["by_severity"].get("high", 0) - current_issues["by_severity"].get("high", 0)
        
        # Determine if there's improvement
        is_improving = total_diff > 0
        has_critical = current_issues["by_severity"].get("critical", 0) > 0
        
        # Build progress metrics
        progress_metrics = {
            "total_issues_change": total_diff,
            "critical_issues_change": critical_diff,
            "high_issues_change": high_diff,
            "is_improving": is_improving,
            "percent_change": self._calculate_percent_change(previous_issues["total"], current_issues["total"]),
            "layers_improved": []
        }
        
        # Check which layers improved
        for layer in ["backend", "middleware", "design", "frontend"]:
            prev_count = previous_issues["by_layer"].get(layer, 0)
            curr_count = current_issues["by_layer"].get(layer, 0)
            
            if prev_count > curr_count:
                progress_metrics["layers_improved"].append(layer)
        
        # Determine conclusion
        if current_issues["total"] == 0:
            conclusion = "All issues resolved"
        elif is_improving:
            conclusion = "Making progress" if not has_critical else "Making progress but critical issues remain"
        else:
            conclusion = "No improvement" if total_diff == 0 else "Regression detected"
        
        # Determine if refinement should continue
        continue_refinement = current_issues["total"] > 0 and (
            has_critical or 
            current_issues["by_severity"].get("high", 0) > 0 or
            not is_improving
        )
        
        return {
            "is_first_iteration": False,
            "current_issues": current_issues,
            "previous_issues": previous_issues,
            "progress_metrics": progress_metrics,
            "conclusion": conclusion,
            "continue_refinement": continue_refinement
        }
    
    def _count_issues(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Count issues in test results by various dimensions.
        
        Args:
            results: Test results.
            
        Returns:
            Issue counts.
        """
        by_severity = {}
        by_type = {}
        by_layer = {}
        total = 0
        
        # Count build errors
        if "build" in results:
            build = results["build"]
            errors = len(build.get("errors", []))
            warnings = len(build.get("warnings", []))
            
            by_type["build_error"] = errors
            by_type["build_warning"] = warnings
            by_severity["critical"] = by_severity.get("critical", 0) + errors
            by_severity["medium"] = by_severity.get("medium", 0) + warnings
            by_layer["backend"] = by_layer.get("backend", 0) + errors + warnings
            
            total += errors + warnings
        
        # Count static analysis issues
        if "static_analysis" in results:
            static = results["static_analysis"]
            
            for issue in static.get("issues", []):
                severity = issue.get("severity", "medium").lower()
                issue_type = "static_" + issue.get("type", "error").lower()
                file_path = issue.get("file", "")
                
                # Determine layer from file path
                layer = "backend"  # Default
                if "/frontend/" in file_path or file_path.endswith((".js", ".html", ".css")):
                    layer = "frontend"
                elif "/design/" in file_path:
                    layer = "design"
                elif "/middleware/" in file_path:
                    layer = "middleware"
                
                by_severity[severity] = by_severity.get(severity, 0) + 1
                by_type[issue_type] = by_type.get(issue_type, 0) + 1
                by_layer[layer] = by_layer.get(layer, 0) + 1
                
                total += 1
        
        # Count unit test failures
        if "unit_tests" in results:
            unit = results["unit_tests"]
            failures = len(unit.get("failures", []))
            
            by_type["unit_test_failure"] = failures
            by_severity["high"] = by_severity.get("high", 0) + failures
            
            # Distribute failures across layers based on test names
            for failure in unit.get("failures", []):
                test_name = failure.get("test", "").lower()
                
                if "frontend" in test_name:
                    by_layer["frontend"] = by_layer.get("frontend", 0) + 1
                elif "design" in test_name:
                    by_layer["design"] = by_layer.get("design", 0) + 1
                elif "middleware" in test_name:
                    by_layer["middleware"] = by_layer.get("middleware", 0) + 1
                else:
                    by_layer["backend"] = by_layer.get("backend", 0) + 1
            
            total += failures
        
        # Count browser test failures
        if "browser_tests" in results:
            browser = results["browser_tests"]
            failures = len(browser.get("failures", []))
            
            by_type["browser_test_failure"] = failures
            by_severity["high"] = by_severity.get("high", 0) + failures
            by_layer["frontend"] = by_layer.get("frontend", 0) + failures
            
            total += failures
        
        return {
            "total": total,
            "by_severity": by_severity,
            "by_type": by_type,
            "by_layer": by_layer
        }
    
    def _calculate_percent_change(self, previous: int, current: int) -> float:
        """
        Calculate percent change between two values.
        
        Args:
            previous: Previous value.
            current: Current value.
            
        Returns:
            Percent change.
        """
        if previous == 0:
            return 0.0 if current == 0 else 100.0
            
        return ((previous - current) / previous) * 100.0