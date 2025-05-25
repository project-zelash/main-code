"""
Helper functions for the Browser AI Agent

This module provides convenient functions to control the browser agent
with Google Gemini 2.0 Flash as the default model.
"""

from .agent_control import run_task, retrieve_logs, get_agent_status, stop_agent, pause_resume_agent
from .model_config import set_default_model, get_current_model_config

__all__ = [
    'run_task',
    'retrieve_logs',
    'get_agent_status',
    'stop_agent',
    'pause_resume_agent',
    'set_default_model',
    'get_current_model_config'
]
