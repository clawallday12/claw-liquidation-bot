#!/usr/bin/env python3
"""
browser.py - Headless browser automation via Playwright
"""

import sys
import json
import argparse
from playwright.sync_api import sync_playwright

def browser_fetch(url, wait_selector=None, timeout=10000):
    """Fetch URL in headless browser, wait for selector if specified"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            page.goto(url, timeout=timeout)
            
            if wait_selector:
                page.wait_for_selector(wait_selector, timeout=timeout)
            
            content = page.content()
            browser.close()
            return content
        
        except Exception as e:
            browser.close()
            print(json.dumps({"error": str(e), "url": url}), file=sys.stderr)
            return None

def browser_click_and_fetch(url, selector, wait_selector=None, timeout=10000):
    """Navigate to URL, click element, wait for response"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            page.goto(url, timeout=timeout)
            page.click(selector)
            
            if wait_selector:
                page.wait_for_selector(wait_selector, timeout=timeout)
            else:
                page.wait_for_load_state('networkidle')
            
            content = page.content()
            browser.close()
            return content
        
        except Exception as e:
            browser.close()
            print(json.dumps({"error": str(e), "url": url, "selector": selector}), file=sys.stderr)
            return None

def main():
    parser = argparse.ArgumentParser(description="Browser automation")
    parser.add_argument('url', help="URL to fetch")
    parser.add_argument('--wait-selector', help="CSS selector to wait for")
    parser.add_argument('--click', help="CSS selector to click")
    parser.add_argument('--timeout', type=int, default=10000, help="Timeout in ms")
    args = parser.parse_args()
    
    if args.click:
        content = browser_click_and_fetch(args.url, args.click, args.wait_selector, args.timeout)
    else:
        content = browser_fetch(args.url, args.wait_selector, args.timeout)
    
    if content:
        print(content)
    else:
        sys.exit(1)

if __name__ == '__main__':
    main()
