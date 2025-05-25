#!/usr/bin/env python3
"""
Simple Browser Automation Test
"""

import asyncio
import sys
from pathlib import Path

async def main():
    """Main function to test browser automation."""
    
    try:
        print("🚀 Starting browser automation test...")
        
        from playwright.async_api import async_playwright
        print("✅ Playwright imported successfully")
        
        async with async_playwright() as p:
            print("🌐 Launching browser...")
            
            # Launch browser in headless mode first to test
            browser = await p.chromium.launch(headless=False, slow_mo=1000)
            print("✅ Browser launched successfully")
            
            page = await browser.new_page()
            print("✅ New page created")
            
            print("🔍 Navigating to Google...")
            await page.goto("https://www.google.com", timeout=30000)
            print("✅ Google loaded successfully")
            
            # Take a screenshot
            await page.screenshot(path="google_homepage.png")
            print("📸 Screenshot taken: google_homepage.png")
            
            print("🔍 Looking for search box...")
            await page.wait_for_selector('input[name="q"], textarea[name="q"]', timeout=10000)
            print("✅ Search box found")
            
            print("⌨️  Typing search query...")
            await page.fill('input[name="q"], textarea[name="q"]', "100 best songs of all time")
            print("✅ Search query typed")
            
            print("🔍 Pressing Enter...")
            await page.press('input[name="q"], textarea[name="q"]', "Enter")
            print("✅ Search submitted")
            
            print("⏳ Waiting for search results...")
            await page.wait_for_load_state("networkidle", timeout=15000)
            print("✅ Search results loaded")
            
            # Take screenshot of results
            await page.screenshot(path="search_results.png")
            print("📸 Search results screenshot: search_results.png")
            
            print("🖱️  Looking for first result...")
            await page.wait_for_selector("h3", timeout=10000)
            print("✅ Found search result headers")
            
            # Get the first result link
            first_result = await page.query_selector("h3")
            if first_result:
                print("🖱️  Clicking first result...")
                await first_result.click()
                print("✅ Clicked first result")
                
                print("⏳ Waiting for page to load...")
                await page.wait_for_load_state("networkidle", timeout=15000)
                
                # Get page info
                title = await page.title()
                url = page.url
                
                print(f"📄 Page Title: {title}")
                print(f"🔗 Page URL: {url}")
                
                # Take final screenshot
                await page.screenshot(path="final_page.png")
                print("📸 Final page screenshot: final_page.png")
                
            else:
                print("❌ Could not find first result")
            
            print("⏳ Waiting 5 seconds before closing...")
            await asyncio.sleep(5)
            
            await browser.close()
            print("✅ Browser closed")
            
        print("\n🎉 Browser automation completed successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
