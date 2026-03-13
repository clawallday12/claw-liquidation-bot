#!/usr/bin/env python3
import sys
sys.path.insert(0, 'twitter')
from fetch_market_data import get_trending_tickers, get_top_movers, get_quote

def fmt_vol(v):
    if not v: return "N/A"
    if v > 1e6: return f"{v/1e6:.1f}M"
    return f"{v/1e3:.0f}K"

trending = get_trending_tickers()
gainers, losers = get_top_movers()
stocks = [t for t in trending if not t.endswith('-USD')][:4]

print("=== POST 1: TRENDING NOW ===")
post1 = "What's trending on Wall Street right now:\n"
for sym in stocks:
    q = get_quote(sym)
    if q and q.get('change_pct') is not None:
        post1 += f"\n${sym} {q['change_pct']:+.1f}% | Vol: {fmt_vol(q.get('volume'))}"
post1 += "\n\nWhich one are you watching? Drop it below 👇"
print(post1)
print(f"[{len(post1)} chars]\n")

print("=== POST 2: TOP MOVERS ===")
post2 = "TOP MOVERS TODAY\n"
if gainers:
    post2 += "\nGainers:\n"
    for g in gainers[:3]:
        post2 += f"${g['symbol']} {g['change_pct']:+.1f}%\n"
if losers:
    post2 += "\nLosers:\n"
    for l in losers[:3]:
        post2 += f"${l['symbol']} {l['change_pct']:+.1f}%\n"
post2 += "\nMarkets don't sleep. Neither should your watchlist."
print(post2)
print(f"[{len(post2)} chars]\n")

print("=== POST 3: SINGLE STOCK BREAKDOWN ===")
if gainers:
    top = gainers[0]
    sym = top['symbol']
    q = get_quote(sym)
    if q:
        post3 = f"${sym} is up {top['change_pct']:.1f}% today.\n\n"
        post3 += f"Price: ${q.get('price', 0):.2f}\n"
        post3 += f"Volume: {fmt_vol(q.get('volume'))} (avg: {fmt_vol(q.get('avg_volume'))})\n"
        post3 += f"\nSomething is happening here. Keep it on your radar."
        print(post3)
        print(f"[{len(post3)} chars]")
