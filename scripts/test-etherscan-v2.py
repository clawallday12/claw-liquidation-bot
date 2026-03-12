#!/usr/bin/env python3
import requests, warnings, json
warnings.filterwarnings('ignore')

# Etherscan V2 - try with no key and with demo key
BASE = "https://api.etherscan.io/v2/api"

tests = [
    ("gas_no_key",  f"{BASE}?chainid=1&module=gastracker&action=gasoracle"),
    ("gas_demo",    f"{BASE}?chainid=1&module=gastracker&action=gasoracle&apikey=YourApiKeyToken"),
    ("price_v2",    f"{BASE}?chainid=1&module=stats&action=ethprice&apikey=YourApiKeyToken"),
]

print("Testing Etherscan V2...")
for name, url in tests:
    r = requests.get(url, timeout=6, verify=False)
    data = r.json() if r.status_code == 200 else {}
    result = str(data.get("result", ""))[:120]
    msg = data.get("message", "")
    print(f"  {name}: status={data.get('status')} msg={msg}")
    if result: print(f"    result={result}")
