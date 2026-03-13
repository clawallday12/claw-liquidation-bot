#!/usr/bin/env python3
"""Playwright reply engine with proper login flow"""
import asyncio, json, sys, os
from pathlib import Path
os.chdir('C:/Users/firas/.openclaw/workspace')

EMAIL = "admin@narrately.ai"
PASSWORD = "Claw999!"
SESSION_FILE = Path("config/twitter-session.json")

async def reply_to(tweet_url: str, reply_text: str, headless=True):
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless, args=["--no-sandbox"])
        ctx = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 900}
        )
        page = await ctx.new_page()
        try:
            # Load session
            if SESSION_FILE.exists():
                await ctx.add_cookies(json.loads(SESSION_FILE.read_text()))

            # Check login
            await page.goto("https://x.com/home", wait_until="domcontentloaded", timeout=20000)
            await asyncio.sleep(3)

            if "login" in page.url or "flow" in page.url:
                print("Logging in...")
                await page.goto("https://x.com/i/flow/login", wait_until="domcontentloaded", timeout=20000)
                await asyncio.sleep(3)
                inputs = await page.query_selector_all('input')
                if inputs: await inputs[0].fill(EMAIL)
                await page.keyboard.press("Enter")
                await asyncio.sleep(2)
                # Username check
                try:
                    oc = await page.query_selector('input[data-testid="ocfEnterTextTextInput"]')
                    if oc:
                        await oc.fill("jeeniferdq")
                        await page.keyboard.press("Enter")
                        await asyncio.sleep(2)
                except: pass
                pwd = await page.query_selector('input[type="password"]')
                if pwd:
                    await pwd.fill(PASSWORD)
                    await page.keyboard.press("Enter")
                    await asyncio.sleep(5)
                cookies = await ctx.cookies()
                SESSION_FILE.write_text(json.dumps(cookies))
                print("Logged in")

            # Go to the tweet
            print(f"Navigating to tweet...")
            await page.goto(tweet_url, wait_until="domcontentloaded", timeout=20000)
            await asyncio.sleep(4)
            await page.screenshot(path="logs/pw-reply-1.png")

            # Click the Reply button on the tweet
            reply_btn = await page.query_selector('[data-testid="reply"]')
            if reply_btn:
                await reply_btn.click()
                await asyncio.sleep(2)
                print("Clicked reply button")
            else:
                # Try finding reply via aria
                btns = await page.query_selector_all('[role="button"]')
                print(f"Found {len(btns)} buttons, looking for reply...")
                await page.screenshot(path="logs/pw-reply-2.png")

            await asyncio.sleep(2)
            await page.screenshot(path="logs/pw-reply-3.png")

            # Find the reply textarea
            box = None
            for sel in ['[data-testid="tweetTextarea_0"]', '[data-testid="tweetTextarea_0root"] div[contenteditable]', 'div[contenteditable="true"][role="textbox"]']:
                box = await page.query_selector(sel)
                if box:
                    print(f"Found textarea: {sel}")
                    break

            if not box:
                print("No textarea found")
                return {"success": False, "error": "No textarea"}

            await box.click()
            await asyncio.sleep(1)
            await page.keyboard.type(reply_text, delay=25)
            await asyncio.sleep(1)

            # Post button
            for sel in ['[data-testid="tweetButtonInline"]', '[data-testid="tweetButton"]']:
                btn = await page.query_selector(sel)
                if btn:
                    await btn.click()
                    await asyncio.sleep(4)
                    cookies = await ctx.cookies()
                    SESSION_FILE.write_text(json.dumps(cookies))
                    print(f"Reply posted: {reply_text}")
                    return {"success": True}

            return {"success": False, "error": "No post button"}

        except Exception as e:
            await page.screenshot(path="logs/pw-reply-error.png")
            return {"success": False, "error": str(e)[:100]}
        finally:
            await browser.close()

if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else "https://x.com/alphatrends/status/2032468876198846635"
    text = sys.argv[2] if len(sys.argv) > 2 else "$CL watching this VWAP level closely"
    result = asyncio.run(reply_to(url, text))
    print(result)
