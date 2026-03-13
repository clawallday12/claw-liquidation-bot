#!/usr/bin/env python3
"""
Twitter auto-poster via Playwright browser automation
Account: @jeeniferdq
"""
import asyncio, sys, os, json, warnings
from datetime import datetime
from pathlib import Path
warnings.filterwarnings('ignore')

EMAIL = "admin@narrately.ai"
PASSWORD = "Claw999!"
HANDLE = "jeeniferdq"
LOG_FILE = Path("logs/twitter-posts.json")
LOG_FILE.parent.mkdir(exist_ok=True)

async def post_tweet(text: str, headless: bool = True) -> dict:
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800}
        )
        page = await context.new_page()

        try:
            # Check if already logged in via saved state
            state_file = Path("config/twitter-session.json")

            if state_file.exists():
                await context.add_cookies(json.loads(state_file.read_text()))
                await page.goto("https://twitter.com/compose/tweet", wait_until="networkidle", timeout=15000)
                await asyncio.sleep(2)
                if "login" not in page.url.lower():
                    return await _compose_tweet(page, context, text, state_file)

            # Login flow
            print("Logging in...")
            await page.goto("https://x.com/i/flow/login", wait_until="networkidle", timeout=15000)
            await asyncio.sleep(2)

            # Enter email/username
            await page.fill('input[autocomplete="username"]', EMAIL)
            await page.keyboard.press("Enter")
            await asyncio.sleep(2)

            # Handle username check if prompted
            try:
                unusual = await page.query_selector('input[data-testid="ocfEnterTextTextInput"]')
                if unusual:
                    await unusual.fill(HANDLE)
                    await page.keyboard.press("Enter")
                    await asyncio.sleep(2)
            except: pass

            # Enter password
            await page.fill('input[name="password"]', PASSWORD)
            await page.keyboard.press("Enter")
            await asyncio.sleep(4)

            # Save cookies
            cookies = await context.cookies()
            state_file.write_text(json.dumps(cookies))
            print(f"Logged in, session saved")

            # Navigate to compose
            await page.goto("https://x.com/compose/tweet", wait_until="networkidle", timeout=15000)
            await asyncio.sleep(2)

            return await _compose_tweet(page, context, text, state_file)

        except Exception as e:
            screenshot = f"logs/twitter-error-{datetime.now().strftime('%H%M%S')}.png"
            await page.screenshot(path=screenshot)
            await browser.close()
            return {"success": False, "error": str(e), "screenshot": screenshot}

        finally:
            await browser.close()

async def _compose_tweet(page, context, text: str, state_file) -> dict:
    """Actually compose and send the tweet"""
    try:
        await asyncio.sleep(2)

        # Find tweet input
        tweet_box = await page.query_selector('[data-testid="tweetTextarea_0"]')
        if not tweet_box:
            tweet_box = await page.query_selector('div[contenteditable="true"]')
        if not tweet_box:
            screenshot = f"logs/twitter-nobox-{datetime.now().strftime('%H%M%S')}.png"
            await page.screenshot(path=screenshot)
            return {"success": False, "error": "No tweet box found", "screenshot": screenshot}

        await tweet_box.click()
        await tweet_box.fill(text)
        await asyncio.sleep(1)

        # Click Post button
        post_btn = await page.query_selector('[data-testid="tweetButtonInline"]')
        if not post_btn:
            post_btn = await page.query_selector('[data-testid="tweetButton"]')
        if not post_btn:
            return {"success": False, "error": "No post button found"}

        await post_btn.click()
        await asyncio.sleep(3)

        # Save updated session
        cookies = await context.cookies()
        state_file.write_text(json.dumps(cookies))

        # Log the post
        log = []
        if LOG_FILE.exists():
            try: log = json.loads(LOG_FILE.read_text())
            except: pass
        entry = {"ts": datetime.now().isoformat(), "text": text, "success": True}
        log.append(entry)
        LOG_FILE.write_text(json.dumps(log, indent=2))

        print(f"Posted: {text[:80]}...")
        return {"success": True, "text": text}

    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    tweet = sys.argv[1] if len(sys.argv) > 1 else None
    if not tweet:
        print("Usage: python post-tweet.py \"tweet text\"")
        sys.exit(1)
    result = asyncio.run(post_tweet(tweet))
    print(json.dumps(result, indent=2))
