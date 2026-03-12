#!/usr/bin/env python3
import requests, json, warnings
warnings.filterwarnings('ignore')

TOKEN = 'd59387ad-25d3-4707-bca5-f06acfcbe112'
HEADERS = {'Authorization': f'Bearer {TOKEN}', 'Content-Type': 'application/json'}
API = 'https://backboard.railway.app/graphql/v2'
SERVICE_ID = 'ba2312aa-98c8-406f-b30b-e6ef9d44cbca'
ENV_ID = '6f81b107-2734-4d1f-9958-c4191e5483e3'

def gql(query, variables=None):
    r = requests.post(API, json={'query': query, 'variables': variables or {}}, headers=HEADERS, timeout=15, verify=False)
    return r.json()

# Correct mutation: serviceId not id
print('[1] Connecting GitHub source...')
result = gql('''
mutation($svc: String!, $input: ServiceInstanceUpdateInput!) {
  serviceInstanceUpdate(serviceId: $svc, input: $input)
}''', {
    'svc': SERVICE_ID,
    'input': {
        'source': {
            'repo': 'clawallday12/claw-liquidation-bot'
        },
        'startCommand': 'python web3/liquidation-bot-v3.py',
    }
})
print(json.dumps(result, indent=2))

# Verify source is set
print('\n[2] Verifying...')
verify = gql('''
query($id: String!) {
  service(id: $id) {
    serviceInstances {
      edges { node { id startCommand source { repo image } } }
    }
  }
}''', {'id': SERVICE_ID})
print(json.dumps(verify, indent=2))

# Deploy
print('\n[3] Deploying...')
deploy = gql(
    'mutation($s: String!, $e: String!) { serviceInstanceDeploy(serviceId: $s, environmentId: $e) }',
    {'s': SERVICE_ID, 'e': ENV_ID}
)
print(json.dumps(deploy, indent=2))
