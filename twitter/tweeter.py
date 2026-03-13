# -*- coding: utf-8 -*-
"""
@jeeniferdq - Finance Twitter engine v3
Voice: real human trader. No AI tells. No CTAs. No fake enthusiasm.
Studies: @unusual_whales, @StockMKTNewz, @zerohedge, @DeItaone style
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
                        "avg_vol": q.get("averageDailyVolume3Month",0),
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

def get_news_rss():
    """Get news headlines from Google News RSS - no key needed"""
    headlines = []
    feeds = [
        "https://news.google.com/rss/search?q=stock+market+today&hl=en-US&gl=US&ceid=US:en",
        "https://news.google.com/rss/search?q=earnings+stocks&hl=en-US&gl=US&ceid=US:en",
    ]
    for url in feeds:
        try:
            r = requests.get(url, headers=HEADERS, timeout=8, verify=False)
            if r.status_code == 200:
                import re
                titles = re.findall(r'<title><!\[CDATA\[(.*?)\]\]></title>', r.text)
                headlines += [t for t in titles[1:6] if len(t) > 20]
                if headlines: break
        except: pass
    return headlines

def get_stock_news(symbol):
    """Get news for specific ticker via Google News RSS"""
    try:
        import re
        r = requests.get(
            f"https://news.google.com/rss/search?q={symbol}+stock&hl=en-US&gl=US&ceid=US:en",
            headers=HEADERS, timeout=8, verify=False
        )
        if r.status_code == 200:
            titles = re.findall(r'<title><!\[CDATA\[(.*?)\]\]></title>', r.text)
            return [t for t in titles[1:4] if len(t) > 15]
    except: pass
    return []

def fmt_vol_ratio(vol, avg):
    if not vol or not avg or avg == 0: return ""
    ratio = vol / avg
    if ratio > 3: return f" ({ratio:.0f}x avg vol)"
    if ratio > 1.5: return f" ({ratio:.1f}x avg vol)"
    return ""

def fmt_vol(v):
    if not v: return "N/A"
    if v > 1e9: return f"{v/1e9:.1f}B"
    if v > 1e6: return f"{v/1e6:.1f}M"
    return f"{v/1e3:.0f}K"

# --- HUMAN-VOICE POST GENERATORS ---
# Rule: No CTAs. No "follow for". No "here's what you need to know".
# Sound like a trader watching screens, not a content creator.

def post_single_mover():
    gainers, _ = get_movers()
    if not gainers: return None, None
    g = gainers[0]
    sym, pct, price = g['symbol'], g['change_pct'], g['price']
    vol = fmt_vol(g['volume'])
    vol_ratio = fmt_vol_ratio(g['volume'], g['avg_vol'])
    news = get_stock_news(sym)
    catalyst = news[0] if news else None

    if catalyst and len(catalyst) < 100:
        templates = [
            f"${sym} +{pct:.0f}%\n\n{catalyst}",
            f"${sym} ripping today\n\n{catalyst}\n\nStock up {pct:.0f}% on {vol} volume{vol_ratio}",
            f"${sym} up {pct:.0f}% - {catalyst}",
        ]
    else:
        templates = [
            f"${sym} up {pct:.0f}% on {vol} volume{vol_ratio}\n\nwatching to see if this holds",
            f"${sym} ripping {pct:.0f}%\n\nprice ${price:.2f}, volume {vol}{vol_ratio}\n\ninsane move",
            f"${sym} {pct:.0f}% move today\n\n{vol} shares traded{vol_ratio}\n\nbig",
            f"that ${sym} move is wild. +{pct:.0f}% on {vol} volume{vol_ratio}",
        ]
    return random.choice(templates).strip(), "mover_spotlight"

def post_losers_reaction():
    _, losers = get_movers()
    if not losers: return None, None
    top = losers[0]
    sym, pct, price = top['symbol'], top['change_pct'], top['price']
    vol = fmt_vol(top['volume'])
    news = get_stock_news(sym)
    catalyst = news[0] if news else None

    if catalyst and len(catalyst) < 100:
        templates = [
            f"${sym} getting obliterated today\n\n{catalyst}\n\ndown {abs(pct):.0f}%",
            f"${sym} -{abs(pct):.0f}%\n\n{catalyst}",
        ]
    else:
        templates = [
            f"${sym} down {abs(pct):.0f}% on {vol} volume\n\nouch",
            f"${sym} getting hit hard today. -{abs(pct):.0f}%\n\n{vol} volume, price ${price:.2f}",
            f"rough day for ${ sym} holders. -{abs(pct):.0f}%",
        ]
    return random.choice(templates).strip(), "loser_reaction"

def post_morning_scan():
    gainers, losers = get_movers()
    if not gainers: return None, None
    date = datetime.now().strftime("%b %d")

    # Raw, no-fluff scan format like real accounts
    lines = [f"morning scan {date}"]
    lines.append("")
    lines.append("moving up:")
    for g in gainers[:4]:
        vol_r = fmt_vol_ratio(g['volume'], g['avg_vol'])
        lines.append(f"${g['symbol']} +{g['change_pct']:.1f}%{vol_r}")
    lines.append("")
    lines.append("moving down:")
    for l in losers[:3]:
        lines.append(f"${l['symbol']} -{abs(l['change_pct']):.1f}%")
    return "\n".join(lines).strip(), "morning_scan"

def post_volume_alert():
    gainers, _ = get_movers()
    high_vol = [g for g in gainers if g.get('avg_vol') and g['volume'] > g['avg_vol'] * 2]
    if not high_vol: return post_single_mover()
    g = high_vol[0]
    sym = g['symbol']
    vol = fmt_vol(g['volume'])
    avg = fmt_vol(g['avg_vol'])
    ratio = round(g['volume'] / g['avg_vol'], 1)
    templates = [
        f"${sym} trading {vol} shares today\n\naverage is {avg}\n\n{ratio}x normal volume. something is going on",
        f"unusual volume on ${sym}\n\n{ratio}x average today\n\n{vol} vs normal {avg}",
        f"${sym} volume is absurd right now\n\n{ratio}x average\n\nprice up {g['change_pct']:.0f}%",
    ]
    return random.choice(templates).strip(), "volume_alert"

def post_midday_check():
    gainers, losers = get_movers()
    if not gainers: return None, None
    templates = [
        f"midday\n\n{gainers[0]['symbol']} still running (+{gainers[0]['change_pct']:.0f}%)\n{losers[0]['symbol']} still bleeding (-{abs(losers[0]['change_pct']):.0f}%)\n\nmarket's not slowing down",
        f"halfway through the session\n\nleaders: ${gainers[0]['symbol']} ${gainers[1]['symbol'] if len(gainers)>1 else ''}\nlaggards: ${losers[0]['symbol']} ${losers[1]['symbol'] if len(losers)>1 else ''}\n\nstill a lot of time left",
        f"${gainers[0]['symbol']} holding its gains at midday. +{gainers[0]['change_pct']:.0f}%\n${losers[0]['symbol']} still ugly at -{abs(losers[0]['change_pct']):.0f}%",
    ]
    return random.choice(templates).strip(), "midday"

def post_close():
    gainers, losers = get_movers()
    if not gainers: return None, None
    date = datetime.now().strftime("%b %d")
    templates = [
        f"close - {date}\n\nbest: ${gainers[0]['symbol']} +{gainers[0]['change_pct']:.0f}%\nworst: ${losers[0]['symbol']} -{abs(losers[0]['change_pct']):.0f}%\n\nwild session",
        f"that's a wrap for {date}\n\n${gainers[0]['symbol']} the big winner at +{gainers[0]['change_pct']:.0f}%\n${losers[0]['symbol']} got destroyed -{abs(losers[0]['change_pct']):.0f}%",
        f"eod {date}\n\n{', '.join(['$'+g['symbol'] for g in gainers[:3]])} green\n{', '.join(['$'+l['symbol'] for l in losers[:3]])} red\n\nback tomorrow",
    ]
    return random.choice(templates).strip(), "close"

def post_trending_raw():
    trending = get_trending()
    if not trending: return None, None
    stocks = [t for t in trending if not t.endswith('-USD')][:5]
    templates = [
        "tickers getting attention right now:\n\n" + "\n".join(f"${s}" for s in stocks),
        "what wall street is watching today:\n\n" + " ".join(f"${s}" for s in stocks),
        "trending:\n\n" + "\n".join(f"${s}" for s in stocks[:4]),
    ]
    return random.choice(templates).strip(), "trending"

def post_news_take():
    headlines = get_news_rss()
    if not headlines: return None, None
    h = headlines[0]
    templates = [
        h,
        f"notable: {h}",
    ]
    return random.choice(templates).strip(), "news"

# --- CORE LOOP ---

def auto_post():
    if recently_posted(25):
        print("Posted recently, skipping.")
        return None, None

    hour = datetime.now().hour
    if 6 <= hour < 9:
        pool = [post_morning_scan, post_morning_scan, post_single_mover]
    elif 9 <= hour < 11:
        pool = [post_volume_alert, post_single_mover, post_news_take, post_morning_scan]
    elif 11 <= hour < 13:
        pool = [post_midday_check, post_single_mover, post_losers_reaction]
    elif 13 <= hour < 15:
        pool = [post_volume_alert, post_trending_raw, post_single_mover]
    elif 15 <= hour < 17:
        pool = [post_single_mover, post_losers_reaction, post_close]
    else:
        pool = [post_close, post_news_take, post_trending_raw]

    random.shuffle(pool)
    for fn in pool:
        text, ptype = fn()
        if text:
            return tweet(text, ptype)
    return None, None

def tweet(text: str, post_type: str):
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

def delete_tweet(tweet_id):
    client = get_client()
    r = client.delete_tweet(tweet_id)
    print(f"Deleted {tweet_id}: {r}")

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "auto"
    dispatch = {
        "mover": post_single_mover, "loser": post_losers_reaction,
        "scan": post_morning_scan, "volume": post_volume_alert,
        "midday": post_midday_check, "close": post_close,
        "trending": post_trending_raw, "news": post_news_take,
    }
    if cmd == "delete" and len(sys.argv) > 2:
        delete_tweet(sys.argv[2])
    elif cmd in dispatch:
        text, ptype = dispatch[cmd]()
        if text:
            safe = text.encode('ascii', 'replace').decode()
            print(f"--- [{ptype}] ---\n{safe}\n[{len(text)} chars]")
            if "--post" in sys.argv:
                tweet(text, ptype)
    else:
        auto_post()
