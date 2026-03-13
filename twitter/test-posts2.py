#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys, os
os.chdir('C:/Users/firas/.openclaw/workspace')
exec(open('twitter/fetch-market-data.py').read())

trending = get_trending_tickers()
gainers, losers = get_top_movers()
stocks = [t for t in trending if not t.endswith('-USD')][:4]

def fmt(v):
    if not v: return 'N/A'
    if v > 1e6: return f'{v/1e6:.1f}M'
    return f'{v/1e3:.0f}K'

# Build posts without emoji (Windows console issue, emojis fine in actual tweets)
print("=== POST 1: TRENDING ===")
p1 = "Stocks trending on Wall Street right now:\n"
for sym in stocks:
    q = get_quote(sym)
    pct = q.get('change_pct') if q else None
    if pct is not None:
        p1 += f"\n${sym}  {pct:+.1f}% | Vol: {fmt(q.get('volume'))}"
p1 += "\n\nWhich are you watching? Drop it below"
print(p1)
print(f"[{len(p1)} chars]\n")

print("=== POST 2: TOP MOVERS ===")
p2 = "TOP MOVERS\n\nGainers:"
for g in gainers[:3]:
    p2 += f"\n${g['symbol']}  {g['change_pct']:+.1f}%"
p2 += "\n\nLosers:"
for l in losers[:3]:
    p2 += f"\n${l['symbol']}  {l['change_pct']:+.1f}%"
p2 += "\n\nMarkets move fast. Stay locked in."
print(p2)
print(f"[{len(p2)} chars]\n")

print("=== POST 3: SINGLE STOCK BREAKDOWN ===")
if gainers:
    top = gainers[0]
    q = get_quote(top['symbol'])
    if q:
        price = q.get('price', 0)
        vol = fmt(q.get('volume'))
        avg = fmt(q.get('avg_volume'))
        p3 = f"${top['symbol']} up {top['change_pct']:.1f}% today.\n\nPrice: ${price:.2f}\nVolume: {vol} (avg: {avg})\n\nSomething is moving here. Watch closely."
        print(p3)
        print(f"[{len(p3)} chars]")
