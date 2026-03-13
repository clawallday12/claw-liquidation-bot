# -*- coding: utf-8 -*-
"""
@jeeniferdq brain — event-driven finance account
Persona: mid-20s, genuinely into markets, professional but real
Posts when something worth saying happens. Always watching.
Zero AI tells. Zero fixed schedule. Zero CTAs.
"""
import json, os, sys, requests, warnings, random, time, re
from datetime import datetime, timedelta
from pathlib import Path
import tweepy

os.chdir('C:/Users/firas/.openclaw/workspace')
warnings.filterwarnings('ignore')
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
LOG = Path("logs/twitter-posts.json")
STATE = Path("logs/brain-state.json")
LOG.parent.mkdir(exist_ok=True)

def load_state():
    if STATE.exists():
        try: return json.loads(STATE.read_text())
        except: pass
    return {"last_posted": None, "last_scan": None, "seen_headlines": [], "seen_movers": {}, "post_count_today": 0}

def save_state(s):
    STATE.write_text(json.dumps(s, indent=2, default=str))

def get_client():
    creds = json.loads(Path("config/twitter-api.json").read_text())
    return tweepy.Client(
        consumer_key=creds["consumer_key"], consumer_secret=creds["consumer_secret"],
        access_token=creds["access_token"], access_token_secret=creds["access_token_secret"],
        wait_on_rate_limit=True
    )

def get_api_v1():
    creds = json.loads(Path("config/twitter-api.json").read_text())
    auth = tweepy.OAuth1UserHandler(
        creds["consumer_key"], creds["consumer_secret"],
        creds["access_token"], creds["access_token_secret"]
    )
    return tweepy.API(auth)

def mins_since_last_post():
    if not LOG.exists(): return 999
    try:
        posts = json.loads(LOG.read_text())
        if not posts: return 999
        last = datetime.fromisoformat(posts[-1]["ts"])
        return (datetime.now() - last).total_seconds() / 60
    except: return 999

# --- DATA ---
def get_movers():
    gainers, losers = [], []
    for scrId, target in [("day_gainers", gainers), ("day_losers", losers)]:
        try:
            r = requests.get(
                f"https://query1.finance.yahoo.com/v1/finance/screener/predefined/saved?scrIds={scrId}&count=5",
                headers=H, timeout=8, verify=False
            )
            if r.status_code == 200:
                qs = r.json().get("finance",{}).get("result",[{}])[0].get("quotes",[])
                for q in qs[:5]:
                    target.append({
                        "symbol": q.get("symbol",""), "name": q.get("shortName",""),
                        "price": q.get("regularMarketPrice",0),
                        "change_pct": q.get("regularMarketChangePercent",0),
                        "volume": q.get("regularMarketVolume",0),
                        "avg_vol": q.get("averageDailyVolume3Month",0),
                    })
        except: pass
    return gainers, losers

def get_trending():
    try:
        r = requests.get("https://query1.finance.yahoo.com/v1/finance/trending/US?count=10", headers=H, timeout=8, verify=False)
        if r.status_code == 200:
            qs = r.json()["finance"]["result"][0]["quotes"]
            return [q["symbol"] for q in qs if not q["symbol"].endswith("-USD")]
    except: pass
    return []

def get_news():
    headlines = []
    urls = [
        "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx6TVdZU0FtVnVHZ0pWVXlnQVAB",  # Business
        "https://feeds.finance.yahoo.com/rss/2.0/headline?s=^GSPC&region=US&lang=en-US",
    ]
    for url in urls:
        try:
            r = requests.get(url, headers=H, timeout=8, verify=False)
            titles = re.findall(r'<title><!\[CDATA\[(.*?)\]\]></title>', r.text)
            clean = [t for t in titles[1:8] if len(t) > 20 and 'google' not in t.lower()]
            headlines.extend(clean)
            if len(headlines) >= 5: break
        except: pass
    return headlines[:8]

def get_stock_news(symbol):
    try:
        r = requests.get(
            f"https://news.google.com/rss/search?q={symbol}+stock+earnings&hl=en-US&gl=US&ceid=US:en",
            headers=H, timeout=8, verify=False
        )
        titles = re.findall(r'<title><!\[CDATA\[(.*?)\]\]></title>', r.text)
        return [t for t in titles[1:5] if len(t) > 15 and symbol in t]
    except: pass
    return []

