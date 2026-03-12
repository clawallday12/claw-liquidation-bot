#!/usr/bin/env python3
import requests, json, warnings
warnings.filterwarnings('ignore')

TOKEN = 'd59387ad-25d3-4707-bca5-f06acfcbe112'
HEADERS = {'Authorization': f'Bearer {TOKEN}', 'Content-Type': 'application/json'}
API = 'https://backboard.railway.app/graphql/v2'
SERVICE_ID = 'ba2312aa-98c8-406f-b30b-e6ef9d44cbca'

def gql(query, variables=None):
    r = requests.post(API, json={'query': query, 'variables': variables or {}}, headers=HEADERS, timeout=15, verify=False)
    return r.json()

print('[1] Service instance config...')
result = gql('''
query($id: String!) {
  service(id: $id) {
    id name
    serviceInstances {
      edges {
        node {
          id
          buildCommand
          startCommand
          source { image repo }
        }
      }
    }
  }
}''', {'id': SERVICE_ID})
print(json.dumps(result, indent=2))
