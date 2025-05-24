"""
Browser-Use MCP Helpers

This package provides helper functions to use the browser-use MCP server
for browser automation tasks, similar to the previous helper functions
but with the advantages of the MCP implementation.
"""

from .browser_helpers import (
    run_browser_task,
    run_deep_research,
    stop_browser_task,
    get_browser_logs
)

__all__ = [
    "run_browser_task",
    "run_deep_research",
    "stop_browser_task", 
    "get_browser_logs"
]
