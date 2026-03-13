#!/usr/bin/env python3
"""
Main Twitter runner - generates + posts content on schedule
Run this on cron every 30 min during market hours
"""
import sys, os, json, asyncio
from datetime import datetime, timezone
from pathlib import Path
os.chdir('C:/Users/firas/.openclaw/workspace')

# Inline data fetching (no import issues)
import requests, warnings
warnings.filterwarnings('ignore')

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

def get_movers():
    gainers, losers = [], []
    for scrId, target in [("day_gainers", gainers), ("day_losers", losers)]:
        try:
            r = requests.get(
                f"https://query1.finance.yahoo.com/v1/finance/screener/predefined/saved?scrIds={scrId}&count=5",
                headers=HEADERS, timeout=8, verify=False
            )
            if r.status_code == 200:
                quotes = r.json().get("finance",{}).get("result",[{}])[0].get("quotes",[])
                for q in quotes[:5]:
                    target.append({
                        "symbol": q.get("symbol",""),
                        "name": q.get("shortName",""),
                        "price": q.get("regularMarketPrice",0),
                        "change_pct": q.get("regularMarketChangePercent",0),
                        "volume": q.get("regularMarketVolume",0),
                    })
        except: pass
    return gainers, losers

def get_trending():
    try:
        r = requests.get("https://query1.finance.yahoo.com/v1/finance/trending/US?count=10", headers=HEADERS, timeout=8, verify=False)
        if r.status_code == 200:
            quotes = r.json()["finance"]["result"][0]["quotes"]
            return [q["symbol"] for q in quotes if not q["symbol"].endswith("-USD")]
    except: pass
    return []

def fmt_vol(v):
    if not v: return ""
    if v > 1e9: return f"{v/1e9:.1f}B"
    if v > 1e6: return f"{v/1e6:.1f}M"
    return f"{v/1e3:.0f}K"

def build_post(post_type="movers"):
    gainers, losers = get_movers()
    trending = get_trending()
    now = datetime.now()
    date_str = now.strftime("%b %d")

    if post_type == "premarket":
        lines = [f"PRE-MARKET MOVERS - {date_str}", ""]
        if gainers:
            lines.append("Top Gainers:")
            for g in gainers[:4]:
                lines.append(f"  ${g['symbol']} {g['change_pct']:+.1f}%")
        if losers:
            lines.append("")
            lines.append("Top Losers:")
            for l in losers[:3]:
                lines.append(f"  ${l['symbol']} {l['change_pct']:+.1f}%")
        lines.append("")
        lines.append("Market opens soon. What are you watching? Follow for daily movers.")
        return "\n".join(lines)

    elif post_type == "breakdown" and gainers:
        top = gainers[0]
        sym = top['symbol']
        name = top['name'] or sym
        pct = top['change_pct']
        price = top['price']
        vol = fmt_vol(top['volume'])
        lines = [
            f"${sym} is up {pct:.0f}% today.",
            "",
            f"Price: ${price:.2f}",
            f"Volume: {vol}",
            "",
            f"Moves like this don't happen for no reason.",
            f"Keep ${sym} on your radar today."
        ]
        return "\n".join(lines)

    elif post_type == "trending" and trending:
        lines = ["Trending on Wall Street right now:", ""]
        for sym in trending[:6]:
            lines.append(f"${sym}")
        lines.append("")
        lines.append("Markets are paying attention to these. Are you?")
        lines.append("Follow for daily market coverage.")
        return "\n".join(lines)

    else:  # default movers
        lines = [f"MARKET MOVERS - {date_str}", ""]
        if gainers:
            lines.append("Winners:")
            for g in gainers[:3]:
                lines.append(f"${g['symbol']} +{g['change_pct']:.1f}%")
        if losers:
            lines.append("")
            lines.append("Losers:")
            for l in losers[:3]:
                lines.append(f"${l['symbol']} {l['change_pct']:.1f}%")
        lines.append("")
        lines.append("Follow for pre-market alerts, movers, and breaking news every day.")
        return "\n".join(lines)

