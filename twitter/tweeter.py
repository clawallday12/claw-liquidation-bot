# -*- coding: utf-8 -*-
"""
@jeeniferdq Twitter engine v2
- ASCII-safe text (no encoding issues)
- Hook-driven copy based on writing-x-posts skill
- Deduplication built in
- Real Yahoo Finance data
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

def get_client():
    creds = json.loads(Path("config/twitter-api.json").read_text())
    return tweepy.Client(
        consumer_key=creds["consumer_key"],
        consumer_secret=creds["consumer_secret"],
        access_token=creds["access_token"],
        access_token_secret=creds["access_token_secret"],
        wait_on_rate_limit=True
    )

def recently_posted(minutes=25):
    if not LOG.exists(): return False
    try:
        posts = json.loads(LOG.read_text())
        if not posts: return False
        last_dt = datetime.fromisoformat(posts[-1]["ts"])
        return (datetime.now() - last_dt).total_seconds() / 60 < minutes
    except: return False

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
        r = requests.get(
            "https://query1.finance.yahoo.com/v1/finance/trending/US?count=10",
            headers=HEADERS, timeout=8, verify=False
        )
        if r.status_code == 200:
            quotes = r.json()["finance"]["result"][0]["quotes"]
            return [q["symbol"] for q in quotes if not q["symbol"].endswith("-USD")]
    except: pass
    return []

def fmt_vol(v):
    if not v: return "N/A"
    if v > 1e9: return f"{v/1e9:.1f}B"
    if v > 1e6: return f"{v/1e6:.1f}M"
    return f"{v/1e3:.0f}K"

# --- POST GENERATORS (hook-driven, ASCII-safe) ---

def post_premarket():
    gainers, losers = get_movers()
    if not gainers: return None, None
    date = datetime.now().strftime("%b %d")
    top = gainers[0]

    hooks = [
        f"Before the bell - {date}\n\n",
        f"Market opens soon. Here's what's moving - {date}\n\n",
        f"Early movers to watch - {date}\n\n",
    ]
    text = random.choice(hooks)
    text += "Gainers:\n"
    for g in gainers[:4]:
        text += f"${g['symbol']} {g['change_pct']:+.1f}%\n"
    text += "\nLosers:\n"
    for l in losers[:3]:
        text += f"${l['symbol']} {l['change_pct']:+.1f}%\n"
    text += "\nWhich are you watching? Follow for daily coverage."
    return text.strip(), "premarket"

def post_breakdown():
    gainers, _ = get_movers()
    if not gainers: return None, None
    top = gainers[0]
    sym = top['symbol']
    pct = top['change_pct']
    price = top['price']
    vol = fmt_vol(top['volume'])

    templates = [
        f"${sym} is up {pct:.0f}% today.\n\nPrice: ${price:.2f}\nVolume: {vol}\n\nBig moves don't happen for no reason. What's your take?",
        f"${sym} ripping {pct:.0f}% right now.\n\nHere's what you need to know:\n- Price: ${price:.2f}\n- Volume: {vol}\n\nSomething is happening here. Follow to stay updated.",
        f"Eye on ${sym} today.\n\n{pct:.0f}% move on {vol} volume.\n\nThis kind of action creates opportunities.\n\nWhat are you seeing?",
    ]
    return random.choice(templates).strip(), "breakdown"

def post_movers():
    gainers, losers = get_movers()
    if not gainers: return None, None
    date = datetime.now().strftime("%b %d")

    hooks = [
        f"Market movers right now ({date}):\n\n",
        f"Stocks making moves today ({date}):\n\n",
        f"The market is moving. Here's what matters ({date}):\n\n",
    ]
    text = random.choice(hooks)
    text += "Winners:\n"
    for g in gainers[:4]:
        text += f"${g['symbol']} {g['change_pct']:+.1f}%\n"
    text += "\nGetting hit:\n"
    for l in losers[:3]:
        text += f"${l['symbol']} {l['change_pct']:+.1f}%\n"
    text += "\nFollow for real-time movers every day."
    return text.strip(), "movers"

def post_trending():
    trending = get_trending()
    stocks = [t for t in trending if not t.endswith('-USD')][:6]
    if not stocks: return None, None

    hooks = [
        "Stocks everyone is watching right now:\n\n",
        "Wall Street's attention is here right now:\n\n",
        "These tickers are trending today:\n\n",
    ]
    text = random.choice(hooks)
    for s in stocks:
        text += f"${s}\n"
    text += "\nWhich one are you in? Drop it below."
    return text.strip(), "trending"

def post_midday():
    gainers, losers = get_movers()
    if not gainers: return None, None
    text = "Midday check:\n\n"
    text += "Leading the session:\n"
    for g in gainers[:3]:
        text += f"${g['symbol']} {g['change_pct']:+.1f}%\n"
    text += "\nGetting sold:\n"
    for l in losers[:3]:
        text += f"${l['symbol']} {l['change_pct']:+.1f}%\n"
    text += "\nStill 2 hours to go. Stay locked in."
    return text.strip(), "midday"

def post_eod():
    gainers, losers = get_movers()
    if not gainers: return None, None
    date = datetime.now().strftime("%b %d")
    text = f"Market close - {date}\n\n"
    text += "Today's winners:\n"
    for g in gainers[:3]:
        text += f"${g['symbol']} {g['change_pct']:+.1f}%\n"
    text += "\nToday's losers:\n"
    for l in losers[:3]:
        text += f"${l['symbol']} {l['change_pct']:+.1f}%\n"
    text += "\nSee you at pre-market tomorrow. Follow so you never miss a move."
    return text.strip(), "eod"

def post_hook_thread_opener():
    """High-engagement hook post based on writing-x-posts skill"""
    gainers, losers = get_movers()
    if not gainers: return None, None
    top = gainers[0]
    sym = top['symbol']
    pct = top['change_pct']

    templates = [
        f"I track hundreds of stocks every day.\n\n${sym} is the one making noise right now.\n\nUp {pct:.0f}%. Here's what I'm watching:",
        f"Most traders missed ${sym} this morning.\n\nIt was up {pct:.0f}% before most people checked their phones.\n\nHere's the setup that made it obvious:",
        f"${sym} just moved {pct:.0f}%.\n\nIf you weren't watching, here's why it matters:\n\nAnd what it means for the rest of the day:",
    ]
    return random.choice(templates).strip(), "hook_post"

def auto_post():
    if recently_posted(25):
        print("Posted recently, skipping.")
        return None, None

    hour = datetime.now().hour
    # Vary content by time + some randomness for freshness
    if 6 <= hour < 9:
        fns = [post_premarket, post_premarket, post_trending]
    elif 9 <= hour < 11:
        fns = [post_breakdown, post_hook_thread_opener, post_movers]
    elif 11 <= hour < 13:
        fns = [post_midday, post_breakdown, post_movers]
    elif 13 <= hour < 15:
        fns = [post_trending, post_breakdown, post_hook_thread_opener]
    elif 15 <= hour < 17:
        fns = [post_movers, post_breakdown, post_eod]
    else:
        fns = [post_eod, post_movers]

    for fn in random.sample(fns, len(fns)):
        text, ptype = fn()
        if text:
            return tweet(text, ptype)
    return None, None

def tweet(text: str, post_type: str):
    # Ensure clean ASCII-compatible encoding
    clean = text.encode('utf-8').decode('utf-8')
    client = get_client()
    r = client.create_tweet(text=clean)
    tweet_id = r.data["id"]
    url = f"https://twitter.com/jeeniferdq/status/{tweet_id}"

    log = []
    if LOG.exists():
        try: log = json.loads(LOG.read_text())
        except: pass
    log.append({"ts": datetime.now().isoformat(), "type": post_type, "text": clean, "id": tweet_id, "url": url})
    LOG.write_text(json.dumps(log, indent=2))
    print(f"Posted [{post_type}] -> {url}")
    return tweet_id, url

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "auto"
    dispatch = {
        "premarket": post_premarket, "movers": post_movers,
        "breakdown": post_breakdown, "trending": post_trending,
        "midday": post_midday, "eod": post_eod,
        "hook": post_hook_thread_opener,
    }
    if cmd in dispatch:
        text, ptype = dispatch[cmd]()
        if text:
            print(f"--- PREVIEW [{ptype}] ---\n{text.encode('ascii','replace').decode()}\n[{len(text)} chars]")
            if "--post" in sys.argv:
                tweet(text, ptype)
    else:
        auto_post()
