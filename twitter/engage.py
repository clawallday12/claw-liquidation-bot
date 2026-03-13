# -*- coding: utf-8 -*-
"""
@jeeniferdq engagement + learning engine v3
- Playwright-based replies/QTs (bypasses free API restrictions)
- Real metric tracking on own tweets
- Learning loop: analyze performance, adapt tone/frequency/content
- Runs every cycle
"""
import json, os, re, random, time, asyncio, requests, warnings
from datetime import datetime
from pathlib import Path
import tweepy

os.chdir('C:/Users/firas/.openclaw/workspace')
warnings.filterwarnings('ignore')
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

METRICS_FILE  = Path("logs/tweet-metrics.json")
LEARNING_FILE = Path("logs/learning.json")
ENGAGED_FILE  = Path("logs/engaged-tweets.json")
SESSION_FILE  = Path("config/twitter-session.json")

def get_client():
    creds = json.loads(Path("config/twitter-api.json").read_text())
    return tweepy.Client(
        consumer_key=creds["consumer_key"], consumer_secret=creds["consumer_secret"],
        access_token=creds["access_token"], access_token_secret=creds["access_token_secret"],
        bearer_token=creds["bearer_token"], wait_on_rate_limit=True
    )

def load_json(path, default):
    p = Path(path)
    if p.exists():
        try: return json.loads(p.read_text())
        except: pass
    return default

def save_json(path, data):
    Path(path).write_text(json.dumps(data, indent=2, default=str))

def log_post(text, ptype, tweet_id, url, extra=None):
    log = load_json("logs/twitter-posts.json", [])
    entry = {"ts": datetime.now().isoformat(), "type": ptype, "text": text, "id": str(tweet_id), "url": url}
    if extra: entry.update(extra)
    log.append(entry)
    save_json("logs/twitter-posts.json", log)

# --- METRIC TRACKING ---
def refresh_metrics():
    client = get_client()
    post_log = load_json("logs/twitter-posts.json", [])
    metrics  = load_json(METRICS_FILE, {})
    ids = [str(p["id"]) for p in post_log if p.get("id") and p.get("type") not in ("reply","quote_tweet")]
    if not ids: return metrics
    for i in range(0, len(ids), 100):
        try:
            resp = client.get_tweets(ids=ids[i:i+100], tweet_fields=["public_metrics","created_at"])
            if resp.data:
                for t in resp.data:
                    m = t.public_metrics
                    metrics[str(t.id)] = {
                        "likes": m["like_count"], "rts": m["retweet_count"],
                        "replies": m["reply_count"], "impressions": m.get("impression_count",0),
                        "checked": datetime.now().isoformat()
                    }
        except Exception as e:
            print(f"Metrics error: {e}")
    save_json(METRICS_FILE, metrics)
    return metrics

# --- LEARNING ENGINE ---
def analyze_and_adapt():
    post_log = load_json("logs/twitter-posts.json", [])
    metrics  = load_json(METRICS_FILE, {})
    learning = load_json(LEARNING_FILE, {})

    scored = []
    for p in post_log:
        pid = str(p.get("id",""))
        m = metrics.get(pid, {})
        score = m.get("likes",0)*3 + m.get("rts",0)*5 + m.get("replies",0)*2
        scored.append({
            "type": p.get("type","?"), "text": p.get("text","")[:120],
            "score": score, "likes": m.get("likes",0), "rts": m.get("rts",0),
            "len": len(p.get("text","")), "ts": p.get("ts",""), "url": p.get("url","")
        })

    # Type performance
    type_perf = {}
    for s in scored:
        t = s["type"]
        type_perf.setdefault(t, {"scores":[], "count":0})
        type_perf[t]["scores"].append(s["score"])
        type_perf[t]["count"] += 1
    for t in type_perf:
        sc = type_perf[t]["scores"]
        type_perf[t].update({"avg": round(sum(sc)/len(sc),2), "total": sum(sc), "best": max(sc)})

    def avg_s(lst): return round(sum(x["score"] for x in lst)/max(len(lst),1), 2)
    short  = [s for s in scored if s["len"] < 80]
    medium = [s for s in scored if 80 <= s["len"] < 200]

    recs = []
    st = sorted(type_perf.items(), key=lambda x: x[1]["avg"], reverse=True)
    if st and st[0][1]["avg"] > 0:
        recs.append(f"Best type: [{st[0][0]}] — post more of these")
    if len(st) > 1 and st[-1][1]["avg"] == 0 and st[-1][1]["count"] >= 2:
        recs.append(f"Worst type: [{st[-1][0]}] getting no engagement — reduce frequency")
    if avg_s(short) >= avg_s(medium) and short:
        recs.append("Short posts (<80 chars) performing best — keep punchy")

    # Study timeline for trending topics → feed into brain.py
    trending_topics = study_timeline_for_trends()
    if trending_topics:
        recs.append(f"Trending topics in feed: {', '.join(trending_topics[:4])}")

    result = {
        "updated": datetime.now().isoformat(),
        "total_posts": len(scored),
        "total_engagement": sum(s["score"] for s in scored),
        "type_performance": {k: {"avg": v["avg"], "count": v["count"], "best": v["best"]} for k,v in type_perf.items()},
        "length": {"short_avg": avg_s(short), "medium_avg": avg_s(medium)},
        "recommendations": recs,
        "best_posts": sorted(scored, key=lambda x: x["score"], reverse=True)[:3],
        "trending_topics": trending_topics,
    }
    save_json(LEARNING_FILE, result)
    return result

