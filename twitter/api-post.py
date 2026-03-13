#!/usr/bin/env python3
"""Post tweets via Twitter API v2"""
import json, sys, tweepy
from pathlib import Path

creds = json.loads(Path("config/twitter-api.json").read_text())

def get_client():
    # Try OAuth 2.0 with bearer (read-only) + OAuth 1.0a for posting
    client = tweepy.Client(
        bearer_token=creds["bearer_token"],
        consumer_key=creds["consumer_key"],
        consumer_secret=creds["consumer_secret"],
        access_token=creds.get("access_token") or None,
        access_token_secret=creds.get("access_token_secret") or None,
        wait_on_rate_limit=True
    )
    return client

def post_tweet(text: str):
    client = get_client()
    try:
        response = client.create_tweet(text=text)
        tweet_id = response.data["id"]
        print(f"Posted! ID: {tweet_id}")
        print(f"URL: https://twitter.com/jeeniferdq/status/{tweet_id}")
        return {"success": True, "id": tweet_id}
    except tweepy.errors.Unauthorized as e:
        return {"success": False, "error": "unauthorized", "detail": str(e)}
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_auth_url():
    """Get OAuth 1.0a PIN-based auth URL to get access tokens"""
    auth = tweepy.OAuth1UserHandler(
        creds["consumer_key"], creds["consumer_secret"],
        callback="oob"
    )
    url = auth.get_authorization_url()
    print(f"Authorize here: {url}")
    print("Then enter the PIN")
    return auth

if __name__ == "__main__":
    if len(sys.argv) > 1:
        result = post_tweet(sys.argv[1])
        print(json.dumps(result, indent=2))
    else:
        # Test auth
        print("Testing auth...")
        result = post_tweet("test")
        print(result)
