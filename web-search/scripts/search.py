#!/usr/bin/env python3
"""
search.py - Unified web search via free APIs (DuckDuckGo, SerpAPI, Brave)
"""

import json
import sys
import argparse
import requests
from typing import List, Dict

def search_duckduckgo(query: str, max_results: int = 10) -> List[Dict]:
    """Search via DuckDuckGo (no API key needed)"""
    try:
        url = "https://api.duckduckgo.com/"
        params = {
            "q": query,
            "format": "json",
            "no_html": 1,
            "skip_disambig": 1,
        }
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        
        results = []
        
        # Abstract result
        if data.get("AbstractText"):
            results.append({
                "title": data.get("Heading", "Definition"),
                "snippet": data["AbstractText"],
                "url": data.get("AbstractURL", ""),
                "source": "DuckDuckGo",
            })
        
        # Related links
        for item in data.get("RelatedTopics", [])[:max_results]:
            if "FirstURL" in item:
                results.append({
                    "title": item.get("Text", "").split(" - ")[0],
                    "snippet": item.get("Text", ""),
                    "url": item["FirstURL"],
                    "source": "DuckDuckGo",
                })
        
        return results[:max_results]
    except Exception as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        return []

def search_serpapi(query: str, api_key: str, max_results: int = 10) -> List[Dict]:
    """Search via SerpAPI (100 free/month)"""
    try:
        url = "https://serpapi.com/search"
        params = {
            "q": query,
            "api_key": api_key,
            "num": max_results,
        }
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        
        results = []
        for item in data.get("organic_results", [])[:max_results]:
            results.append({
                "title": item.get("title", ""),
                "snippet": item.get("snippet", ""),
                "url": item.get("link", ""),
                "source": "SerpAPI",
            })
        
        return results
    except Exception as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        return []

def main():
    parser = argparse.ArgumentParser(description="Web search via free APIs")
    parser.add_argument("query", help="Search query")
    parser.add_argument("--engine", default="duckduckgo", choices=["duckduckgo", "serpapi"])
    parser.add_argument("--key", help="API key (for SerpAPI)")
    parser.add_argument("--limit", type=int, default=10, help="Max results")
    args = parser.parse_args()
    
    if args.engine == "duckduckgo":
        results = search_duckduckgo(args.query, args.limit)
    elif args.engine == "serpapi":
        if not args.key:
            print(json.dumps({"error": "SerpAPI requires --key"}), file=sys.stderr)
            sys.exit(1)
        results = search_serpapi(args.query, args.key, args.limit)
    else:
        print(json.dumps({"error": "Unknown engine"}), file=sys.stderr)
        sys.exit(1)
    
    print(json.dumps(results, indent=2))

if __name__ == '__main__':
    main()
