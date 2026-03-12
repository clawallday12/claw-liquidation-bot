#!/usr/bin/env python3
import requests, json, warnings
warnings.filterwarnings('ignore')

TOKEN = 'd59387ad-25d3-4707-bca5-f06acfcbe112'
HEADERS = {'Authorization': f'Bearer {TOKEN}', 'Content-Type': 'application/json'}
API = 'https://backboard.railway.app/graphql/v2'
DEPLOYMENT_ID = '3eb72a08-14b2-4db3-b27a-54a7e2f44588'

def gql(query, variables=None):
    r = requests.post(API, json={'query': query, 'variables': variables or {}}, headers=HEADERS, timeout=15, verify=False)
    return r.json()

print('[1] Fetching deployment logs...')
result = gql('''
query($id: String!) {
  deploymentLogs(deploymentId: $id) {
    message
    timestamp
  }
}''', {'id': DEPLOYMENT_ID})

logs = result.get('data', {}).get('deploymentLogs', [])
print(f'Got {len(logs)} log lines')
for l in logs[-80:]:
    print(l.get('timestamp','')[:19], l.get('message',''))

# Also check for errors/alerts
if logs:
    msgs = [l.get('message','').lower() for l in logs]
    alerts = [l for l in logs if any(kw in l.get('message','').lower() for kw in ['error', 'fear', 'tvl', 'crash', 'drop', 'alert', 'critical', 'warning', 'exception', 'traceback'])]
    if alerts:
        print('\n=== ALERTS DETECTED ===')
        for a in alerts:
            print(a.get('timestamp','')[:19], a.get('message',''))
    else:
        print('\nNo alerts detected in logs.')
