#!/usr/bin/env python3
import requests, json, warnings
warnings.filterwarnings('ignore')

TOKEN = 'd59387ad-25d3-4707-bca5-f06acfcbe112'
HEADERS = {'Authorization': f'Bearer {TOKEN}', 'Content-Type': 'application/json'}
API = 'https://backboard.railway.app/graphql/v2'
DEPLOYMENT_ID = 'c661220e-0c44-46d5-9eb2-0848677d382b'

def gql(query, variables=None):
    r = requests.post(API, json={'query': query, 'variables': variables or {}}, headers=HEADERS, timeout=15, verify=False)
    return r.json()

# Try build logs
print('[1] Build logs...')
result = gql('''
query($id: String!) {
  buildLogs(deploymentId: $id) {
    message timestamp
  }
}''', {'id': DEPLOYMENT_ID})
print(json.dumps(result, indent=2)[:3000])

# Try deployment status details
print('\n[2] Deployment details...')
result2 = gql('''
query($id: String!) {
  deployment(id: $id) {
    id status
    meta
    createdAt
  }
}''', {'id': DEPLOYMENT_ID})
print(json.dumps(result2, indent=2))
