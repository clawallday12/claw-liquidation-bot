#!/usr/bin/env python3
import requests, json, warnings
warnings.filterwarnings('ignore')

TOKEN = 'd59387ad-25d3-4707-bca5-f06acfcbe112'
HEADERS = {'Authorization': f'Bearer {TOKEN}', 'Content-Type': 'application/json'}
API = 'https://backboard.railway.app/graphql/v2'

PROJECT_ID = 'c7af4ad0-0b6e-436b-8105-8735892b4c5f'
SERVICE_ID = 'ba2312aa-98c8-406f-b30b-e6ef9d44cbca'

def gql(query, variables=None):
    payload = {'query': query}
    if variables:
        payload['variables'] = variables
    r = requests.post(API, json=payload, headers=HEADERS, timeout=10, verify=False)
    return r.json()

# Get service deployments
print('[1] Service deployments...')
result = gql('''
query($serviceId: String!, $projectId: String!) {
  deployments(first:5, input:{serviceId:$serviceId, projectId:$projectId}) {
    edges {
      node {
        id
        status
        createdAt
        url
      }
    }
  }
}''', {'serviceId': SERVICE_ID, 'projectId': PROJECT_ID})
print(json.dumps(result, indent=2))
