# -*- coding: utf-8 -*-
"""
Study trending finance tweets + manage follows
Learn language, style, formatting from real accounts
"""
import json, os, sys, time
from pathlib import Path
import tweepy

os.chdir('C:/Users/firas/.openclaw/workspace')

def get_clients():
    creds = json.loads(Path("config/twitter-api.json").read_text())
    client = tweepy.Client(
        consumer_key=creds["consumer_key"], consumer_secret=creds["consumer_secret"],
        access_token=creds["access_token"], access_token_secret=creds["access_token_secret"],
        wait_on_rate_limit=True
    )
    auth = tweepy.OAuth1UserHandler(
        creds["consumer_key"], creds["consumer_secret"],
        creds["access_token"], creds["access_token_secret"]
    )
    api = tweepy.API(auth, wait_on_rate_limit=True)
    return client, api

# Core finance/markets accounts to follow
SEED_ACCOUNTS = [
    "unusual_whales",    # options flow, very popular
    "DeItaone",          # fast headlines
    "markets",           # Bloomberg Markets
    "StockMKTNewz",      # market news
    "FinancialJuice",    # fast news feed
    "MarketWatch",       # market news
    "WSJ",               # Wall Street Journal
    "business",          # Bloomberg
    "Reuters",           # Reuters news
    "CNBC",              # CNBC
    "zerohedge",         # macro/markets commentary
    "TruthGundlach",     # Jeffrey Gundlach macro
    "elerianmohamed",    # Mohamed El-Erian commentary
    "RaoulGMI",          # Raoul Pal macro
    "JSeyff",            # Jason Seifer trading
    "alphatrends",       # technical analysis
    "Convertbond",       # markets commentary
    "thestalwart",       # Joe Weisenthal Bloomberg
    "traceyalloway",     # Tracy Alloway Bloomberg
    "muddywatersre",     # short seller Carson Block
    "BurryArchive",      # Michael Burry posts
]

def follow_accounts(client, api):
    results = {"followed": [], "already": [], "failed": []}
    for handle in SEED_ACCOUNTS:
        try:
            user = client.get_user(username=handle, user_fields=["id", "name", "public_metrics"])
            if user.data:
                uid = user.data.id
                try:
                    api.create_friendship(user_id=uid)
                    followers = user.data.public_metrics.get("followers_count", 0)
                    print(f"  Followed @{handle} ({followers:,} followers)")
                    results["followed"].append(handle)
                    time.sleep(0.5)
                except tweepy.errors.Forbidden:
                    results["already"].append(handle)
                except Exception as e:
                    print(f"  Failed @{handle}: {e}")
                    results["failed"].append(handle)
        except Exception as e:
            print(f"  Error @{handle}: {e}")
            results["failed"].append(handle)
    return results

def study_trending_tweets(client, tickers):
    """Pull real tweets about trending tickers, analyze language"""
    studied = {}
    for ticker in tickers[:5]:
        query = f"${ticker} -is:retweet lang:en"
        try:
            tweets = client.search_recent_tweets(
                query=query,
                max_results=20,
                tweet_fields=["public_metrics", "created_at", "text"],
                sort_order="relevancy"
            )
            if not tweets.data:
                continue

            # Sort by engagement
            sorted_tweets = sorted(
                tweets.data,
                key=lambda t: (t.public_metrics["like_count"] + t.public_metrics["retweet_count"]),
                reverse=True
            )

            top = sorted_tweets[:5]
            studied[ticker] = [
                {
                    "text": t.text[:200],
                    "likes": t.public_metrics["like_count"],
                    "rts": t.public_metrics["retweet_count"],
                    "len": len(t.text)
                }
                for t in top
            ]

            print(f"\n  === ${ticker} top tweets ===")
            for t in top[:3]:
                print(f"  [{t.public_metrics['like_count']} likes | {t.public_metrics['retweet_count']} RTs]")
                print(f"  {t.text[:150]}")
                print()

        except Exception as e:
            print(f"  Error searching {ticker}: {e}")

    # Save study results
    study_file = Path("logs/tweet-studies.json")
    existing = {}
    if study_file.exists():
        try: existing = json.loads(study_file.read_text())
        except: pass
    existing.update(studied)
    study_file.write_text(json.dumps(existing, indent=2))
    return studied

def get_my_stats(client):
    me = client.get_me(user_fields=["public_metrics"])
    m = me.data.public_metrics
    print(f"\n@jeeniferdq stats:")
    print(f"  Followers: {m['followers_count']}")
    print(f"  Following: {m['following_count']}")
    print(f"  Tweets: {m['tweet_count']}")
    return m

def search_finance_to_engage(client):
    """Find high-engagement tweets to learn from"""
    queries = [
        "stock market today -is:retweet lang:en",
        "earnings beat -is:retweet lang:en has:cashtags",
        "unusual volume -is:retweet lang:en has:cashtags",
    ]
    all_tweets = []
    for q in queries:
        try:
            r = client.search_recent_tweets(
                query=q, max_results=10,
                tweet_fields=["public_metrics", "text", "author_id"],
                sort_order="relevancy"
            )
            if r.data:
                all_tweets.extend(r.data)
        except: pass

    # Show high performers
    top = sorted(all_tweets, key=lambda t: t.public_metrics["like_count"], reverse=True)[:10]
    print("\n=== HIGH-PERFORMING FINANCE TWEETS (for style study) ===")
    for t in top:
        likes = t.public_metrics["like_count"]
        rts = t.public_metrics["retweet_count"]
        if likes > 0:
            print(f"\n[{likes} likes | {rts} RTs | {len(t.text)} chars]")
            print(t.text[:250])

    return top

if __name__ == "__main__":
    import requests, warnings
    warnings.filterwarnings('ignore')
    H = {"User-Agent": "Mozilla/5.0"}

    client, api = get_clients()

    print("=== @jeeniferdq STATS ===")
    get_my_stats(client)

    if "--follow" in sys.argv or "--all" in sys.argv:
        print("\n=== FOLLOWING SEED ACCOUNTS ===")
        results = follow_accounts(client, api)
        print(f"\nFollowed: {len(results['followed'])}")
        print(f"Already following: {len(results['already'])}")

    if "--study" in sys.argv or "--all" in sys.argv:
        # Get trending tickers to study
        r = requests.get("https://query1.finance.yahoo.com/v1/finance/trending/US?count=10",
                        headers=H, timeout=8, verify=False)
        tickers = []
        if r.status_code == 200:
            qs = r.json()["finance"]["result"][0]["quotes"]
            tickers = [q["symbol"] for q in qs if not q["symbol"].endswith("-USD")][:5]
        print(f"\n=== STUDYING TWEETS FOR: {tickers} ===")
        study_results = study_trending_tweets(client, tickers)

    if "--engage" in sys.argv or "--all" in sys.argv:
        print("\n=== STUDYING HIGH-ENGAGEMENT FINANCE TWEETS ===")
        search_finance_to_engage(client)

    if not any(a in sys.argv for a in ["--follow", "--study", "--engage", "--all"]):
        print("\nUsage: python study-and-follow.py [--follow] [--study] [--engage] [--all]")
        get_my_stats(client)
