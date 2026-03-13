#!/usr/bin/env python3
"""Twitter poster - fixed timeouts"""
import sys, os, json, asyncio
from pathlib import Path
os.chdir('C:/Users/firas/.openclaw/workspace')

EMAIL = "admin@narrately.ai"
PASSWORD = "Claw999!"
SESSION_FILE = Path("config/twitter-session.json")

async def post(tweet_text):
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox","--disable-dev-shm-usage"])
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 900}
        )
        page = await context.new_page()

        try:
            # Load session if exists
            if SESSION_FILE.exists():
                await context.add_cookies(json.loads(SESSION_FILE.read_text()))

            print("Navigating to X...")
            await page.goto("https://x.com/home", wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(4)
            await page.screenshot(path="logs/tw1-home.png")

            if "login" in page.url or "flow" in page.url or "i/flow" in page.url:
                print("Need to login...")
                await page.goto("https://x.com/i/flow/login", wait_until="domcontentloaded", timeout=30000)
                await asyncio.sleep(3)
                await page.screenshot(path="logs/tw2-login.png")

                # Fill username
                await page.wait_for_selector('input[autocomplete="username"]', timeout=15000)
                await page.fill('input[autocomplete="username"]', EMAIL)
                await asyncio.sleep(1)
                await page.click('[data-testid="LoginForm_Login_Button"]')
                await asyncio.sleep(3)
                await page.screenshot(path="logs/tw3-after-email.png")

                # Check for unusual activity prompt
                try:
                    unusual = await page.query_selector('input[data-testid="ocfEnterTextTextInput"]')
                    if unusual:
                        print("Username verification needed")
                        await unusual.fill("jeeniferdq")
                        await page.click('[data-testid="ocfEnterTextNextButton"]')
                        await asyncio.sleep(2)
                except: pass

                # Password
                await page.wait_for_selector('input[name="password"]', timeout=10000)
                await page.fill('input[name="password"]', PASSWORD)
                await asyncio.sleep(1)
                await page.click('[data-testid="LoginForm_Login_Button"]')
                await asyncio.sleep(5)
                await page.screenshot(path="logs/tw4-after-login.png")
                print(f"After login URL: {page.url}")

                # Save session
                cookies = await context.cookies()
                SESSION_FILE.write_text(json.dumps(cookies))

            print("Composing tweet...")
            await page.screenshot(path="logs/tw5-home-loggedin.png")

            # Try compose button
            try:
                compose = await page.wait_for_selector('[data-testid="SideNav_NewTweet_Button"]', timeout=8000)
                await compose.click()
                await asyncio.sleep(2)
            except:
                await page.goto("https://x.com/compose/tweet", wait_until="domcontentloaded", timeout=15000)
                await asyncio.sleep(3)

            await page.screenshot(path="logs/tw6-compose.png")

            # Find text box
            box = None
            for selector in ['[data-testid="tweetTextarea_0"]', 'div[contenteditable="true"][role="textbox"]']:
                try:
                    box = await page.wait_for_selector(selector, timeout=8000)
                    if box: break
                except: pass

            if not box:
                await page.screenshot(path="logs/tw7-no-box.png")
                return {"success": False, "error": "No tweet input found", "url": page.url}

            await box.click()
            await asyncio.sleep(1)
            await page.keyboard.type(tweet_text, delay=30)
            await asyncio.sleep(2)
            await page.screenshot(path="logs/tw8-typed.png")

            # Post
            btn = None
            for sel in ['[data-testid="tweetButtonInline"]', '[data-testid="tweetButton"]']:
                try:
                    btn = await page.wait_for_selector(sel, timeout=5000)
                    if btn: break
                except: pass

            if not btn:
                return {"success": False, "error": "Post button not found"}

            await btn.click()
            await asyncio.sleep(5)
            await page.screenshot(path="logs/tw9-after-post.png")

            # Save updated session
            cookies = await context.cookies()
            SESSION_FILE.write_text(json.dumps(cookies))

            print("Posted!")
            return {"success": True, "url": page.url}

        except Exception as e:
            import traceback
            await page.screenshot(path="logs/tw-error.png")
            return {"success": False, "error": str(e), "trace": traceback.format_exc()[-300:]}
        finally:
            await browser.close()

if __name__ == "__main__":
    tweet = sys.argv[1] if len(sys.argv) > 1 else "PRE-MARKET MOVERS - Mar 13\n\nTop Gainers:\n$CE +14.7%\n$CF +13.2%\n$FLY +12.8%\n\nTop Losers:\n$NTSK -21.3%\n$GSIW -18.4%\n\nMarket opens in less than 3 hours. What are you watching?"
    result = asyncio.run(post(tweet))
    print(json.dumps(result, indent=2))
