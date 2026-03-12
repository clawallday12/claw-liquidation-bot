#!/usr/bin/env python3
"""
api-call.py - JSON API request utility
"""

import sys
import json
import argparse
import requests
from urllib.parse import urljoin

def api_request(method, url, headers=None, data=None, timeout=10):
    """Make HTTP request to API"""
    default_headers = {
        "User-Agent": "Claw/1.0",
        "Accept": "application/json",
    }
    if headers:
        default_headers.update(headers)
    
    try:
        if method.upper() == 'GET':
            resp = requests.get(url, headers=default_headers, timeout=timeout)
        elif method.upper() == 'POST':
            resp = requests.post(url, json=data, headers=default_headers, timeout=timeout)
        elif method.upper() == 'PUT':
            resp = requests.put(url, json=data, headers=default_headers, timeout=timeout)
        elif method.upper() == 'DELETE':
            resp = requests.delete(url, headers=default_headers, timeout=timeout)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        resp.raise_for_status()
        return resp.json(), resp.status_code
    
    except requests.exceptions.RequestException as e:
        print(json.dumps({"error": str(e), "url": url, "method": method}), file=sys.stderr)
        return None, None

def main():
    parser = argparse.ArgumentParser(description="API request utility")
    parser.add_argument('url', help="API endpoint URL")
    parser.add_argument('--method', default='GET', help="HTTP method (GET, POST, PUT, DELETE)")
    parser.add_argument('--header', action='append', nargs=2, metavar=('KEY', 'VALUE'), help="Add header")
    parser.add_argument('--data', help="JSON data for POST/PUT (as JSON string)")
    parser.add_argument('--timeout', type=int, default=10, help="Request timeout in seconds")
    args = parser.parse_args()
    
    headers = {}
    if args.header:
        for k, v in args.header:
            headers[k] = v
    
    data = None
    if args.data:
        try:
            data = json.loads(args.data)
        except json.JSONDecodeError:
            print(f"Invalid JSON: {args.data}", file=sys.stderr)
            sys.exit(1)
    
    result, status = api_request(args.method, args.url, headers, data, args.timeout)
    
    if result:
        print(json.dumps(result, indent=2))
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == '__main__':
    main()
