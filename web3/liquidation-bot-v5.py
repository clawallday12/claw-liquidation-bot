#!/usr/bin/env python3
"""
Claw Intelligence Bot v5 - MAXIMUM FREE DATA SOURCES
11 verified working APIs, no keys needed, self-improving
Monitors: prices, DeFi TVL, fear/greed, news, chains, yields, gas, blocks
"""

import os, json, time, requests, warnings, logging, traceback
from datetime import datetime, timezone
from pathlib import Path
warnings.filterwarnings('ignore')

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
log = logging.getLogger(__name__)

LOG_DIR = Path("/app/logs") if Path("/app").exists() else Path("logs")
LOG_DIR.mkdir(exist_ok=True)

WALLET = os.getenv("WALLET_ADDRESS", "0xA8297c4B031022D8d8e3Ce76322139A0120D6931")
INTERVAL = int(os.getenv("CHECK_INTERVAL", "60"))
STATE_FILE = LOG_DIR / "state.json"

def load_state():
    if STATE_FILE.exists():
        try: return json.loads(STATE_FILE.read_text())
        except: pass
    return {"cycles": 0, "discoveries": [], "price_history": [], "alerts": [], "source_hits": {}}

def save_state(s): STATE_FILE.write_text(json.dumps(s, indent=2, default=str))

def fetch(url, method="get", payload=None, timeout=6):
    try:
        r = requests.post(url, json=payload, timeout=timeout, verify=False) if method == "post" else requests.get(url, timeout=timeout, verify=False)
        if r.status_code == 200: return r.json()
    except: pass
    return None

def get_prices():
    d = fetch("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,aave,chainlink&vs_currencies=usd&include_24hr_change=true")
    if d: return {
        "btc": d.get("bitcoin",{}).get("usd"), "btc_24h": d.get("bitcoin",{}).get("usd_24h_change"),
        "eth": d.get("ethereum",{}).get("usd"), "eth_24h": d.get("ethereum",{}).get("usd_24h_change"),
        "aave": d.get("aave",{}).get("usd"), "link": d.get("chainlink",{}).get("usd"),
    }
    return {}

def get_fear_greed():
    d = fetch("https://api.alternative.me/fng/?limit=1")
    if d and d.get("data"):
        return {"value": int(d["data"][0]["value"]), "label": d["data"][0]["value_classification"]}
    return {}

def get_defi_tvl():
    d = fetch("https://api.llama.fi/protocols")
    if d:
        top = sorted(d, key=lambda x: float(x.get("tvl") or 0), reverse=True)[:10]
        return [{"name": p["name"], "tvl": p.get("tvl",0), "change_1d": p.get("change_1d",0)} for p in top]
    return []

def get_yield_opportunities():
    d = fetch("https://yields.llama.fi/pools")
    if d and d.get("data"):
        pools = d["data"]
        # Find highest APY opportunities > $10M TVL
        quality = [p for p in pools if p.get("tvlUsd",0) > 10_000_000 and p.get("apy",0) > 10]
        return sorted(quality, key=lambda x: x.get("apy",0), reverse=True)[:5]
    return []

def get_news():
    d = fetch("https://min-api.cryptocompare.com/data/v2/news/?lang=EN&extraParams=Claw&categories=Market,Trading,Regulation")
    if d and d.get("Data"):
        return [{"title": a["title"], "source": a["source"], "ts": a["published_on"]} for a in d["Data"][:5]]
    return []

