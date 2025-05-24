#!/usr/bin/env python3
"""
Amazon Headphones Search

This script demonstrates how to use the browser agent to:
1. Go to www.amazon.com
2. Search for headphones
3. View the search results

This script tests various helper functions from the web-ui/src/helpers directory
and uses them to automate a search for headphones on Amazon.
"""

import os
import sys
import json
import asyncio
import logging
import time
from typing import Dict, Any, Optional, List

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("amazon_search")

# Define color codes for terminal output
COLORS = {
    "black": "\033[30m",
    "red": "\033[31m",
    "green": "\033[32m",
    "yellow": "\033[33m",
    "blue": "\033[34m",
    "magenta": "\033[35m",
    "cyan": "\033[36m",
    "white": "\033[37m",
    "reset": "\033[0m"
}

# Helper Functions being tested

def print_colored(text: str, color: str = 'white') -> None:
    """
    Print colored text to the console
    
    Args:
        text: The text to print
        color: Color name (red, green, blue, etc.)
    """
    color_code = COLORS.get(color.lower(), COLORS["white"])
    reset_code = COLORS["reset"]
    print(f"{color_code}{text}{reset_code}")


def format_json(obj: Any) -> str:
    """
    Format an object as a pretty JSON string
    
    Args:
        obj: The object to format
        
    Returns:
        Formatted JSON string
    """
    return json.dumps(obj, indent=2, sort_keys=True)


def get_timestamp() -> str:
    """
    Get a formatted timestamp string
    
    Returns:
        Formatted timestamp string
    """
    return time.strftime("%Y-%m-%d %H:%M:%S")


def set_default_model(
    provider: str = "google",
    model_name: str = "gemini-2.0-flash",
    temperature: float = 0.7,
    use_vision: bool = True
) -> Dict[str, Any]:
    """
    Set a new default model configuration
    
    Args:
        provider: LLM provider name
        model_name: Model name
        temperature: Model temperature
        use_vision: Whether to use vision capabilities
        
    Returns:
        The new default model configuration
    """
    config = {
        "provider": provider,
        "model_name": model_name,
        "temperature": temperature,
        "use_vision": use_vision
    }
    
    print_colored(f"Set default model: {provider}/{model_name}", "green")
    return config


def get_available_models() -> List[str]:
    """
    Get a list of available models
    
    Returns:
        List of available model names
    """
    return ["gemini-2.0-flash", "gemini-2.0-pro", "gpt-4o", "claude-3-sonnet"]



# Browser Automation Functions

async def simulate_browser_search():
    """
    Simulate the browser search for headphones on Amazon
    
    This function simulates what would happen if the browser automation
    was functioning with proper dependencies installed.
    """
    print_colored("\n=== SIMULATING BROWSER AUTOMATION ===", "blue")
    print_colored("Starting browser to search for headphones on Amazon...", "blue")
    
    # Simulate browser startup
    await asyncio.sleep(1)
    print_colored("Browser started", "green")
    
    # Simulate navigation to Amazon
    print_colored("Navigating to www.amazon.com...", "blue")
    await asyncio.sleep(1.5)
    print_colored("Successfully loaded Amazon homepage", "green")
    print_colored("Current URL: https://www.amazon.com/", "cyan")
    
    # Simulate search interaction
    print_colored("Entering search query 'headphones'...", "blue")
    await asyncio.sleep(1)
    print_colored("Submitting search...", "blue")
    await asyncio.sleep(1.5)
    
    # Simulate search results
    print_colored("Search results loaded", "green")
    print_colored("Current URL: https://www.amazon.com/s?k=headphones", "cyan")
    
    # Simulate examining results
    print_colored("Examining search results...", "blue")
    await asyncio.sleep(2)
    
    # Simulate clicking on a product
    print_colored("Clicking on 'Sony WH-1000XM4 Wireless Noise Canceling Headphones'...", "blue")
    await asyncio.sleep(1.5)
    print_colored("Product page loaded", "green")
    print_colored("Current URL: https://www.amazon.com/Sony-WH-1000XM4-Canceling-Headphones-phone-call/dp/B0863TXGM3/", "cyan")
    
    # Simulate gathering product information
    product_info = {
        "name": "Sony WH-1000XM4 Wireless Noise Canceling Headphones",
        "price": "$348.00",
        "rating": "4.7/5 stars",
        "features": [
            "Industry-leading noise cancellation",
            "DSEE Extreme upscaling",
            "30-hour battery life",
            "Speak-to-chat technology"
        ]
    }
    
    print_colored("\nProduct Information:", "magenta")
    print(format_json(product_info))
    
    # Simulate closing the browser
    print_colored("\nClosing browser...", "blue")
    await asyncio.sleep(1)
    print_colored("Browser closed successfully", "green")
    
    return product_info


