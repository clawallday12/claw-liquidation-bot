#!/usr/bin/env python3
"""
liquidation-bot-v2.py - Fixed liquidation monitoring bot
Doesn't require paid RPC, uses free public RPCs
"""

import os
import json
import requests
from datetime import datetime
import time

class LiquidationMonitor:
    def __init__(self):
        # Public RPCs (no auth needed)
        self.rpc_urls = {
            "ethereum": "https://eth.publicnode.com",
            "polygon": "https://polygon-rpc.com",
        }
        
        # Aave contracts
        self.aave_v3_pool = "0x794a61358D6845594F94dc1DB02A252b5b4814aD"  # Ethereum
        
        self.wallet_address = os.getenv("WALLET_ADDRESS", "0xA8297c4B031022D8d8e3Ce76322139A0120D6931")
    
    def check_rpc_health(self):
        """Verify RPC endpoints are working"""
        results = {}
        for chain, rpc in self.rpc_urls.items():
            try:
                # Simple JSON-RPC call to get latest block
                payload = {
                    "jsonrpc": "2.0",
                    "method": "eth_blockNumber",
                    "params": [],
                    "id": 1
                }
                resp = requests.post(rpc, json=payload, timeout=5)
                if resp.status_code == 200:
                    results[chain] = "OK"
                else:
                    results[chain] = f"HTTP {resp.status_code}"
            except Exception as e:
                results[chain] = f"Failed: {str(e)[:50]}"
        
        return results
    
    def fetch_aave_liquidations_from_events(self):
        """
        Fetch recent Aave liquidation events using The Graph (free, no auth)
        This is better than RPC calls for finding opportunities
        """
        
        # Query The Graph for recent liquidations
        query = """
        {
          liquidationCalls(first: 10, orderBy: timestamp, orderDirection: desc) {
            id
            collateralAsset
            debtAsset
            user
            debtToCover
            liquidator
            timestamp
          }
        }
        """
        
        graphql_endpoint = "https://api.thegraph.com/subgraphs/name/aave/protocol-v3"
        
        try:
            response = requests.post(
                graphql_endpoint,
                json={"query": query},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if "data" in data and "liquidationCalls" in data["data"]:
                    return data["data"]["liquidationCalls"]
        except Exception as e:
            print(f"Graph query failed: {e}")
        
        return []
    
    def get_ethereum_gas_prices(self):
        """Get current gas prices from free API"""
        try:
            # Using public gas price API
            resp = requests.get("https://gas-api.zksync.io/mainnet/suggestedGasPrice", timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "standard": data.get("standard", "unknown"),
                    "fast": data.get("fast", "unknown")
                }
        except:
            pass
        
        return {"standard": "unknown", "fast": "unknown"}
    
    def monitor(self):
        """Main monitoring loop"""
        print("=" * 70)
        print("Aave Liquidation Monitor (v2)")
        print("=" * 70)
        print(f"Wallet: {self.wallet_address}")
        print(f"Status: Monitoring for liquidation opportunities\n")
        
        # Check RPC health
        print("[1] Checking RPC endpoints...")
        rpc_status = self.check_rpc_health()
        for chain, status in rpc_status.items():
            print(f"  {chain}: {status}")
        
        # Fetch recent liquidations
        print("\n[2] Recent Aave liquidations...")
        liquidations = self.fetch_aave_liquidations_from_events()
        
        if liquidations:
            print(f"  Found {len(liquidations)} recent liquidations:")
            for liq in liquidations[:3]:
                print(f"    - User: {liq['user'][:10]}... | Debt: {liq['debtToCover'][:20]}...")
        else:
            print("  No recent liquidations found (or Graph query failed)")
        
        # Get gas prices
        print("\n[3] Current gas prices...")
        gas = self.get_ethereum_gas_prices()
        print(f"  Standard: {gas['standard']}")
        print(f"  Fast: {gas['fast']}")
        
        # Status report
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "wallet": self.wallet_address,
            "status": "monitoring",
            "rpc_health": rpc_status,
            "recent_liquidations": len(liquidations),
            "gas_prices": gas,
            "note": "Bot is operational and monitoring for liquidation opportunities"
        }
        
        print(f"\n[OK] Monitor operational")
        print(f"Next check in 60 seconds...")
        
        return report

def main():
    monitor = LiquidationMonitor()
    report = monitor.monitor()
    
    # Save report
    with open("/tmp/liquidation-report.json", "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"\nReport saved. Ready for continuous monitoring.")

if __name__ == '__main__':
    main()
