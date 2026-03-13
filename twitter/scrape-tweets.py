# -*- coding: utf-8 -*-
"""Scrape real tweets from finance accounts via Playwright"""
import asyncio, json, os, re
from pathlib import Path
os.chdir('C:/Users/firas/.openclaw/workspace')

STUDY_ACCOUNTS = ["unusual_whales", "DeItaone", "StockMKTNewz", "FinancialJuice"]

async def scrape_account(handle):
    from playwright.async_api import async_playwright
    tweets = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 900}
        )
        page = await ctx.new_page()
        try:
            await page.goto(f"https://x.com/{handle}", wait_until="domcontentloaded", timeout=20000)
            await asyncio.sleep(4)

            # Get tweet text elements
            tweet_els = await page.query_selector_all('[data-testid="tweetText"]')
            for el in tweet_els[:10]:
                text = await el.inner_text()
                if text and len(text) > 10:
                    tweets.append(text.strip()[:280])

            await page.screenshot(path=f"logs/study-{handle}.png")
        except Exception as e:
            print(f"  Error scraping @{handle}: {e}")
        finally:
            await browser.close()
    return tweets

async def scrape_all():
    results = {}
    for handle in STUDY_ACCOUNTS:
        print(f"Scraping @{handle}...")
        tweets = await scrape_account(handle)
        results[handle] = tweets
        if tweets:
            print(f"  Got {len(tweets)} tweets:")
            for t in tweets[:4]:
                print(f"    > {t[:120]}")
        else:
            print(f"  No tweets (login wall or blocked)")
        print()

    Path("logs/account-studies.json").write_text(json.dumps(results, indent=2))

    # Style analysis
    all_tweets = [t for tweets in results.values() for t in tweets]
    if all_tweets:
        print(f"\n=== PATTERNS ({len(all_tweets)} tweets studied) ===")
        short = [t for t in all_tweets if len(t) < 100]
        print(f"Short posts (<100 chars): {len(short)}/{len(all_tweets)} = {100*len(short)//max(len(all_tweets),1)}%")
        with_ticker = [t for t in all_tweets if '$' in t]
        print(f"With $TICKER: {len(with_ticker)}/{len(all_tweets)} = {100*len(with_ticker)//max(len(all_tweets),1)}%")
        print("\nShortest posts:")
        for t in sorted(short, key=len)[:5]:
            print(f"  [{len(t)}] {t}")

if __name__ == "__main__":
    asyncio.run(scrape_all())
