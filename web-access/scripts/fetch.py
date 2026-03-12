#!/usr/bin/env python3
"""
fetch.py - HTTP + HTML parsing utility for autonomous web access
"""

import sys
import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import argparse

def fetch_url(url, timeout=10, headers=None, verify_ssl=False):
    """Fetch URL and return raw content"""
    default_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Claw/1.0"
    }
    if headers:
        default_headers.update(headers)
    
    try:
        resp = requests.get(url, timeout=timeout, headers=default_headers, verify=verify_ssl)
        resp.raise_for_status()
        return resp.content, resp.text, resp.status_code
    except requests.exceptions.RequestException as e:
        print(json.dumps({"error": str(e), "url": url}), file=sys.stderr)
        return None, None, None

def parse_html(html, selector=None):
    """Parse HTML and optionally extract by CSS selector"""
    soup = BeautifulSoup(html, 'html.parser')
    
    if selector:
        elements = soup.select(selector)
        return [{'tag': el.name, 'text': el.get_text(strip=True), 'html': str(el)[:200]} for el in elements]
    
    return {
        'title': soup.title.string if soup.title else None,
        'headings': [h.get_text(strip=True) for h in soup.find_all(['h1', 'h2', 'h3'])],
        'links': [{'href': a.get('href'), 'text': a.get_text(strip=True)} for a in soup.find_all('a')][:10],
        'text_length': len(soup.get_text()),
    }

def main():
    parser = argparse.ArgumentParser(description="Fetch and parse URLs")
    parser.add_argument('url', help="URL to fetch")
    parser.add_argument('--selector', help="CSS selector to extract")
    parser.add_argument('--json-output', action='store_true', help="Output as JSON")
    args = parser.parse_args()
    
    content, text, status = fetch_url(args.url)
    
    if content is None:
        sys.exit(1)
    
    result = parse_html(text, args.selector)
    
    if args.json_output:
        print(json.dumps(result, indent=2))
    else:
        print(result)

if __name__ == '__main__':
    main()
