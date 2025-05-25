"""
Browser-Use MCP Helper Functions

This module provides helper functions to act as a client to a running
MCP browser-use server for browser automation tasks.
"""

import os
import json
import requests # Ensure 'requests' is in the main requirements.txt
import logging
from typing import Dict, Any, Optional # Simplified imports

logger = logging.getLogger(__name__)

# Configuration for the MCP server connection will now be primarily managed
# by the Zelash application's central configuration, which should provide
# the server URL to these functions or the classes that use them.
# For direct use or testing, environment variables can still be a fallback.

# ZELASH_BROWSER_AUTOMATION_SERVER_URL will be the primary source.
# Example: "http://127.0.0.1:8777" (note: no /mcp path by default for uvicorn)
DEFAULT_MCP_SERVER_URL = "http://127.0.0.1:8777"
MCP_SERVER_URL = os.getenv("ZELASH_BROWSER_AUTOMATION_SERVER_URL", DEFAULT_MCP_SERVER_URL)

# Timeout for requests to the MCP server (in seconds)
DEFAULT_MCP_REQUEST_TIMEOUT = 300.0 # 5 minutes
MCP_REQUEST_TIMEOUT = float(os.getenv("ZELASH_MCP_CLIENT_REQUEST_TIMEOUT", str(DEFAULT_MCP_REQUEST_TIMEOUT)))

# API Key for MCP server if it's configured to use one.
# The mcp-browser-use server itself doesn't have this, but a gateway might.
MCP_API_KEY = os.getenv("ZELASH_MCP_SERVER_API_KEY_FOR_CLIENT")


def _get_mcp_server_url():
    """Gets the MCP server URL, prioritizing Zelash config."""
    # In a full integration, this would ideally come from a shared config module
    # or be passed into the functions/classes that use these helpers.
    return os.getenv("ZELASH_BROWSER_AUTOMATION_SERVER_URL", MCP_SERVER_URL)

def _get_mcp_request_timeout():
    """Gets the MCP request timeout."""
    return float(os.getenv("ZELASH_MCP_CLIENT_REQUEST_TIMEOUT", str(MCP_REQUEST_TIMEOUT)))

def _get_mcp_api_key():
    """Gets the API key for the MCP client if configured."""
    return os.getenv("ZELASH_MCP_SERVER_API_KEY_FOR_CLIENT", MCP_API_KEY)


def _send_mcp_request(method: str, params: Dict[str, Any], task_description_for_log: str) -> str:
    """
    Sends a JSON-RPC request to the configured MCP server.

    Args:
        method: The MCP tool name (e.g., "run_browser_agent").
        params: A dictionary of parameters for the MCP tool.
        task_description_for_log: A short description of the task for logging.

    Returns:
        The string result from the MCP tool, or an error message string.
    """
    server_url = _get_mcp_server_url()
    request_timeout = _get_mcp_request_timeout()
    api_key = _get_mcp_api_key()

    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": os.urandom(6).hex() # Generate a random hex id
    }

    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}" # Or other scheme if needed

    logger.info(f"Sending MCP request to {server_url} for method '{method}' with task: {task_description_for_log[:100]}...")
    logger.debug(f"MCP Request Payload: {json.dumps(payload)}")
    logger.debug(f"MCP Request Headers: {headers}")


    try:
        response = requests.post(server_url, json=payload, headers=headers, timeout=request_timeout)
        response.raise_for_status()  # Raises an HTTPError for bad responses (4XX or 5XX)
        
        response_data = response.json()
        logger.debug(f"MCP Response Data: {json.dumps(response_data)}")

        if "error" in response_data and response_data["error"] is not None:
            error_info = response_data["error"]
            error_code = error_info.get("code", "N/A")
            error_message = error_info.get("message", "Unknown MCP error")
            error_data = error_info.get("data", None)
            log_msg = f"MCP server returned an error for method '{method}'. Code: {error_code}, Message: {error_message}"
            if error_data:
                log_msg += f", Data: {error_data}"
            logger.error(log_msg)
            return f"Error: MCP Server - {error_message} (Code: {error_code})"
        
        result = response_data.get("result")
        
        # The mcp-browser-use server tools (run_browser_agent, run_deep_research)
        # are expected to return a string.
        if not isinstance(result, str):
            logger.error(f"Unexpected result type or missing result from MCP server for method '{method}'. Expected string, got {type(result)}. Full response: {response_data}")
            return "Error: Unexpected or missing result from MCP server. Expected a string. Check server logs."
            
        logger.info(f"MCP method '{method}' completed successfully for task: {task_description_for_log[:100]}.")
        return result

    except requests.exceptions.Timeout:
        logger.error(f"Request to MCP server at {server_url} timed out for method '{method}' after {request_timeout} seconds. Task: {task_description_for_log[:100]}")
        return f"Error: MCP request timed out ({request_timeout}s)."
    except requests.exceptions.ConnectionError:
        logger.error(f"Failed to connect to MCP server at {server_url}. Ensure the server is running and accessible. Method: '{method}'. Task: {task_description_for_log[:100]}")
        return f"Error: Could not connect to MCP server at {server_url}."
    except requests.exceptions.HTTPError as e:
        # This will catch 4xx/5xx errors after raise_for_status()
        logger.error(f"HTTP error occurred during MCP request to {server_url} for method '{method}': {e}. Response: {e.response.text[:500] if e.response else 'No response body'}")
        return f"Error: MCP communication failed with HTTP status {e.response.status_code if e.response else 'N/A'} - {str(e)}."
    except requests.exceptions.RequestException as e:
        logger.error(f"An error occurred during MCP request to {server_url} for method '{method}': {e}. Task: {task_description_for_log[:100]}")
        return f"Error: MCP communication failed - {str(e)}."
    except json.JSONDecodeError:
        resp_text = response.text if 'response' in locals() else 'No response object'
        logger.error(f"Failed to decode JSON response from MCP server at {server_url} for method '{method}'. Response text: {resp_text[:500]}. Task: {task_description_for_log[:100]}")
        return "Error: Invalid JSON response from MCP server."
    except Exception as e: # Catch any other unexpected errors
        logger.error(f"An unexpected error occurred in MCP client for method '{method}' to {server_url}: {e}. Task: {task_description_for_log[:100]}", exc_info=True)
        return f"Error: Unexpected client-side error - {str(e)}."