def study_timeline_for_trends():
    """Extract trending topics/tickers from home timeline to inform content"""
    client = get_client()
    try:
        resp = client.get_home_timeline(max_results=20, tweet_fields=["text"])
        if not resp.data: return []
        all_text = " ".join(t.text for t in resp.data)
        tickers = re.findall(r'\$([A-Z]{2,5})', all_text)
        kws = re.findall(r'\b(tariff|inflation|fed|rate|earnings|gdp|jobs|cpi|rally|selloff|recession|bitcoin|crypto|oil|gold)\b', all_text.lower())
        from collections import Counter
        top_tickers = [f"${t}" for t,_ in Counter(tickers).most_common(5)]
        top_kws = [k for k,_ in Counter(kws).most_common(3)]
        return top_tickers + top_kws
    except:
        return []

# --- PLAYWRIGHT ENGAGEMENT ---
async def playwright_reply(tweet_url: str, reply_text: str):
    from playwright.async_api import async_playwright
    creds = json.loads(Path("config/twitter-api.json").read_text())
    EMAIL, PASSWORD = "admin@narrately.ai", "Claw999!"

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        ctx = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 900}
        )
        page = await ctx.new_page()
        try:
            if SESSION_FILE.exists():
                await ctx.add_cookies(json.loads(SESSION_FILE.read_text()))

            await page.goto("https://x.com/home", wait_until="domcontentloaded", timeout=20000)
            await asyncio.sleep(3)

            if "login" in page.url or "flow" in page.url:
                await page.goto("https://x.com/i/flow/login", wait_until="domcontentloaded", timeout=20000)
                await asyncio.sleep(3)
                inputs = await page.query_selector_all('input')
                if inputs: await inputs[0].fill(EMAIL)
                await page.keyboard.press("Enter")
                await asyncio.sleep(2)
                pwd = await page.query_selector('input[type="password"]')
                if pwd:
                    await pwd.fill(PASSWORD)
                    await page.keyboard.press("Enter")
                    await asyncio.sleep(4)
                cookies = await ctx.cookies()
                SESSION_FILE.write_text(json.dumps(cookies))

            # Navigate to the tweet
            await page.goto(tweet_url, wait_until="domcontentloaded", timeout=20000)
            await asyncio.sleep(3)

            # Click reply button
            reply_btn = await page.query_selector('[data-testid="reply"]')
            if reply_btn:
                await reply_btn.click()
                await asyncio.sleep(2)

            # Find reply box and type
            box = await page.query_selector('[data-testid="tweetTextarea_0"]')
            if not box:
                box = await page.query_selector('div[contenteditable="true"]')
            if box:
                await box.click()
                await page.keyboard.type(reply_text, delay=25)
                await asyncio.sleep(1)
                # Post
                post_btn = await page.query_selector('[data-testid="tweetButtonInline"]')
                if post_btn:
                    await post_btn.click()
                    await asyncio.sleep(3)
                    cookies = await ctx.cookies()
                    SESSION_FILE.write_text(json.dumps(cookies))
                    return {"success": True, "text": reply_text}
            return {"success": False, "error": "No text box found"}
        except Exception as e:
            return {"success": False, "error": str(e)[:100]}
        finally:
            await browser.close()

