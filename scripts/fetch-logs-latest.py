#!/usr/bin/env python3
import requests, json, warnings
warnings.filterwarnings('ignore')

TOKEN = 'd59387ad-25d3-4707-bca5-f06acfcbe112'
HEADERS = {'Authorization': f'Bearer {TOKEN}', 'Content-Type': 'application/json'}
API = 'https://backboard.railway.app/graphql/v2'

def gql(query, variables=None):
    r = requests.post(API, json={'query': query, 'variables': variables or {}}, headers=HEADERS, timeout=15, verify=False)
    return r.json()

# Get latest deployment ID first
dep_result = gql('''
query {
  deployments(input: { projectId: null }) {
    edges { node { id status createdAt } }
  }
}''')

edges = dep_result.get('data', {}).get('deployments', {}).get('edges', [])
latest_success = next((e['node'] for e in edges if e['node']['status'] == 'SUCCESS'), None)
if not latest_success:
    print('No SUCCESS deployment found')
    exit(1)

DEPLOYMENT_ID = latest_success['id']
print(f'[Using deployment {DEPLOYMENT_ID} created {latest_success["createdAt"][:19]}]')

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

# Alert summary
if logs:
    alerts = [l for l in logs if any(kw in l.get('message','').lower() for kw in ['error', 'fear', 'tvl', 'crash', 'drop', 'alert', 'critical', 'warning', 'exception', 'traceback', 'discovery'])]
    unique_alerts = list({l.get('message',''): l for l in alerts}.values())
    if unique_alerts:
        print('\n=== UNIQUE ALERT TYPES ===')
        for a in unique_alerts[:10]:
            print(a.get('timestamp','')[:19], a.get('message',''))
