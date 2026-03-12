#!/usr/bin/env python3
"""
Check Gmail for verification emails from API signups
Use Playwright to read Gmail inbox
"""
from playwright.sync_api import sync_playwright
import time, re, json

EMAIL = "clawallday12@gmail.com"
PASSWORD = "Claw999!"

def check_gmail_for_keys():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0"
        )
        page = context.new_page()
        
        print("[1] Navigating to Gmail...")
        page.goto("https://accounts.google.com/signin/v2/identifier", timeout=15000)
        time.sleep(2)
        
        # Fill email
        email_field = page.query_selector("input[type='email']")
        if email_field:
            email_field.fill(EMAIL)
            page.keyboard.press("Enter")
            time.sleep(2)
            print("  Email entered")
        
        # Fill password
        pass_field = page.query_selector("input[type='password']")
        if pass_field:
            pass_field.fill(PASSWORD)
            page.keyboard.press("Enter")
            time.sleep(3)
            print("  Password entered")
        
        print(f"  After login: {page.url}")
        page.screenshot(path="logs/gmail-login.png")
        
        # Navigate to Gmail inbox
        page.goto("https://mail.google.com/mail/u/0/#inbox", timeout=15000)
        time.sleep(4)
        print(f"  Gmail URL: {page.url}")
        page.screenshot(path="logs/gmail-inbox.png")
        
        # Look for emails from API services
        emails = page.query_selector_all("tr.zA")
        print(f"  Found {len(emails)} emails in inbox")
        
        for email in emails[:10]:
            text = email.text_content()
            if any(kw in text.lower() for kw in ['newsapi', 'tavily', 'etherscan', 'api', 'verify', 'confirm', 'key']):
                print(f"  RELEVANT: {text[:100]}")
                email.click()
                time.sleep(2)
                body = page.content()
                
                # Look for API keys
                key_patterns = [
                    r'[a-f0-9]{32}',  # MD5-style
                    r'tvly-[a-zA-Z0-9]{32,}',  # Tavily
                    r'[a-zA-Z0-9]{40}',  # Generic long key
                ]
                for pattern in key_patterns:
                    matches = re.findall(pattern, body)
                    if matches:
                        print(f"  POTENTIAL KEY: {matches[0]}")
                
                page.go_back()
                time.sleep(1)
        
        browser.close()

check_gmail_for_keys()
print("Done. Check logs/ for screenshots")
