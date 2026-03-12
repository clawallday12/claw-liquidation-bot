#!/usr/bin/env python3
"""
Discover and test all free APIs that need zero authentication
Build maximum capability without waiting for email verification
"""
import requests, json, warnings, time
warnings.filterwarnings('ignore')

RESULTS = {}

def test(name, url, method="get", payload=None, headers=None, parse=None):
    try:
        h = headers or {}
        if method == "get":
            r = requests.get(url, headers=h, timeout=6, verify=False)
        else:
            r = requests.post(url, json=payload, headers=h, timeout=6, verify=False)
        
        if r.status_code == 200:
            data = r.json()
            result = parse(data) if parse else "OK"
            print(f"  [OK] {name}: {result}")
            RESULTS[name] = {"status": "working", "sample": str(result)[:100]}
            return data
        else:
            print(f"  [FAIL] {name}: HTTP {r.status_code}")
            RESULTS[name] = {"status": f"HTTP {r.status_code}"}
    except Exception as e:
        print(f"  [FAIL] {name}: {str(e)[:60]}")
        RESULTS[name] = {"status": f"error: {str(e)[:60]}"}
    return None

print("=== FREE API DISCOVERY ===\n")

print("[1] Crypto Market Data (no key)")
test("CoinGecko prices", "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd",
     parse=lambda d: f"BTC=${d['bitcoin']['usd']:,} ETH=${d['ethereum']['usd']:,}")
test("CoinGecko trending", "https://api.coingecko.com/api/v3/trending",
     parse=lambda d: [c['item']['name'] for c in d['coins'][:3]])
test("Binance BTC price", "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT",
     parse=lambda d: f"BTC=${float(d['price']):,.2f}")
test("Binance top pairs", "https://api.binance.com/api/v3/ticker/24hr",
     parse=lambda d: f"{len(d)} pairs, top mover: {sorted(d, key=lambda x: float(x.get('priceChangePercent',0)), reverse=True)[0]['symbol']}")
test("Binance orderbook BTC", "https://api.binance.com/api/v3/depth?symbol=BTCUSDT&limit=5",
     parse=lambda d: f"bid={d['bids'][0][0]} ask={d['asks'][0][0]}")

print("\n[2] DeFi Data (no key)")
test("DeFiLlama TVL", "https://api.llama.fi/protocols",
     parse=lambda d: f"{len(d)} protocols, top: {d[0]['name']} ${d[0]['tvl']/1e9:.1f}B")
test("DeFiLlama chains", "https://api.llama.fi/chains",
     parse=lambda d: f"Top chains: {[c['name'] for c in sorted(d, key=lambda x: x.get('tvl',0), reverse=True)[:3]]}")
test("DeFiLlama yields", "https://yields.llama.fi/pools",
     parse=lambda d: f"{len(d.get('data',[]))} yield pools")

print("\n[3] Blockchain/On-chain (no key)")
test("ETH block", "https://ethereum.publicnode.com", method="post",
     payload={"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1},
     parse=lambda d: f"Block {int(d['result'],16):,}")
test("ETH gas", "https://ethereum.publicnode.com", method="post",
     payload={"jsonrpc":"2.0","method":"eth_gasPrice","params":[],"id":1},
     parse=lambda d: f"Gas: {int(d['result'],16)/1e9:.1f} gwei")
test("Polygon block", "https://polygon-rpc.com", method="post",
     payload={"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1},
     parse=lambda d: f"Block {int(d['result'],16):,}")

print("\n[4] Market Intelligence (no key)")
test("Fear & Greed Index", "https://api.alternative.me/fng/?limit=1",
     parse=lambda d: f"{d['data'][0]['value']} ({d['data'][0]['value_classification']})")
test("BTC dominance", "https://api.coingecko.com/api/v3/global",
     parse=lambda d: f"BTC dominance: {d['data']['market_cap_percentage']['btc']:.1f}%")
test("DeFi stats", "https://api.coingecko.com/api/v3/global/decentralized_finance_defi",
     parse=lambda d: f"DeFi TVL: ${float(d['data']['defi_market_cap'])/1e9:.1f}B")

print("\n[5] News/Content (no key)")
test("CryptoCompare news", "https://min-api.cryptocompare.com/data/v2/news/?lang=EN&extraParams=Claw",
     parse=lambda d: f"{len(d.get('Data',[]))} articles, latest: {d.get('Data',[{}])[0].get('title','?')[:50]}")

print("\n[6] Coinglass Derivatives (no key needed)")
test("Coinglass funding", "https://open-api.coinglass.com/public/v2/funding?symbol=BTC",
     parse=lambda d: f"code={d.get('code')} success={d.get('success')}")

print("\n=== SUMMARY ===")
working = [k for k,v in RESULTS.items() if v['status'] == 'working']
print(f"Working APIs: {len(working)}/{len(RESULTS)}")
for k in working:
    print(f"  + {k}")

# Save
with open("config/free-apis.json", "w") as f:
    json.dump(RESULTS, f, indent=2)
print(f"\nSaved to config/free-apis.json")
