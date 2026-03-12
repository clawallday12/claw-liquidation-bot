#!/usr/bin/env python3
import sys, json, os
os.chdir('C:/Users/firas/.openclaw/workspace')

# Load and patch the bot for single-cycle test
src = open('web3/liquidation-bot-v4.py').read()
src = src.replace("while True:", "if False:").replace("if __name__ == '__main__':", "if False:").replace("break", "pass")
exec(src, globals())

state = load_state()
report = run_cycle(state)
save_state(state)

print('\n=== CYCLE REPORT ===')
print(json.dumps(report['state_summary'], indent=2))
print(f"Discoveries: {report['discoveries']}")
print(f"Liquidations found: {report['liquidations_this_cycle']}")
