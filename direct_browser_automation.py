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
REPO_ROOT = Path(__file__).parent  # main-code directory
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
            
            # Handle potential cookie consent or privacy notices
            try:
                # Look for common consent buttons
                consent_selectors = [
                    'button:has-text("Accept all")',
                    'button:has-text("I agree")',
                    'button:has-text("Accept")',
                    '[data-testid="accept-all"]',
                    '.VfPpkd-LgbsSe[jsname="tWT92d"]'  # Google's "Accept all" button
                ]
                
                for selector in consent_selectors:
                    try:
                        await page.click(selector, timeout=2000)
                        print("Clicked consent button")
                        break
                    except:
                        continue
            except:
                pass
            
            # Type the search query
            print("Typing search query: '100 best songs of all time'")
            
            # Try different search input selectors
            search_selectors = [
                'textarea[name="q"]',
                'input[name="q"]',
                '[data-testid="search-input"]',
                '.gLFyf'  # Google's search input class
            ]
            
            search_input = None
            for selector in search_selectors:
                try:
                    await page.wait_for_selector(selector, timeout=3000)
                    search_input = selector
                    break
                except:
                    continue
            
            if search_input:
                await page.fill(search_input, "100 best songs of all time")
                
                # Press Enter to search
                print("Pressing Enter to search...")
                await page.press(search_input, "Enter")
            else:
                print("Could not find search input, trying alternative method...")
                await page.keyboard.type("100 best songs of all time")
                await page.keyboard.press("Enter")
            
            # Wait for the search results
            print("Waiting for search results...")
            await page.wait_for_load_state("networkidle")
            
            # Take a screenshot to show the search results
            screenshot_path = REPO_ROOT / "search_results.png"
            await page.screenshot(path=str(screenshot_path))
            print(f"Screenshot saved to: {screenshot_path}")
            
            # Find and click the first search result
            print("Looking for the first search result...")
            
            # Try different selectors for search results
            result_selectors = [
                "h3:first-of-type",
                ".LC20lb:first-of-type",  # Google's result title class
                "[data-sokoban-container] h3:first-of-type",
                ".g h3:first-of-type"
            ]
            
            clicked = False
            for selector in result_selectors:
                try:
                    await page.wait_for_selector(selector, timeout=5000)
                    print(f"Found search result with selector: {selector}")
                    await page.click(selector)
                    clicked = True
                    break
                except Exception as e:
                    print(f"Failed with selector {selector}: {e}")
                    continue
            
            if not clicked:
                print("Could not find clickable search result, trying alternative...")
                # Try clicking any visible link
                try:
                    await page.click("a[href*='http']:first-of-type")
                    clicked = True
                except:
                    print("Could not click any search result")
            
            if clicked:
                print("Successfully clicked on a search result!")
                
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
                
                print(f"\n✅ SUCCESS!")
                print(f"Page Title: {title}")
                print(f"Page URL: {url}")
            else:
                print("❌ Could not click on any search result")
            
            # Wait for 10 seconds to view the page
            print("\nWaiting for 10 seconds so you can view the page...")
            for i in range(10, 0, -1):
                print(f"Closing in {i} seconds...", end="\r")
                await asyncio.sleep(1)
            
        except Exception as e:
            print(f"Error during browser automation: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            # Close browser
            print("\n\nClosing browser...")
            await browser.close()
            
    print("\n================ TASK COMPLETE ================\n")
    print("The browser task has been completed and the browser has been closed.")
    print(f"Screenshots saved to: {REPO_ROOT}")

if __name__ == "__main__":
    asyncio.run(run_browser_task())
