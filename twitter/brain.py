# -*- coding: utf-8 -*-
"""
@jeeniferdq brain v2 — event-driven finance account
Persona: mid-20s, sharp, watches everything — stocks, macro, politics-x-markets
Posts when worth it. Studies constantly. Human timing. Zero AI tells.

Learnings from studying @unusual_whales, @DeItaone, @StockMKTNewz, @FinancialJuice:
- 48% of posts are <100 chars
- ALL CAPS for breaking headlines
- $TICKER used selectively (not every post)
- Short reactions work: "insane" "wtf" "big"
- Mix: movers + macro news + educational takes
- Never sound scheduled
"""
import json, os, sys, re, requests, warnings, random, time
from datetime import datetime
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
    return {"last_posted": None, "seen_headlines": [], "seen_movers": {}, "scan_done": {}}

def save_state(s):
    STATE.write_text(json.dumps(s, indent=2, default=str))

def get_client():
    creds = json.loads(Path("config/twitter-api.json").read_text())
    return tweepy.Client(
        consumer_key=creds["consumer_key"], consumer_secret=creds["consumer_secret"],
        access_token=creds["access_token"], access_token_secret=creds["access_token_secret"],
        bearer_token=creds["bearer_token"], wait_on_rate_limit=True
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

# --- DATA SOURCES ---
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
            return [q["symbol"] for q in r.json()["finance"]["result"][0]["quotes"]
                    if not q["symbol"].endswith("-USD")]
    except: pass
    return []

def get_news():
    """Multi-source news: Google News RSS + RSS feeds"""
    headlines = []
    feeds = [
        "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx6TVdZU0FtVnVHZ0pWVXlnQVAB",
        "https://news.google.com/rss/search?q=stock+market+earnings+fed&hl=en-US&gl=US&ceid=US:en",
        "https://feeds.a.dj.com/rss/RSSMarketsMain.xml",  # WSJ Markets
        "https://feeds.content.dowjones.io/public/rss/mw_topstories",  # MarketWatch
    ]
    for url in feeds:
        try:
            r = requests.get(url, headers=H, timeout=8, verify=False)
            if r.status_code == 200:
                # Parse titles
                titles = re.findall(r'<title><!\[CDATA\[(.*?)\]\]></title>', r.text)
                if not titles:
                    titles = re.findall(r'<title>(.*?)</title>', r.text)
                clean = [
                    re.sub(r'<[^>]+>', '', t).strip()
                    for t in titles[1:8]
                    if len(t) > 20 and 'google' not in t.lower()
                    and 'rss' not in t.lower()
                ]
                headlines.extend(clean)
                if len(headlines) >= 8: break
        except: pass
    return list(dict.fromkeys(headlines))[:8]  # dedupe

def get_stock_news(symbol):
    try:
        r = requests.get(
            f"https://news.google.com/rss/search?q={symbol}+stock&hl=en-US&gl=US&ceid=US:en",
            headers=H, timeout=8, verify=False
        )
        titles = re.findall(r'<title><!\[CDATA\[(.*?)\]\]></title>', r.text)
        return [t for t in titles[1:4] if len(t) > 15][:3]
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

def should_post(sym, state, hours=2):
    seen = state.get("seen_movers", {})
    if sym not in seen: return True
    return (datetime.now() - datetime.fromisoformat(seen[sym])).seconds > hours * 3600

def mark_seen(sym, state):
    state.setdefault("seen_movers", {})[sym] = datetime.now().isoformat()

# --- CHART ---
def make_chart_upload(symbol, change_pct=None):
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

# --- VOICE LIBRARY (mid-20s, sharp, real) ---
def voice_big_gainer(g, news=None):
    sym, pct, price = g['symbol'], g['change_pct'], g['price']
    vol = fmt_vol(g['volume'])
    vr = vol_ratio(g['volume'], g['avg_vol'])
    vr_str = f" ({vr:.0f}x vol)" if vr > 1.8 else ""

    if news:
        n = re.sub(r'<[^>]+>', '', news[0])[:120]
        return random.choice([
            f"${sym} {pct:+.0f}%\n\n{n}",
            f"${sym} ripping after this\n\n{n}",
            f"there it is for ${sym}\n\n{n}\n\nup {pct:.0f}%",
        ])
    if vr > 4:
        return random.choice([
            f"${sym} volume is insane. {vr:.0f}x average\n\n{vol} shares. up {pct:.0f}%\n\nsomeone knows something",
            f"${sym} {pct:.0f}%\n\n{vol} volume today ({vr:.0f}x normal)\n\nwatch this",
        ])
    return random.choice([
        f"${sym} {pct:+.0f}%{vr_str}\n\nbig move today",
        f"${sym} up {pct:.0f}% to ${price:.2f}{vr_str}",
        f"${sym} ripping. {pct:.0f}%{vr_str}",
        f"watching ${sym} closely. {pct:.0f}% move{vr_str}",
    ])

def voice_big_loser(l, news=None):
    sym, pct = l['symbol'], abs(l['change_pct'])
    vol = fmt_vol(l['volume'])
    if news:
        n = re.sub(r'<[^>]+>', '', news[0])[:120]
        return random.choice([
            f"${sym} -{pct:.0f}%\n\n{n}",
            f"rough day for ${sym}\n\n{n}",
        ])
    return random.choice([
        f"${sym} getting destroyed. -{pct:.0f}%",
        f"ouch. ${sym} -{pct:.0f}% today on {vol} volume",
        f"${sym} -{pct:.0f}%\n\nbig selling pressure",
        f"${sym} down {pct:.0f}%. brutal",
    ])

def voice_scan(gainers, losers):
    hour = datetime.now().hour
    if hour < 10:
        label = random.choice(["morning scan", "pre-market", "opening scan"])
    elif hour < 14:
        label = random.choice(["midday", "midday check", "session so far"])
    else:
        label = random.choice(["into the close", "eod", "closing"])

    lines = [label, ""]
    for g in gainers[:4]:
        vr = vol_ratio(g['volume'], g['avg_vol'])
        suffix = f" ({vr:.0f}x vol)" if vr > 2.5 else ""
        lines.append(f"${g['symbol']} +{g['change_pct']:.1f}%{suffix}")
    lines.append("")
    for l in losers[:3]:
        lines.append(f"${l['symbol']} {l['change_pct']:.1f}%")
    return "\n".join(lines)

def voice_news(headline):
    h = re.sub(r'<[^>]+>', '', headline).strip()
    # Breaking news style if it's market-moving
    keywords = ["fed", "rate", "inflation", "cpi", "gdp", "jobs", "earnings", "beats", "misses", "bankrupt", "crash", "surge", "ban", "tariff"]
    is_breaking = any(k in h.lower() for k in keywords)

    if is_breaking and len(h) < 120:
        # DeItaone style: ALL CAPS
        return random.choice([
            h.upper(),
            f"BREAKING: {h}",
            h,
        ])
    return random.choice([
        h,
        f"notable: {h}",
        h,
    ])

def voice_volume_spike(g):
    sym, pct = g['symbol'], g['change_pct']
    vol = fmt_vol(g['volume'])
    vr = vol_ratio(g['volume'], g['avg_vol'])
    return random.choice([
        f"${sym} trading {vol} today. that's {vr:.0f}x normal volume\n\nup {pct:.0f}%",
        f"unusual volume on ${sym}\n\n{vr:.0f}x average. {vol} shares so far",
        f"${sym} {vr:.0f}x normal volume. {pct:.0f}% move.\n\nsomething is happening",
    ])

def voice_educational():
    """Viral educational/comparison posts like @StockMKTNewz"""
    posts = [
        "the s&p 500 is down 8% in the last 30 days\n\nmost people panic sell here\n\nthis is when generational wealth gets built",
        "fear & greed index is at extreme fear right now\n\nhistorically this is when the best buying opportunities appear\n\nnot financial advice",
        "reminder: every bear market in history has been followed by a new all-time high",
        "the stocks making the biggest moves today are moving for a reason\n\nfigure out the reason before you trade",
    ]
    return random.choice(posts)

# --- DECISION ENGINE ---
def run(state, force=False):
    since_last = mins_since_last_post()
    min_gap = random.randint(20, 50)
    if not force and since_last < min_gap:
        print(f"Gap: {since_last:.0f}min (want {min_gap}min)")
        return None

    gainers, losers = get_movers()
    hour = datetime.now().hour
    is_market = 9 <= hour < 16

    # P1: Big gainer with news (highest engagement potential)
    for g in gainers:
        if g['change_pct'] > 10 and should_post(g['symbol'], state):
            news = get_stock_news(g['symbol'])
            text = voice_big_gainer(g, news or None)
            vr = vol_ratio(g['volume'], g['avg_vol'])
            media_id = make_chart_upload(g['symbol'], g['change_pct']) if vr > 2 else None
            result = post(text, "big_gainer", [media_id] if media_id else None)
            mark_seen(g['symbol'], state)
            return result

    # P2: Severe loser
    for l in losers:
        if abs(l['change_pct']) > 15 and should_post(l['symbol'], state):
            news = get_stock_news(l['symbol'])
            text = voice_big_loser(l, news or None)
            result = post(text, "big_loser")
            mark_seen(l['symbol'], state)
            return result

    # P3: Volume spike
    for g in gainers:
        vr = vol_ratio(g['volume'], g['avg_vol'])
        if vr > 3.5 and should_post(g['symbol'], state):
            text = voice_volume_spike(g)
            result = post(text, "volume_spike")
            mark_seen(g['symbol'], state)
            return result

    # P4: News reaction (breaking / macro)
    if is_market or hour >= 6:
        headlines = get_news()
        seen_hl = state.get("seen_headlines", [])
        for h in headlines:
            clean = re.sub(r'<[^>]+>', '', h).strip()
            if clean and clean not in seen_hl and len(clean) > 20:
                text = voice_news(clean)
                result = post(text, "news")
                state.setdefault("seen_headlines", []).append(clean)
                state["seen_headlines"] = state["seen_headlines"][-30:]
                return result

    # P5: Scan (once per period)
    period = "am" if hour < 12 else "pm"
    scan_key = f"scan_{datetime.now().strftime('%Y%m%d')}_{period}"
    if scan_key not in state.get("scan_done", {}) and gainers:
        text = voice_scan(gainers, losers)
        result = post(text, "scan")
        state.setdefault("scan_done", {})[scan_key] = datetime.now().isoformat()
        return result

    # P6: Educational/viral post (mix in occasionally)
    if since_last > 90 and random.random() < 0.3:
        text = voice_educational()
        return post(text, "educational")

    print("Nothing worth posting")
    return None

def post(text, ptype, media_ids=None):
    client = get_client()
    r = client.create_tweet(text=text, media_ids=media_ids)
    tid = r.data["id"]
    url = f"https://twitter.com/jeeniferdq/status/{tid}"
    log = []
    if LOG.exists():
        try: log = json.loads(LOG.read_text())
        except: pass
    log.append({"ts": datetime.now().isoformat(), "type": ptype, "text": text, "id": tid, "url": url})
    LOG.write_text(json.dumps(log, indent=2))
    print(f"Posted [{ptype}] {url}")
    print(f"  > {text[:100].replace(chr(10),' ')}")
    return tid, url

def delete(tweet_id):
    get_client().delete_tweet(tweet_id)
    print(f"Deleted {tweet_id}")

if __name__ == "__main__":
    if "--delete" in sys.argv:
        idx = sys.argv.index("--delete")
        delete(sys.argv[idx+1])
        sys.exit(0)
    force = "--force" in sys.argv
    state = load_state()
    result = run(state, force=force)
    save_state(state)
    if result: print(result[1])
