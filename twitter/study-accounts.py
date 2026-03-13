# -*- coding: utf-8 -*-
"""Study real finance Twitter accounts via RSS + scraping. No search tier needed."""
import json, os, sys, re, requests, warnings, time
from pathlib import Path
from datetime import datetime
import tweepy

os.chdir('C:/Users/firas/.openclaw/workspace')
warnings.filterwarnings('ignore')
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

ACCOUNTS_TO_STUDY = [
    "unusual_whales", "DeItaone", "StockMKTNewz",
    "FinancialJuice", "zerohedge", "thestalwart",
    "traceyalloway", "markets", "WSJ", "business"
]

ACCOUNTS_TO_FOLLOW = [
    "unusual_whales", "DeItaone", "StockMKTNewz", "FinancialJuice",
    "markets", "MarketWatch", "WSJ", "business", "Reuters", "CNBC",
    "zerohedge", "elerianmohamed", "thestalwart", "traceyalloway",
    "alphatrends", "Convertbond", "muddywatersre", "BurryArchive",
    "RaoulGMI", "TruthGundlach", "LiveSquawk", "FirstSquawk",
    "FT", "TheEconomist", "bespokeinvest", "sentimentrader",
]

def get_nitter_feed(handle):
    """Get tweets via nitter RSS - works without API key"""
    instances = [
        f"https://nitter.net/{handle}/rss",
        f"https://nitter.privacydev.net/{handle}/rss",
        f"https://nitter.poast.org/{handle}/rss",
    ]
    for url in instances:
        try:
            r = requests.get(url, headers=H, timeout=10, verify=False)
            if r.status_code == 200 and '<item>' in r.text:
                items = re.findall(r'<title><!\[CDATA\[(.*?)\]\]></title>', r.text)
                descs = re.findall(r'<description><!\[CDATA\[(.*?)\]\]></description>', r.text)
                tweets = []
                for i, (title, desc) in enumerate(zip(items[1:], descs[1:])):
                    clean = re.sub(r'<[^>]+>', ' ', desc).strip()
                    clean = re.sub(r'\s+', ' ', clean)[:280]
                    tweets.append(clean)
                return tweets[:10]
        except: continue
    return []

def study_all_accounts():
    findings = {}
    print("Studying top finance accounts...\n")
    for handle in ACCOUNTS_TO_STUDY:
        tweets = get_nitter_feed(handle)
        if tweets:
            print(f"@{handle} ({len(tweets)} tweets):")
            for t in tweets[:3]:
                print(f"  > {t[:120]}")
            findings[handle] = tweets
            print()
        else:
            print(f"@{handle}: no data from nitter")
    Path("logs/account-studies.json").write_text(json.dumps(findings, indent=2))
    return findings

def analyze_style(findings):
    """Extract patterns from what we studied"""
    all_tweets = []
    for handle, tweets in findings.items():
        all_tweets.extend(tweets)

    if not all_tweets:
        return

    # Length analysis
    lengths = [len(t) for t in all_tweets]
    avg_len = sum(lengths) / len(lengths) if lengths else 0

    # Common patterns
    has_cashtag = sum(1 for t in all_tweets if '$' in t)
    has_percent = sum(1 for t in all_tweets if '%' in t)
    has_question = sum(1 for t in all_tweets if '?' in t)
    short_posts = sum(1 for t in all_tweets if len(t) < 100)

    print("\n=== STYLE ANALYSIS ===")
    print(f"Total tweets studied: {len(all_tweets)}")
    print(f"Avg tweet length: {avg_len:.0f} chars")
    print(f"With $TICKER: {has_cashtag}/{len(all_tweets)} ({100*has_cashtag/len(all_tweets):.0f}%)")
    print(f"With %: {has_percent}/{len(all_tweets)} ({100*has_percent/len(all_tweets):.0f}%)")
    print(f"With ?: {has_question}/{len(all_tweets)}")
    print(f"Short (<100 chars): {short_posts}/{len(all_tweets)} ({100*short_posts/len(all_tweets):.0f}%)")

    print("\n=== SHORTEST HIGH-SIGNAL POSTS ===")
    short = sorted([t for t in all_tweets if 20 < len(t) < 120], key=len)[:10]
    for t in short:
        print(f"  [{len(t)}] {t}")

def follow_via_v2(client, api):
    """Follow accounts using available API methods"""
    creds = json.loads(Path("config/twitter-api.json").read_text())
    me = client.get_me()
    my_id = me.data.id

    followed = []
    for handle in ACCOUNTS_TO_FOLLOW:
        try:
            # Get user ID first using bearer token
            bearer_client = tweepy.Client(bearer_token=creds["bearer_token"])
            user = bearer_client.get_user(username=handle)
            if not user.data:
                continue
            uid = user.data.id

            # Follow via v2 with user auth
            r = client.follow_user(uid)
            if r.data and r.data.get("following"):
                print(f"  Followed @{handle}")
                followed.append(handle)
            elif r.data and r.data.get("pending_follow"):
                print(f"  Pending @{handle} (protected)")
            time.sleep(0.5)
        except tweepy.errors.Forbidden as e:
            if "already" in str(e).lower():
                pass  # already following
            else:
                print(f"  Blocked @{handle}: {str(e)[:50]}")
        except Exception as e:
            print(f"  Failed @{handle}: {str(e)[:60]}")

    print(f"\nFollowed {len(followed)} new accounts")
    return followed

if __name__ == "__main__":
    creds = json.loads(Path("config/twitter-api.json").read_text())
    client = tweepy.Client(
        consumer_key=creds["consumer_key"], consumer_secret=creds["consumer_secret"],
        access_token=creds["access_token"], access_token_secret=creds["access_token_secret"],
        bearer_token=creds["bearer_token"],
        wait_on_rate_limit=True
    )
    auth = tweepy.OAuth1UserHandler(
        creds["consumer_key"], creds["consumer_secret"],
        creds["access_token"], creds["access_token_secret"]
    )
    api = tweepy.API(auth, wait_on_rate_limit=True)

    # Stats
    me = client.get_me(user_fields=["public_metrics"])
    m = me.data.public_metrics
    print(f"@jeeniferdq: {m['followers_count']} followers | {m['following_count']} following | {m['tweet_count']} tweets\n")

    # Study
    print("=== STUDYING ACCOUNTS ===")
    findings = study_all_accounts()
    analyze_style(findings)

    # Follow
    print("\n=== FOLLOWING RELEVANT ACCOUNTS ===")
    follow_via_v2(client, api)
