#!/usr/bin/env python3
"""
Grab stock chart screenshots for Twitter posts
Uses TradingView lightweight charts via Playwright
"""
import asyncio, sys, os, json
from pathlib import Path
os.chdir('C:/Users/firas/.openclaw/workspace')

async def grab_chart(symbol: str, period: str = "1D") -> str:
    """Returns path to saved chart PNG"""
    from playwright.async_api import async_playwright
    out = Path(f"logs/chart-{symbol}.png")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 900, "height": 500})
        page = await context.new_page()

        # Use Yahoo Finance chart - clean, no login needed
        url = f"https://finance.yahoo.com/chart/{symbol}"
        await page.goto(url, wait_until="domcontentloaded", timeout=20000)
        await asyncio.sleep(4)

        # Try to get just the chart area
        try:
            chart = await page.query_selector('[data-testid="chart-container"]')
            if chart:
                await chart.screenshot(path=str(out))
            else:
                # Fallback: screenshot the whole page
                await page.screenshot(path=str(out), clip={"x": 0, "y": 100, "width": 900, "height": 450})
        except:
            await page.screenshot(path=str(out))

        await browser.close()
        print(f"Chart saved: {out}")
        return str(out)

async def grab_finviz_chart(symbol: str) -> str:
    """Finviz chart - simpler, always works"""
    import requests, warnings
    warnings.filterwarnings('ignore')
    out = Path(f"logs/chart-{symbol}.png")
    url = f"https://finviz.com/chart.ashx?t={symbol}&ty=c&ta=1&p=d&s=l"
    H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36", "Referer": "https://finviz.com"}
    r = requests.get(url, headers=H, timeout=10, verify=False)
    if r.status_code == 200 and len(r.content) > 1000:
        out.write_bytes(r.content)
        print(f"Finviz chart saved: {out} ({len(r.content)/1024:.0f}KB)")
        return str(out)
    print(f"Failed: {r.status_code}")
    return None

if __name__ == "__main__":
    sym = sys.argv[1] if len(sys.argv) > 1 else "CE"
    # Try finviz first (no Playwright needed)
    result = asyncio.run(grab_finviz_chart(sym))
    if not result:
        result = asyncio.run(grab_chart(sym))
    print("Chart path:", result)