def fmt_vol(v):
    if not v: return "N/A"
    if v > 1e9: return f"{v/1e9:.1f}B"
    if v > 1e6: return f"{v/1e6:.1f}M"
    return f"{v/1e3:.0f}K"

def vol_ratio(vol, avg):
    if not vol or not avg or avg == 0: return 0
    return round(vol / avg, 1)

# --- GENERATE CHART ---
def make_and_upload_chart(symbol, change_pct=None):
    try:
        exec(open('twitter/make-chart.py').read(), {'__name__': '__run__'})
    except:
        pass
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("make_chart", "twitter/make-chart.py")
        mod = importlib.util.load_from_spec(spec)
    except: pass

    # Direct call
    try:
        g = {}
        exec(open('twitter/make-chart.py').read(), g)
        path = g['make_chart'](symbol, today_change=change_pct)
        if path and Path(path).exists():
            api = get_api_v1()
            media = api.media_upload(filename=path)
            return media.media_id
    except Exception as e:
        print(f"Chart error: {e}")
    return None

# --- TWEET COMPOSERS (human voice) ---
# Mid-20s, watches markets all day, has opinions, casual but sharp

def compose_mover(g, news=None):
    sym = g['symbol']
    pct = g['change_pct']
    price = g['price']
    vol = fmt_vol(g['volume'])
    vr = vol_ratio(g['volume'], g['avg_vol'])
    vr_str = f" ({vr}x avg vol)" if vr > 1.5 else ""

    if news:
        n = news[0][:120]
        pool = [
            f"${sym} {pct:+.0f}%\n\n{n}",
            f"${sym} going crazy today\n\n{n}\n\n+{pct:.0f}% on {vol} volume",
            f"there it is. ${sym} +{pct:.0f}%\n\n{n}",
        ]
    elif vr > 3:
        pool = [
            f"${sym} volume is insane today\n\n{vr}x average. {vol} shares already\n\nprice up {pct:.0f}%",
            f"someone knows something. ${sym} trading {vr:.0f}x normal volume\n\n+{pct:.0f}%",
            f"${sym} {vr:.0f}x normal volume today\n\n{vol} shares. up {pct:.0f}%\n\nwatch this",
        ]
    else:
        pool = [
            f"${sym} up {pct:.0f}% today{vr_str}\n\nbig move",
            f"${sym} ripping. {pct:.0f}%{vr_str}",
            f"${sym} +{pct:.0f}% to ${price:.2f} on {vol} volume{vr_str}",
            f"watching ${sym} closely. up {pct:.0f}% on {vol}{vr_str}",
        ]
    return random.choice(pool)

def compose_loser(l, news=None):
    sym = l['symbol']
    pct = abs(l['change_pct'])
    vol = fmt_vol(l['volume'])
    vr = vol_ratio(l['volume'], l['avg_vol'])

    if news:
        n = news[0][:120]
        pool = [
            f"${sym} -{pct:.0f}%\n\n{n}",
            f"rough one for ${sym}\n\n{n}\n\ndown {pct:.0f}%",
        ]
    else:
        pool = [
            f"${sym} getting destroyed today. -{pct:.0f}%",
            f"${sym} down {pct:.0f}%\n\n{vol} volume. not pretty",
            f"ouch. ${sym} -{pct:.0f}% today",
            f"${sym} -{pct:.0f}%. brutal session",
        ]
    return random.choice(pool)

def compose_scan(gainers, losers):
    hour = datetime.now().hour
    prefix = random.choice(["morning scan", "opening scan", "pre-market"]) if hour < 10 else \
             random.choice(["midday", "checking in", "session update"]) if hour < 14 else \
             random.choice(["into the close", "eod", "closing"]) if hour < 17 else "after hours"

    lines = [prefix, ""]
    for g in gainers[:4]:
        vr = vol_ratio(g['volume'], g['avg_vol'])
        vr_str = f" ({vr:.0f}x vol)" if vr > 2 else ""
        lines.append(f"${g['symbol']} +{g['change_pct']:.1f}%{vr_str}")
    lines.append("")
    for l in losers[:3]:
        lines.append(f"${l['symbol']} {l['change_pct']:.1f}%")
    return "\n".join(lines)