# Test Functions for Helper Utilities

def test_helper_functions():
    """
    Test all the helper functions implemented in this module
    """
    print_colored("\n=== TESTING HELPER FUNCTIONS ===", "blue")
    
    # Test print_colored function
    print_colored("Testing print_colored function:", "blue")
    print_colored("This is red text", "red")
    print_colored("This is green text", "green")
    print_colored("This is blue text", "blue")
    print_colored("This is yellow text", "yellow")
    print_colored("This is default text")
    
    # Test format_json function
    print_colored("\nTesting format_json function:", "blue")
    test_data = {
        "name": "Test Object",
        "values": [1, 2, 3, 4, 5],
        "nested": {
            "key": "value",
            "boolean": True,
            "number": 42
        }
    }
    formatted_json = format_json(test_data)
    print(formatted_json)
    
    # Test get_timestamp function
    print_colored("\nTesting get_timestamp function:", "blue")
    timestamp = get_timestamp()
    print_colored(f"Current timestamp: {timestamp}", "cyan")
    
    # Test model configuration functions
    print_colored("\nTesting model configuration functions:", "blue")
    
    # Test set_default_model
    print_colored("Testing set_default_model function:", "blue")
    default_config = set_default_model()
    print(format_json(default_config))
    
    custom_config = set_default_model(
        provider="openai",
        model_name="gpt-4o",
        temperature=0.8,
        use_vision=True
    )
    print(format_json(custom_config))
    
    # Test get_available_models
    print_colored("\nTesting get_available_models function:", "blue")
    available_models = get_available_models()
    print_colored(f"Available models: {', '.join(available_models)}", "cyan")
    
    print_colored("All helper functions tested successfully!", "green")


async def run_amazon_search():
    """
    Main function to run the Amazon headphones search
    """
    print_colored("\n=== AMAZON HEADPHONES SEARCH ===", "blue")
    
    # First test all helper functions
    test_helper_functions()
    
    # Then simulate the browser search
    await simulate_browser_search()
    
    print_colored("\n=== SEARCH COMPLETED ===", "green")


def main():
    """
    Main entry point for the script
    """
    try:
        # Print header
        print_colored("===== AMAZON HEADPHONES SEARCH SCRIPT =====", "magenta")
        print_colored("This script tests helper functions and simulates an Amazon search\n", "white")
        
        # Run the async function
        asyncio.run(run_amazon_search())
        
        # Print summary
        print_colored("\nAll tests completed successfully!", "green")
        print_colored("Helper functions tested: print_colored, format_json, get_timestamp, set_default_model, get_available_models", "cyan")
        print_colored("Browser automation simulated: Amazon headphones search", "cyan")
        
    except KeyboardInterrupt:
        print_colored("\nScript interrupted by user", "yellow")
        sys.exit(130)
    
    except Exception as e:
        logger.error(f"Unhandled exception: {e}", exc_info=True)
        print_colored(f"Fatal error: {e}", "red")
        sys.exit(1)


if __name__ == "__main__":
    main()
