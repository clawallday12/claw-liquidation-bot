#!/usr/bin/env python3
"""
Claw Bot v7 - PATTERN DETECTION
Adds: ETH drop pattern detection across last 10 cycles from price_history.
Logs PATTERN_ALERT when ETH drops >3% over last 10 cycles.
"""

import os, json, time, requests, warnings, logging, traceback
from datetime import datetime, timezone
from pathlib import Path
from web3 import Web3
warnings.filterwarnings('ignore')

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
log = logging.getLogger(__name__)

LOG_DIR = Path("/app/logs") if Path("/app").exists() else Path("logs")
LOG_DIR.mkdir(exist_ok=True)

# Config
PRIVATE_KEY    = os.getenv("PRIVATE_KEY", "")
WALLET         = os.getenv("WALLET_ADDRESS", "0xA8297c4B031022D8d8e3Ce76322139A0120D6931")
INTERVAL       = int(os.getenv("CHECK_INTERVAL", "60"))
RPC_URL        = "https://ethereum.publicnode.com"
STATE_FILE     = LOG_DIR / "state.json"

# Pattern detection config
PATTERN_WINDOW    = 10     # cycles to look back
PATTERN_DROP_PCT  = 3.0    # % drop threshold

# Web3 setup
w3 = Web3(Web3.HTTPProvider(RPC_URL))

def load_state():
    if STATE_FILE.exists():
        try: return json.loads(STATE_FILE.read_text())
        except: pass
    return {"cycles": 0, "discoveries": [], "price_history": [], "alerts": [],
            "executions": [], "revenue_eth": 0.0, "wallet_balance_eth": 0.0,
            "pattern_alerts": []}

def save_state(s): STATE_FILE.write_text(json.dumps(s, indent=2, default=str))

def fetch(url, method="get", payload=None, timeout=6):
    try:
        r = requests.post(url, json=payload, timeout=timeout, verify=False) if method == "post" else requests.get(url, timeout=timeout, verify=False)
        if r.status_code == 200: return r.json()
    except: pass
    return None

# --- PATTERN DETECTION ---

def detect_eth_drop_pattern(state):
    """
    Reads price_history from state, checks if ETH dropped >PATTERN_DROP_PCT
    over the last PATTERN_WINDOW cycles. Logs PATTERN_ALERT if detected.
    Returns (triggered: bool, drop_pct: float)
    """
    history = state.get("price_history", [])
    if len(history) < 2:
        return False, 0.0

    window = history[-PATTERN_WINDOW:] if len(history) >= PATTERN_WINDOW else history

    # Filter entries that have ETH price
    eth_prices = [e.get("eth") for e in window if e.get("eth")]
    if len(eth_prices) < 2:
        return False, 0.0

    eth_start = eth_prices[0]
    eth_end   = eth_prices[-1]

    if eth_start <= 0:
        return False, 0.0

    drop_pct = ((eth_start - eth_end) / eth_start) * 100.0

    if drop_pct >= PATTERN_DROP_PCT:
        msg = (
            f"PATTERN_ALERT: ETH dropped {drop_pct:.2f}% over last {len(eth_prices)} cycles "
            f"(${eth_start:,.0f} -> ${eth_end:,.0f}) | window={PATTERN_WINDOW} threshold={PATTERN_DROP_PCT}%"
        )
        log.warning(msg)
        return True, drop_pct

    # Log a mild trace so we know detection ran
    log.info(
        f"PatternCheck: ETH {'+' if drop_pct <= 0 else '-'}{abs(drop_pct):.2f}% "
        f"over {len(eth_prices)} cycles (${eth_start:,.0f}→${eth_end:,.0f}) — no alert"
    )
    return False, drop_pct

# --- DATA SOURCES ---

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
        quality = [p for p in d["data"] if p.get("tvlUsd",0) > 10_000_000 and p.get("apy",0) > 10]
        return sorted(quality, key=lambda x: x.get("apy",0), reverse=True)[:5]
    return []

def get_aave_liquidations():
    query = '{liquidationCalls(first:10,orderBy:timestamp,orderDirection:desc){id user liquidator debtToCover collateralAsset debtAsset timestamp}}'
    d = fetch("https://api.thegraph.com/subgraphs/name/aave/protocol-v3", "post", {"query": query})
    if d and "data" in d: return d["data"].get("liquidationCalls", [])
    return []

def get_news():
    d = fetch("https://min-api.cryptocompare.com/data/v2/news/?lang=EN&extraParams=Claw&categories=Market,Trading")
    if d and d.get("Data"):
        return [{"title": a["title"], "source": a["source"]} for a in d["Data"][:3]]
    return []

def get_eth_gas():
    d = fetch("https://api.etherscan.io/v2/api?chainid=1&module=gastracker&action=gasoracle")
    if d and d.get("status") == "1":
        r = d["result"]
        return {"safe": float(r.get("SafeGasPrice",0)), "fast": float(r.get("FastGasPrice",0))}
    d2 = fetch("https://ethereum.publicnode.com", "post", {"jsonrpc":"2.0","method":"eth_gasPrice","params":[],"id":1})
    if d2 and "result" in d2:
        return {"safe": round(int(d2["result"],16)/1e9, 2), "fast": round(int(d2["result"],16)/1e9*1.2, 2)}
    return {"safe": 0, "fast": 0}

# --- WALLET FUNCTIONS ---

def get_wallet_balance():
    try:
        balance_wei = w3.eth.get_balance(WALLET)
        return round(Web3.from_wei(balance_wei, 'ether'), 6)
    except Exception as e:
        log.error(f"Balance check failed: {e}")
        return 0.0

