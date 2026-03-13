#!/usr/bin/env python3
"""
Generate Twitter posts from live market data
Optimized for stocks/finance niche, high engagement format
"""
import sys, json, random
from datetime import datetime
sys.path.insert(0, 'twitter')
from fetch_market_data import get_trending_tickers, get_top_movers, get_quote, get_news_headlines

def format_volume(vol):
    if not vol: return "N/A"
    if vol > 1_000_000: return f"{vol/1_000_000:.1f}M"
    if vol > 1_000: return f"{vol/1_000:.0f}K"
    return str(vol)

def format_mcap(mc):
    if not mc: return ""
    if mc > 1_000_000_000_000: return f"${mc/1_000_000_000_000:.2f}T"
    if mc > 1_000_000_000: return f"${mc/1_000_000_000:.1f}B"
    if mc > 1_000_000: return f"${mc/1_000_000:.0f}M"
    return f"${mc:,}"

def generate_premarket_post():
    gainers, losers = get_top_movers()
    trending = get_trending_tickers()
    ts = datetime.now().strftime("%b %d")

    lines = [f"🌅 PRE-MARKET MOVERS — {ts}\n"]
    if gainers:
        lines.append("📈 Top Gainers:")
        for g in gainers[:3]:
            lines.append(f"  ${g['symbol']} {g['change_pct']:+.1f}%")
    if losers:
        lines.append("\n📉 Top Losers:")
        for l in losers[:3]:
            lines.append(f"  ${l['symbol']} {l['change_pct']:+.1f}%")
    if trending:
        lines.append(f"\nTrending: {' '.join(['$'+t for t in trending[:4] if not t.endswith('-USD')])}")

    lines.append("\nMarket opens in less than 1 hour. 👀")
    return "\n".join(lines)

def generate_mover_breakdown(symbol: str):
    q = get_quote(symbol)
    if not q or not q.get("change_pct"):
        return None

    pct = q["change_pct"]
    price = q["price"]
    name = q.get("name", symbol)
    vol = q.get("volume")
    avg_vol = q.get("avg_volume")
    vol_ratio = round(vol/avg_vol, 1) if vol and avg_vol else None

    direction = "🚀" if pct > 0 else "🔻"
    action = "surging" if pct > 5 else "rallying" if pct > 2 else "sliding" if pct < -5 else "dropping"

    lines = [f"{direction} ${symbol} is {action} {pct:+.1f}% to ${price:.2f}"]
    if vol_ratio and vol_ratio > 1.5:
        lines.append(f"Volume: {format_volume(vol)} ({vol_ratio}x avg) — unusual activity")
    if q.get("market_cap"):
        lines.append(f"Market cap: {format_mcap(q['market_cap'])}")

    lines.append(f"\nWatch ${symbol} closely today.")
    if abs(pct) > 10:
        lines.append(f"Moves like this don't happen without a reason. 👀")

    return "\n".join(lines)

def generate_eod_recap():
    gainers, losers = get_top_movers()
    ts = datetime.now().strftime("%b %d")

    lines = [f"📊 MARKET CLOSE — {ts}\n"]
    if gainers:
        lines.append("Today's biggest winners:")
        for g in gainers[:3]:
            lines.append(f"  ✅ ${g['symbol']} {g['change_pct']:+.1f}%")
    if losers:
        lines.append("\nToday's biggest losers:")
        for l in losers[:3]:
            lines.append(f"  ❌ ${l['symbol']} {l['change_pct']:+.1f}%")

    lines.append("\nMarkets closed. See you at pre-market. 🔔")
    return "\n".join(lines)

def generate_trending_post():
    trending = get_trending_tickers()
    stocks = [t for t in trending if not t.endswith('-USD')][:5]
    if not stocks:
        return None

    lines = ["👀 What's trending on Wall Street right now:\n"]
    for sym in stocks:
        q = get_quote(sym)
        if q and q.get("change_pct") is not None:
            lines.append(f"${sym} — {q['change_pct']:+.1f}% | Vol: {format_volume(q.get('volume'))}")
    lines.append("\nWhich one are you watching? 👇")
    return "\n".join(lines)

def generate_news_post():
    news = get_news_headlines()
    if not news:
        return None
    item = news[0]
    title = item["title"]
    return f"🔔 {title}\n\nThis is the kind of news that moves markets. Watch how it plays out today. 👀\n\n$SPY $QQQ"

def get_post(post_type: str = "auto"):
    if post_type == "premarket":
        return generate_premarket_post()
    elif post_type == "trending":
        return generate_trending_post()
    elif post_type == "eod":
        return generate_eod_recap()
    elif post_type == "news":
        return generate_news_post()
    elif post_type == "auto":
        hour = datetime.now().hour
        if 6 <= hour <= 9: return generate_premarket_post()
        elif 9 <= hour <= 15: return generate_trending_post() or generate_mover_breakdown(get_trending_tickers()[0] if get_trending_tickers() else "SPY")
        else: return generate_eod_recap()
    return None

if __name__ == "__main__":
    post_type = sys.argv[1] if len(sys.argv) > 1 else "auto"
    post = get_post(post_type)
    if post:
        print("=== GENERATED POST ===")
        print(post)
        print(f"\n[{len(post)} chars]")
    else:
        print("Could not generate post")