def run_browser_task(
    task: str,
    # These parameters are now informational as the server primarily controls these settings.
    # They are kept for potential future use if the MCP tool evolves to accept them as overrides.
    headless_hint: bool = False, 
    use_vision_hint: bool = True,
) -> str:
    """
    Run a browser task by sending a request to the MCP browser-use server.
    The actual headless/vision mode is determined by the MCP server's configuration.

    Args:
        task: The natural language task to perform.
        headless_hint: (Informational) Preferred mode; server configuration takes precedence.
        use_vision_hint: (Informational) Preferred vision use; server configuration takes precedence.

    Returns:
        The string result from the MCP tool (output of the browser agent) or an error message.
    """
    logger.info(f"Initiating browser task via MCP: {task[:150]}... (Headless hint: {headless_hint}, Vision hint: {use_vision_hint})")
    
    # Parameters for 'run_browser_agent' as per mcp-browser-use README:
    # - task (string, required)
    # Other settings like headless, vision, LLM models are configured on the server.
    params = {"task": task}
    
    # If in the future, the MCP tool 'run_browser_agent' supports overriding these via params,
    # they could be added here, e.g.:
    # if headless_hint is not None: params["headless_override"] = headless_hint
    # if use_vision_hint is not None: params["use_vision_override"] = use_vision_hint

    return _send_mcp_request(method="run_browser_agent", params=params, task_description_for_log=task)

def run_deep_research(
    research_task: str,
    max_parallel_browsers_override: Optional[int] = None,
) -> str:
    """
    Run a deep research task by sending a request to the MCP browser-use server.

    Args:
        research_task: The research topic or question.
        max_parallel_browsers_override: (Optional) Override server's default for max parallel browsers.

    Returns:
        The string result from the MCP tool (research report) or an error message.
    """
    logger.info(f"Initiating deep research task via MCP: {research_task[:150]}...")
    
    # Parameters for 'run_deep_research' as per mcp-browser-use README:
    # - research_task (string, required)
    # - max_parallel_browsers (integer, optional)
    params: Dict[str, Any] = {"research_task": research_task}
    if max_parallel_browsers_override is not None:
        params["max_parallel_browsers"] = max_parallel_browsers_override
        logger.info(f"Overriding max_parallel_browsers to: {max_parallel_browsers_override}")
    
    return _send_mcp_request(method="run_deep_research", params=params, task_description_for_log=research_task)

# Removed:
# - Global REPO_ROOT, MCP_INTEGRATION_PATH, BROWSER_USE_INTEGRATION_PATH (not relevant for client)
# - sys.path.append calls (not relevant for client)
# - stop_browser_task() and get_browser_logs() (not applicable to synchronous MCP client model)
# - Hardcoded API key (now uses _get_mcp_api_key() which checks env var)

if __name__ == "__main__":
    # Configure basic logging for example run
    logging.basicConfig(
        level=logging.DEBUG, # Use DEBUG to see detailed MCP request/response
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    
    # Ensure ZELASH_BROWSER_AUTOMATION_SERVER_URL is set in your environment
    # to point to the running mcp-browser-use server, e.g., http://127.0.0.1:8777
    # You can also set ZELASH_MCP_CLIENT_REQUEST_TIMEOUT if needed.
    
    effective_server_url = _get_mcp_server_url()
    print(f"MCP Helper attempting to connect to: {effective_server_url} with timeout {_get_mcp_request_timeout()}s")
    if _get_mcp_api_key():
        print("Using API Key for MCP requests.")

    # Test run_browser_task
    browser_task_description = "Go to example.com, find its title, and then find the link to 'More information...'.