def compose_news_reaction(headline):
    # React like a human to a headline
    h = headline[:200]
    reactions = [
        h,
        f"notable: {h}",
        f"big if true\n\n{h}",
        f"markets watching this\n\n{h}",
    ]
    return random.choice(reactions)

# --- DECISION ENGINE ---
def should_post_about(sym, state, min_pct=8.0):
    """Only post about something once per session"""
    seen = state.get("seen_movers", {})
    return sym not in seen or (datetime.now() - datetime.fromisoformat(seen[sym])).seconds > 7200

def mark_posted(sym, state):
    state.setdefault("seen_movers", {})[sym] = datetime.now().isoformat()

def run_once(state, force=False):
    """Evaluate what to post, if anything"""
    since_last = mins_since_last_post()

    # Human timing: don't post more than every 20 min, vary naturally
    min_gap = random.randint(18, 45)
    if not force and since_last < min_gap:
        print(f"Too soon ({since_last:.0f}min since last, want {min_gap}min gap)")
        return None

    gainers, losers = get_movers()
    trending = get_trending()
    hour = datetime.now().hour
    is_market_hours = 9 <= hour < 16

    # Priority 1: Big mover with high volume (>10% AND >2x vol) — post with chart
    for g in gainers:
        if g['change_pct'] > 10 and vol_ratio(g['volume'], g['avg_vol']) > 2:
            if should_post_about(g['symbol'], state):
                news = get_stock_news(g['symbol'])
                text = compose_mover(g, news if news else None)
                media_id = make_and_upload_chart(g['symbol'], g['change_pct'])
                result = do_tweet(text, "big_mover", media_ids=[media_id] if media_id else None)
                mark_posted(g['symbol'], state)
                return result

    # Priority 2: Severe loser
    for l in losers:
        if abs(l['change_pct']) > 15:
            if should_post_about(l['symbol'], state):
                news = get_stock_news(l['symbol'])
                text = compose_loser(l, news if news else None)
                result = do_tweet(text, "big_loser")
                mark_posted(l['symbol'], state)
                return result

    # Priority 3: Volume spike on any mover
    for g in gainers:
        vr = vol_ratio(g['volume'], g['avg_vol'])
        if vr > 3 and should_post_about(g['symbol'], state):
            text = compose_mover(g)
            result = do_tweet(text, "volume_spike")
            mark_posted(g['symbol'], state)
            return result

    # Priority 4: Morning/close scan (only once per session)
    scan_key = "scan_am" if hour < 12 else "scan_pm"
    last_scan = state.get(scan_key)
    if not last_scan or (datetime.now() - datetime.fromisoformat(last_scan)).seconds > 14400:
        if gainers:
            text = compose_scan(gainers, losers)
            result = do_tweet(text, "scan")
            state[scan_key] = datetime.now().isoformat()
            return result

    # Priority 5: News reaction (if not posted in last hour)
    if since_last > 60:
        headlines = get_news()
        seen = state.get("seen_headlines", [])
        for h in headlines:
            if h not in seen:
                text = compose_news_reaction(h)
                result = do_tweet(text, "news")
                state.setdefault("seen_headlines", []).append(h)
                state["seen_headlines"] = state["seen_headlines"][-20:]
                return result

    print("Nothing worth posting right now")
    return None

def do_tweet(text, post_type, media_ids=None):
    client = get_client()
    r = client.create_tweet(text=text, media_ids=media_ids)
    tweet_id = r.data["id"]
    url = f"https://twitter.com/jeeniferdq/status/{tweet_id}"
    log = []
    if LOG.exists():
        try: log = json.loads(LOG.read_text())
        except: pass
    log.append({"ts": datetime.now().isoformat(), "type": post_type, "text": text, "id": tweet_id, "url": url})
    LOG.write_text(json.dumps(log, indent=2))
    print(f"Posted [{post_type}] {url}")
    print(f"  > {text[:80]}")
    return tweet_id, url

if __name__ == "__main__":
    force = "--force" in sys.argv
    state = load_state()
    result = run_once(state, force=force)
    save_state(state)
    if result:
        print(f"Done: {result[1]}")
