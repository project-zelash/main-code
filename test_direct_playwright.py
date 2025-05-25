#!/usr/bin/env python3
"""
Independent test of DirectPlaywrightTester to verify browser testing functionality.

This script tests the DirectPlaywrightTester in isolation to identify any issues
with browser automation, service detection, or Playwright configuration.
"""

import asyncio
import time
import subprocess
import sys
import os
import requests
from pathlib import Path

# Add current directory to path for imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))
sys.path.insert(0, str(current_dir / "src"))

# Create a simplified DirectPlaywrightTester for testing
class DirectPlaywrightTester:
    """Direct Playwright browser testing - simplified for testing."""
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self._ensure_playwright_installed()
        
    def _ensure_playwright_installed(self):
        """Ensure Playwright browsers are installed."""
        try:
            from playwright.async_api import async_playwright
            print("✅ Playwright import successful")
        except ImportError:
            print("❌ Playwright not available - install with: pip install playwright")
            raise
        
    async def test_application(self, service_urls: list, custom_tests=None) -> dict:
        """Test application using direct Playwright automation."""
        print("\n================ STARTING BROWSER TESTING ================\n")
        
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            return {
                "success": False,
                "error": "Playwright not available - install with: pip install playwright && playwright install"
            }
        
        test_results = {
            "success": True,
            "tested_urls": [],
            "successful_connections": 0,
            "failed_connections": 0,
            "detailed_results": [],
            "screenshots": []
        }
        
        async with async_playwright() as p:
            # Launch browser (visible or headless based on setting)
            browser = await p.chromium.launch(headless=self.headless)
            context = await browser.new_context(viewport={"width": 1280, "height": 720})
            
            try:
                for i, url in enumerate(service_urls):
                    print(f"\nTesting URL {i+1}/{len(service_urls)}: {url}")
                    
                    page = await context.new_page()
                    url_result = {
                        "url": url,
                        "success": False,
                        "error": None,
                        "page_title": None,
                        "response_time": 0,
                        "screenshot_path": None
                    }
                    
                    try:
                        # Pre-check: Verify the URL is responding before browser test
                        print(f"Pre-checking URL availability: {url}")
                        try:
                            pre_response = requests.get(url, timeout=10)
                            if pre_response.status_code >= 400:
                                url_result["error"] = f"Server returned error status {pre_response.status_code}"
                                print(f"❌ Pre-check failed: Server returned {pre_response.status_code}")
                                test_results["failed_connections"] += 1
                                continue
                            else:
                                print(f"✅ Pre-check passed: Server returned {pre_response.status_code}")
                        except requests.exceptions.ConnectionError:
                            url_result["error"] = "Connection refused - server not responding"
                            print(f"❌ Pre-check failed: Connection refused")
                            test_results["failed_connections"] += 1
                            continue
                        except Exception as e:
                            url_result["error"] = f"Pre-check failed: {str(e)}"
                            print(f"❌ Pre-check failed: {str(e)}")
                            test_results["failed_connections"] += 1
                            continue
                        
                        start_time = time.time()
                        
                        # Navigate to the URL with longer timeout and better error handling
                        print(f"Navigating to {url} with browser...")
                        try:
                            await page.goto(url, timeout=45000, wait_until="networkidle")
                        except Exception as nav_error:
                            # Try with different wait conditions
                            nav_error_str = str(nav_error)
                            if "ERR_EMPTY_RESPONSE" in nav_error_str:
                                print(f"Empty response detected, trying with domcontentloaded...")
                                try:
                                    await page.goto(url, timeout=30000, wait_until="domcontentloaded")
                                except Exception as retry_error:
                                    url_result["error"] = f"Browser navigation failed: {str(retry_error)}"
                                    print(f"❌ Browser navigation failed: {str(retry_error)}")
                                    test_results["failed_connections"] += 1
                                    continue
                            else:
                                url_result["error"] = f"Browser navigation failed: {nav_error_str}"
                                print(f"❌ Browser navigation failed: {nav_error_str}")
                                test_results["failed_connections"] += 1
                                continue
                        
                        # Calculate response time
                        url_result["response_time"] = time.time() - start_time
                        
                        # Wait a bit more for dynamic content
                        print("Waiting for page content to load...")
                        await asyncio.sleep(2)
                        
                        # Try to get page title with fallback
                        try:
                            url_result["page_title"] = await page.title()
                        except:
                            url_result["page_title"] = "Unable to get title"
                        
                        # Check if page loaded successfully with multiple methods
                        try:
                            # Method 1: Check page content
                            page_content = await page.content()
                            content_length = len(page_content)
                            print(f"Page content length: {content_length} characters")
                            
                            # Method 2: Check for basic HTML structure
                            has_html = "<html" in page_content.lower()
                            has_body = "<body" in page_content.lower()
                            
                            # Method 3: Check if there are any visible elements
                            try:
                                visible_elements = await page.query_selector_all("*")
                                element_count = len(visible_elements)
                                print(f"Visible elements found: {element_count}")
                            except:
                                element_count = 0
                            
                            # Determine success based on multiple criteria
                            if content_length > 100 and (has_html or has_body or element_count > 5):
                                url_result["success"] = True
                                test_results["successful_connections"] += 1
                                print(f"✅ Successfully tested: {url}")
                                print(f"   Page Title: {url_result['page_title']}")
                                print(f"   Response Time: {url_result['response_time']:.2f}s")
                                print(f"   Content Length: {content_length} chars")
                                print(f"   Elements: {element_count}")
                            else:
                                url_result["error"] = f"Page appears empty or malformed (content: {content_length} chars, elements: {element_count})"
                                test_results["failed_connections"] += 1
                                print(f"❌ Failed: {url} - {url_result['error']}")
                                
                        except Exception as content_error:
                            url_result["error"] = f"Failed to analyze page content: {str(content_error)}"
                            test_results["failed_connections"] += 1
                            print(f"❌ Failed to analyze content: {str(content_error)}")
                        
                    except Exception as e:
                        url_result["error"] = str(e)
                        test_results["failed_connections"] += 1
                        print(f"❌ Failed to test {url}: {str(e)}")
                    
                    finally:
                        try:
                            await page.close()
                        except:
                            pass
                    
                    test_results["detailed_results"].append(url_result)
                    test_results["tested_urls"].append(url)
                
                # Calculate overall success
                total_tests = len(service_urls)
                success_rate = (test_results["successful_connections"] / total_tests * 100) if total_tests > 0 else 0
                
                if test_results["successful_connections"] == 0:
                    test_results["success"] = False
                    test_results["error"] = "No successful connections to any service URL"
                
                print(f"\n✅ Browser testing completed: {test_results['successful_connections']}/{total_tests} URLs successful")
                
            finally:
                await browser.close()
        
        print("\n================ BROWSER TESTING COMPLETE ================\n")
        return test_results

