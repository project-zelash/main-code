import pytest
import asyncio
from unittest.mock import patch, MagicMock

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src/helpers')))

# Test for browser_actions.perform_browser_search (should be working, so only smoke-test)
def test_perform_browser_search_runs():
    from browser_actions import perform_browser_search
    # Patch WebuiManager and run_agent_task as imported in the function
    with patch('src.webui.webui_manager.WebuiManager') as MockManager, \
         patch('src.webui.components.browser_use_agent_tab.run_agent_task', return_value=async_iter([])), \
         patch('src.webui.components.browser_use_agent_tab.handle_stop', return_value=asyncio.Future()), \
         patch('src.webui.components.browser_use_agent_tab.handle_clear', return_value=asyncio.Future()):
        loop = asyncio.get_event_loop()
        # handle_stop and handle_clear futures must be set to done
        for fut in [MockManager.return_value, MockManager.return_value]:
            pass  # No need to set_result for these mocks
        loop.run_until_complete(perform_browser_search())

# Helper for async generator patching
def async_iter(items):
    async def gen():
        for item in items:
            yield item
    return gen()

# Test for direct_browser_trigger.run_browser_task
def test_run_browser_task_runs():
    from direct_browser_trigger import run_browser_task
    with patch('src.webui.webui_manager.WebuiManager') as MockManager, \
         patch('src.webui.components.browser_use_agent_tab.run_agent_task', return_value=async_iter([])), \
         patch('src.webui.components.browser_use_agent_tab.handle_stop', return_value=asyncio.Future()), \
         patch('src.webui.components.browser_use_agent_tab.handle_clear', return_value=asyncio.Future()):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(run_browser_task())

# Test for working_example.run_browser_search
def test_working_example_runs():
    from working_example import run_browser_search
    with patch('src.webui.webui_manager.WebuiManager') as MockManager, \
         patch('src.webui.components.browser_use_agent_tab.run_agent_task', return_value=async_iter([])), \
         patch('src.webui.components.browser_use_agent_tab.handle_stop', return_value=asyncio.Future()), \
         patch('src.webui.components.browser_use_agent_tab.handle_clear', return_value=asyncio.Future()):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(run_browser_search())
