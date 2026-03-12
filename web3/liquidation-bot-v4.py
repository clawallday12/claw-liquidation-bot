#!/usr/bin/env python3
"""
liquidation-bot-v4.py - SELF-IMPROVING autonomous agent
Not just a monitor. It logs, learns, refines, discovers, and escalates.
Every cycle it gets smarter about where opportunities are.
"""

import os, json, time, requests, warnings, logging, traceback
from datetime import datetime, timezone
from pathlib import Path
from collections import defaultdict
warnings.filterwarnings('ignore')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
log = logging.getLogger(__name__)

LOG_DIR = Path("/app/logs") if Path("/app").exists() else Path("logs")
LOG_DIR.mkdir(exist_ok=True)

WALLET        = os.getenv("WALLET_ADDRESS", "0xA8297c4B031022D8d8e3Ce76322139A0120D6931")
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "60"))

# Multiple data sources - bot learns which are most reliable
SOURCES = {
    "coingecko":    "https://api.coingecko.com/api/v3",
    "rpc_public":   "https://ethereum.publicnode.com",
    "rpc_llama":    "https://eth.llamarpc.com",
    "graph_aave_v3": "https://api.thegraph.com/subgraphs/name/aave/protocol-v3",
    "graph_aave_v3_alt": "https://api.thegraph.com/subgraphs/name/messari/aave-v3-ethereum",
    "defillama":    "https://api.llama.fi",
}

# Self-improving state - persisted across cycles
STATE_FILE = LOG_DIR / "bot-state.json"

def load_state():
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except:
            pass
    return {
        "cycles": 0,
        "source_reliability": {k: {"success": 0, "fail": 0} for k in SOURCES},
        "opportunities_detected": 0,
        "prices_tracked": {},
        "protocols_monitored": [],
        "improvements_log": [],
        "total_liquidations_seen": 0,
        "best_rpc": "rpc_public",
    }

def save_state(state):
    STATE_FILE.write_text(json.dumps(state, indent=2))

def track_source(state, source, success):
    """Learn which sources are reliable"""
    if source not in state["source_reliability"]:
        state["source_reliability"][source] = {"success": 0, "fail": 0}
    key = "success" if success else "fail"
    state["source_reliability"][source][key] += 1

def get_best_rpc(state):
    """Pick most reliable RPC based on history"""
    rpcs = ["rpc_public", "rpc_llama"]
    best, best_score = rpcs[0], -1
    for rpc in rpcs:
        stats = state["source_reliability"].get(rpc, {"success": 0, "fail": 1})
        total = stats["success"] + stats["fail"]
        score = stats["success"] / total if total > 0 else 0
        if score > best_score:
            best, best_score = rpc, score
    return best

def fetch(url, method="get", payload=None, timeout=6):
    try:
        if method == "post":
            r = requests.post(url, json=payload, timeout=timeout, verify=False)
        else:
            r = requests.get(url, timeout=timeout, verify=False)
        r.raise_for_status()
        return r.json(), None
    except Exception as e:
        return None, str(e)

def get_prices(state):
    data, err = fetch(f"{SOURCES['coingecko']}/simple/price?ids=ethereum,bitcoin,aave&vs_currencies=usd")
    track_source(state, "coingecko", data is not None)
    if data:
        prices = {
            "btc": data.get("bitcoin", {}).get("usd"),
            "eth": data.get("ethereum", {}).get("usd"),
            "aave": data.get("aave", {}).get("usd"),
        }
        # Detect significant price moves (self-improvement: flag volatility)
        prev = state.get("prices_tracked", {})
        for asset, price in prices.items():
            if price and asset in prev and prev[asset]:
                change_pct = abs(price - prev[asset]) / prev[asset] * 100
                if change_pct > 2:
                    log.warning(f"PRICE ALERT: {asset.upper()} moved {change_pct:.1f}% -> potential liquidation opportunity")
                    state["opportunities_detected"] += 1
        state["prices_tracked"] = prices
        return prices
    return {}

