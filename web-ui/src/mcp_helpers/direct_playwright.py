#!/usr/bin/env python3
"""
Direct Playwright Browser Automation

This script uses Playwright directly to perform a browser automation task,
guaranteeing a visible browser window.
"""

import asyncio
import os
import sys
import time
from pathlib import Path

# Add the repository root to the path for imports
REPO_ROOT = Path(__file__).parents[3]  # main-code directory
sys.path.append(str(REPO_ROOT))

async def run_browser_task():
    """Run a browser task directly using Playwright."""
    
    # Import Playwright here to ensure it's available in the virtual environment
    from playwright.async_api import async_playwright
    
    print("\n================ STARTING BROWSER TASK ================\n")
    print("Task: Go to www.google.com and search for '100 best songs of all time'. Click on the first search result.")
    
    async with async_playwright() as p:
        # Launch a visible Chrome browser
        browser = await p.chromium.launch(headless=False)
        
        # Create a new context
        context = await browser.new_context(viewport={"width": 1280, "height": 720})
        
        # Create a new page
        page = await context.new_page()
        
        print("\nBrowser launched successfully. You should see a Chrome window open.")
        
        try:
            # Navigate to Google
            print("\nNavigating to Google...")
            await page.goto("https://www.google.com")
            
            # Wait for the page to load
            await page.wait_for_load_state("networkidle")
            
            # Type the search query
            print("Typing search query: '100 best songs of all time'")
            await page.fill('textarea[name="q"]', "100 best songs of all time")
            
            # Press Enter to search
            print("Pressing Enter to search...")
            await page.press('textarea[name="q"]', "Enter")
            
            # Wait for the search results
            print("Waiting for search results...")
            await page.wait_for_load_state("networkidle")
            
            # Take a screenshot to show the search results
            screenshot_path = REPO_ROOT / "search_results.png"
            await page.screenshot(path=str(screenshot_path))
            print(f"Screenshot saved to: {screenshot_path}")
            
            # Find and click the first search result
            print("Clicking on the first search result...")
            # Wait for search results to appear
            await page.wait_for_selector("h3", state="visible")
            # Click on the first result
            await page.click("h3:first-of-type")
            
            # Wait for the page to load
            print("Waiting for the target page to load...")
            await page.wait_for_load_state("networkidle")
            
            # Take a screenshot of the target page
            target_path = REPO_ROOT / "target_page.png"
            await page.screenshot(path=str(target_path))
            print(f"Target page screenshot saved to: {target_path}")
            
            # Get the page title and URL
            title = await page.title()
            url = page.url
            
            print(f"\nPage Title: {title}")
            print(f"Page URL: {url}")
            
            # Wait for 10 seconds to view the page
            print("\nWaiting for 10 seconds so you can view the page...")
            for i in range(10, 0, -1):
                print(f"Closing in {i} seconds...", end="\r")
                await asyncio.sleep(1)
            
        except Exception as e:
            print(f"Error during browser automation: {e}")
        
        finally:
            # Close browser
            print("\n\nClosing browser...")
            await browser.close()
            
    print("\n================ TASK COMPLETE ================\n")
    print("The browser task has been completed and the browser has been closed.")
    print(f"Screenshots saved to: {REPO_ROOT}")

if __name__ == "__main__":
    asyncio.run(run_browser_task())
