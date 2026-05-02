#!/usr/bin/env python3
"""Reusable Playwright smoke tester for generated Zelash applications."""

import argparse
import asyncio
import json
from pathlib import Path
from typing import Dict, Any


async def test_url(url: str, headless: bool = True, timeout_ms: int = 30000) -> Dict[str, Any]:
    from playwright.async_api import async_playwright

    output_dir = Path("automation_workspace") / "browser_screenshots"
    output_dir.mkdir(parents=True, exist_ok=True)
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=headless)
        page = await browser.new_page(viewport={"width": 1280, "height": 720})
        try:
            response = await page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
            await page.wait_for_load_state("networkidle", timeout=timeout_ms)
            title = await page.title()
            content = await page.content()
            screenshot = output_dir / "latest.png"
            await page.screenshot(path=str(screenshot), full_page=True)
            ok = bool(response and response.status < 400 and "<body" in content.lower())
            return {
                "success": ok,
                "url": url,
                "status_code": response.status if response else None,
                "title": title,
                "content_length": len(content),
                "screenshot": str(screenshot),
            }
        finally:
            await browser.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Test a generated application URL with Playwright.")
    parser.add_argument("url", help="URL to test, for example http://localhost:3000")
    parser.add_argument("--headed", action="store_true", help="Run browser visibly")
    parser.add_argument("--timeout", type=int, default=30000, help="Navigation timeout in milliseconds")
    args = parser.parse_args()
    result = asyncio.run(test_url(args.url, headless=not args.headed, timeout_ms=args.timeout))
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["success"] else 1)


if __name__ == "__main__":
    main()
