#!/usr/bin/env python3
import requests, json, warnings
warnings.filterwarnings('ignore')

TOKEN = 'd59387ad-25d3-4707-bca5-f06acfcbe112'
HEADERS = {'Authorization': f'Bearer {TOKEN}', 'Content-Type': 'application/json'}
API = 'https://backboard.railway.app/graphql/v2'
DEPLOYMENT_ID = '3eb72a08-14b2-4db3-b27a-54a7e2f44588'

def gql(query, variables=None):
    r = requests.post(API, json={'query': query, 'variables': variables or {}}, headers=HEADERS, timeout=15, verify=False)
    try: return r.json()
    except: return {}

# Get deployment logs
result = gql('''
query($deploymentId: String!) {
  deploymentLogs(deploymentId: $deploymentId) {
    message
    severity
    timestamp
  }
}''', {'deploymentId': DEPLOYMENT_ID})

logs = result.get('data', {}).get('deploymentLogs', [])
print(f"Total log entries: {len(logs)}")
print()
for entry in logs[-50:]:
    ts = entry.get('timestamp','')[:19]
    msg = entry.get('message','')
    sev = entry.get('severity','')
    print(f"[{ts}] {msg}")
