#!/usr/bin/env python3
import sys, os, json, asyncio
from pathlib import Path
os.chdir('C:/Users/firas/.openclaw/workspace')

EMAIL = "admin@narrately.ai"
PASSWORD = "Claw999!"
SESSION_FILE = Path("config/twitter-session.json")

async def post(tweet_text):
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 900}
        )
        page = await context.new_page()

        try:
            if SESSION_FILE.exists():
                await context.add_cookies(json.loads(SESSION_FILE.read_text()))

            await page.goto("https://x.com/home", wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(5)

            if "login" in page.url or "flow" in page.url:
                print("Logging in...")
                await page.goto("https://x.com/i/flow/login", wait_until="domcontentloaded", timeout=30000)
                await asyncio.sleep(4)

                # Use the visible input - it has placeholder "Phone, email, or username"
                inputs = await page.query_selector_all('input')
                print(f"Found {len(inputs)} inputs")
                if inputs:
                    await inputs[0].fill(EMAIL)
                else:
                    # Try by placeholder
                    await page.fill('input[placeholder*="email"]', EMAIL)
                await asyncio.sleep(1)

                # Click Next button
                next_btns = await page.query_selector_all('button')
                for btn in next_btns:
                    text = await btn.inner_text()
                    if 'next' in text.lower():
                        await btn.click()
                        break
                else:
                    await page.keyboard.press("Enter")
                await asyncio.sleep(3)
                await page.screenshot(path="logs/tw-after-email.png")

                # Username verification if triggered
                inputs2 = await page.query_selector_all('input')
                current_url = page.url
                print(f"URL after email: {current_url}")
                if 'username' in await page.content() or 'Enter your phone' in await page.content():
                    print("Username check triggered")
                    if inputs2:
                        await inputs2[0].fill("jeeniferdq")
                        await page.keyboard.press("Enter")
                        await asyncio.sleep(2)

                # Password
                await asyncio.sleep(2)
                pwd_inputs = await page.query_selector_all('input[type="password"]')
                if pwd_inputs:
                    await pwd_inputs[0].fill(PASSWORD)
                    await page.keyboard.press("Enter")
                    await asyncio.sleep(5)
                    print("Password entered")
                else:
                    print("ERROR: No password field found")
                    await page.screenshot(path="logs/tw-no-pwd.png")
                    return {"success": False, "error": "No password field"}

                await page.screenshot(path="logs/tw-after-login.png")
                print(f"Post-login URL: {page.url}")

                cookies = await context.cookies()
                SESSION_FILE.write_text(json.dumps(cookies))

            # Compose
            print("Going to compose...")
            await page.goto("https://x.com/compose/tweet", wait_until="domcontentloaded", timeout=20000)
            await asyncio.sleep(4)
            await page.screenshot(path="logs/tw-compose.png")
            print(f"Compose URL: {page.url}")

            # Find textarea
            box = None
            for sel in ['[data-testid="tweetTextarea_0"]', 'div[contenteditable="true"]', '[role="textbox"]']:
                box = await page.query_selector(sel)
                if box:
                    print(f"Found box with: {sel}")
                    break

            if not box:
                print("No text box — checking all contenteditable elements")
                els = await page.query_selector_all('[contenteditable]')
                print(f"Contenteditable elements: {len(els)}")
                if els:
                    box = els[0]

            if not box:
                await page.screenshot(path="logs/tw-nobox.png")
                return {"success": False, "error": "No tweet box", "url": page.url}

            await box.click()
            await asyncio.sleep(1)
            await page.keyboard.type(tweet_text, delay=25)
            await asyncio.sleep(2)
            await page.screenshot(path="logs/tw-typed.png")

            # Post button
            for sel in ['[data-testid="tweetButtonInline"]', '[data-testid="tweetButton"]']:
                btn = await page.query_selector(sel)
                if btn:
                    await btn.click()
                    await asyncio.sleep(5)
                    await page.screenshot(path="logs/tw-posted.png")
                    cookies = await context.cookies()
                    SESSION_FILE.write_text(json.dumps(cookies))
                    return {"success": True, "final_url": page.url}

            return {"success": False, "error": "Post button not found", "url": page.url}

        except Exception as e:
            import traceback
            try: await page.screenshot(path="logs/tw-exception.png")
            except: pass
            return {"success": False, "error": str(e)[-200:]}
        finally:
            await browser.close()

if __name__ == "__main__":
    tweet = sys.argv[1] if len(sys.argv) > 1 else "PRE-MARKET MOVERS - Mar 13\n\nTop Gainers:\n$CE +14.7%\n$CF +13.2%\n$FLY +12.8%\n\nTop Losers:\n$NTSK -21.3%\n$GSIW -18.4%\n\nMarket opens in less than 3 hours. What are you watching? Follow for daily coverage."
    result = asyncio.run(post(tweet))
    print(json.dumps(result, indent=2))
