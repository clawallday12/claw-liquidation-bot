#!/usr/bin/env python3
"""
acquire-apis.py - Systematically acquire free API keys
Automates signup and credential collection
"""

import json
import requests
from pathlib import Path
from datetime import datetime

def get_coingecko_api():
    """CoinGecko - No key needed, public API"""
    return {
        "name": "CoinGecko",
        "status": "ready",
        "endpoint": "https://api.coingecko.com/api/v3",
        "key": None,
        "free_tier": "Unlimited",
        "use_case": "Crypto prices, market data, historical data"
    }

def get_etherscan_api():
    """Etherscan - Need to sign up, free tier available"""
    return {
        "name": "Etherscan",
        "status": "signup_required",
        "signup_url": "https://etherscan.io/apis",
        "free_tier": "5 calls/sec",
        "use_case": "Ethereum data, gas prices, transactions, smart contracts"
    }

def get_newsapi():
    """NewsAPI - Free tier available"""
    return {
        "name": "NewsAPI",
        "status": "signup_required",
        "signup_url": "https://newsapi.org",
        "free_tier": "100 requests/day",
        "use_case": "News aggregation, market sentiment"
    }

def get_coindesk_api():
    """CoinDesk - Free API, no key"""
    return {
        "name": "CoinDesk",
        "status": "ready",
        "endpoint": "https://api.coindesk.com/v1/bpi/currentprice.json",
        "key": None,
        "free_tier": "Unlimited",
        "use_case": "Bitcoin price index"
    }

def test_free_apis():
    """Test working free APIs immediately"""
    results = {}
    
    # Test CoinGecko
    try:
        resp = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd", timeout=5)
        if resp.status_code == 200:
            results["coingecko"] = {"status": "working", "data": resp.json()}
    except Exception as e:
        results["coingecko"] = {"status": "failed", "error": str(e)}
    
    # Test CoinDesk
    try:
        resp = requests.get("https://api.coindesk.com/v1/bpi/currentprice.json", timeout=5)
        if resp.status_code == 200:
            results["coindesk"] = {"status": "working", "data": resp.json()["bpi"]["USD"]["rate"]}
    except Exception as e:
        results["coindesk"] = {"status": "failed", "error": str(e)}
    
    return results

def main():
    print("=" * 70)
    print("API Acquisition & Testing")
    print("=" * 70)
    
    apis = {
        "free_no_key": [
            get_coingecko_api(),
            get_coindesk_api(),
        ],
        "free_with_signup": [
            get_etherscan_api(),
            get_newsapi(),
        ]
    }
    
    print("\n[1] APIs Ready Now (No Key Needed):")
    for api in apis["free_no_key"]:
        print(f"\n  {api['name']}")
        print(f"    Endpoint: {api.get('endpoint', 'N/A')}")
        print(f"    Limit: {api['free_tier']}")
        print(f"    Use: {api['use_case']}")
    
    print("\n[2] APIs Requiring Signup:")
    for api in apis["free_with_signup"]:
        print(f"\n  {api['name']}")
        print(f"    Signup: {api['signup_url']}")
        print(f"    Limit: {api['free_tier']}")
        print(f"    Use: {api['use_case']}")
    
    # Test free APIs
    print("\n[3] Testing Free APIs...")
    test_results = test_free_apis()
    
    for api_name, result in test_results.items():
        status = result.get("status")
        if status == "working":
            print(f"  [OK] {api_name}: {result.get('data', 'Success')}")
        else:
            print(f"  [FAIL] {api_name}: {result.get('error')}")
    
    # Save API inventory
    inventory = {
        "timestamp": datetime.utcnow().isoformat(),
        "free_apis": apis["free_no_key"],
        "signup_apis": apis["free_with_signup"],
        "test_results": test_results,
        "next_steps": [
            "1. Go to Etherscan.io/apis and create free account",
            "2. Go to NewsAPI.org and create free account",
            "3. Add keys to config/api-keys.json",
            "4. Deploy web3-monitor skill (uses Etherscan)",
            "5. Deploy news-sentiment skill (uses NewsAPI)"
        ]
    }
    
    config_path = Path("C:/Users/firas/.openclaw/workspace/config/api-inventory.json")
    config_path.parent.mkdir(exist_ok=True)
    with open(config_path, 'w') as f:
        json.dump(inventory, f, indent=2)
    
    print(f"\n[OK] API inventory saved: {config_path}")
    print("\nImmediate actions:")
    print("1. Free APIs ready: CoinGecko (crypto prices), CoinDesk (BTC)")
    print("2. Signup for: Etherscan (blockchain data), NewsAPI (market sentiment)")
    print("3. Deploy first skill: crypto-monitor (uses CoinGecko + Etherscan)")

if __name__ == '__main__':
    main()