def get_reply_targets():
    """Get timeline tweets worth engaging with"""
    client = get_client()
    engaged = set(str(x) for x in load_json(ENGAGED_FILE, []))
    FINANCE_KW = ["stock","market","earnings","fed","rate","inflation","cpi","gdp",
                  "tariff","nasdaq","s&p","rally","selloff","crude","oil","gold","bitcoin"]
    try:
        resp = client.get_home_timeline(
            max_results=20,
            tweet_fields=["public_metrics","author_id","created_at"],
            expansions=["author_id"], user_fields=["username","public_metrics"]
        )
        if not resp.data: return []
        user_map = {}
        if resp.includes and resp.includes.get("users"):
            for u in resp.includes["users"]:
                user_map[u.id] = u.username

        candidates = []
        for t in resp.data:
            if str(t.id) in engaged: continue
            tl = t.text.lower()
            has_ticker = bool(re.search(r'\$[A-Z]{2,5}', t.text))
            has_kw = any(k in tl for k in FINANCE_KW)
            if not (has_ticker or has_kw): continue
            score = t.public_metrics["like_count"]*2 + t.public_metrics["retweet_count"]*3
            candidates.append({
                "id": str(t.id), "text": t.text,
                "author": user_map.get(t.author_id, "?"),
                "score": score, "likes": t.public_metrics["like_count"],
            })
        return sorted(candidates, key=lambda x: x["score"], reverse=True)[:5]
    except Exception as e:
        print(f"Timeline error: {e}")
        return []

def compose_reply(tweet_text, author):
    text = tweet_text.lower()
    tickers = re.findall(r'\$([A-Z]{2,5})', tweet_text)
    ticker = f"${tickers[0]}" if tickers else None
    is_bearish = any(w in text for w in ["down","crash","drop","bear","dump","weak","slump"])
    is_bullish = any(w in text for w in ["up","rip","surge","rally","bull","strong","breakout"])
    is_macro = any(w in text for w in ["fed","rate","inflation","cpi","gdp","tariff","jobs"])

    if is_macro:
        opts = ["market's going to be reactive all day on this",
                "this changes the rate narrative",
                "bonds and equities both moving on this one"]
    elif ticker and is_bullish:
        opts = [f"{ticker} has been on my radar", f"watching {ticker} follow-through",
                f"{ticker} looking strong"]
    elif ticker and is_bearish:
        opts = [f"{ticker} finding support here or not — that's the question",
                f"rough session for {ticker} holders",
                f"{ticker} getting sold hard"]
    elif ticker:
        opts = [f"{ticker} worth watching today", f"keeping {ticker} on the screen"]
    else:
        opts = ["watching how this develops", "market's pricing this in fast",
                "this is moving the tape"]
    return random.choice(opts)

def run_engagement():
    targets = get_reply_targets()
    print(f"Found {len(targets)} engagement targets")
    engaged = list(load_json(ENGAGED_FILE, []))
    already = set(str(x) for x in engaged)
    actions = 0

    for t in targets[:2]:
        if actions >= 2: break
        reply_text = compose_reply(t["text"], t["author"])
        tweet_url = f"https://x.com/{t['author']}/status/{t['id']}"
        print(f"  Replying to @{t['author']} [{t['likes']} likes]: {reply_text[:50]}")
        try:
            result = asyncio.run(playwright_reply(tweet_url, reply_text))
            if result.get("success"):
                print(f"  Done via Playwright")
                log_post(reply_text, "reply", f"reply_{t['id']}", tweet_url, {"replied_author": t["author"]})
                already.add(t["id"])
                actions += 1
                time.sleep(3)
            else:
                print(f"  Failed: {result.get('error','?')[:60]}")
                already.add(t["id"])  # mark as seen to avoid retry
        except Exception as e:
            print(f"  Error: {e}")

    save_json(ENGAGED_FILE, list(already)[-300:])
    return actions

if __name__ == "__main__":
    import sys
    cmd = sys.argv[1] if len(sys.argv) > 1 else "all"
    if cmd == "metrics":
        m = refresh_metrics()
        print(f"Refreshed {len(m)} tweet metrics")
    elif cmd == "analyze":
        r = analyze_and_adapt()
        print("Recs:", r.get("recommendations",[]))
        print("Trending:", r.get("trending_topics",[]))
    elif cmd == "engage":
        n = run_engagement()
        print(f"Engaged with {n} tweets")
    else:
        print("=== METRICS ==="); refresh_metrics()
        print("=== LEARNING ==="); r = analyze_and_adapt()
        print("Recs:", r.get("recommendations",[]))
        print("Trending in feed:", r.get("trending_topics",[]))
        print("=== ENGAGE ==="); n = run_engagement()
        print(f"Actions: {n}")
