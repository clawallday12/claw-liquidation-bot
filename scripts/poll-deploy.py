#!/usr/bin/env python3
import requests, json, warnings, time
warnings.filterwarnings('ignore')

TOKEN = 'd59387ad-25d3-4707-bca5-f06acfcbe112'
HEADERS = {'Authorization': f'Bearer {TOKEN}', 'Content-Type': 'application/json'}
API = 'https://backboard.railway.app/graphql/v2'
SERVICE_ID = 'ba2312aa-98c8-406f-b30b-e6ef9d44cbca'
PROJECT_ID = 'c7af4ad0-0b6e-436b-8105-8735892b4c5f'

def gql(query, variables=None):
    payload = {'query': query}
    if variables:
        payload['variables'] = variables
    r = requests.post(API, json=payload, headers=HEADERS, timeout=15, verify=False)
    return r.json()

print('Waiting 10s for Railway to register deployment...')
time.sleep(10)

print('Checking deployment status...')
result = gql(
    'query($s: String!, $p: String!) { deployments(first:3, input:{serviceId:$s, projectId:$p}) { edges { node { id status createdAt } } } }',
    {'s': SERVICE_ID, 'p': PROJECT_ID}
)
print(json.dumps(result, indent=2))
