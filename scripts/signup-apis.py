#!/usr/bin/env python3
"""
Autonomous API key acquisition via browser automation
Targets: Tavily, NewsAPI, Etherscan
"""
from playwright.sync_api import sync_playwright
import time, json, re

EMAIL = "clawallday12@gmail.com"
PASSWORD = "Claw999!"

def try_tavily(page):
    """Tavily - AI search API, free tier 1000 searches/month"""
    print("\n[TAVILY] Attempting signup...")
    try:
        page.goto("https://app.tavily.com/sign-up", timeout=15000)
        time.sleep(2)
        print(f"  Page: {page.title()} | {page.url}")
        
        # Check for Google auth button (faster than email)
        google_btn = page.query_selector("button:has-text('Google'), a:has-text('Google'), [data-provider='google']")
        if google_btn:
            print("  Found Google auth option")
        
        # Check for email field
        email_field = page.query_selector("input[type='email'], input[name='email'], input[placeholder*='email' i]")
        if email_field:
            email_field.fill(EMAIL)
            print(f"  Filled email: {EMAIL}")
            
            # Password field
            pass_field = page.query_selector("input[type='password']")
            if pass_field:
                pass_field.fill(PASSWORD)
                print("  Filled password")
            
            # Submit
            submit = page.query_selector("button[type='submit'], button:has-text('Sign up'), button:has-text('Create')")
            if submit:
                submit.click()
                time.sleep(3)
                print(f"  After submit: {page.url}")
                return page.url
        
        # Screenshot for debugging
        page.screenshot(path="logs/tavily-signup.png")
        print("  Screenshot saved")
        return None
    except Exception as e:
        print(f"  Error: {e}")
        return None

def try_newsapi(page):
    """NewsAPI - free 100 requests/day"""
    print("\n[NEWSAPI] Attempting signup...")
    try:
        page.goto("https://newsapi.org/register", timeout=15000)
        time.sleep(2)
        print(f"  Page: {page.title()} | {page.url}")
        
        # Get all fields
        inputs = page.query_selector_all("input")
        fields = {}
        for inp in inputs:
            name = inp.get_attribute("name") or inp.get_attribute("id") or ""
            itype = inp.get_attribute("type") or "text"
            fields[name] = itype
        print(f"  Fields found: {fields}")
        
        # Fill form
        for sel in ["input[name='firstName'], input[id='firstName'], input[placeholder*='first' i]"]:
            el = page.query_selector(sel)
            if el:
                el.fill("Claw")
                break
        
        email_field = page.query_selector("input[type='email'], input[name='email']")
        if email_field:
            email_field.fill(EMAIL)
            print(f"  Filled email")
        
        pass_field = page.query_selector("input[type='password']")
        if pass_field:
            pass_field.fill(PASSWORD)
        
        submit = page.query_selector("button[type='submit'], input[type='submit']")
        if submit:
            submit.click()
            time.sleep(3)
            print(f"  After submit: {page.url}")
            
            # Look for API key on success page
            body = page.content()
            key_match = re.search(r'[a-f0-9]{32}', body)
            if key_match:
                print(f"  POTENTIAL API KEY: {key_match.group()}")
                return key_match.group()
        
        page.screenshot(path="logs/newsapi-signup.png")
        return None
    except Exception as e:
        print(f"  Error: {e}")
        return None

def try_coinglass(page):
    """Coinglass - free crypto derivatives data"""
    print("\n[COINGLASS] Checking free API...")
    try:
        # Try public API first
        import requests, warnings
        warnings.filterwarnings('ignore')
        r = requests.get("https://open-api.coinglass.com/public/v2/funding?symbol=BTC", 
                        headers={"coinglassSecret": ""}, timeout=5, verify=False)
        print(f"  Status: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            print(f"  Public API works! Keys: {list(data.keys())[:5]}")
            return "public_no_key"
    except Exception as e:
        print(f"  Error: {e}")
    return None

import os
os.makedirs("logs", exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    )
    page = context.new_page()
    
    results = {}
    
    # Try each API
    results["tavily"] = try_tavily(page)
    results["newsapi"] = try_newsapi(page)
    results["coinglass"] = try_coinglass(page)
    
    browser.close()

print("\n=== RESULTS ===")
print(json.dumps(results, indent=2))

# Save any found keys
import pathlib
pathlib.Path("config/api-keys.json").write_text(json.dumps(results, indent=2))
print("Keys saved to config/api-keys.json")
