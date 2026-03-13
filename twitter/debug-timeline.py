#!/usr/bin/env python3
import json
from pathlib import Path
import tweepy

creds = json.loads(Path("config/twitter-api.json").read_text())
client = tweepy.Client(
    consumer_key=creds["consumer_key"], consumer_secret=creds["consumer_secret"],
    access_token=creds["access_token"], access_token_secret=creds["access_token_secret"],
    bearer_token=creds["bearer_token"], wait_on_rate_limit=True
)

# Check what timeline returns and why candidates are 0
resp = client.get_home_timeline(
    max_results=10,
    tweet_fields=["public_metrics","author_id"],
    expansions=["author_id"],
    user_fields=["username"]
)
if resp.data:
    user_map = {u.id: u.username for u in (resp.includes.get("users") or [])}
    print(f"Timeline: {len(resp.data)} tweets")
    for t in resp.data[:8]:
        author = user_map.get(t.author_id, "?")
        print(f"  @{author}: {t.text[:100]}")
else:
    print("No timeline data:", resp)
