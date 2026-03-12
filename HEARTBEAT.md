# HEARTBEAT.md - Autonomous Tasks

## Active Tasks (run on every heartbeat)

1. Check Railway bot v5 deployment status — alert if FAILED
2. Check overnight alerts from bot (Extreme Fear, TVL drops, price crashes)
3. If between 8am-11pm ET: generate 30-min check-in for Firas (cron handles this)
4. If new skills available on ClawHub: install clean ones (VirusTotal check first)

## Overnight Priorities (while Firas sleeps)

1. Attempt API key signups: Etherscan, Tavily, NewsAPI
2. Build liquidation execution layer (prep tx signing code)
3. Update BOOTSTRAP.md with full session learnings
4. Monitor bot logs via Railway API
