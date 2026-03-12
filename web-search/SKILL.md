---
name: web-search
description: Autonomous web search via free APIs (DuckDuckGo, SerpAPI, Brave). No key required for DuckDuckGo. High-accuracy research capability.
metadata:
  {
    "openclaw": {
      "emoji": "🔍",
      "requires": { "bins": ["python"], "packages": ["requests"] },
    },
  }
---

# Web Search Skill

Autonomous web search using free APIs. No API keys required for DuckDuckGo. Premium APIs available for higher accuracy.

## Quick Start

### DuckDuckGo (No Key, Unlimited)

```python
python web-search/scripts/search.py "best AI agent frameworks" --engine duckduckgo
```

### SerpAPI (100 free/month)

```python
python web-search/scripts/search.py "crypto agent trading" --engine serpapi --key YOUR_KEY
```

## Features

- **DuckDuckGo**: Free, unlimited, no key needed
- **SerpAPI**: Higher accuracy, 100 free searches/month
- **Brave Search**: Free tier available
- JSON output for downstream processing
- Result deduplication
- Source attribution

## Income Stream Integration

Used for:
- Market research (crypto opportunities, AI pricing trends)
- Competitive intelligence (who's building what)
- Data aggregation (sell research reports)
- Trend analysis (capitalize on emerging niches)
