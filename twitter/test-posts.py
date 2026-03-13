#!/usr/bin/env python3
import sys, os
os.chdir('C:/Users/firas/.openclaw/workspace')
exec(open('twitter/fetch-market-data.py').read())

trending = get_trending_tickers()
gainers, losers = get_top_movers()
stocks = [t for t in trending if not t.endswith('-USD')][:4]

def fmt(v):
    if not v: return 'N/A'
    return f'{v/1e6:.1f}M' if v > 1e6 else f'{v/1e3:.0f}K'

# Post 1: Trending
lines = ['Stocks trending on Wall Street right now:\n']
for sym in stocks:
    q = get_quote(sym)
    if q and q.get('change_pct') is not None:
        lines.append(f'${sym} {q["change_pct"]:+.1f}% | Vol: {fmt(q.get("volume"))}')
lines.append('\nWhich are you watching? Drop it below 👇')
p1 = '\n'.join(lines)
print('=== POST 1: TRENDING ===')
print(p1)
print(f'[{len(p1)} chars]\n')

# Post 2: Top movers
lines2 = ['TOP MOVERS\n']
if gainers:
    lines2.append('Gainers:')
    for g in gainers[:3]:
        lines2.append(f'  ${g["symbol"]} {g["change_pct"]:+.1f}%')
if losers:
    lines2.append('\nLosers:')
    for l in losers[:3]:
        lines2.append(f'  ${l["symbol"]} {l["change_pct"]:+.1f}%')
lines2.append('\nMarkets move fast. Stay locked in. 🎯')
p2 = '\n'.join(lines2)
print('=== POST 2: MOVERS ===')
print(p2)
print(f'[{len(p2)} chars]\n')

# Post 3: Single stock breakdown
if gainers:
    top = gainers[0]
    q = get_quote(top['symbol'])
    if q:
        p3_lines = [
            f'${top["symbol"]} up {top["change_pct"]:.1f}% today.',
            '',
            f'Price: ${q.get("price",0):.2f}',
            f'Volume: {fmt(q.get("volume"))} (avg {fmt(q.get("avg_volume"))})',
            '',
            'Something is happening here. Watch closely. 👀'
        ]
        p3 = '\n'.join(p3_lines)
        print('=== POST 3: STOCK BREAKDOWN ===')
        print(p3)
        print(f'[{len(p3)} chars]')
