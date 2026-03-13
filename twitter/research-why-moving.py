#!/usr/bin/env python3
"""Find WHY a stock is moving - news, context, catalyst"""
import requests, warnings, sys
warnings.filterwarnings('ignore')
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

def get_catalyst(symbol):
    results = []
    # Yahoo Finance news
    try:
        r = requests.get(f"https://query1.finance.yahoo.com/v2/finance/news?symbols={symbol}&count=5", headers=HEADERS, timeout=8, verify=False)
        if r.status_code == 200:
            items = r.json().get("items",{}).get("result",[])
            for i in items[:5]:
                results.append(i.get("title",""))
    except: pass

    # Yahoo Finance summary/profile for context
    try:
        r2 = requests.get(f"https://query2.finance.yahoo.com/v10/finance/quoteSummary/{symbol}?modules=assetProfile,summaryDetail,defaultKeyStatistics", headers=HEADERS, timeout=8, verify=False)
        if r2.status_code == 200:
            data = r2.json().get("quoteSummary",{}).get("result",[{}])[0]
            profile = data.get("assetProfile",{})
            results.append(f"Sector: {profile.get('sector','?')} | Industry: {profile.get('industry','?')}")
    except: pass

    return results

if __name__ == "__main__":
    sym = sys.argv[1] if len(sys.argv) > 1 else "CE"
    print(f"Catalyst research: {sym}")
    for item in get_catalyst(sym):
        print(f"  {item}")
