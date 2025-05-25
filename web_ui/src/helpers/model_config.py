"""
Model configuration helper functions for the Browser AI Agent

This module provides functions to set and manage the default model (Google Gemini 2.0 Flash).
"""

import os
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Default model configuration for Google Gemini 2.0 Flash
DEFAULT_MODEL_CONFIG = {
    "provider": "google",
    "model_name": "gemini-2.0-flash",
    "temperature": 0.6,
    "use_vision": True,
}

# Default agent configuration
DEFAULT_AGENT_CONFIG = {
    "max_steps": 100,
    "max_actions": 10,
    "max_input_tokens": 128000,
    "max_browser_state_tokens": 16000,
    "use_vision": True,
}

# Default browser configuration
DEFAULT_BROWSER_CONFIG = {
    "headless": False,
    "slow_mo": 0,
    "window_size": {"width": 1280, "height": 800},
}


def ensure_default_google_model(llm_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Ensure Google Gemini is used as the default model if no configuration is provided.
    
    Args:
        llm_config: Existing LLM configuration (can be None)
        
    Returns:
        LLM configuration with Google Gemini as default
    """
    # Start with the default config
    config = DEFAULT_MODEL_CONFIG.copy()
    
    # Override with provided config if any
    if llm_config:
        config.update(llm_config)
    
    # Ensure API key is set if using Google
    if config["provider"] == "google" and not config.get("api_key"):
        # Get from environment if available
        api_key = os.getenv("GOOGLE_API_KEY")
        if api_key:
            config["api_key"] = api_key
            # Log success but mask most of the key
            if api_key:
                masked_key = "******" + api_key[-4:] if len(api_key) > 4 else "******"
                logger.debug(f"Using Google API key from environment: {masked_key}")
        else:
            logger.warning("GOOGLE_API_KEY not found in environment")
    
    return config


def set_default_model(
    provider: str = "google",
    model_name: str = "gemini-2.0-flash",
    temperature: float = 0.6,
    use_vision: bool = True,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Set a new default model configuration.
    
    Args:
        provider: LLM provider name
        model_name: Model name
        temperature: Model temperature
        use_vision: Whether to use vision capabilities
        api_key: API key (optional)
        base_url: Base URL for API (optional)
        
    Returns:
        The new default model configuration
    """
    global DEFAULT_MODEL_CONFIG
    
    # Update the default config
    DEFAULT_MODEL_CONFIG = {
        "provider": provider,
        "model_name": model_name,
        "temperature": temperature,
        "use_vision": use_vision,
    }
    
    # Add optional parameters if provided
    if api_key:
        DEFAULT_MODEL_CONFIG["api_key"] = api_key
    
    if base_url:
        DEFAULT_MODEL_CONFIG["base_url"] = base_url
    
    return DEFAULT_MODEL_CONFIG


def get_current_model_config() -> Dict[str, Any]:
    """
    Get the current default model configuration.
    
    Returns:
        Current default model configuration
    """
    return DEFAULT_MODEL_CONFIG.copy()


def get_default_configs() -> Dict[str, Dict[str, Any]]:
    """
    Get all default configurations for agent, browser, and LLM.
    
    Returns:
        Dictionary containing all default configurations
    """
    return {
        "llm": DEFAULT_MODEL_CONFIG.copy(),
        "agent": DEFAULT_AGENT_CONFIG.copy(),
        "browser": DEFAULT_BROWSER_CONFIG.copy(),
    }


def update_env_with_model_config(config: Dict[str, Any]) -> bool:
    """
    Update the .env file with the given model configuration.
    This makes the configuration persist across restarts.
    
    Args:
        config: Model configuration
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Path to .env file
        env_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), '.env')
        
        # Check if file exists
        if not os.path.exists(env_file):
            logger.error(f".env file not found at {env_file}")
            return False
        
        # Read current content
        with open(env_file, 'r') as f:
            lines = f.readlines()
        
        # Prepare new content with updated values
        new_lines = []
        updated_keys = set()
        
        for line in lines:
            line = line.strip()
            # Skip empty lines and comments
            if not line or line.startswith('#'):
                new_lines.append(line)
                continue
            
            # Parse key-value pair
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                
                # Update provider-specific settings
                if config.get('provider') == 'google':
                    if key == 'GOOGLE_API_KEY' and 'api_key' in config:
                        new_lines.append(f"{key}={config['api_key']}")
                        updated_keys.add(key)
                    else:
                        new_lines.append(line)
                else:
                    new_lines.append(line)
            else:
                new_lines.append(line)
        
        # Add new keys if not updated
        if config.get('provider') == 'google' and 'api_key' in config and 'GOOGLE_API_KEY' not in updated_keys:
            new_lines.append(f"GOOGLE_API_KEY={config['api_key']}")
        
        # Write back to file
        with open(env_file, 'w') as f:
            f.write('\n'.join(new_lines) + '\n')
        
        return True
    
    except Exception as e:
        logger.error(f"Error updating .env file: {e}", exc_info=True)
        return False
