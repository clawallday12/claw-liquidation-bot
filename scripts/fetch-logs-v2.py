#!/usr/bin/env python3
"""Fetch logs from latest SUCCESS deployment."""
import requests, json, warnings, sys
warnings.filterwarnings('ignore')

TOKEN = 'd59387ad-25d3-4707-bca5-f06acfcbe112'
HEADERS = {'Authorization': f'Bearer {TOKEN}', 'Content-Type': 'application/json'}
API = 'https://backboard.railway.app/graphql/v2'

SERVICE_ID = 'f9c8c5b9-ed9b-4078-b6f8-71ceee1de68c'  # from previous sessions

def gql(query, variables=None):
    r = requests.post(API, json={'query': query, 'variables': variables or {}},
                      headers=HEADERS, timeout=15, verify=False)
    data = r.json()
    if 'errors' in data:
        print('GQL errors:', data['errors'], file=sys.stderr)
    return data

# Step 1: get deployments for this service
result = gql('''
query($serviceId: String!) {
  deployments(input: { serviceId: $serviceId }) {
    edges { node { id status createdAt } }
  }
}''', {'serviceId': SERVICE_ID})

edges = (result.get('data') or {}).get('deployments', {}).get('edges', [])
if not edges:
    # fallback: try without filter
    result2 = gql('{ deployments { edges { node { id status createdAt } } } }')
    edges = (result2.get('data') or {}).get('deployments', {}).get('edges', [])

latest = next((e['node'] for e in edges if e['node']['status'] == 'SUCCESS'), None)
if not latest:
    print('No SUCCESS deployment found. Edges:', edges[:3])
    sys.exit(1)

dep_id = latest['id']
print(f'Deployment: {dep_id} | Created: {latest["createdAt"][:19]}')

# Step 2: fetch logs
logs_result = gql('''
query($id: String!) {
  deploymentLogs(deploymentId: $id) { message timestamp }
}''', {'id': dep_id})

logs = (logs_result.get('data') or {}).get('deploymentLogs', [])
print(f'Total log lines: {len(logs)}')

# Print last 60
for l in logs[-60:]:
    print(l.get('timestamp','')[:19], l.get('message',''))

# Unique alert/discovery types
seen = set()
print('\n--- UNIQUE SIGNAL TYPES ---')
for l in logs:
    msg = l.get('message', '')
    for kw in ['ALERT:', 'DISCOVERY:', 'ERROR', 'CRITICAL', 'Traceback']:
        if kw in msg:
            key = msg[:80]
            if key not in seen:
                seen.add(key)
                print(l.get('timestamp','')[:19], msg[:120])
            break
