#!/usr/bin/env python3
import requests, warnings, json
warnings.filterwarnings('ignore')

# Etherscan free calls without key
endpoints = [
    ("gasoracle", "https://api.etherscan.io/api?module=gastracker&action=gasoracle"),
    ("ethprice", "https://api.etherscan.io/api?module=stats&action=ethprice"),
    ("ethsupply", "https://api.etherscan.io/api?module=stats&action=ethsupply"),
]

print("Testing Etherscan without API key...")
for name, url in endpoints:
    r = requests.get(url, timeout=6, verify=False)
    if r.status_code == 200:
        data = r.json()
        status = data.get("status")
        msg = data.get("message", "")
        result = str(data.get("result", ""))[:100]
        print(f"  {name}: status={status} msg={msg} result={result}")
    else:
        print(f"  {name}: HTTP {r.status_code}")
