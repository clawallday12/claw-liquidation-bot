#!/usr/bin/env python3
import json
from pathlib import Path
from datetime import datetime

log_file = Path("logs/twitter-posts.json")
state_file = Path("logs/brain-state.json")

log = json.loads(log_file.read_text()) if log_file.exists() else []
state = json.loads(state_file.read_text()) if state_file.exists() else {}

print(f"Total tweets posted: {len(log)}")
print("\nLast 5 posts:")
for p in log[-5:]:
    ts = p["ts"][:16]
    ptype = p["type"]
    text = p["text"][:70].replace("\n", " ")
    url = p["url"]
    print(f"  [{ts}] [{ptype}]")
    print(f"  {text}")
    print(f"  {url}")
    print()

if log:
    last = datetime.fromisoformat(log[-1]["ts"])
    mins = (datetime.now() - last).total_seconds() / 60
    print(f"Last post: {mins:.0f} min ago")

seen = state.get("seen_movers", {})
print(f"Seen movers this session: {list(seen.keys())}")
