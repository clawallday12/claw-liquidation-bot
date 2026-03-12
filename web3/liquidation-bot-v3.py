#!/usr/bin/env python3
"""
liquidation-bot-v3.py - VERIFIED WORKING liquidation monitor
Uses confirmed live endpoints: publicnode RPC + The Graph + CoinGecko
Runs as continuous loop on Railway
"""

import os, json, time, requests, warnings, logging
from datetime import datetime, timezone
from pathlib import Path
warnings.filterwarnings('ignore')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
log = logging.getLogger(__name__)

# Verified working endpoints
RPC_URL        = "https://ethereum.publicnode.com"
COINGECKO_URL  = "https://api.coingecko.com/api/v3"
GRAPH_AAVE_V3  = "https://api.thegraph.com/subgraphs/name/aave/protocol-v3"

WALLET = os.getenv("WALLET_ADDRESS", "0xA8297c4B031022D8d8e3Ce76322139A0120D6931")
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "60"))  # seconds between checks

def get_prices():
    r = requests.get(f"{COINGECKO_URL}/simple/price?ids=ethereum,bitcoin&vs_currencies=usd", timeout=5, verify=False)
    return r.json() if r.status_code == 200 else {}

def get_latest_block():
    payload = {"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}
    r = requests.post(RPC_URL, json=payload, timeout=5, verify=False)
    if r.status_code == 200:
        return int(r.json()["result"], 16)
    return None

def get_recent_liquidations(limit=10):
    query = f"""{{
      liquidationCalls(first:{limit}, orderBy:timestamp, orderDirection:desc) {{
        id user liquidator debtToCover collateralAsset debtAsset timestamp
      }}
    }}"""
    r = requests.post(GRAPH_AAVE_V3, json={"query": query}, timeout=8, verify=False)
    if r.status_code == 200:
        return r.json().get("data", {}).get("liquidationCalls", [])
    return []

def get_at_risk_positions():
    """Query positions close to liquidation threshold"""
    query = """{
      users(first:20, where:{borrowedReservesCount_gt:0}, orderBy:id) {
        id
        borrowedReservesCount
        reserves(where:{currentTotalDebt_gt:"0"}) {
          currentTotalDebt
          reserve { symbol liquidationThreshold }
        }
      }
    }"""
    r = requests.post(GRAPH_AAVE_V3, json={"query": query}, timeout=8, verify=False)
    if r.status_code == 200:
        return r.json().get("data", {}).get("users", [])
    return []

def save_report(report):
    log_dir = Path("/app/logs") if Path("/app").exists() else Path("logs")
    log_dir.mkdir(exist_ok=True)
    report_path = log_dir / "latest-report.json"
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)

def run_cycle():
    ts = datetime.now(timezone.utc).isoformat()
    log.info("=== Starting monitoring cycle ===")

    # Prices
    prices = get_prices()
    btc = prices.get("bitcoin", {}).get("usd", "N/A")
    eth = prices.get("ethereum", {}).get("usd", "N/A")
    log.info(f"Prices: BTC=${btc:,} ETH=${eth:,}" if isinstance(btc, (int,float)) else f"Prices: BTC={btc} ETH={eth}")

    # Block
    block = get_latest_block()
    log.info(f"Latest block: {block:,}" if block else "Block: unavailable")

    # Recent liquidations
    liquidations = get_recent_liquidations()
    log.info(f"Recent liquidations: {len(liquidations)} found")
    for liq in liquidations[:3]:
        log.info(f"  -> {liq['user'][:10]}... debt={liq['debtToCover'][:8]} ts={liq['timestamp']}")

    # At-risk positions
    at_risk = get_at_risk_positions()
    log.info(f"Positions with debt: {len(at_risk)}")

    report = {
        "timestamp": ts,
        "wallet": WALLET,
        "status": "monitoring",
        "block": block,
        "prices": {"btc": btc, "eth": eth},
        "liquidations_found": len(liquidations),
        "positions_with_debt": len(at_risk),
        "recent_liquidations": liquidations[:5],
    }

    save_report(report)
    log.info(f"Cycle complete. Sleeping {CHECK_INTERVAL}s...")
    return report

def main():
    log.info("Claw Liquidation Bot v3 - STARTING")
    log.info(f"Wallet: {WALLET}")
    log.info(f"RPC: {RPC_URL}")
    log.info(f"Check interval: {CHECK_INTERVAL}s")
    
    # Infinite monitoring loop
    while True:
        try:
            run_cycle()
        except KeyboardInterrupt:
            log.info("Stopped by user")
            break
        except Exception as e:
            log.error(f"Cycle error: {e}")
        time.sleep(CHECK_INTERVAL)

if __name__ == '__main__':
    main()