def check_wallet_funded():
    balance = get_wallet_balance()
    log.info(f"Wallet {WALLET[:12]}... balance: {balance} ETH")
    return balance

# --- INTELLIGENCE ---

def analyze(state, prices, fear_greed, tvl, yields, gas):
    alerts = []
    opportunities = []

    eth = prices.get("eth", 0) or 0
    eth_24h = prices.get("eth_24h", 0) or 0
    fg = fear_greed.get("value", 50)

    if abs(eth_24h) > 3:
        alerts.append(f"ETH 24h: {eth_24h:+.1f}% - {'liquidation risk HIGH' if eth_24h < -3 else 'rally'}")
    if fg < 20:
        alerts.append(f"EXTREME FEAR ({fg}) - liquidation cascade risk, accumulation zone")
    if eth < 1800:
        alerts.append(f"ETH CRITICAL ${eth} - mass liquidations imminent on lending protocols")

    for p in tvl:
        change = p.get("change_1d") or 0
        if change < -10:
            alerts.append(f"TVL CRASH: {p['name']} {change:.0f}% 24h")

    balance = state.get("wallet_balance_eth", 0)
    if yields and balance > 0.01:
        best = yields[0]
        opportunities.append({
            "type": "yield",
            "project": best.get("project"),
            "symbol": best.get("symbol"),
            "apy": best.get("apy"),
            "tvl_usd": best.get("tvlUsd"),
            "note": f"{best.get('apy',0):.1f}% APY on {best.get('project')} - worth monitoring"
        })

    return alerts, opportunities

# --- MAIN LOOP ---

def run_cycle(state):
    state["cycles"] += 1
    c = state["cycles"]
    ts = datetime.now(timezone.utc).isoformat()
    log.info(f"=== Cycle {c} | {ts[:19]} ===")

    if c % 10 == 1:
        balance = check_wallet_funded()
        state["wallet_balance_eth"] = float(balance)
        if balance > 0:
            log.info(f"WALLET FUNDED: {balance} ETH available for execution")
        else:
            log.info("Wallet empty - monitoring only until funded")

    prices = get_prices()
    fear_greed = get_fear_greed()
    gas = get_eth_gas()
    tvl = get_defi_tvl()

    yields, news, liquidations = [], [], []
    if c % 3 == 0:
        yields = get_yield_opportunities()
        news = get_news()
    if c % 5 == 0:
        liquidations = get_aave_liquidations()

    if prices:
        log.info(f"BTC:${prices.get('btc',0):,}({prices.get('btc_24h',0):+.1f}%) ETH:${prices.get('eth',0):,}({prices.get('eth_24h',0):+.1f}%) AAVE:${prices.get('aave',0)}")
    if fear_greed:
        log.info(f"Fear&Greed:{fear_greed['value']}({fear_greed['label']}) Gas:{gas.get('safe',0):.2f}gwei")
    if tvl:
        tvl_summary = [(p['name'], round(float(p['tvl'] or 0)/1e9,1)) for p in tvl[:3]]
        log.info(f"TVL:{tvl_summary}")
    if liquidations:
        log.info(f"Aave liquidations:{len(liquidations)}")
    if news:
        log.info(f"News:{news[0]['title'][:70]}")

    alerts, opportunities = analyze(state, prices, fear_greed, tvl, yields, gas)
    for a in alerts: log.warning(f"ALERT:{a}")
    for o in opportunities: log.info(f"OPPORTUNITY:{o}")

    # Update price history BEFORE pattern detection so latest price is included
    if prices:
        state["price_history"].append({"cycle":c,"ts":ts,**prices})
        state["price_history"] = state["price_history"][-200:]

    # --- v7 PATTERN DETECTION ---
    pattern_triggered, drop_pct = detect_eth_drop_pattern(state)
    if pattern_triggered:
        pattern_entry = {
            "cycle": c, "ts": ts,
            "drop_pct": round(drop_pct, 4),
            "window": PATTERN_WINDOW,
            "eth_now": prices.get("eth")
        }
        state.setdefault("pattern_alerts", []).append(pattern_entry)
        state["pattern_alerts"] = state["pattern_alerts"][-50:]

    state["alerts"].extend([{"text":a,"cycle":c,"ts":ts} for a in alerts])
    state["alerts"] = state["alerts"][-100:]

    report = {
        "cycle":c, "ts":ts, "prices":prices, "fear_greed":fear_greed,
        "gas":gas, "tvl_top3":tvl[:3], "alerts":alerts,
        "opportunities":opportunities, "liquidations_found":len(liquidations),
        "wallet_balance_eth":state.get("wallet_balance_eth",0),
        "revenue_eth":state.get("revenue_eth",0),
        "pattern_triggered": pattern_triggered,
        "pattern_drop_pct": round(drop_pct, 4),
        "stats":{
            "cycles":c,
            "total_alerts":len(state["alerts"]),
            "executions":len(state.get("executions",[])),
            "pattern_alerts":len(state.get("pattern_alerts",[]))
        }
    }
    (LOG_DIR / "latest.json").write_text(json.dumps(report, indent=2, default=str))
    return report

def main():
    log.info("Claw Bot v7 | PATTERN DETECTION | ETH drop >3% over 10 cycles -> PATTERN_ALERT")
    log.info(f"Wallet: {WALLET}")
    log.info(f"Web3 connected: {w3.is_connected()}")
    log.info(f"Interval: {INTERVAL}s | PatternWindow:{PATTERN_WINDOW} cycles | Threshold:{PATTERN_DROP_PCT}%")

    state = load_state()
    log.info(f"Resuming from cycle {state['cycles']} | Revenue: {state.get('revenue_eth',0)} ETH | PatternAlerts: {len(state.get('pattern_alerts',[]))}")

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
