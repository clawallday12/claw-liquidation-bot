---
name: web-access
description: Autonomous web browsing, scraping, and API access via Python. Fetch URLs, parse HTML, extract data, and automate browser interactions.
metadata:
  {
    "openclaw": {
      "emoji": "🌐",
      "requires": { "bins": ["python"], "packages": ["requests", "beautifulsoup4", "playwright"] },
    },
  }
---

# Web Access Skill

Autonomous internet connectivity via Python for web scraping, API requests, and browser automation.

## Capabilities

- **HTTP Requests**: GET/POST/PUT/DELETE via requests/httpx
- **HTML Parsing**: beautifulsoup4 for DOM extraction
- **Browser Automation**: Playwright for headless Chromium
- **JSON APIs**: Parse and traverse API responses
- **Data Extraction**: CSS selectors, XPath, regex

## Quick Start

### Fetch & Parse URL

```python
import requests
from bs4 import BeautifulSoup

url = "https://example.com"
resp = requests.get(url, timeout=10)
soup = BeautifulSoup(resp.content, 'html.parser')
titles = soup.select('h1')
for t in titles:
    print(t.get_text())
```

### API Request

```python
import requests

api_url = "https://api.example.com/data"
headers = {"Authorization": "Bearer YOUR_TOKEN"}
data = requests.get(api_url, headers=headers).json()
print(data)
```

### Browser Automation

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto("https://example.com")
    content = page.content()
    browser.close()
    print(content)
```

## Usage Patterns

1. **Fetch news/articles** → scrape content
2. **Monitor websites** → detect changes
3. **API integration** → pull/push data
4. **Form automation** → fill & submit
5. **Data extraction** → tables, lists, structured content

## Files

- `scripts/fetch.py` - HTTP + HTML parsing utility
- `scripts/browser.py` - Playwright wrapper
- `scripts/api-call.py` - JSON API helper

## Safety Notes

- **Respect robots.txt** - Don't hammer sites
- **User-Agent** - Identify yourself in requests
- **Rate limiting** - Add delays between requests
- **Authentication** - Store API keys securely