async def post_to_twitter(tweet_text):
    from playwright.async_api import async_playwright

    EMAIL = "admin@narrately.ai"
    PASSWORD = "Claw999!"
    SESSION_FILE = Path("config/twitter-session.json")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 900}
        )
        page = await context.new_page()

        try:
            # Try session cookie
            if SESSION_FILE.exists():
                cookies = json.loads(SESSION_FILE.read_text())
                await context.add_cookies(cookies)

            await page.goto("https://x.com/home", wait_until="domcontentloaded", timeout=20000)
            await asyncio.sleep(3)

            # Login if needed
            if "login" in page.url or "flow" in page.url:
                print("Logging in...")
                await page.goto("https://x.com/i/flow/login", wait_until="domcontentloaded", timeout=20000)
                await asyncio.sleep(2)

                # Username
                try:
                    await page.fill('input[autocomplete="username"]', EMAIL)
                    await page.keyboard.press("Enter")
                    await asyncio.sleep(2)
                except:
                    inputs = await page.query_selector_all('input')
                    if inputs: await inputs[0].fill(EMAIL)
                    await page.keyboard.press("Enter")
                    await asyncio.sleep(2)

                # Unusual activity check
                try:
                    el = await page.query_selector('input[data-testid="ocfEnterTextTextInput"]')
                    if el:
                        await el.fill("jeeniferdq")
                        await page.keyboard.press("Enter")
                        await asyncio.sleep(2)
                except: pass

                # Password
                await page.fill('input[name="password"]', PASSWORD)
                await page.keyboard.press("Enter")
                await asyncio.sleep(5)

                cookies = await context.cookies()
                SESSION_FILE.write_text(json.dumps(cookies))
                print("Logged in, session saved")

            # Compose tweet
            await page.screenshot(path="logs/twitter-before-compose.png")

            # Click compose
            compose = await page.query_selector('[data-testid="SideNav_NewTweet_Button"]')
            if compose:
                await compose.click()
                await asyncio.sleep(2)
            else:
                await page.goto("https://x.com/compose/tweet", wait_until="domcontentloaded", timeout=15000)
                await asyncio.sleep(3)

            # Type tweet
            box = await page.query_selector('[data-testid="tweetTextarea_0"]')
            if not box:
                box = await page.query_selector('div[contenteditable="true"]')
            if not box:
                await page.screenshot(path="logs/twitter-no-textbox.png")
                return {"success": False, "error": "No tweet text box found"}

            await box.click()
            await asyncio.sleep(1)
            # Type character by character to avoid issues
            await page.keyboard.type(tweet_text, delay=20)
            await asyncio.sleep(2)

            await page.screenshot(path="logs/twitter-before-post.png")

            # Post
            btn = await page.query_selector('[data-testid="tweetButtonInline"]')
            if not btn:
                btn = await page.query_selector('[data-testid="tweetButton"]')
            if btn:
                await btn.click()
                await asyncio.sleep(4)
                # Save session
                cookies = await context.cookies()
                SESSION_FILE.write_text(json.dumps(cookies))
                await page.screenshot(path="logs/twitter-after-post.png")
                print(f"Posted successfully!")
                return {"success": True, "text": tweet_text}
            else:
                return {"success": False, "error": "Post button not found"}

        except Exception as e:
            await page.screenshot(path=f"logs/twitter-error.png")
            return {"success": False, "error": str(e)}
        finally:
            await browser.close()

if __name__ == "__main__":
    post_type = sys.argv[1] if len(sys.argv) > 1 else "movers"
    do_post = "--post" in sys.argv

    tweet = build_post(post_type)
    print("=== GENERATED TWEET ===")
    print(tweet)
    print(f"\n[{len(tweet)} chars]")

    if do_post:
        print("\nPosting to Twitter...")
        result = asyncio.run(post_to_twitter(tweet))
        print(f"Result: {result}")

        # Log it
        log_file = Path("logs/twitter-posts.json")
        log = []
        if log_file.exists():
            try: log = json.loads(log_file.read_text())
            except: pass
        log.append({"ts": datetime.now().isoformat(), "type": post_type, "text": tweet, "result": result})
        log_file.write_text(json.dumps(log, indent=2))
