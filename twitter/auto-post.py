#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Cron-safe auto-poster - called every 30min by OpenClaw"""
import sys, os
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
os.chdir('C:/Users/firas/.openclaw/workspace')

from datetime import datetime
import json
from pathlib import Path

# Avoid double-posting: check if we posted in the last 20 min
LOG = Path("logs/twitter-posts.json")
def recently_posted(minutes=20):
    if not LOG.exists(): return False
    try:
        posts = json.loads(LOG.read_text())
        if not posts: return False
        last = posts[-1]["ts"]
        last_dt = datetime.fromisoformat(last)
        diff = (datetime.now() - last_dt).total_seconds() / 60
        return diff < minutes
    except: return False

if recently_posted(20):
    print(f"Posted recently, skipping this cycle")
    sys.exit(0)

# Import and run
exec(open('twitter/tweeter.py').read())
tweet_id, url = auto_post()
if url:
    print(f"Posted: {url}")
else:
    print("No post generated for this time slot")
