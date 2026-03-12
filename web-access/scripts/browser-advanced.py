#!/usr/bin/env python3
"""
browser-advanced.py - Enhanced browser automation with intelligent waiting
- Smart element detection
- Screenshot capture
- Form filling
- Cookie/session management
- JavaScript execution
"""

import json
import sys
import argparse
from playwright.sync_api import sync_playwright, expect
import time

def smart_browser_fetch(url, wait_for=None, take_screenshot=False, execute_js=None, timeout=30000):
    """
    Smart fetch with intelligent waiting and element detection
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_default_timeout(timeout)
        
        try:
            # Navigate
            print(f"[1] Navigating to {url}")
            page.goto(url, wait_until="domcontentloaded")
            
            # Wait for specific element if requested
            if wait_for:
                print(f"[2] Waiting for selector: {wait_for}")
                page.wait_for_selector(wait_for, timeout=timeout)
            
            # Wait for network to settle
            page.wait_for_load_state("networkidle", timeout=10000)
            
            # Execute JavaScript if provided
            if execute_js:
                print(f"[3] Executing JavaScript")
                result = page.evaluate(execute_js)
                print(f"    Result: {result}")
            
            # Take screenshot
            screenshot_path = None
            if take_screenshot:
                screenshot_path = "/tmp/screenshot.png"
                page.screenshot(path=screenshot_path)
                print(f"[4] Screenshot saved: {screenshot_path}")
            
            # Get page content
            html = page.content()
            
            # Get page metadata
            metadata = {
                "url": page.url,
                "title": page.title(),
                "html_length": len(html),
                "screenshot": screenshot_path,
                "success": True
            }
            
            browser.close()
            return html, metadata
            
        except Exception as e:
            browser.close()
            return None, {"error": str(e), "success": False}

def fill_and_submit_form(url, form_data, submit_selector="button[type='submit']", timeout=30000):
    """
    Fill out a form and submit it
    form_data: dict of {selector: value} pairs
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_default_timeout(timeout)
        
        try:
            page.goto(url, wait_until="domcontentloaded")
            
            # Fill form fields
            for selector, value in form_data.items():
                print(f"[1] Filling {selector} with {value}")
                page.fill(selector, value)
            
            # Submit
            print(f"[2] Submitting form")
            page.click(submit_selector)
            
            # Wait for response
            page.wait_for_load_state("networkidle", timeout=10000)
            
            result = {
                "final_url": page.url,
                "title": page.title(),
                "success": True
            }
            
            browser.close()
            return result
            
        except Exception as e:
            browser.close()
            return {"error": str(e), "success": False}

def extract_data_with_selectors(url, selectors, wait_for=None, timeout=30000):
    """
    Extract specific data from page using CSS selectors
    selectors: dict of {name: selector} pairs
    Returns: dict of {name: [values]} pairs
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_default_timeout(timeout)
        
        try:
            page.goto(url, wait_until="domcontentloaded")
            
            if wait_for:
                page.wait_for_selector(wait_for, timeout=timeout)
            
            page.wait_for_load_state("networkidle", timeout=10000)
            
            extracted = {}
            for name, selector in selectors.items():
                elements = page.query_selector_all(selector)
                values = []
                for elem in elements:
                    text = elem.text_content() if elem else None
                    if text:
                        values.append(text.strip())
                extracted[name] = values
            
            browser.close()
            return extracted
            
        except Exception as e:
            browser.close()
            return {"error": str(e)}

def main():
    parser = argparse.ArgumentParser(description="Advanced browser automation")
    parser.add_argument("url", help="URL to visit")
    parser.add_argument("--wait", help="CSS selector to wait for")
    parser.add_argument("--screenshot", action="store_true", help="Take screenshot")
    parser.add_argument("--js", help="JavaScript to execute")
    parser.add_argument("--form", help="JSON form data: {selector: value}")
    parser.add_argument("--extract", help="JSON selectors to extract: {name: selector}")
    parser.add_argument("--timeout", type=int, default=30000, help="Timeout in ms")
    
    args = parser.parse_args()
    
    # Simple fetch
    if not args.form and not args.extract:
        html, metadata = smart_browser_fetch(
            args.url,
            wait_for=args.wait,
            take_screenshot=args.screenshot,
            execute_js=args.js,
            timeout=args.timeout
        )
        
        if metadata.get("success"):
            print(json.dumps(metadata, indent=2))
        else:
            print(json.dumps(metadata, indent=2), file=sys.stderr)
            sys.exit(1)
    
    # Form submission
    elif args.form:
        form_data = json.loads(args.form)
        result = fill_and_submit_form(args.url, form_data, timeout=args.timeout)
        print(json.dumps(result, indent=2))
    
    # Data extraction
    elif args.extract:
        selectors = json.loads(args.extract)
        result = extract_data_with_selectors(args.url, selectors, wait_for=args.wait, timeout=args.timeout)
        print(json.dumps(result, indent=2))

if __name__ == '__main__':
    main()
