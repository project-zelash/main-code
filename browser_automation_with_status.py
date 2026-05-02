#!/usr/bin/env python3
"""Playwright URL tester with human-readable progress output."""

import argparse
import asyncio
import json

from direct_browser_automation import test_url


async def run_with_status(url: str, headless: bool, timeout_ms: int) -> dict:
    print("START browser verification")
    print(f"URL {url}")
    result = await test_url(url, headless=headless, timeout_ms=timeout_ms)
    print("RESULT")
    print(json.dumps(result, indent=2))
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify a generated app in Chromium.")
    parser.add_argument("url", help="URL to verify")
    parser.add_argument("--headed", action="store_true", help="Run browser visibly")
    parser.add_argument("--timeout", type=int, default=30000)
    args = parser.parse_args()
    result = asyncio.run(run_with_status(args.url, headless=not args.headed, timeout_ms=args.timeout))
    raise SystemExit(0 if result.get("success") else 1)


if __name__ == "__main__":
    main()