def get_block(state):
    rpc = SOURCES[get_best_rpc(state)]
    data, err = fetch(rpc, "post", {"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1})
    track_source(state, get_best_rpc(state), data is not None)
    if data:
        return int(data["result"], 16)
    return None

def get_aave_liquidations(state):
    """Try multiple subgraph endpoints - learn which works"""
    for source_key in ["graph_aave_v3", "graph_aave_v3_alt"]:
        query = '{liquidationCalls(first:10,orderBy:timestamp,orderDirection:desc){id user liquidator debtToCover collateralAsset debtAsset timestamp}}'
        data, err = fetch(SOURCES[source_key], "post", {"query": query})
        track_source(state, source_key, data is not None and "data" in (data or {}))
        if data and "data" in data:
            liqs = data["data"].get("liquidationCalls", [])
            if liqs:
                state["total_liquidations_seen"] += len(liqs)
                return liqs, source_key
    return [], None

def get_defi_tvl(state):
    """Monitor DeFi TVL for risk signals"""
    data, err = fetch(f"{SOURCES['defillama']}/protocols")
    track_source(state, "defillama", data is not None)
    if data and isinstance(data, list):
        top = sorted(data, key=lambda x: x.get("tvl", 0), reverse=True)[:5]
        return [{"name": p["name"], "tvl": p.get("tvl", 0), "change_1d": p.get("change_1d", 0)} for p in top]
    return []

def discover_new_opportunities(state, prices, tvl_data):
    """Self-improvement: actively discover new opportunities each cycle"""
    discoveries = []

    # Check for DeFi TVL drops (signal potential liquidation cascade)
    for protocol in tvl_data:
        if protocol.get("change_1d") and protocol["change_1d"] < -5:
            discoveries.append(f"TVL DROP: {protocol['name']} down {protocol['change_1d']:.1f}% in 24h - monitor for liquidations")

    # ETH price threshold checks
    eth = prices.get("eth")
    if eth:
        if eth < 1500:
            discoveries.append(f"ETH CRITICAL LOW (${eth}) - high liquidation risk on collateralized positions")
        elif eth < 2000:
            discoveries.append(f"ETH LOW ZONE (${eth}) - monitor Aave health factors closely")

    # Log new discoveries
    for d in discoveries:
        log.warning(f"DISCOVERY: {d}")
        if d not in state["improvements_log"]:
            state["improvements_log"].append({"discovery": d, "cycle": state["cycles"], "ts": datetime.now(timezone.utc).isoformat()})

    return discoveries

def log_improvement(state, improvement):
    """Track what the bot is learning"""
    entry = {
        "cycle": state["cycles"],
        "improvement": improvement,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    state["improvements_log"].append(entry)
    if len(state["improvements_log"]) > 100:  # Keep last 100
        state["improvements_log"] = state["improvements_log"][-100:]
    log.info(f"IMPROVEMENT LOGGED: {improvement}")

def run_cycle(state):
    state["cycles"] += 1
    cycle = state["cycles"]
    log.info(f"=== Cycle {cycle} ===")

    # Prices
    prices = get_prices(state)
    if prices:
        log.info(f"Prices | BTC:${prices.get('btc',0):,} ETH:${prices.get('eth',0):,} AAVE:${prices.get('aave',0)}")

    # Block
    block = get_block(state)
    if block:
        log.info(f"Block: {block:,} | RPC: {get_best_rpc(state)}")

    # Liquidations
    liqs, source_used = get_aave_liquidations(state)
    log.info(f"Aave liquidations: {len(liqs)} | Source: {source_used or 'none'}")
    for l in liqs[:3]:
        log.info(f"  LIQ: user={l['user'][:10]} debt={l['debtToCover'][:12]} asset={l.get('debtAsset','?')[:10]}")

    # DeFi TVL (every 5 cycles to save API calls)
    tvl_data = []
    if cycle % 5 == 0:
        tvl_data = get_defi_tvl(state)
        tvl_summary = [(p['name'], round(p['tvl']/1e9, 1)) for p in tvl_data[:3]]
        log.info(f"DeFi TVL top protocols: {tvl_summary}")

    # Discover opportunities
    discoveries = discover_new_opportunities(state, prices, tvl_data)
    if discoveries:
        log.warning(f"Discoveries this cycle: {len(discoveries)}")

    # Self-improvement: log reliability stats every 10 cycles
    if cycle % 10 == 0:
        reliability = {k: v for k, v in state["source_reliability"].items() if v["success"] + v["fail"] > 0}
        log.info(f"Source reliability: {json.dumps(reliability)}")
        log_improvement(state, f"Cycle {cycle}: best_rpc={get_best_rpc(state)}, total_liqs_seen={state['total_liquidations_seen']}, opportunities={state['opportunities_detected']}")

    # Save full report
    report = {
        "cycle": cycle,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "prices": prices,
        "block": block,
        "liquidations_this_cycle": len(liqs),
        "discoveries": discoveries,
        "state_summary": {
            "total_cycles": state["cycles"],
            "opportunities_detected": state["opportunities_detected"],
            "total_liquidations_seen": state["total_liquidations_seen"],
            "best_rpc": get_best_rpc(state),
        }
    }

    (LOG_DIR / "latest-report.json").write_text(json.dumps(report, indent=2))
    (LOG_DIR / f"cycle-{cycle:05d}.json").write_text(json.dumps(report, indent=2))

    return report

def main():
    log.info("Claw Liquidation Bot v4 - SELF-IMPROVING MODE")
    log.info(f"Wallet: {WALLET} | Interval: {CHECK_INTERVAL}s")
    log.info("Directive: Monitor -> Discover -> Learn -> Improve -> Execute")

    state = load_state()
    log.info(f"Resuming from cycle {state['cycles']} | {state['opportunities_detected']} opportunities detected so far")

    while True:
        try:
            run_cycle(state)
            save_state(state)
        except KeyboardInterrupt:
            log.info("Stopped. Saving state...")
            save_state(state)
            break
        except Exception as e:
            log.error(f"Cycle error: {e}")
            log.error(traceback.format_exc())
        time.sleep(CHECK_INTERVAL)

if __name__ == '__main__':
    main()
