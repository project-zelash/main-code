from typing import Dict, List, Any, Optional
import json
import re # Import re for regex operations

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
        self.llm = llm_factory.create_llm("gemini", model=os.getenv("GEMINI_ANALYSIS_MODEL", "gemini-1.5-pro"), temperature=0.3) # Allow model override
        self.previous_results = None
    
    def classify_issues(self, test_results_input: Dict[str, Any]) -> Dict[str, Any]: # Return type changed
        """
        Analyze test results, classify issues, and suggest fix tasks.
        
        Args:
            test_results_input: Results from tests (can include build results, static analysis, unit tests, etc.)
            
        Returns:
            Dictionary containing analysis success, issues found, classified issues, and fix tasks.
        """
        # Convert test results to a standardized format
        formatted_results = self._format_test_results(test_results_input)
        
        # Create a prompt for issue classification and fix task generation
        prompt = self._create_classification_prompt(formatted_results)
        
        # Run LLM to classify issues
        messages = [
            {\"role\": \"system\", \"content\": \"You are an expert software engineer specializing in debugging, issue analysis, and proposing actionable fix tasks. Your output MUST be a single, valid JSON object, with no surrounding text or markdown formatting.\"},
            {\"role\": \"user\", \"content\": prompt}
        ]
        
        llm_response_content = ""
        try:
            response = self.llm.chat(messages)
            llm_response_content = response.get(\"content\", \"\")
            
            # Extract and process the classification and fix tasks
            analysis_output = self._extract_analysis_from_response(llm_response_content)

            # Store results for future progress comparison
            self.previous_results = test_results_input # Store the original input

            if analysis_output.get(\"parsing_error\"): # Check if parsing itself failed
                return {
                    \"success\": False,
                    \"issues_found\": True, # Assume issues if parsing failed
                    \"analysis\": analysis_output, # Contains the parsing error details
                    \"message\": f\"Failed to parse LLM response: {analysis_output['parsing_error_message']}\"
                }

            if not analysis_output.get(\"issues\") and not analysis_output.get(\"fix_tasks\"):
                # If LLM returns empty valid JSON, it means no issues were identified from the input
                 return {
                    \"success\": True,
                    \"issues_found\": False,
                    \"analysis\": {\"issues\": [], \"fix_tasks\": []},
                    \"message\": \"Analysis complete. No actionable issues or fix tasks identified by LLM.\"
                }
            
            return {
                \"success\": True,
                \"issues_found\": bool(analysis_output.get(\"issues\")), # True if there are any issues
                \"analysis\": analysis_output, # Contains \"issues\" and \"fix_tasks\"
                \"message\": \"Analysis and fix task suggestion complete.\"
            }

        except Exception as e:
            # Log this error appropriately if you have a logging mechanism
            error_message = f\"Error during LLM call or processing in FeedbackAnalyzer: {str(e)}. LLM response snippet: {llm_response_content[:500]}\"
            print(error_message) # Or use a proper logger
            return {
                \"success\": False,
                \"issues_found\": True, # Assume issues if analysis fails
                \"analysis\": {
                    \"issues\": [{\
                        \"type\": \"analyzer_error\", \"severity\": \"critical\", \"component\": \"FeedbackAnalyzer\",
                        \"layer\": \"N/A\", \"message\": f\"Failed during analysis: {str(e)}\",
                        \"cause\": \"LLM interaction or response processing failed. Check logs for details.\",
                        \"affected_files\": []
                    }],
                    \"fix_tasks\": []
                },
                \"message\": f\"Error during feedback analysis: {str(e)}\"
            }
    
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
        # Added a more complete example in the prompt
        return f\"\"\"
        Analyze these test results and classify all issues found:
        
        {formatted_results}
        
        For each issue, provide:
        1. The type of issue (e.g., build_error, runtime_error, logical_error, security_vulnerability, performance_bottleneck, ui_glitch, data_corruption, configuration_error, test_failure_incorrect_logic, dependency_conflict).
        2. The severity (critical, high, medium, low).
        3. The affected component or specific module name (e.g., 'user_authentication_module', 'api_gateway_routing', 'shopping_cart_ui_state_management').
        4. A clear, concise description of the problem, referencing specific error messages or test failures.
        5. The most likely root cause, being as specific as possible.
        6. A detailed, actionable, step-by-step suggested approach to fix it. This should be concrete enough for another LLM to implement the fix.
        7. The specific file(s) and ideally line number(s) or function/class names that likely need modification. If multiple files, list them.

        Return your analysis as a SINGLE, VALID JSON OBJECT with two top-level keys: "issues" and "fix_tasks".
        The "issues" key should have an array of issue objects.
        The "fix_tasks" key should have an array of task objects, where each task aims to resolve one or more identified issues.

        IMPORTANT: Your entire response MUST be only the JSON object. Do not include any explanatory text, markdown formatting (like ```json), or any other characters before or after the JSON object.

        JSON Structure Example:
        {{
            "issues": [
                {{
                    "type": "runtime_error",
                    "severity": "high",
                    "component": "payment_processing_service",
                    "layer": "backend",
                    "message": "NullPointerException when processing Visa payments for amounts over $1000.",
                    "cause": "The 'discount_code_object' is null for high-value transactions if no discount is applied, but its properties are accessed directly.",
                    "affected_files": [ 
                        {{ "path": "src/services/payment_processor.py", "details": "process_visa function, around line 155" }}
                    ]
                }}
            ],
            "fix_tasks": [
                {{
                    "task_id": "fix_payment_npe_001",
                    "description": "Add a null check for 'discount_code_object' before accessing its properties in 'process_visa' function within 'payment_processor.py'. If null, use default values or skip discount logic.",
                    "target_layer": "backend",
                    "target_components": ["payment_processing_service"],
                    "related_issue_messages": ["NullPointerException when processing Visa payments for amounts over $1000."],
                    "estimated_complexity": "low",
                    "suggested_implementation_details": "In 'payment_processor.py', locate the 'process_visa' function. Before the line 'final_amount -= discount_code_object.value', insert: 'if discount_code_object is not None and hasattr(discount_code_object, 'value'):'. Ensure to handle the 'else' case appropriately, perhaps by logging or applying no discount."
                }}
            ]
        }}
        
        If no issues are found from the provided test results, return exactly this JSON:
        {{
            "issues": [],
            "fix_tasks": []
        }}
        \"\"\"
    
    def _extract_analysis_from_response(self, response: str) -> Dict[str, Any]: # Return type changed to Dict[str, Any] to include potential parsing error flags
        """
        Extract classified issues and fix_tasks from LLM response.
        Handles potential markdown code blocks and validates structure.
        
        Args:
            response: LLM response text.
            
        Returns:
            A dictionary with "issues" and "fix_tasks" lists, or error flags if parsing fails.
        """
        try:
            # Strip markdown code block fences if present
            # Handles ```json ... ``` or ``` ... ```
            cleaned_response = re.sub(r\"^```(?:json)?\\n?|\\n?```$\", \"\", response.strip(), flags=re.MULTILINE)

            # Attempt to find JSON object, robustly handling potential surrounding text if regex didn't catch it all
            # This is a fallback if the LLM still includes minor non-JSON text despite prompt instructions.
            json_start = cleaned_response.find('{')
            json_end = cleaned_response.rfind('}') + 1
            
            if json_start != -1 and json_end > json_start:
                json_str = cleaned_response[json_start:json_end]
                
                try:
                    parsed_json = json.loads(json_str)
                except json.JSONDecodeError as e_json_specific:
                    error_msg = f"JSONDecodeError: {e_json_specific} when parsing string."
                    # Log this specific error for better debugging
                    print(f"FeedbackAnalyzer: {error_msg} Parsed JSON: {json_str[:500]}")
                    self._log_feedback_analyzer_error(
                        method_name="_extract_analysis_from_response",
                        message=error_msg,
                        details={"json_string_snippet": json_str[:500], "raw_response_snippet": response[:500], "error": str(e_json_specific)}
                    )
                    return {"parsing_error": True, "error_message": error_msg, "raw_response": response}
                
                # Validate basic structure
                if isinstance(parsed_json, dict) and \\
                   "issues" in parsed_json and \\
                   "fix_tasks" in parsed_json and \\
                   isinstance(parsed_json["issues"], list) and \\
                   isinstance(parsed_json["fix_tasks"], list):
                    return parsed_json 
                else:
                    # Log an issue about the unexpected structure
                    error_msg = "LLM response was parsed but has an unexpected structure."
                    attempted_parse_snippet = f" Parsed JSON snippet: {json_str[:500]}" if json_str else ""
                    print(f"FeedbackAnalyzer: {error_msg}{attempted_parse_snippet}") # This is the area of the original error at line 338
                    self._log_feedback_analyzer_error(
                        method_name="_extract_analysis_from_response",
                        message=error_msg,
                        details={"parsed_json_snippet": json_str[:500], "raw_response_snippet": response[:500]}
                    )
                    return {
                        "parsing_error": True, 
                        "error_message": f"{error_msg}{attempted_parse_snippet}",
                        "issues": [], 
                        "fix_tasks": []
                    }
            else:
                # Could not find a JSON object
                error_msg = "Could not find JSON object in LLM response."
                print(f"FeedbackAnalyzer: {error_msg} Cleaned Response: {cleaned_response[:500]}")
                return {
                    "parsing_error": True,
                    "parsing_error_message": error_msg,
                    "issues": [],
                    "fix_tasks": []
                }
                
        except (ValueError, json.JSONDecodeError) as e:
            # Log this error
            error_msg = f\"Failed to parse LLM response into JSON: {str(e)}.\"
            # Try to provide a snippet of what was attempted to be parsed if json_str was defined
            attempted_parse_snippet = ""
            if 'json_str' in locals() and json_str:
                attempted_parse_snippet = f\" Attempted to parse: {json_str[:500]}\"
            elif 'cleaned_response' in locals() and cleaned_response:
                attempted_parse_snippet = f\" Cleaned response was: {cleaned_response[:500]}\"
            else:
                attempted_parse_snippet = f\" Original response was: {response[:500]}\"

            print(f\"FeedbackAnalyzer: {error_msg}{attempted_parse_snippet}\")
            return {
                "parsing_error": True,
                "parsing_error_message": f\"{error_msg}{attempted_parse_snippet}\",
                "issues": [], # Ensure keys exist even on parsing error
                "fix_tasks": []
            }

    def extract_error_context(self, issues: List[Dict[str, Any]], project_files: Dict[str, str]) -> Dict[str, Any]:
        """
        Extract additional context for issues from project files.
        This method might be less critical if the LLM in classify_issues already handles file context well.
        Consider if this is still needed or if its logic should be merged/simplified.
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