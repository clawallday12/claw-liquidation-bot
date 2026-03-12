#!/usr/bin/env python3
import sys, json, os
os.chdir('C:/Users/firas/.openclaw/workspace')
src = open('web3/liquidation-bot-v5.py').read().replace('while True:', 'if False:').replace('break', 'pass')
exec(src, globals())
state = load_state()
report = run_cycle(state)
save_state(state)
print('\n=== VERIFIED OUTPUT ===')
print(f"Prices: BTC=${report['prices'].get('btc',0):,} ETH=${report['prices'].get('eth',0):,}")
print(f"Fear/Greed: {report['fear_greed']}")
print(f"BTC Dom: {report['btc_dominance']}%")
print(f"Alerts: {report['alerts']}")
print(f"Discoveries: {report['discoveries']}")
