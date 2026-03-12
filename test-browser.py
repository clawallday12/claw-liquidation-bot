#!/usr/bin/env python3
import sys
sys.path.insert(0, '/web-access/scripts')

# Import directly
exec(open('web-access/scripts/browser-advanced.py').read())

result = extract_data_with_selectors(
    'http://example.com',
    {'headings': 'h1, h2', 'paragraphs': 'p', 'links': 'a'}
)
import json
print(json.dumps(result, indent=2))
