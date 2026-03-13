#!/usr/bin/env python3
import requests, warnings, json
warnings.filterwarnings('ignore')
H = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

for sym in ['CE', 'CF', 'FLY', 'LYB', 'OLN']:
    info = {}
    # Profile / sector
    r = requests.get(f'https://query2.finance.yahoo.com/v10/finance/quoteSummary/{sym}?modules=assetProfile', headers=H, timeout=8, verify=False)
    if r.status_code == 200:
        res = r.json().get('quoteSummary', {}).get('result', [])
        if res:
            p = res[0].get('assetProfile', {})
            info['sector'] = p.get('sector', '?')
            info['industry'] = p.get('industry', '?')

    # News
    r2 = requests.get(f'https://query1.finance.yahoo.com/v2/finance/news?symbols={sym}&count=3', headers=H, timeout=8, verify=False)
    if r2.status_code == 200:
        items = r2.json().get('items', {}).get('result', [])
        info['news'] = [i.get('title', '') for i in items[:3]]

    print(f"\n{sym}: {info.get('sector','?')} / {info.get('industry','?')}")
    for n in info.get('news', []):
        print(f"  - {n}")
