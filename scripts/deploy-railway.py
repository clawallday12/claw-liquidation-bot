#!/usr/bin/env python3
import requests, json, warnings
warnings.filterwarnings('ignore')

TOKEN = 'd59387ad-25d3-4707-bca5-f06acfcbe112'
HEADERS = {'Authorization': f'Bearer {TOKEN}', 'Content-Type': 'application/json'}
API = 'https://backboard.railway.app/graphql/v2'

PROJECT_ID = 'c7af4ad0-0b6e-436b-8105-8735892b4c5f'
SERVICE_ID = 'ba2312aa-98c8-406f-b30b-e6ef9d44cbca'
ENV_ID = '6f81b107-2734-4d1f-9958-c4191e5483e3'

def gql(query, variables=None):
    payload = {'query': query}
    if variables:
        payload['variables'] = variables
    r = requests.post(API, json=payload, headers=HEADERS, timeout=15, verify=False)
    try:
        return r.json()
    except:
        return {'raw': r.text}

# Set env vars
print('[1] Setting environment variables...')
upsert = gql('''
mutation($input: VariableCollectionUpsertInput!) {
  variableCollectionUpsert(input: $input)
}''', {
    'input': {
        'projectId': PROJECT_ID,
        'serviceId': SERVICE_ID,
        'environmentId': ENV_ID,
        'variables': {
            'WALLET_ADDRESS': '0xA8297c4B031022D8d8e3Ce76322139A0120D6931',
            'CHECK_INTERVAL': '60',
        }
    }
})
print(json.dumps(upsert, indent=2))

# Trigger deploy
print('\n[2] Triggering deployment...')
deploy = gql('''
mutation($input: ServiceInstanceDeployInput!) {
  serviceInstanceDeploy(input: $input)
}''', {
    'input': {
        'serviceId': SERVICE_ID,
        'environmentId': ENV_ID,
    }
})
print(json.dumps(deploy, indent=2))

# Check deployments
print('\n[3] Deployment status...')
deps = gql('''
query($serviceId: String!, $projectId: String!) {
  deployments(first:3, input:{serviceId:$serviceId, projectId:$projectId}) {
    edges { node { id status createdAt } }
  }
}''', {'serviceId': SERVICE_ID, 'projectId': PROJECT_ID})
print(json.dumps(deps, indent=2))
