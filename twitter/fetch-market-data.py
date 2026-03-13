#!/usr/bin/env python3
"""Fetch real market data for Twitter posts - no API keys needed"""
import requests, json, warnings
warnings.filterwarnings('ignore')

def get_trending_tickers():
    """Yahoo Finance trending tickers"""
    try:
        r = requests.get(
            "https://query1.finance.yahoo.com/v1/finance/trending/US?count=10",
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=8, verify=False
        )
        if r.status_code == 200:
            data = r.json()
            quotes = data["finance"]["result"][0]["quotes"]
            return [q["symbol"] for q in quotes[:10]]
    except: pass
    return []

def get_quote(symbol):
    """Yahoo Finance quote"""
    try:
        r = requests.get(
            f"https://query1.finance.yahoo.com/v2/finance/quote?symbols={symbol}",
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=8, verify=False
        )
        if r.status_code == 200:
            result = r.json()["quoteResponse"]["result"]
            if result:
                q = result[0]
                return {
                    "symbol": q.get("symbol"),
                    "name": q.get("shortName", ""),
                    "price": q.get("regularMarketPrice"),
                    "change": q.get("regularMarketChange"),
                    "change_pct": q.get("regularMarketChangePercent"),
                    "volume": q.get("regularMarketVolume"),
                    "avg_volume": q.get("averageDailyVolume3Month"),
                    "market_cap": q.get("marketCap"),
                    "pre_market": q.get("preMarketPrice"),
                    "pre_market_change_pct": q.get("preMarketChangePercent"),
                }
    except: pass
    return {}

def get_market_summary():
    """SPY, QQQ, DIA, VIX"""
    indices = ["^GSPC", "^IXIC", "^DJI", "^VIX", "SPY", "QQQ"]
    results = {}
    for sym in indices:
        q = get_quote(sym)
        if q:
            results[sym] = q
    return results

def get_top_movers():
    """Top gainers/losers"""
    gainers, losers = [], []
    try:
        r = requests.get(
            "https://query1.finance.yahoo.com/v1/finance/screener/predefined/saved?scrIds=day_gainers&count=5",
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=8, verify=False
        )
        if r.status_code == 200:
            quotes = r.json().get("finance",{}).get("result",[{}])[0].get("quotes",[])
            gainers = [{"symbol": q["symbol"], "change_pct": q.get("regularMarketChangePercent",0), "price": q.get("regularMarketPrice")} for q in quotes[:5]]
    except: pass
    try:
        r = requests.get(
            "https://query1.finance.yahoo.com/v1/finance/screener/predefined/saved?scrIds=day_losers&count=5",
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=8, verify=False
        )
        if r.status_code == 200:
            quotes = r.json().get("finance",{}).get("result",[{}])[0].get("quotes",[])
            losers = [{"symbol": q["symbol"], "change_pct": q.get("regularMarketChangePercent",0), "price": q.get("regularMarketPrice")} for q in quotes[:5]]
    except: pass
    return gainers, losers

def get_news_headlines():
    """Yahoo Finance news"""
    try:
        r = requests.get(
            "https://query1.finance.yahoo.com/v2/finance/news?count=10",
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=8, verify=False
        )
        if r.status_code == 200:
            items = r.json().get("items", {}).get("result", [])
            return [{"title": i.get("title"), "summary": i.get("summary","")[:150]} for i in items[:10]]
    except: pass
    # fallback: CryptoCompare for general finance news
    try:
        r = requests.get("https://min-api.cryptocompare.com/data/v2/news/?lang=EN&categories=Market", timeout=6, verify=False)
        if r.status_code == 200:
            return [{"title": a["title"]} for a in r.json().get("Data", [])[:10]]
    except: pass
    return []

if __name__ == "__main__":
    print("=== MARKET DATA TEST ===\n")
    print("[Trending tickers]")
    tickers = get_trending_tickers()
    print(tickers)

    print("\n[Market summary]")
    summary = get_market_summary()
    for sym, data in summary.items():
        if data.get("change_pct") is not None:
            print(f"  {sym}: ${data.get('price',0):.2f} ({data.get('change_pct',0):+.2f}%)")

    print("\n[Top movers]")
    gainers, losers = get_top_movers()
    print("Gainers:", [(g["symbol"], f"{g['change_pct']:+.1f}%") for g in gainers])
    print("Losers: ", [(l["symbol"], f"{l['change_pct']:+.1f}%") for l in losers])

    print("\n[News]")
    news = get_news_headlines()
    for n in news[:5]:
        print(f"  - {n['title']}")
