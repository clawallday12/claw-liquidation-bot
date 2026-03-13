#!/usr/bin/env python3
"""
@jeeniferdq automated Twitter engine
- Pulls real market data
- Generates optimized posts
- Posts via Twitter API v2
- Tracks all posts and metrics
"""
import json, sys, os, requests, warnings, random
from datetime import datetime
from pathlib import Path
import tweepy

os.chdir('C:/Users/firas/.openclaw/workspace')
warnings.filterwarnings('ignore')

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
LOG = Path("logs/twitter-posts.json")
LOG.parent.mkdir(exist_ok=True)

# --- AUTH ---
def get_client():
    creds = json.loads(Path("config/twitter-api.json").read_text())
    return tweepy.Client(
        consumer_key=creds["consumer_key"],
        consumer_secret=creds["consumer_secret"],
        access_token=creds["access_token"],
        access_token_secret=creds["access_token_secret"],
        wait_on_rate_limit=True
    )

# --- DATA ---
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

# --- POST GENERATORS ---
def post_premarket():
    gainers, losers = get_movers()
    date = datetime.now().strftime("%b %d")
    lines = [f"PRE-MARKET MOVERS — {date}", ""]
    if gainers:
        lines.append("Gainers:")
        for g in gainers[:4]:
            lines.append(f"  ${g['symbol']} {g['change_pct']:+.1f}%")
    if losers:
        lines.append("")
        lines.append("Losers:")
        for l in losers[:3]:
            lines.append(f"  ${l['symbol']} {l['change_pct']:+.1f}%")
    lines += ["", "Market opens in 90 min.", "Follow for daily coverage. 🔔"]
    return "\n".join(lines), "premarket"

def post_movers():
    gainers, losers = get_movers()
    date = datetime.now().strftime("%b %d")
    lines = [f"MARKET MOVERS — {date}", ""]
    if gainers:
        lines.append("Top Gainers:")
        for g in gainers[:4]:
            lines.append(f"  ${g['symbol']} {g['change_pct']:+.1f}%")
    if losers:
        lines.append("")
        lines.append("Top Losers:")
        for l in losers[:3]:
            lines.append(f"  ${l['symbol']} {l['change_pct']:+.1f}%")
    lines += ["", "Follow for real-time movers every day. 🎯"]
    return "\n".join(lines), "movers"

def post_breakdown():
    gainers, _ = get_movers()
    if not gainers:
        return None, None
    top = gainers[0]
    sym, pct, price = top['symbol'], top['change_pct'], top['price']
    vol = fmt_vol(top['volume'])
    templates = [
        f"${sym} is up {pct:.0f}% today.\n\nPrice: ${price:.2f}\nVolume: {vol}\n\nSomething is moving here. What's your take? 👇",
        f"${sym} ripping {pct:.0f}% — here's what you need to know:\n\n• Price: ${price:.2f}\n• Volume: {vol}\n\nBig moves don't happen for no reason.",
        f"Eye on ${sym} today.\n\n{pct:.0f}% move. Volume at {vol}.\n\nThis is the kind of action that creates opportunities.",
    ]
    return random.choice(templates), "breakdown"

def post_trending():
    trending = get_trending()
    stocks = [t for t in trending if not t.endswith('-USD')][:6]
    if not stocks:
        return None, None
    lines = ["Trending on Wall Street right now:", ""]
    lines += [f"${s}" for s in stocks]
    lines += ["", "Which one are you watching? 👇", "Follow for daily market coverage."]
    return "\n".join(lines), "trending"

def post_eod():
    gainers, losers = get_movers()
    date = datetime.now().strftime("%b %d")
    lines = [f"MARKET CLOSE — {date}", ""]
    if gainers:
        lines.append("Today's winners:")
        for g in gainers[:3]:
            lines.append(f"  ${g['symbol']} {g['change_pct']:+.1f}%")
    if losers:
        lines.append("")
        lines.append("Today's losers:")
        for l in losers[:3]:
            lines.append(f"  ${l['symbol']} {l['change_pct']:+.1f}%")
    lines += ["", "See you at pre-market tomorrow. 🔔", "Follow so you never miss a mover."]
    return "\n".join(lines), "eod"

def post_midday():
    gainers, losers = get_movers()
    lines = ["MIDDAY CHECK", ""]
    if gainers:
        lines.append("Leading the session:")
        for g in gainers[:3]:
            lines.append(f"  ${g['symbol']} {g['change_pct']:+.1f}%")
    if losers:
        lines.append("")
        lines.append("Getting hit:")
        for l in losers[:3]:
            lines.append(f"  ${l['symbol']} {l['change_pct']:+.1f}%")
    lines += ["", "Markets still moving. Stay locked in. 🎯"]
    return "\n".join(lines), "midday"

# --- POST & LOG ---
def tweet(text: str, post_type: str):
    client = get_client()
    r = client.create_tweet(text=text)
    tweet_id = r.data["id"]
    url = f"https://twitter.com/jeeniferdq/status/{tweet_id}"

    # Log it
    log = []
    if LOG.exists():
        try: log = json.loads(LOG.read_text())
        except: pass
    log.append({"ts": datetime.now().isoformat(), "type": post_type, "text": text, "id": tweet_id, "url": url})
    LOG.write_text(json.dumps(log, indent=2))

    print(f"Posted [{post_type}]: {url}")
    return tweet_id, url

# --- SCHEDULE LOGIC ---
def auto_post():
    hour = datetime.now().hour  # ET
    # 6-9am: premarket
    if 6 <= hour < 9:
        text, ptype = post_premarket()
    # 9-11am: movers + breakdown
    elif 9 <= hour < 11:
        text, ptype = post_breakdown() if random.random() > 0.4 else post_movers()
    # 11am-1pm: midday
    elif 11 <= hour < 13:
        text, ptype = post_midday()
    # 1-3pm: trending + breakdown
    elif 13 <= hour < 15:
        text, ptype = post_trending() if random.random() > 0.5 else post_breakdown()
    # 3-4pm: into the close
    elif 15 <= hour < 16:
        text, ptype = post_movers()
    # 4pm+: EOD
    else:
        text, ptype = post_eod()

    if text:
        return tweet(text, ptype)
    return None, None

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "auto"
    if cmd == "premarket":
        text, ptype = post_premarket()
    elif cmd == "movers":
        text, ptype = post_movers()
    elif cmd == "breakdown":
        text, ptype = post_breakdown()
    elif cmd == "trending":
        text, ptype = post_trending()
    elif cmd == "eod":
        text, ptype = post_eod()
    elif cmd == "midday":
        text, ptype = post_midday()
    else:
        text, ptype = None, None
        auto_post()
        sys.exit(0)

    if text:
        print(f"--- [{ptype}] ---\n{text}\n")
        tweet(text, ptype)
