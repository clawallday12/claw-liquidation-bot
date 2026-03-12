#!/usr/bin/env python3
import requests, json, warnings
warnings.filterwarnings('ignore')

print('[1] Testing Aave via The Graph...')
query = '{liquidationCalls(first:5,orderBy:timestamp,orderDirection:desc){user debtToCover collateralAsset timestamp}}'
try:
    r = requests.post('https://api.thegraph.com/subgraphs/name/aave/protocol-v3', json={'query':query}, timeout=8, verify=False)
    print(f'    Status: {r.status_code}')
    if r.status_code == 200:
        d = r.json()
        liqs = d.get('data',{}).get('liquidationCalls',[])
        print(f'    Found {len(liqs)} recent liquidations')
        for l in liqs[:3]:
            user = l['user'][:12]
            debt = l['debtToCover'][:10]
            ts = l['timestamp']
            print(f'    -> user: {user}... debt: {debt}... ts: {ts}')
    else:
        print(f'    Error: {r.text[:200]}')
except Exception as e:
    print(f'    Failed: {e}')

print()
print('[2] Testing CoinGecko...')
try:
    r2 = requests.get('https://api.coingecko.com/api/v3/simple/price?ids=ethereum,bitcoin&vs_currencies=usd', timeout=5, verify=False)
    if r2.status_code == 200:
        prices = r2.json()
        print(f'    BTC: ${prices["bitcoin"]["usd"]:,}')
        print(f'    ETH: ${prices["ethereum"]["usd"]:,}')
    else:
        print(f'    Error: {r2.status_code}')
except Exception as e:
    print(f'    Failed: {e}')

print()
print('[3] Testing Ethereum RPC (publicnode)...')
try:
    payload = {'jsonrpc':'2.0','method':'eth_blockNumber','params':[],'id':1}
    r3 = requests.post('https://ethereum.publicnode.com', json=payload, timeout=5, verify=False)
    if r3.status_code == 200:
        block = int(r3.json()['result'], 16)
        print(f'    Latest block: {block:,}')
    else:
        print(f'    Error: {r3.status_code}')
except Exception as e:
    print(f'    Failed: {e}')
