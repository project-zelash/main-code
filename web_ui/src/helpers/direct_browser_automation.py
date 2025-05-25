#!/usr/bin/env python3
"""
Direct Browser Automation Script

This script bypasses the requirement for an LLM configuration and directly 
automates browser interactions using Playwright. It performs an Amazon
headphones search as a demonstration.
"""

import os
import sys
import asyncio
import logging
from typing import Optional, List, Dict, Any

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("direct_browser_automation")

# Add project root to path if needed
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Import the browser automation components
from src.browser.custom_browser import CustomBrowser
from src.browser.custom_context import CustomBrowserContextConfig
from src.controller.custom_controller import CustomController


def print_colored(text: str, color: str = "white") -> None:
    """
    Print colored text to the console
    
    Args:
        text: The text to print
        color: Color name (red, green, blue, etc.)
    """
    color_codes = {
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
    color_code = color_codes.get(color.lower(), color_codes["white"])
    reset_code = color_codes["reset"]
    print(f"{color_code}{text}{reset_code}")


async def search_amazon_headphones() -> None:
    """
    Direct browser automation to search for headphones on Amazon
    without requiring an LLM configuration
    """
    print_colored("=== DIRECT BROWSER AUTOMATION - AMAZON HEADPHONES SEARCH ===", "magenta")
    
    browser = None
    browser_context = None
    
    try:
        # Initialize the browser (same as what happens in the WebUI)
        print_colored("Initializing browser...", "blue")
        browser = await CustomBrowser.create(
            headless=False,
            browser_executable_path=None,
            slow_mo=100,  # Add a small delay for visibility
        )
        print_colored("Browser initialized successfully", "green")
        
        # Create a browser context
        print_colored("Creating browser context...", "blue")
        browser_context = await browser.new_context(
            config=CustomBrowserContextConfig(
                screen_size={"width": 1280, "height": 800},
                locale="en-US",
                timezone_id="America/Los_Angeles",
                is_mobile=False,
                record_video=True,
                record_har=True,
            )
        )
        print_colored("Browser context created successfully", "green")
        
        # Create a controller for interacting with the browser
        controller = CustomController(browser_context)
        
        # Create a new page
        print_colored("Creating new page...", "blue")
        page = await browser_context.new_page()
        await page.goto("about:blank")
        print_colored("New page created", "green")
        
        # Execute the Amazon headphones search task
        print_colored("Starting Amazon headphones search task...", "cyan")
        
        # 1. Navigate to Amazon
        print_colored("Navigating to Amazon...", "blue")
        await page.goto("https://www.amazon.com")
        print_colored("Amazon homepage loaded", "green")
        
        # 2. Search for headphones
        print_colored("Searching for headphones...", "blue")
        search_box = await page.wait_for_selector("#twotabsearchtextbox")
        await search_box.fill("headphones")
        await search_box.press("Enter")
        print_colored("Search executed", "green")
        
        # 3. Wait for search results
        print_colored("Waiting for search results...", "blue")
        await page.wait_for_selector('[data-component-type="s-search-result"]', timeout=10000)
        print_colored("Search results loaded", "green")
        
        # 4. Extract some product information
        print_colored("Extracting product information...", "blue")
        product_elements = await page.query_selector_all('[data-component-type="s-search-result"]')
        
        products = []
        for i, product_element in enumerate(product_elements[:5]):  # Get first 5 products
            try:
                title_element = await product_element.query_selector("h2 a span")
                price_element = await product_element.query_selector(".a-price .a-offscreen")
                
                title = await title_element.text_content() if title_element else "No title found"
                price = await price_element.text_content() if price_element else "Price not available"
                
                products.append({"title": title, "price": price})
                
                print_colored(f"Product {i+1}:", "yellow")
                print_colored(f"  Title: {title}", "white")
                print_colored(f"  Price: {price}", "green")
                print("")
                
            except Exception as e:
                print_colored(f"Error extracting product {i+1}: {e}", "red")
        
        # 5. Take a screenshot
        print_colored("Taking a screenshot...", "blue")
        screenshot_path = os.path.join(current_dir, "amazon_headphones_screenshot.png")
        await page.screenshot(path=screenshot_path)
        print_colored(f"Screenshot saved to: {screenshot_path}", "green")
        
        # 6. Simulate clicking on the first product
        print_colored("Clicking on the first product...", "blue")
        first_product = await page.query_selector('[data-component-type="s-search-result"] h2 a')
        if first_product:
            await first_product.click()
            # Wait for product page to load
            await page.wait_for_load_state("networkidle")
            print_colored("Product page loaded", "green")
            
            # Extract product details
            product_title = await page.title()
            print_colored(f"Product page title: {product_title}", "cyan")
        else:
            print_colored("No product found to click", "yellow")
        
        print_colored("Task completed successfully!", "green")
        
    except Exception as e:
        logger.error(f"Error during browser automation: {e}", exc_info=True)
        print_colored(f"Error: {e}", "red")
    
    finally:
        # Clean up resources
        print_colored("Cleaning up resources...", "blue")
        if browser_context:
            await browser_context.close()
        if browser:
            await browser.close()
        print_colored("Browser closed", "green")


async def main() -> None:
    """Main entry point for the script"""
    try:
        await search_amazon_headphones()
    except KeyboardInterrupt:
        print_colored("\nScript interrupted by user", "yellow")
    except Exception as e:
        logger.error(f"Unhandled exception: {e}", exc_info=True)
        print_colored(f"Fatal error: {e}", "red")


if __name__ == "__main__":
    print_colored("This script demonstrates direct browser automation without requiring an LLM", "cyan")
    print_colored("It will open a browser window and search for headphones on Amazon", "cyan")
    asyncio.run(main())