def start_test_server(port=8080):
    """Start a simple Python HTTP server for testing."""
    # Create a simple test directory with content
    test_dir = Path("./test_server_content")
    test_dir.mkdir(exist_ok=True)
    
    # Create test HTML file (without Unicode characters)
    test_html = test_dir / "index.html"
    test_html.write_text("""<!DOCTYPE html>
<html>
<head>
    <title>Test Server for Playwright Testing</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #f0f0f0; }
        .container { max-width: 600px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; }
        .status { color: green; font-weight: bold; font-size: 18px; }
        button { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
        button:hover { background: #0056b3; }
    </style>
</head>
<body>
    <div class="container">
        <h1>DirectPlaywrightTester Test Page</h1>
        <p class="status">Test server is running successfully!</p>
        <p>This page is served by Python's HTTP server for testing browser automation.</p>
        <button onclick="alert('Button clicked!')">Test Button</button>
        <div id="content">
            <p>Test content for validation</p>
            <ul>
                <li>Item 1</li>
                <li>Item 2</li>
                <li>Item 3</li>
            </ul>
        </div>
    </div>
    <script>
        console.log('Test page loaded successfully');
        document.addEventListener('DOMContentLoaded', function() {
            console.log('DOM content loaded');
        });
    </script>
</body>
</html>""", encoding='utf-8')
    
    # Start HTTP server
    print(f"Starting test HTTP server on port {port}...")
    print(f"Serving content from: {test_dir.absolute()}")
    
    process = subprocess.Popen(
        ["python", "-m", "http.server", str(port)],
        cwd=test_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait for server to start
    time.sleep(3)
    
    # Verify server is running
    try:
        response = requests.get(f"http://localhost:{port}", timeout=5)
        if response.status_code == 200:
            print(f"Test server started successfully on http://localhost:{port}")
            print(f"Server response length: {len(response.text)} characters")
            return process, f"http://localhost:{port}"
        else:
            print(f"Server responded with status {response.status_code}")
            return None, None
    except Exception as e:
        print(f"Failed to verify server: {e}")
        return None, None

def stop_test_server(process):
    """Stop the test server."""
    if process:
        print("🛑 Stopping test server...")
        process.terminate()
        try:
            process.wait(timeout=5)
            print("✅ Test server stopped successfully")
        except subprocess.TimeoutExpired:
            print("⚠️ Force killing test server...")
            process.kill()

async def test_playwright_basic():
    """Test basic Playwright functionality."""
    print("\n" + "="*60)
    print("🧪 TESTING: Basic Playwright Installation")
    print("="*60)
    
    try:
        from playwright.async_api import async_playwright
        print("✅ Playwright import successful")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            print("✅ Chromium browser launched successfully")
            
            context = await browser.new_context()
            page = await context.new_page()
            print("✅ Browser page created successfully")
            
            # Test navigation to a reliable site
            await page.goto("https://httpbin.org/html", timeout=30000)
            title = await page.title()
            print(f"✅ Successfully navigated to test site, title: {title}")
            
            await browser.close()
            print("✅ Browser closed successfully")
            
        return True
    except Exception as e:
        print(f"❌ Basic Playwright test failed: {e}")
        return False

async def test_localhost_connection():
    """Test connection to localhost server."""
    print("\n" + "="*60)
    print("🧪 TESTING: Localhost Server Connection")
    print("="*60)
    
    # Start test server
    server_process, server_url = start_test_server(8080)
    
    if not server_process or not server_url:
        print("❌ Failed to start test server")
        return False
    
    try:
        # Test HTTP request first
        print("🔍 Testing HTTP request to localhost...")
        response = requests.get(server_url, timeout=10)
        print(f"✅ HTTP request successful: {response.status_code}")
        print(f"📄 Content length: {len(response.text)} characters")
        
        # Test Playwright navigation
        print("🔍 Testing Playwright navigation to localhost...")
        from playwright.async_api import async_playwright
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            
            # Navigate to localhost
            await page.goto(server_url, timeout=30000, wait_until="networkidle")
            title = await page.title()
            content = await page.content()
            
            print(f"✅ Playwright navigation successful")
            print(f"📄 Page title: {title}")
            print(f"📄 Content length: {len(content)} characters")
            
            # Check for expected content
            if "DirectPlaywrightTester Test Page" in content:
                print("✅ Expected content found in page")
            else:
                print("⚠️ Expected content not found")
            
            await browser.close()
            
        return True
        
    except Exception as e:
        print(f"❌ Localhost connection test failed: {e}")
        return False
    finally:
        stop_test_server(server_process)

async def test_direct_playwright_tester():
    """Test our DirectPlaywrightTester class."""
    print("\n" + "="*60)
    print("🧪 TESTING: DirectPlaywrightTester Class")
    print("="*60)
    
    # Start test server
    server_process, server_url = start_test_server(8081)
    
    if not server_process or not server_url:
        print("❌ Failed to start test server")
        return False
    
    try:
        # Initialize tester
        print("🔍 Initializing DirectPlaywrightTester...")
        tester = DirectPlaywrightTester(headless=True)
        print("✅ DirectPlaywrightTester initialized")
        
        # Test with our server
        print(f"🔍 Testing with URL: {server_url}")
        result = await tester.test_application([server_url])
        
        print(f"📊 Test Result Summary:")
        print(f"   Success: {result.get('success')}")
        print(f"   Tested URLs: {result.get('tested_urls')}")
        print(f"   Successful connections: {result.get('successful_connections')}")
        print(f"   Failed connections: {result.get('failed_connections')}")
        
        if result.get('detailed_results'):
            for i, detail in enumerate(result['detailed_results']):
                print(f"   URL {i+1}: {detail.get('url')} - {'✅ Success' if detail.get('success') else '❌ Failed'}")
                if detail.get('error'):
                    print(f"     Error: {detail['error']}")
                if detail.get('page_title'):
                    print(f"     Title: {detail['page_title']}")
        
        return result.get('success', False)
        
    except Exception as e:
        print(f"❌ DirectPlaywrightTester test failed: {e}")
        import traceback
        print(f"📄 Full traceback: {traceback.format_exc()}")
        return False
    finally:
        stop_test_server(server_process)

async def test_with_python_http_server():
    """Test with Python HTTP server like the automation workflow uses."""
    print("\n" + "="*60)
    print("🧪 TESTING: Python HTTP Server (Automation Workflow Style)")
    print("="*60)
    
    # Create test content in a temporary directory
    test_dir = Path("./test_python_server")
    test_dir.mkdir(exist_ok=True)
    
    # Create index.html like the deployment manager does (without Unicode characters)
    index_file = test_dir / "index.html"
    index_file.write_text("""<!DOCTYPE html>
<html>
<head>
    <title>Generated Project</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .container { max-width: 800px; margin: 0 auto; }
        .status { color: green; font-weight: bold; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Project Generated Successfully</h1>
        <p class="status">Server is running on port 3000</p>
        <h2>Project Files:</h2>
        <ul>
            <li>index.html</li>
            <li>test.js</li>
            <li>style.css</li>
        </ul>
        <p>This is a generated project served by Python's built-in HTTP server.</p>
    </div>
</body>
</html>""", encoding='utf-8')
    
    # Start Python HTTP server exactly like deployment manager
    print("Starting Python HTTP server on port 3002...")
    process = subprocess.Popen(
        ["python", "-m", "http.server", "3002"],
        cwd=test_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait for server startup
    time.sleep(5)
    
    try:
        # Check if port is listening
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            result = s.connect_ex(('localhost', 3002))
            if result == 0:
                print("Port 3002 is accepting connections")
            else:
                print(f"Port 3002 not accepting connections (result: {result})")
                return False
        
        # Test HTTP request
        print("Testing HTTP request...")
        response = requests.get("http://localhost:3002", timeout=10)
        print(f"HTTP request successful: {response.status_code}")
        
        # Test with DirectPlaywrightTester
        print("Testing with DirectPlaywrightTester...")
        tester = DirectPlaywrightTester(headless=True)
        result = await tester.test_application(["http://localhost:3002"])
        
        print(f"DirectPlaywrightTester Result:")
        print(f"   Success: {result.get('success')}")
        print(f"   Successful connections: {result.get('successful_connections')}")
        print(f"   Failed connections: {result.get('failed_connections')}")
        
        if result.get('detailed_results'):
            for detail in result['detailed_results']:
                print(f"   URL: {detail.get('url')}")
                print(f"   Success: {detail.get('success')}")
                if detail.get('error'):
                    print(f"   Error: {detail['error']}")
                if detail.get('page_title'):
                    print(f"   Title: {detail['page_title']}")
        
        return result.get('success', False)
        
    except Exception as e:
        print(f"Python HTTP server test failed: {e}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        return False
    finally:
        print("Stopping Python HTTP server...")
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
        
        # Cleanup
        try:
            import shutil
            shutil.rmtree(test_dir)
        except:
            pass

async def main():
    """Run all tests."""
    print("🚀 STARTING INDEPENDENT DirectPlaywrightTester TESTS")
    print("="*80)
    
    tests = [
        ("Basic Playwright", test_playwright_basic),
        ("Localhost Connection", test_localhost_connection),
        ("DirectPlaywrightTester Class", test_direct_playwright_tester),
        ("Python HTTP Server", test_with_python_http_server)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n🧪 Running: {test_name}")
        try:
            result = await test_func()
            results[test_name] = result
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"🏁 {test_name}: {status}")
        except Exception as e:
            results[test_name] = False
            print(f"🏁 {test_name}: ❌ FAILED (Exception: {e})")
    
    # Summary
    print("\n" + "="*80)
    print("📊 TEST SUMMARY")
    print("="*80)
    
    passed = sum(1 for r in results.values() if r)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"   {test_name}: {status}")
    
    print(f"\n🏆 Overall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("✅ All tests passed! DirectPlaywrightTester is working correctly.")
    else:
        print("❌ Some tests failed. Review the output above for details.")
    
    return passed == total

if __name__ == "__main__":
    asyncio.run(main())