#!/usr/bin/env python3
"""
Browser Automation with Timeout and Status Updates
"""

import asyncio
import sys
import signal
from pathlib import Path

class TimeoutException(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutException("Operation timed out")

async def run_with_status():
    """Run browser automation with regular status updates."""
    
    try:
        print("🚀 STARTING BROWSER AUTOMATION")
        print("=" * 50)
        
        from playwright.async_api import async_playwright
        print("✅ Playwright imported")
        
        # Set up timeout
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(60)  # 60 second timeout
        
        async with async_playwright() as p:
            print("🌐 Launching Chrome browser (visible window)...")
            
            # Launch with visible browser
            browser = await p.chromium.launch(
                headless=False,
                slow_mo=500,  # Slow down operations to see them
                args=['--no-first-run', '--no-default-browser-check']
            )
            
            page = await browser.new_page()
            print("✅ Browser launched and page created")
            
            print("🔍 Navigating to Google...")
            await page.goto("https://www.google.com")
            await page.wait_for_load_state("networkidle")
            print("✅ Google homepage loaded")
            
            # Handle consent if needed
            try:
                consent_button = page.locator('button:has-text("Accept"), button:has-text("I agree"), [aria-label*="Accept"]').first
                if await consent_button.is_visible(timeout=2000):
                    await consent_button.click()
                    print("✅ Clicked consent button")
            except:
                print("ℹ️  No consent button found or needed")
            
            print("📸 Taking homepage screenshot...")
            await page.screenshot(path="google_homepage.png")
            print("✅ Homepage screenshot saved")
            
            print("⌨️  Searching for '100 best songs of all time'...")
            
            # Find search input
            search_input = page.locator('input[name="q"], textarea[name="q"]').first
            await search_input.fill("100 best songs of all time")
            await search_input.press("Enter")
            print("✅ Search query submitted")
            
            print("⏳ Waiting for search results...")
            await page.wait_for_load_state("networkidle")
            await page.wait_for_selector("h3", timeout=10000)
            print("✅ Search results loaded")
            
            print("📸 Taking search results screenshot...")
            await page.screenshot(path="search_results_new.png")
            print("✅ Search results screenshot saved")
            
            print("🖱️  Clicking on first search result...")
            first_result = page.locator("h3").first
            await first_result.click()
            print("✅ Clicked first result")
            
            print("⏳ Waiting for target page to load...")
            await page.wait_for_load_state("networkidle")
            
            # Get page information
            title = await page.title()
            url = page.url
            
            print(f"📄 Target Page Title: {title}")
            print(f"🔗 Target Page URL: {url}")
            
            print("📸 Taking final screenshot...")
            await page.screenshot(path="target_page_new.png")
            print("✅ Final screenshot saved")
            
            print("⏳ Keeping browser open for 5 seconds...")
            await asyncio.sleep(5)
            
            await browser.close()
            print("✅ Browser closed")
            
        signal.alarm(0)  # Cancel timeout
        
        print("\n🎉 BROWSER AUTOMATION COMPLETED SUCCESSFULLY!")
        print("=" * 50)
        print("📁 Files created:")
        print("  - google_homepage.png")
        print("  - search_results_new.png") 
        print("  - target_page_new.png")
        
        return True
        
    except TimeoutException:
        print("⏰ Browser automation timed out after 60 seconds")
        return False
    except Exception as e:
        print(f"❌ Error during browser automation: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main entry point."""
    success = await run_with_status()
    if success:
        print("\n✅ Task completed successfully!")
    else:
        print("\n❌ Task failed or timed out!")
    return success

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
