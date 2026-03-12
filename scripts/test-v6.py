#!/usr/bin/env python3
import sys, json, os
os.chdir('C:/Users/firas/.openclaw/workspace')
src = open('web3/liquidation-bot-v6.py').read().replace('while True:', 'if False:').replace('break', 'pass')
exec(src, globals())
state = load_state()
report = run_cycle(state)
save_state(state)
print('\n=== V6 TEST ===')
print(f"Web3 connected: {w3.is_connected()}")
print(f"Wallet balance: {state['wallet_balance_eth']} ETH")
print(f"Prices: BTC=${report['prices'].get('btc',0):,} ETH=${report['prices'].get('eth',0):,}")
print(f"Alerts: {report['alerts']}")
print(f"Opportunities: {report['opportunities']}")