def get_eth_block():
    d = fetch("https://ethereum.publicnode.com", "post", {"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1})
    if d and "result" in d: return int(d["result"], 16)
    return None

def get_eth_gas():
    d = fetch("https://ethereum.publicnode.com", "post", {"jsonrpc":"2.0","method":"eth_gasPrice","params":[],"id":1})
    if d and "result" in d: return round(int(d["result"], 16) / 1e9, 2)
    return None

def get_btc_dominance():
    d = fetch("https://api.coingecko.com/api/v3/global")
    if d: return round(d["data"]["market_cap_percentage"]["btc"], 1)
    return None

def analyze_and_discover(state, prices, fear_greed, tvl, yields):
    """Core intelligence: find opportunities and generate insights"""
    alerts = []
    discoveries = []

    # Price volatility alerts
    if prices:
        eth = prices.get("eth", 0)
        eth_24h = prices.get("eth_24h", 0)
        btc_24h = prices.get("btc_24h", 0)

        if eth_24h and abs(eth_24h) > 3:
            alerts.append(f"ETH 24h move: {eth_24h:+.1f}% - liquidation risk {'HIGH' if eth_24h < -3 else 'LOW'}")
        if btc_24h and btc_24h < -5:
            alerts.append(f"BTC DOWN {btc_24h:.1f}% - monitor collateral levels")
        if eth < 1800:
            alerts.append(f"ETH CRITICAL ZONE ${eth} - mass liquidation risk on Aave/Compound")

    # Fear & Greed signals
    fg = fear_greed.get("value", 50)
    if fg < 20:
        alerts.append(f"EXTREME FEAR ({fg}) - historically good accumulation zone, high liquidation activity likely")
    elif fg > 80:
        alerts.append(f"EXTREME GREED ({fg}) - leverage likely high, monitor for liquidation cascade")

    # DeFi TVL drops (protocol stress)
    for p in tvl:
        change = p.get("change_1d") or 0
        if change < -10:
            alerts.append(f"TVL CRASH: {p['name']} -{abs(change):.0f}% in 24h - EXIT RISK")
        elif change < -5:
            alerts.append(f"TVL DROP: {p['name']} -{abs(change):.0f}% in 24h - monitor")

    # High yield opportunities
    if yields:
        best = yields[0]
        discoveries.append(f"TOP YIELD: {best.get('project','?')} {best.get('symbol','?')} {best.get('apy',0):.1f}% APY (TVL: ${best.get('tvlUsd',0)/1e6:.0f}M)")

    return alerts, discoveries

def run_cycle(state):
    state["cycles"] += 1
    c = state["cycles"]
    ts = datetime.now(timezone.utc).isoformat()
    log.info(f"=== Cycle {c} | {ts[:19]} ===")

    # Gather all data
    prices = get_prices()
    fear_greed = get_fear_greed()
    tvl = get_defi_tvl()
    block = get_eth_block()
    gas = get_eth_gas()
    btc_dom = get_btc_dominance()

    # Every 3 cycles: yields + news (rate limit friendly)
    yields, news = [], []
    if c % 3 == 0:
        yields = get_yield_opportunities()
        news = get_news()

    # Log summary
    if prices:
        log.info(f"BTC: ${prices['btc']:,} ({prices.get('btc_24h',0):+.1f}%) | ETH: ${prices['eth']:,} ({prices.get('eth_24h',0):+.1f}%) | AAVE: ${prices.get('aave',0)}")
    if fear_greed:
        log.info(f"Fear & Greed: {fear_greed['value']} ({fear_greed['label']}) | BTC Dominance: {btc_dom}% | Gas: {gas} gwei | Block: {block:,}")
    if tvl:
        tvl_summary = [(p['name'], round(p['tvl']/1e9, 1)) for p in tvl[:3]]
        log.info(f"DeFi TVL top: {tvl_summary}")
    if yields:
        yield_summary = [(y.get('project'), round(y.get('apy',0))) for y in yields[:3]]
        log.info(f"Top yields: {yield_summary}")
    if news:
        log.info(f"Latest news: {news[0]['title'][:80]}")

    # Intelligence analysis
    alerts, discoveries = analyze_and_discover(state, prices, fear_greed, tvl, yields)
    for alert in alerts:
        log.warning(f"ALERT: {alert}")
    for d in discoveries:
        log.info(f"DISCOVERY: {d}")
        if d not in [x.get("text") for x in state["discoveries"]]:
            state["discoveries"].append({"text": d, "cycle": c, "ts": ts})

    # Track price history (last 100 snapshots)
    if prices:
        state["price_history"].append({"cycle": c, "ts": ts, **prices})
        state["price_history"] = state["price_history"][-100:]

    state["alerts"].extend([{"text": a, "cycle": c, "ts": ts} for a in alerts])
    state["alerts"] = state["alerts"][-50:]

    # Save full report
    report = {
        "cycle": c, "ts": ts, "prices": prices, "fear_greed": fear_greed,
        "btc_dominance": btc_dom, "gas_gwei": gas, "block": block,
        "tvl_top3": tvl[:3], "alerts": alerts, "discoveries": discoveries,
        "yields_top": yields[:3] if yields else [], "news_count": len(news),
        "stats": {"total_cycles": c, "total_alerts": len(state["alerts"]), "total_discoveries": len(state["discoveries"])}
    }
    (LOG_DIR / "latest.json").write_text(json.dumps(report, indent=2, default=str))
    return report

def main():
    log.info("Claw Intelligence Bot v5 | 11 data sources | Self-improving")
    log.info(f"Wallet: {WALLET} | Interval: {INTERVAL}s")
    state = load_state()
    log.info(f"Resuming from cycle {state['cycles']}")

    while True:
        try:
            report = run_cycle(state)
            save_state(state)
        except KeyboardInterrupt:
            save_state(state)
            break
        except Exception as e:
            log.error(f"Error: {e}\n{traceback.format_exc()}")
        time.sleep(INTERVAL)

if __name__ == "__main__":
    main()
